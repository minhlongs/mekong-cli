# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shell command step execution and sanitization for RecipeExecutor."""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from typing import TYPE_CHECKING

from rich.panel import Panel

from src.core.command_sanitizer import CommandSanitizer
from src.core.retry import ExponentialBackoff, call_with_retry
from src.core.verifier import ExecutionResult

if TYPE_CHECKING:
    from rich.console import Console
    from .parser import RecipeStep


def _extract_shell_command(raw_description: str) -> str:
    """Extract clean shell command from step description or markdown backticks."""
    command = raw_description.strip()
    backtick_matches = re.findall(r"`([^`]+)`", command)
    if backtick_matches:
        command = (
            backtick_matches[0].strip()
            if len(backtick_matches) == 1
            else backtick_matches[-1].strip()
        )
    else:
        lower = command.lower()
        for marker in ("command to execute is:", "command is:", "command:"):
            if marker in lower:
                parts = re.split(rf"(?i){re.escape(marker)}\s*", command)
                if len(parts) > 1:
                    command = parts[-1].strip()
                break

    command = command.strip()
    if command.startswith("`") and command.endswith("`") and len(command) >= 2:
        command = command[1:-1].strip()
    elif (command.startswith('"') and command.endswith('"')) or (
        command.startswith("'") and command.endswith("'")
    ):
        command = command[1:-1].strip()
    return command


def _get_executor_facade():
    """Return executor facade module so monkeypatches on executor.subprocess work."""
    return (
        sys.modules.get("src.harness.pev.executor")
        or sys.modules.get("harness.pev.executor")
    )


class ShellStepMixin:
    """Mixin providing sanitized shell command execution with retry."""

    MAX_RETRIES_PER_STEP: int = 5
    console: Console
    _backoff: ExponentialBackoff

    def _execute_shell_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute shell command step with automatic retry on failure."""
        command = _extract_shell_command(step.description)
        if not command:
            self.console.print("[yellow]Skipping empty step[/yellow]")
            return ExecutionResult(
                exit_code=0,
                stdout="[SKIPPED] Empty command",
                stderr="",
                metadata={"mode": "shell", "skipped": True},
            )

        facade = _get_executor_facade()
        sanitizer_cls = getattr(facade, "CommandSanitizer", CommandSanitizer)
        sanitizer = sanitizer_cls()
        if not sanitizer.is_safe_command(command):
            res = sanitizer.sanitize(command)
            self.console.print(
                f"[red]BLOCKED:[/red] Unsafe command: {command}. "
                f"Reason: {res.blocked_reason}. "
                f"Patterns: {res.blocked_patterns}. "
                f"Warnings: {res.warnings}"
            )
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=(
                    f"Command blocked by sanitizer: {command}. "
                    f"Reason: {res.blocked_reason}"
                ),
                metadata={"mode": "shell", "blocked": True},
            )

        def _run_shell() -> ExecutionResult:
            subproc_mod = getattr(facade, "subprocess", subprocess)
            cmd_args = shlex.split(command) if isinstance(command, str) else command
            process = subproc_mod.run(cmd_args, shell=False, check=True, text=True, capture_output=True)
            if process.stdout:
                self.console.print(Panel(process.stdout.strip(), title="Output", border_style="green", expand=False))
            if process.stderr:
                self.console.print(Panel(process.stderr.strip(), title="Stderr", border_style="yellow", expand=False))
            return ExecutionResult(
                exit_code=process.returncode or 0, stdout=process.stdout or "",
                stderr=process.stderr or "", metadata={"mode": "shell", "command": command},
            )

        def _on_shell_retry(attempt: int, delay: float) -> None:
            self.console.print(f"[yellow]Retry {attempt} after {delay:.1f}s...[/yellow]")

        raw_attempts = (step.params.get("retry", 1) + 1) if step.params else 2
        max_attempts = min(raw_attempts, self.MAX_RETRIES_PER_STEP + 1)
        retry_fn = getattr(facade, "call_with_retry", call_with_retry)

        success, result_or_err, stats = retry_fn(
            _run_shell, max_attempts=max_attempts, backoff=self._backoff,
            retryable=(subprocess.CalledProcessError,), on_retry=_on_shell_retry,
        )

        if success:
            result = result_or_err
            result.metadata["attempt"] = stats.attempts
            result.metadata["delays"] = stats.delays
            return result

        e = result_or_err
        self.console.print(f"[bold red]Error executing step {step.order}[/bold red] (failed after {stats.attempts} attempts)")
        err_code = getattr(e, "returncode", 1)
        err_out = getattr(e, "stdout", "") or ""
        err_err = getattr(e, "stderr", "") or ""
        if err_out:
            self.console.print(Panel(err_out.strip(), title="Output (Partial)", border_style="yellow", expand=False))
        if err_err:
            self.console.print(Panel(err_err.strip(), title="Error Output", border_style="red", expand=False))
        return ExecutionResult(
            exit_code=err_code, stdout=err_out, stderr=err_err or str(e), error=e,
            metadata={"mode": "shell", "command": command, "attempt": stats.attempts, "delays": stats.delays},
        )
