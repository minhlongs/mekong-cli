# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Free Tier Usage Tracker — ROIaaS Phase 6."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.lib.free_tier_schema import _DDL, DB_PATH, FreeTierUsage


class FreeTierTracker:
    """SQLite-based free tier usage tracker for analytics."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with closing(self._connect()) as conn:
                conn.executescript(_DDL)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"FreeTierTracker: DB init failed: {exc}") from exc

    def track_command(
        self, key_id: str, command: str, command_cost: int = 1,
        email: Optional[str] = None, session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Track a command execution for free tier user."""
        try:
            now = datetime.now(timezone.utc)
            iso_now = now.isoformat()
            if session_id is None:
                session_id = f"{key_id}-{now.strftime('%Y%m%d%H%M%S')}"
            with closing(self._connect()) as conn:
                conn.execute(
                    """INSERT INTO free_tier_usage
                       (key_id, email, command, command_cost, session_id, created_at, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (key_id, email, command, command_cost, session_id, iso_now, json.dumps(metadata or {})),
                )
                conn.execute(
                    """INSERT INTO free_tier_sessions
                       (session_id, key_id, started_at, last_activity, commands_count, total_credits)
                       VALUES (?, ?, ?, ?, 1, ?)
                       ON CONFLICT (session_id) DO UPDATE SET
                       last_activity = excluded.last_activity,
                       commands_count = free_tier_sessions.commands_count + 1,
                       total_credits = free_tier_sessions.total_credits + excluded.total_credits""",
                    (session_id, key_id, iso_now, iso_now, command_cost),
                )
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_usage_summary(self, key_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a free tier user."""
        try:
            with closing(self._connect()) as conn:
                row = conn.execute(
                    """SELECT COUNT(*) as total_commands, COALESCE(SUM(command_cost), 0) as total_credits,
                        COUNT(DISTINCT DATE(created_at)) as active_days, COUNT(DISTINCT command) as unique_commands
                       FROM free_tier_usage WHERE key_id = ? AND created_at >= datetime('now', ?)""",
                    (key_id, f"-{days} days"),
                ).fetchone()
                if not row:
                    return {"total_commands": 0, "total_credits": 0, "active_days": 0, "unique_commands": 0}
                top = conn.execute(
                    """SELECT command, SUM(command_cost) as credits FROM free_tier_usage
                       WHERE key_id = ? AND created_at >= datetime('now', ?)
                       GROUP BY command ORDER BY credits DESC LIMIT 5""",
                    (key_id, f"-{days} days"),
                ).fetchall()
                return {
                    "total_commands": row["total_commands"], "total_credits": row["total_credits"],
                    "active_days": row["active_days"], "unique_commands": row["unique_commands"],
                    "top_commands": [{"command": r["command"], "credits": r["credits"]} for r in top],
                }
        except sqlite3.Error:
            return {"total_commands": 0, "total_credits": 0, "active_days": 0, "unique_commands": 0, "top_commands": []}

    def get_unsynced_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            with closing(self._connect()) as conn:
                rows = conn.execute(
                    "SELECT * FROM free_tier_usage WHERE synced = FALSE AND sync_attempted < 3 ORDER BY created_at LIMIT ?",
                    (limit,),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error:
            return []

    def mark_synced(self, record_ids: List[int]) -> int:
        try:
            with closing(self._connect()) as conn:
                ph = ",".join("?" * len(record_ids))
                cur = conn.execute(f"UPDATE free_tier_usage SET synced = TRUE WHERE id IN ({ph})", record_ids)
                conn.commit()
                return cur.rowcount
        except sqlite3.Error:
            return 0

    def increment_sync_attempts(self, record_ids: List[int]) -> int:
        try:
            with closing(self._connect()) as conn:
                ph = ",".join("?" * len(record_ids))
                cur = conn.execute(f"UPDATE free_tier_usage SET sync_attempted = sync_attempted + 1 WHERE id IN ({ph})", record_ids)
                conn.commit()
                return cur.rowcount
        except sqlite3.Error:
            return 0

    def clear_old_records(self, days: int = 90) -> int:
        try:
            with closing(self._connect()) as conn:
                cur = conn.execute("DELETE FROM free_tier_usage WHERE created_at < datetime('now', ?) AND synced = TRUE", (f"-{days} days",))
                conn.commit()
                return cur.rowcount
        except sqlite3.Error:
            return 0


_tracker: Optional[FreeTierTracker] = None


def get_tracker(db_path: Optional[Path] = None) -> FreeTierTracker:
    global _tracker
    if _tracker is None or (db_path and _tracker.db_path != db_path):
        _tracker = FreeTierTracker(db_path or DB_PATH)
    return _tracker


def track_free_tier_command(key_id: str, command: str, command_cost: int = 1, email: Optional[str] = None, session_id: Optional[str] = None) -> bool:
    return get_tracker().track_command(key_id=key_id, command=command, command_cost=command_cost, email=email, session_id=session_id)


def get_free_tier_summary(key_id: str, days: int = 30) -> Dict[str, Any]:
    return get_tracker().get_usage_summary(key_id, days)


__all__ = [
    "FreeTierTracker", "FreeTierUsage", "get_tracker",
    "track_free_tier_command", "get_free_tier_summary",
]
