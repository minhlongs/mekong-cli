"""
Rollback handler — reverses completed steps on failure.
Provides both RollbackHandler class and _handle_failure helper used by runner.
"""

import shlex
import subprocess
from typing import List

from rich.console import Console

from .models import OrchestrationStatus, OrchestrationResult
from ..parser import RecipeStep


class RollbackHandler:
    """Handles rollback of completed steps on failure."""

    def __init__(self, enable_rollback: bool = True) -> None:
        self.enable_rollback = enable_rollback
        try:
            from ..command_sanitizer import CommandSanitizer
            self._sanitizer = CommandSanitizer(strict_mode=True)
        except Exception:
            self._sanitizer = None

    def rollback(
        self,
        result: OrchestrationResult,
        failed_step: RecipeStep,
    ) -> None:
        """Roll back all completed steps in reverse order."""
        if not self.enable_rollback:
            return

        rollback_errors: List[str] = []

        for step_result in reversed(result.step_results):
            if not step_result.verification.passed:
                continue  # Only roll back passed steps

            step = step_result.step
            rollback_cmd = step.params.get("rollback") if step.params else None
            if not rollback_cmd:
                continue

            # Security check — block dangerous commands
            if self._sanitizer is not None:
                san = self._sanitizer.sanitize(rollback_cmd)
                if not san.is_safe:
                    msg = f"Step {step.order} rollback blocked (security): {san.blocked_reason}"
                    rollback_errors.append(msg)
                    continue

            try:
                cmd_args = rollback_cmd.split()
                proc = subprocess.run(
                    cmd_args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if proc.returncode != 0:
                    msg = f"Step {step.order} rollback failed: {proc.stderr.strip()}"
                    rollback_errors.append(msg)
            except subprocess.TimeoutExpired:
                rollback_errors.append(f"Step {step.order} rollback timed out")
            except Exception as exc:
                rollback_errors.append(f"Step {step.order} rollback error: {exc}")

        if rollback_errors:
            result.errors.extend(rollback_errors)
            result.warnings.append("Rollback completed with errors")

        result.status = OrchestrationStatus.ROLLED_BACK


def handle_failure(
    result: OrchestrationResult,
    failed_step: RecipeStep,
    enable_rollback: bool,
    console: Console,
) -> None:
    """
    Handle step failure with console output and rollback.

    Used internally by runner. Reverses completed steps in reverse order
    by executing their rollback commands (if defined in step params).
    """
    console.print(
        f"\n[bold red]❌ Step {failed_step.order} failed verification[/bold red]"
    )

    if not enable_rollback:
        return

    console.print("[yellow]🔄 Rolling back completed steps...[/yellow]")

    rollback_errors = []
    for step_result in reversed(result.step_results):
        if not step_result.verification.passed:
            continue

        step = step_result.step
        rollback_cmd = step.params.get("rollback") if step.params else None

        if not rollback_cmd:
            console.print(
                f"  [dim]Step {step.order}: no rollback command — skipping[/dim]"
            )
            continue

        console.print(f"  [yellow]↩ Rolling back step {step.order}...[/yellow]")

        try:
            rollback_args = (
                shlex.split(rollback_cmd)
                if isinstance(rollback_cmd, str)
                else rollback_cmd
            )
            proc = subprocess.run(
                rollback_args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode == 0:
                console.print(f"  [green]✓ Step {step.order} rolled back[/green]")
            else:
                msg = f"Step {step.order} rollback failed: {proc.stderr.strip()}"
                rollback_errors.append(msg)
                console.print(f"  [red]✗ {msg}[/red]")
        except subprocess.TimeoutExpired:
            msg = f"Step {step.order} rollback timed out"
            rollback_errors.append(msg)
            console.print(f"  [red]✗ {msg}[/red]")
        except Exception as e:
            msg = f"Step {step.order} rollback error: {e}"
            rollback_errors.append(msg)
            console.print(f"  [red]✗ {msg}[/red]")

    if rollback_errors:
        result.errors.extend(rollback_errors)
        result.warnings.append("Rollback completed with errors")

    result.status = OrchestrationStatus.ROLLED_BACK


__all__ = [
    "RollbackHandler",
    "handle_failure",
]
