"""Observe, verify, repair, remember, commit, and DAG loop mixin."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, cast

from src.core.dag_scheduler import DAGScheduler, _get_order
from src.core.memory_separation import MemoryTier

from .intent import _criteria_to_verifier_dict, _ExecResultLike, _report_to_verification, _topological_task_order
from .models import (
    _MAX_REPAIR_ATTEMPTS, CommitRecord, Criteria, MemoryEntry, Observation,
    RepairAction, RepairStrategy, Result, Scope, SideEffect, Task, Verification,
)

logger = logging.getLogger(__name__)


class RepairMemoryMixin:
    """Mixin implementing observe, verify, repair, remember, commit, and task loops."""

    def observe(self, result: Result) -> Observation:
        metrics: dict[str, Any] = {"has_error": result.error is not None}
        estimated = result.metadata.get("estimated_cost")
        if estimated is not None:
            metrics["estimated_cost"] = estimated
        if self._telemetry is not None:
            self._telemetry.emit({
                "event_type": "task_completed",
                "metric": 1.0,
                "estimated_cost": estimated,
                "mission_id": self._mission_id,
            })
        se = [SideEffect(kind="error", target=result.task_id, data={"error": result.error})] if result.error else []
        return Observation(result=result, metrics=metrics, side_effects=se)

    def verify(self, observation: Observation, criteria: Criteria) -> Verification:
        criteria_dict = _criteria_to_verifier_dict(criteria)
        if not criteria_dict:
            return Verification(passed=observation.result.error is None)
        result = observation.result
        exec_result_like = _ExecResultLike(
            exit_code=0 if result.error is None else 1,
            stdout=str(result.output) if result.output is not None else "",
            stderr=result.error or "",
            metadata=result.metadata or {},
        )
        report = self._verifier.verify(cast(Any, exec_result_like), criteria_dict)
        return _report_to_verification(report)

    def repair(self, verification: Verification) -> RepairAction:
        """Attempt to repair a failed result. Abort after 3 retries."""
        if self._repair_count >= 3:
            return RepairAction(strategy=RepairStrategy.ESCALATE)
        self._repair_count += 1
        if verification.failures:
            has_error = any("error" in f.lower() for f in verification.failures)
            return RepairAction(strategy=RepairStrategy.RETRY if has_error else RepairStrategy.FALLBACK)
        return RepairAction(strategy=RepairStrategy.RETRY)

    def remember(self, observation: Observation) -> MemoryEntry:
        key = f"obs-{observation.result.task_id}"
        value = {"task_id": observation.result.task_id, "error": observation.result.error, "metrics": observation.metrics}
        entry = MemoryEntry(key=key, value=value, scope=Scope.SESSION)
        payload = json.dumps(value, default=str).encode("utf-8")
        try:
            if self._memory_store is not None:
                self._memory_store.store(key, payload, ttl=3600)
                self._session_keys.add(key)
        except Exception:
            if self._memory_separation is not None:
                try:
                    self._memory_separation.store(key, payload, tier=MemoryTier.SESSION)
                    self._session_keys.add(key)
                except Exception:
                    logger.warning("remember() write failed key=%s", key)
            else:
                logger.warning("remember() write failed key=%s", key)
        return entry

    def flush_session(self) -> int:
        """Clear all SESSION-tier memory. Returns count deleted."""
        try:
            return self._flush_session_keys()
        except Exception:
            return 0

    def _flush_session_keys(self) -> int:
        """Delete every SESSION-tier key through the conformant adapter."""
        cleared = 0
        if self._memory_store is not None:
            for key in list(self._session_keys):
                try:
                    if self._memory_store.delete(key):
                        cleared += 1
                except Exception:
                    logger.warning("session flush failed key=%s", key)
            self._session_keys.clear()
            if hasattr(self._memory_store, "prune_expired"):
                try:
                    self._memory_store.prune_expired()
                except Exception:
                    pass
        if self._memory_separation is not None and hasattr(self._memory_separation, "flush_session"):
            try:
                cleared += self._memory_separation.flush_session()
            except Exception:
                pass
        return cleared

    def commit(self, result: Result) -> CommitRecord:
        record = CommitRecord(id=f"commit-{uuid.uuid4().hex[:12]}", result=result)
        if result.error is None and self._billing is not None and hasattr(self._billing, "record_usage"):
            try:
                self._billing.record_usage(self._agent_id, 0, "default", "run")
                if hasattr(self._billing, "check_quota"):
                    self._billing.check_quota(self._agent_id)
            except Exception as exc:
                logger.warning("Billing record_usage failed: %s", exc)
        if self._telemetry is not None:
            self._telemetry.emit({"event_type": "run_completed", "task_id": result.task_id, "error": result.error, "mission_id": self._mission_id})
        return record

    def _is_cancelled(self) -> bool:
        return bool(getattr(self, "_cancel_requested", False))

    def _cancelled_result(self, task: Task, prior: Result | None = None) -> Result:
        return Result(
            task_id=prior.task_id if prior else task.id,
            output=prior.output if prior else None,
            error="mission cancelled",
            metadata={**(prior.metadata if prior else {}), "cancelled": True},
        )

    def _run_dag_tasks(self, tasks: list[Task], criteria: Criteria) -> list[Result]:
        ordered = _topological_task_order(tasks)
        if len(ordered) <= 1:
            return [self._run_task_loop(t, criteria) for t in ordered]
        sched: DAGScheduler = DAGScheduler(ordered)
        results: dict[str, Result] = {}
        for task in ordered:
            step_order, step_key = _get_order(task), str(task.step.id)
            if step_order in sched.cancelled_steps or step_key in sched.cancelled_steps:
                logger.warning("DAG: skipping cancelled task=%s (upstream failed)", task.id)
                results[step_key] = self._cancelled_result(task)
                continue
            result = self._run_task_loop(task, criteria)
            results[step_key] = result
            if result.error is not None and not result.metadata.get("gate_blocked", False):
                sched.mark_failed(step_order)
                logger.warning("DAG: task=%s failed, cancelling downstream dependents", task.id)
            else:
                sched.mark_completed(step_order)
        return [results[str(t.step.id)] for t in ordered]

    def _run_task_loop(self, task: Task, criteria: Criteria) -> Result:
        attempts = 0
        if self._is_cancelled():
            return self._cancelled_result(task)
        result = self.execute(task)
        while attempts < _MAX_REPAIR_ATTEMPTS:
            if self._is_cancelled():
                return self._cancelled_result(task, result)
            obs = self.observe(result)
            verification = self.verify(obs, criteria)
            self._trace_step(task, result, verification)
            if verification.passed or result.metadata.get("gate_blocked", False):
                return result
            attempts += 1
            action = self.repair(verification)
            if action.strategy in (RepairStrategy.ESCALATE, RepairStrategy.ROLLBACK):
                return result
            result = self.execute(task)
        return result
