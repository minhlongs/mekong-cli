# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and priority enum for Priority Task Queue."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class TaskPriority(IntEnum):
    """Task priority levels (lower number = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass(order=True)
class QueuedTask:
    """A task in the priority queue."""

    priority: int
    enqueued_at: float = field(compare=True)
    task_id: str = field(compare=False, default="")
    goal: str = field(compare=False, default="")
    payload: dict[str, Any] = field(compare=False, default_factory=dict)
    attempt: int = field(compare=False, default=0)
    max_attempts: int = field(compare=False, default=3)
    source: str = field(compare=False, default="manual")


@dataclass
class DeadLetterEntry:
    """A task that exhausted all retry attempts."""

    task: QueuedTask
    final_error: str
    failed_at: float = field(default_factory=time.time)
