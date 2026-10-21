# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Magic-link token mint/verify/rate-limit/purge service."""
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

import src.api.vn_pilot_state as _state
from src.services.magic_link_store import (
    MagicLinkAlreadyRedeemed,
    MagicLinkExpired,
    MagicLinkInvalid,
    _db_path,
    _now_iso,
    _open_conn,
    _parse_iso,
)
from src.services.sqlite_migrations import ensure_schema


def mint_token(
    email: str,
    purpose: str,
    org_id: str | None = None,
    ttl_minutes: int = 15,
) -> str:
    """Generate a 32-byte urlsafe token and persist to magic_link_tokens."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=ttl_minutes)).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    created_at = now.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    conn = _open_conn()
    try:
        conn.execute(
            "INSERT INTO magic_link_tokens (token, email, purpose, org_id, expires_at, redeemed_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, NULL, ?)",
            (token, email, purpose, org_id, expires_at, created_at),
        )
        conn.commit()
    finally:
        conn.close()
    return token


def verify_and_redeem(token: str) -> dict[str, Any]:
    """Atomically verify and mark a token as redeemed."""
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
        if datetime.now(timezone.utc) > _parse_iso(row["expires_at"]):
            raise MagicLinkExpired("Token expired")

        rowcount = conn.execute(
            "UPDATE magic_link_tokens SET redeemed_at = ? WHERE token = ? AND redeemed_at IS NULL",
            (_now_iso(), token),
        ).rowcount
        conn.commit()
        if rowcount == 0:
            raise MagicLinkAlreadyRedeemed("Token already redeemed (race)")
        return {"email": row["email"], "purpose": row["purpose"], "org_id": row["org_id"]}
    finally:
        conn.close()


def check_rate_limit(email: str, window_hours: int = 1, max_count: int = 5) -> bool:
    """Return True if email is under the rate limit cap."""
    window_start = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM magic_link_tokens WHERE email = ? AND created_at > ?",
            (email, window_start),
        ).fetchone()
        count = row["cnt"] if row else 0
    finally:
        conn.close()
    return count < max_count


def purge_expired(grace_hours: int = 24) -> int:
    """Delete tokens expired more than grace_hours ago."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=grace_hours)).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    conn = _open_conn()
    try:
        cursor = conn.execute("DELETE FROM magic_link_tokens WHERE expires_at < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def mint_jwt_for_email(email: str) -> tuple[str, str]:
    """Mint a 24h JWT for email. Resolves scopes from org_members if present."""
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
        try:
            for row in conn.execute("SELECT org_id, scope FROM org_members WHERE email = ?", (email,)).fetchall():
                if row["org_id"] and row["org_id"] not in allowed_orgs:
                    allowed_orgs.append(row["org_id"])
                if row["scope"] and row["scope"] not in scopes:
                    scopes.append(row["scope"])
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()

    if not scopes:
        scopes = ["none"]
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=24)
    payload = {
        "sub": email,
        "scopes": scopes,
        "allowed_orgs": allowed_orgs,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256"), exp.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


__all__ = [
    "MagicLinkInvalid",
    "MagicLinkExpired",
    "MagicLinkAlreadyRedeemed",
    "_db_path",
    "_open_conn",
    "_now_iso",
    "_parse_iso",
    "_state",
    "ensure_schema",
    "mint_token",
    "verify_and_redeem",
    "check_rate_limit",
    "purge_expired",
    "mint_jwt_for_email",
]
