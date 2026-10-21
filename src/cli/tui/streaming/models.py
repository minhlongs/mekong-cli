# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and ProgressPanel for TUI streaming renderer."""

from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

from src.cli.tui.theme import get_theme


class RendererState(str, Enum):
    """Lifecycle states for the streaming renderer."""

    IDLE = "idle"
    RUNNING = "running"
    CANCELLING = "cancelling"
    STOPPED = "stopped"


@dataclass(frozen=True)
class OutputLine:
    """A single line of streamed agent output."""

    text: str
    timestamp: float
    source: str = "agent"
    status: str = "running"  # running | success | warning | error


@dataclass(frozen=True)
class StepProgress:
    """Progress data for a single pipeline step."""

    order: int
    title: str
    status: str  # pending | running | success | error | skipped
    duration: float = 0.0
    timestamp: float = 0.0


_STATUS_COLORS = {
    "running": "yellow",
    "success": "green",
    "warning": "orange3",
    "error": "red",
    "skipped": "dim",
    "pending": "dim",
}

_STEP_ICONS = {
    "pending": "○",
    "running": "◉",
    "success": "✓",
    "error": "✗",
    "skipped": "−",
}

_MAX_OUTPUT_LINES = 500


class ProgressPanel:
    """Progress panel showing overview of pipeline execution.

    Renders a Rich Progress bar plus per-step status list inside a Panel.
    Designed to be embedded as the top section of a Live layout.
    """

    def __init__(self, total_steps: int, console: Optional[Console] = None) -> None:
        self.total_steps = total_steps
        self.console = console or Console(theme=get_theme())
        self._progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[bold green]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self._task_id: Optional[TaskID] = None
        self._steps: dict[int, StepProgress] = {}
        self._completed_count: int = 0

    def _ensure_task(self) -> TaskID:
        if self._task_id is None:
            self._task_id = self._progress.add_task(
                "Pipeline", total=self.total_steps, completed=0
            )
        return self._task_id

    def add_step(self, order: int, title: str) -> None:
        """Register a new step in the progress tracker."""
        self._steps[order] = StepProgress(order=order, title=title, status="pending")

    def start_step(self, order: int) -> None:
        """Mark a step as running."""
        if order in self._steps:
            self._steps[order] = dataclasses.replace(
                self._steps[order], status="running", timestamp=time.monotonic()
            )
            self._ensure_task()

    def complete_step(self, order: int, success: bool = True) -> None:
        """Mark a step as completed (success or error)."""
        if order not in self._steps:
            return
        step = self._steps[order]
        now = time.monotonic()
        duration = (now - step.timestamp) if step.timestamp else 0.0
        status = "success" if success else "error"
        if success:
            self._completed_count += 1
        self._steps[order] = dataclasses.replace(
            step, status=status, duration=duration, timestamp=now
        )
        task_id = self._ensure_task()
        delta = 1 if success else 0
        self._progress.update(task_id, advance=delta)

    def cancel_step(self, order: int) -> None:
        """Mark a step as skipped due to cancellation."""
        if order in self._steps:
            self._steps[order] = dataclasses.replace(
                self._steps[order], status="skipped", duration=0.0
            )

    def render(self) -> Panel:
        """Render the full progress panel."""
        step_lines: list[str] = []
        for order in sorted(self._steps):
            step = self._steps[order]
            icon = _STEP_ICONS.get(step.status, "?")
            color = _STATUS_COLORS.get(step.status, "white")
            dur = f" ({step.duration:.1f}s)" if step.duration > 0 else ""
            step_lines.append(
                f"[{color}]{icon}[/{color}] [{color}]Step {order}:[/{color}] "
                f"{step.title}{dur}"
            )
        if not step_lines:
            step_lines.append("[dim]No steps registered yet[/dim]")

        step_text = Text("\n".join(step_lines))
        combined = Group(self._progress, Text(""), step_text)

        return Panel(
            combined,
            title="[bold]Pipeline Progress[/bold]",
            border_style="blue",
            padding=(0, 1),
        )
