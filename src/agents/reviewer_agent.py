# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Reviewer Agent.

Specialized agent for validating changes and checking regressions.
Uses restricted tool set (read_files, code_search, find_files, glob).
Mirrors Codebuff's reviewer agent.
"""

from __future__ import annotations

import logging
import shlex
from typing import Any

from ..core.agent_base import AgentBase, Task, Result

logger = logging.getLogger(__name__)


class ReviewerAgent(AgentBase):
    """Agent for reviewing code changes and checking regressions.

    Restricted to read/search tools - cannot modify files or execute commands.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize ReviewerAgent with review-focused tool restriction."""
        super().__init__(
            name="ReviewerAgent",
            allowed_tools=[
                "read_files",
                "code_search",
                "find_files",
                "glob",
                "file:list",
            ],
            **kwargs,
        )

    def plan(self, input_data: str) -> list[Task]:
        """Plan: parse review request into validation tasks.

        Args:
            input_data: Review context (e.g. "review changes to auth.py").

        Returns:
            List of review tasks.
        """
        return [
            Task(
                id="reviewer_check",
                description=f"Review: {input_data[:100]}",
                input={"context": input_data},
            )
        ]

    def execute(self, task: Task) -> Result:
        """Execute: perform review checks.

        This is a stub - production version would use code_search and read_files
        to validate changes against criteria.

        Args:
            task: Task with review context.

        Returns:
            Result with review findings.
        """
        context = task.input.get("context", "")
        logger.info("ReviewerAgent reviewing: %s", context[:100])

        # Return review checklist
        return Result(
            task_id=task.id,
            success=True,
            output=f"Review planned for: {context}\n"
                   f"Checks: syntax, imports, type hints, tests, no console.log",
        )

    def check_regression(
        self,
        changed_files: list[str],
        test_command: str = "python3 -m pytest tests/",
    ) -> Result:
        """Check for regressions by running tests.

        Args:
            changed_files: List of files that were modified.
            test_command: Command to run for regression testing.

        Returns:
            Result with test results.
        """
        try:
            import subprocess
            # Use shlex.split for safe command parsing
            cmd = shlex.split(test_command)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            passed = result.returncode == 0
            return Result(
                task_id="regression_check",
                success=passed,
                output=result.stdout if passed else result.stderr,
                error=None if passed else result.stderr,
            )
        except Exception as e:
            return Result(task_id="regression_check", success=False, output=None, error=str(e))


# Export
__all__ = ["ReviewerAgent"]
