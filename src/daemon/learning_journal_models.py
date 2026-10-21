# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Learning Journal Models & Persistence — MissionEntry, DailyStats, and disk I/O helpers.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MissionEntry:
    """A single mission entry in the journal."""

    task_id: str
    description: str
    status: str  # success, failed, cancelled
    created_at: str
    started_at: str | None
    completed_at: str | None
    duration_ms: int
    worker: str | None
    capability: str
    priority: str
    error: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "worker": self.worker,
            "capability": self.capability,
            "priority": self.priority,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class DailyStats:
    """Aggregated stats for a single day."""

    date: str
    total_missions: int = 0
    successful: int = 0
    failed: int = 0
    cancelled: int = 0
    avg_duration_ms: float = 0.0
    total_duration_ms: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "total_missions": self.total_missions,
            "successful": self.successful,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "total_duration_ms": self.total_duration_ms,
            "success_rate": round(self.success_rate, 2),
        }


def load_missions_from_file(journal_file: Path) -> list[MissionEntry]:
    """Load mission entries from JSON file."""
    if not journal_file.exists():
        return []
    try:
        data = json.loads(journal_file.read_text())
        missions = [
            MissionEntry(
                task_id=m["task_id"],
                description=m["description"],
                status=m["status"],
                created_at=m.get("created_at", ""),
                started_at=m.get("started_at"),
                completed_at=m.get("completed_at"),
                duration_ms=m.get("duration_ms", 0),
                worker=m.get("worker"),
                capability=m.get("capability", "general"),
                priority=m.get("priority", "MEDIUM"),
                error=m.get("error"),
                metadata=m.get("metadata", {}),
            )
            for m in data.get("missions", [])
        ]
        logger.info(f"[LearningJournal] Loaded {len(missions)} missions")
        return missions
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"[LearningJournal] Failed to load journal: {e}")
        return []


def load_daily_stats_from_file(stats_file: Path) -> dict[str, DailyStats]:
    """Load daily stats dictionary from JSON file."""
    if not stats_file.exists():
        return {}
    try:
        data = json.loads(stats_file.read_text())
        return {
            date: DailyStats(
                date=date,
                total_missions=s.get("total_missions", 0),
                successful=s.get("successful", 0),
                failed=s.get("failed", 0),
                cancelled=s.get("cancelled", 0),
                avg_duration_ms=s.get("avg_duration_ms", 0),
                total_duration_ms=s.get("total_duration_ms", 0),
                success_rate=s.get("success_rate", 0),
            )
            for date, s in data.get("stats", {}).items()
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"[LearningJournal] Failed to load daily stats: {e}")
        return {}


def load_insights_from_file(insights_file: Path) -> list[dict]:
    """Load learning insights from JSON file."""
    if not insights_file.exists():
        return []
    try:
        return json.loads(insights_file.read_text()).get("insights", [])
    except (json.JSONDecodeError, KeyError):
        return []
