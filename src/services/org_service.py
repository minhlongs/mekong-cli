"""Org service — slug canonicalization, org creation, member management, invites.

Backed by the SQLite orgs + org_members + org_invites tables (P02/P03 schemas).
All writes are atomic via explicit transactions. Zero new pip dependencies.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import src.api.vn_pilot_state as _state
from src.services.audit_logger import audit_admin_action
from src.services.sqlite_migrations import ensure_schema
from src.services import magic_link_service
from src.services import resend_client

# ---------- Constants ----------

RESERVED_SLUGS: frozenset[str] = frozenset({"default", "admin", "api", "www"})

_SLUG_MAX = 32
_SLUG_MIN = 3
_COLLAPSE_RE = re.compile(r"-{2,}")
_ALLOW_RE = re.compile(r"[^a-z0-9-]")


# ---------- Custom exceptions ----------


class InvalidSlugError(Exception):
    """Slug too short, too long, or contains invalid characters."""


class ReservedSlugError(Exception):
    """Slug matches a reserved name."""


class SlugCollisionError(Exception):
    """An org with this slug already exists."""

    def __init__(self, slug: str, suggestions: list[str]) -> None:
        super().__init__(f"Org slug '{slug}' already taken")
        self.slug = slug
        self.suggestions = suggestions


class OrgNotFoundError(Exception):
    """Org_id does not exist."""


class MemberNotFoundError(Exception):
    """User is not a member of the org."""


class LastAdminError(Exception):
    """Cannot remove the last org_admin."""


# ---------- Internal helpers ----------


def _db_path() -> Path:
    return _state.CONFIG_DIR / "pilot.db"


def _open_conn() -> sqlite3.Connection:
    """Open WAL-mode SQLite; create schema if DB is fresh."""
    db = _db_path()
    is_new = not db.exists()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    if is_new:
        ensure_schema(conn)
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _trial_expires_iso() -> str:
    """Return ISO timestamp 14 days from now."""
    dt = datetime.now(timezone.utc) + timedelta(days=14)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


# ---------- Slug helpers ----------


def canonicalize_slug(display_name: str) -> str:
    """Normalize a display name to a URL-safe slug.

    Steps:
    1. NFKD decompose + strip non-ASCII (handles Vietnamese names).
    2. Lowercase.
    3. Replace any non-[a-z0-9] char with hyphen.
    4. Collapse consecutive hyphens.
    5. Strip leading/trailing hyphens.
    6. Validate length: [3, 32].

    Args:
        display_name: Raw org name from user.

    Returns:
        Canonicalized slug string.

    Raises:
        InvalidSlugError: If result is shorter than 3 or longer than 32 chars.
    """
    # Normalize unicode → ASCII-safe
    normalized = unicodedata.normalize("NFKD", display_name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")

    slug = ascii_only.lower()
    slug = _ALLOW_RE.sub("-", slug)
    slug = _COLLAPSE_RE.sub("-", slug)
    slug = slug.strip("-")

    if len(slug) < _SLUG_MIN:
        raise InvalidSlugError(
            f"Slug '{slug}' is too short (min {_SLUG_MIN} chars). "
            f"Original display_name: '{display_name}'"
        )
    if len(slug) > _SLUG_MAX:
        raise InvalidSlugError(
            f"Slug '{slug}' is too long (max {_SLUG_MAX} chars). "
            f"Original display_name: '{display_name}'"
        )
    return slug


def is_reserved_slug(slug: str) -> bool:
    """Return True if slug is in the reserved list."""
    return slug in RESERVED_SLUGS


def suggest_alternatives(slug: str) -> list[str]:
    """Return 3 alternative slugs by appending numeric/locale suffixes."""
    return [f"{slug}-2", f"{slug}-3", f"{slug}-vn"]


def _slug_exists(conn: sqlite3.Connection, slug: str) -> bool:
    row = conn.execute("SELECT 1 FROM orgs WHERE org_id = ?", (slug,)).fetchone()
    return row is not None


# ---------- Service functions ----------


def create_org(display_name: str, founder_email: str) -> dict[str, Any]:
    """Create a new org with founder as first org_admin member.

    Atomic transaction: slug collision check + INSERT orgs + INSERT org_members.
    SQLite PK uniqueness is the final guard against race conditions.

    Args:
        display_name: Human-readable org name.
        founder_email: Email of the calling user (from JWT sub claim).

    Returns:
        Dict with keys: org_id, user_id, display_name, status, trial_expires_at.

    Raises:
        InvalidSlugError: Canonicalized slug is out-of-length bounds.
        ReservedSlugError: Slug matches reserved name.
        SlugCollisionError: Org with that slug already exists.
    """
    slug = canonicalize_slug(display_name)

    if is_reserved_slug(slug):
        raise ReservedSlugError(f"Slug '{slug}' is reserved and cannot be used.")

    user_id = "opc_org_" + secrets.token_urlsafe(6)
    now = _now_iso()
    trial_expires = _trial_expires_iso()
    raw_payload = json.dumps(
        {"display_name": display_name, "founder_email": founder_email}
    )

    conn = _open_conn()
    try:
        # Begin explicit transaction
        conn.execute("BEGIN IMMEDIATE")

        # Check collision within the transaction (prevents TOCTOU race)
        if _slug_exists(conn, slug):
            suggestions = suggest_alternatives(slug)
            conn.rollback()
            raise SlugCollisionError(slug, suggestions)

        conn.execute(
            """
            INSERT INTO orgs
                (org_id, display_name, status, platform_fee_paid_until,
                 trial_expires_at, created_at, created_by_email,
                 polar_org_subscription_id, raw_payload)
            VALUES (?, ?, 'unverified', NULL, ?, ?, ?, NULL, ?)
            """,
            (slug, display_name, trial_expires, now, founder_email, raw_payload),
        )

        conn.execute(
            """
            INSERT INTO org_members
                (org_id, user_id, email, scope, joined_at, invited_by)
            VALUES (?, ?, ?, 'org_admin', ?, NULL)
            """,
            (slug, user_id, founder_email, now),
        )

        conn.commit()
    except SlugCollisionError:
        raise
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        # PK violation from a simultaneous insert (race condition)
        suggestions = suggest_alternatives(slug)
        raise SlugCollisionError(slug, suggestions) from exc
    finally:
        conn.close()

    audit_admin_action(
        scope="org.created",
        org=slug,
        sub=founder_email,
        endpoint="/v1/org/create",
    )

    return {
        "org_id": slug,
        "user_id": user_id,
        "display_name": display_name,
        "status": "unverified",
        "trial_expires_at": trial_expires,
    }


def get_org_summary(org_id: str) -> dict[str, Any]:
    """Return org metadata + member list.

    Args:
        org_id: Canonical slug.

    Returns:
        Dict with org fields + members list.

    Raises:
        OrgNotFoundError: org_id does not exist.
    """
    conn = _open_conn()
    try:
        org_row = conn.execute(
            "SELECT org_id, display_name, status, trial_expires_at, "
            "platform_fee_paid_until, created_at, created_by_email "
            "FROM orgs WHERE org_id = ?",
            (org_id,),
        ).fetchone()

        if org_row is None:
            raise OrgNotFoundError(f"Org '{org_id}' not found")

        member_rows = conn.execute(
            "SELECT user_id, email, scope, joined_at "
            "FROM org_members WHERE org_id = ? ORDER BY joined_at",
            (org_id,),
        ).fetchall()
    finally:
        conn.close()

    members = [
        {
            "user_id": r["user_id"],
            "email": r["email"],
            "scope": r["scope"],
            "joined_at": r["joined_at"],
        }
        for r in member_rows
    ]

    return {
        "org_id": org_row["org_id"],
        "display_name": org_row["display_name"],
        "status": org_row["status"],
        "trial_expires_at": org_row["trial_expires_at"],
        "platform_fee_paid_until": org_row["platform_fee_paid_until"],
        "created_at": org_row["created_at"],
        "created_by_email": org_row["created_by_email"],
        "member_count": len(members),
        "members": members,
    }


def remove_member(org_id: str, user_id: str, actor_email: str) -> None:
    """Remove a member from an org.

    Self-remove is allowed (member removes themselves).
    Cannot remove the last org_admin.

    Args:
        org_id:      Org to remove from.
        user_id:     Member to remove.
        actor_email: Email of the requester (for audit log).

    Raises:
        OrgNotFoundError:   org_id doesn't exist.
        MemberNotFoundError: user_id not in org.
        LastAdminError:     user_id is the only org_admin.
    """
    conn = _open_conn()
    try:
        # Verify org exists
        org_row = conn.execute(
            "SELECT 1 FROM orgs WHERE org_id = ?", (org_id,)
        ).fetchone()
        if org_row is None:
            raise OrgNotFoundError(f"Org '{org_id}' not found")

        # Verify member exists
        member_row = conn.execute(
            "SELECT scope FROM org_members WHERE org_id = ? AND user_id = ?",
            (org_id, user_id),
        ).fetchone()
        if member_row is None:
            raise MemberNotFoundError(f"User '{user_id}' not in org '{org_id}'")

        # Guard: cannot remove last admin
        if member_row["scope"] == "org_admin":
            admin_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM org_members "
                "WHERE org_id = ? AND scope = 'org_admin'",
                (org_id,),
            ).fetchone()["cnt"]
            if admin_count <= 1:
                raise LastAdminError(
                    f"Cannot remove the last org_admin from '{org_id}'"
                )

        conn.execute(
            "DELETE FROM org_members WHERE org_id = ? AND user_id = ?",
            (org_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    audit_admin_action(
        scope="org.member_removed",
        org=org_id,
        sub=actor_email,
        endpoint="/v1/org/members",
    )


# =============================================================================
# Phase 9 P03 — Org Invite Flow
# =============================================================================

_VALID_INVITE_SCOPES: frozenset[str] = frozenset(
    {"org_admin", "cs", "marketing", "readonly"}
)


class AlreadyMemberError(Exception):
    """Invitee email already has an active membership in this org."""


class InviteInvalidError(Exception):
    """invite_id not found in org_invites table."""


class InviteExpiredError(Exception):
    """Invite found but expires_at is in the past (or set to 'REVOKED')."""


class InviteRevokedOrUsedError(Exception):
    """Invite redeemed_at is non-NULL (used timestamp or 'REVOKED' sentinel)."""


class InviteEmailMismatchError(Exception):
    """joiner_email does not match invitee_email on the invite row."""


class InvalidInviteScopeError(Exception):
    """Requested scope is not in _VALID_INVITE_SCOPES."""


class InviteAlreadyUsedError(Exception):
    """Admin tried to revoke an invite that was already redeemed or revoked."""


def _invite_expires_iso() -> str:
    """Return ISO timestamp 7 days from now."""
    dt = datetime.now(timezone.utc) + timedelta(days=7)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _build_invite_email_body(org_display_name: str, accept_url: str) -> str:
    """Return HTML body for Vietnamese org invite email."""
    return f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #1a56db;">Mekong Hub</h2>
  <p>Xin chào,</p>
  <p>Bạn được mời tham gia tổ chức <strong>{org_display_name}</strong> trên Mekong Hub.</p>
  <p>Nhấp vào liên kết bên dưới để chấp nhận lời mời. Liên kết có hiệu lực trong <strong>7 ngày</strong>:</p>
  <p style="margin: 24px 0;">
    <a href="{accept_url}"
       style="background-color: #1a56db; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 6px; display: inline-block;">
      Tham gia tổ chức
    </a>
  </p>
  <p style="color: #6b7280; font-size: 14px;">
    Hoặc copy URL: <code style="word-break: break-all;">{accept_url}</code>
  </p>
  <p style="color: #6b7280; font-size: 13px;">
    Nếu bạn không mong đợi lời mời này, hãy bỏ qua email này.
  </p>
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
  <p style="color: #9ca3af; font-size: 12px;">Mekong Hub — Nền tảng cho doanh nghiệp một người Việt Nam</p>
</body>
</html>""".strip()


def create_invite(
    org_id: str,
    invitee_email: str,
    scope: str,
    invited_by_user_id: str,
) -> dict[str, Any]:
    """Create (or reuse) an org invite and send a VN invitation email.

    Idempotent: if a pending (non-expired, non-redeemed) invite already
    exists for (org_id, invitee_email), reuses that row and resends the email.

    Args:
        org_id:               Target org slug.
        invitee_email:        Recipient email.
        scope:                Invite scope — org_admin|cs|marketing|readonly.
        invited_by_user_id:   org_members.user_id of the inviting admin.

    Returns:
        Dict with keys: invite_id, expires_at.

    Raises:
        InvalidInviteScopeError: scope not in allowed set.
        AlreadyMemberError:      invitee already an active member.
        OrgNotFoundError:        org_id does not exist.
    """
    if scope not in _VALID_INVITE_SCOPES:
        raise InvalidInviteScopeError(
            f"Scope '{scope}' not in {sorted(_VALID_INVITE_SCOPES)}"
        )

    now = _now_iso()
    conn = _open_conn()
    try:
        # Verify org exists
        org_row = conn.execute(
            "SELECT display_name FROM orgs WHERE org_id = ?", (org_id,)
        ).fetchone()
        if org_row is None:
            raise OrgNotFoundError(f"Org '{org_id}' not found")
        display_name = org_row["display_name"]

        # Check existing membership
        member_row = conn.execute(
            "SELECT 1 FROM org_members WHERE org_id = ? AND email = ?",
            (org_id, invitee_email.lower()),
        ).fetchone()
        if member_row is not None:
            raise AlreadyMemberError(
                f"'{invitee_email}' is already a member of org '{org_id}'"
            )

        # Check pending invite (idempotent reuse)
        pending = conn.execute(
            "SELECT invite_id, expires_at FROM org_invites "
            "WHERE org_id = ? AND invitee_email = ? "
            "AND redeemed_at IS NULL AND expires_at > ?",
            (org_id, invitee_email.lower(), now),
        ).fetchone()

        if pending is not None:
            invite_id = pending["invite_id"]
            expires_at = pending["expires_at"]
        else:
            invite_id = secrets.token_urlsafe(16)
            expires_at = _invite_expires_iso()
            conn.execute(
                """
                INSERT INTO org_invites
                    (invite_id, org_id, invitee_email, invited_by_user_id,
                     scope, expires_at, redeemed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    invite_id,
                    org_id,
                    invitee_email.lower(),
                    invited_by_user_id,
                    scope,
                    expires_at,
                    now,
                ),
            )
            conn.commit()
    finally:
        conn.close()

    # Mint a short-lived magic-link token for email delivery tunnel
    ml_token = magic_link_service.mint_token(
        invitee_email, purpose="join_invite", org_id=org_id, ttl_minutes=15
    )

    base_url = os.environ.get("MEKONG_PUBLIC_BASE_URL", "https://api.mekong.dev")
    accept_url = (
        f"{base_url}/v1/auth/verify"
        f"?token={ml_token}"
        f"&next=/v1/org/join%3Finvite%3D{invite_id}"
    )
    html_body = _build_invite_email_body(display_name, accept_url)
    subject = f"Tham gia {display_name} trên Mekong"

    try:
        resend_client.send_email(invitee_email, subject, html_body)
    except Exception:
        # Email failure is non-fatal — invite row already committed.
        # Admin can revoke + reinvite. Logged by caller's BackgroundTask.
        pass

    audit_admin_action(
        scope="org.invite_created",
        org=org_id,
        sub=invited_by_user_id,
        endpoint="/v1/org/invite",
    )

    return {"invite_id": invite_id, "expires_at": expires_at}


def accept_invite(invite_id: str, joiner_email: str) -> dict[str, Any]:
    """Atomically redeem an invite and add the joiner to org_members.

    Uses BEGIN IMMEDIATE to prevent TOCTOU race on the invite row.

    Args:
        invite_id:    PK from org_invites.
        joiner_email: Email from JWT sub claim (must match invitee_email).

    Returns:
        Dict with keys: org_id, user_id, scope.

    Raises:
        InviteInvalidError:      invite_id not found.
        InviteExpiredError:      expires_at in the past.
        InviteRevokedOrUsedError: redeemed_at is not NULL.
        InviteEmailMismatchError: joiner_email != invitee_email (case-insensitive).
    """
    now = _now_iso()
    conn = _open_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            "SELECT org_id, invitee_email, invited_by_user_id, scope, "
            "expires_at, redeemed_at "
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
            raise InviteEmailMismatchError(
                "Email does not match invite recipient"
            )

        org_id = row["org_id"]
        scope = row["scope"]
        invited_by = row["invited_by_user_id"]
        user_id = "opc_org_" + secrets.token_urlsafe(6)

        # Mark invite as redeemed
        conn.execute(
            "UPDATE org_invites SET redeemed_at = ? WHERE invite_id = ?",
            (now, invite_id),
        )

        # Add joiner to org_members (INSERT OR IGNORE guards against concurrent join)
        conn.execute(
            """
            INSERT OR IGNORE INTO org_members
                (org_id, user_id, email, scope, joined_at, invited_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (org_id, user_id, joiner_email.lower(), scope, now, invited_by),
        )

        conn.commit()
    except (InviteInvalidError, InviteExpiredError,
            InviteRevokedOrUsedError, InviteEmailMismatchError):
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    audit_admin_action(
        scope="org.invite_accepted",
        org=org_id,
        sub=joiner_email,
        endpoint="/v1/org/join",
    )

    return {"org_id": org_id, "user_id": user_id, "scope": scope}


def revoke_invite(invite_id: str, actor_email: str) -> None:
    """Soft-revoke an invite by setting redeemed_at = 'REVOKED'.

    Args:
        invite_id:   PK from org_invites.
        actor_email: Email of the org_admin issuing the revocation (for audit).

    Raises:
        InviteInvalidError:   invite_id not found.
        InviteAlreadyUsedError: invite was already redeemed or revoked.
    """
    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT org_id, redeemed_at FROM org_invites WHERE invite_id = ?",
            (invite_id,),
        ).fetchone()

        if row is None:
            raise InviteInvalidError(f"Invite '{invite_id}' not found")

        if row["redeemed_at"] is not None:
            raise InviteAlreadyUsedError("Invite already redeemed or revoked")

        conn.execute(
            "UPDATE org_invites SET redeemed_at = 'REVOKED' WHERE invite_id = ?",
            (invite_id,),
        )
        conn.commit()
        org_id = row["org_id"]
    finally:
        conn.close()

    audit_admin_action(
        scope="org.invite_revoked",
        org=org_id,
        sub=actor_email,
        endpoint="/v1/org/invites",
    )


def list_invites(org_id: str) -> list[dict[str, Any]]:
    """Return pending (non-expired, non-redeemed) invites for an org.

    Args:
        org_id: Org slug.

    Returns:
        List of dicts with invite_id, invitee_email, scope, expires_at, created_at.
    """
    now = _now_iso()
    conn = _open_conn()
    try:
        rows = conn.execute(
            "SELECT invite_id, invitee_email, scope, expires_at, created_at "
            "FROM org_invites "
            "WHERE org_id = ? AND redeemed_at IS NULL AND expires_at > ? "
            "ORDER BY created_at",
            (org_id, now),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "invite_id": r["invite_id"],
            "invitee_email": r["invitee_email"],
            "scope": r["scope"],
            "expires_at": r["expires_at"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
