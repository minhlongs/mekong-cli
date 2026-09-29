# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/daily_command.py — Autonomous Daily Executive Briefing CLI.

Coordinates daily status reporting: git activity, open technical debt (TODO/FIXME),
queue depth, and synthesized strategic focus priorities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.daily_briefing import (
    DailyBriefingEngine,
    DailyBriefingReport,
    get_daily_briefing_engine,
)

console = Console()


def register_daily_command(app: typer.Typer) -> None:
    """Register the 'daily' command onto the main Typer application."""

    @app.command(name="daily")
    def daily_cmd(
        since: str = typer.Option(
            "24 hours ago",
            "--since",
            "-s",
            help="Time window for git commit velocity (e.g. '24 hours ago', '7 days ago', 'midnight')",
        ),
        todos: bool = typer.Option(
            True,
            "--todos/--no-todos",
            help="Scan and report open codebase technical debt (TODO, FIXME, HACK)",
        ),
        export_path: Optional[str] = typer.Option(
            None,
            "--export",
            "-e",
            help="Export daily briefing report to specified markdown file path",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON daily briefing",
        ),
    ) -> None:
        """🏯 Daily status report — revenue, pending approvals, system health, today's focus."""
        engine = get_daily_briefing_engine()
        report = engine.generate_report(since=since, include_debt=todos)

        # Optional Export
        if export_path:
            p = Path(export_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if export_path.endswith(".json") or json_output:
                p.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
            else:
                content = (
                    f"# Daily Briefing — {report.date}\n\n"
                    f"- **Repository:** {report.repo_name}\n"
                    f"- **Branch:** {report.current_branch}\n"
                    f"- **Commits ({since}):** {report.commits_count}\n"
                    f"- **Dirty Files:** {report.dirty_files_count}\n\n"
                    f"## Focus Priorities\n"
                    + "\n".join(f"- {p}" for p in report.focus_priorities)
                    + "\n"
                )
                p.write_text(content, encoding="utf-8")

        if json_output:
            print(json.dumps(report.to_dict(), indent=2))
            if not report.ok:
                raise typer.Exit(code=1)
            return

        if not report.ok:
            console.print(f"[bold red]Daily report error:[/bold red] {report.error}")
            raise typer.Exit(code=1)

        # Build Executive Dashboard Panel
        header_text = (
            f"[bold cyan]🏯 DAILY REPORT — {report.date}[/bold cyan]\n"
            f"[dim]Repository:[/dim]  [bold]{report.repo_name}[/bold]  |  "
            f"[dim]Branch:[/dim]      [cyan]{report.current_branch}[/cyan]\n"
            f"[dim]Activity:[/dim]    [green]{report.commits_count} commits[/green] "
            f"(window: [dim]{since}[/dim])  |  "
            f"[dim]Dirty:[/dim]       {report.dirty_files_count} uncommitted files\n"
            f"[dim]Mesh Health:[/dim] Queue depth {report.queue_depth}  |  "
            f"DLQ {report.dlq_count} dead tasks"
        )
        console.print(Panel(header_text, title="Executive Standup", border_style="cyan", box=ROUNDED))

        # Recent Commits Table
        if report.recent_commits:
            c_table = Table(title="Recent Git Activity", box=ROUNDED)
            c_table.add_column("SHA", style="dim", width=9)
            c_table.add_column("Author", style="cyan")
            c_table.add_column("Age", style="yellow")
            c_table.add_column("Commit Message")

            for c in report.recent_commits:
                c_table.add_row(c.sha, c.author[:18], c.date, c.message[:60])
            console.print(c_table)

        # Technical Debt Table
        if report.debt_items:
            d_table = Table(title="Open Action Markers & Debt", box=ROUNDED)
            d_table.add_column("Marker", style="bold red", width=8)
            d_table.add_column("Location", style="cyan")
            d_table.add_column("Details")

            for d in report.debt_items:
                marker_style = "bold red" if d.marker in ("FIXME", "XXX") else "bold yellow"
                d_table.add_row(f"[{marker_style}]{d.marker}[/{marker_style}]", f"{d.file}:{d.line}", d.text)
            console.print(d_table)

        # Strategic Focus
        if report.focus_priorities:
            focus_lines = "\n".join(f"  • [bold green]{p}[/bold green]" for p in report.focus_priorities)
            console.print(
                Panel(
                    focus_lines,
                    title="🎯 Today's Strategic Focus",
                    border_style="green",
                    box=ROUNDED,
                )
            )

        if export_path:
            console.print(f"[dim]Exported briefing to {export_path}[/dim]")
