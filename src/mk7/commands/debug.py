"""Mekong CLI 7 — debug command: analyze issue -> fix plan."""

from __future__ import annotations

import json
import re

import typer
from rich.console import Console

from ..core.llm import LLMClient
from ..core.models import resolve

console = Console()


def debug_cmd(
    issue: str = typer.Argument(..., help="Bug/issue description"),
    execute: bool = typer.Option(False, "--execute", help="Plan only (default) or execute"),
) -> None:
    """Debug an issue — generates a fix plan (defaults to dry-run)."""
    client = LLMClient()
    entry = resolve("sonnet")

    console.print(f"[bold]Debugging:[/] {issue}")
    prompt = (
        f"Bug: {issue}\n\n"
        "Reply with ONLY a JSON object (no prose, no code fence): "
        '{"root_cause": "short", "files": ["a.py"], "fix_steps": ["1.", "2."], "verify": ["cmd1"]}'
    )
    raw = client.text(entry.id, prompt, max_tokens=4096)
    data = None
    try:
        data = json_loads(raw)
    except Exception:
        pass
    if not data:
        # Fallback: model replied in prose — show it directly.
        console.print(raw[:1200])
        if not execute:
            console.print("\n[dim]Dry-run — use --execute to apply.[/]")
        raise typer.Exit(0)
    console.print(f"\n[bold red]Root cause:[/] {data.get('root_cause', '?')}")
    console.print("\n[bold]Files:[/]")
    for f in data.get("files", []):
        console.print(f"  - {f}")
    console.print("\n[bold]Fix steps:[/]")
    for i, s in enumerate(data.get("fix_steps", []), 1):
        console.print(f"  {i}. {s}")
    console.print("\n[bold]Verify:[/]")
    for v in data.get("verify", []):
        console.print(f"  - {v}")
    if execute:
        console.print("[yellow]--execute: fix execution not yet implemented in v7 MVP.[/]")

    if not execute:
        console.print("\n[dim]Dry-run — use --execute to apply.[/]")


def json_loads(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return json.loads(cleaned)
