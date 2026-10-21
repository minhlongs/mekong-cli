# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - GitAgent

Real agent for Git operations: status, diff, commit, branch management.
"""

import subprocess
from typing import List

from ..core.agent_base import AgentBase, Result, Task
from .git_agent_helpers import GitAgentHelpersMixin


class GitAgent(GitAgentHelpersMixin, AgentBase):
    """
    Agent for Git repository operations.

    Supports:
    - status: Show working tree status
    - diff: Show unstaged changes
    - log: Show recent commits
    - commit: Stage all and commit
    - push: Push to remote
    - pull: Pull from remote
    - checkout: Switch branches
    - branch: List or create branches
    """

    def __init__(self, cwd: str = ".") -> None:
        """Initialize GitAgent with working directory."""
        super().__init__(name="GitAgent")
        self.cwd = cwd

    def plan(self, input_data: str) -> List[Task]:
        """Parse git command string into tasks."""
        parts = input_data.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "status":
            return [Task(id="git_status", description="Git status", input={})]

        elif command == "diff":
            return [Task(id="git_diff", description="Git diff", input={})]

        elif command == "log":
            count = int(args) if args.isdigit() else 10
            return [
                Task(
                    id="git_log",
                    description=f"Git log (last {count})",
                    input={"count": count},
                )
            ]

        elif command == "commit":
            message = args or "chore: auto-commit via Mekong CLI"
            return [
                Task(id="git_add", description="Stage all changes", input={}),
                Task(
                    id="git_commit",
                    description=f"Commit: {message}",
                    input={"message": message},
                ),
            ]

        elif command == "push":
            remote = args.split()[0] if args else "origin"
            branch = args.split()[1] if len(args.split()) > 1 else ""
            return [
                Task(
                    id="git_push",
                    description=f"Push to {remote}",
                    input={"remote": remote, "branch": branch},
                )
            ]

        elif command == "pull":
            remote = args.split()[0] if args else "origin"
            return [
                Task(
                    id="git_pull",
                    description=f"Pull from {remote}",
                    input={"remote": remote},
                )
            ]

        elif command == "checkout":
            if not args:
                return [
                    Task(
                        id="git_custom",
                        description="checkout requires branch name",
                        input={"cmd": "branch -a"},
                    )
                ]
            return [
                Task(
                    id="git_checkout",
                    description=f"Checkout: {args}",
                    input={"target": args},
                )
            ]

        elif command == "branch":
            if args:
                return [
                    Task(
                        id="git_branch_create",
                        description=f"Create branch: {args}",
                        input={"name": args},
                    )
                ]
            return [Task(id="git_branch_list", description="List branches", input={})]

        else:
            return [
                Task(
                    id="git_custom",
                    description=f"git {input_data}",
                    input={"cmd": input_data},
                )
            ]

    def execute(self, task: Task) -> Result:
        """Execute git command."""
        cmd = self._build_command(task)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout.strip() or result.stderr.strip()
            return Result(
                task_id=task.id,
                success=result.returncode == 0,
                output=output,
                error=result.stderr.strip() if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            return Result(
                task_id=task.id, success=False, output=None, error="Command timed out"
            )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))


__all__ = ["GitAgent", "subprocess"]
