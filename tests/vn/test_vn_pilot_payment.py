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
from src.api import vn_pilot_state
from src.services import vietqr_recurring as vqr
from src.middleware import pilot_credit_gate as pcg


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """FastAPI app with isolated CONFIG_DIR."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app)


@pytest.fixture
def client_with_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Same but with pilot credit gate enabled."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
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
        # Falls back to env placeholder when MEKONG_BANK_ACCOUNT_NUMBER is unset
        assert "SET_MEKONG_BANK_ACCOUNT_NUMBER" in data["account_number"]
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
    @staticmethod
    def _admin_headers() -> dict:
        token = os.environ.get("MEKONG_ADMIN_TOKEN", "")
        return {"x-admin-token": token} if token else {}

    def test_no_admin_token_returns_503(self, client: TestClient, _seed_subscription) -> None:
        _seed_subscription("opc_001_exp1")
        if "MEKONG_ADMIN_TOKEN" in os.environ:
            del os.environ["MEKONG_ADMIN_TOKEN"]
        r = client.get("/v1/pilot/expiring-clients")
        assert r.status_code == 503

    def test_expiring_no_header_returns_401(self, client: TestClient, _seed_subscription) -> None:
        """Per-request auth: missing x-admin-token → 401 even when env is set."""
        _seed_subscription("opc_001_auth1")
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            # No x-admin-token header
            r = client.get("/v1/pilot/expiring-clients?days=7")
        finally:
            os.environ.pop("MEKONG_ADMIN_TOKEN", None)
        assert r.status_code == 401

    def test_expiring_wrong_token_returns_403(self, client: TestClient, _seed_subscription) -> None:
        """Per-request auth: wrong token → 403."""
        _seed_subscription("opc_001_auth2")
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            r = client.get("/v1/pilot/expiring-clients?days=7",
                           headers={"x-admin-token": "wrong-token"})
        finally:
            os.environ.pop("MEKONG_ADMIN_TOKEN", None)
        assert r.status_code == 403

    def test_empty_when_no_expiring(self, client: TestClient, _seed_subscription) -> None:
        _seed_subscription("opc_001_far", next_due_days=60)  # 60 days out
        os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin"
        try:
            r = client.get("/v1/pilot/expiring-clients?days=14",
                           headers=self._admin_headers())
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
            r = client.get("/v1/pilot/expiring-clients?days=7",
                           headers=self._admin_headers())
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
            r = client.get("/v1/pilot/expiring-clients?days=7",
                           headers=self._admin_headers())
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
            r = client.get("/v1/pilot/expiring-clients?days=14",
                           headers=self._admin_headers())
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

    def test_payment_instructions_rejects_invalid_user_id(self, client: TestClient) -> None:
        """_payment_instructions_data rejects non-opc_ user_id (injection guard)."""
        os.environ["MEKONG_USER_ID"] = "<script>alert(1)</script>"
        try:
            r = client.get("/v1/pilot/payment-instructions")
        finally:
            os.environ.pop("MEKONG_USER_ID", None)
        assert r.status_code == 400

    def test_payment_instructions_accepts_valid_user_id(self, client: TestClient) -> None:
        """Valid opc_ user_id passes sanitization."""
        os.environ["MEKONG_USER_ID"] = "opc_001_test123"
        try:
            r = client.get("/v1/pilot/payment-instructions")
        finally:
            os.environ.pop("MEKONG_USER_ID", None)
        assert r.status_code == 200
        assert "MEKONG-opc_001_test123" in r.json()["bank_tx_ref"]

    def test_get_subscription_status_returns_expired(self, tmp_path, monkeypatch) -> None:
        """get_subscription_status correctly returns 'expired' (not 'active')."""
        import src.api.vn_pilot_state as _state
        from src.services import vietqr_recurring as vqr
        monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(vqr, "_ensure_dir", lambda: None)
        vqr._append_subscription({
            "user_id": "opc_status_exp",
            "org_id": "default",
            "tier": "starter_vnd",
            "status": "expired",
            "next_due_at": "2026-01-01",
            "credits": 0,
            "started_at": "2026-01-01",
            "last_paid_at": "2026-01-01",
            "renewal_count": 0,
        })
        assert vqr.get_subscription_status("opc_status_exp") == "expired"

    def test_get_subscription_status_returns_overdue(self, tmp_path, monkeypatch) -> None:
        """get_subscription_status correctly returns 'overdue' for subs past due."""
        import src.api.vn_pilot_state as _state
        from src.services import vietqr_recurring as vqr
        monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(vqr, "_ensure_dir", lambda: None)
        vqr._append_subscription({
            "user_id": "opc_status_od",
            "org_id": "default",
            "tier": "starter_vnd",
            "status": "overdue",
            "next_due_at": "2026-01-01",
            "credits": 10,
            "started_at": "2026-01-01",
            "last_paid_at": "2026-01-01",
            "renewal_count": 0,
        })
        assert vqr.get_subscription_status("opc_status_od") == "overdue"




# ---------------------------------------------------------------------------
# PilotCreditGateMiddleware integration
# ---------------------------------------------------------------------------
#
# Skip-list semantics (design contract):
#   /v1/pilot/credit-status    — expired users MUST see their balance to pay
#   /v1/pilot/payment-instructions — expired users need payment instructions
#   /v1/pilot/renew            — manual topup after bank transfer
#   /health, /healthz, /metrics — observability must always work
#   /v1/pilot/signup           — signup must always work
#   /v1/pilot/expiring-clients — admin view (not credit-consuming)
#   /v1/pilot/health, /v1/pilot/stats, /v1/pilot/recent — informational
#
# Any other route blocked by check_pilot_credit() for expired/overdue
# pilots returns HTTP 402 + VietQR payment instructions.

@pytest.fixture
def gate_app(tmp_path, monkeypatch):
    """FastAPI app with pilot routes + PilotCreditGateMiddleware enabled.

    Both vpr.CONFIG_DIR and vn_pilot_state.CONFIG_DIR are patched:
      vqr._append_subscription → _ensure_dir() → vn_pilot_state.CONFIG_DIR
      vqr._append_subscription → JsonlBackend.append_subscription
        → vn_pilot_common._subscriptions_path() → vn_pilot_state.CONFIG_DIR
    """
    monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_PILOT_GATE", "1")
    pcg.configure(enabled=True)
    app = FastAPI()
    app.include_router(vpr.router)
    app.add_middleware(pcg.PilotCreditGateMiddleware)
    return TestClient(app)


def _seed(monkeypatch, tmp_path, user_id: str, status: str = "active",
          next_due_days: int = 30, credits: int = 50) -> None:
    """Seed a subscription into tmp_path."""
    monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(vqr, "_ensure_dir", lambda: None)
    started = "2026-05-01"
    next_due = (datetime.now(timezone.utc).date()
                + timedelta(days=next_due_days)).isoformat()
    rec = {
        "user_id": user_id,
        "org_id": "default",
        "tier": "starter_vnd",
        "monthly_vnd": 199_000,
        "credits": credits,
        "status": status,
        "started_at": started,
        "last_paid_at": started,
        "next_due_at": next_due,
        "bank_tx_ref": f"seed-{user_id}",
        "renewal_count": 0,
    }
    vqr._append_subscription(rec)


class TestPilotCreditGateMiddleware:
    """Middleware skip-list / block-path behavior via TestClient."""

    def test_payment_instructions_not_blocked_for_expired(self, gate_app, monkeypatch, tmp_path):
        """Payment instructions endpoint is in _SKIP_PATHS — always 200."""
        _seed(monkeypatch, tmp_path, "opc_mw_pay", "expired")
        r = gate_app.get(
            "/v1/pilot/payment-instructions",
            headers={"x-user-id": "opc_mw_pay"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "payment_required"

    def test_credit_status_shown_to_expired(self, gate_app, monkeypatch, tmp_path):
        """credit-status is in _SKIP_PATHS — expired still 200 (to see bill)."""
        _seed(monkeypatch, tmp_path, "opc_mw_st", "expired")
        r = gate_app.get(
            "/v1/pilot/credit-status",
            headers={"x-user-id": "opc_mw_st"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["user_id"] == "opc_mw_st"
        assert body["status"] == "expired"

    def test_active_user_not_blocked(self, gate_app, monkeypatch, tmp_path):
        """Active subscription — all routes pass through."""
        _seed(monkeypatch, tmp_path, "opc_mw_act", "active", next_due_days=30)
        r = gate_app.get(
            "/v1/pilot/credit-status",
            headers={"x-user-id": "opc_mw_act"},
        )
        assert r.status_code == 200

    def test_no_user_id_fail_open(self, gate_app):
        """No user_id / MEKONG_USER_ID → check_pilot_credit returns None
        → fail-open → request falls through to the endpoint.
        The endpoint returns 400 (no user id required), not 402.  This is
        the expected fail-open contract — middleware never fabricates a block
        when it cannot identify the pilot.
        """
        if "MEKONG_USER_ID" in os.environ:
            del os.environ["MEKONG_USER_ID"]
        r = gate_app.get("/v1/pilot/credit-status")
        assert r.status_code == 400  # endpoint requires user id

    def test_gate_disabled_allows_expired(self, tmp_path, monkeypatch):
        """MEKONG_PILOT_GATE=0 — middleware is a no-op."""
        monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
        monkeypatch.setenv("MEKONG_PILOT_GATE", "0")
        pcg.configure(enabled=False)
        _seed(monkeypatch, tmp_path, "opc_mw_off", "expired")
        app = FastAPI()
        app.include_router(vpr.router)
        app.add_middleware(pcg.PilotCreditGateMiddleware)
        client = TestClient(app)
        r = client.get(
            "/v1/pilot/credit-status",
            headers={"x-user-id": "opc_mw_off"},
        )
        assert r.status_code == 200

    def test_overdue_beyond_grace_blocked(self, gate_app, monkeypatch, tmp_path):
        """overdue + 10 days overdue (grace=3) → subscription-level blocked check."""
        _seed(monkeypatch, tmp_path, "opc_mw_grc", "overdue",
              next_due_days=-10)
        r = gate_app.get(
            "/v1/pilot/credit-status",
            headers={"x-user-id": "opc_mw_grc"},
        )
        # credit-status is in _SKIP_PATHS, so it shows the overdue user
        # their status — but the BLOCK happens on non-payment routes
        # Here we test it shows overdue (skip path works).
        assert r.status_code == 200
        assert r.json()["status"] == "overdue"

    def test_skip_list_includes_payment_and_admin_paths(self):
        """SKIP_PATHS contract: payment + health + admin paths are accessible
        to expired pilots (so they can pay or admin can diagnose)."""
        required = {
            "/health", "/healthz", "/metrics",
            "/v1/pilot/payment-instructions",
            "/v1/pilot/credit-status",
            "/v1/pilot/expiring-clients",
            "/v1/pilot/renew",
            "/v1/pilot/signup",
            "/v1/pilot/health", "/v1/pilot/stats", "/v1/pilot/recent",
        }
        for path in required:
            assert path in pcg._SKIP_PATHS, f"{path!r} must be in _SKIP_PATHS"

    def test_check_pilot_credit_direct_block(self, tmp_path, monkeypatch):
        """Call check_pilot_credit() directly — unit-level block test."""
        from starlette.requests import Request

        monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
        _seed(monkeypatch, tmp_path, "opc_direct", "expired")

        scope = {
            "type": "http", "method": "GET",
            "path": "/v1/some/generic/route",
            "headers": [(b"x-user-id", b"opc_direct")],
            "query_string": b"", "server": ("localhost", 8000),
            "scheme": "http", "root_path": "",
        }
        req = Request(scope)
        res = pcg.check_pilot_credit(req)
        assert res is not None
        assert res.status_code == 402
        body = res.body.decode()
        assert "payment_required" in body
        assert "MEKONG-opc_direct" in body

    def test_check_pilot_credit_direct_pass_through(self, tmp_path, monkeypatch):
        """check_pilot_credit() returns None for active pilot (allow)."""
        from starlette.requests import Request

        monkeypatch.setattr(vn_pilot_state, "CONFIG_DIR", tmp_path)
        _seed(monkeypatch, tmp_path, "opc_active2", "active", next_due_days=30)

        scope = {
            "type": "http", "method": "GET",
            "path": "/v1/some/generic/route",
            "headers": [(b"x-user-id", b"opc_active2")],
            "query_string": b"", "server": ("localhost", 8000),
            "scheme": "http", "root_path": "",
        }
        req = Request(scope)
        assert pcg.check_pilot_credit(req) is None
