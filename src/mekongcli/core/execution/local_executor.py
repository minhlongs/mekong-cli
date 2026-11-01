# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Local execution runtime with command safety, worktree boundaries, and timeouts."""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from src.core.command_sanitizer import CommandSanitizer


@dataclass
class ExecutionOutcome:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    blocked_reason: str = ""

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.blocked_reason


@dataclass
class TaskResult:
    summary: str
    success: bool


class LocalExecutor:
    """Executes allowed local commands without invoking a shell."""

    def __init__(
        self,
        cwd: str | Path = ".",
        timeout_seconds: int = 60,
        strict_mode: bool = True,
        worktree_root: str | Path | None = None,
    ) -> None:
        self.cwd = Path(cwd)
        self.timeout_seconds = timeout_seconds
        self.strict_mode = strict_mode
        self.worktree_root = Path(worktree_root).resolve() if worktree_root else None
        self._sanitizer = CommandSanitizer(strict_mode=strict_mode)

    def _validate_worktree_escape(self, args: list[str]) -> str | None:
        """Verify command arguments do not escape the isolated worktree boundary."""
        root = self.worktree_root or self.cwd.resolve()
        for token in args:
            parts = token.split("=", 1) if "=" in token else [token]
            for raw_part in parts:
                part = raw_part[7:] if raw_part.startswith("file://") else raw_part
                if not part:
                    continue
                if ".." in Path(part).parts:
                    return f"Path escape detected outside worktree boundary: {token}"
                if self.worktree_root is not None:
                    if part.startswith("/") or part.startswith("~"):
                        try:
                            candidate = Path(part).expanduser().resolve()
                            candidate.relative_to(root)
                        except ValueError:
                            return f"Absolute path outside isolated worktree rejected: {token}"
                    else:
                        rel_candidate = root / part
                        if rel_candidate.exists() or rel_candidate.is_symlink():
                            try:
                                rel_candidate.resolve().relative_to(root)
                            except ValueError:
                                return f"Symlink escape outside isolated worktree rejected: {token}"
        return None

    def run(self, command: str) -> ExecutionOutcome:
        started = time.time()
        safe = self._sanitizer.sanitize(command)
        if not safe.is_safe:
            reason = safe.blocked_reason or (
                f"Blocked by CommandSanitizer: {', '.join(safe.blocked_patterns)}"
                if safe.blocked_patterns
                else "Blocked by CommandSanitizer"
            )
            return ExecutionOutcome(
                command=command,
                exit_code=126,
                stdout="",
                stderr="",
                duration_ms=0.0,
                blocked_reason=reason,
            )

        try:
            args = shlex.split(safe.sanitized_command)
        except ValueError as exc:
            return ExecutionOutcome(
                command=safe.sanitized_command,
                exit_code=126,
                stdout="",
                stderr=str(exc),
                duration_ms=0.0,
                blocked_reason=f"Malformed command syntax: {exc}",
            )

        escape_reason = self._validate_worktree_escape(args)
        if escape_reason:
            return ExecutionOutcome(
                command=safe.sanitized_command,
                exit_code=126,
                stdout="",
                stderr=escape_reason,
                duration_ms=0.0,
                blocked_reason=escape_reason,
            )

        try:
            proc = subprocess.run(
                args,
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            return ExecutionOutcome(
                command=safe.sanitized_command,
                exit_code=proc.returncode,
                stdout=proc.stdout[-4000:],
                stderr=proc.stderr[-4000:],
                duration_ms=(time.time() - started) * 1000,
            )
        except subprocess.TimeoutExpired as exc:
            out_str = exc.stdout if isinstance(exc.stdout, str) else ""
            err_str = exc.stderr if isinstance(exc.stderr, str) else ""
            return ExecutionOutcome(
                command=safe.sanitized_command,
                exit_code=124,
                stdout=out_str[-4000:],
                stderr=err_str[-4000:],
                duration_ms=(time.time() - started) * 1000,
                blocked_reason=f"Timed out after {self.timeout_seconds}s",
            )
        except OSError as exc:
            return ExecutionOutcome(
                command=safe.sanitized_command,
                exit_code=127,
                stdout="",
                stderr=str(exc),
                duration_ms=(time.time() - started) * 1000,
                blocked_reason=str(exc),
            )
