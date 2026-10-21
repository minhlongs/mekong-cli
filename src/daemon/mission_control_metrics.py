# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mission Control Journal & Queue Helpers — Metrics calculation and dispatch queue.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.core.file_lock import locked_read

logger = logging.getLogger(__name__)


@dataclass
class WorkerStatus:
    """Status of a single worker daemon."""

    name: str
    status: str  # online, offline, errored, stopping
    cpu: float
    memory_mb: float
    uptime_ms: int
    restarts: int
    pid: int | None = None


@dataclass
class DaemonMetrics:
    """Aggregate metrics for the daemon army."""

    total_workers: int = 0
    online_workers: int = 0
    throughput_per_minute: float = 0.0
    success_rate: float = 0.0
    queue_depth: int = 0
    avg_response_time_ms: float = 0.0
    last_updated: str = ""


@dataclass
class QueueItem:
    """Item in the dispatch queue."""

    task_id: str
    description: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str  # pending, active, completed, failed
    assigned_to: str | None = None
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None


def _get_mc() -> Any:
    """Lazy reference to mission_control facade for monkeypatch compatibility."""
    from . import mission_control
    return mission_control


def _read_missions_from_journal(log_on_error: bool = True, log_msg: str = "") -> list[dict] | None:
    """Read missions list from journal file, returning None on error or missing file."""
    mc = _get_mc()
    journal_file = mc.JOURNAL_DIR / "missions.json"
    if not journal_file.exists():
        return None
    try:
        with locked_read(journal_file) as f:
            content = f.read()
            data = json.loads(content) if content else {}
        return data.get("missions", [])
    except (json.JSONDecodeError, KeyError, ValueError):
        if log_on_error and log_msg:
            logger.exception(log_msg)
        return []


def _calculate_throughput(missions: list[dict] | None = None) -> float:
    """Calculate tasks completed per minute from journal."""
    if missions is None:
        loaded = _read_missions_from_journal(True, "Failed to calculate throughput")
        if loaded is None:
            return 0.0
        missions = loaded

    if not missions:
        return 0.0

    now = datetime.now()
    recent = [
        m
        for m in missions
        if m.get("completed_at")
        and (now - datetime.fromisoformat(m["completed_at"])).total_seconds() < 3600
    ]
    if not recent:
        return 0.0

    first_time = datetime.fromisoformat(recent[0]["completed_at"])
    last_time = datetime.fromisoformat(recent[-1]["completed_at"])
    span_minutes = max((last_time - first_time).total_seconds() / 60, 1)
    return round(len(recent) / span_minutes, 2)


def _calculate_success_rate(missions: list[dict] | None = None) -> float:
    """Calculate success rate from journal."""
    if missions is None:
        mc = _get_mc()
        journal_file = mc.JOURNAL_DIR / "missions.json"
        if not journal_file.exists():
            return 100.0
        try:
            with locked_read(journal_file) as f:
                content = f.read()
                data = json.loads(content) if content else {}
            missions = data.get("missions", [])
        except (json.JSONDecodeError, KeyError):
            logger.exception("Failed to calculate success rate")
            return 0.0

    if not missions:
        return 100.0

    recent = missions[-100:]
    successful = sum(1 for m in recent if m.get("status") == "success")
    return round(successful / len(recent) * 100, 2)


def _get_queue_depth(missions: list[dict] | None = None) -> int:
    """Get current queue depth from journal."""
    if missions is None:
        loaded = _read_missions_from_journal(False)
        if loaded is None:
            return 0
        missions = loaded

    return sum(1 for m in missions if m.get("status") in ["pending", "active"])


def _calculate_avg_response_time(missions: list[dict] | None = None) -> float:
    """Calculate average response time from journal."""
    if missions is None:
        loaded = _read_missions_from_journal(False)
        if loaded is None:
            return 0.0
        missions = loaded

    if not missions:
        return 0.0

    recent = missions[-50:]
    times = [m.get("duration_ms", 0) for m in recent if m.get("duration_ms")]
    if not times:
        return 0.0

    return round(sum(times) / len(times), 2)
