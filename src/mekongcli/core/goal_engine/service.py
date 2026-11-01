# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Goal engine service tying planning, execution, verification, leases, worktrees, and memory."""

from __future__ import annotations

import concurrent.futures
import threading
import time
from pathlib import Path
from typing import Any, Callable

from src.core.memory_canonical import MemoryEntry, MemoryStore
from src.mekongcli.core.execution import ExecutionOutcome, LocalExecutor
from src.mekongcli.core.swarm import RoleRegistry
from src.mekongcli.core.telemetry import GoalEventBusAdapter
from src.mekongcli.core.verification import VerificationPipeline

from .models import (
    Checkpoint,
    ExecutionTruthStatus,
    Goal,
    GoalStatus,
    GoalTask,
    TaskGraph,
    TaskStatus,
    VerificationRun,
    WorkerLease,
    new_id,
)
from .planner import GoalPlanner
from .store import MAX_AUTONOMOUS_WORKERS, LeaseCapacityError, SQLiteGoalStore
from .worktree_manager import WorktreeIsolationManager


class GoalEngine:
    """Persistent, local-first autonomous goal execution service."""

    def __init__(
        self,
        store: SQLiteGoalStore | None = None,
        cwd: str | Path = ".",
        memory_store: MemoryStore | None = None,
        max_autonomous_workers: int = MAX_AUTONOMOUS_WORKERS,
    ) -> None:
        from src.mekongcli.core.governance import StopConditionPolicy

        self.store = store or SQLiteGoalStore()
        self.cwd = Path(cwd)
        self.planner = GoalPlanner()
        self.roles = RoleRegistry()
        self.events = GoalEventBusAdapter()
        self.stop_policy = StopConditionPolicy()
        self.memory_store = memory_store
        self.max_autonomous_workers = min(max(1, max_autonomous_workers), MAX_AUTONOMOUS_WORKERS)
        self.worktree_manager = WorktreeIsolationManager(repo_root=self.cwd)

    def create_goal(self, title: str) -> Goal:
        from src.mekongcli.core.governance import StopConditionPolicy as _SCP

        goal = Goal(
            id=new_id("goal"),
            title=title,
            status=GoalStatus.PLANNED,
            truth_status=ExecutionTruthStatus.PLANNED,
            stop_conditions=list(_SCP.DEFAULTS),
        )
        tasks, criteria = self.planner.decompose(goal.id, title)
        self.store.save_goal(goal)
        self.store.save_tasks(tasks)
        self.store.save_criteria(goal.id, criteria)
        self._checkpoint(goal.id, None, "goal-created", {"tasks": len(tasks)})
        self._event(goal.id, "goal.created", {"title": title})
        self._memory(goal.id, "goal_created", title)
        return goal

    def run_goal(
        self,
        goal_id: str,
        verification_profile: str = "standard",
        execute_commands: bool = False,
        timeout_seconds: float | None = None,
        ticket_id: str | None = None,
        isolate_worktree: bool = False,
    ) -> Goal:
        VerificationPipeline.validate_profile(verification_profile)
        goal = self._require_goal(goal_id)
        if goal.status == GoalStatus.CANCELLED:
            raise RuntimeError(f"Goal {goal_id} is cancelled")

        if ticket_id is not None:
            self._enforce_ticket_mandate_and_budget(ticket_id)

        goal.status = GoalStatus.RUNNING
        goal.truth_status = ExecutionTruthStatus.RUNNING
        self.store.save_goal(goal)
        self._event(goal.id, "goal.started", {"profile": verification_profile})

        tasks = self.store.get_tasks(goal.id)
        graph = TaskGraph(goal_id=goal.id, tasks=tasks)
        completed_any = True
        while completed_any:
            completed_any = False
            for task in graph.ready_tasks(allow_simulated=not execute_commands):
                if ticket_id is not None:
                    self._enforce_ticket_mandate_and_budget(ticket_id)

                task.status = TaskStatus.RUNNING
                task.truth_status = ExecutionTruthStatus.RUNNING
                task.attempts += 1
                self.store.save_tasks([task])
                assignment = self.roles.assign(task)
                self._event(
                    goal.id,
                    "task.started",
                    {
                        "task_id": task.id,
                        "role": assignment.role.value,
                        "rationale": assignment.rationale,
                    },
                )

                if execute_commands and task.command:
                    use_wt = isolate_worktree or task.mutates_workspace
                    wt_path: Path | None = None
                    try:
                        if use_wt:
                            wt_path = self.worktree_manager.allocate(
                                ticket_id or goal.id, task.id
                            )
                        exec_cwd = wt_path if wt_path is not None else self.cwd
                        outcome = self._execute_task_outcome(
                            task.command,
                            cwd=exec_cwd,
                            timeout_seconds=timeout_seconds,
                            worktree_root=wt_path,
                        )
                    except Exception as exc:
                        outcome = ExecutionOutcome(
                            command=task.command,
                            exit_code=1,
                            stdout="",
                            stderr=str(exc),
                            duration_ms=0.0,
                            blocked_reason=f"Unhandled execution exception: {exc}",
                        )
                    finally:
                        if wt_path is not None:
                            self.worktree_manager.cleanup(wt_path)

                    task.exit_code = outcome.exit_code
                    task.stdout = outcome.stdout
                    task.stderr = outcome.stderr
                    task.blocked_reason = outcome.blocked_reason or None

                    if not outcome.success:
                        summary = (
                            outcome.blocked_reason
                            or outcome.stderr.strip()
                            or f"Command failed with exit code {outcome.exit_code}"
                        )
                        task.result_summary = summary
                        if outcome.exit_code == 126 and outcome.blocked_reason:
                            task.status = TaskStatus.FAILED
                            task.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
                        else:
                            task.status = TaskStatus.FAILED
                            task.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
                        self.store.save_tasks([task])

                        all_tasks = self.store.get_tasks(goal.id)
                        prop_graph = TaskGraph(goal_id=goal.id, tasks=all_tasks)
                        propagated = prop_graph.propagate_failures()
                        if propagated:
                            self.store.save_tasks(propagated)

                        self._checkpoint(
                            goal.id,
                            task.id,
                            f"task-failed:{task.title}",
                            {
                                "role": task.role.value,
                                "exit_code": outcome.exit_code,
                                "summary": summary,
                            },
                        )
                        self._event(
                            goal.id,
                            "task.failed",
                            {
                                "task_id": task.id,
                                "exit_code": outcome.exit_code,
                                "summary": summary,
                            },
                        )
                        goal.status = GoalStatus.FAILED
                        goal.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
                        self.store.save_goal(goal)
                        self._event(
                            goal.id,
                            "goal.failed",
                            {"task_id": task.id, "reason": summary},
                        )
                        return goal

                    summary = outcome.stdout.strip() or "command completed"
                    task.status = TaskStatus.COMPLETED
                    task.truth_status = ExecutionTruthStatus.VERIFIED_SUCCESS
                    task.result_summary = summary
                else:
                    summary = f"{assignment.role.value} completed directive: {task.title}"
                    task.status = TaskStatus.COMPLETED
                    task.truth_status = ExecutionTruthStatus.SIMULATED
                    task.result_summary = summary

                self.store.save_tasks([task])
                self._checkpoint(
                    goal.id,
                    task.id,
                    f"task-completed:{task.title}",
                    {"role": task.role.value, "summary": summary},
                )
                self._event(
                    goal.id,
                    "task.completed",
                    {"task_id": task.id, "summary": summary, "truth_status": task.truth_status.value},
                )
                completed_any = True
                graph = TaskGraph(goal_id=goal.id, tasks=self.store.get_tasks(goal.id))

            tasks = self.store.get_tasks(goal.id)
            stop_reason = self.stop_policy.should_stop_for_retries(goal, tasks)
            if stop_reason:
                goal.status = GoalStatus.BLOCKED
                goal.truth_status = ExecutionTruthStatus.BLOCKED
                self.store.save_goal(goal)
                self._event(goal.id, "goal.blocked", {"reason": stop_reason})
                return goal

        tasks = self.store.get_tasks(goal.id)
        if any(task.truth_status == ExecutionTruthStatus.WAITING_APPROVAL for task in tasks):
            goal.status = GoalStatus.BLOCKED
            goal.truth_status = ExecutionTruthStatus.WAITING_APPROVAL
            self.store.save_goal(goal)
            self._event(goal.id, "goal.blocked", {"reason": "waiting_approval"})
            return goal

        if any(task.status == TaskStatus.FAILED for task in tasks):
            goal.status = GoalStatus.FAILED
            goal.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
            self.store.save_goal(goal)
            self._event(goal.id, "goal.failed", {"reason": "task_execution_failed"})
            return goal

        if any(task.status != TaskStatus.COMPLETED for task in tasks):
            goal.status = GoalStatus.BLOCKED
            goal.truth_status = ExecutionTruthStatus.BLOCKED
            self.store.save_goal(goal)
            self._event(goal.id, "goal.blocked", {"reason": "pending_tasks_remain"})
            return goal

        return self.verify_goal(
            goal.id,
            verification_profile,
            simulated_run=not execute_commands,
        )

    def run_goal_parallel(
        self,
        goal_id: str,
        verification_profile: str = "standard",
        execute_commands: bool = False,
        max_workers: int = MAX_AUTONOMOUS_WORKERS,
        timeout_seconds: float | None = None,
        isolate_worktree: bool = False,
        ticket_id: str | None = None,
    ) -> Goal:
        VerificationPipeline.validate_profile(verification_profile)
        goal = self._require_goal(goal_id)
        if goal.status == GoalStatus.CANCELLED:
            raise RuntimeError(f"Goal {goal_id} is cancelled")

        if ticket_id is not None:
            self._enforce_ticket_mandate_and_budget(ticket_id)

        effective_workers = min(max(1, max_workers), self.max_autonomous_workers)
        goal.status = GoalStatus.RUNNING
        goal.truth_status = ExecutionTruthStatus.RUNNING
        self.store.save_goal(goal)
        self._event(
            goal.id,
            "goal.started",
            {
                "profile": verification_profile,
                "mode": "parallel",
                "max_autonomous_workers": effective_workers,
            },
        )

        db_lock = threading.Lock()
        active_futures: dict[concurrent.futures.Future, tuple[GoalTask, str]] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as executor:
            while True:
                with db_lock:
                    tasks = self.store.get_tasks(goal.id)
                    graph = TaskGraph(goal_id=goal.id, tasks=tasks)
                    propagated = graph.propagate_failures()
                    if propagated:
                        self.store.save_tasks(propagated)
                    ready = graph.ready_tasks(allow_simulated=not execute_commands)
                    running_ids = {t.id for t, _ in active_futures.values()}
                    new_ready = [t for t in ready if t.id not in running_ids]

                if not active_futures and not new_ready:
                    break

                saturated_wait = False
                for task in new_ready:
                    if len(active_futures) >= effective_workers:
                        break
                    worker_id = f"autoworker_{goal.id}_{task.id}"
                    now = time.time()
                    lease = WorkerLease(
                        worker_id=worker_id,
                        lane_kind="AUTONOMOUS",
                        ticket_id=ticket_id or goal.id,
                        task_id=task.id,
                        lease_expires_at=now + float(timeout_seconds or 120.0),
                        heartbeat_at=now,
                        attempt_no=task.attempts + 1,
                        is_idempotent=task.is_idempotent,
                        side_effect_uncertain=task.side_effect_uncertain,
                    )
                    with db_lock:
                        if not self.store.acquire_worker_lease(lease, now=now):
                            # Autonomous worker lane is saturated; queue until a slot frees up
                            if task.truth_status != ExecutionTruthStatus.QUEUED:
                                task.truth_status = ExecutionTruthStatus.QUEUED
                                self.store.save_tasks([task])
                            saturated_wait = True
                            continue

                        task.status = TaskStatus.RUNNING
                        task.truth_status = ExecutionTruthStatus.RUNNING
                        task.attempts += 1
                        self.store.save_tasks([task])
                        assignment = self.roles.assign(task)
                        self._event(
                            goal.id,
                            "task.started",
                            {
                                "task_id": task.id,
                                "role": assignment.role.value,
                                "rationale": assignment.rationale,
                                "worker_id": worker_id,
                            },
                        )

                    def make_task_runner(
                        t: GoalTask = task,
                        role_val: str = assignment.role.value,
                        use_wt: bool = isolate_worktree or task.mutates_workspace,
                    ) -> Callable[[], ExecutionOutcome | str]:
                        def run() -> ExecutionOutcome | str:
                            if not (execute_commands and t.command):
                                return f"{role_val} completed directive: {t.title}"
                            wt_path: Path | None = None
                            try:
                                if use_wt:
                                    wt_path = self.worktree_manager.allocate(
                                        ticket_id or goal.id, t.id
                                    )
                                exec_cwd = wt_path if wt_path is not None else self.cwd
                                return self._execute_task_outcome(
                                    t.command,
                                    cwd=exec_cwd,
                                    timeout_seconds=timeout_seconds,
                                    worktree_root=wt_path,
                                )
                            finally:
                                if wt_path is not None:
                                    self.worktree_manager.cleanup(wt_path)

                        return run

                    future = executor.submit(make_task_runner())
                    active_futures[future] = (task, worker_id)

                if not active_futures:
                    if saturated_wait:
                        goal.status = GoalStatus.BLOCKED
                        goal.truth_status = ExecutionTruthStatus.QUEUED
                        self.store.save_goal(goal)
                        self._event(
                            goal.id,
                            "goal.blocked",
                            {"reason": "autonomous_worker_lanes_saturated"},
                        )
                        return goal
                    break

                done, _ = concurrent.futures.wait(
                    active_futures.keys(),
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )

                for future in done:
                    task, worker_id = active_futures.pop(future)
                    with db_lock:
                        self.store.release_worker_lease(worker_id)

                    exc_caught: Exception | None = None
                    res_val: ExecutionOutcome | str | None = None
                    try:
                        res_val = future.result()
                    except Exception as exc:
                        exc_caught = exc

                    with db_lock:
                        if exc_caught is not None:
                            summary = f"Error during task execution: {exc_caught}"
                            task.status = TaskStatus.FAILED
                            task.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
                            task.exit_code = 1
                            task.stderr = str(exc_caught)
                            task.blocked_reason = summary
                            task.result_summary = summary
                            self.store.save_tasks([task])
                            prop_graph = TaskGraph(
                                goal_id=goal.id,
                                tasks=self.store.get_tasks(goal.id),
                            )
                            propagated = prop_graph.propagate_failures()
                            if propagated:
                                self.store.save_tasks(propagated)
                            self._event(
                                goal.id,
                                "task.failed",
                                {"task_id": task.id, "summary": summary},
                            )
                        elif isinstance(res_val, ExecutionOutcome):
                            task.exit_code = res_val.exit_code
                            task.stdout = res_val.stdout
                            task.stderr = res_val.stderr
                            task.blocked_reason = res_val.blocked_reason or None
                            if not res_val.success:
                                summary = (
                                    res_val.blocked_reason
                                    or res_val.stderr.strip()
                                    or f"Command failed with exit code {res_val.exit_code}"
                                )
                                task.status = TaskStatus.FAILED
                                task.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
                                task.result_summary = summary
                                self.store.save_tasks([task])
                                prop_graph = TaskGraph(
                                    goal_id=goal.id,
                                    tasks=self.store.get_tasks(goal.id),
                                )
                                propagated = prop_graph.propagate_failures()
                                if propagated:
                                    self.store.save_tasks(propagated)
                                self._event(
                                    goal.id,
                                    "task.failed",
                                    {
                                        "task_id": task.id,
                                        "exit_code": res_val.exit_code,
                                        "summary": summary,
                                    },
                                )
                            else:
                                summary = res_val.stdout.strip() or "command completed"
                                task.status = TaskStatus.COMPLETED
                                task.truth_status = ExecutionTruthStatus.VERIFIED_SUCCESS
                                task.result_summary = summary
                                self.store.save_tasks([task])
                                self._checkpoint(
                                    goal.id,
                                    task.id,
                                    f"task-completed:{task.title}",
                                    {"role": task.role.value, "summary": summary},
                                )
                                self._event(
                                    goal.id,
                                    "task.completed",
                                    {"task_id": task.id, "summary": summary},
                                )
                        else:
                            summary = str(res_val)
                            task.status = TaskStatus.COMPLETED
                            task.truth_status = ExecutionTruthStatus.SIMULATED
                            task.result_summary = summary
                            self.store.save_tasks([task])
                            self._checkpoint(
                                goal.id,
                                task.id,
                                f"task-completed:{task.title}",
                                {"role": task.role.value, "summary": summary},
                            )
                            self._event(
                                goal.id,
                                "task.completed",
                                {"task_id": task.id, "summary": summary},
                            )

            tasks = self.store.get_tasks(goal.id)
            if any(task.status == TaskStatus.FAILED for task in tasks):
                goal.status = GoalStatus.FAILED
                goal.truth_status = ExecutionTruthStatus.EXECUTION_FAILED
                self.store.save_goal(goal)
                self._event(goal.id, "goal.failed", {"reason": "parallel_task_failed"})
                return goal

            stop_reason = self.stop_policy.should_stop_for_retries(goal, tasks)
            if stop_reason:
                goal.status = GoalStatus.BLOCKED
                goal.truth_status = ExecutionTruthStatus.BLOCKED
                self.store.save_goal(goal)
                self._event(goal.id, "goal.blocked", {"reason": stop_reason})
                return goal

            if any(task.status != TaskStatus.COMPLETED for task in tasks):
                goal.status = GoalStatus.BLOCKED
                goal.truth_status = ExecutionTruthStatus.BLOCKED
                self.store.save_goal(goal)
                self._event(goal.id, "goal.blocked", {"reason": "pending_tasks_remain"})
                return goal

            return self.verify_goal(
                goal.id,
                verification_profile,
                simulated_run=not execute_commands,
            )

    def execute_operator_lane(
        self,
        action_name: str,
        callback: Callable[[], Any],
        ticket_id: str = "operator_control",
    ) -> Any:
        """Execute an operator control action on the reserved OPERATOR_CONTROL lane."""
        now = time.time()
        worker_id = f"op_lane_{action_name}"
        lease = WorkerLease(
            worker_id=worker_id,
            lane_kind="OPERATOR_CONTROL",
            ticket_id=ticket_id,
            task_id=action_name,
            lease_expires_at=now + 30.0,
            heartbeat_at=now,
            is_idempotent=True,
        )
        if not self.store.acquire_worker_lease(lease, now=now):
            raise LeaseCapacityError("Reserved OPERATOR_CONTROL lane is currently busy")
        try:
            return callback()
        finally:
            self.store.release_worker_lease(worker_id)

    def resume_goal(
        self,
        goal_id: str,
        verification_profile: str = "standard",
        execute_commands: bool = False,
        now: float | None = None,
        ticket_id: str | None = None,
        isolate_worktree: bool = False,
    ) -> Goal:
        """Reconcile orphaned RUNNING tasks before resuming goal execution."""
        reconciled = self.store.reconcile_orphaned_running_tasks(goal_id, now=now)
        for task in reconciled:
            self._event(
                goal_id,
                "task.reconciled",
                {
                    "task_id": task.id,
                    "status": task.status.value,
                    "truth_status": task.truth_status.value,
                    "blocked_reason": task.blocked_reason,
                },
            )
        if any(t.truth_status == ExecutionTruthStatus.WAITING_APPROVAL for t in reconciled):
            goal = self._require_goal(goal_id)
            goal.status = GoalStatus.BLOCKED
            goal.truth_status = ExecutionTruthStatus.WAITING_APPROVAL
            self.store.save_goal(goal)
            self._event(
                goal.id,
                "goal.blocked",
                {"reason": "orphaned_non_idempotent_task_requires_approval"},
            )
            return goal

        return self.run_goal(
            goal_id,
            verification_profile=verification_profile,
            execute_commands=execute_commands,
            ticket_id=ticket_id,
            isolate_worktree=isolate_worktree,
        )

    def cancel_goal(self, goal_id: str) -> Goal:
        goal = self._require_goal(goal_id)
        goal.status = GoalStatus.CANCELLED
        goal.truth_status = ExecutionTruthStatus.CANCELLED
        self.store.save_goal(goal)
        self._checkpoint(goal.id, None, "goal-cancelled", {})
        self._event(goal.id, "goal.cancelled", {})
        return goal

    def verify_goal(
        self,
        goal_id: str,
        verification_profile: str = "standard",
        *,
        simulated_run: bool | None = None,
    ) -> Goal:
        VerificationPipeline.validate_profile(verification_profile)
        goal = self._require_goal(goal_id)
        goal.status = GoalStatus.VERIFYING
        self.store.save_goal(goal)
        passed, results = VerificationPipeline.for_profile(verification_profile, self.cwd).run()
        run = VerificationRun(
            id=new_id("verify"),
            goal_id=goal.id,
            profile=verification_profile,
            passed=passed,
            results=results,
        )
        self.store.save_verification_run(run)
        self._checkpoint(goal.id, None, "verification-completed", {"passed": passed})
        self._event(goal.id, "goal.verification", {"passed": passed, "profile": verification_profile})

        tasks = self.store.get_tasks(goal.id)
        all_simulated = (
            simulated_run
            if simulated_run is not None
            else all(t.truth_status == ExecutionTruthStatus.SIMULATED for t in tasks)
        )
        has_real_gates = verification_profile != "none" and len(results) > 0

        criteria = self.store.get_criteria(goal.id)
        for item in criteria:
            item.satisfied = passed
            if not passed:
                item.evidence = "verification failed"
            elif not has_real_gates:
                item.evidence = f"verification:{run.id}:unverified_profile_none"
            else:
                item.evidence = f"verification:{run.id}"
        self.store.save_criteria(goal.id, criteria)

        if not passed:
            goal.status = GoalStatus.BLOCKED
            goal.truth_status = ExecutionTruthStatus.VERIFICATION_FAILED
        elif all_simulated:
            # Keep legacy GoalStatus.SATISFIED for directive simulation compatibility
            # while strictly setting truth_status = SIMULATED (never VERIFIED_SUCCESS).
            goal.status = GoalStatus.SATISFIED
            goal.truth_status = ExecutionTruthStatus.SIMULATED
        elif not has_real_gates:
            # Real command run with profile="none" has 0 verification gates -> UNAVAILABLE
            goal.status = GoalStatus.SATISFIED
            goal.truth_status = ExecutionTruthStatus.UNAVAILABLE
        else:
            goal.status = GoalStatus.SATISFIED
            goal.truth_status = ExecutionTruthStatus.VERIFIED_SUCCESS

        self.store.save_goal(goal)
        status = "success" if passed else "failed"
        self._memory(goal.id, "verification", f"{verification_profile}:{status}")
        self._mirror_legacy_memory(goal, status, results)
        self._event(
            goal.id,
            "goal.completed",
            {"status": goal.status.value, "truth_status": goal.truth_status.value},
        )
        return goal

    def status(self, goal_id: str) -> dict[str, Any]:
        return self.store.snapshot(goal_id)

    def list_goals(self) -> list[Goal]:
        return self.store.list_goals()

    def _enforce_ticket_mandate_and_budget(self, ticket_id: str) -> None:
        mandate = self.store.verify_mandate_integrity(ticket_id)
        row = self.store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(ticket_id)
        actual_cost = row.get("actual_cost")
        estimated_cost = row.get("estimated_cost")
        spent = (
            float(actual_cost)
            if actual_cost is not None
            else (float(estimated_cost) if estimated_cost is not None else 0.0)
        )
        if spent > mandate.cost_budget:
            raise RuntimeError(
                f"Ticket {ticket_id} cost budget exhausted: spent={spent} > budget={mandate.cost_budget}"
            )

    def _execute_task_outcome(
        self,
        command: str,
        cwd: Path | None = None,
        timeout_seconds: float | None = None,
        worktree_root: Path | None = None,
    ) -> ExecutionOutcome:
        exec_cwd = cwd if cwd is not None else self.cwd
        timeout_int = int(timeout_seconds) if timeout_seconds is not None else 60
        return LocalExecutor(
            exec_cwd,
            timeout_seconds=timeout_int,
            strict_mode=True,
            worktree_root=worktree_root,
        ).run(command)

    def _execute_task(self, command: str | None) -> str:
        if not command:
            return "no command configured"
        outcome = self._execute_task_outcome(command)
        if not outcome.success:
            return outcome.blocked_reason or outcome.stderr or f"exit {outcome.exit_code}"
        return outcome.stdout.strip() or "command completed"

    def _require_goal(self, goal_id: str) -> Goal:
        goal = self.store.get_goal(goal_id)
        if goal is None:
            raise KeyError(goal_id)
        return goal

    def _checkpoint(
        self,
        goal_id: str,
        task_id: str | None,
        label: str,
        state: dict[str, Any],
    ) -> None:
        self.store.add_checkpoint(
            Checkpoint(
                id=new_id("checkpoint"),
                goal_id=goal_id,
                task_id=task_id,
                label=label,
                state=state,
            )
        )

    def _event(self, goal_id: str, event_name: str, payload: dict[str, Any]) -> None:
        self.store.add_event(goal_id, event_name, payload)
        self.events.emit(event_name, {"goal_id": goal_id, **payload})

    def _memory(self, goal_id: str, kind: str, content: str) -> None:
        self.store.add_memory(goal_id, kind, content)
        self.events.emit("memory.recorded", {"goal_id": goal_id, "kind": kind})

    def _mirror_legacy_memory(
        self,
        goal: Goal,
        status: str,
        results: list[dict[str, Any]],
    ) -> None:
        memory_store = self.memory_store
        if memory_store is None:
            try:
                memory_store = MemoryStore()
            except Exception:
                return
        errors = [
            str(item.get("stderr") or item.get("blocked_reason") or "")
            for item in results
            if not item.get("passed")
        ]
        try:
            memory_store.record(
                MemoryEntry(
                    goal=goal.title,
                    status=status,
                    error_summary="; ".join(errors)[:500],
                    recipe_used="goal-engine-v1",
                    context={"goal_id": goal.id},
                )
            )
        except Exception:
            return
