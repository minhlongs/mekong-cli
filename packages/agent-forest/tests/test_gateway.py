"""Gateway endpoints via FastAPI TestClient + fakeredis."""

from __future__ import annotations


def _login(client, username="founder1", password="founder1-dev") -> str:
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_metrics_empty_queue(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/plain")
    body = res.text
    assert "agent_forest_queue_depth 0" in body
    assert "agent_forest_up 1" in body
    assert "# TYPE agent_forest_queue_depth gauge" in body
    # Heartbeat gauges default to 0 when no workers alive
    assert "agent_forest_workers_alive 0" in body
    assert "agent_forest_worker_last_seen_timestamp 0" in body
    # Task lifecycle counters — zero on fresh Redis
    assert "# HELP agent_forest_tasks_completed_total" in body
    assert "# TYPE agent_forest_tasks_completed_total counter" in body
    assert "agent_forest_tasks_completed_total 0" in body
    assert "# HELP agent_forest_tasks_failed_total" in body
    assert "# TYPE agent_forest_tasks_failed_total counter" in body
    assert "agent_forest_tasks_failed_total 0" in body


def test_metrics_task_counters_increment(client, fake_redis):
    """After bumping Redis counters directly, /metrics should reflect them."""
    fake_redis.incr("agent_forest:tasks:completed")
    fake_redis.incr("agent_forest:tasks:completed")
    fake_redis.incr("agent_forest:tasks:failed")
    body = client.get("/metrics").text
    assert "agent_forest_tasks_completed_total 2" in body
    assert "agent_forest_tasks_failed_total 1" in body


def test_metrics_reflects_worker_heartbeat(client, fake_redis):
    """Publishing a heartbeat into Redis should bump alive gauge."""
    from agent_forest.worker.heartbeat import publish

    publish(fake_redis, "test-worker-1")
    publish(fake_redis, "test-worker-2")
    m = client.get("/metrics").text
    assert "agent_forest_workers_alive 2" in m
    # last_seen_timestamp is a positive unix-ts (>10^9 for years past 2001)
    for line in m.splitlines():
        if line.startswith("agent_forest_worker_last_seen_timestamp "):
            value = int(line.split()[-1])
            assert value > 1_000_000_000


def test_metrics_reflects_queue_depth(client, fake_redis):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/task", json={"prompt": "a"}, headers=headers)
    assert res.status_code == 202
    res = client.post("/task", json={"prompt": "b"}, headers=headers)
    assert res.status_code == 202
    m = client.get("/metrics").text
    assert "agent_forest_queue_depth 2" in m


def test_login_and_me(client):
    token = _login(client)
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "founder1"
    assert body["user_id"] == "usr_founder1"


def test_login_rejects_bad_password(client):
    res = client.post("/auth/login", json={"username": "founder1", "password": "nope"})
    assert res.status_code == 401


def test_task_requires_auth(client):
    res = client.post("/task", json={"prompt": "hello"})
    assert res.status_code == 401


def test_create_and_fetch_task(client, fake_redis):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/task", json={"prompt": "write hi.txt"}, headers=headers)
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    res = client.get(f"/task/{job_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["prompt"] == "write hi.txt"
    assert res.json()["status"] == "queued"


def test_list_tasks_scoped_per_user(client, fake_redis):
    t1 = _login(client, "founder1", "founder1-dev")
    t2 = _login(client, "founder2", "founder2-dev")

    client.post("/task", json={"prompt": "A"}, headers={"Authorization": f"Bearer {t1}"})
    client.post("/task", json={"prompt": "B"}, headers={"Authorization": f"Bearer {t2}"})

    l1 = client.get("/tasks", headers={"Authorization": f"Bearer {t1}"}).json()
    l2 = client.get("/tasks", headers={"Authorization": f"Bearer {t2}"}).json()
    assert [j["prompt"] for j in l1] == ["A"]
    assert [j["prompt"] for j in l2] == ["B"]


def test_cross_user_fetch_returns_404(client, fake_redis):
    t1 = _login(client, "founder1", "founder1-dev")
    t2 = _login(client, "founder2", "founder2-dev")
    res = client.post(
        "/task", json={"prompt": "secret"}, headers={"Authorization": f"Bearer {t1}"}
    )
    job_id = res.json()["job_id"]
    res = client.get(f"/task/{job_id}", headers={"Authorization": f"Bearer {t2}"})
    assert res.status_code == 404


def test_webhook_validation_rejects_loopback(client):
    token = _login(client)
    res = client.post(
        "/task",
        json={"prompt": "x", "webhook_url": "http://localhost/hook"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
