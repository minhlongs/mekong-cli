"""12 test cases for Phase 9 P03 — Org Invite Flow.

Coverage:
 1. create_invite happy path — row in org_invites + magic_link_tokens both created
 2. Invalid scope rejected (422)
 3. Already-member returns 409
 4. Idempotent create — pending invite reused, no duplicate row
 5. Email sent via resend_client (mock)
 6. accept_invite happy path — org_members row added, redeemed_at set, JWT returned
 7. Accept by wrong email → 400
 8. Accept expired invite → 410
 9. Accept revoked invite → 410
10. Replay attack: redeem twice → 2nd attempt 410
11. revoke_invite happy path + revoke already-used → 410
12. GET /v1/org/invites returns pending invites for org admin
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
from src.services.org_service import (
    InvalidInviteScopeError,
    create_invite,
    create_org,
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
    monkeypatch.setenv("MEKONG_PUBLIC_BASE_URL", "https://api.mekong.dev")

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


def _seed_org(display_name: str = "Acme Corp",
              founder: str = "founder@acme.vn") -> dict:
    """Helper: create org and return result dict."""
    return create_org(display_name, founder)


# =============================================================================
# Test 1: create_invite happy path — DB rows created
# =============================================================================
def test_create_invite_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """create_invite inserts rows in org_invites and magic_link_tokens."""
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda to, subject, html: {"id": "mock-email-id"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    founder_user_id = result["user_id"]

    invite = create_invite(
        org_id=org_id,
        invitee_email="alice@acme.vn",
        scope="cs",
        invited_by_user_id=founder_user_id,
    )

    assert "invite_id" in invite
    assert "expires_at" in invite

    conn = _db_conn(tmp_path)
    invite_row = conn.execute(
        "SELECT * FROM org_invites WHERE invite_id = ?", (invite["invite_id"],)
    ).fetchone()
    assert invite_row is not None
    assert invite_row["org_id"] == org_id
    assert invite_row["invitee_email"] == "alice@acme.vn"
    assert invite_row["scope"] == "cs"
    assert invite_row["redeemed_at"] is None

    ml_row = conn.execute(
        "SELECT * FROM magic_link_tokens WHERE email = ? AND purpose = 'join_invite'",
        ("alice@acme.vn",),
    ).fetchone()
    assert ml_row is not None
    assert ml_row["org_id"] == org_id
    conn.close()


# =============================================================================
# Test 2: Invalid scope rejected with InvalidInviteScopeError
# =============================================================================
def test_create_invite_invalid_scope_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    with pytest.raises(InvalidInviteScopeError):
        create_invite(
            org_id=result["org_id"],
            invitee_email="bad@acme.vn",
            scope="superadmin",  # not in valid set
            invited_by_user_id=result["user_id"],
        )


# =============================================================================
# Test 3: Already-member returns AlreadyMemberError (and 409 via endpoint)
# =============================================================================
def test_create_invite_already_member_returns_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    founder_email = "founder@acme.vn"

    token = _make_jwt(founder_email, ["org_admin"], [org_id])
    resp = client.post(
        f"/v1/org/invite?org_id={org_id}",
        json={"invitee_email": founder_email, "scope": "readonly"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "already_member"


# =============================================================================
# Test 4: Idempotent invite creation — reuse pending row, no duplicate
# =============================================================================
def test_create_invite_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Calling create_invite twice for same (org, email) reuses the invite row."""
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    uid = result["user_id"]

    inv1 = create_invite(org_id, "bob@acme.vn", "cs", uid)
    inv2 = create_invite(org_id, "bob@acme.vn", "cs", uid)

    # Same invite_id returned
    assert inv1["invite_id"] == inv2["invite_id"]

    # Only one row in org_invites
    conn = _db_conn(tmp_path)
    count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM org_invites WHERE org_id = ? AND invitee_email = ?",
        (org_id, "bob@acme.vn"),
    ).fetchone()["cnt"]
    conn.close()
    assert count == 1


# =============================================================================
# Test 5: Email sent via resend_client (mock verifies call)
# =============================================================================
def test_create_invite_sends_email(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invitation email is dispatched via resend_client.send_email."""
    sent: list[dict] = []

    def _mock_send(to: str, subject: str, html: str) -> dict:
        sent.append({"to": to, "subject": subject})
        return {"id": "mock-123"}

    monkeypatch.setattr("src.services.org_service.resend_client.send_email", _mock_send)
    result = _seed_org()

    create_invite(result["org_id"], "charlie@acme.vn", "marketing", result["user_id"])

    assert len(sent) == 1
    assert sent[0]["to"] == "charlie@acme.vn"
    assert "Acme Corp" in sent[0]["subject"]


# =============================================================================
# Test 6: accept_invite happy path — org_members row added, JWT returned
# =============================================================================
def test_accept_invite_happy_path(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /v1/org/join — happy path: org_members row inserted, 201 + JWT."""
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    uid = result["user_id"]

    invite = create_invite(org_id, "diana@acme.vn", "readonly", uid)

    # Joiner has a JWT (obtained via magic-link verify in real flow)
    token = _make_jwt("diana@acme.vn", ["none"], [])
    resp = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.json()
    body = resp.json()
    assert body["org_id"] == org_id
    assert body["scope"] == "readonly"
    assert "jwt" in body

    conn = _db_conn(tmp_path)
    member = conn.execute(
        "SELECT * FROM org_members WHERE org_id = ? AND email = ?",
        (org_id, "diana@acme.vn"),
    ).fetchone()
    assert member is not None
    assert member["scope"] == "readonly"

    invite_row = conn.execute(
        "SELECT redeemed_at FROM org_invites WHERE invite_id = ?",
        (invite["invite_id"],),
    ).fetchone()
    assert invite_row["redeemed_at"] is not None
    assert invite_row["redeemed_at"] != "REVOKED"
    conn.close()


# =============================================================================
# Test 7: Accept by wrong email → 400
# =============================================================================
def test_accept_invite_wrong_email_returns_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    invite = create_invite(result["org_id"], "eve@acme.vn", "readonly", result["user_id"])

    # Different user tries to use this invite
    token = _make_jwt("attacker@evil.com", ["none"], [])
    resp = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "invite_email_mismatch"


# =============================================================================
# Test 8: Accept expired invite → 410
# =============================================================================
def test_accept_expired_invite_returns_410(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    invite = create_invite(result["org_id"], "frank@acme.vn", "cs", result["user_id"])

    # Backdate expires_at to past
    past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    ) + "Z"
    conn = _db_conn(tmp_path)
    conn.execute(
        "UPDATE org_invites SET expires_at = ? WHERE invite_id = ?",
        (past, invite["invite_id"]),
    )
    conn.commit()
    conn.close()

    token = _make_jwt("frank@acme.vn", ["none"], [])
    resp = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 410
    assert resp.json()["detail"]["error"] == "invite_expired"


# =============================================================================
# Test 9: Accept revoked invite → 410
# =============================================================================
def test_accept_revoked_invite_returns_410(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    invite = create_invite(result["org_id"], "grace@acme.vn", "cs", result["user_id"])

    # Revoke the invite
    conn = _db_conn(tmp_path)
    conn.execute(
        "UPDATE org_invites SET redeemed_at = 'REVOKED' WHERE invite_id = ?",
        (invite["invite_id"],),
    )
    conn.commit()
    conn.close()

    token = _make_jwt("grace@acme.vn", ["none"], [])
    resp = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 410
    assert resp.json()["detail"]["error"] == "invite_used_or_revoked"


# =============================================================================
# Test 10: Replay attack — redeem twice, second attempt 410
# =============================================================================
def test_accept_invite_replay_attack_returns_410(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    invite = create_invite(result["org_id"], "henry@acme.vn", "readonly", result["user_id"])
    token = _make_jwt("henry@acme.vn", ["none"], [])

    r1 = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 410
    assert r2.json()["detail"]["error"] == "invite_used_or_revoked"


# =============================================================================
# Test 11a: revoke_invite happy path — redeemed_at = 'REVOKED'
# =============================================================================
def test_revoke_invite_happy_path(
    tmp_path: Path, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    invite = create_invite(org_id, "ivy@acme.vn", "marketing", result["user_id"])

    token = _make_jwt("founder@acme.vn", ["org_admin"], [org_id])
    resp = client.delete(
        f"/v1/org/invites/{invite['invite_id']}?org_id={org_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    conn = _db_conn(tmp_path)
    row = conn.execute(
        "SELECT redeemed_at FROM org_invites WHERE invite_id = ?",
        (invite["invite_id"],),
    ).fetchone()
    conn.close()
    assert row["redeemed_at"] == "REVOKED"


# =============================================================================
# Test 11b: revoke already-used invite → 410
# =============================================================================
def test_revoke_already_used_invite_returns_410(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    invite = create_invite(org_id, "jack@acme.vn", "cs", result["user_id"])

    # First: joiner redeems
    join_token = _make_jwt("jack@acme.vn", ["none"], [])
    jr = client.post(
        f"/v1/org/join?invite={invite['invite_id']}",
        headers={"Authorization": f"Bearer {join_token}"},
    )
    assert jr.status_code == 201

    # Now admin tries to revoke after it's been used
    admin_token = _make_jwt("founder@acme.vn", ["org_admin"], [org_id])
    resp = client.delete(
        f"/v1/org/invites/{invite['invite_id']}?org_id={org_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 410
    assert resp.json()["detail"]["error"] == "invite_already_used_or_revoked"


# =============================================================================
# Test 12: GET /v1/org/invites — admin sees pending invites
# =============================================================================
def test_list_invites_returns_pending_for_admin(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.services.org_service.resend_client.send_email",
        lambda *a, **kw: {"id": "x"},
    )
    result = _seed_org()
    org_id = result["org_id"]
    uid = result["user_id"]

    # Create two invites
    create_invite(org_id, "kate@acme.vn", "readonly", uid)
    create_invite(org_id, "liam@acme.vn", "cs", uid)

    token = _make_jwt("founder@acme.vn", ["org_admin"], [org_id])
    resp = client.get(
        f"/v1/org/invites?org_id={org_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    invites = resp.json()
    assert len(invites) == 2
    emails = {i["invitee_email"] for i in invites}
    assert emails == {"kate@acme.vn", "liam@acme.vn"}
