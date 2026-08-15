"""Tests for POST /task/{job_id}/feedback (Giai đoạn 3.2.B).

Auth is mocked via dependency override (bypasses /auth/login entirely) so this
test file contains no credential-shaped strings for secret scanners to flag.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent_forest.gateway import routes_task
from agent_forest.gateway.deps import current_user
from agent_forest.users import User


@pytest.fixture
def authed_client(client: TestClient):
    """TestClient where current_user always resolves to founder1."""
    stub = User("usr_founder1", "founder1", "")
    client.app.dependency_overrides[current_user] = lambda: stub
    yield client
    client.app.dependency_overrides.pop(current_user, None)


def _as(c: TestClient, uid: str, username: str) -> TestClient:
    """Flip the current_user override to impersonate a given user."""
    stub = User(uid, username, "")
    c.app.dependency_overrides[current_user] = lambda: stub
    return c


def _enqueue(c: TestClient, prompt: str = "hi") -> str:
    res = c.post("/task", json={"prompt": prompt})
    assert res.status_code == 202
    return res.json()["job_id"]


def test_feedback_rejects_missing_auth(client: TestClient):
    """No dep override → real current_user enforces Bearer header."""
    res = client.post("/task/job_abc/feedback", json={"rating": "good"})
    assert res.status_code == 401


def test_feedback_404_when_job_not_owned(authed_client: TestClient):
    res = authed_client.post(
        "/task/nonexistent/feedback", json={"rating": "good"}
    )
    assert res.status_code == 404


def test_feedback_accepts_good_rating_and_forwards(
    authed_client: TestClient, monkeypatch
):
    calls: list[tuple] = []

    def _spy(rating, user_id, job_id, *, note=None, **_kw):
        calls.append((rating, user_id, job_id, note))
        return True

    monkeypatch.setattr(routes_task, "emit_user_feedback", _spy)

    jid = _enqueue(authed_client)
    res = authed_client.post(
        f"/task/{jid}/feedback",
        json={"rating": "good", "note": "nice output"},
    )
    assert res.status_code == 202
    body = res.json()
    assert body["rating"] == "good"
    assert body["job_id"] == jid
    assert body["forwarded"] is True
    assert calls[0][0] == "good"
    assert calls[0][3] == "nice output"


def test_feedback_records_false_forwarded_when_mekongd_down(
    authed_client: TestClient, monkeypatch
):
    monkeypatch.setattr(
        routes_task, "emit_user_feedback", lambda *a, **kw: False
    )
    jid = _enqueue(authed_client)
    res = authed_client.post(f"/task/{jid}/feedback", json={"rating": "bad"})
    assert res.status_code == 202
    assert res.json()["forwarded"] is False


def test_feedback_rejects_invalid_rating(authed_client: TestClient):
    jid = _enqueue(authed_client)
    res = authed_client.post(
        f"/task/{jid}/feedback", json={"rating": "meh"}
    )
    assert res.status_code == 422


def test_feedback_enforces_tenant_isolation(authed_client: TestClient):
    """founder1 must not feedback on founder2's job."""
    # founder1 enqueues
    jid = _enqueue(authed_client, prompt="private")

    # Flip identity to founder2 on the same client
    other = _as(authed_client, "usr_founder2", "founder2")
    res = other.post(f"/task/{jid}/feedback", json={"rating": "good"})
    assert res.status_code == 404  # opaque — don't leak existence
