from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from cli.theme import get_theme, TOKENS


class BlockStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class BlockLine:
    text: str
    status: BlockStatus = BlockStatus.RUNNING


@dataclass
class CommandBlock:
    command: str
    args: str = ""
    lines: list[BlockLine] = field(default_factory=list)
    status: BlockStatus = BlockStatus.RUNNING
    started_at: datetime = field(default_factory=datetime.now)

    @property
    def title(self) -> str:
        ts = self.started_at.strftime("%H:%M")
        icon = {"running": "⏳", "success": "✓", "warning": "⚠", "error": "✗"}.get(
            self.status.value, "·"
        )
        cmd_display = f"{self.command} -- {self.args}" if self.args else self.command
        return f"{icon} [bold]{cmd_display}[/bold]  {ts}"

    @property
    def duration(self) -> str:
        delta = datetime.now() - self.started_at
        secs = delta.total_seconds()
        return f"{secs:.1f}s"


class BlockRenderer:
    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console(theme=get_theme())
        self.current_block: Optional[CommandBlock] = None

    def start(self, command: str, args: str = "") -> None:
        self.current_block = CommandBlock(command=command, args=args)
        self._render()

    def add_line(self, text: str, status: BlockStatus = BlockStatus.RUNNING) -> None:
        if self.current_block:
            self.current_block.lines.append(BlockLine(text=text, status=status))

    def set_status(self, status: BlockStatus) -> None:
        if self.current_block:
            self.current_block.status = status
            self._render()

    def _render(self) -> None:
        if not self.current_block:
            return
        lines = []
        for line in self.current_block.lines:
            color = {"running": "yellow", "success": "green", "warning": "orange3", "error": "red"}.get(
                line.status.value, "white"
            )
            lines.append(f"[{color}]{line.text}[/{color}]")
        body = "\n".join(lines) if lines else "[dim]Waiting...[/dim]"
        panel = Panel(body, title=self.current_block.title, border_style="panel.border")
        self.console.clear()
        self.console.print(panel)

    def finish(self) -> None:
        self.set_status(BlockStatus.SUCCESS)


def run_with_blocks(command: str, args: str = "") -> None:
    renderer = BlockRenderer()
    renderer.start(command, args)
    try:
        renderer.add_line(f"Executing: {command} {args}".strip())
        renderer.finish()
    except KeyboardInterrupt:
        renderer.set_status(BlockStatus.ERROR)
        renderer.add_line("[yellow]Interrupted by user[/yellow]")
