# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/signals/local_store.py — SQLite write-through recorder for MissionEvent.

Design:
  - WAL mode: concurrent reads while writing
  - Schema migration on first init (idempotent)
  - Default DB path: {repo_root}/data/signals.sqlite (gitignored)
  - Writes are synchronous; reads via offline.py use read-only connection
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from src.core.signals.events import MissionEvent

log = logging.getLogger(__name__)

# Default path — override via SIGNALS_DB_PATH env var
# parents[3] = repo root (src/core/signals/local_store.py → repo_root/data/signals.sqlite)
_DEFAULT_DB = Path(__file__).parents[3] / "data" / "signals.sqlite"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS missions (
    mission_id   TEXT    NOT NULL PRIMARY KEY,
    agent_id     TEXT    NOT NULL,
    credits_used INTEGER NOT NULL DEFAULT 0,
    success      INTEGER NOT NULL DEFAULT 0,  -- SQLite bool: 0/1
    duration_ms  INTEGER NOT NULL DEFAULT 0,
    ts           TEXT    NOT NULL,
    user_id_hash TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_missions_agent_ts ON missions (agent_id, ts);
"""


def _get_db_path() -> Path:
    import os
    return Path(os.environ.get("SIGNALS_DB_PATH", str(_DEFAULT_DB)))


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def write_event(event: MissionEvent, db_path: Optional[Path] = None) -> bool:
    """
    Write a MissionEvent to SQLite. Returns True on success.
    Swallows exceptions — never breaks the caller.
    """
    path = db_path or _get_db_path()
    try:
        conn = _connect(path)
        conn.execute(
            """
            INSERT OR REPLACE INTO missions
                (mission_id, agent_id, credits_used, success, duration_ms, ts, user_id_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.mission_id,
                event.agent_id,
                event.credits_used,
                int(event.success),
                event.duration_ms,
                event.ts,
                event.user_id_hash,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("signals.local_store write failed: %s", exc)
        return False


def row_count(db_path: Optional[Path] = None) -> int:
    """Return total rows in missions table. 0 if DB does not exist."""
    path = db_path or _get_db_path()
    if not path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(path))
        (count,) = conn.execute("SELECT COUNT(*) FROM missions").fetchone()
        conn.close()
        return int(count)
    except Exception:  # noqa: BLE001
        return 0
