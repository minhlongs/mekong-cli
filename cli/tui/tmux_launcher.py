
from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class TmuxLayout:
    """3-pane Warp-style tmux layout."""
    session: str = "mekong"
    palette_width: int = 80
    output_height: int = 15


class TmuxLauncher:
    """Launch and manage a tmux session with Warp-style 3-pane layout.

    Layout:
        ┌──────────────────┬────────────────────┐
        │  palette (input) │   block history    │
        │                  ├────────────────────┤
        │                  │   raw output       │
        └──────────────────┴────────────────────┘
    """

    def __init__(self, layout: Optional[TmuxLayout] = None) -> None:
        self.layout = layout or TmuxLayout()

    def is_available(self) -> bool:
        """Check if tmux is installed."""
        return shutil.which("tmux") is not None

    def launch(self, initial_cmd: str = "") -> None:
        """Create tmux session with 3-pane layout."""
        if not self.is_available():
            print("[red]tmux not found[/red] — install with: brew install tmux")
            print("[dim]Falling back to single-pane mode.[/dim]")
            self._fallback(initial_cmd)
            return

        L = self.layout
        subprocess.run(["tmux", "new-session", "-d", "-s", L.session, "-x", "160", "-y", "40"])

        # Split: left (palette, 80 cols) | right (split top/bottom)
        subprocess.run(["tmux", "split-window", "-h", "-t", f"{L.session}:0", "-l", str(L.palette_width)])
        subprocess.run(["tmux", "split-window", "-v", "-t", f"{L.session}:0.1", "-l", str(L.output_height)])

        # Send initial command to right-bottom pane (raw output)
        subprocess.run(["tmux", "send-keys", "-t", f"{L.session}:0.2", initial_cmd, "Enter"])

        # Send palette prompt to left pane
        subprocess.run(["tmux", "send-keys", "-t", f"{L.session}:0.0",
                        "mekong palette", "Enter"])

        print(f"[green]✓[/green] tmux session [bold]{L.session}[/bold] launched")
        print("[dim]Attach with: tmux attach -t " + L.session + "[/dim]")

        subprocess.run(["tmux", "attach-session", "-t", L.session])

    def _fallback(self, initial_cmd: str = "") -> None:
        """Single-pane fallback when tmux is unavailable."""
        cmd = ["python3", "-m", "src.main", "palette"]
        if initial_cmd:
            cmd = ["python3", "-m", "src.main", initial_cmd]
        subprocess.run(cmd)
