# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Worker Pool Models & Helpers — WorkerState, WorkerInfo, WorkerPoolStats, and PM2 sync helpers.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class WorkerState(Enum):
    """Worker lifecycle states."""

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERRORED = "errored"
    STOPPING = "stopping"


@dataclass
class WorkerInfo:
    """Information about a single worker."""

    id: str
    name: str
    capability: str  # builder, reviewer, tester, etc.
    state: WorkerState = WorkerState.IDLE
    pid: int | None = None
    cpu: float = 0.0
    memory_mb: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: str = ""
    started_at: str = ""


@dataclass
class WorkerPoolStats:
    """Aggregate statistics for the worker pool."""

    total_workers: int = 0
    idle_workers: int = 0
    busy_workers: int = 0
    offline_workers: int = 0
    avg_cpu: float = 0.0
    avg_memory_mb: float = 0.0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0


def apply_pm2_status_to_workers(workers: dict[str, WorkerInfo], stdout: str) -> None:
    """Parse PM2 jlist JSON and update worker state/metrics in place."""
    try:
        processes = json.loads(stdout)
    except json.JSONDecodeError:
        logger.exception("PM2 returned invalid JSON")
        return

    for p in processes:
        name = p.get("pm2_env", {}).get("name", "")
        if name not in workers:
            continue

        worker = workers[name]
        status = p.get("pm2_env", {}).get("status", "unknown")
        monit = p.get("monit", {})

        worker.pid = p.get("pid")
        worker.cpu = monit.get("cpu", 0.0)
        worker.memory_mb = monit.get("memory", 0) / 1024 / 1024

        if status == "online":
            if worker.state == WorkerState.OFFLINE:
                worker.state = WorkerState.IDLE
        elif status == "errored":
            worker.state = WorkerState.ERRORED
        elif status == "stopping":
            worker.state = WorkerState.STOPPING
        else:
            worker.state = WorkerState.OFFLINE

        worker.last_heartbeat = datetime.now().isoformat()


def compute_worker_pool_stats(workers: dict[str, WorkerInfo]) -> WorkerPoolStats:
    """Compute aggregate statistics for the worker pool."""
    stats = WorkerPoolStats(
        total_workers=len(workers),
        idle_workers=sum(1 for w in workers.values() if w.state == WorkerState.IDLE),
        busy_workers=sum(1 for w in workers.values() if w.state == WorkerState.BUSY),
        offline_workers=sum(1 for w in workers.values() if w.state == WorkerState.OFFLINE),
    )

    if workers:
        stats.avg_cpu = sum(w.cpu for w in workers.values()) / len(workers)
        stats.avg_memory_mb = sum(w.memory_mb for w in workers.values()) / len(workers)
        stats.total_tasks_completed = sum(w.tasks_completed for w in workers.values())
        stats.total_tasks_failed = sum(w.tasks_failed for w in workers.values())

    return stats


def classify_worker_health(workers: dict[str, WorkerInfo]) -> dict[str, Any]:
    """Classify workers into healthy, degraded, and unhealthy buckets."""
    health: dict[str, list[str]] = {"healthy": [], "degraded": [], "unhealthy": []}
    for worker in workers.values():
        if worker.state in [WorkerState.IDLE, WorkerState.BUSY]:
            health["healthy"].append(worker.name)
        elif worker.state == WorkerState.ERRORED:
            health["degraded"].append(worker.name)
        else:
            health["unhealthy"].append(worker.name)
    return health
