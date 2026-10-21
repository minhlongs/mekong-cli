# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Memory CLI commands: list, search, clear, store, recall, history, stats.

Wires both the JSONL MemoryStore (src/core/memory_store.py) and the
YAML-backed MemoryStore (src/core/memory.py) into the Mekong CLI.
Invoked as sub-app of `mekong memory`.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from src.cli.commands.memory_learn_commands import (
    _learn_app,
    learn_clear_cmd,
    learn_patterns_cmd,
    learn_record_cmd,
    learn_similar_cmd,
    learn_stats_cmd,
    learn_threshold_cmd,
)
from src.cli.commands.memory_yaml_commands import (
    DEFAULT_YAML_PATH,
    _yaml_store,
    memory_delete_cmd,
    memory_history_cmd,
    memory_recall_cmd,
    memory_store_cmd,
    render_memory_stats,
)

console = Console()

memory_app = typer.Typer(
    name="memory",
    help="Memory: execution history & learning (JSONL + YAML store)",
)

DEFAULT_JSONL_PATH = Path(".mekong/memory.jsonl")


def _jsonl_store() -> "src.core.memory_store.MemoryStore":  # noqa: F821
    from src.core.memory_store import MemoryStore

    path = os.environ.get("MEKONG_MEMORY_PATH") or DEFAULT_JSONL_PATH
    return MemoryStore(path=path)


def _jsonl_adapter() -> "src.core.adapters.jsonl_memory_adapter.JsonlMemoryAdapter":  # noqa: F821
    from src.core.adapters.jsonl_memory_adapter import JsonlMemoryAdapter

    path = os.environ.get("MEKONG_MEMORY_PATH") or DEFAULT_JSONL_PATH
    return JsonlMemoryAdapter(path=path)


@memory_app.command(name="list")
def memory_list(
    limit: int = typer.Option(20, "--limit", "-l", help="Max entries"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Filter by agent"),
) -> None:
    """Show recent JSONL memory entries."""
    entries = _jsonl_store().recent(limit=limit)
    if agent:
        entries = [e for e in entries if e.agent == agent]
    if not entries:
        console.print("[yellow]No memory entries yet.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Memory ({len(entries)} entries)")
    for col, kw in [("Time", {"style": "dim", "width": 19}), ("Agent", {"style": "cyan", "width": 12}), ("Action", {"max_width": 60}), ("Outcome", {"justify": "center"}), ("Tags", {"style": "dim", "max_width": 30})]:
        table.add_column(col, **kw)
    for e in entries:
        style = "green" if e.outcome.lower() == "success" else ("red" if e.outcome.lower() == "failed" else "yellow")
        table.add_row(e.timestamp[:19], (e.agent or "-")[:12], (e.action or "-")[:60], f"[{style}]{e.outcome}[/{style}]", ", ".join(e.tags or [])[:30])
    console.print(table)


@memory_app.command(name="search")
def memory_search_cmd(
    query: str = typer.Argument(..., help="Search query (action/outcome/tags)"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
) -> None:
    """Search past entries by keyword (via the conformant JSONL adapter)."""
    hits = _jsonl_adapter().search(query=query, limit=limit)
    if not hits:
        console.print(f"[yellow]No results for '{query}'.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Matches ({len(hits)}) — '{query}'")
    for col, kw in [("Time", {"style": "dim", "width": 19}), ("Agent", {"style": "cyan", "width": 12}), ("Action", {"max_width": 60}), ("Outcome", {"justify": "center"}), ("Tags", {"style": "dim", "max_width": 30})]:
        table.add_column(col, **kw)
    for h in hits:
        meta = h.metadata if isinstance(h.metadata, dict) else {}
        outcome = h.data.decode("utf-8", errors="replace") if h.data else "-"
        style = "green" if outcome.lower() == "success" else ("red" if outcome.lower() == "failed" else "yellow")
        table.add_row(str(meta.get("timestamp") or "-")[:19], str(meta.get("agent") or "-")[:12], (h.key or "-")[:60], f"[{style}]{outcome}[/{style}]", ", ".join(meta.get("tags") or [])[:30])
    console.print(table)


@memory_app.command(name="clear")
def memory_clear_cmd(
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """Clear all JSONL memory entries (wipe .mekong/memory.jsonl)."""
    if not force:
        console.print("[red]This deletes the entire .mekong/memory.jsonl file.[/red]")
        if not Confirm.ask("Proceed?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()
    console.print(f"[green]Cleared {_jsonl_store().clear()} entries.[/green]")


@memory_app.command(name="stats")
def memory_stats_cmd() -> None:
    """Memory store statistics (JSONL + YAML)."""
    render_memory_stats(_jsonl_store)


memory_app.command(name="store")(memory_store_cmd)
memory_app.command(name="recall")(memory_recall_cmd)
memory_app.command(name="history")(memory_history_cmd)
memory_app.command(name="delete")(memory_delete_cmd)
memory_app.add_typer(_learn_app)

__all__ = [
    "DEFAULT_JSONL_PATH", "DEFAULT_YAML_PATH", "_jsonl_adapter", "_jsonl_store", "_learn_app",
    "_yaml_store", "learn_clear_cmd", "learn_patterns_cmd", "learn_record_cmd",
    "learn_similar_cmd", "learn_stats_cmd", "learn_threshold_cmd", "memory_app",
    "memory_clear_cmd", "memory_delete_cmd", "memory_history_cmd", "memory_list",
    "memory_recall_cmd", "memory_search_cmd", "memory_stats_cmd", "memory_store_cmd",
]
