# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - DAG Scheduler."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any

from .dag_scheduler_shapes import DAGStepResult, coerce_id, get_dependencies, get_order

_coerce_id, _get_order, _get_dependencies = coerce_id, get_order, get_dependencies

logger = logging.getLogger(__name__)


class DAGScheduler:
    """DAG-based scheduler for recipe steps."""

    def __init__(self, steps: list, max_workers: int = 4) -> None:
        self.steps = steps
        self._steps = {_get_order(s, idx): s for idx, s in enumerate(steps)}
        self._max_workers = max_workers
        self._completed: set[Any] = set()
        self._failed: set[Any] = set()
        self._cancelled: set[Any] = set()
        self._lock = threading.Lock()

    def get_ready_steps(self) -> list:
        with self._lock:
            done = self._completed | self._failed | self._cancelled
            return [s for o, s in self._steps.items() if o not in done and all(d in self._completed for d in _get_dependencies(s))]

    def mark_completed(self, order: Any) -> None:
        with self._lock:
            self._completed.add(order)

    def mark_failed(self, order: Any) -> None:
        with self._lock:
            self._failed.add(order)
            queue = [order]
            while queue:
                curr = queue.pop(0)
                for o, s in self._steps.items():
                    if o not in self._cancelled and curr in _get_dependencies(s):
                        self._cancelled.add(o)
                        queue.append(o)

    def is_done(self) -> bool:
        return set(self._steps.keys()) == (self._completed | self._failed | self._cancelled)

    @property
    def cancelled_steps(self) -> set[Any]:
        return self._cancelled.copy()

    def has_dependencies(self) -> bool:
        return any(bool(_get_dependencies(step)) for step in self._steps.values())

    def _build_graph(self, strict: bool = False) -> tuple[list[Any], dict[Any, int], dict[Any, list[Any]]]:
        orders = list(self._steps.keys())
        in_degree: dict[Any, int] = {o: 0 for o in orders}
        adj: dict[Any, list[Any]] = defaultdict(list)
        for order, step in self._steps.items():
            for dep in _get_dependencies(step):
                if dep in self._steps:
                    adj[dep].append(order)
                    in_degree[order] += 1
                elif strict:
                    raise RuntimeError(f"task '{order}' depends on unknown step '{dep}'")
        return orders, in_degree, adj

    def get_execution_order(self, strict: bool = False) -> list[Any]:
        if not self._steps or not self.has_dependencies():
            return list(self._steps.keys())
        orders, in_degree, adj = self._build_graph(strict=strict)
        queue = [o for o in orders if in_degree[o] == 0]
        exec_order: list[Any] = []
        while queue:
            curr = queue.pop(0)
            exec_order.append(curr)
            for nbr in adj.get(curr, []):
                in_degree[nbr] -= 1
                if in_degree[nbr] == 0:
                    queue.append(nbr)
        if len(exec_order) != len(orders):
            if strict:
                raise RuntimeError(f"circular task dependency detected among: {[o for o in orders if o not in set(exec_order)]}")
            return list(self._steps.keys())
        return exec_order

    def get_parallel_groups(self) -> list[list[Any]]:
        if not self._steps:
            return []
        if not self.has_dependencies():
            return [list(self._steps.keys())]
        orders, in_degree, adj = self._build_graph(strict=False)
        current_wave = [o for o in orders if in_degree[o] == 0]
        groups, processed = [], 0
        while current_wave:
            groups.append(current_wave)
            processed += len(current_wave)
            current_wave = [nbr for curr in current_wave for nbr in adj.get(curr, []) if (in_degree.__setitem__(nbr, in_degree[nbr] - 1) or in_degree[nbr] == 0)]
        return groups if processed == len(orders) else [list(self._steps.keys())]

    def execute_all(self, executor_fn: Callable, on_complete: Callable | None = None) -> dict[Any, DAGStepResult]:
        results: dict[Any, DAGStepResult] = {}
        in_flight: set[Any] = set()
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures: dict[Future, Any] = {}
            while not self.is_done():
                for step in [s for s in self.get_ready_steps() if _get_order(s) not in in_flight]:
                    so = _get_order(step)
                    in_flight.add(so)
                    futures[pool.submit(executor_fn, step)] = step
                if not futures:
                    break
                for future in list(as_completed(futures)):
                    so = _get_order(futures.pop(future))
                    try:
                        res = future.result()
                        passed = getattr(getattr(res, "verification", None), "passed", False)
                        dag_res = DAGStepResult(order=so, success=passed, result=res)
                    except Exception as e:
                        dag_res, passed = DAGStepResult(order=so, success=False, error=str(e)), False
                    results[so] = dag_res
                    self.mark_completed(so) if passed else self.mark_failed(so)
                    if on_complete:
                        on_complete(so, dag_res)
        return results


def validate_dag(steps: list) -> str | None:
    if not steps:
        return None
    sched = DAGScheduler(steps)
    try:
        sched.get_execution_order(strict=False)
        orders, in_degree, adj = sched._build_graph(strict=False)
        queue = [o for o in orders if in_degree[o] == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for nbr in adj.get(node, []):
                in_degree[nbr] -= 1
                if in_degree[nbr] == 0:
                    queue.append(nbr)
        return "Circular dependency detected in recipe steps" if visited != len(orders) else None
    except Exception:
        return "Circular dependency detected in recipe steps"


__all__ = ["DAGScheduler", "DAGStepResult", "validate_dag"]
