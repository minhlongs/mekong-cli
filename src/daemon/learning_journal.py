# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Learning Journal — Mission telemetry logging and stats aggregation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .learning_journal_models import (
    DailyStats,
    MissionEntry,
    load_daily_stats_from_file,
    load_insights_from_file,
    load_missions_from_file,
)

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"
JOURNAL_DIR = MEKONG_DIR / "journal"
JOURNAL_FILE = JOURNAL_DIR / "missions.json"
STATS_FILE = JOURNAL_DIR / "daily_stats.json"
INSIGHTS_FILE = JOURNAL_DIR / "insights.json"

JOURNAL_DIR.mkdir(parents=True, exist_ok=True)


class LearningJournal:
    """Persistent journal for mission telemetry and learning."""

    def __init__(self, retention_days: int = 90) -> None:
        self.retention_days = retention_days
        self._missions: list[MissionEntry] = []
        self._daily_stats: dict[str, DailyStats] = {}
        self._insights: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load journal from disk."""
        self._missions = load_missions_from_file(JOURNAL_FILE)
        self._daily_stats = load_daily_stats_from_file(STATS_FILE)
        self._insights = load_insights_from_file(INSIGHTS_FILE)

    def _save(self) -> None:
        """Save journal to disk."""
        JOURNAL_FILE.write_text(
            json.dumps({"missions": [m.to_dict() for m in self._missions[-1000:]]}, indent=2)
        )
        STATS_FILE.write_text(
            json.dumps({"stats": {d: s.to_dict() for d, s in self._daily_stats.items()}}, indent=2)
        )
        INSIGHTS_FILE.write_text(json.dumps({"insights": self._insights[-100:]}, indent=2))

    def log_mission(
        self,
        task_id: str,
        description: str,
        status: str,
        duration_ms: int = 0,
        worker: str | None = None,
        capability: str = "general",
        priority: str = "MEDIUM",
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a mission to the journal."""
        now = datetime.now().isoformat()
        entry = MissionEntry(
            task_id=task_id,
            description=description,
            status=status,
            created_at=now,
            started_at=now if status != "cancelled" else None,
            completed_at=now if status in ["success", "failed"] else None,
            duration_ms=duration_ms,
            worker=worker,
            capability=capability,
            priority=priority,
            error=error,
            metadata=metadata or {},
        )
        self._missions.append(entry)
        logger.info(f"[LearningJournal] Logged mission {task_id} ({status})")
        self._update_daily_stats(entry)
        self._save()
        self._archive_old_entries()

    def _update_daily_stats(self, entry: MissionEntry) -> None:
        """Update daily stats for the entry's date."""
        date = entry.created_at[:10]
        stats = self._daily_stats.setdefault(date, DailyStats(date=date))
        stats.total_missions += 1
        if entry.status == "success":
            stats.successful += 1
        elif entry.status == "failed":
            stats.failed += 1
        elif entry.status == "cancelled":
            stats.cancelled += 1
        stats.total_duration_ms += entry.duration_ms
        stats.avg_duration_ms = stats.total_duration_ms / stats.total_missions
        stats.success_rate = (
            (stats.successful / stats.total_missions * 100) if stats.total_missions > 0 else 0
        )

    def _archive_old_entries(self) -> None:
        """Archive entries older than retention period."""
        cutoff_str = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        original_count = len(self._missions)
        self._missions = [m for m in self._missions if m.created_at > cutoff_str]
        if len(self._missions) < original_count:
            logger.info(f"[LearningJournal] Archived {original_count - len(self._missions)} old entries")

    def get_missions(
        self, limit: int = 100, status: str | None = None, capability: str | None = None
    ) -> list[dict]:
        """Get missions from the journal."""
        missions = self._missions
        if status:
            missions = [m for m in missions if m.status == status]
        if capability:
            missions = [m for m in missions if m.capability == capability]
        missions = sorted(missions, key=lambda m: m.created_at, reverse=True)
        return [m.to_dict() for m in missions[:limit]]

    def get_daily_stats(self, days: int = 30) -> list[dict]:
        """Get daily stats for the last N days."""
        cutoff_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stats = [s.to_dict() for date, s in self._daily_stats.items() if date >= cutoff_str]
        return sorted(stats, key=lambda s: s["date"], reverse=True)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        total = len(self._missions)
        if total == 0:
            return {"total_missions": 0, "success_rate": 0, "avg_duration_ms": 0, "total_duration_ms": 0}
        successful = sum(1 for m in self._missions if m.status == "success")
        total_duration = sum(m.duration_ms for m in self._missions)
        return {
            "total_missions": total,
            "successful": successful,
            "failed": sum(1 for m in self._missions if m.status == "failed"),
            "cancelled": sum(1 for m in self._missions if m.status == "cancelled"),
            "success_rate": round(successful / total * 100, 2),
            "avg_duration_ms": round(total_duration / total, 2),
            "total_duration_ms": total_duration,
        }

    def add_insight(
        self, insight_type: str, description: str, data: dict[str, Any] | None = None
    ) -> None:
        """Add a learning insight."""
        self._insights.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": insight_type,
                "description": description,
                "data": data or {},
            }
        )
        self._save()

    def get_insights(self, limit: int = 20) -> list[dict]:
        """Get recent insights."""
        return self._insights[-limit:]

    def clear(self) -> None:
        """Clear all journal data."""
        self._missions.clear()
        self._daily_stats.clear()
        self._insights.clear()
        self._save()
        logger.info("[LearningJournal] Cleared all data")
