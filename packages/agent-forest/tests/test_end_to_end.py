"""E2E: gateway enqueues → worker consumes → status transitions to completed."""

from __future__ import annotations


def test_gateway_worker_roundtrip(client, fake_redis, settings):
    from agent_forest import queue as q
    from agent_forest.worker.main import process_one
    from agent_forest.worker.runner import JobOutcome

    res = client.post(
        "/auth/login", json={"username": "founder1", "password": "founder1-dev"}
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/task", json={"prompt": "ping"}, headers=headers)
    job_id = res.json()["job_id"]

    key = q.pop_job_key(fake_redis, timeout=1)
    assert key == f"job:usr_founder1:{job_id}"

    def stub(_p: str, _s: str, *, max_rounds: int = 1) -> JobOutcome:
        return JobOutcome(status="completed", result="pong")

    process_one(fake_redis, settings, key=key, executor=stub)
    final = client.get(f"/task/{job_id}", headers=headers).json()
    assert final["status"] == "completed"
    assert final["result"] == "pong"
