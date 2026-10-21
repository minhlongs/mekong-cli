# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org service models, exceptions, slug helpers, and SQLite connection utilities."""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema

# ---------- Constants ----------

RESERVED_SLUGS: frozenset[str] = frozenset({"default", "admin", "api", "www"})
_VALID_INVITE_SCOPES: frozenset[str] = frozenset(
    {"org_admin", "cs", "marketing", "readonly"}
)

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


def _txn(fn, *args, **kwargs) -> Any:
    """Run fn inside a transaction; rollback on exception."""
    conn = _open_conn()
    try:
        result = fn(conn, *args, **kwargs)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _trial_expires_iso() -> str:
    """Return ISO timestamp 14 days from now."""
    dt = datetime.now(timezone.utc) + timedelta(days=14)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _invite_expires_iso() -> str:
    """Return ISO timestamp 7 days from now."""
    dt = datetime.now(timezone.utc) + timedelta(days=7)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


# ---------- Slug helpers ----------


def canonicalize_slug(display_name: str) -> str:
    """Normalize a display name to a URL-safe slug."""
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
