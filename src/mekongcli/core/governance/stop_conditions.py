"""Stop-condition checks for autonomous goal execution."""

from __future__ import annotations

from src.mekongcli.core.goal_engine.models import Goal, GoalTask


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
        failed_attempts = sum(task.attempts for task in tasks if task.status.value == "failed")
        if failed_attempts >= goal.retry_limit:
            return "verification_repeatedly_fails"
        return ""
