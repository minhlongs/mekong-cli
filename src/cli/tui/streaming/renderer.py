# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""StreamingRenderer implementation for real-time TUI output."""

from __future__ import annotations

import dataclasses
import time
from typing import Any, Callable, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from src.cli.tui.streaming.models import (
    _MAX_OUTPUT_LINES, _STATUS_COLORS, OutputLine, ProgressPanel, RendererState, StepProgress,
)
from src.cli.tui.theme import get_theme
from src.core.event_bus import EventType, StreamingEventBus, get_streaming_bus


class StreamingRenderer:
    """Real-time streaming renderer using Rich Live display."""

    def __init__(
        self, bus: Optional[StreamingEventBus] = None,
        max_lines: int = _MAX_OUTPUT_LINES, console: Optional[Console] = None,
    ) -> None:
        self.bus = bus or get_streaming_bus()
        self.max_lines = max_lines
        self.console = console or Console(theme=get_theme())
        self._output_lines: list[OutputLine] = []
        self._steps: dict[int, StepProgress] = {}
        self._total_steps: int = 0
        self._state = RendererState.IDLE
        self._live: Optional[Live] = None
        self._progress_panel: Optional[ProgressPanel] = None
        self._cancel_callback: Optional[Callable[[], None]] = None
        self._cancelled: bool = False
        self._start_time: float = 0.0
        self._subscribed_types: list[Any] = []

    def set_total_steps(self, total: int) -> None:
        self._total_steps = total

    def register_step(self, order: int, title: str) -> None:
        self._steps[order] = StepProgress(order=order, title=title, status="pending")

    def cancel(self) -> None:
        self._handle_cancel()

    def on_cancel(self, callback: Callable[[], None]) -> None:
        self._cancel_callback = callback

    def stop(self) -> None:
        self._state = RendererState.STOPPED

    def add_output(self, text: str, source: str = "agent") -> None:
        self._output_lines.append(OutputLine(text=text, timestamp=time.monotonic(), source=source, status="running"))
        self._evict_lines()

    def mark_output(self, index: int, status: str) -> None:
        if 0 <= index < len(self._output_lines):
            self._output_lines[index] = dataclasses.replace(self._output_lines[index], status=status)

    def start(self) -> None:
        if self._state == RendererState.RUNNING:
            return
        self._state, self._cancelled, self._start_time = RendererState.RUNNING, False, time.monotonic()
        self._progress_panel = ProgressPanel(total_steps=self._total_steps, console=self.console)
        for order in sorted(self._steps):
            self._progress_panel.add_step(order, self._steps[order].title)

        self._subscribed_types = [
            EventType.STEP_STARTED, EventType.STEP_COMPLETED, EventType.STEP_FAILED,
            EventType.STEP_HEALED, EventType.GOAL_STARTED, EventType.GOAL_COMPLETED, EventType.HALT_TRIGGERED,
        ]
        for event_type in self._subscribed_types:
            self.bus.subscribe(event_type, self._on_event)

        try:
            with Live(self._render(), console=self.console, refresh_per_second=10, screen=True) as live:
                self._live = live
                while self._state == RendererState.RUNNING:
                    time.sleep(0.05)
        except KeyboardInterrupt:
            self._handle_cancel()
        finally:
            self._cleanup()
            self.console.show_cursor()

    def _on_event(self, event: Any) -> None:
        etype, data = event.type, event.data or {}
        order = int(data.get("step_order", data.get("step", 0))) if etype in (EventType.STEP_STARTED, EventType.STEP_COMPLETED, EventType.STEP_FAILED) else 0
        if etype == EventType.STEP_STARTED:
            self._handle_step_started(order, data.get("title", f"Step {order}"))
        elif etype in (EventType.STEP_COMPLETED, EventType.STEP_FAILED):
            self._handle_step_completed(order, success=(etype == EventType.STEP_COMPLETED))
        elif etype == EventType.STEP_HEALED:
            self._handle_step_healed(data)
        elif etype == EventType.GOAL_COMPLETED:
            self._handle_goal_completed(data)
        elif etype == EventType.HALT_TRIGGERED:
            self._handle_halt(data)

        for line in data.get("stdout", data.get("output", "")).splitlines():
            if line.strip():
                self.add_output(line, source="agent")

    def _handle_step_started(self, order: int, title: str) -> None:
        self._steps.setdefault(order, StepProgress(order=order, title=title, status="pending"))
        self._steps[order] = dataclasses.replace(self._steps[order], status="running", timestamp=time.monotonic())
        if self._progress_panel:
            self._progress_panel.add_step(order, title)
            self._progress_panel.start_step(order)
        self.add_output(f"[bold cyan]▶ Step {order}:[/bold cyan] {title}", source="renderer")

    def _handle_step_completed(self, order: int, success: bool) -> None:
        if order in self._steps:
            step, now = self._steps[order], time.monotonic()
            self._steps[order] = dataclasses.replace(
                step, status="success" if success else "error",
                duration=(now - step.timestamp) if step.timestamp else 0.0, timestamp=now,
            )
        if self._progress_panel:
            self._progress_panel.complete_step(order, success=success)
        icon, style = ("✓", "green") if success else ("✗", "red")
        self.add_output(f"[{style}]{icon} Step {order} {'done' if success else 'failed'}[/{style}]", source="renderer")

    def _handle_step_healed(self, data: dict[str, Any]) -> None:
        self.add_output(f"[yellow]\U0001f527 Step {data.get('step_order', data.get('step', '?'))} self-healed[/yellow]", source="renderer")

    def _handle_goal_completed(self, data: dict[str, Any]) -> None:
        self._state = RendererState.STOPPED

    def _handle_halt(self, data: dict[str, Any]) -> None:
        self.add_output(f"[bold red]⛔ HALT: {data.get('reason', 'unknown')}[/bold red]", source="renderer")
        self._state = RendererState.STOPPED

    def _handle_cancel(self) -> None:
        self._cancelled = True
        self._state = RendererState.CANCELLING
        self.add_output("[bold yellow]⚠ Cancellation requested — shutting down...[/bold yellow]", source="renderer")
        if self._cancel_callback:
            try:
                self._cancel_callback()
            except Exception:
                pass
        self.bus.emit(EventType.HALT_TRIGGERED, {"reason": "user_cancelled"})
        self._state = RendererState.STOPPED

    def _render(self) -> Layout:
        layout = Layout()
        progress = self._progress_panel.render() if self._progress_panel else Panel("[dim]Initializing...[/dim]", title="Progress", border_style="blue")
        layout.split_column(Layout(progress, name="progress", size=8), Layout(self._build_output_panel(), name="output"))
        return layout

    def _build_output_panel(self) -> Panel:
        lines = self._output_lines[-self.max_lines :]
        body = (
            Text("[dim]Waiting for agent output...[/dim]")
            if not lines
            else Text("\n").join([Text.from_markup(ln.text, style=_STATUS_COLORS.get(ln.status, "white")) for ln in lines])
        )
        return Panel(body, title="[bold]Agent Output[/bold]", border_style="gray", padding=(0, 1))

    def _evict_lines(self) -> None:
        while len(self._output_lines) > self.max_lines:
            self._output_lines.pop(0)

    def _cleanup(self) -> None:
        for event_type in self._subscribed_types:
            try:
                self.bus.unsubscribe(event_type, self._on_event)
            except Exception:
                pass
        self._live = None
