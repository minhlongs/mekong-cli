# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Engagement event storage for retention tracking."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional

from src.raas.engagement_store_models import (
    _DB_PATH, _DDL, DailyActivity, EngagementEvent, HealthSnapshot, StreakData, _cutoff_date,
)

logger = logging.getLogger(__name__)


class EngagementStore:
    """SQLite store for engagement tracking data."""

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(_DDL)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to init engagement DB: {exc}") from exc

    def _fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(query, params).fetchall()

    def _fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(query, params).fetchone()

    def track_event(
        self, user_id: str, workspace_id: str, event_type: str, event_date: Optional[str] = None
    ) -> None:
        now = datetime.now(timezone.utc)
        event_date = event_date or now.strftime("%Y-%m-%d")
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO engagement_events (user_id, workspace_id, event_type, event_date, created_at) "
                    "VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, event_type, event_date) "
                    "DO UPDATE SET event_count = event_count + 1",
                    (user_id, workspace_id, event_type, event_date, now.isoformat()),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to track event: {exc}") from exc

    def get_user_events(self, user_id: str, days: int = 30) -> List[EngagementEvent]:
        rows = self._fetchall(
            "SELECT user_id, workspace_id, event_type, event_count, event_date, created_at "
            "FROM engagement_events WHERE user_id = ? AND event_date >= ? ORDER BY event_date DESC",
            (user_id, _cutoff_date(days)),
        )
        return [
            EngagementEvent(r["user_id"], r["workspace_id"], r["event_type"], r["event_count"], r["event_date"], r["created_at"])
            for r in rows
        ]

    def get_daily_event_counts(self, user_id: str, days: int = 30) -> List[DailyActivity]:
        rows = self._fetchall(
            "SELECT event_date, SUM(event_count) as total, GROUP_CONCAT(DISTINCT event_type) as types "
            "FROM engagement_events WHERE user_id = ? AND event_date >= ? GROUP BY event_date ORDER BY event_date DESC",
            (user_id, _cutoff_date(days)),
        )
        return [DailyActivity(r["event_date"], r["total"], (r["types"] or "").split(",")) for r in rows]

    def get_active_dates(self, user_id: str, days: int = 30) -> List[str]:
        rows = self._fetchall(
            "SELECT DISTINCT event_date FROM engagement_events WHERE user_id = ? AND event_date >= ? ORDER BY event_date",
            (user_id, _cutoff_date(days)),
        )
        return [r["event_date"] for r in rows]

    def upsert_streak(self, data: StreakData) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_active_date, streak_started, grace_used, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET "
                "current_streak=excluded.current_streak, longest_streak=excluded.longest_streak, "
                "last_active_date=excluded.last_active_date, streak_started=excluded.streak_started, "
                "grace_used=excluded.grace_used, updated_at=excluded.updated_at",
                (data.user_id, data.current_streak, data.longest_streak, data.last_active_date, data.streak_started, data.grace_used, now),
            )
            conn.commit()

    def get_streak(self, user_id: str) -> Optional[StreakData]:
        row = self._fetchone("SELECT * FROM user_streaks WHERE user_id = ?", (user_id,))
        return StreakData(row["user_id"], row["current_streak"], row["longest_streak"], row["last_active_date"], row["streak_started"], row["grace_used"]) if row else None

    def save_health_snapshot(
        self, workspace_id: str, score: int, grade: str, components: Dict[str, float], snapshot_date: Optional[str] = None
    ) -> None:
        now = datetime.now(timezone.utc)
        snapshot_date = snapshot_date or now.strftime("%Y-%m-%d")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO workspace_health_snapshots (workspace_id, score, grade, components, snapshot_date, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(workspace_id, snapshot_date) "
                "DO UPDATE SET score=excluded.score, grade=excluded.grade, components=excluded.components",
                (workspace_id, score, grade, json.dumps(components), snapshot_date, now.isoformat()),
            )
            conn.commit()

    def get_health_history(self, workspace_id: str, days: int = 30) -> List[HealthSnapshot]:
        rows = self._fetchall(
            "SELECT * FROM workspace_health_snapshots WHERE workspace_id = ? AND snapshot_date >= ? ORDER BY snapshot_date DESC",
            (workspace_id, _cutoff_date(days)),
        )
        return [HealthSnapshot(r["workspace_id"], r["score"], r["grade"], json.loads(r["components"]), r["snapshot_date"]) for r in rows]

    def dismiss_nudge(self, user_id: str, nudge_id: str, reason: str = "manual") -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO nudge_dismissals (user_id, nudge_id, dismissed_at, reason) VALUES (?, ?, ?, ?)",
                    (user_id, nudge_id, datetime.now(timezone.utc).isoformat(), reason),
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def get_dismissed_nudge_ids(self, user_id: str) -> List[str]:
        return [r["nudge_id"] for r in self._fetchall("SELECT nudge_id FROM nudge_dismissals WHERE user_id = ?", (user_id,))]

    def get_distinct_users(self, workspace_id: str) -> List[str]:
        return [r["user_id"] for r in self._fetchall("SELECT DISTINCT user_id FROM engagement_events WHERE workspace_id = ?", (workspace_id,))]

    def get_workspace_event_stats(self, workspace_id: str, days: int = 30) -> Dict[str, int]:
        row = self._fetchone(
            "SELECT COUNT(DISTINCT event_date) as active_days, COUNT(*) as total_events FROM engagement_events WHERE workspace_id = ? AND event_date >= ?",
            (workspace_id, _cutoff_date(days)),
        )
        return {"active_days": (row["active_days"] if row else 0) or 0, "total_events": (row["total_events"] if row else 0) or 0}

    def get_workspace_feature_count(self, workspace_id: str, days: int = 30) -> int:
        row = self._fetchone("SELECT COUNT(DISTINCT event_type) as types FROM engagement_events WHERE workspace_id = ? AND event_date >= ?", (workspace_id, _cutoff_date(days)))
        return row["types"] if row else 0

    def get_workspace_user_count(self, workspace_id: str) -> int:
        row = self._fetchone("SELECT COUNT(DISTINCT user_id) as cnt FROM engagement_events WHERE workspace_id = ?", (workspace_id,))
        return row["cnt"] if row else 0

    def get_billing_balance(self, workspace_id: str) -> Optional[int]:
        try:
            row = self._fetchone("SELECT balance FROM credit_accounts WHERE workspace_id = ?", (workspace_id,))
            return row["balance"] if row else None
        except sqlite3.OperationalError:
            return None


__all__ = ["_DB_PATH", "_DDL", "EngagementEvent", "DailyActivity", "StreakData", "HealthSnapshot", "EngagementStore", "_cutoff_date"]
