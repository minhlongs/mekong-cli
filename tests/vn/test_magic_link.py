"""15 test cases for Phase 9 P01 — Email Magic-Link Auth Infra.

Isolation: tmp_path + monkeypatch MEKONG_CONFIG_DIR so no ~/.mekong pollution.
Resend client is always mocked — no real email sends.
SQLite WAL mode is used; DB created fresh per-test via tmp_path fixture.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator

import jwt
import pytest
from fastapi.testclient import TestClient

import src.api.vn_pilot_state as _state
from src.services import magic_link_service, resend_client
from src.services.sqlite_migrations import ensure_schema


# ---------- Fixtures ----------

@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    """Point CONFIG_DIR to tmp_path and create a fresh pilot.db with full schema."""
    monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("MEKONG_JWT_SECRET", "test-jwt-secret-32chars-minimum!")
    monkeypatch.setenv("MEKONG_PUBLIC_BASE_URL", "https://test.example.com")

    # Pre-create DB with schema so magic_link_service._open_conn() doesn't
    # treat it as "new" (which would skip ensure_schema if is_new is False
    # after first call). We create it explicitly.
    db_path = tmp_path / "pilot.db"
    conn = sqlite3.connect(str(db_path))
    ensure_schema(conn)
    conn.close()

    yield


@pytest.fixture()
def mock_resend(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Replace resend_client.send_email with a fake. Returns call log list."""
    calls: list[dict] = []

    def fake_send(to: str, subject: str, html: str) -> dict:
        calls.append({"to": to, "subject": subject, "html": html})
        return {"id": "fake-resend-id-123"}

    monkeypatch.setattr(resend_client, "send_email", fake_send)
    return calls


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """FastAPI test client with VN auth routes."""
    from src.api.auth_routes import vn_auth_router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(vn_auth_router)
    return TestClient(app, raise_server_exceptions=False)


# ---------- Helper ----------

def _db_conn(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "pilot.db"))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# Test 1: mint_token inserts row into magic_link_tokens
# =============================================================================
def test_mint_inserts_row(tmp_path: Path) -> None:
    token = magic_link_service.mint_token("user@example.com", "login")
    assert len(token) >= 32

    conn = _db_conn(tmp_path)
    row = conn.execute(
        "SELECT * FROM magic_link_tokens WHERE token = ?", (token,)
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["email"] == "user@example.com"
    assert row["purpose"] == "login"
    assert row["redeemed_at"] is None
    assert row["expires_at"] is not None


# =============================================================================
# Test 2: POST /magic-link always returns 200 (happy path)
# =============================================================================
def test_magic_link_endpoint_returns_200(
    client: TestClient, mock_resend: list[dict]
) -> None:
    resp = client.post("/v1/auth/magic-link", json={"email": "boss@acme.vn"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "message" in body


# =============================================================================
# Test 3: Rate limit — 6th request in 1h silently returns 200 (no email send)
# =============================================================================
def test_rate_limit_drops_silently(
    client: TestClient, mock_resend: list[dict]
) -> None:
    email = "ratelimit@example.com"
    for _ in range(5):
        resp = client.post("/v1/auth/magic-link", json={"email": email})
        assert resp.status_code == 200

    # 6th request — over cap, but still 200
    resp6 = client.post("/v1/auth/magic-link", json={"email": email})
    assert resp6.status_code == 200
    assert resp6.json()["ok"] is True

    # Only 5 emails sent (the 6th was dropped)
    assert len(mock_resend) == 5


# =============================================================================
# Test 4: verify_and_redeem happy path
# =============================================================================
def test_verify_happy_path(tmp_path: Path) -> None:
    token = magic_link_service.mint_token("verify@example.com", "login")
    result = magic_link_service.verify_and_redeem(token)

    assert result["email"] == "verify@example.com"
    assert result["purpose"] == "login"

    # Row should be marked redeemed
    conn = _db_conn(tmp_path)
    row = conn.execute(
        "SELECT redeemed_at FROM magic_link_tokens WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    assert row["redeemed_at"] is not None


# =============================================================================
# Test 5: Expired token raises MagicLinkExpired → GET /verify returns 401
# =============================================================================
def test_expired_token_returns_401(client: TestClient, tmp_path: Path) -> None:
    # Mint with 0-minute TTL (already expired)
    token = magic_link_service.mint_token("expire@example.com", "login", ttl_minutes=0)

    # Force expiry: set expires_at to past
    conn = _db_conn(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    ) + "Z"
    conn.execute(
        "UPDATE magic_link_tokens SET expires_at = ? WHERE token = ?",
        (past, token),
    )
    conn.commit()
    conn.close()

    resp = client.get(f"/v1/auth/verify?token={token}")
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "invalid_or_expired_link"


# =============================================================================
# Test 6: Replay — redeemed token returns 401 on 2nd use
# =============================================================================
def test_replay_returns_401(client: TestClient, mock_resend: list[dict]) -> None:
    token = magic_link_service.mint_token("replay@example.com", "login")

    resp1 = client.get(f"/v1/auth/verify?token={token}")
    assert resp1.status_code == 200

    resp2 = client.get(f"/v1/auth/verify?token={token}")
    assert resp2.status_code == 401
    assert resp2.json()["detail"]["error"] == "invalid_or_expired_link"


# =============================================================================
# Test 7: Unknown / garbage token returns 401
# =============================================================================
def test_unknown_token_returns_401(client: TestClient) -> None:
    resp = client.get("/v1/auth/verify?token=not-a-real-token-xyzzy")
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "invalid_or_expired_link"


# =============================================================================
# Test 8: JWT claims include allowed_orgs from org_members (if table exists)
# =============================================================================
def test_jwt_claims_allowed_orgs(tmp_path: Path) -> None:
    email = "org_member@example.com"

    # Create org_members table manually (Phase P02 will ship this properly)
    conn = _db_conn(tmp_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS org_members (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            email TEXT NOT NULL,
            scope TEXT NOT NULL
        )"""
    )
    conn.execute(
        "INSERT INTO org_members VALUES (?, ?, ?, ?)",
        ("m1", "acme-org", email, "org_admin"),
    )
    conn.commit()
    conn.close()

    jwt_token, expires_at = magic_link_service.mint_jwt_for_email(email)
    secret = "test-jwt-secret-32chars-minimum!"
    claims = jwt.decode(jwt_token, secret, algorithms=["HS256"])

    assert "acme-org" in claims["allowed_orgs"]
    assert "org_admin" in claims["scopes"]


# =============================================================================
# Test 9: JWT scopes union when member of multiple orgs
# =============================================================================
def test_jwt_scopes_union_multi_org(tmp_path: Path) -> None:
    email = "multi@example.com"
    conn = _db_conn(tmp_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS org_members (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            email TEXT NOT NULL,
            scope TEXT NOT NULL
        )"""
    )
    conn.execute("INSERT INTO org_members VALUES (?, ?, ?, ?)", ("m1", "org-a", email, "org_viewer"))
    conn.execute("INSERT INTO org_members VALUES (?, ?, ?, ?)", ("m2", "org-b", email, "org_admin"))
    conn.commit()
    conn.close()

    jwt_token, _ = magic_link_service.mint_jwt_for_email(email)
    secret = "test-jwt-secret-32chars-minimum!"
    claims = jwt.decode(jwt_token, secret, algorithms=["HS256"])

    assert set(claims["allowed_orgs"]) == {"org-a", "org-b"}
    assert "org_viewer" in claims["scopes"]
    assert "org_admin" in claims["scopes"]


# =============================================================================
# Test 10: New user (no org memberships) → scopes=["none"], allowed_orgs=[]
# =============================================================================
def test_jwt_scopes_none_for_unknown_email() -> None:
    jwt_token, expires_at = magic_link_service.mint_jwt_for_email("newuser@example.com")
    secret = "test-jwt-secret-32chars-minimum!"
    claims = jwt.decode(jwt_token, secret, algorithms=["HS256"])

    assert claims["scopes"] == ["none"]
    assert claims["allowed_orgs"] == []


# =============================================================================
# Test 11: purge_expired deletes tokens expired >24h ago
# =============================================================================
def test_purge_expired(tmp_path: Path) -> None:
    # Mint a normal token + one stale token
    fresh_token = magic_link_service.mint_token("fresh@example.com", "login")
    stale_token = magic_link_service.mint_token("stale@example.com", "login")

    # Set stale_token expires_at to 48h ago
    conn = _db_conn(tmp_path)
    stale_expires = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    ) + "Z"
    conn.execute(
        "UPDATE magic_link_tokens SET expires_at = ? WHERE token = ?",
        (stale_expires, stale_token),
    )
    conn.commit()
    conn.close()

    deleted = magic_link_service.purge_expired(grace_hours=24)
    assert deleted >= 1

    # Fresh token should still exist
    conn = _db_conn(tmp_path)
    still_there = conn.execute(
        "SELECT token FROM magic_link_tokens WHERE token = ?", (fresh_token,)
    ).fetchone()
    gone = conn.execute(
        "SELECT token FROM magic_link_tokens WHERE token = ?", (stale_token,)
    ).fetchone()
    conn.close()

    assert still_there is not None
    assert gone is None


# =============================================================================
# Test 12: Email enumeration resistance — unknown email same response as known
# =============================================================================
def test_enumeration_resistance(
    client: TestClient, mock_resend: list[dict]
) -> None:
    resp_known = client.post("/v1/auth/magic-link", json={"email": "real@example.com"})
    resp_unknown = client.post("/v1/auth/magic-link", json={"email": "nobody@notexist.invalid"})

    assert resp_known.status_code == 200
    assert resp_unknown.status_code == 200
    # Same response shape
    assert resp_known.json().keys() == resp_unknown.json().keys()
    assert resp_known.json()["ok"] == resp_unknown.json()["ok"]


# =============================================================================
# Test 13: Rate limit boundary — 5th request allowed, 6th dropped
# =============================================================================
def test_rate_limit_boundary(
    client: TestClient, mock_resend: list[dict]
) -> None:
    email = "boundary@example.com"
    for i in range(5):
        r = client.post("/v1/auth/magic-link", json={"email": email})
        assert r.status_code == 200, f"Request {i+1} failed"

    # Confirm 5 tokens in DB (all minted)
    from src.services.magic_link_service import check_rate_limit
    assert check_rate_limit(email) is False  # now at cap → returns False

    # 6th via endpoint — silently dropped
    r6 = client.post("/v1/auth/magic-link", json={"email": email})
    assert r6.status_code == 200
    assert len(mock_resend) == 5  # still only 5 emails


# =============================================================================
# Test 14: resend_client raises RuntimeError if RESEND_API_KEY missing
# =============================================================================
def test_resend_client_raises_on_missing_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        resend_client.send_email("to@example.com", "Subject", "<p>Body</p>")


# =============================================================================
# Test 15: resend_client times out at 10s (mock urllib to simulate timeout)
# =============================================================================
def test_resend_client_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.error
    import urllib.request as _urllib_req

    monkeypatch.setenv("RESEND_API_KEY", "test-key-fake")

    def fake_urlopen(req, timeout=None):
        raise urllib.error.URLError("timed out")

    monkeypatch.setattr(_urllib_req, "urlopen", fake_urlopen)

    with pytest.raises(urllib.error.URLError, match="timed out"):
        resend_client.send_email("to@example.com", "Subject", "<p>Body</p>")
