"""Command palette -- fuzzy keyword -> mekong subcommand.

Imports routing table from cli.tui.router (single source of truth).
Provides interactive autocomplete via questionary + Typer sub-app.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Optional

import questionary
import typer

from cli.theme import get_theme
from cli.tui.router import ROUTE_TABLE, CommandMatch, fuzzy_match, get_all_commands

# -- Typer sub-app (registered in entrypoint.py) --
palette_app = typer.Typer(
    help="Command Palette -- fuzzy search + interactive command picker",
    rich_markup_mode="rich",
)

@dataclass
class CommandMatchLocal:
    command: str
    score: float
    matched_pattern: str


def fuzzy_search(
    query: str,
    routing_table_or_max=None,
    max_results: int = 5,
) -> list[CommandMatchLocal]:
    """Match query against routing table via the unified router.

    Old API: fuzzy_search(query, custom_routing_table, [max_results])
      custom_routing_table: list of (command, [vi], [en]) tuples

    New API: fuzzy_search(query) or fuzzy_search(query, max_results=N)
      Uses unified ROUTE_TABLE from cli.tui.router (via fuzzy_match).

    When a custom routing table is supplied (old-format tuples), converts
    to RouteEntry objects and delegates matching to RouteTable.fuzzy()
    instead of reimplementing the matching logic inline.
    """
    if not query or not query.strip():
        return []

    # Old API: custom routing table provided -- convert to RouteEntry
    # and delegate to RouteTable (single matching implementation).
    if isinstance(routing_table_or_max, (list, tuple)):
        entries: list = []
        for item in routing_table_or_max:
            if isinstance(item, tuple) and len(item) == 3:
                cmd, vi, en = item
            elif hasattr(item, "command"):
                cmd = item.command
                vi = item.vi_keywords
                en = item.en_keywords
            else:
                continue
            from cli.tui.router import RouteEntry
            entries.append(RouteEntry(command=cmd, vi_keywords=tuple(vi), en_keywords=tuple(en)))
        from src.command_fabric.router import RouteTable
        table = RouteTable(entries=entries)
        max_r = max_results if isinstance(max_results, int) else 5
        results = table.fuzzy(query, max_r)
        return [
            CommandMatchLocal(command=e.command, score=e.score, matched_pattern=e.matched_pattern)
            for e in results
        ]

    # New API: use unified fuzzy_match from cli.tui.router
    if isinstance(routing_table_or_max, int):
        max_r = routing_table_or_max
    else:
        max_r = int(max_results) if max_results else 5
    entries = fuzzy_match(query, max_r)
    return [
        CommandMatchLocal(
            command=e.command,
            score=e.score,
            matched_pattern=e.matched_pattern,
        )
        for e in entries
    ]


class CommandPicker:
    """Interactive command picker using questionary autocomplete.

    Usage:
        picker = CommandPicker()
        cmd = picker.pick("tạo landing page")  # -> "cook" or None
    """

    def __init__(
        self,
        max_suggestions: int = 5,
    ) -> None:
        self.max_suggestions = max_suggestions

    def pick(self, query: str) -> Optional[str]:
        """Show autocomplete prompt, return selected command or None."""
        results = fuzzy_search(query, self.max_suggestions)
        if not results:
            return None

        choices = [r.command for r in results]
        answer = questionary.autocomplete(
            "mekong >",
            choices=choices,
            default=query,
        ).ask()
        return answer if answer else None


# -- Typer commands --

@palette_app.command("search")
def palette_search(
    query: str = typer.Argument("", help="Từ khóa tìm kiếm (VI/EN)"),
) -> None:
    """Tìm và chạy command bằng ngôn ngữ tự nhiên."""
    from rich.console import Console

    console = Console(theme=get_theme())

    if not query:
        # No query -> show full catalog as select
        all_commands = sorted(get_all_commands())
        answer = questionary.select(
            "Chọn command:",
            choices=all_commands,
        ).ask()
        if answer:
            _exec_command(answer, console)
        return

    results = fuzzy_search(query)
    if not results:
        console.print(
            f"[yellow]Không tìm thấy command cho:[/yellow] [bold]{query}[/bold]"
        )
        console.print("[dim]Thử: /ask, /brainstorm, hoặc mekong --help[/dim]")
        return

    # Show matches + let user pick
    top = results[0]
    console.print(
        f"\n[bold]Kết quả cho:[/bold] [cyan]{query}[/cyan]\n"
        f" [green]-> {top.command}[/green] [dim](match: {top.matched_pattern})[/dim]\n"
    )

    confirm = questionary.confirm(
        f"Chạy [bold]mekong {top.command}[/bold]?", default=True
    ).ask()
    if confirm:
        _exec_command(top.command, console)


def _exec_command(command: str, console=None) -> None:
    """Execute a mekong subcommand via python3 -m src.main."""
    import sys
    from rich.console import Console as RichConsole

    c = console or RichConsole(theme=get_theme())
    c.print(f"\n[bold cyan] mekong {command}[/bold cyan]")
    c.print("[dim]-" * 40 + "[/dim]")
    try:
        subprocess.run(
            [sys.executable, "-m", "src.main", command],
            check=False,
        )
    except KeyboardInterrupt:
        c.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        c.print(f"[red]Loi:[/red] {e}")
