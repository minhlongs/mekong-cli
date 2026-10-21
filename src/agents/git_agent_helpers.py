# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""GitAgent helpers for command construction and conventional semantic commits."""

from typing import Any, List, cast

from ..core.agent_base import Result, Task


def _git_mod() -> Any:
    import src.agents.git_agent as _mod
    return _mod


class GitAgentHelpersMixin:
    """Mixin providing git command builder and semantic commit helpers."""

    cwd: str

    def _build_command(self, task: Task) -> List[str]:
        """Build git command list from task."""
        cmd_map = {
            "git_status": ["git", "status", "--short"],
            "git_diff": ["git", "diff", "--stat"],
            "git_log": ["git", "log", "--oneline", f"-{task.input.get('count', 10)}"],
            "git_add": ["git", "add", "-A"],
            "git_commit": [
                "git",
                "commit",
                "-m",
                task.input.get("message", "auto-commit"),
            ],
            "git_branch_list": ["git", "branch", "-a"],
            "git_branch_create": [
                "git",
                "checkout",
                "-b",
                task.input.get("name", "new-branch"),
            ],
        }

        cmd = cmd_map.get(task.id)
        if cmd:
            return cmd

        if task.id == "git_push":
            parts = ["git", "push", task.input.get("remote", "origin")]
            branch = task.input.get("branch", "")
            if branch:
                parts.append(branch)
            return parts

        if task.id == "git_pull":
            return ["git", "pull", task.input.get("remote", "origin")]

        if task.id == "git_checkout":
            return ["git", "checkout", task.input.get("target", "main")]

        custom = cast(str, task.input.get("cmd", ""))
        return ["git"] + custom.split()

    def semantic_commit(self, message: str = "") -> Result:
        """Auto-detect commit type and create a conventional commit."""
        if not message:
            message = self._auto_commit_message()

        tasks = [
            Task(id="git_add", description="Stage all changes", input={}),
            Task(
                id="git_commit",
                description=f"Commit: {message}",
                input={"message": message},
            ),
        ]
        results: list[Result] = []
        for task in tasks:
            results.append(self.execute(task))  # type: ignore[attr-defined]
        return results[-1] if results else Result(
            task_id="semantic_commit", success=False, output=None, error="No tasks"
        )

    def _auto_commit_message(self) -> str:
        """Detect commit type from changed files."""
        sub = _git_mod().subprocess
        try:
            diff_result = sub.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            files = diff_result.stdout.strip().splitlines()
            if not files:
                diff_result = sub.run(
                    ["git", "diff", "--name-only"],
                    cwd=self.cwd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                files = diff_result.stdout.strip().splitlines()
        except (sub.TimeoutExpired, OSError):
            return "chore: auto-commit via Mekong CLI"

        commit_type = self._detect_type(files)
        scope = self._detect_scope(files)
        scope_str = f"({scope})" if scope else ""
        return f"{commit_type}{scope_str}: update {len(files)} files"

    @staticmethod
    def _detect_type(files: List[str]) -> str:
        """Detect conventional commit type from file paths."""
        test_files = [f for f in files if "test" in f.lower()]
        doc_files = [f for f in files if f.endswith(".md") or "docs/" in f]

        if len(test_files) == len(files) and files:
            return "test"
        if len(doc_files) == len(files) and files:
            return "docs"
        if any("fix" in f.lower() for f in files):
            return "fix"
        return "feat"

    @staticmethod
    def _detect_scope(files: List[str]) -> str:
        """Detect scope from common file path prefix."""
        if not files:
            return ""
        dirs = set()
        for f in files:
            parts = f.split("/")
            if len(parts) > 1:
                dirs.add(parts[-2] if len(parts) > 2 else parts[0])
        if len(dirs) == 1:
            return dirs.pop()
        return ""
