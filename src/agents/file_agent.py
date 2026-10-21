# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - FileAgent

Real agent for file system operations: search, read, create, analyze.
"""

import subprocess
from typing import List

from ..core.agent_base import AgentBase, Result, Task
from .file_agent_ops import FileAgentOpsMixin


class FileAgent(FileAgentOpsMixin, AgentBase):
    """
    Agent for file system operations.

    Supports:
    - find <pattern>: Search for files matching pattern
    - read <path>: Read file content
    - write <path> <content>: Write content to file
    - tree [depth]: Show directory tree
    - stats: Show project file statistics
    - grep <pattern>: Search content in files
    """

    def __init__(self, cwd: str = ".") -> None:
        """Initialize FileAgent with working directory."""
        super().__init__(name="FileAgent")
        self.cwd = cwd

    def plan(self, input_data: str) -> List[Task]:
        """Parse file command into tasks."""
        parts = input_data.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "find":
            return [
                Task(
                    id="file_find",
                    description=f"Find files: {args}",
                    input={"pattern": args},
                )
            ]

        elif command == "read":
            return [
                Task(id="file_read", description=f"Read: {args}", input={"path": args})
            ]

        elif command == "write":
            write_parts = args.split(maxsplit=1)
            path = write_parts[0] if write_parts else ""
            content = write_parts[1] if len(write_parts) > 1 else ""
            return [
                Task(
                    id="file_write",
                    description=f"Write: {path}",
                    input={"path": path, "content": content},
                )
            ]

        elif command == "tree":
            depth = int(args) if args.isdigit() else 3
            return [
                Task(
                    id="file_tree",
                    description=f"Directory tree (depth {depth})",
                    input={"depth": depth},
                )
            ]

        elif command == "stats":
            return [
                Task(
                    id="file_stats",
                    description="Project file statistics",
                    input={"path": "src"},
                )
            ]

        elif command == "grep":
            return [
                Task(
                    id="file_grep", description=f"Grep: {args}", input={"pattern": args}
                )
            ]

        else:
            return [
                Task(
                    id="file_custom", description=input_data, input={"raw": input_data}
                )
            ]

    def execute(self, task: Task) -> Result:
        """Execute file operation."""
        try:
            if task.id == "file_find":
                return self._exec_find(task)
            elif task.id == "file_read":
                return self._exec_read(task)
            elif task.id == "file_write":
                return self._exec_write(task)
            elif task.id == "file_tree":
                return self._exec_tree(task)
            elif task.id == "file_stats":
                return self._exec_stats(task)
            elif task.id == "file_grep":
                return self._exec_grep(task)
            else:
                return Result(
                    task_id=task.id,
                    success=False,
                    output=None,
                    error=f"Unknown task: {task.id}",
                )
        except subprocess.TimeoutExpired:
            return Result(
                task_id=task.id, success=False, output=None, error="Command timed out"
            )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))


__all__ = ["FileAgent", "subprocess"]
