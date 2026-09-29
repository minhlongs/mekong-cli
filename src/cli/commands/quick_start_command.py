# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/quick_start_command.py — CLI command surface for 5-Step Project Kickoff Engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from src.core.quick_start_engine import get_quick_start_engine

console = Console()


def register_quick_start_command(app: typer.Typer) -> None:
    """Register the 'quick-start' command onto the main Typer application."""

    @app.command(name="quick-start")
    def quick_start_cmd(
        project_name: str = typer.Argument(
            ...,
            help="Name or slug of the new project to initialize",
        ),
        project_type: str = typer.Option(
            "agent",
            "--type",
            "-t",
            help="Project archetype: 'cli', 'web', 'agent', 'fullstack'",
        ),
        target_dir: Optional[str] = typer.Option(
            None,
            "--dir",
            "-d",
            help="Destination directory (defaults to ./<project_name>)",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Simulate the 5-step kickoff process without writing files or initializing git",
        ),
        no_git: bool = typer.Option(
            False,
            "--no-git",
            help="Skip automatic git repository initialization and initial commit",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON kickoff report",
        ),
    ) -> None:
        """🚀 Start any new project from idea to production in 5 steps. Quick project kickoff."""
        engine = get_quick_start_engine()
        dest_path = Path(target_dir).resolve() if target_dir else None

        report = engine.kickoff(
            project_name=project_name,
            project_type=project_type,
            target_dir=dest_path,
            dry_run=dry_run,
            init_git=not no_git,
        )

        if json_output:
            print(json.dumps(report.to_dict(), indent=2))
            if not report.ok:
                raise typer.Exit(code=1)
            return

        if not report.ok:
            console.print(f"[bold red]Quick-Start Error:[/bold red] {report.error}")
            raise typer.Exit(code=1)

        # Header Panel
        dry_run_badge = " [bold yellow][DRY RUN][/bold yellow]" if dry_run else ""
        header_text = (
            f"[bold cyan]🚀 QUICK START KICKOFF — 5 STEPS{dry_run_badge}[/bold cyan]\n"
            f"[dim]Project Name:[/dim] [bold]{report.project_name}[/bold]  |  "
            f"[dim]Archetype:[/dim]    [cyan]{report.project_type.upper()}[/cyan]\n"
            f"[dim]Destination:[/dim]  [green]{report.target_dir}[/green]  |  "
            f"[dim]Created At:[/dim]   {report.created_at}"
        )
        console.print(Panel(header_text, border_style="cyan", box=ROUNDED))

        # 5 Steps Table
        steps_table = Table(title="5-Step Autonomous Execution Lifecycle", box=ROUNDED)
        steps_table.add_column("Step", justify="center", style="bold", width=6)
        steps_table.add_column("Phase", style="bold cyan", width=24)
        steps_table.add_column("Status", justify="center", width=12)
        steps_table.add_column("Summary / Outcome")

        for s in report.steps:
            if s.status in ("completed", "done"):
                status_str = "[bold green]✓ DONE[/bold green]"
            elif s.status == "simulated":
                status_str = "[bold yellow]SIMULATED[/bold yellow]"
            else:
                status_str = f"[bold dim]{s.status.upper()}[/bold dim]"

            steps_table.add_row(f"{s.step_number}", s.name, status_str, s.summary)

        console.print(steps_table)

        # File Tree
        if report.files_created:
            tree = Tree(f"[bold]{report.project_name}/[/bold]")
            for f in sorted(report.files_created):
                parts = f.split("/")
                current = tree
                for part in parts[:-1]:
                    # Search or add subtree
                    match = next((c for c in current.children if str(c.label) == f"[cyan]{part}/[/cyan]"), None)
                    if match is None:
                        current = current.add(f"[cyan]{part}/[/cyan]")
                    else:
                        current = match
                current.add(f"[green]{parts[-1]}[/green]")
            console.print(Panel(tree, title="📦 Generated Project Hierarchy", border_style="dim", box=ROUNDED))

        # Next Steps
        if report.next_steps:
            next_text = "\n".join(f"  [bold cyan]${dry_run_badge}[/bold cyan] {cmd}" for cmd in report.next_steps)
            console.print(
                Panel(
                    next_text,
                    title="🎯 Recommended Next Actions",
                    border_style="green",
                    box=ROUNDED,
                )
            )
