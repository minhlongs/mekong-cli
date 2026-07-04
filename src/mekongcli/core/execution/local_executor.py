"""Local execution runtime with command safety and timeouts."""

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

    def __init__(self, cwd: str | Path = ".", timeout_seconds: int = 60) -> None:
        self.cwd = Path(cwd)
        self.timeout_seconds = timeout_seconds
        self._sanitizer = CommandSanitizer(strict_mode=False)

    def run(self, command: str) -> ExecutionOutcome:
        started = time.time()
        safe = self._sanitizer.sanitize(command)
        if not safe.is_safe:
            return ExecutionOutcome(
                command=command,
                exit_code=126,
                stdout="",
                stderr="",
                duration_ms=0.0,
                blocked_reason=safe.blocked_reason,
            )

        try:
            proc = subprocess.run(
                shlex.split(safe.sanitized_command),
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
            return ExecutionOutcome(
                command=safe.sanitized_command,
                exit_code=124,
                stdout=(exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
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
