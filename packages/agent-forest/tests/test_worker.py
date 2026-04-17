"""Worker process_one flow with a stub executor (no real agent-core subprocess)."""

from __future__ import annotations


def test_process_one_updates_status_on_success(fake_redis, settings):
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    q.enqueue_job(
        fake_redis, job_id="j1", user_id="usr_founder1", prompt="x", webhook_url=None
    )

    def stub(_prompt: str, _sandbox: str) -> JobOutcome:
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

    def stub(_prompt: str, _sandbox: str) -> JobOutcome:
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


def test_run_loop_honors_max_iterations(fake_redis, settings, monkeypatch):
    from agent_forest.worker import main as worker_main

    # Patch redis.Redis.from_url to return our fakeredis, then run 1 iteration.
    monkeypatch.setattr(
        worker_main.redis.Redis,
        "from_url",
        staticmethod(lambda *_a, **_k: fake_redis),
    )
    iters = worker_main.run_loop(settings, max_iterations=1, executor=lambda *_: None)
    assert iters == 1
