"""Memory CLI commands: search, list, clear.

Wires the JSONL MemoryStore (src/core/memory_store.py) into the Mekong CLI.
Invoked as sub-app of `mekong memory`.
"""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

memory_app = typer.Typer(
    name="memory",
    help="Memory: execution history & learning (JSONL store)",
)

DEFAULT_MEMORY_PATH = Path(".mekong/memory.jsonl")


def _store() -> "src.core.memory_store.MemoryStore":  # noqa: F821 — lazy import to avoid cycles
    from src.core.memory_store import MemoryStore, DEFAULT_MEMORY_PATH

    path = os.environ.get("MEKONG_MEMORY_PATH") or DEFAULT_MEMORY_PATH
    return MemoryStore(path=path)


@memory_app.command(name="list")
def memory_list(
    limit: int = typer.Option(20, "--limit", "-l", help="Max entries to show"),
) -> None:
    """Show recent memory entries."""
    entries = _store().recent(limit=limit)
    if not entries:
        console.print("[yellow]No memory entries yet.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Memory ({len(entries)} entries)")
    table.add_column("Time", style="dim", width=20)
    table.add_column("Agent", style="cyan", width=12)
    table.add_column("Action", style="cyan", max_width=50)
    table.add_column("Outcome", justify="center")
    table.add_column("Tags", style="dim")

    for e in entries:
        style = "green" if e.outcome.lower() == "success" else (
            "red" if e.outcome.lower() == "failed" else "yellow"
        )
        table.add_row(
            e.timestamp[:19],
            e.agent[:12],
            e.action[:50],
            f"[{style}]{e.outcome}[/{style}]",
            ", ".join(e.tags)[:30],
        )

    console.print(table)


@memory_app.command(name="search")
def memory_search_cmd(
    query: str = typer.Argument(..., help="Search query (matches action/outcome/tags)"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
) -> None:
    """Search past memory entries by keyword."""
    entries = _store().search(query=query, limit=limit)
    if not entries:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Matches ({len(entries)}) — '{query}'")
    table.add_column("Time", style="dim", width=20)
    table.add_column("Agent", style="cyan", width=12)
    table.add_column("Action", max_width=50)
    table.add_column("Outcome", justify="center")
    table.add_column("Tags", style="dim")

    for e in entries:
        style = "green" if e.outcome.lower() == "success" else (
            "red" if e.outcome.lower() == "failed" else "yellow"
        )
        table.add_row(
            e.timestamp[:19],
            e.agent[:12],
            e.action[:50],
            f"[{style}]{e.outcome}[/{style}]",
            ", ".join(e.tags)[:30],
        )

    console.print(table)


@memory_app.command(name="clear")
def memory_clear_cmd(
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Clear all memory entries (requires confirmation unless --force)."""
    if not force:
        console.print(
            "[red]This deletes the entire .mekong/memory.jsonl file.[/red]"
        )
        confirm = typer.confirm("Proceed?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    removed = _store().clear()
    console.print(f"[green]Memory cleared. {removed} entries removed.[/green]")


__all__ = [
    "memory_app",
]
