# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Task Router Models & Persistence — Task, TaskPriority, TaskStatus, and journal I/O.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.file_lock import locked_read, locked_read_write

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskStatus(Enum):
    """Task lifecycle states."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=True)
class Task:
    """A task to be dispatched to a worker."""

    priority_value: int = field(compare=True)
    created_at: float = field(compare=True, default_factory=datetime.now().timestamp)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = field(compare=False, default="")
    capability: str = field(compare=False, default="general")
    payload: dict[str, Any] = field(compare=False, default_factory=dict)
    status: TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    assigned_to: str | None = field(compare=False, default=None)
    started_at: str | None = field(compare=False, default=None)
    completed_at: str | None = field(compare=False, default=None)
    error: str | None = field(compare=False, default=None)
    retry_count: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)

    def __post_init__(self) -> None:
        if isinstance(self.priority_value, TaskPriority):
            self.priority_value = self.priority_value.value

    @property
    def priority(self) -> str:
        """Get priority as string."""
        return TaskPriority(self.priority_value).name

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority,
            "capability": self.capability,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "retry_count": self.retry_count,
        }


@dataclass
class TaskQueueStats:
    """Statistics for the task queue."""

    pending: int = 0
    active: int = 0
    completed: int = 0
    failed: int = 0
    critical_pending: int = 0


def append_mission_to_journal(journal_file: Path, task: Task) -> None:
    """Append a completed/failed task entry to the missions journal under file lock."""
    journal_entry = task.to_dict()
    journal_entry["duration_ms"] = 0
    if task.started_at and task.completed_at:
        try:
            start = datetime.fromisoformat(task.started_at)
            end = datetime.fromisoformat(task.completed_at)
            journal_entry["duration_ms"] = int((end - start).total_seconds() * 1000)
        except ValueError:
            pass

    with locked_read_write(journal_file) as f:
        missions = []
        try:
            content = f.read()
            if content:
                data = json.loads(content)
                missions = data.get("missions", [])
        except (json.JSONDecodeError, KeyError):
            missions = []

        missions.append(journal_entry)
        if len(missions) > 1000:
            missions = missions[-1000:]

        f.seek(0)
        f.write(json.dumps({"missions": missions}, indent=2))
        f.truncate()


def read_pending_from_journal(journal_file: Path) -> list[Task]:
    """Read incomplete tasks from journal file for crash recovery."""
    if not journal_file.exists():
        return []

    try:
        with locked_read(journal_file) as f:
            content = f.read()
            data = json.loads(content) if content else {}
        missions = data.get("missions", [])

        tasks: list[Task] = []
        for m in missions:
            if m.get("status") in ["pending", "active"]:
                task = Task(
                    task_id=m.get("task_id", str(uuid.uuid4())[:8]),
                    description=m.get("description", ""),
                    priority_value=TaskPriority[m.get("priority", "MEDIUM")].value,
                    capability=m.get("capability", "general"),
                    payload=m.get("payload", {}),
                    retry_count=m.get("retry_count", 0),
                )
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.assigned_to = None
                tasks.append(task)
        return tasks
    except (json.JSONDecodeError, KeyError, ValueError):
        logger.exception("Failed to load journal")
        return []
