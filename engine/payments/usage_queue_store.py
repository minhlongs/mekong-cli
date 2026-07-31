"""SQLite fallback store for usage queue events."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional


class UsageQueueFallbackStore:
    """Persist usage events when primary metering storage is unavailable."""

    def __init__(self, sqlite_path: Optional[str] = None) -> None:
        if sqlite_path is None:
            sqlite_path = ".mekong/usage_buffer.db"
        self._sqlite_path = Path(sqlite_path)
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._sqlite_conn: Optional[sqlite3.Connection] = None

    def store(self, event: dict[str, Any]) -> None:
        """Store one event in SQLite fallback."""
        if self._sqlite_conn is None:
            self._sqlite_conn = sqlite3.connect(self._sqlite_path)
            self._init_schema()

        query = """
            INSERT INTO usage_buffer (key_id, tier, command, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        self._sqlite_conn.execute(
            query,
            (
                event["key_id"],
                event["tier"],
                event["command"],
                str(event["metadata"]),
                event["timestamp"],
            ),
        )
        self._sqlite_conn.commit()

    def _init_schema(self) -> None:
        """Initialize SQLite schema."""
        self._sqlite_conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                command TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._sqlite_conn.commit()


__all__ = ["UsageQueueFallbackStore"]
