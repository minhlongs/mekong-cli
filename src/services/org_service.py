"""Org service — slug canonicalization, org creation, member management.

Backed by the SQLite orgs + org_members tables (Phase 9 P02 schema extension).
All writes are atomic via explicit transactions. Zero new pip dependencies.
"""
from __future__ import annotations

import json
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
