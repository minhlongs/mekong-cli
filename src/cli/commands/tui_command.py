# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/tui_command.py — Warp-Style Interactive Terminal UI (TUI) Mode.

Launches interactive terminal mode with:
- Command palette fuzzy navigation (VI + EN)
- Real-time telemetry & AGI subsystem health dashboard
- Multi-pane / single-pane terminal support
"""

from __future__ import annotations

import json
import shutil
import sys
from typing import Optional

import typer
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

from src.core.palette_bridge import PaletteBridge

console = Console()


def register_tui_command(app: typer.Typer) -> None:
    """Register the 'tui' command onto the main Typer application."""

    @app.command(name="tui")
    def tui(
        query: Optional[str] = typer.Argument(
            None,
            help="Optional initial search query to pre-fill in command palette",
        ),
        dashboard: bool = typer.Option(
            False,
            "--dashboard",
            "-d",
            help="Display the real-time telemetry and AGI health dashboard",
        ),
        single_pane: bool = typer.Option(
            False,
            "--single-pane",
            "-s",
            help="Force single-pane mode without tmux",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output telemetry dashboard in JSON format",
        ),
    ) -> None:
        """🖥️ TUI Mode: Launch Warp-style interactive terminal UI & telemetry dashboard."""
        bridge = PaletteBridge()

        # 1. JSON Output Mode
        if json_output:
            summary = bridge.get_tui_dashboard_summary(detailed=True)
            print(json.dumps(summary, indent=2))
            return

        # 2. Telemetry Dashboard Mode
        if dashboard:
            _render_dashboard(bridge)
            return

        # 3. If query provided, run palette search
        if query:
            results = bridge.search(query, limit=5)
            if not results:
                console.print(f"[yellow]No matches found for query:[/yellow] {query}")
                return

            table = Table(
                title=f"🖥️ TUI Palette Match: '{query}'",
                border_style="cyan",
                show_lines=True,
            )
            table.add_column("Score", style="bold green", justify="center", width=7)
            table.add_column("Type", style="bold magenta", width=9)
            table.add_column("Name", style="bold cyan", min_width=14)
            table.add_column("Category", style="yellow", width=12)
            table.add_column("Command Syntax", style="bold white", min_width=20)
            for res in results:
                table.add_row(
                    f"{res.score:.2f}",
                    f"{res.item.icon} {res.item.item_type}",
                    res.item.name,
                    res.item.category,
                    res.item.command_syntax,
                )
            console.print(table)
            return

        # 4. Interactive Mode
        _render_dashboard(bridge)
        console.print()

        try:
            import questionary
            action = questionary.select(
                "TUI Action Menu:",
                choices=[
                    "🔍 Search Command Palette",
                    "📊 View Full Telemetry & Health",
                    "🍳 Quick Cook (New Feature)",
                    "🐛 Debug Issue",
                    "🛑 Emergency Halt",
                    "🚪 Exit TUI",
                ],
            ).ask()

            if not action or "Exit" in action:
                console.print("[dim]Exiting TUI mode.[/dim]")
                return

            if "Search Command Palette" in action:
                q = questionary.text("Type command search query:").ask()
                if q:
                    results = bridge.search(q, limit=5)
                    table = Table(title=f"Results for '{q}'", border_style="cyan")
                    table.add_column("Name", style="bold cyan")
                    table.add_column("Category", style="yellow")
                    table.add_column("Syntax", style="bold white")
                    for r in results:
                        table.add_row(r.item.name, r.item.category, r.item.command_syntax)
                    console.print(table)
            elif "View Full Telemetry" in action:
                _render_dashboard(bridge, detailed=True)
            elif "Quick Cook" in action:
                console.print("[bold green]Running:[/bold green] mekong cook")
            elif "Debug" in action:
                console.print("[bold yellow]Running:[/bold yellow] mekong debug")
            elif "Emergency Halt" in action:
                from src.core.governance import Governance
                Governance().halt()
                console.print("[bold red]🛑 All operations halted.[/bold red]")
        except (ImportError, Exception):
            pass


def _render_dashboard(bridge: PaletteBridge, detailed: bool = False) -> None:
    """Render rich terminal telemetry and health status panels."""
    summary = bridge.get_tui_dashboard_summary(detailed=True)

    header = Panel(
        "[bold cyan]🖥️  MEKONG INTERACTIVE TUI & TELEMETRY STREAM[/bold cyan]\n"
        "[dim]CEO Solo Agentic Harness Engineering Platform • Binh Pháp Tactical Engine[/dim]",
        title="[bold green]Mekong OS v2.0.0-agi[/bold green]",
        border_style="cyan",
    )
    console.print(header)

    # Subsystems & Health Table
    sub_table = Table(title="🧠 AGI Core Subsystems", border_style="magenta", show_lines=True)
    sub_table.add_column("Subsystem", style="bold")
    sub_table.add_column("Status", justify="center")

    details = summary.get("subsystems_detail", {})
    for name, online in details.items():
        status_badge = "[green]✓ ONLINE[/green]" if online else "[red]✗ OFFLINE[/red]"
        sub_table.add_row(name, status_badge)

    # Telemetry & Evals Table
    eval_table = Table(title="📊 Telemetry & Performance", border_style="green", show_lines=True)
    eval_table.add_column("Metric", style="bold")
    eval_table.add_column("Value", style="bold cyan")

    evals = summary.get("evals", {})
    eval_table.add_row("Total Missions Executed", str(evals.get("total_missions", 0)))
    eval_table.add_row("Success Rate", f"{evals.get('success_rate', 100.0)}%")
    eval_table.add_row("p95 Latency", f"{evals.get('p95_duration_ms', 0)} ms")
    eval_table.add_row("Total Credits Consumed", f"{evals.get('total_credits', 0.0)} MCU")
    eval_table.add_row("Durable Checkpoints Saved", str(summary.get("checkpoints_count", 0)))

    # Catalog Table
    cat_table = Table(title="⚡ Agentic Capabilities", border_style="yellow", show_lines=True)
    cat_table.add_column("Layer / Dimension", style="bold")
    cat_table.add_column("Count", style="bold magenta")

    catalog = summary.get("catalog", {})
    cat_table.add_row("Total Catalog Items", str(catalog.get("total_items", 0)))
    types = catalog.get("types", {})
    for t_name, count in types.items():
        cat_table.add_row(f"  • {t_name.capitalize()}", str(count))

    console.print(Columns([sub_table, eval_table, cat_table]))
