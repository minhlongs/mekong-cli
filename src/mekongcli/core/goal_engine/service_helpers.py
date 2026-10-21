# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""GoalEngine execution helpers — parallel runner, task execution, checkpoints, and memory mirroring."""
from __future__ import annotations

import concurrent.futures
import threading
from pathlib import Path
from typing import Any

from src.core.memory_canonical import MemoryEntry, MemoryStore
from src.mekongcli.core.execution import LocalExecutor
from src.mekongcli.core.swarm import RoleRegistry
from src.mekongcli.core.telemetry import GoalEventBusAdapter
from src.mekongcli.core.verification import VerificationPipeline

from .models import Checkpoint, Goal, GoalStatus, GoalTask, TaskGraph, TaskStatus, new_id
from .store import SQLiteGoalStore


class GoalEngineHelpersMixin:
    """Internal helper methods and parallel execution loop for GoalEngine."""

    store: SQLiteGoalStore
    cwd: Path
    roles: RoleRegistry
    events: GoalEventBusAdapter
    stop_policy: Any
    memory_store: MemoryStore | None

    def verify_goal(self, goal_id: str, verification_profile: str = "standard") -> Goal:
        raise NotImplementedError

    def run_goal_parallel(
        self,
        goal_id: str,
        verification_profile: str = "standard",
        execute_commands: bool = False,
        max_workers: int = 3,
        timeout_seconds: float | None = None,
    ) -> Goal:
        VerificationPipeline.validate_profile(verification_profile)
        goal = self._require_goal(goal_id)
        if goal.status == GoalStatus.CANCELLED:
            raise RuntimeError(f"Goal {goal_id} is cancelled")

        goal.status = GoalStatus.RUNNING
        self.store.save_goal(goal)
        self._event(goal.id, "goal.started", {"profile": verification_profile, "mode": "parallel"})

        db_lock = threading.Lock()
        active_futures: dict[concurrent.futures.Future, GoalTask] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                with db_lock:
                    tasks = self.store.get_tasks(goal.id)
                    ready = TaskGraph(goal_id=goal.id, tasks=tasks).ready_tasks()
                    running_ids = {t.id for t in active_futures.values()}
                    new_ready = [t for t in ready if t.id not in running_ids]

                if not active_futures and not new_ready:
                    break

                for task in new_ready:
                    with db_lock:
                        task.status = TaskStatus.RUNNING
                        task.attempts += 1
                        self.store.save_tasks([task])
                        assignment = self.roles.assign(task)
                        self._event(
                            goal.id,
                            "task.started",
                            {"task_id": task.id, "role": assignment.role.value, "rationale": assignment.rationale},
                        )

                    def make_task_runner(
                        t: Any = task, role_val: str = assignment.role.value
                    ) -> Any:
                        return lambda: (
                            self._execute_task(t.command)
                            if execute_commands and t.command
                            else f"{role_val} completed directive: {t.title}"
                        )

                    active_futures[executor.submit(make_task_runner())] = task

                done, _ = concurrent.futures.wait(
                    active_futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED
                )
                for future in done:
                    task = active_futures.pop(future)
                    try:
                        summary = future.result()
                    except Exception as e:
                        summary = f"Error during task execution: {str(e)}"
                    with db_lock:
                        task.status = TaskStatus.COMPLETED
                        task.result_summary = summary
                        self.store.save_tasks([task])
                        self._checkpoint(
                            goal.id, task.id, f"task-completed:{task.title}",
                            {"role": task.role.value, "summary": summary},
                        )
                        self._event(goal.id, "task.completed", {"task_id": task.id, "summary": summary})

            tasks = self.store.get_tasks(goal.id)
            stop_reason = self.stop_policy.should_stop_for_retries(goal, tasks)
            if stop_reason:
                goal.status = GoalStatus.BLOCKED
                self.store.save_goal(goal)
                self._event(goal.id, "goal.blocked", {"reason": stop_reason})
                return goal

            if any(task.status != TaskStatus.COMPLETED for task in tasks):
                goal.status = GoalStatus.BLOCKED
                self.store.save_goal(goal)
                self._event(goal.id, "goal.blocked", {"reason": "pending_tasks_remain"})
                return goal

            return self.verify_goal(goal.id, verification_profile)

    def _execute_task(self, command: str | None) -> str:
        if not command:
            return "no command configured"
        outcome = LocalExecutor(self.cwd).run(command)
        if not outcome.success:
            return outcome.blocked_reason or outcome.stderr or f"exit {outcome.exit_code}"
        return outcome.stdout.strip() or "command completed"

    def _require_goal(self, goal_id: str) -> Goal:
        goal = self.store.get_goal(goal_id)
        if goal is None:
            raise KeyError(goal_id)
        return goal

    def _checkpoint(self, goal_id: str, task_id: str | None, label: str, state: dict[str, Any]) -> None:
        self.store.add_checkpoint(
            Checkpoint(id=new_id("checkpoint"), goal_id=goal_id, task_id=task_id, label=label, state=state)
        )

    def _event(self, goal_id: str, event_name: str, payload: dict[str, Any]) -> None:
        self.store.add_event(goal_id, event_name, payload)
        self.events.emit(event_name, {"goal_id": goal_id, **payload})

    def _memory(self, goal_id: str, kind: str, content: str) -> None:
        self.store.add_memory(goal_id, kind, content)
        self.events.emit("memory.recorded", {"goal_id": goal_id, "kind": kind})

    def _mirror_legacy_memory(self, goal: Goal, status: str, results: list[dict[str, Any]]) -> None:
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
                    goal=goal.title, status=status, error_summary="; ".join(errors)[:500],
                    recipe_used="goal-engine-v1", context={"goal_id": goal.id},
                )
            )
        except Exception:
            return
