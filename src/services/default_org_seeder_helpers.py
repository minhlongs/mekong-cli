# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Default org seeder constants, SQLite helpers, and prerequisite checks."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from src.services.sqlite_migrations import _db_path

FOUNDER_USER_ID = "opc_founder_001"
DEFAULT_ORG_ID = "default"
DEFAULT_ORG_DISPLAY_NAME = "Founder Default Org"
PLATFORM_FEE_PAID_UNTIL = "2099-12-31"
TRIAL_EXPIRES_AT = "2099-12-31"
SEED_RAW_PAYLOAD = '{"seed":"phase-9-p06"}'

_P02_TABLES = frozenset({"orgs", "org_members"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _synthetic_email(user_id: str) -> str:
    return f"{user_id}@pilot.mekong.local"


def _open_conn() -> sqlite3.Connection:
    """Open WAL-mode connection to pilot.db."""
    db = _db_path()
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _tables_present(conn: sqlite3.Connection) -> bool:
    """Return True if both P02 tables (orgs, org_members) exist."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?)",
        tuple(_P02_TABLES),
    ).fetchall()
    return {r["name"] for r in rows} == _P02_TABLES


def verify_prereqs() -> None:
    """Raise RuntimeError if environment or schema prerequisites are not met."""
    storage = os.getenv("MEKONG_PILOT_STORAGE", "").lower()
    if storage != "sqlite":
        raise RuntimeError(
            "MEKONG_PILOT_STORAGE must be 'sqlite' to run the seeder. "
            f"Current value: '{storage}'. "
            "Run: export MEKONG_PILOT_STORAGE=sqlite"
        )

    db = _db_path()
    if not db.exists():
        raise RuntimeError(
            f"pilot.db not found at {db}. "
            "Run scripts/migrate-jsonl-to-sqlite.py first."
        )

    conn = _open_conn()
    try:
        if not _tables_present(conn):
            raise RuntimeError(
                "P02 schema (orgs + org_members tables) not present in pilot.db. "
                "Ensure Phase 9 P02 has been deployed before running this seeder."
            )
    finally:
        conn.close()


__all__ = [
    "FOUNDER_USER_ID",
    "DEFAULT_ORG_ID",
    "DEFAULT_ORG_DISPLAY_NAME",
    "PLATFORM_FEE_PAID_UNTIL",
    "TRIAL_EXPIRES_AT",
    "SEED_RAW_PAYLOAD",
    "_P02_TABLES",
    "_now_iso",
    "_synthetic_email",
    "_open_conn",
    "_tables_present",
    "verify_prereqs",
    "_db_path",
]
