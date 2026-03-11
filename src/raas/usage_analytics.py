"""Per-tenant usage analytics aggregation for RaaS.

Aggregates credit consumption and mission metrics over time windows.
Provides daily/weekly/monthly rollups for dashboard display.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"


@dataclass
class DailyUsage:
    """Credits consumed per day for a tenant."""

    date: str  # YYYY-MM-DD
    credits_used: int
    missions_count: int
    missions_completed: int
    missions_failed: int


@dataclass
class TenantUsageSummary:
    """Aggregated usage summary for a tenant."""

    tenant_id: str
    period_start: str
    period_end: str
    total_credits_used: int
    total_missions: int
    missions_completed: int
    missions_failed: int
    daily_breakdown: List[DailyUsage] = field(default_factory=list)
    complexity_breakdown: Dict[str, int] = field(default_factory=dict)


class UsageAnalytics:
    """Aggregates usage metrics from SQLite mission and transaction records.

    Reads from the shared tenants.db populated by CreditStore and MissionStore.
    All queries are read-only — no writes here.
    """

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def get_tenant_summary(
        self,
        tenant_id: str,
        days: int = 30,
    ) -> TenantUsageSummary:
        """Compute usage summary for the last N days.

        Args:
            tenant_id: Tenant to aggregate.
            days: Look-back window in days (default 30).

        Returns:
            Aggregated summary including daily breakdown.
        """
        now = datetime.now(timezone.utc)
        period_start = (now - timedelta(days=days)).isoformat()
        period_end = now.isoformat()

        try:
            with self._connect() as conn:
                daily = self._daily_breakdown(conn, tenant_id, period_start)
                complexity = self._complexity_breakdown(conn, tenant_id, period_start)
                totals = self._totals(conn, tenant_id, period_start)
        except sqlite3.OperationalError:
            # Tables may not exist yet on fresh installs
            daily, complexity, totals = [], {}, {"total": 0, "done": 0, "failed": 0}

        return TenantUsageSummary(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            total_credits_used=totals.get("credits_used", 0),
            total_missions=totals.get("total", 0),
            missions_completed=totals.get("done", 0),
            missions_failed=totals.get("failed", 0),
            daily_breakdown=daily,
            complexity_breakdown=complexity,
        )

    def _daily_breakdown(
        self,
        conn: sqlite3.Connection,
        tenant_id: str,
        since: str,
    ) -> List[DailyUsage]:
        rows = conn.execute(
            """
            SELECT
                substr(created_at, 1, 10)  AS day,
                SUM(credits_cost)          AS credits_used,
                COUNT(*)                   AS missions_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN status = 'failed'    THEN 1 ELSE 0 END) AS failed
            FROM missions
            WHERE tenant_id = ? AND created_at >= ?
            GROUP BY day
            ORDER BY day ASC
            """,
            (tenant_id, since),
        ).fetchall()
        return [
            DailyUsage(
                date=r["day"],
                credits_used=r["credits_used"] or 0,
                missions_count=r["missions_count"] or 0,
                missions_completed=r["completed"] or 0,
                missions_failed=r["failed"] or 0,
            )
            for r in rows
        ]

    def _complexity_breakdown(
        self,
        conn: sqlite3.Connection,
        tenant_id: str,
        since: str,
    ) -> Dict[str, int]:
        rows = conn.execute(
            """
            SELECT complexity, COUNT(*) AS cnt
            FROM missions
            WHERE tenant_id = ? AND created_at >= ?
            GROUP BY complexity
            """,
            (tenant_id, since),
        ).fetchall()
        return {r["complexity"]: r["cnt"] for r in rows}

    def _totals(
        self,
        conn: sqlite3.Connection,
        tenant_id: str,
        since: str,
    ) -> Dict[str, int]:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(credits_cost), 0)                         AS credits_used,
                COUNT(*)                                                AS total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)  AS done,
                SUM(CASE WHEN status = 'failed'    THEN 1 ELSE 0 END)  AS failed
            FROM missions
            WHERE tenant_id = ? AND created_at >= ?
            """,
            (tenant_id, since),
        ).fetchone()
        if row is None:
            return {"credits_used": 0, "total": 0, "done": 0, "failed": 0}
        return {
            "credits_used": row["credits_used"] or 0,
            "total": row["total"] or 0,
            "done": row["done"] or 0,
            "failed": row["failed"] or 0,
        }

    def get_recent_activity(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Return the most recent mission records as dicts for dashboard display.

        Args:
            tenant_id: Tenant to query.
            limit: Max records to return (default 10).

        Returns:
            List of mission dicts ordered by created_at desc.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, goal, status, complexity, credits_cost,
                           created_at, completed_at
                    FROM missions
                    WHERE tenant_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (tenant_id, limit),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return []
