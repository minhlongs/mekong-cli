# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Credit metering middleware for RaaS PEV pipeline.

Connects the credit system into Plan-Execute-Verify pipeline by tracking
per-task credit usage, enforcing balance checks, and aggregating usage stats.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
import uuid

from src.raas.credit_metering_models import (
    TASK_COSTS,
    InsufficientCreditsError,
    UsageEvent,
    UsageSummary,
)
from src.raas.credits import DB_PATH, CreditStore


class CreditMeter:
    """Middleware that enforces credit checks and records usage events."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._credit_store = CreditStore(db_path=db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS usage_events (
                        id           TEXT PRIMARY KEY,
                        tenant_id    TEXT NOT NULL,
                        mission_id   TEXT,
                        task_type    TEXT NOT NULL,
                        credits_used INTEGER NOT NULL,
                        timestamp    TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditMeter: failed to initialize DB: {exc}") from exc

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _period_filter(period: str) -> str:
        if period == "monthly":
            return datetime.now(timezone.utc).strftime("%Y-%m")
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def check_balance(self, tenant_id: str, complexity: str) -> None:
        """Verify tenant has enough credits for a given task type."""
        cost = TASK_COSTS.get(complexity)
        if cost is None:
            raise ValueError(f"Unknown task type '{complexity}'. Valid types: {list(TASK_COSTS)}")
        balance = self._credit_store.get_balance(tenant_id)
        if balance < cost:
            raise InsufficientCreditsError(tenant_id=tenant_id, required=cost, available=balance)

    def record_usage(
        self,
        tenant_id: str,
        task_type: str,
        credits_used: int,
        mission_id: Optional[str] = None,
    ) -> UsageEvent:
        """Log a usage event to the metering table."""
        event = UsageEvent(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            mission_id=mission_id,
            task_type=task_type,
            credits_used=credits_used,
            timestamp=self._now_iso(),
        )
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO usage_events (id, tenant_id, mission_id, task_type, credits_used, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (event.id, event.tenant_id, event.mission_id, event.task_type, event.credits_used, event.timestamp),
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditMeter.record_usage failed: {exc}") from exc
        return event

    def get_usage_summary(self, tenant_id: str, period: str = "daily") -> UsageSummary:
        """Aggregate credit usage for a tenant over a period."""
        if period not in ("daily", "monthly"):
            raise ValueError("period must be 'daily' or 'monthly'")

        like_pattern = f"{self._period_filter(period)}%"
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT task_type, SUM(credits_used) as total FROM usage_events "
                    "WHERE tenant_id = ? AND timestamp LIKE ? GROUP BY task_type",
                    (tenant_id, like_pattern),
                ).fetchall()
                count_row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM usage_events WHERE tenant_id = ? AND timestamp LIKE ?",
                    (tenant_id, like_pattern),
                ).fetchone()
                event_count = int(count_row["cnt"]) if count_row else 0
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditMeter.get_usage_summary failed: {exc}") from exc

        breakdown: Dict[str, int] = {row["task_type"]: int(row["total"]) for row in rows}
        return UsageSummary(
            tenant_id=tenant_id,
            period=period,
            total_credits_used=sum(breakdown.values()),
            event_count=event_count,
            breakdown=breakdown,
        )

    def list_events(self, tenant_id: str, limit: int = 50) -> List[UsageEvent]:
        """Return recent usage events for a tenant, newest first."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id, tenant_id, mission_id, task_type, credits_used, timestamp "
                    "FROM usage_events WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (tenant_id, limit),
                ).fetchall()
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditMeter.list_events failed: {exc}") from exc

        return [
            UsageEvent(
                id=row["id"],
                tenant_id=row["tenant_id"],
                mission_id=row["mission_id"],
                task_type=row["task_type"],
                credits_used=int(row["credits_used"]),
                timestamp=row["timestamp"],
            )
            for row in rows
        ]


__all__ = [
    "TASK_COSTS", "InsufficientCreditsError", "UsageEvent",
    "UsageSummary", "CreditMeter", "DB_PATH", "CreditStore",
]
