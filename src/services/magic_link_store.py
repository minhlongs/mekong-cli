# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Magic-link token exceptions and SQLite connection/timestamp helpers."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema


class MagicLinkInvalid(Exception):
    """Token not found in DB."""


class MagicLinkExpired(Exception):
    """Token found but expires_at is in the past."""


class MagicLinkAlreadyRedeemed(Exception):
    """Token found but redeemed_at is not NULL."""


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
    dt = datetime.fromisoformat(iso)
    return dt.replace(tzinfo=timezone.utc)


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
]
