# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Goal engine service tying planning, execution, verification, and memory."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.memory_canonical import MemoryEntry, MemoryStore
from src.mekongcli.core.execution import LocalExecutor
from src.mekongcli.core.swarm import RoleRegistry
from src.mekongcli.core.telemetry import GoalEventBusAdapter
from src.mekongcli.core.verification import VerificationPipeline

from .models import (
    Checkpoint,
    Goal,
    GoalStatus,
    GoalTask,
    TaskGraph,
    TaskStatus,
    VerificationRun,
    new_id,
)
from .planner import GoalPlanner
from .service_helpers import GoalEngineHelpersMixin
from .store import SQLiteGoalStore


class GoalEngine(GoalEngineHelpersMixin):
    """Persistent, local-first autonomous goal execution service."""

    def __init__(
        self,
        store: SQLiteGoalStore | None = None,
        cwd: str | Path = ".",
        memory_store: MemoryStore | None = None,
    ) -> None:
        from src.mekongcli.core.governance import StopConditionPolicy

        self.store = store or SQLiteGoalStore()
        self.cwd = Path(cwd)
        self.planner = GoalPlanner()
        self.roles = RoleRegistry()
        self.events = GoalEventBusAdapter()
        self.stop_policy = StopConditionPolicy()
        self.memory_store = memory_store

    def create_goal(self, title: str) -> Goal:
        from src.mekongcli.core.governance import StopConditionPolicy as _SCP

        goal = Goal(id=new_id("goal"), title=title, stop_conditions=list(_SCP.DEFAULTS))
        tasks, criteria = self.planner.decompose(goal.id, title)
        goal.status = GoalStatus.PLANNED
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
    ) -> Goal:
        VerificationPipeline.validate_profile(verification_profile)
        goal = self._require_goal(goal_id)
        if goal.status == GoalStatus.CANCELLED:
            raise RuntimeError(f"Goal {goal_id} is cancelled")

        goal.status = GoalStatus.RUNNING
        self.store.save_goal(goal)
        self._event(goal.id, "goal.started", {"profile": verification_profile})

        tasks = self.store.get_tasks(goal.id)
        graph = TaskGraph(goal_id=goal.id, tasks=tasks)
        completed_any = True
        while completed_any:
            completed_any = False
            for task in graph.ready_tasks():
                task.status = TaskStatus.RUNNING
                task.attempts += 1
                self.store.save_tasks([task])
                assignment = self.roles.assign(task)
                self._event(
                    goal.id,
                    "task.started",
                    {"task_id": task.id, "role": assignment.role.value, "rationale": assignment.rationale},
                )
                summary = (
                    self._execute_task(task.command)
                    if execute_commands and task.command
                    else f"{assignment.role.value} completed directive: {task.title}"
                )
                task.status = TaskStatus.COMPLETED
                task.result_summary = summary
                self.store.save_tasks([task])
                self._checkpoint(
                    goal.id, task.id, f"task-completed:{task.title}",
                    {"role": task.role.value, "summary": summary},
                )
                self._event(goal.id, "task.completed", {"task_id": task.id, "summary": summary})
                completed_any = True
                graph = TaskGraph(goal_id=goal.id, tasks=self.store.get_tasks(goal.id))

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

    def resume_goal(self, goal_id: str, verification_profile: str = "standard") -> Goal:
        return self.run_goal(goal_id, verification_profile=verification_profile)

    def cancel_goal(self, goal_id: str) -> Goal:
        goal = self._require_goal(goal_id)
        goal.status = GoalStatus.CANCELLED
        self.store.save_goal(goal)
        self._checkpoint(goal.id, None, "goal-cancelled", {})
        self._event(goal.id, "goal.cancelled", {})
        return goal

    def verify_goal(self, goal_id: str, verification_profile: str = "standard") -> Goal:
        VerificationPipeline.validate_profile(verification_profile)
        goal = self._require_goal(goal_id)
        goal.status = GoalStatus.VERIFYING
        self.store.save_goal(goal)
        passed, results = VerificationPipeline.for_profile(verification_profile, self.cwd).run()
        run = VerificationRun(
            id=new_id("verify"), goal_id=goal.id, profile=verification_profile, passed=passed, results=results
        )
        self.store.save_verification_run(run)
        self._checkpoint(goal.id, None, "verification-completed", {"passed": passed})
        self._event(goal.id, "goal.verification", {"passed": passed, "profile": verification_profile})

        criteria = self.store.get_criteria(goal.id)
        for item in criteria:
            item.satisfied = passed
            item.evidence = f"verification:{run.id}" if passed else "verification failed"
        self.store.save_criteria(goal.id, criteria)

        goal.status = GoalStatus.SATISFIED if passed else GoalStatus.BLOCKED
        self.store.save_goal(goal)
        status = "success" if passed else "failed"
        self._memory(goal.id, "verification", f"{verification_profile}:{status}")
        self._mirror_legacy_memory(goal, status, results)
        self._event(goal.id, "goal.completed", {"status": goal.status.value})
        return goal

    def status(self, goal_id: str) -> dict[str, Any]:
        return self.store.snapshot(goal_id)

    def list_goals(self) -> list[Goal]:
        return self.store.list_goals()


__all__ = [
    "GoalEngine", "GoalEngineHelpersMixin", "MemoryEntry", "MemoryStore", "LocalExecutor",
    "RoleRegistry", "GoalEventBusAdapter", "VerificationPipeline", "Checkpoint", "Goal",
    "GoalStatus", "GoalTask", "TaskGraph", "TaskStatus", "VerificationRun", "new_id",
    "GoalPlanner", "SQLiteGoalStore",
]
