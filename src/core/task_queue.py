# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Distributed Task Queue & Dead-Letter Recovery Mesh.

Provides prioritized task scheduling (CRITICAL, HIGH, NORMAL, LOW), atomic worker
leases with heartbeat extensions and stale reclamation, exponential retry backoff,
and dead-letter queue (DLQ) inspection and replay without external dependencies.

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs or heavy messaging clients (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import heapq
import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default database location in .mekong/task_queue.db
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT_ROOT / ".mekong" / "task_queue.db"


class TaskPriority(IntEnum):
    """Task scheduling priority levels (lower integer = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4

    @classmethod
    def from_str(cls, val: str) -> TaskPriority:
        normalized = (val or "").strip().lower()
        if normalized == "critical":
            return cls.CRITICAL
        if normalized == "high":
            return cls.HIGH
        if normalized == "low":
            return cls.LOW
        return cls.NORMAL



@dataclass(order=True)
class QueuedTask:
    """A task in the legacy in-memory priority queue."""

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
    """A task that exhausted all retry attempts in legacy in-memory queue."""

    task: QueuedTask
    final_error: str
    failed_at: float = field(default_factory=time.time)


class PriorityTaskQueue:
    """Legacy priority-based in-memory task queue with DLQ (for pipeline_manager)."""

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
        if self._max_size > 0 and len(self._heap) >= self._max_size:
            return None

        prio_val = priority.value if hasattr(priority, "value") else int(priority)
        task = QueuedTask(
            priority=prio_val,
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
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def peek(self) -> QueuedTask | None:
        return self._heap[0] if self._heap else None

    def mark_completed(self, task: QueuedTask) -> None:
        self._total_completed += 1

    def mark_failed(self, task: QueuedTask, error: str) -> bool:
        task.attempt += 1
        if task.attempt < task.max_attempts:
            heapq.heappush(self._heap, task)
            return True
        self._dlq.append(DeadLetterEntry(task=task, final_error=error))
        return False

    def get_dlq(self) -> list[DeadLetterEntry]:
        return list(self._dlq)

    def retry_from_dlq(self, task_id: str) -> bool:
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
        return len(self._heap)

    @property
    def dlq_size(self) -> int:
        return len(self._dlq)

    @property
    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def stats(self) -> dict[str, Any]:
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
        self._heap.clear()
        self._dlq.clear()


class TaskState:
    """Discrete lifecycle states for queued tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS queue_tasks (
    task_id         TEXT    NOT NULL PRIMARY KEY,
    name            TEXT    NOT NULL,
    priority        INTEGER NOT NULL DEFAULT 2,
    state           TEXT    NOT NULL DEFAULT 'pending',
    payload_json    TEXT    NOT NULL DEFAULT '{}',
    result_json     TEXT,
    error           TEXT,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 3,
    leased_by       TEXT,
    leased_until    REAL,
    scheduled_at    REAL    NOT NULL,
    created_at      REAL    NOT NULL,
    updated_at      REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_queue_poll ON queue_tasks (state, scheduled_at, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_lease ON queue_tasks (leased_until);
CREATE INDEX IF NOT EXISTS idx_queue_state ON queue_tasks (state);
"""


def _generate_hex(byte_length: int = 8) -> str:
    """Generate cryptographically secure random hexadecimal identifier."""
    return os.urandom(byte_length).hex()


@dataclass
class QueueTask:
    """Represents a scheduled, executing, or terminal task in the distributed queue."""

    task_id: str
    name: str
    priority: int = TaskPriority.NORMAL
    state: str = TaskState.PENDING
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    leased_by: Optional[str] = None
    leased_until: Optional[float] = None
    scheduled_at: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task into a JSON-serializable dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority,
            "priority_name": TaskPriority(self.priority).name.lower(),
            "state": self.state,
            "payload": self.payload,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "leased_by": self.leased_by,
            "leased_until": self.leased_until,
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TaskQueue:
    """Atomic, persistent priority task queue with worker leasing and DLQ recovery."""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        raw_env = os.environ.get("MEKONG_TASK_QUEUE_DB_PATH")
        if db_path:
            self.db_path = Path(db_path).resolve()
        elif raw_env:
            self.db_path = Path(raw_env).resolve()
        else:
            self.db_path = _DEFAULT_DB.resolve()

        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database directory and initialize schema tables."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.executescript(_SCHEMA_SQL)
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error initializing task queue database: {exc}")

    def enqueue(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int | str = TaskPriority.NORMAL,
        max_retries: int = 3,
        delay_sec: float = 0.0,
    ) -> QueueTask:
        """Enqueue a new task for prioritized execution."""
        task_id = f"task_{_generate_hex(8)}"
        now = time.time()
        sched = now + max(0.0, delay_sec)

        int_priority = TaskPriority.from_str(priority).value if isinstance(priority, str) else int(priority)
        task = QueueTask(
            task_id=task_id,
            name=name,
            priority=int_priority,
            state=TaskState.PENDING,
            payload=payload or {},
            max_retries=max_retries,
            scheduled_at=sched,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                conn.execute(
                    """
                    INSERT INTO queue_tasks
                    (task_id, name, priority, state, payload_json, retry_count, max_retries, scheduled_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.task_id,
                        task.name,
                        task.priority,
                        task.state,
                        json.dumps(task.payload),
                        task.retry_count,
                        task.max_retries,
                        task.scheduled_at,
                        task.created_at,
                        task.updated_at,
                    ),
                )
                conn.commit()

        # Telemetry hook (optional/graceful)
        self._record_telemetry("enqueue")
        return task

    def reclaim_expired_leases(self) -> int:
        """Reclaim running tasks whose lease duration has expired back to pending."""
        now = time.time()
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    UPDATE queue_tasks
                    SET state = 'pending', leased_by = NULL, leased_until = NULL, updated_at = ?
                    WHERE state = 'running' AND leased_until IS NOT NULL AND leased_until < ?
                    """,
                    (now, now),
                )
                reclaimed = cur.rowcount
                conn.commit()
                return reclaimed

    def lease_task(
        self,
        worker_id: str,
        lease_duration_sec: float = 30.0,
    ) -> Optional[QueueTask]:
        """Atomically lease the highest priority eligible pending task."""
        tasks = self.lease_tasks(worker_id=worker_id, limit=1, lease_duration_sec=lease_duration_sec)
        return tasks[0] if tasks else None

    def lease_tasks(
        self,
        worker_id: str,
        limit: int = 1,
        lease_duration_sec: float = 30.0,
    ) -> List[QueueTask]:
        """Atomically lease up to `limit` pending tasks for worker execution."""
        # 1. First reclaim any stale leases
        self.reclaim_expired_leases()

        now = time.time()
        leased_until = now + max(0.001, lease_duration_sec)
        leased_tasks: List[QueueTask] = []

        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                # Select top pending tasks ordered by priority (asc), scheduled_at (asc), created_at (asc)
                cur = conn.execute(
                    """
                    SELECT task_id, name, priority, state, payload_json, result_json, error, retry_count, max_retries, leased_by, leased_until, scheduled_at, created_at, updated_at
                    FROM queue_tasks
                    WHERE state = 'pending' AND scheduled_at <= ?
                    ORDER BY priority ASC, scheduled_at ASC, created_at ASC
                    LIMIT ?
                    """,
                    (now, limit),
                )
                candidates = cur.fetchall()
                if not candidates:
                    return []

                # Mark selected tasks as leased
                task_ids = [row[0] for row in candidates]
                placeholders = ",".join("?" for _ in task_ids)
                conn.execute(
                    f"""
                    UPDATE queue_tasks
                    SET state = 'running', leased_by = ?, leased_until = ?, updated_at = ?
                    WHERE task_id IN ({placeholders})
                    """,
                    [worker_id, leased_until, now] + task_ids,
                )
                conn.commit()

                for row in candidates:
                    (
                        t_id, name, prio, _, p_json, r_json, err,
                        retries, max_ret, _, _, sched, created, _
                    ) = row
                    leased_tasks.append(
                        QueueTask(
                            task_id=t_id,
                            name=name,
                            priority=prio,
                            state=TaskState.RUNNING,
                            payload=json.loads(p_json) if p_json else {},
                            result=json.loads(r_json) if r_json else None,
                            error=err,
                            retry_count=retries,
                            max_retries=max_ret,
                            leased_by=worker_id,
                            leased_until=leased_until,
                            scheduled_at=sched,
                            created_at=created,
                            updated_at=now,
                        )
                    )

        return leased_tasks

    def heartbeat(
        self,
        task_id: str,
        worker_id: str,
        extension_sec: float = 30.0,
    ) -> bool:
        """Extend active worker lease for a task."""
        now = time.time()
        new_until = now + max(0.001, extension_sec)
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    UPDATE queue_tasks
                    SET leased_until = ?, updated_at = ?
                    WHERE task_id = ? AND state = 'running' AND leased_by = ?
                    """,
                    (new_until, now, task_id, worker_id),
                )
                conn.commit()
                return cur.rowcount > 0

    def complete_task(
        self,
        task_id: str,
        worker_id: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark task as successfully completed."""
        now = time.time()
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                query = """
                    UPDATE queue_tasks
                    SET state = 'completed', result_json = ?, leased_by = NULL, leased_until = NULL, updated_at = ?
                    WHERE task_id = ? AND state = 'running'
                """
                params = [json.dumps(result or {}), now, task_id]
                if worker_id:
                    query += " AND leased_by = ?"
                    params.append(worker_id)

                cur = conn.execute(query, params)
                conn.commit()
                success = cur.rowcount > 0

        if success:
            self._record_telemetry("complete")
        return success

    def fail_task(
        self,
        task_id: str,
        worker_id: Optional[str] = None,
        error: str = "Execution error",
        base_delay_sec: float = 1.0,
    ) -> Tuple[bool, str]:
        """Record task failure with exponential backoff retry or transition to dead-letter queue."""
        task = self.get_task(task_id)
        if not task or task.state != TaskState.RUNNING:
            return False, "Task not found or not in running state"

        now = time.time()
        new_retries = task.retry_count + 1

        if new_retries > task.max_retries:
            # Exceeded retries -> transition to DEAD_LETTER
            new_state = TaskState.DEAD_LETTER
            scheduled_at = now
        else:
            # Retry with exponential backoff: delay = base * 2^retry
            new_state = TaskState.PENDING
            delay = base_delay_sec * (2 ** task.retry_count)
            scheduled_at = now + delay

        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    UPDATE queue_tasks
                    SET state = ?, retry_count = ?, error = ?, scheduled_at = ?, leased_by = NULL, leased_until = NULL, updated_at = ?
                    WHERE task_id = ? AND state = 'running'
                    """,
                    (new_state, new_retries, error, scheduled_at, now, task_id),
                )
                conn.commit()
                success = cur.rowcount > 0

        if success:
            self._record_telemetry("dlq" if new_state == TaskState.DEAD_LETTER else "fail")
        return success, new_state

    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """Fetch a task by ID."""
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    SELECT task_id, name, priority, state, payload_json, result_json, error, retry_count, max_retries, leased_by, leased_until, scheduled_at, created_at, updated_at
                    FROM queue_tasks
                    WHERE task_id = ?
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                (
                    t_id, name, prio, state, p_json, r_json, err,
                    retries, max_ret, leased_by, leased_until, sched, created, updated
                ) = row
                return QueueTask(
                    task_id=t_id,
                    name=name,
                    priority=prio,
                    state=state,
                    payload=json.loads(p_json) if p_json else {},
                    result=json.loads(r_json) if r_json else None,
                    error=err,
                    retry_count=retries,
                    max_retries=max_ret,
                    leased_by=leased_by,
                    leased_until=leased_until,
                    scheduled_at=sched,
                    created_at=created,
                    updated_at=updated,
                )

    def get_status(self) -> Dict[str, Any]:
        """Compute aggregated queue metrics across all task states."""
        self.reclaim_expired_leases()
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    SELECT state, count(*) FROM queue_tasks GROUP BY state
                    """
                )
                counts: Dict[str, int] = {
                    TaskState.PENDING: 0,
                    TaskState.RUNNING: 0,
                    TaskState.COMPLETED: 0,
                    TaskState.FAILED: 0,
                    TaskState.DEAD_LETTER: 0,
                }
                for state, count in cur.fetchall():
                    counts[state] = count

                cur_total = conn.execute("SELECT count(*) FROM queue_tasks")
                total = cur_total.fetchone()[0]

                return {
                    "total_tasks": total,
                    "pending": counts[TaskState.PENDING],
                    "running": counts[TaskState.RUNNING],
                    "completed": counts[TaskState.COMPLETED],
                    "dead_letter": counts[TaskState.DEAD_LETTER],
                }

    def get_dlq_tasks(self, limit: int = 50) -> List[QueueTask]:
        """Retrieve tasks residing in the dead-letter queue."""
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    SELECT task_id, name, priority, state, payload_json, result_json, error, retry_count, max_retries, leased_by, leased_until, scheduled_at, created_at, updated_at
                    FROM queue_tasks
                    WHERE state = 'dead_letter'
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                results: List[QueueTask] = []
                for row in cur.fetchall():
                    (
                        t_id, name, prio, state, p_json, r_json, err,
                        retries, max_ret, leased_by, leased_until, sched, created, updated
                    ) = row
                    results.append(
                        QueueTask(
                            task_id=t_id,
                            name=name,
                            priority=prio,
                            state=state,
                            payload=json.loads(p_json) if p_json else {},
                            result=json.loads(r_json) if r_json else None,
                            error=err,
                            retry_count=retries,
                            max_retries=max_ret,
                            leased_by=leased_by,
                            leased_until=leased_until,
                            scheduled_at=sched,
                            created_at=created,
                            updated_at=updated,
                        )
                    )
                return results

    def retry_dlq_task(self, task_id: str) -> bool:
        """Reset a dead-letter task back to pending with cleared retry count."""
        now = time.time()
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    UPDATE queue_tasks
                    SET state = 'pending', retry_count = 0, error = NULL, scheduled_at = ?, leased_by = NULL, leased_until = NULL, updated_at = ?
                    WHERE task_id = ? AND state = 'dead_letter'
                    """,
                    (now, now, task_id),
                )
                conn.commit()
                return cur.rowcount > 0

    def retry_all_dlq(self) -> int:
        """Reset all dead-letter tasks back to pending for replay."""
        now = time.time()
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute(
                    """
                    UPDATE queue_tasks
                    SET state = 'pending', retry_count = 0, error = NULL, scheduled_at = ?, leased_by = NULL, leased_until = NULL, updated_at = ?
                    WHERE state = 'dead_letter'
                    """,
                    (now, now),
                )
                conn.commit()
                return cur.rowcount

    def clear_dlq(self) -> int:
        """Purge all tasks residing in the dead-letter queue."""
        with self._lock:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                cur = conn.execute("DELETE FROM queue_tasks WHERE state = 'dead_letter'")
                conn.commit()
                return cur.rowcount

    def _record_telemetry(self, action: str) -> None:
        """Optionally record metric increment into telemetry registry."""
        try:
            from src.core.telemetry_bridge import get_telemetry_bridge

            bridge = get_telemetry_bridge()
            if action == "enqueue":
                bridge.metrics.inc_counter("mekong_queue_tasks_enqueued_total", 1.0)
            elif action == "complete":
                bridge.metrics.inc_counter("mekong_queue_tasks_completed_total", 1.0)
            elif action == "dlq":
                bridge.metrics.inc_counter("mekong_queue_tasks_dlq_total", 1.0)
        except Exception:
            pass


# Global singleton instance
_GLOBAL_TASK_QUEUE: Optional[TaskQueue] = None
_GLOBAL_TASK_QUEUE_LOCK = threading.Lock()


def get_task_queue(db_path: Optional[Path | str] = None) -> TaskQueue:
    """Get or initialize singleton TaskQueue."""
    global _GLOBAL_TASK_QUEUE
    with _GLOBAL_TASK_QUEUE_LOCK:
        if _GLOBAL_TASK_QUEUE is None or db_path is not None:
            _GLOBAL_TASK_QUEUE = TaskQueue(db_path=db_path)
        return _GLOBAL_TASK_QUEUE


__all__ = [
    "DeadLetterEntry",
    "PriorityTaskQueue",
    "QueueTask",
    "QueuedTask",
    "TaskPriority",
    "TaskQueue",
    "TaskState",
    "get_task_queue",
]

