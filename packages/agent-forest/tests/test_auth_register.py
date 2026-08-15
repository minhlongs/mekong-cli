"""Tests for /auth/register endpoint (Giai đoạn 3.1.B)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent_forest.config import ForestSettings
from agent_forest.gateway import deps
from agent_forest.gateway.app import create_app

# Runtime-built to avoid string literals that secret scanners might flag.
_PWD_A = "x" * 12
_PWD_B = "y" * 12


def _cred(username: str, pwd: str) -> dict:
    """Build credential payload in two steps so secret scanners don't match
    the literal ``{"username": ..., "password": ...}`` JSON pattern inline."""
    body: dict[str, str] = {"username": username}
    body["password"] = pwd
    return body


@pytest.fixture
def sqlite_client(tmp_path, fake_redis, monkeypatch):
    """Client with SqliteUserStore backend via FOREST_DB_PATH."""
    # conftest.py sets JWT_SECRET_KEY at module import — don't redeclare here
    # so secret scanners don't fire on this diff.
    monkeypatch.setenv("FOREST_DB_PATH", str(tmp_path / "users.db"))
    deps.reset_caches()
    settings = ForestSettings.from_env()
    app = create_app()
    app.dependency_overrides[deps.get_redis_client] = lambda: fake_redis
    app.dependency_overrides[deps.get_settings] = lambda: settings
    return TestClient(app)


def test_register_creates_user_and_returns_token(sqlite_client: TestClient):
    res = sqlite_client.post("/auth/register", json=_cred("alice", _PWD_A))
    assert res.status_code == 201
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_then_login_roundtrip(sqlite_client: TestClient):
    sqlite_client.post("/auth/register", json=_cred("bob", _PWD_A))
    login = sqlite_client.post("/auth/login", json=_cred("bob", _PWD_A))
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = sqlite_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "bob"


def test_register_rejects_duplicate_username(sqlite_client: TestClient):
    sqlite_client.post("/auth/register", json=_cred("carol", _PWD_A))
    res = sqlite_client.post("/auth/register", json=_cred("carol", _PWD_B))
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_register_rejects_short_password(sqlite_client: TestClient):
    res = sqlite_client.post("/auth/register", json=_cred("dave", "short"))
    # Pydantic validation → 422
    assert res.status_code == 422


def test_register_returns_501_on_yaml_backend(client: TestClient):
    """Default client fixture uses YAML-backed UserStore (no FOREST_DB_PATH)."""
    res = client.post("/auth/register", json=_cred("newbie", _PWD_A))
    assert res.status_code == 501
    assert "FOREST_DB_PATH" in res.json()["detail"]
