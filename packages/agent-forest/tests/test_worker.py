"""Worker process_one flow with a stub executor (no real agent-core subprocess)."""

from __future__ import annotations


def test_process_one_updates_status_on_success(fake_redis, settings):
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    q.enqueue_job(
        fake_redis, job_id="j1", user_id="usr_founder1", prompt="x", webhook_url=None
    )

    def stub(_prompt: str, _sandbox: str, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="completed", result="mock output")

    outcome = process_one(
        fake_redis, settings, key="job:usr_founder1:j1", executor=stub
    )
    assert outcome.status == "completed"
    data = q.get_job(fake_redis, "usr_founder1", "j1")
    assert data["status"] == "completed"
    assert data["result"] == "mock output"


def test_process_one_records_failure(fake_redis, settings):
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    q.enqueue_job(
        fake_redis, job_id="j2", user_id="usr_founder2", prompt="x", webhook_url=None
    )

    def stub(_prompt: str, _sandbox: str, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="failed", error="boom")

    outcome = process_one(
        fake_redis, settings, key="job:usr_founder2:j2", executor=stub
    )
    assert outcome.status == "failed"
    data = q.get_job(fake_redis, "usr_founder2", "j2")
    assert data["status"] == "failed"
    assert data["error"] == "boom"


def test_process_one_rejects_malformed_key(fake_redis, settings):
    from agent_forest.worker.main import process_one

    outcome = process_one(fake_redis, settings, key="not-a-key")
    assert outcome.status == "failed"


def test_process_one_emits_signal_with_outcome(fake_redis, settings, monkeypatch):
    """Giai đoạn 3.2.A: worker fires a signal on every completed job."""
    from agent_forest import queue as q
    from agent_forest.worker import main as worker_main
    from agent_forest.worker.runner import JobOutcome

    calls: list[tuple] = []

    def _spy(status, user_id, job_id, *, error=None, **_kw):
        calls.append((status, user_id, job_id, error))
        return True

    monkeypatch.setattr(worker_main, "emit_signal", _spy)

    q.enqueue_job(
        fake_redis, job_id="j9", user_id="usr_sig", prompt="x", webhook_url=None
    )

    def stub(_p, _s, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="completed", result="ok")

    worker_main.process_one(
        fake_redis, settings, key="job:usr_sig:j9", executor=stub
    )
    assert calls == [("completed", "usr_sig", "j9", None)]


def test_process_one_emits_bad_signal_with_error(fake_redis, settings, monkeypatch):
    from agent_forest import queue as q
    from agent_forest.worker import main as worker_main
    from agent_forest.worker.runner import JobOutcome

    calls: list[tuple] = []
    monkeypatch.setattr(
        worker_main,
        "emit_signal",
        lambda status, uid, jid, *, error=None, **_kw: calls.append(
            (status, uid, jid, error)
        )
        or True,
    )

    q.enqueue_job(
        fake_redis, job_id="j10", user_id="usr_sig", prompt="x", webhook_url=None
    )

    def stub(_p, _s, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="failed", error="explode")

    worker_main.process_one(
        fake_redis, settings, key="job:usr_sig:j10", executor=stub
    )
    assert calls == [("failed", "usr_sig", "j10", "explode")]


def test_process_one_increments_completed_counter(fake_redis, settings):
    """Giai đoạn 3.3.B: completed outcome increments Redis counter."""
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    q.enqueue_job(
        fake_redis, job_id="cnt1", user_id="usr_founder1", prompt="x", webhook_url=None
    )

    def stub(_p, _s, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="completed", result="ok")

    process_one(fake_redis, settings, key="job:usr_founder1:cnt1", executor=stub)
    assert int(fake_redis.get("agent_forest:tasks:completed") or 0) == 1
    assert int(fake_redis.get("agent_forest:tasks:failed") or 0) == 0


def test_process_one_increments_failed_counter(fake_redis, settings):
    """Giai đoạn 3.3.B: failed outcome increments Redis counter."""
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    q.enqueue_job(
        fake_redis, job_id="cnt2", user_id="usr_founder2", prompt="x", webhook_url=None
    )

    def stub(_p, _s, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="failed", error="boom")

    process_one(fake_redis, settings, key="job:usr_founder2:cnt2", executor=stub)
    assert int(fake_redis.get("agent_forest:tasks:failed") or 0) == 1
    assert int(fake_redis.get("agent_forest:tasks:completed") or 0) == 0


def test_process_one_counter_graceful_on_redis_error(fake_redis, settings, monkeypatch):
    """Giai đoạn 3.3.B: counter bump failure must NOT crash worker (best-effort)."""
    from agent_forest import queue as q
    from agent_forest.worker import main as worker_main
    from agent_forest.worker.runner import JobOutcome

    q.enqueue_job(
        fake_redis, job_id="cnt3", user_id="usr_founder1", prompt="x", webhook_url=None
    )

    # Patch incr to raise — worker should still return completed outcome
    original_incr = fake_redis.incr

    def _boom(key):
        raise ConnectionError("redis gone")

    monkeypatch.setattr(fake_redis, "incr", _boom)

    def stub(_p, _s, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="completed", result="ok")

    outcome = worker_main.process_one(
        fake_redis, settings, key="job:usr_founder1:cnt3", executor=stub
    )
    # Must survive the Redis error without propagating
    assert outcome.status == "completed"

    # Restore so other tests aren't affected
    monkeypatch.setattr(fake_redis, "incr", original_incr)


def test_run_loop_honors_max_iterations(fake_redis, settings, monkeypatch):
    from agent_forest.worker import main as worker_main

    # Patch redis.Redis.from_url to return our fakeredis, then run 1 iteration.
    monkeypatch.setattr(
        worker_main.redis.Redis,
        "from_url",
        staticmethod(lambda *_a, **_k: fake_redis),
    )
    iters = worker_main.run_loop(
        settings, max_iterations=1, executor=lambda *_a, **_k: None
    )
    assert iters == 1
