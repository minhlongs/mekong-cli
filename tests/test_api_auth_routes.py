"""Tests for src.api.auth_routes (POST /auth/login)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth_routes import JWT_ALGORITHM, router


@pytest.fixture(autouse=True)
def _isolate_license_store(tmp_path, monkeypatch):
    store_path = tmp_path / "licenses.json"
    monkeypatch.setenv("LICENSE_STORE_PATH", str(store_path))
    from src.lib import license_store as ls_mod

    ls_mod._default_store = None
    yield store_path
    ls_mod._default_store = None


@pytest.fixture
def jwt_secret(monkeypatch) -> str:
    secret = "auth-test-secret"
    monkeypatch.setenv("JWT_SECRET=REDACTED", secret)
    return secret


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _seed(path: Path, key: str, **overrides) -> None:
    record = {
        "subscription_id": "sub_1",
        "customer_id": "cus_99",
        "customer_email": "u@example.com",
        "tier": "growth",
        "product_name": "Growth",
        "created_at": "2026-04-27T00:00:00+00:00",
        "status": "active",
    }
    record.update(overrides)
    path.write_text(json.dumps({key: record}))


class TestLoginEndpoint:
    def test_invalid_license_returns_401(self, client):
        resp = client.post("/auth/login", json={"license_key": "lic_does_not_exist"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["error"] == "invalid_license"

    def test_inactive_license_returns_402(
        self, client, _isolate_license_store
    ):
        _seed(_isolate_license_store, "lic_inactive", status="cancelled")
        resp = client.post("/auth/login", json={"license_key": "lic_inactive"})
        assert resp.status_code == 402
        assert resp.json()["detail"]["error"] == "license_inactive"

    def test_success_returns_jwt(self, client, _isolate_license_store, jwt_secret):
        _seed(_isolate_license_store, "lic_okay99")
        resp = client.post("/auth/login", json={"license_key": "lic_okay99"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["tenant_id"] == "cus_99"
        assert body["tier"] == "growth"
        assert body["expires_in"] == 3600
        assert body["token_type"] == "Bearer"

        claims = jwt.decode(
            body["access_token"], jwt_secret, algorithms=[JWT_ALGORITHM]
        )
        assert claims["tenant_id"] == "cus_99"
        assert claims["license_key"] == "lic_okay99"
        assert claims["tier"] == "growth"
        assert claims["exp"] - claims["iat"] == 3600

    def test_missing_tenant_id_returns_500(
        self, client, _isolate_license_store
    ):
        _seed(_isolate_license_store, "lic_broken", customer_id=None)
        resp = client.post("/auth/login", json={"license_key": "lic_broken"})
        assert resp.status_code == 500
        assert resp.json()["detail"]["error"] == "license_missing_tenant"

    def test_validation_rejects_short_key(self, client):
        resp = client.post("/auth/login", json={"license_key": "x"})
        assert resp.status_code == 422  # pydantic validation

    def test_token_iat_recent(self, client, _isolate_license_store, jwt_secret):
        _seed(_isolate_license_store, "lic_nowkey")
        before = int(time.time())
        resp = client.post("/auth/login", json={"license_key": "lic_nowkey"})
        after = int(time.time())
        assert resp.status_code == 200
        claims = jwt.decode(
            resp.json()["access_token"], jwt_secret, algorithms=[JWT_ALGORITHM]
        )
        assert before <= claims["iat"] <= after
