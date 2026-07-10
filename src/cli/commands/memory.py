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
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

memory_app = typer.Typer(
 name="memory",
 help="Memory: execution history & learning (JSONL + YAML store)",
)

DEFAULT_JSONL_PATH = Path(".mekong/memory.jsonl")
DEFAULT_YAML_PATH = Path(".mekong/memory.yaml")


# ---------------------------------------------------------------------------
# JSONL backend (action/agent/outcome/tags schema)
# ---------------------------------------------------------------------------

def _jsonl_store() -> "src.core.memory_store.MemoryStore": # noqa: F821
 from src.core.memory_store import MemoryStore

 path = os.environ.get("MEKONG_MEMORY_PATH") or DEFAULT_JSONL_PATH
 return MemoryStore(path=path)


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
 table.add_column("Time", style="dim", width=19)
 table.add_column("Agent", style="cyan", width=12)
 table.add_column("Action", max_width=60)
 table.add_column("Outcome", justify="center")
 table.add_column("Tags", style="dim", max_width=30)

 for e in entries:
  style = "green" if e.outcome.lower() == "success" else (
   "red" if e.outcome.lower() == "failed" else "yellow"
  )
  table.add_row(
   e.timestamp[:19],
   (e.agent or "-")[:12],
   (e.action or "-")[:60],
   f"[{style}]{e.outcome}[/{style}]",
   ", ".join(e.tags or [])[:30],
  )

 console.print(table)


@memory_app.command(name="search")
def memory_search_cmd(
 query: str = typer.Argument(..., help="Search query (action/outcome/tags)"),
 limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
) -> None:
 """Search past entries by keyword."""
 entries = _jsonl_store().search(query=query, limit=limit)
 if not entries:
  console.print(f"[yellow]No results for '{query}'.[/yellow]")
  raise typer.Exit()

 table = Table(title=f"Matches ({len(entries)}) — '{query}'")
 table.add_column("Time", style="dim", width=19)
 table.add_column("Agent", style="cyan", width=12)
 table.add_column("Action", max_width=60)
 table.add_column("Outcome", justify="center")
 table.add_column("Tags", style="dim", max_width=30)

 for e in entries:
  style = "green" if e.outcome.lower() == "success" else (
   "red" if e.outcome.lower() == "failed" else "yellow"
  )
  table.add_row(
   e.timestamp[:19],
   (e.agent or "-")[:12],
   (e.action or "-")[:60],
   f"[{style}]{e.outcome}[/{style}]",
   ", ".join(e.tags or [])[:30],
  )
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

 removed = _jsonl_store().clear()
 console.print(f"[green]Cleared {removed} entries.[/green]")


# ---------------------------------------------------------------------------
# YAML backend (goal/status/reflection schema + vector semantic search)
# ---------------------------------------------------------------------------


def _yaml_store() -> "src.core.memory.MemoryStore": # noqa: F821
 from src.core.memory import MemoryStore

 path = os.environ.get("MEKONG_MEMORY_YAML_PATH") or str(DEFAULT_YAML_PATH)
 return MemoryStore(store_path=path)


@memory_app.command(name="store")
def memory_store_cmd(
 goal: str = typer.Argument(..., help="Goal / task description"),
 status: str = typer.Option("success", "--status", help="success|failed|partial"),
 reflection: str = typer.Option("", "--reflection", help="Post-task reflection"),
 recipe: str = typer.Option("", "--recipe", help="Recipe used"),
 duration_ms: float = typer.Option(0.0, "--duration-ms", help="Duration in ms"),
) -> None:
 """Record a goal outcome to the YAML memory store."""
 from src.core.memory import MemoryEntry

 entry = MemoryEntry(
  goal=goal,
  status=status,
  duration_ms=duration_ms,
  reflection=reflection,
  recipe_used=recipe,
  context={},
 )
 _yaml_store().record(entry)
 console.print(f"[green]Stored: {goal[:50]}... [{status}][/green]")


@memory_app.command(name="recall")
def memory_recall_cmd(
 query: str = typer.Argument(..., help="Natural-language query for semantic search"),
 top_k: int = typer.Option(5, "--top-k", "-k", help="Max results"),
) -> None:
 """Semantic search the YAML memory store by goal/reflection text."""
 try:
  results = _yaml_store().semantic_search(query, top_k=top_k)
 except Exception as exc:
  console.print(f"[red]Semantic search unavailable: {exc}[/red]")
  raise typer.Exit(1)

 if not results:
  console.print(f"[yellow]No memories similar to '{query}'.[/yellow]")
  raise typer.Exit()

 from src.core.memory import MemoryEntry
 table = Table(title=f"Recalled ({len(results)}) — '{query[:40]}'")
 table.add_column("Time", style="dim", width=10)
 table.add_column("Status", justify="center")
 table.add_column("Goal", max_width=60)
 table.add_column("Recipe", max_width=20)

 for e in results:
  if not isinstance(e, MemoryEntry):
   continue
  style = "green" if e.status == "success" else (
   "red" if e.status == "failed" else "yellow"
  )
  table.add_row(
   f"{e.timestamp:.1f}",
   f"[{style}]{e.status}[/{style}]",
   (e.goal or "-")[:60],
   (e.recipe_used or "-")[:20],
  )

 console.print(table)


@memory_app.command(name="history")
def memory_history_cmd(
 goal_pattern: str = typer.Argument("", help="Filter by goal substring (optional)"),
 limit: int = typer.Option(20, "--limit", "-l", help="Max entries"),
) -> None:
 """Show recent YAML goal entries."""
 entries = _yaml_store().recent(limit=limit)
 if goal_pattern:
  entries = [e for e in entries if goal_pattern.lower() in (e.goal or "").lower()]

 if not entries:
  console.print("[yellow]No YAML memory entries found.[/yellow]")
  raise typer.Exit()

 table = Table(title=f"YAML History ({len(entries)} entries)")
 table.add_column("Time", style="dim", width=10)
 table.add_column("Status", justify="center")
 table.add_column("Recipe", max_width=20)
 table.add_column("Goal", max_width=60)

 for e in entries:
  style = "green" if e.status == "success" else (
   "red" if e.status == "failed" else "yellow"
  )
  table.add_row(
   f"{e.timestamp:.1f}",
   f"[{style}]{e.status}[/{style}]",
   (e.recipe_used or "-")[:20],
   (e.goal or "-")[:60],
  )
 console.print(table)


@memory_app.command(name="stats")
def memory_stats_cmd() -> None:
 """Memory store statistics (JSONL + YAML)."""
 j_store = _jsonl_store()
 y_store = _yaml_store()

 j_recent = j_store.recent(limit=1000)
 j_success = sum(1 for e in j_recent if e.outcome.lower() == "success")
 j_failed = sum(1 for e in j_recent if e.outcome.lower() == "failed")

 y_stats = y_store.stats() if hasattr(y_store, "stats") else {}

 panel_text = (
 f"[bold]JSONL}}[/bold]  entries (recent 1k): {len(j_recent)}  "
 f"success: {j_success}  failed: {j_failed}\n"
 f"[bold]YAML  [/bold] total: {y_stats.get('total', '?')}  "
 f"success rate: {y_stats.get('success_rate', '?')}  "
 f"collections: {y_stats.get('collections', '?')}"
 )
 console.print(Panel(panel_text, title="Memory Stats", border_style="cyan"))


@memory_app.command(name="delete")
def memory_delete_cmd(
 goal: str = typer.Argument(..., help="Goal text to delete (exact match in YAML)"),
) -> None:
 """Delete a YAML memory entry by exact goal text match."""
 store = _yaml_store()
 entries = store.recent(limit=2000)
 matches = [e for e in entries if (e.goal or "") == goal]
 if not matches:
  console.print(f"[yellow]No entry found for goal: {goal!r}[/yellow]")
  raise typer.Exit()

 if not Confirm.ask(f"Delete {len(matches)} matching entries?", default=False):
  console.print("[yellow]Cancelled.[/yellow]")
  raise typer.Exit()

 # MemoryStore.recent() returns copies; actual deletion requires store
 # internals. Use the clear + re-save approach only if collection supports it.
 console.print(
 f"[yellow]Delete not yet implemented for YAML store (found {len(matches)} matches). "
 f"Remove entry manually from .mekong/memory.yaml.[/yellow]"
 )


__all__ = ["memory_app"]
