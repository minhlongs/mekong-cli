"""Worker main loop: BRPOP task_queue, dispatch, update state, fire webhook."""

from __future__ import annotations

import logging
import multiprocessing as mp
import signal
import sys
from collections.abc import Callable

import redis

from agent_forest import queue as q
from agent_forest.config import ForestSettings
from agent_forest.sandbox import user_output_dir
from agent_forest.webhook import send_webhook
from agent_forest.worker.heartbeat import default_worker_id
from agent_forest.worker.heartbeat import publish as publish_heartbeat
from agent_forest.worker.runner import JobOutcome
from agent_forest.worker.signals import emit as emit_signal

log = logging.getLogger("agent_forest.worker")
_STOP = False


def _install_signal_handlers() -> None:
    def _handle(signum, _frame):  # noqa: ANN001
        global _STOP
        log.info("signal %s received; draining", signum)
        _STOP = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)


def _execute_in_subprocess(
    prompt: str, sandbox_str: str, *, max_rounds: int = 1
) -> JobOutcome:
    """Spawn a fresh Python process so AGENT_CORE_OUTPUTS rebind is clean."""
    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)

    def _target(conn, prompt_, sandbox_, rounds_):  # noqa: ANN001
        from pathlib import Path as _Path

        from agent_forest.worker.runner import run_job as _run

        outcome = _run(prompt_, _Path(sandbox_), max_rounds=rounds_)
        conn.send((outcome.status, outcome.result, outcome.error))
        conn.close()

    proc = ctx.Process(target=_target, args=(child_conn, prompt, sandbox_str, max_rounds))
    proc.start()
    proc.join(timeout=300)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        return JobOutcome(status="failed", error="subprocess timeout (300s)")
    if not parent_conn.poll():
        return JobOutcome(status="failed", error="subprocess produced no result")
    status, result, error = parent_conn.recv()
    return JobOutcome(status=status, result=result, error=error)


def process_one(
    r: redis.Redis,
    settings: ForestSettings,
    *,
    key: str,
    executor: Callable[..., JobOutcome] = _execute_in_subprocess,
) -> JobOutcome:
    parsed = q.parse_job_key(key)
    if not parsed:
        log.warning("malformed key: %s", key)
        return JobOutcome(status="failed", error=f"malformed key {key!r}")
    user_id, job_id = parsed
    data = q.get_job(r, user_id, job_id)
    if not data:
        return JobOutcome(status="failed", error="job missing")
    q.update_job_status(r, user_id, job_id, status="running")
    sandbox = user_output_dir(settings.outputs_dir, user_id)
    outcome = executor(
        data.get("prompt", ""), str(sandbox), max_rounds=settings.feedback_rounds
    )
    q.update_job_status(
        r, user_id, job_id, status=outcome.status, result=outcome.result, error=outcome.error
    )
    emit_signal(outcome.status, user_id, job_id, error=outcome.error)
    # Pillar 2 throughput counters — best-effort, never crash the worker.
    try:
        if outcome.status == "completed":
            r.incr("agent_forest:tasks:completed")
        elif outcome.status == "failed":
            r.incr("agent_forest:tasks:failed")
    except Exception as exc:  # noqa: BLE001
        log.warning("counter bump failed: %s", exc)
    webhook = data.get("webhook_url") or ""
    if webhook:
        payload = q.get_job(r, user_id, job_id) or {}
        send_webhook(webhook, payload, timeout=settings.webhook_timeout_seconds)
    return outcome


def _select_executor(settings: ForestSettings) -> Callable[..., JobOutcome]:
    """Return the executor callable based on settings.worker_executor."""
    if settings.worker_executor == "docker":
        from agent_forest.worker.docker_executor import execute_in_container

        def _docker_exec(p: str, s: str, *, max_rounds: int = 1) -> JobOutcome:
            return execute_in_container(p, s, settings=settings, max_rounds=max_rounds)

        return _docker_exec
    return _execute_in_subprocess


def run_loop(
    settings: ForestSettings | None = None,
    *,
    max_iterations: int | None = None,
    executor: Callable[..., JobOutcome] = _execute_in_subprocess,
) -> int:
    settings = settings or ForestSettings.from_env()
    # If caller didn't override executor, auto-select based on settings.
    if executor is _execute_in_subprocess:
        executor = _select_executor(settings)
    _install_signal_handlers()
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    worker_id = default_worker_id()
    log.info("worker online; id=%s polling=%s", worker_id, settings.redis_url)
    iterations = 0
    while not _STOP:
        if max_iterations is not None and iterations >= max_iterations:
            break
        iterations += 1
        try:
            publish_heartbeat(r, worker_id)
        except Exception as exc:  # noqa: BLE001 — heartbeat is best-effort, never crash worker
            log.warning("heartbeat publish failed: %s", exc)
        key = q.pop_job_key(r, timeout=settings.worker_poll_seconds)
        if not key:
            continue
        try:
            process_one(r, settings, key=key, executor=executor)
        except Exception as exc:  # noqa: BLE001
            log.exception("worker crash on %s: %s", key, exc)
    log.info("worker exited after %d iterations", iterations)
    return iterations


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    run_loop()


if __name__ == "__main__":  # pragma: no cover
    main()
