# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Task Router — Intelligent task routing with priority queue.
"""

from __future__ import annotations

import heapq
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .task_router_models import (
    Task,
    TaskPriority,
    TaskQueueStats,
    TaskStatus,
    append_mission_to_journal,
    read_pending_from_journal,
)

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"
JOURNAL_DIR = MEKONG_DIR / "journal"
JOURNAL_FILE = JOURNAL_DIR / "missions.json"

JOURNAL_DIR.mkdir(parents=True, exist_ok=True)


class TaskRouter:
    """Routes tasks to available workers based on capability and load."""

    def __init__(self, max_size: int = 1000) -> None:
        self._queue: list[Task] = []
        self._active_tasks: dict[str, Task] = {}
        self._completed_tasks: list[Task] = []
        self._dead_letter_queue: list[Task] = []
        self._max_size = max_size
        self._task_history: list[dict] = []

    def enqueue(
        self,
        description: str,
        priority: str = "MEDIUM",
        capability: str = "general",
        payload: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> Task:
        """Add a task to the priority queue."""
        priority_enum = TaskPriority[priority.upper()]
        task = Task(
            description=description,
            priority_value=priority_enum.value,
            capability=capability,
            payload=payload or {},
            max_retries=max_retries,
        )
        if len(self._queue) >= self._max_size:
            logger.warning(f"[TaskRouter] Queue at capacity ({self._max_size}), dropping task")
            return task

        heapq.heappush(self._queue, task)
        logger.info(f"[TaskRouter] Enqueued {task.task_id}: {description[:50]} (priority={priority})")
        self._task_history.append(
            {"event": "enqueue", "task_id": task.task_id, "timestamp": datetime.now().isoformat()}
        )
        return task

    def get_next_task(self, capability: str | None = None) -> Task | None:
        """Get the highest priority task that matches the capability."""
        for i, task in enumerate(self._queue):
            if capability is None or task.capability == capability:
                self._queue.pop(i)
                heapq.heapify(self._queue)
                task.status = TaskStatus.ACTIVE
                task.started_at = datetime.now().isoformat()
                self._active_tasks[task.task_id] = task
                logger.info(f"[TaskRouter] Dequeued {task.task_id} for {task.capability}")
                return task
        return None

    def complete(self, task_id: str, result: Any = None) -> None:
        """Mark a task as completed."""
        if task_id not in self._active_tasks:
            logger.warning(f"[TaskRouter] Task {task_id} not found in active tasks")
            return
        task = self._active_tasks.pop(task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        self._completed_tasks.append(task)
        if len(self._completed_tasks) > 100:
            self._completed_tasks = self._completed_tasks[-100:]
        logger.info(f"[TaskRouter] Completed {task_id}")
        self._log_mission(task)

    def fail(self, task_id: str, error: str) -> Task | None:
        """Mark a task as failed. Returns task for retry or None if max retries exceeded."""
        if task_id not in self._active_tasks:
            logger.warning(f"[TaskRouter] Task {task_id} not found in active tasks")
            return None
        task = self._active_tasks.pop(task_id)
        task.error = error
        task.retry_count += 1
        logger.warning(f"[TaskRouter] Failed {task_id}: {error} (retry {task.retry_count}/{task.max_retries})")

        if task.retry_count >= task.max_retries:
            task.status = TaskStatus.FAILED
            self._dead_letter_queue.append(task)
            logger.error(f"[TaskRouter] Task {task_id} moved to dead letter queue")
            self._log_mission(task)
            return None

        task.status = TaskStatus.PENDING
        task.started_at = None
        task.assigned_to = None
        heapq.heappush(self._queue, task)
        return task

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending or active task."""
        for i, task in enumerate(self._queue):
            if task.task_id == task_id:
                self._queue.pop(i)
                heapq.heapify(self._queue)
                task.status = TaskStatus.CANCELLED
                logger.info(f"[TaskRouter] Cancelled {task_id}")
                return True
        if task_id in self._active_tasks:
            task = self._active_tasks.pop(task_id)
            task.status = TaskStatus.CANCELLED
            logger.info(f"[TaskRouter] Cancelled active task {task_id}")
            return True
        return False

    def get_stats(self) -> TaskQueueStats:
        """Get queue statistics."""
        return TaskQueueStats(
            pending=len(self._queue),
            active=len(self._active_tasks),
            completed=len(self._completed_tasks),
            failed=len(self._dead_letter_queue),
            critical_pending=sum(1 for t in self._queue if t.priority_value == TaskPriority.CRITICAL.value),
        )

    def get_queue_snapshot(self) -> list[dict]:
        return [t.to_dict() for t in sorted(self._queue)]

    def get_active_tasks(self) -> list[dict]:
        return [t.to_dict() for t in self._active_tasks.values()]

    def get_dead_letter_queue(self) -> list[dict]:
        return [t.to_dict() for t in self._dead_letter_queue]

    def clear_completed(self) -> int:
        count = len(self._completed_tasks)
        self._completed_tasks.clear()
        logger.info(f"[TaskRouter] Cleared {count} completed tasks")
        return count

    def _log_mission(self, task: Task) -> None:
        append_mission_to_journal(JOURNAL_FILE, task)

    def load_pending_from_journal(self) -> int:
        tasks = read_pending_from_journal(JOURNAL_FILE)
        for task in tasks:
            heapq.heappush(self._queue, task)
        if tasks or JOURNAL_FILE.exists():
            logger.info(f"[TaskRouter] Reloaded {len(tasks)} pending tasks from journal")
        return len(tasks)
