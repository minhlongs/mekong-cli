# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/palette_command.py — Interactive Command Palette CLI.

Fuzzy search across Mekong CLI commands, Antigravity skills, and domain subagents
with bilingual Vietnamese + English support and real-time interactive autocomplete.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.palette_bridge import PaletteBridge

console = Console()


def register_palette_command(app: typer.Typer) -> None:
    """Register the 'palette' command onto the main Typer application."""

    @app.command(name="palette")
    def palette(
        query: Optional[str] = typer.Argument(
            None,
            help="Natural language search query in Vietnamese or English (e.g. 'sửa lỗi', 'kế hoạch', 'cook')",
        ),
        category: str = typer.Option(
            "all",
            "--category",
            "-c",
            help="Filter category: strategy, business, product, engineering, operations, vietnam, or all",
        ),
        limit: int = typer.Option(
            5,
            "--limit",
            "-l",
            help="Maximum number of matches to display",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output search matches in JSON format (ideal for headless MCP tools)",
        ),
        execute: bool = typer.Option(
            False,
            "--exec",
            "-x",
            help="Automatically execute the top matching command",
        ),
    ) -> None:
        """🔍 Command Palette: Fuzzy search Mekong commands, skills, and subagents (VI + EN)."""
        bridge = PaletteBridge()

        # Handle direct query or non-interactive
        active_query = query

        # Interactive loop if no query provided and in a real interactive terminal
        if not active_query and sys.stdin.isatty() and not json_output:
            console.print(
                Panel(
                    "[bold cyan]🔍 Mekong Command Palette[/bold cyan] — [dim]Warp-Style Interactive Terminal[/dim]\n"
                    "Search across 230+ skills, 25 subagents, and 60+ commands.\n"
                    "[dim]Bilingual: Type Vietnamese ('sửa lỗi', 'kế toán') or English ('debug', 'tax')[/dim]",
                    title="Mekong CLI",
                    border_style="cyan",
                )
            )

            try:
                import questionary
                user_input = questionary.text(
                    "Enter search query (or press Enter to view top commands, 'q' to quit):"
                ).ask()
                if not user_input or user_input.strip().lower() == "q":
                    console.print("[dim]Palette closed.[/dim]")
                    return
                active_query = user_input.strip()
            except (ImportError, Exception):
                pass

        results = bridge.search(active_query, category=category, limit=limit)

        if json_output:
            output = {
                "ok": True,
                "query": active_query or "",
                "category": category,
                "total_matches": len(results),
                "matches": [r.to_dict() for r in results],
            }
            print(json.dumps(output, indent=2))
            return

        if not results:
            console.print(
                Panel(
                    f"[yellow]No direct match found for:[/yellow] [bold]{active_query}[/bold]\n\n"
                    "Suggestions:\n"
                    "  • Try broad keywords: [cyan]cook[/cyan], [cyan]plan[/cyan], [cyan]debug[/cyan], [cyan]thue[/cyan], [cyan]ke-toan[/cyan]\n"
                    "  • Or use [bold]mekong ask[/bold] for natural language assistance",
                    title="🔍 Search Results",
                    border_style="yellow",
                )
            )
            return

        # Render Rich Table
        table = Table(
            title=f"🔍 Command Palette Results: '{active_query or 'Top Catalog'}'",
            border_style="cyan",
            show_lines=True,
        )
        table.add_column("Score", style="bold green", justify="center", width=7)
        table.add_column("Type", style="bold magenta", width=9)
        table.add_column("Name", style="bold cyan", min_width=14)
        table.add_column("Category", style="yellow", width=12)
        table.add_column("Description", style="dim", min_width=30)
        table.add_column("Command Syntax", style="bold white", min_width=20)

        for res in results:
            item = res.item
            score_str = f"{res.score:.2f}"
            icon = item.icon
            table.add_row(
                score_str,
                f"{icon} {item.item_type}",
                item.name,
                item.category,
                item.description,
                f"[underline]{item.command_syntax}[/underline]",
            )

        console.print(table)

        if execute and results:
            top_match = results[0].item
            console.print(f"\n[bold green]Executing top match:[/bold green] {top_match.command_syntax}")
            cmd_args = shlex.split(top_match.command_syntax)
            if cmd_args and cmd_args[0] == "mekong":
                # Run through python -m src.main
                full_cmd = [sys.executable, "-m", "src.main"] + cmd_args[1:]
                subprocess.run(full_cmd)
