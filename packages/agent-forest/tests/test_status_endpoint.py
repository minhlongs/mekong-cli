"""Tests for GET /status JSON endpoint (Giai đoạn 3.1.E)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_status_returns_json_shape(client: TestClient):
    res = client.get("/status")
    assert res.status_code == 200
    body = res.json()
    assert body["service"] == "agent-forest"
    assert body["up"] is True
    assert isinstance(body["queue_depth"], int)
    assert isinstance(body["workers_alive"], int)
    assert isinstance(body["worker_last_seen_ts"], int)
    assert "version" in body


def test_status_reports_queue_depth(client: TestClient, fake_redis):
    from agent_forest.queue import TASK_QUEUE

    fake_redis.lpush(TASK_QUEUE, "job:x:y")
    fake_redis.lpush(TASK_QUEUE, "job:a:b")
    res = client.get("/status")
    assert res.status_code == 200
    assert res.json()["queue_depth"] == 2


def test_status_reports_alive_workers(client: TestClient, fake_redis):
    from agent_forest.worker.heartbeat import publish

    publish(fake_redis, "worker-1")
    publish(fake_redis, "worker-2")
    res = client.get("/status")
    body = res.json()
    assert body["workers_alive"] == 2
    assert body["worker_last_seen_ts"] > 0


def test_status_handles_redis_error_gracefully(client: TestClient, monkeypatch):
    """Broken redis → -1 sentinels, endpoint still returns 200."""
    from agent_forest.gateway import app as app_mod

    class _BrokenRedis:
        def llen(self, key):
            raise RuntimeError("redis down")

        def keys(self, pattern):
            raise RuntimeError("redis down")

        def pipeline(self):
            raise RuntimeError("redis down")

    monkeypatch.setattr(app_mod, "count_alive", lambda _r: -1)
    monkeypatch.setattr(app_mod, "last_seen_timestamp", lambda _r: 0)

    # Override dep to broken redis just for this test
    from agent_forest.gateway import deps

    client.app.dependency_overrides[deps.get_redis_client] = lambda: _BrokenRedis()
    try:
        res = client.get("/status")
        assert res.status_code == 200
        body = res.json()
        assert body["queue_depth"] == -1
        # count_alive/last_seen monkey-patched to fallback values
        assert body["workers_alive"] == -1
        assert body["worker_last_seen_ts"] == 0
    finally:
        client.app.dependency_overrides.pop(deps.get_redis_client, None)
