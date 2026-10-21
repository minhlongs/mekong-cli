# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org invite flow — create, accept, revoke, and list invites."""
from __future__ import annotations

import os
import secrets
from typing import Any

from src.services import magic_link_service, resend_client
from src.services.audit_logger import audit_admin_action
from src.services.org_service_models import (
    AlreadyMemberError,
    InvalidInviteScopeError,
    InviteAlreadyUsedError,
    InviteEmailMismatchError,
    InviteExpiredError,
    InviteInvalidError,
    InviteRevokedOrUsedError,
    OrgNotFoundError,
    _VALID_INVITE_SCOPES,
    _invite_expires_iso,
    _now_iso,
    _open_conn,
)


def _build_invite_email_body(org_display_name: str, accept_url: str) -> str:
    """Return HTML body for Vietnamese org invite email."""
    return (
        '<html>\n<body style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">\n'
        '  <h2 style="color: #1a56db;">Mekong Hub</h2>\n  <p>Xin chào,</p>\n'
        f"  <p>Bạn được mời tham gia tổ chức <strong>{org_display_name}</strong> trên Mekong Hub.</p>\n"
        "  <p>Nhấp vào liên kết bên dưới để chấp nhận lời mời. Liên kết có hiệu lực trong <strong>7 ngày</strong>:</p>\n"
        f'  <p style="margin: 24px 0;"><a href="{accept_url}" style="background-color: #1a56db; color: white; '
        'padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Tham gia tổ chức</a></p>\n'
        f'  <p style="color: #6b7280; font-size: 14px;">Hoặc copy URL: <code style="word-break: break-all;">{accept_url}</code></p>\n'
        '  <p style="color: #6b7280; font-size: 13px;">Nếu bạn không mong đợi lời mời này, hãy bỏ qua email này.</p>\n'
        '  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
        '  <p style="color: #9ca3af; font-size: 12px;">Mekong Hub — Nền tảng cho doanh nghiệp một người Việt Nam</p>\n'
        "</body>\n</html>"
    )


def create_invite(org_id: str, invitee_email: str, scope: str, invited_by_user_id: str) -> dict[str, Any]:
    """Create (or reuse) an org invite and send a VN invitation email."""
    if scope not in _VALID_INVITE_SCOPES:
        raise InvalidInviteScopeError(f"Scope '{scope}' not in {sorted(_VALID_INVITE_SCOPES)}")

    now = _now_iso()
    conn = _open_conn()
    try:
        org_row = conn.execute("SELECT display_name FROM orgs WHERE org_id = ?", (org_id,)).fetchone()
        if org_row is None:
            raise OrgNotFoundError(f"Org '{org_id}' not found")
        display_name = org_row["display_name"]

        if conn.execute(
            "SELECT 1 FROM org_members WHERE org_id = ? AND email = ?", (org_id, invitee_email.lower())
        ).fetchone() is not None:
            raise AlreadyMemberError(f"'{invitee_email}' is already a member of org '{org_id}'")

        pending = conn.execute(
            "SELECT invite_id, expires_at FROM org_invites "
            "WHERE org_id = ? AND invitee_email = ? AND redeemed_at IS NULL AND expires_at > ?",
            (org_id, invitee_email.lower(), now),
        ).fetchone()

        if pending is not None:
            invite_id, expires_at = pending["invite_id"], pending["expires_at"]
        else:
            invite_id, expires_at = secrets.token_urlsafe(16), _invite_expires_iso()
            conn.execute(
                "INSERT INTO org_invites (invite_id, org_id, invitee_email, invited_by_user_id, "
                "scope, expires_at, redeemed_at, created_at) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)",
                (invite_id, org_id, invitee_email.lower(), invited_by_user_id, scope, expires_at, now),
            )
            conn.commit()
    finally:
        conn.close()

    ml_token = magic_link_service.mint_token(invitee_email, purpose="join_invite", org_id=org_id, ttl_minutes=15)
    base_url = os.environ.get("MEKONG_PUBLIC_BASE_URL", "https://api.mekong.dev")
    accept_url = f"{base_url}/v1/auth/verify?token={ml_token}&next=/v1/org/join%3Finvite%3D{invite_id}"
    try:
        resend_client.send_email(
            invitee_email, f"Tham gia {display_name} trên Mekong", _build_invite_email_body(display_name, accept_url)
        )
    except Exception:
        pass

    audit_admin_action(scope="org.invite_created", org=org_id, sub=invited_by_user_id, endpoint="/v1/org/invite")
    return {"invite_id": invite_id, "expires_at": expires_at}


def accept_invite(invite_id: str, joiner_email: str) -> dict[str, Any]:
    """Atomically redeem an invite and add the joiner to org_members."""
    now = _now_iso()
    conn = _open_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT org_id, invitee_email, invited_by_user_id, scope, expires_at, redeemed_at "
            "FROM org_invites WHERE invite_id = ?",
            (invite_id,),
        ).fetchone()
        if row is None:
            conn.rollback()
            raise InviteInvalidError(f"Invite '{invite_id}' not found")
        if row["redeemed_at"] is not None:
            conn.rollback()
            raise InviteRevokedOrUsedError("Invite already used or revoked")
        if row["expires_at"] < now:
            conn.rollback()
            raise InviteExpiredError("Invite has expired")
        if row["invitee_email"].lower() != joiner_email.lower():
            conn.rollback()
            raise InviteEmailMismatchError("Email does not match invite recipient")

        org_id, scope, invited_by = row["org_id"], row["scope"], row["invited_by_user_id"]
        user_id = "opc_org_" + secrets.token_urlsafe(6)
        conn.execute("UPDATE org_invites SET redeemed_at = ? WHERE invite_id = ?", (now, invite_id))
        conn.execute(
            "INSERT OR IGNORE INTO org_members (org_id, user_id, email, scope, joined_at, invited_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_id, user_id, joiner_email.lower(), scope, now, invited_by),
        )
        conn.commit()
    except (InviteInvalidError, InviteExpiredError, InviteRevokedOrUsedError, InviteEmailMismatchError):
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    audit_admin_action(scope="org.invite_accepted", org=org_id, sub=joiner_email, endpoint="/v1/org/join")
    return {"org_id": org_id, "user_id": user_id, "scope": scope}


def revoke_invite(invite_id: str, actor_email: str) -> None:
    """Soft-revoke an invite by setting redeemed_at = 'REVOKED'."""
    conn = _open_conn()
    try:
        row = conn.execute("SELECT org_id, redeemed_at FROM org_invites WHERE invite_id = ?", (invite_id,)).fetchone()
        if row is None:
            raise InviteInvalidError(f"Invite '{invite_id}' not found")
        if row["redeemed_at"] is not None:
            raise InviteAlreadyUsedError("Invite already redeemed or revoked")
        conn.execute("UPDATE org_invites SET redeemed_at = 'REVOKED' WHERE invite_id = ?", (invite_id,))
        conn.commit()
        org_id = row["org_id"]
    finally:
        conn.close()
    audit_admin_action(scope="org.invite_revoked", org=org_id, sub=actor_email, endpoint="/v1/org/invites")


def list_invites(org_id: str) -> list[dict[str, Any]]:
    """Return pending (non-expired, non-redeemed) invites for an org."""
    now = _now_iso()
    conn = _open_conn()
    try:
        rows = conn.execute(
            "SELECT invite_id, invitee_email, scope, expires_at, created_at FROM org_invites "
            "WHERE org_id = ? AND redeemed_at IS NULL AND expires_at > ? ORDER BY created_at",
            (org_id, now),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
