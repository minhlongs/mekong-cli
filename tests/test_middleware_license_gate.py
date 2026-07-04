"""Tests for src.middleware.license_gate FastAPI dependency."""
from __future__ import annotations

import json
import time
from pathlib import Path

import jwt
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from src.middleware import license_gate as gate_mod
from src.middleware.license_gate import JWT_ALGORITHM, license_gate


@pytest.fixture(autouse=True)
def _isolate_license_store(tmp_path, monkeypatch):
    """Force LicenseStore to use a tmp file per test."""
    store_path = tmp_path / "licenses.json"
    monkeypatch.setenv("LICENSE_STORE_PATH", str(store_path))
    # Reset module-level singleton so the env var takes effect.
    from src.lib import license_store as ls_mod

    ls_mod._default_store = None
    yield store_path
    ls_mod._default_store = None


@pytest.fixture
def jwt_secret(monkeypatch) -> str:
    secret = "unit-test-secret"
    monkeypatch.setenv("JWT_SECRET=REDACTED", secret)
    return secret


@pytest.fixture
def app(monkeypatch) -> FastAPI:
    application = FastAPI()

    @application.post("/protected")
    async def protected(
        request: Request, tenant_id: str = Depends(license_gate)
    ) -> dict:
        return {"tenant_id": tenant_id}

    return application


def _seed_license(path: Path, license_key: str, **overrides) -> None:
    record = {
        "subscription_id": "sub_1",
        "customer_id": "cus_42",
        "customer_email": "test@example.com",
        "tier": "starter",
        "product_name": "Starter",
        "created_at": "2026-04-27T00:00:00+00:00",
        "status": "active",
    }
    record.update(overrides)
    payload = {license_key: record}
    path.write_text(json.dumps(payload))


def _make_token(secret: str, **claims) -> str:
    now = int(time.time())
    payload = {"iat": now, "exp": now + 60, **claims}
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def _seed_credits(tenant_id: str, balance: int) -> None:
    from src.raas.credits import CreditStore

    store = CreditStore()
    current = store.get_balance(tenant_id)
    if balance > current:
        store.add_credits(tenant_id, balance - current, "test_seed")
    elif balance < current and current > 0:
        store.deduct(tenant_id, current - balance, "test_seed")


class TestMissingOrInvalidToken:
    def test_missing_token_401(self, app):
        client = TestClient(app)
        resp = client.post("/protected")
        assert resp.status_code == 401
        assert resp.json()["detail"] == {"error": "missing_token"}

    def test_invalid_token_signature_401(self, app, jwt_secret):
        bad = jwt.encode({"tenant_id": "x"}, "wrong-secret", algorithm="HS256")
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {bad}"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["error"] == "invalid_token"

    def test_expired_token_401(self, app, jwt_secret):
        past = int(time.time()) - 10
        token = jwt.encode(
            {"tenant_id": "x", "license_key": "lk", "iat": past - 60, "exp": past},
            jwt_secret,
            algorithm="HS256",
        )
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["error"] == "token_expired"

    def test_malformed_claims_401(self, app, jwt_secret):
        token = _make_token(jwt_secret)  # no tenant_id / license_key
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["error"] == "malformed_claims"


class TestLicenseStateChecks:
    def test_inactive_license_402(self, app, jwt_secret, _isolate_license_store):
        _seed_license(_isolate_license_store, "lk_inactive", status="cancelled")
        token = _make_token(jwt_secret, tenant_id="cus_42", license_key="lk_inactive")
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 402
        body = resp.json()["detail"]
        assert body["error"] == "license_inactive"
        assert "recharge_url" in body

    def test_unknown_license_402(self, app, jwt_secret):
        token = _make_token(jwt_secret, tenant_id="cus_42", license_key="lk_missing")
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 402
        assert resp.json()["detail"]["error"] == "license_inactive"

    def test_zero_credits_402(self, app, jwt_secret, _isolate_license_store):
        _seed_license(_isolate_license_store, "lk_no_credit")
        _seed_credits("cus_42", 0)
        token = _make_token(jwt_secret, tenant_id="cus_42", license_key="lk_no_credit")
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 402
        assert resp.json()["detail"]["error"] == "no_credits"

    def test_success_path_returns_tenant(
        self, app, jwt_secret, _isolate_license_store
    ):
        _seed_license(_isolate_license_store, "lk_ok")
        _seed_credits("cus_42", 50)
        token = _make_token(jwt_secret, tenant_id="cus_42", license_key="lk_ok")
        client = TestClient(app)
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == {"tenant_id": "cus_42"}


class TestRechargeUrl:
    def test_default_recharge_url(self, monkeypatch):
        monkeypatch.delenv("RECHARGE_URL", raising=False)
        assert gate_mod._recharge_url() == "https://www.mekongmind.com/billing"

    def test_override_recharge_url(self, monkeypatch):
        monkeypatch.setenv("RECHARGE_URL", "https://example.com/buy")
        assert gate_mod._recharge_url() == "https://example.com/buy"
