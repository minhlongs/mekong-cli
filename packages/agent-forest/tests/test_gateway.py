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
