"""Redis queue producer/consumer + per-user isolation."""

from __future__ import annotations


def test_enqueue_persists_record(fake_redis):
    from agent_forest import queue as q

    record = q.enqueue_job(
        fake_redis, job_id="j1", user_id="u1", prompt="hi", webhook_url=None
    )
    assert record["status"] == "queued"
    assert q.get_job(fake_redis, "u1", "j1")["prompt"] == "hi"


def test_list_jobs_scoped_to_user(fake_redis):
    from agent_forest import queue as q

    q.enqueue_job(fake_redis, job_id="j1", user_id="u1", prompt="a", webhook_url=None)
    q.enqueue_job(fake_redis, job_id="j2", user_id="u2", prompt="b", webhook_url=None)

    u1_jobs = q.list_jobs(fake_redis, "u1")
    u2_jobs = q.list_jobs(fake_redis, "u2")
    assert [j["job_id"] for j in u1_jobs] == ["j1"]
    assert [j["job_id"] for j in u2_jobs] == ["j2"]


def test_pop_and_parse_key(fake_redis):
    from agent_forest import queue as q

    q.enqueue_job(fake_redis, job_id="j1", user_id="u1", prompt="x", webhook_url=None)
    key = q.pop_job_key(fake_redis, timeout=1)
    assert key == "job:u1:j1"
    assert q.parse_job_key(key) == ("u1", "j1")


def test_parse_malformed_key():
    from agent_forest import queue as q

    assert q.parse_job_key("garbage") is None
    assert q.parse_job_key("job:only-one") is None


def test_update_status(fake_redis):
    from agent_forest import queue as q

    q.enqueue_job(fake_redis, job_id="j1", user_id="u1", prompt="x", webhook_url=None)
    q.update_job_status(
        fake_redis, "u1", "j1", status="completed", result="ok", error=None
    )
    data = q.get_job(fake_redis, "u1", "j1")
    assert data["status"] == "completed"
    assert data["result"] == "ok"
