# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Dispatcher Models & Selection — LoadBalanceStrategy, DispatchResult, and worker selection helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .worker_pool import WorkerInfo, WorkerState


class LoadBalanceStrategy(Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_FIRST = "capability_first"


@dataclass
class DispatchResult:
    """Result of a task dispatch."""

    success: bool
    task_id: str
    worker_name: str | None = None
    error: str | None = None
    duration_ms: int = 0


def select_round_robin_worker(
    workers: list[WorkerInfo],
    current_index: int,
    capability: str | None = None,
) -> tuple[WorkerInfo | None, int]:
    """Select an idle worker matching capability using round-robin."""
    if not workers:
        return None, current_index

    available = [
        w
        for w in workers
        if w.state == WorkerState.IDLE and (capability is None or w.capability == capability)
    ]
    if not available:
        return None, current_index

    next_index = (current_index + 1) % len(available)
    return available[next_index], next_index


def select_least_loaded_worker(
    workers: list[WorkerInfo],
    capability: str | None = None,
) -> WorkerInfo | None:
    """Select an idle worker matching capability with the lowest CPU load."""
    if not workers:
        return None

    available = [
        w
        for w in workers
        if w.state == WorkerState.IDLE and (capability is None or w.capability == capability)
    ]
    if not available:
        return None

    return min(available, key=lambda w: w.cpu)


def format_dispatcher_stats(
    pool_stats: Any,
    queue_stats: Any,
    total_dispatched: int,
    strategy_value: str,
) -> dict[str, Any]:
    """Format dispatcher statistics dictionary."""
    return {
        "workers": {
            "total": pool_stats.total_workers,
            "idle": pool_stats.idle_workers,
            "busy": pool_stats.busy_workers,
            "offline": pool_stats.offline_workers,
            "avg_cpu": round(pool_stats.avg_cpu, 2),
            "avg_memory_mb": round(pool_stats.avg_memory_mb, 1),
        },
        "queue": {
            "pending": queue_stats.pending,
            "active": queue_stats.active,
            "completed": queue_stats.completed,
            "failed": queue_stats.failed,
            "critical_pending": queue_stats.critical_pending,
        },
        "dispatch": {
            "total_dispatched": total_dispatched,
            "strategy": strategy_value,
        },
    }
