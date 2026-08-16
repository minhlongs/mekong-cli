# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stop-condition checks for autonomous goal execution."""

from __future__ import annotations

from src.mekongcli.core.goal_engine.models import Goal, GoalTask, TaskStatus


class StopConditionPolicy:
    """Applies v1 safety stop conditions before and during execution."""

    DEFAULTS = (
        "secrets_exposed",
        "verification_repeatedly_fails",
        "unsafe_shell_execution_detected",
        "dependency_conflicts_unresolved",
        "memory_corruption_detected",
    )

    def should_stop_for_retries(self, goal: Goal, tasks: list[GoalTask]) -> str:
        for task in tasks:
            if task.status == TaskStatus.FAILED and task.attempts >= task.max_attempts:
                return "verification_repeatedly_fails"
        return ""
