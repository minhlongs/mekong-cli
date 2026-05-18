"""Magic-link token mint/verify/rate-limit/purge service.

Backed by the SQLite magic_link_tokens table (Phase 8 P05 schema extension).
DB connection opened fresh per call — lightweight, WAL-mode safe, no shared state.

Rate-limit strategy: SQLite COUNT query on (email, created_at) with index —
no in-memory dict needed; DB is single ACID source of truth.
NOTE: Rate limit is per-process effective only when all requests hit the same
SQLite DB file. For single-host M1 gateway this is always true.

JWT minting re-uses admin_token_service.decode_jwt signing helpers via PyJWT
directly (MEKONG_JWT_SECRET, HS256, 24h TTL).
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema

# ---------- Custom exceptions ----------


class MagicLinkInvalid(Exception):
    """Token not found in DB."""


class MagicLinkExpired(Exception):
    """Token found but expires_at is in the past."""


class MagicLinkAlreadyRedeemed(Exception):
    """Token found but redeemed_at is not NULL."""


# ---------- Internal helpers ----------


def _db_path() -> Path:
    return _state.CONFIG_DIR / "pilot.db"


def _open_conn() -> sqlite3.Connection:
    """Open a WAL-mode SQLite connection; create schema if DB is fresh."""
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


def _parse_iso(iso: str) -> datetime:
    """Parse ISO 8601 string (with or without trailing Z) to UTC datetime."""
    iso = iso.rstrip("Z")
    if "." in iso:
        dt = datetime.fromisoformat(iso)
    else:
        dt = datetime.fromisoformat(iso)
    return dt.replace(tzinfo=timezone.utc)


# ---------- Public API ----------


def mint_token(
    email: str,
    purpose: str,
    org_id: str | None = None,
    ttl_minutes: int = 15,
) -> str:
    """Generate a 32-byte urlsafe token and persist to magic_link_tokens.

    Args:
        email:       Recipient email address.
        purpose:     Intent — "login" | "signup" | "join_invite".
        org_id:      Non-null only for "join_invite" tokens.
        ttl_minutes: Minutes until token expires (default 15).

    Returns:
        The raw token string (43-char urlsafe base64).
    """
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=ttl_minutes)).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    created_at = now.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    conn = _open_conn()
    try:
        conn.execute(
            """
            INSERT INTO magic_link_tokens
                (token, email, purpose, org_id, expires_at, redeemed_at, created_at)
            VALUES (?, ?, ?, ?, ?, NULL, ?)
            """,
            (token, email, purpose, org_id, expires_at, created_at),
        )
        conn.commit()
    finally:
        conn.close()

    return token


def verify_and_redeem(token: str) -> dict[str, Any]:
    """Atomically verify and mark a token as redeemed.

    Args:
        token: Raw token string from URL query param.

    Returns:
        Dict with keys: email, purpose, org_id.

    Raises:
        MagicLinkInvalid:        Token not found.
        MagicLinkExpired:        Token found but past expires_at.
        MagicLinkAlreadyRedeemed: Token already redeemed.
    """
    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT token, email, purpose, org_id, expires_at, redeemed_at "
            "FROM magic_link_tokens WHERE token = ?",
            (token,),
        ).fetchone()

        if row is None:
            raise MagicLinkInvalid("Token not found")

        if row["redeemed_at"] is not None:
            raise MagicLinkAlreadyRedeemed("Token already redeemed")

        expires_dt = _parse_iso(row["expires_at"])
        if datetime.now(timezone.utc) > expires_dt:
            raise MagicLinkExpired("Token expired")

        # Atomic redeem — UPDATE WHERE redeemed_at IS NULL ensures single-use
        redeemed_at = _now_iso()
        rowcount = conn.execute(
            "UPDATE magic_link_tokens SET redeemed_at = ? "
            "WHERE token = ? AND redeemed_at IS NULL",
            (redeemed_at, token),
        ).rowcount
        conn.commit()

        if rowcount == 0:
            # Race condition: another request redeemed it between SELECT and UPDATE
            raise MagicLinkAlreadyRedeemed("Token already redeemed (race)")

        return {
            "email": row["email"],
            "purpose": row["purpose"],
            "org_id": row["org_id"],
        }
    finally:
        conn.close()


def check_rate_limit(email: str, window_hours: int = 1, max_count: int = 5) -> bool:
    """Return True if email is under the rate limit cap.

    Uses SQLite COUNT on indexed (email, created_at) — O(log n) per query.
    Window boundary is computed from current UTC time minus window_hours.

    Args:
        email:        Email to check.
        window_hours: Rolling window size (default 1 hour).
        max_count:    Max tokens allowed in the window (default 5).

    Returns:
        True if count < max_count (request is allowed).
        False if count >= max_count (request should be silently dropped).
    """
    window_start = (
        datetime.now(timezone.utc) - timedelta(hours=window_hours)
    ).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM magic_link_tokens "
            "WHERE email = ? AND created_at > ?",
            (email, window_start),
        ).fetchone()
        count = row["cnt"] if row else 0
    finally:
        conn.close()

    return count < max_count


def purge_expired(grace_hours: int = 24) -> int:
    """Delete tokens expired more than grace_hours ago.

    Designed to be called from check-org-trials.py cron (Phase 9 GC).
    Returns the number of rows deleted.

    Args:
        grace_hours: Hours after expiry before deletion (default 24).
    """
    cutoff = (
        datetime.now(timezone.utc) - timedelta(hours=grace_hours)
    ).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    conn = _open_conn()
    try:
        cursor = conn.execute(
            "DELETE FROM magic_link_tokens WHERE expires_at < ?",
            (cutoff,),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def mint_jwt_for_email(email: str) -> tuple[str, str]:
    """Mint a 24h JWT for email. Resolves scopes from org_members if present.

    Scope resolution:
    - If org_members table exists and has rows for email → union of member.scope
    - Otherwise → scopes=["none"], allowed_orgs=[]

    JWT claims: sub, scopes, allowed_orgs, iat, exp (HS256, MEKONG_JWT_SECRET).

    Args:
        email: Verified email from magic-link.

    Returns:
        Tuple of (jwt_string, expires_at_iso).

    Raises:
        RuntimeError: MEKONG_JWT_SECRET not set.
    """
    secret = os.getenv("MEKONG_JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "MEKONG_JWT_SECRET env var is required for JWT minting. "
            "Set it in your launchd plist EnvironmentVariables."
        )

    scopes: list[str] = []
    allowed_orgs: list[str] = []

    conn = _open_conn()
    try:
        # org_members table may not exist in Phase 9 P01 — handle gracefully
        try:
            rows = conn.execute(
                "SELECT org_id, scope FROM org_members WHERE email = ?",
                (email,),
            ).fetchall()
            for row in rows:
                if row["org_id"] and row["org_id"] not in allowed_orgs:
                    allowed_orgs.append(row["org_id"])
                if row["scope"] and row["scope"] not in scopes:
                    scopes.append(row["scope"])
        except sqlite3.OperationalError:
            # org_members table doesn't exist yet (added in P02)
            pass
    finally:
        conn.close()

    if not scopes:
        scopes = ["none"]

    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=24)
    exp_iso = exp.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    payload = {
        "sub": email,
        "scopes": scopes,
        "allowed_orgs": allowed_orgs,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, exp_iso
