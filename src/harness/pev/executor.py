# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Recipe Executor

Executes recipes parsed from Markdown files.
Returns ExecutionResult for orchestrator integration.
"""

from __future__ import annotations

import shlex  # noqa: F401
import subprocess  # noqa: F401
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.core.circuit_breaker import get_circuit_breaker
from src.core.command_sanitizer import CommandSanitizer  # noqa: F401
from src.core.crash_detector import CrashPatternDetector
from src.core.retry import ExponentialBackoff, call_with_retry  # noqa: F401
from src.core.verifier import ExecutionResult
from src.harness.pev.checkpoint import (
    CheckpointStore,
    PipelineCheckpoint,
    _utc_now,
)

from .executor_agent_steps import AgentStepsMixin
from .executor_remote_steps import RemoteStepsMixin
from .executor_shell_step import ShellStepMixin, _extract_shell_command  # noqa: F401
from .parser import Recipe, RecipeStep


class RecipeExecutor(RemoteStepsMixin, AgentStepsMixin, ShellStepMixin):
    """Executes a Recipe step by step, returning structured results."""

    MAX_RETRIES_PER_STEP = 5
    MAX_TOTAL_ITERATIONS = 20

    def __init__(
        self,
        recipe: Recipe,
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        """Initialize RecipeExecutor with a parsed recipe."""
        self.recipe = recipe
        self.console = Console()
        self._total_iterations: int = 0
        self._checkpoint_store = checkpoint_store
        self._backoff: ExponentialBackoff = ExponentialBackoff(
            initial=1.0, max_delay=30.0, factor=2.0,
        )
        self._llm_breaker = get_circuit_breaker(
            "pev-llm", failure_threshold=3, recovery_timeout=30.0,
        )
        self._api_breaker = get_circuit_breaker(
            "pev-api", failure_threshold=3, recovery_timeout=30.0,
        )
        self._browse_breaker = get_circuit_breaker(
            "pev-browse", failure_threshold=3, recovery_timeout=30.0,
        )
        self._crash_detector: CrashPatternDetector | None = CrashPatternDetector()

    def execute_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute a single step (shell, llm, api, tool, or browse)."""
        self._total_iterations += 1
        if self._total_iterations > self.MAX_TOTAL_ITERATIONS:
            msg = (
                f"Global iteration cap reached ({self.MAX_TOTAL_ITERATIONS}). "
                "Pipeline aborted to prevent runaway execution."
            )
            self.console.print(f"[bold red]ITERATION CAP:[/bold red] {msg}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=msg,
                metadata={
                    "iteration_cap_hit": True,
                    "total_iterations": self._total_iterations,
                },
            )

        self.console.print(f"\n[bold blue]Step {step.order}:[/bold blue] {step.title}")
        step_type = step.params.get("type", "shell") if step.params else "shell"

        if step_type == "llm":
            result = self._execute_llm_step(step)
        elif step_type == "api":
            result = self._execute_api_step(step)
        elif step_type == "tool":
            result = self._execute_tool_step(step)
        elif step_type == "browse":
            result = self._execute_browse_step(step)
        else:
            result = self._execute_shell_step(step)

        if self._crash_detector is not None:
            signals = self._crash_detector.inspect_step(result)
            if signals:
                result.metadata["crash_signals"] = signals
                self.console.print(
                    "[bold red][crash-detected][/bold red] Signals: "
                    + ", ".join(f"{s['category']}:{s['signal']}" for s in signals)
                )

        if result.exit_code == 0 and self._checkpoint_store is not None:
            pipeline_id = self.recipe.name
            existing = self._checkpoint_store.load(pipeline_id)
            completed = list(existing.completed_steps) if existing else []
            if step.order not in completed:
                completed.append(step.order)
            checkpoint = PipelineCheckpoint(
                pipeline_id=pipeline_id,
                completed_steps=completed,
                last_step_order=step.order,
                status="running",
                created_at=existing.created_at if existing else _utc_now(),
                updated_at=_utc_now(),
            )
            self._checkpoint_store.save(checkpoint)

        return result

    def run(self) -> bool:
        """Run the full recipe (legacy mode, returns bool)."""
        self.console.print(
            Panel(
                Text(self.recipe.title or self.recipe.name, style="italic"),
                title=f"Running: {self.recipe.name}",
                border_style="cyan",
            )
        )

        for step in self.recipe.steps:
            result = self.execute_step(step)
            if result.exit_code != 0:
                self.console.print("\n[bold red]Recipe execution failed.[/bold red]")
                return False

        self.console.print(
            f"\n[bold green]Recipe '{self.recipe.name}' completed successfully![/bold green]"
        )
        return True


__all__ = ["RecipeExecutor"]
