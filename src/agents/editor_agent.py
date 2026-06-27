"""Mekong CLI - Editor Agent.

Specialized agent for precise code edits. Uses restricted tool set
(read_files, write_file, str_replace, apply_patch, run_terminal_command).
Mirrors Codebuff's editor agent.
"""

from __future__ import annotations

import logging
from typing import Any

from ..core.agent_base import AgentBase, Task, Result

logger = logging.getLogger(__name__)


class EditorAgent(AgentBase):
    """Agent for precise code editing.

    Restricted to file modification and terminal tools.
    Cannot read arbitrary files outside the project or spawn other agents.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize EditorAgent with edit-focused tool restriction."""
        super().__init__(
            name="EditorAgent",
            allowed_tools=[
                "read_files",
                "write_file",
                "str_replace",
                "apply_patch",
                "run_terminal_command",
                "shell:run",
                "file:list",
                "file:write",
            ],
            **kwargs,
        )

    def plan(self, input_data: str) -> list[Task]:
        """Plan: parse edit request into tasks.

        Args:
            input_data: Edit description (e.g. "add error handling to api.py").

        Returns:
            List of edit tasks.
        """
        # Simple single-task plan; production version would decompose
        return [
            Task(
                id="editor_apply",
                description=f"Apply edit: {input_data[:100]}",
                input={"description": input_data},
            )
        ]

    def execute(self, task: Task) -> Result:
        """Execute: apply the edit.

        This is a stub - production version would use actual file editing
        via write_file, str_replace, or apply_patch tools.

        Args:
            task: Task with edit description.

        Returns:
            Result indicating edit was planned (actual execution via tools).
        """
        description = task.input.get("description", "")
        logger.info("EditorAgent would apply: %s", description[:100])

        # Return a structured plan for the edit
        # Actual file modifications happen via tool calls in the orchestrator
        return Result(
            task_id=task.id,
            success=True,
            output=f"Edit planned: {description}\n"
                   f"Use tools: read_files, str_replace, write_file to apply.",
        )

    def apply_patch(self, file_path: str, patch: str) -> Result:
        """Apply a unified diff patch to a file.

        Args:
            file_path: Path to the file to patch.
            patch: Unified diff patch string.

        Returns:
            Result indicating success or failure.
        """
        try:
            import subprocess
            result = subprocess.run(
                ["patch", "-p1", "-u"],
                input=patch,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return Result(task_id="apply_patch", success=True, output=result.stdout)
            return Result(task_id="apply_patch", success=False, output=None, error=result.stderr)
        except Exception as e:
            return Result(task_id="apply_patch", success=False, output=None, error=str(e))


# Export
__all__ = ["EditorAgent"]
