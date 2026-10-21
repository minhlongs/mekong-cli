# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""StreamingSession context manager for TUI streaming renderer."""

from __future__ import annotations

import threading
from typing import Any, Optional

from rich.console import Console

from src.cli.tui.streaming.models import StepProgress
from src.cli.tui.streaming.renderer import StreamingRenderer
from src.core.event_bus import StreamingEventBus


class StreamingSession:
    """Convenience context manager for streaming renderer.

    Usage::

        bus = get_streaming_bus()
        with StreamingSession(bus, total_steps=5) as session:
            for step in steps:
                session.register_step(step.order, step.title)
                session.start_step(step.order)
                # execute step -- events flow through bus
    """

    def __init__(
        self,
        bus: Optional[StreamingEventBus] = None,
        total_steps: int = 0,
        console: Optional[Console] = None,
    ) -> None:
        self.renderer = StreamingRenderer(bus=bus, console=console)
        self.renderer.set_total_steps(total_steps)
        self._total = total_steps
        self._steps: dict[int, StepProgress] = {}

    def __enter__(self) -> "StreamingSession":
        self._thread = threading.Thread(target=self.renderer.start, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.renderer.stop()
        if hasattr(self, "_thread"):
            self._thread.join(timeout=2.0)

    def register_step(self, order: int, title: str) -> None:
        self.renderer.register_step(order, title)

    def start_step(self, order: int) -> None:
        sp = self._steps.get(order) or StepProgress(
            order=order, title=f"Step {order}", status="pending"
        )
        self._steps[order] = sp
        self.renderer._handle_step_started(order, sp.title)

    def add_output(self, text: str, source: str = "agent") -> None:
        self.renderer.add_output(text, source=source)

    def set_total_steps(self, n: int) -> None:
        self._total = n
        self.renderer.set_total_steps(n)
