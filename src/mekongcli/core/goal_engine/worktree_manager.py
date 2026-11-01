# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Git worktree workspace isolation manager for concurrent autonomous workers.

NOTE: Git worktrees provide workspace filesystem isolation (preventing concurrent
write workers from clobbering each other's working tree in shared ``cwd``), NOT
OS/kernel container sandboxing. Command execution inside a worktree still relies
on ``CommandSanitizer(strict_mode=True)`` and explicit path-escape checks.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path

_logger = logging.getLogger(__name__)

_SAFE_TOKEN_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class WorktreeEscapeError(PermissionError):
    """Raised when a target path escapes the isolated worktree root."""


class WorktreeIsolationManager:
    """Manages isolated per-worker Git worktrees under ``.mekong/worktrees/``."""

    def __init__(self, repo_root: str | Path = ".", base_dir: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.base_dir = (
            Path(base_dir).resolve()
            if base_dir is not None
            else (self.repo_root / ".mekong" / "worktrees").resolve()
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_segment(raw: str) -> str:
        cleaned = _SAFE_TOKEN_RE.sub("_", raw.strip())
        return cleaned[:64] or "task"

    def worktree_path_for(self, ticket_id: str, task_id: str) -> Path:
        safe_ticket = self._sanitize_segment(ticket_id)
        safe_task = self._sanitize_segment(task_id)
        return (self.base_dir / f"{safe_ticket}_{safe_task}").resolve()

    def allocate(self, ticket_id: str, task_id: str) -> Path:
        """Create an isolated workspace directory (using ``git worktree add --detach`` when in a Git repo)."""
        wt_path = self.worktree_path_for(ticket_id, task_id)
        if wt_path.exists():
            self.cleanup(wt_path)

        wt_path.parent.mkdir(parents=True, exist_ok=True)
        git_dir = self.repo_root / ".git"
        if git_dir.exists():
            try:
                proc = subprocess.run(
                    ["git", "worktree", "add", "--detach", str(wt_path), "HEAD"],
                    cwd=str(self.repo_root),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if proc.returncode == 0 and wt_path.exists():
                    return wt_path
            except Exception as exc:
                _logger.debug("git worktree add fallback to isolated directory: %s", exc)

        wt_path.mkdir(parents=True, exist_ok=True)
        return wt_path

    def validate_path_within_worktree(
        self,
        worktree_path: str | Path,
        target_path: str | Path,
    ) -> Path:
        """Ensure ``target_path`` resolves strictly inside ``worktree_path``."""
        root = Path(worktree_path).resolve()
        target_str = str(target_path)
        if ".." in Path(target_str).parts:
            raise WorktreeEscapeError(
                f"Path traversal '..' rejected for '{target_path}' outside '{root}'"
            )
        candidate = (
            Path(target_path).resolve()
            if Path(target_path).is_absolute()
            else (root / target_path).resolve()
        )
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise WorktreeEscapeError(
                f"Target path '{candidate}' escapes isolated worktree '{root}'"
            ) from exc
        return candidate

    def cleanup(self, worktree_path: str | Path) -> None:
        """Deterministically remove an allocated worktree and prune stale git metadata."""
        wt_path = Path(worktree_path).resolve()
        try:
            wt_path.relative_to(self.base_dir)
        except ValueError:
            raise WorktreeEscapeError(
                f"Refusing to cleanup directory '{wt_path}' outside base_dir '{self.base_dir}'"
            )

        git_dir = self.repo_root / ".git"
        if git_dir.exists():
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt_path)],
                    cwd=str(self.repo_root),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            except Exception:
                pass

        if wt_path.exists():
            shutil.rmtree(wt_path, ignore_errors=True)
