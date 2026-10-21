# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Tracker — unified CLI usage tracking (SQLite + event bus + anomaly detection)."""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.anomaly_detector import (
    AnomalyCategory, AnomalyType, UsageAnomalyDetector, get_detector as _get_detector,
)
from src.core.event_bus import EventBus, EventType, Subscriber, get_event_bus
from src.usage.usage_metering_mixin import _UsageMeteringMixin
from src.usage.usage_models import (
    FREE_TIER_LIMITS, MAX_FUTURE_DRIFT, SQLITE_RETRY_BASE_DELAY, SQLITE_RETRY_MAX,
    WAL_CHECKPOINT_INTERVAL, DailyUsage, UsageEvent, UsageEventType, UsageReport,
)
from src.usage.usage_sqlite import UsageSqliteMixin

logger = logging.getLogger(__name__)


class UsageTracker(UsageSqliteMixin, _UsageMeteringMixin):
    """SQLite-backed usage tracker with schema migrations, WAL management,
    future-timestamp validation, and event-bus metering.
    """

    SCHEMA_VERSION: int = 1

    def __init__(
        self, db_path: Optional[Path] = None, baseline_file: Optional[str] = None
    ) -> None:
        if db_path is None:
            db_path = Path.home() / ".mekong" / "raas" / "tenants.db"
        self._db_path = Path(db_path)
        self._baseline_file = baseline_file
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), timeout=10, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.row_factory = sqlite3.Row
        self._op_counter: int = 0
        self._lock = threading.Lock()
        self._init_schema_version_table()
        self._run_migrations()
        self._init_tables()

    def get_daily_usage(self, license_key: str, date: Optional[str] = None) -> DailyUsage:
        """Get daily usage for a license key."""
        license_key_hash = self._hash_license_key(license_key)
        target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cmd_rows = self._conn.execute(
            "SELECT event_name, SUM(units) as count FROM usage_events WHERE license_key_hash = ? AND event_type = 'command' AND substr(timestamp, 1, 10) = ? GROUP BY event_name",
            (license_key_hash, target_date),
        ).fetchall()
        agent_rows = self._conn.execute(
            "SELECT event_name, SUM(units) as count FROM usage_events WHERE license_key_hash = ? AND event_type = 'agent_call' AND substr(timestamp, 1, 10) = ? GROUP BY event_name",
            (license_key_hash, target_date),
        ).fetchall()
        pipeline_row = self._conn.execute(
            "SELECT SUM(units) as count FROM usage_events WHERE license_key_hash = ? AND event_type = 'pipeline_run' AND substr(timestamp, 1, 10) = ?",
            (license_key_hash, target_date),
        ).fetchone()

        command_breakdown = {r["event_name"]: (r["count"] or 0) for r in cmd_rows}
        agent_breakdown = {r["event_name"]: (r["count"] or 0) for r in agent_rows}
        return DailyUsage(
            date=target_date,
            total_commands=sum(command_breakdown.values()),
            total_agents=sum(agent_breakdown.values()),
            total_pipelines=pipeline_row["count"] or 0 if pipeline_row else 0,
            command_breakdown=command_breakdown,
            agent_breakdown=agent_breakdown,
        )

    def is_free_tier_exceeded(self, license_key: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Check if free tier limit exceeded."""
        usage = self.get_daily_usage(license_key, date)
        if usage.total_commands >= FREE_TIER_LIMITS["commands_per_day"]:
            return {"exceeded": True, "reason": f"Command limit exceeded: {usage.total_commands}/{FREE_TIER_LIMITS['commands_per_day']}"}
        if usage.total_agents >= FREE_TIER_LIMITS["agents_per_day"]:
            return {"exceeded": True, "reason": f"Agent limit exceeded: {usage.total_agents}/{FREE_TIER_LIMITS['agents_per_day']}"}
        if usage.total_pipelines >= FREE_TIER_LIMITS["pipelines_per_day"]:
            return {"exceeded": True, "reason": f"Pipeline limit exceeded: {usage.total_pipelines}/{FREE_TIER_LIMITS['pipelines_per_day']}"}
        return {"exceeded": False}

    def get_free_tier_remaining(self, usage: DailyUsage) -> Dict[str, int]:
        """Get remaining free tier quota."""
        return {
            "commands_remaining": max(0, FREE_TIER_LIMITS["commands_per_day"] - usage.total_commands),
            "agents_remaining": max(0, FREE_TIER_LIMITS["agents_per_day"] - usage.total_agents),
            "pipelines_remaining": max(0, FREE_TIER_LIMITS["pipelines_per_day"] - usage.total_pipelines),
        }

    def get_usage_report(self, license_key: str, days: int = 7) -> UsageReport:
        """Get multi-day usage report."""
        today = datetime.now(timezone.utc)
        daily_reports: List[DailyUsage] = []
        total_commands = total_agents = total_pipelines = 0
        for i in range(days):
            daily = self.get_daily_usage(license_key, (today - timedelta(days=i)).strftime("%Y-%m-%d"))
            daily_reports.append(daily)
            total_commands += daily.total_commands
            total_agents += daily.total_agents
            total_pipelines += daily.total_pipelines
        return UsageReport(
            license_key_hash=self._hash_license_key(license_key),
            period_days=days, total_commands=total_commands,
            total_agents=total_agents, total_pipelines=total_pipelines,
            daily_reports=daily_reports,
        )

    def close(self) -> None:
        """Close database connection, running a final WAL checkpoint."""
        try:
            self._wal_checkpoint()
        except Exception:
            pass
        self._conn.close()


_tracker: Optional[UsageTracker] = None
_tracker_lock = threading.Lock()
_metering: Optional[UsageTracker] = None
_metering_lock = threading.Lock()


def get_tracker() -> UsageTracker:
    """Get or create the global SQLite-backed usage tracker (thread-safe)."""
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = UsageTracker()
    return _tracker


def get_rate_limiter() -> Any:
    """Get global rate limiter instance."""
    from src.auth.rate_limiter import get_rate_limiter as _get_rl
    return _get_rl()


def get_metering() -> UsageTracker:
    """Get or create the global metering (UsageTracker) singleton."""
    global _metering
    if _metering is None:
        with _metering_lock:
            if _metering is None:
                _metering = UsageTracker()
    return _metering


def reset_metering() -> None:
    global _metering
    _metering = None


def reset_tracker() -> None:
    global _tracker
    _tracker = None


UsageMetering = UsageTracker

__all__ = [
    "UsageTracker", "UsageMetering", "get_tracker", "get_rate_limiter",
    "DailyUsage", "UsageReport", "UsageEvent", "UsageEventType",
    "EventBus", "EventType", "Subscriber", "get_event_bus",
    "AnomalyCategory", "AnomalyType", "UsageAnomalyDetector", "_get_detector",
    "get_metering", "reset_metering", "reset_tracker",
    "FREE_TIER_LIMITS", "MAX_FUTURE_DRIFT", "WAL_CHECKPOINT_INTERVAL",
    "SQLITE_RETRY_MAX", "SQLITE_RETRY_BASE_DELAY",
]
