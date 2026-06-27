"""Mekong CLI - FilePicker Agent.

Specialized agent that scans the codebase and surfaces relevant files
for a given task. Uses restricted tool set (read_files, find_files, glob, code_search).
Mirrors Codebuff's file-picker agent.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from ..core.agent_base import AgentBase, Task, Result

logger = logging.getLogger(__name__)


class FilePickerAgent(AgentBase):
    """Agent that scans the codebase and surfaces relevant files.

    Restricted to file/search tools only - cannot execute or modify code.
    """

    def __init__(
        self,
        root: str | None = None,
        max_files: int = 20,
        max_depth: int = 10,
        **kwargs: Any,
    ) -> None:
        """Initialize FilePickerAgent.

        Args:
            root: Root directory to scan. Defaults to cwd.
            max_files: Maximum files to surface in results.
            max_depth: Maximum directory depth to scan (prevents DoS).
            **kwargs: Passed to AgentBase.
        """
        super().__init__(
            name="FilePickerAgent",
            allowed_tools=["read_files", "find_files", "glob", "code_search", "file:list"],
            **kwargs,
        )
        self.root = Path(root or os.getcwd())
        self.max_files = max_files
        self.max_depth = max_depth

    def plan(self, input_data: str) -> list[Task]:
        """Plan: parse goal into file discovery tasks.

        Args:
            input_data: Goal description (e.g. "find auth-related files").

        Returns:
            Single task to discover relevant files.
        """
        return [
            Task(
                id="file_picker_scan",
                description=f"Scan codebase for: {input_data}",
                input={"goal": input_data, "root": str(self.root), "max_files": self.max_files},
            )
        ]

    def execute(self, task: Task) -> Result:
        """Execute: scan filesystem for relevant files.

        Uses simple keyword matching against file paths and names.
        In production, this would use code_search (ripgrep) for content matching.

        Args:
            task: Task with 'goal' in input.

        Returns:
            Result with list of relevant file paths.
        """
        goal = task.input.get("goal", "")
        root = Path(task.input.get("root", self.root))
        max_files = task.input.get("max_files", self.max_files)

        try:
            relevant = self._find_relevant(goal, root, max_files)
            output = "\n".join(f"  {f}" for f in relevant)
            return Result(
                task_id=task.id,
                success=True,
                output=output,
            )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))

    def _find_relevant(self, goal: str, root: Path, max_files: int) -> list[str]:
        """Find files relevant to the goal using keyword matching.

        Args:
            goal: Search goal/keywords.
            root: Directory to search.
            max_files: Maximum results.

        Returns:
            List of relative file paths.
        """
        keywords = [kw.lower() for kw in goal.split() if len(kw) > 2]
        if not keywords:
            keywords = [goal.lower()]

        # Common code extensions to scan
        extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".yaml", ".yml", ".json", ".toml"}

        scored: list[tuple[int, Path]] = []
        try:
            for path in root.rglob("*"):
                # Skip symlinks to prevent following outside project root
                if path.is_symlink():
                    continue
                if not path.is_file():
                    continue
                if path.suffix not in extensions:
                    continue
                # Depth limit to prevent DoS on deep trees
                try:
                    rel_parts = path.relative_to(root).parts
                except ValueError:
                    continue
                depth = len(rel_parts)
                if depth > self.max_depth:
                    continue
                # Skip hidden dirs and common excludes
                if any(p.startswith(".") or p in ("node_modules", "__pycache__", ".git", "dist", "build") for p in rel_parts):
                    continue
                rel = str(Path(*rel_parts))
                score = sum(1 for kw in keywords if kw in rel.lower())
                if score > 0:
                    scored.append((score, path))
        except (OSError, PermissionError):
            pass

        # Sort by score descending, take top N
        scored.sort(key=lambda x: -x[0])
        return [str(p.relative_to(root)) for _, p in scored[:max_files]]


# Export
__all__ = ["FilePickerAgent"]
