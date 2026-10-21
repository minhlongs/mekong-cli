# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Priority Task Queue.

Temporal-inspired task queue with priority levels, backpressure,
and dead letter queue (DLQ) for failed tasks.
"""

from __future__ import annotations

import heapq
import time
from typing import Any

from .queue_models import DeadLetterEntry, QueuedTask, TaskPriority


class PriorityTaskQueue:
    """Priority-based task queue with DLQ.

    Temporal pattern: workers poll the queue for tasks.
    Higher priority tasks are dispatched first.
    Failed tasks exceeding max_attempts go to DLQ.
    """

    def __init__(self, max_size: int = 1000) -> None:
        self._heap: list[QueuedTask] = []
        self._dlq: list[DeadLetterEntry] = []
        self._max_size = max_size
        self._total_enqueued: int = 0
        self._total_completed: int = 0

    def enqueue(
        self,
        task_id: str,
        goal: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        payload: dict[str, Any] | None = None,
        max_attempts: int = 3,
        source: str = "manual",
    ) -> QueuedTask | None:
        """Add a task to the queue. Returns None if queue is full (backpressure)."""
        if self._max_size > 0 and len(self._heap) >= self._max_size:
            return None

        task = QueuedTask(
            priority=priority.value,
            enqueued_at=time.time(),
            task_id=task_id,
            goal=goal,
            payload=payload or {},
            max_attempts=max_attempts,
            source=source,
        )
        heapq.heappush(self._heap, task)
        self._total_enqueued += 1
        return task

    def poll(self) -> QueuedTask | None:
        """Remove and return the highest-priority task. Returns None if empty."""
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def peek(self) -> QueuedTask | None:
        """View the highest-priority task without removing it."""
        return self._heap[0] if self._heap else None

    def mark_completed(self, task: QueuedTask) -> None:
        """Record task completion for metrics."""
        self._total_completed += 1

    def mark_failed(self, task: QueuedTask, error: str) -> bool:
        """Handle task failure. Re-enqueues or moves to DLQ."""
        task.attempt += 1
        if task.attempt < task.max_attempts:
            heapq.heappush(self._heap, task)
            return True
        self._dlq.append(DeadLetterEntry(task=task, final_error=error))
        return False

    def get_dlq(self) -> list[DeadLetterEntry]:
        """Return all dead letter entries."""
        return list(self._dlq)

    def retry_from_dlq(self, task_id: str) -> bool:
        """Move a task from DLQ back to queue for retry."""
        for i, entry in enumerate(self._dlq):
            if entry.task.task_id == task_id:
                task = entry.task
                task.attempt = 0
                heapq.heappush(self._heap, task)
                self._dlq.pop(i)
                return True
        return False

    @property
    def size(self) -> int:
        """Current number of tasks in the queue."""
        return len(self._heap)

    @property
    def dlq_size(self) -> int:
        """Number of tasks in the dead letter queue."""
        return len(self._dlq)

    @property
    def is_empty(self) -> bool:
        """Check if queue has no pending tasks."""
        return len(self._heap) == 0

    def stats(self) -> dict[str, Any]:
        """Return queue statistics."""
        return {
            "pending": self.size,
            "dlq": self.dlq_size,
            "total_enqueued": self._total_enqueued,
            "total_completed": self._total_completed,
            "completion_rate": (
                (self._total_completed / self._total_enqueued * 100)
                if self._total_enqueued > 0
                else 0.0
            ),
        }

    def clear(self) -> None:
        """Remove all tasks from queue and DLQ."""
        self._heap.clear()
        self._dlq.clear()


__all__ = [
    "DeadLetterEntry",
    "PriorityTaskQueue",
    "QueuedTask",
    "TaskPriority",
]
