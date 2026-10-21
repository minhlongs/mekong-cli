# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Dispatcher — Task dispatcher with load balancing.

ISS-006 Classification: STANDALONE WORKER-POOL DISPATCH
  This module is NOT a duplicate of src/core/agent_dispatcher.py.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable

from .dispatcher_models import (
    DispatchResult,
    LoadBalanceStrategy,
    format_dispatcher_stats,
    select_least_loaded_worker,
    select_round_robin_worker,
)
from .task_router import Task, TaskRouter
from .worker_pool import WorkerInfo, WorkerPool, WorkerState  # noqa: F401

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"


class Dispatcher:
    """Dispatches tasks to workers using configurable load balancing."""

    def __init__(
        self,
        worker_pool: WorkerPool | None = None,
        task_router: TaskRouter | None = None,
        strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
    ) -> None:
        self.worker_pool = worker_pool or WorkerPool()
        self.task_router = task_router or TaskRouter()
        self.strategy = strategy
        self._round_robin_index = 0
        self._dispatch_history: list[DispatchResult] = []

    def dispatch(
        self,
        task: Task | None = None,
        description: str | None = None,
        priority: str = "MEDIUM",
        capability: str | None = None,
        timeout_sec: int = 300,
    ) -> DispatchResult:
        """Dispatch a task to an available worker."""
        start_time = time.time()

        if task is None:
            if description:
                task = self.task_router.enqueue(
                    description=description, priority=priority, capability=capability or "general"
                )
            else:
                task = self.task_router.get_next_task(capability)
                if not task:
                    return DispatchResult(success=False, task_id="", error="No pending tasks in queue")

        worker = self._select_worker(capability=task.capability)
        if not worker:
            self.task_router.enqueue(
                description=task.description,
                priority=task.priority,
                capability=task.capability,
                payload=task.payload,
            )
            return DispatchResult(success=False, task_id=task.task_id, error="No available workers")

        self.worker_pool.mark_busy(worker.id)
        task.assigned_to = worker.name
        logger.info(f"[Dispatcher] Dispatched {task.task_id} to {worker.name}")

        duration_ms = int((time.time() - start_time) * 1000)
        result = DispatchResult(
            success=True, task_id=task.task_id, worker_name=worker.name, duration_ms=duration_ms
        )
        self._dispatch_history.append(result)
        if len(self._dispatch_history) > 100:
            self._dispatch_history = self._dispatch_history[-100:]
        return result

    def _select_worker(self, capability: str | None = None) -> WorkerInfo | None:
        """Select a worker based on load balancing strategy."""
        available = self.worker_pool.get_available_worker(capability)
        if not available:
            return None
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(capability)
        if self.strategy == LoadBalanceStrategy.LEAST_LOADED:
            return self._least_loaded_select(capability)
        return available

    def _round_robin_select(self, capability: str | None = None) -> WorkerInfo | None:
        worker, self._round_robin_index = select_round_robin_worker(
            self.worker_pool.list_workers(), self._round_robin_index, capability
        )
        return worker

    def _least_loaded_select(self, capability: str | None = None) -> WorkerInfo | None:
        return select_least_loaded_worker(self.worker_pool.list_workers(), capability)

    def complete_task(self, task_id: str, result: Any = None) -> None:
        """Mark a task as completed and free the worker."""
        task = self.task_router._active_tasks.get(task_id)
        if task and task.assigned_to:
            self.worker_pool.mark_idle(task.assigned_to)
        self.task_router.complete(task_id, result)

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed and free the worker."""
        task = self.task_router._active_tasks.get(task_id)
        if task and task.assigned_to:
            self.worker_pool.mark_failed(task.assigned_to)
        self.task_router.fail(task_id, error)

    def get_stats(self) -> dict[str, Any]:
        """Get dispatcher statistics."""
        return format_dispatcher_stats(
            self.worker_pool.get_stats(),
            self.task_router.get_stats(),
            len(self._dispatch_history),
            self.strategy.value,
        )

    async def dispatch_loop(
        self, process_task: Callable[[Task], Any], interval_sec: float = 1.0
    ) -> None:
        """Continuous dispatch loop for autonomous operation."""
        logger.info("[Dispatcher] Starting dispatch loop")
        while True:
            try:
                result = await asyncio.to_thread(self.dispatch)
                if result.success:
                    asyncio.create_task(self._process_and_complete(result.task_id, process_task))
                else:
                    await asyncio.sleep(interval_sec)
            except asyncio.CancelledError:
                logger.info("[Dispatcher] Dispatch loop cancelled")
                break
            except Exception as e:
                logger.exception(f"[Dispatcher] Error in dispatch loop: {e}")
                await asyncio.sleep(interval_sec)

    async def _process_and_complete(self, task_id: str, process_fn: Callable[[Task], Any]) -> None:
        task = self.task_router._active_tasks.get(task_id)
        if not task:
            return
        try:
            start = time.time()
            await process_fn(task)
            duration_ms = int((time.time() - start) * 1000)
            self.complete_task(task_id, result={"duration_ms": duration_ms})
            logger.info(f"[Dispatcher] Task {task_id} completed in {duration_ms}ms")
        except Exception as e:
            logger.exception(f"[Dispatcher] Task {task_id} failed: {e}")
            self.fail_task(task_id, error=str(e))
