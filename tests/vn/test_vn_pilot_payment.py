"""Tests for pilot payment instructions + expiring-clients endpoints.

Covers:
- GET /v1/pilot/payment-instructions (user-facing, no auth required)
- GET /v1/pilot/expiring-clients (admin-only, MEKONG_ADMIN_TOKEN required)
- _payment_instructions_data helper + _credit_block_response + pilot_credit_gate
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import vn_pilot_routes as vpr
from src.api import vn_pilot_billing as vpb
from src.services import vietqr_recurring as vqr
from src.middleware import pilot_credit_gate as pcg


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """FastAPI app with isolated CONFIG_DIR."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app)


@pytest.fixture
def client_with_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Same but with pilot credit gate enabled."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_PILOT_GATE", "1")
    pcg.configure(enabled=True)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app)


@pytest.fixture
def _seed_subscription(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> callable:
    """Factory fixture: seed a subscription via _append_subscription.

    Uses _append_subscription(rec) directly so the caller controls the
    exact next_due_at date (needed for expiring-clients time-window tests).
    """
    monkeypatch.setattr(vqr, "_ensure_dir", lambda: None)

    def _seed(user_id: str, tier: str = "starter_vnd", monthly_vnd: int = 199_000,
              credits: int = 300, status: str = "active",
              next_due_days: int = 30) -> dict:
        started = datetime.now(timezone.utc).date().isoformat()
        next_due = (datetime.now(timezone.utc).date() + timedelta(days=next_due_days)).isoformat()
        rec = {
            "user_id": user_id,
            "org_id": "default",
            "tier": tier,
            "monthly_vnd": monthly_vnd,
            "credits": credits,
            "status": status,
            "started_at": started,
            "last_paid_at": started,
            "next_due_at": next_due,
            "bank_tx_ref": f"seed-{user_id}",
            "renewal_count": 0,
        }
        vqr._append_subscription(rec)
        return rec
    return _seed


# ---------------------------------------------------------------------------
# Payment instructions
# ---------------------------------------------------------------------------

class TestPaymentInstructions:
    def test_no_auth_returns_400(self, client: TestClient) -> None:
        r = client.get("/v1/pilot/payment-instructions")
        assert r.status_code == 400
        assert "MEKONG_USER_ID" in r.json()["detail"]

    def test_payment_instructions_default_tier(self, client: TestClient) -> None:
        os.environ["MEKONG_USER_ID"] = "opc_001_pay1"
        try:
            r = client.get("/v1/pilot/payment-instructions")
        finally:
            os.environ.pop("MEKONG_USER_ID", None)
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "opc_001_pay1"
        assert data["tier"] == "starter_vnd"
        assert data["amount_vnd"] == 199_000
        assert data["bank_tx_ref"] == "MEKONG-opc_001_pay1"
        assert "Techcombank" in data["bank"]
        assert "instructions_vn" in data
        assert "instructions_en" in data
        assert data["account_number"] == "0977048051"
        assert data["status"] == "payment_required"
        assert data["renew_url"] == "/v1/pilot/credit-status"

    def test_payment_instructions_uses_existing_tier(
        self, client: TestClient, _seed_subscription
    ) -> None:
        user_id = "opc_001_growth"
        _seed_subscription(user_id, tier="growth_vnd", monthly_vnd=299_000)
        os.environ["MEKONG_USER_ID"] = user_id
        try:
            r = client.get("/v1/pilot/payment-instructions")
        finally:
            os.environ.pop("MEKONG_USER_ID", None)
        assert r.status_code == 200
        data = r.json()
        assert data["tier"] == "growth_vnd"
        assert data["amount_vnd"] == 299_000

    def test_payment_instructions_overrides_default_tier_param(self, client: TestClient) -> None:
        os.environ["MEKONG_USER_ID"] = "opc_001_no_sub"
        try:
            r = client.get("/v1/pilot/payment-instructions?tier=pro_vnd")
        finally:
            os.environ.pop("MEKONG_USER_ID", None)
        assert r.status_code == 200
        data = r.json()
        assert data["tier"] == "pro_vnd"
        assert data["amount_vnd"] == 499_000

    def test_vietnamese_instructions_include_bank_details(self, client: TestClient) -> None:
        os.environ["MEKONG_USER_ID"] = "opc_001_vn"
        try:
            r = client.get("/v1/pilot/payment-instructions")
        finally:
            os.environ.pop("MEKONG_USER_ID", None)
        assert r.status_code == 200
        vn = r.json()["instructions_vn"]
        assert "199" in vn or "199.000" in vn
        assert "MEKONG-opc_001_vn" in vn
        assert "0977" in vn


# ---------------------------------------------------------------------------
# Expiring clients (admin)
# ---------------------------------------------------------------------------

class TestExpiringClients:
    def test_no_admin_token_returns_503(self, client: TestClient, _seed_subscription) -> None:
        _seed_subscription("opc_001_exp1")
        if "MEKONG_ADMIN_TOKEN" in os.environ:
            del os.environ["MEKONG_ADMIN_TOKEN"]
        r = client.get("/v1/pilot/expiring-clients")
        assert r.status_code == 503

    def test_empty_when_no_expiring(self, client: TestClient, _seed_subscription) -> None:
        _seed_subscription("opc_001_far", next_due_days=60)  # 60 days out
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            r = client.get("/v1/pilot/expiring-clients?days=14")
        finally:
            os.environ.pop("MEKONG_ADMIN_TOKEN", None)
        assert r.status_code == 200
        data = r.json()
        assert data["scanned"] >= 1
        assert data["clients"] == []

    def test_finds_expiring_within_window(
        self, client: TestClient, _seed_subscription
    ) -> None:
        _seed_subscription("opc_001_soon", next_due_days=5)
        _seed_subscription("opc_001_later", next_due_days=30)
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            r = client.get("/v1/pilot/expiring-clients?days=7")
        finally:
            os.environ.pop("MEKONG_ADMIN_TOKEN", None)
        assert r.status_code == 200
        data = r.json()
        uids = [c["user_id"] for c in data["clients"]]
        assert "opc_001_soon" in uids
        assert "opc_001_later" not in uids
        assert data["warning_days"] == 7

    def test_excludes_cancelled(self, client: TestClient, _seed_subscription) -> None:
        _seed_subscription("opc_001_cancelled", status="cancelled", next_due_days=2)
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            r = client.get("/v1/pilot/expiring-clients?days=7")
        finally:
            os.environ.pop("MEKONG_ADMIN_TOKEN", None)
        assert r.status_code == 200
        data = r.json()
        uids = [c["user_id"] for c in data["clients"]]
        assert "opc_001_cancelled" not in uids

    def test_sorted_by_days_remaining(self, client: TestClient, _seed_subscription) -> None:
        _seed_subscription("opc_001_d10", next_due_days=10)
        _seed_subscription("opc_001_d3", next_due_days=3)
        _seed_subscription("opc_001_d7", next_due_days=7)
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            r = client.get("/v1/pilot/expiring-clients?days=14")
        finally:
            os.environ.pop("MEKONG_ADMIN_TOKEN", None)
        assert r.status_code == 200
        clients = r.json()["clients"]
        days = [c["days_until_due"] for c in clients]
        assert days == sorted(days), "Should be sorted ascending"


# ---------------------------------------------------------------------------
# pilot_credit_gate module
# ---------------------------------------------------------------------------

class TestPilotCreditGate:
    def test_disabled_by_default(self) -> None:
        assert not pcg.is_enabled()

    def test_configure_toggle(self) -> None:
        pcg.configure(enabled=True, warning_days=14, grace_days=5)
        assert pcg.is_enabled()
        assert pcg._cfg["warning_days"] == 14
        assert pcg._cfg["grace_days"] == 5
        pcg.configure(enabled=False)

    def test_payment_instructions_helper(self) -> None:
        data = vpb._payment_instructions_data("opc_test", "growth_vnd")
        assert data["amount_vnd"] == 299_000
        assert data["bank_tx_ref"] == "MEKONG-opc_test"
        assert "Techcombank" in data["bank"]
        assert len(data["instructions_vn"]) > 50
        assert len(data["instructions_en"]) > 50

    def test_payment_instructions_default_tier(self) -> None:
        data = vpb._payment_instructions_data("opc_test")
        assert data["tier"] == "starter_vnd"
        assert data["amount_vnd"] == 199_000

    def test_days_diff(self) -> None:
        assert pcg._days_diff("2026-07-14", "2026-07-20") == 6
        assert pcg._days_diff("2026-07-20", "2026-07-14") == -6
        assert pcg._days_diff("bad", "2026-07-20") == 0
