"""15 test cases for Phase 9 P02 — Org Creation + Member Management.

Isolation: tmp_path + monkeypatch CONFIG_DIR — no ~/.mekong/ pollution.
Schema created fresh per test via ensure_schema fixture.
JWT signed with test secret (MEKONG_JWT_SECRET monkeypatched).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema
from src.services import magic_link_service
from src.services.org_service import (
    InvalidSlugError,
    LastAdminError,
    MemberNotFoundError,
    SlugCollisionError,
    canonicalize_slug,
    create_org,
    get_org_summary,
    remove_member,
)

_JWT_SECRET = "test-jwt-secret-32chars-minimum!"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    """Fresh DB per test — no ~/.mekong pollution."""
    monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("MEKONG_JWT_SECRET", _JWT_SECRET)

    db_path = tmp_path / "pilot.db"
    conn = sqlite3.connect(str(db_path))
    ensure_schema(conn)
    conn.close()

    yield


@pytest.fixture()
def client() -> TestClient:
    """Test client with org_router mounted."""
    from src.api.org_routes import org_router
    app = FastAPI()
    app.include_router(org_router)
    return TestClient(app, raise_server_exceptions=False)


def _make_jwt(email: str, scopes: list[str], allowed_orgs: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "scopes": scopes,
        "allowed_orgs": allowed_orgs,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm="HS256")


def _db_conn(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "pilot.db"))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# Test 1: canonicalize_slug happy path (mixed case + spaces)
# =============================================================================
def test_canonicalize_slug_happy_path() -> None:
    assert canonicalize_slug("Acme Co!") == "acme-co"
    assert canonicalize_slug("Hello World") == "hello-world"
    assert canonicalize_slug("mekong") == "mekong"


# =============================================================================
# Test 2: canonicalize_slug collapses consecutive hyphens
# =============================================================================
def test_canonicalize_slug_collapses_double_dash() -> None:
    result = canonicalize_slug("Acme  --  Corp")
    assert "--" not in result
    assert result == "acme-corp"


# =============================================================================
# Test 3: canonicalize_slug rejects too-short result
# =============================================================================
def test_canonicalize_slug_rejects_too_short() -> None:
    with pytest.raises(InvalidSlugError):
        canonicalize_slug("AB")  # "ab" = 2 chars < 3


# =============================================================================
# Test 4: canonicalize_slug rejects too-long result
# =============================================================================
def test_canonicalize_slug_rejects_too_long() -> None:
    long_name = "A" * 33  # 33 lowercase 'a' chars = 33 > 32
    with pytest.raises(InvalidSlugError):
        canonicalize_slug(long_name)


# =============================================================================
# Test 5: reserved slug returns 409 via endpoint
# =============================================================================
def test_reserved_slug_returns_409(client: TestClient) -> None:
    token = _make_jwt("founder@example.com", ["none"], [])
    resp = client.post(
        "/v1/org/create",
        json={"display_name": "Default"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "slug_reserved"


# =============================================================================
# Test 6: collision returns 409 + 3 suggestions
# =============================================================================
def test_collision_returns_409_with_suggestions(client: TestClient) -> None:
    token = _make_jwt("founder@example.com", ["none"], [])
    headers = {"Authorization": f"Bearer {token}"}

    # First create succeeds
    r1 = client.post("/v1/org/create", json={"display_name": "Acme Co"}, headers=headers)
    assert r1.status_code == 201, r1.json()

    # Second create with same name collides
    r2 = client.post("/v1/org/create", json={"display_name": "Acme Co"}, headers=headers)
    assert r2.status_code == 409
    detail = r2.json()["detail"]
    assert detail["error"] == "slug_collision"
    assert len(detail["suggestions"]) == 3


# =============================================================================
# Test 7: create_org INSERT atomic (raise SlugCollisionError on dup)
# =============================================================================
def test_create_org_atomic_collision() -> None:
    create_org("Test Org", "first@example.com")
    with pytest.raises(SlugCollisionError) as exc_info:
        create_org("Test Org", "second@example.com")
    assert exc_info.value.slug == "test-org"
    assert len(exc_info.value.suggestions) == 3


# =============================================================================
# Test 8: first member auto-added as org_admin
# =============================================================================
def test_first_member_auto_added_as_org_admin(tmp_path: Path) -> None:
    result = create_org("My Startup", "admin@example.com")
    org_id = result["org_id"]

    conn = _db_conn(tmp_path)
    rows = conn.execute(
        "SELECT * FROM org_members WHERE org_id = ?", (org_id,)
    ).fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0]["email"] == "admin@example.com"
    assert rows[0]["scope"] == "org_admin"
    assert rows[0]["invited_by"] is None


# =============================================================================
# Test 9: get_org_summary returns org + member list
# =============================================================================
def test_get_org_summary_returns_members(tmp_path: Path) -> None:
    result = create_org("Summary Test", "owner@example.com")
    org_id = result["org_id"]

    summary = get_org_summary(org_id)

    assert summary["org_id"] == org_id
    assert summary["display_name"] == "Summary Test"
    assert summary["status"] == "unverified"
    assert summary["member_count"] == 1
    assert len(summary["members"]) == 1
    assert summary["members"][0]["email"] == "owner@example.com"
    assert summary["members"][0]["scope"] == "org_admin"


# =============================================================================
# Test 10: remove_member by org_admin succeeds
# =============================================================================
def test_remove_member_by_org_admin_succeeds(tmp_path: Path) -> None:
    # Create org with one admin, then add a second member manually
    result = create_org("Remove Test", "admin@example.com")
    org_id = result["org_id"]

    # Add a second member directly in DB so we can remove them
    conn = _db_conn(tmp_path)
    conn.execute(
        "INSERT INTO org_members (org_id, user_id, email, scope, joined_at, invited_by) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, "opc_org_member1", "member@example.com", "readonly",
         datetime.now(timezone.utc).isoformat() + "Z", "admin@example.com"),
    )
    conn.commit()
    conn.close()

    # Remove the second member
    remove_member(org_id, "opc_org_member1", "admin@example.com")

    conn = _db_conn(tmp_path)
    gone = conn.execute(
        "SELECT 1 FROM org_members WHERE org_id = ? AND user_id = ?",
        (org_id, "opc_org_member1"),
    ).fetchone()
    conn.close()

    assert gone is None


# =============================================================================
# Test 11: remove_member — last admin raises LastAdminError
# =============================================================================
def test_remove_last_admin_raises() -> None:
    result = create_org("Last Admin Test", "solo@example.com")
    org_id = result["org_id"]
    user_id = result["user_id"]

    with pytest.raises(LastAdminError):
        remove_member(org_id, user_id, "solo@example.com")


# =============================================================================
# Test 12: remove_member — non-existent user raises MemberNotFoundError
# =============================================================================
def test_remove_nonexistent_member_raises() -> None:
    result = create_org("Ghost Test", "boss@example.com")
    org_id = result["org_id"]

    with pytest.raises(MemberNotFoundError):
        remove_member(org_id, "opc_org_ghost999", "boss@example.com")


# =============================================================================
# Test 13: self-remove allowed (member removes themselves)
# =============================================================================
def test_self_remove_allowed(tmp_path: Path) -> None:
    # Create org with admin, add a second admin so removal is allowed
    result = create_org("Self Remove", "admin@example.com")
    org_id = result["org_id"]

    # Add a second admin
    conn = _db_conn(tmp_path)
    conn.execute(
        "INSERT INTO org_members (org_id, user_id, email, scope, joined_at, invited_by) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, "opc_org_admin2", "admin2@example.com", "org_admin",
         datetime.now(timezone.utc).isoformat() + "Z", None),
    )
    conn.commit()
    conn.close()

    # First admin removes themselves (self-remove)
    admin1_user_id = result["user_id"]
    remove_member(org_id, admin1_user_id, "admin@example.com")

    conn = _db_conn(tmp_path)
    gone = conn.execute(
        "SELECT 1 FROM org_members WHERE org_id = ? AND user_id = ?",
        (org_id, admin1_user_id),
    ).fetchone()
    remaining = conn.execute(
        "SELECT COUNT(*) AS cnt FROM org_members WHERE org_id = ?", (org_id,)
    ).fetchone()["cnt"]
    conn.close()

    assert gone is None
    assert remaining == 1


# =============================================================================
# Test 14: mint_jwt_for_email integration — org_admin in org_members → JWT claims
# =============================================================================
def test_mint_jwt_integration_org_admin(tmp_path: Path) -> None:
    """P01 mint_jwt_for_email must read org_id and scope from P02 schema correctly."""
    email = "orgadmin@example.com"
    result = create_org("JWT Integration Org", email)
    org_id = result["org_id"]

    jwt_token, expires_at = magic_link_service.mint_jwt_for_email(email)
    claims = jwt.decode(jwt_token, _JWT_SECRET, algorithms=["HS256"])

    assert org_id in claims["allowed_orgs"], (
        f"Expected org_id '{org_id}' in allowed_orgs={claims['allowed_orgs']}"
    )
    assert "org_admin" in claims["scopes"], (
        f"Expected 'org_admin' in scopes={claims['scopes']}"
    )


# =============================================================================
# Test 15: GET /v1/org/me — multi-org JWT without org_id param returns 400
# =============================================================================
def test_get_org_me_multi_org_jwt_requires_param(client: TestClient) -> None:
    # Create two orgs
    create_org("Org Alpha", "multi@example.com")
    create_org("Org Beta", "multi2@example.com")

    # Mint JWT with two orgs in allowed_orgs (simulate multi-org membership)
    token = _make_jwt("multi@example.com", ["org_admin"], ["org-alpha", "org-beta"])

    resp = client.get(
        "/v1/org/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Should get 400 because org_id is ambiguous (multi-org JWT, no param)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "multi_org_jwt_specify_org_id"
