# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia video script input parsing — inline text or file path resolution."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

console = Console()


def resolve_script_content(script_or_path: str) -> str:
    """Resolve a script argument given as inline text or as a path to a text file."""
    trimmed = script_or_path.strip()
    if trimmed.startswith("-"):
        console.print(f"[red]❌ Invalid script argument or option flag: {trimmed}[/red]")
        raise typer.Exit(code=1)

    potential_path = Path(trimmed)
    if len(trimmed) < 256 and potential_path.is_file():
        try:
            return potential_path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]❌ Failed to read script file '{trimmed}': {e}[/red]")
            raise typer.Exit(code=1)
    return script_or_path
