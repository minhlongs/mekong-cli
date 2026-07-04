"""Tests for Phase 9 P04 — Polar.sh org subscription (checkout + webhook).

10 cases covering:
  1. Checkout happy path
  2. Checkout already-active → 409
  3. Checkout missing org → 404
  4. Webhook missing secret → 503
  5. Webhook bad signature → 401
  6. Webhook replay (same event_id) → 200 noop
  7. Webhook subscription.created flips status → active
  8. Webhook subscription.cancelled flips status → cancelled
  9. Webhook unknown event type → 200 logged
  10. Webhook timestamp >5min old → 401 (replay window)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sqlite3
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema

# ---------- Constants ----------

TEST_WEBHOOK_SECRET = "test_polar_webhook_secret_abc123456"
TEST_JWT_SECRET=REDACTED = "test_jwt_secret_for_billing_xyz789"
TEST_ORG_ID = "test-org"


# ---------- Fixtures ----------


@pytest.fixture
def db_conn(tmp_path: Path) -> sqlite3.Connection:
    """Isolated SQLite connection with full schema."""
    monkey = pytest.MonkeyPatch()
    monkey.setattr(_state, "CONFIG_DIR", tmp_path)
    db_path = tmp_path / "pilot.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    ensure_schema(conn)
    conn.commit()
    yield conn
    conn.close()
    monkey.undo()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """FastAPI app with billing routes + isolated CONFIG_DIR."""
    monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_JWT_SECRET=REDACTED", TEST_JWT_SECRET=REDACTED)
    monkeypatch.setenv("MEKONG_ADMIN_TOKEN", "test_admin_token_for_scope")
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)

    from src.api.billing_routes import router as billing_router

    app = FastAPI()
    app.include_router(billing_router)
    return TestClient(app)


# ---------- Helpers ----------


def _seed_org(conn: sqlite3.Connection, org_id: str = TEST_ORG_ID, status: str = "unverified") -> None:
    """Insert an org row for testing."""
    now = "2026-05-19T00:00:00.000000Z"
    conn.execute(
        """
        INSERT OR IGNORE INTO orgs
            (org_id, display_name, status, platform_fee_paid_until,
             trial_expires_at, created_at, created_by_email,
             polar_org_subscription_id, raw_payload)
        VALUES (?, ?, ?, NULL, ?, ?, ?, NULL, ?)
        """,
        (org_id, "Test Org", status, "2026-06-02T00:00:00.000000Z", now, "test@example.com", "{}"),
    )
    conn.commit()


def _make_jwt_token(sub: str = "test@example.com", scopes: list[str] | None = None, allowed_orgs: list[str] | None = None) -> str:
    """Create a JWT token for testing using PyJWT directly."""
    import jwt
    import time

    now = int(time.time())
    claims = {
        "sub": sub,
        "scopes": scopes or ["org_admin"],
        "allowed_orgs": allowed_orgs or [TEST_ORG_ID, "*"],
        "iat": now,
        "exp": now + 86400,
    }
    return jwt.encode(claims, TEST_JWT_SECRET=REDACTED, algorithm="HS256")


def _sign_polar_webhook(body: bytes, webhook_id: str = "wh_test_123", secret: str = TEST_WEBHOOK_SECRET) -> dict[str, str]:
    """Compute Standard Webhooks signature headers."""
    ts = str(int(time.time()))
    signing_input = f"{webhook_id}.{ts}.{body.decode('utf-8')}"
    sig = base64.b64encode(
        hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Content-Type": "application/json",
        "webhook-id": webhook_id,
        "webhook-timestamp": ts,
        "webhook-signature": f"v1,{sig}",
    }


def _make_subscription_created_payload(org_id: str = TEST_ORG_ID) -> dict:
    """Polar subscription.created event payload."""
    return {
        "type": "subscription.created",
        "data": {
            "id": "sub_polar_abc123",
            "status": "active",
            "current_period_end": "2026-06-19T00:00:00.000000Z",
            "metadata": {"mekong_org_id": org_id},
        },
    }


def _make_subscription_cancelled_payload(org_id: str = TEST_ORG_ID) -> dict:
    """Polar subscription.cancelled event payload."""
    return {
        "type": "subscription.cancelled",
        "data": {
            "id": "sub_polar_abc123",
            "metadata": {"mekong_org_id": org_id},
        },
    }


# ---------- Tests ----------


class TestCheckoutEndpoint:
    """POST /v1/billing/checkout/org"""

    def test_checkout_happy_path(self, client: TestClient, db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unverified org + valid JWT → Polar checkout URL returned."""
        _seed_org(db_conn, status="unverified")
        token = _make_jwt_token()
        monkeypatch.setenv("POLAR_PRODUCT_ID_ORG_PLATFORM_FEE", "prod_test_123")

        # Mock Polar client to avoid real API call
        from src.api import billing_routes
        monkeypatch.setattr(
            billing_routes,
            "create_checkout_session",
            lambda **kw: {"url": "https://polar.sh/checkout/abc123", "id": "ch_abc123"},
        )

        r = client.post(
            "/v1/billing/checkout/org?org_id=test-org",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "checkout_url" in data
        assert "polar_checkout_id" in data

    def test_checkout_missing_org_returns_404(self, client: TestClient, db_conn: sqlite3.Connection) -> None:
        """Org not found → 404."""
        token = _make_jwt_token()
        r = client.post(
            "/v1/billing/checkout/org?org_id=nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_checkout_already_active_returns_409(self, client: TestClient, db_conn: sqlite3.Connection) -> None:
        """Active org cannot re-checkout → 409."""
        _seed_org(db_conn, status="active")
        token = _make_jwt_token()
        r = client.post(
            "/v1/billing/checkout/org?org_id=test-org",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 409
        assert "org_already_active" in r.text


class TestWebhookEndpoint:
    """POST /v1/billing/webhook/org"""

    def test_webhook_missing_secret_returns_503(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """POLAR_WEBHOOK_SECRET not set → 503."""
        monkeypatch.delenv("POLAR_WEBHOOK_SECRET", raising=False)
        body = json.dumps({"type": "test"}).encode()
        r = client.post("/v1/billing/webhook/org", content=body, headers={"Content-Type": "application/json"})
        assert r.status_code == 503

    def test_webhook_bad_signature_returns_401(self, client: TestClient) -> None:
        """Invalid HMAC → 401."""
        body = json.dumps({"type": "test"}).encode()
        r = client.post(
            "/v1/billing/webhook/org",
            content=body,
            headers={
                "Content-Type": "application/json",
                "webhook-id": "wh_test",
                "webhook-timestamp": str(int(time.time())),
                "webhook-signature": "v1,bad_signature_here",
            },
        )
        assert r.status_code == 401

    def test_webhook_replay_returns_200_noop(self, client: TestClient, db_conn: sqlite3.Connection) -> None:
        """Same event_id twice → second returns 200 with replayed flag."""
        payload = _make_subscription_created_payload()
        body = json.dumps(payload).encode()
        headers = _sign_polar_webhook(body)

        # First delivery
        r1 = client.post("/v1/billing/webhook/org", content=body, headers=headers)
        assert r1.status_code == 200
        assert r1.json()["ok"] is True

        # Replay (same headers + body)
        r2 = client.post("/v1/billing/webhook/org", content=body, headers=headers)
        assert r2.status_code == 200
        assert r2.json().get("replayed") is True

    def test_webhook_subscription_created_flips_status(self, client: TestClient, db_conn: sqlite3.Connection) -> None:
        """subscription.created → org status = active."""
        _seed_org(db_conn, status="unverified")

        payload = _make_subscription_created_payload()
        body = json.dumps(payload).encode()
        headers = _sign_polar_webhook(body)

        r = client.post("/v1/billing/webhook/org", content=body, headers=headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # Verify DB state
        row = db_conn.execute(
            "SELECT status, polar_org_subscription_id FROM orgs WHERE org_id = ?",
            (TEST_ORG_ID,),
        ).fetchone()
        assert row["status"] == "active"
        assert row["polar_org_subscription_id"] == "sub_polar_abc123"

    def test_webhook_subscription_cancelled_flips_status(self, client: TestClient, db_conn: sqlite3.Connection) -> None:
        """subscription.cancelled → org status = cancelled."""
        _seed_org(db_conn, status="active")
        # Set the polar subscription ID so cancellation can match
        db_conn.execute(
            "UPDATE orgs SET polar_org_subscription_id = 'sub_polar_abc123' WHERE org_id = ?",
            (TEST_ORG_ID,),
        )
        db_conn.commit()

        payload = _make_subscription_cancelled_payload()
        body = json.dumps(payload).encode()
        headers = _sign_polar_webhook(body)

        r = client.post("/v1/billing/webhook/org", content=body, headers=headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

        row = db_conn.execute(
            "SELECT status FROM orgs WHERE org_id = ?",
            (TEST_ORG_ID,),
        ).fetchone()
        assert row["status"] == "cancelled"

    def test_webhook_unknown_event_type_returns_200(self, client: TestClient) -> None:
        """Unknown event type → 200 (logged, not error)."""
        payload = {"type": "subscription.updated", "data": {"id": "sub_x"}}
        body = json.dumps(payload).encode()
        headers = _sign_polar_webhook(body)

        r = client.post("/v1/billing/webhook/org", content=body, headers=headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_webhook_expired_timestamp_returns_401(self, client: TestClient) -> None:
        """Timestamp >5min old → 401 replay_window_expired."""
        old_ts = str(int(time.time()) - 600)  # 10 minutes ago
        body = json.dumps({"type": "test"}).encode()
        webhook_id = "wh_test_old"
        signing_input = f"{webhook_id}.{old_ts}.{body.decode('utf-8')}"
        sig = base64.b64encode(
            hmac.new(TEST_WEBHOOK_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
        ).decode()

        r = client.post(
            "/v1/billing/webhook/org",
            content=body,
            headers={
                "Content-Type": "application/json",
                "webhook-id": webhook_id,
                "webhook-timestamp": old_ts,
                "webhook-signature": f"v1,{sig}",
            },
        )
        assert r.status_code == 401
        assert "replay_window" in r.text
