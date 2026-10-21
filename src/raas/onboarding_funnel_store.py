# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Onboarding funnel event storage and analytics for RaaS."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from src.raas.onboarding_funnel_models import (
    _DB_PATH,
    _DDL,
    FUNNEL_STEPS,
    FunnelData,
    FunnelStep,
)

logger = logging.getLogger(__name__)


class OnboardingFunnelStore:
    """SQLite store for onboarding funnel analytics."""

    FUNNEL_STEPS = FUNNEL_STEPS

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
            raise RuntimeError(f"Failed to initialize onboarding events DB: {exc}") from exc

    def track_event(
        self,
        user_id: str,
        workspace_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an onboarding funnel event."""
        now = datetime.now(timezone.utc).isoformat()
        event_data = event_data or {}

        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO onboarding_events (user_id, workspace_id, event_type, event_data, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, workspace_id, event_type, json.dumps(event_data), now),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to track onboarding event: {exc}") from exc

        logger.debug("Tracked onboarding event: %s for user=%s workspace=%s", event_type, user_id, workspace_id)

    def get_funnel_data(self, days: int = 30) -> FunnelData:
        """Get aggregated funnel data for the last N days."""
        now = datetime.now(timezone.utc)
        period_start = (now - timedelta(days=days)).isoformat()
        period_end = now.isoformat()

        try:
            with self._connect() as conn:
                steps = self._get_step_counts(conn, period_start)
        except sqlite3.OperationalError:
            steps = []

        overall_conversion = 0.0
        if steps and steps[0].count > 0:
            last_step = steps[-1] if steps else None
            if last_step:
                overall_conversion = (last_step.count / steps[0].count) * 100

        initial_count = steps[0].count if steps else 0
        for step in steps:
            if initial_count > 0:
                step.conversion_rate = (step.count / initial_count) * 100

        return FunnelData(
            period_start=period_start,
            period_end=period_end,
            total_days=days,
            steps=steps,
            overall_conversion_rate=overall_conversion,
        )

    def _get_step_counts(self, conn: sqlite3.Connection, since: str) -> List[FunnelStep]:
        steps = []
        for idx, step_name in enumerate(self.FUNNEL_STEPS):
            row = conn.execute(
                "SELECT COUNT(*) as total_count, COUNT(DISTINCT user_id) as unique_users "
                "FROM onboarding_events WHERE event_type = ? AND created_at >= ?",
                (step_name, since),
            ).fetchone()
            if row:
                steps.append(
                    FunnelStep(
                        step_name=step_name,
                        step_order=idx,
                        count=row["total_count"] or 0,
                        unique_users=row["unique_users"] or 0,
                    )
                )
        return steps

    def get_user_funnel_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get funnel progress for a specific user."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT event_type, workspace_id, created_at, event_data "
                    "FROM onboarding_events WHERE user_id = ? ORDER BY created_at ASC",
                    (user_id,),
                ).fetchall()
                return [
                    {
                        "event_type": row["event_type"],
                        "workspace_id": row["workspace_id"],
                        "created_at": row["created_at"],
                        "event_data": json.loads(row["event_data"]) if row["event_data"] else {},
                    }
                    for row in rows
                ]
        except sqlite3.OperationalError:
            return []

    def get_workspace_funnel_events(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all funnel events for a workspace."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT user_id, event_type, created_at, event_data "
                    "FROM onboarding_events WHERE workspace_id = ? ORDER BY created_at ASC",
                    (workspace_id,),
                ).fetchall()
                return [
                    {
                        "user_id": row["user_id"],
                        "event_type": row["event_type"],
                        "created_at": row["created_at"],
                        "event_data": json.loads(row["event_data"]) if row["event_data"] else {},
                    }
                    for row in rows
                ]
        except sqlite3.OperationalError:
            return []


__all__ = ["_DB_PATH", "_DDL", "FunnelStep", "FunnelData", "OnboardingFunnelStore"]
