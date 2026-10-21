# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""First-class ``orchestrate`` command for multi-agent pipeline orchestration.

Dispatches natural language or structured requests across real Mekong execution
engines: Harness PEV (harness / harness-eval / pev), bug repair (/fix), and
autonomous mission execution (/goal), producing file-based pipeline handoff
artifacts in `.orchestrate/latest/`.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel

console = Console()


def register_orchestrate_command(app: typer.Typer) -> None:
    """Register the top-level ``orchestrate`` command on the root app."""

    @app.command(name="orchestrate")
    def orchestrate_cmd(
        context: Optional[str] = typer.Argument(
            None,
            help="Goal, issue, prompt, or task to orchestrate through the pipeline",
        ),
        template: Optional[str] = typer.Option(
            None,
            "--template",
            "-t",
            help="Workflow template: harness | fix | goal | cook | debug | review | research (or auto-classified)",
        ),
        count: int = typer.Option(
            3,
            "--count",
            "-c",
            help="Number of subagents / workers to allocate",
        ),
        delegate: bool = typer.Option(
            False,
            "--delegate",
            help="Enable lead-delegate coordination mode",
        ),
        worktree: bool = typer.Option(
            True,
            "--worktree/--no-worktree",
            help="Enable git worktree isolation for implementation developers",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Plan and validate pipeline without modifying source files or running commands",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output structured machine-readable JSON execution report",
        ),
    ) -> None:
        """🚀 Orchestrate multi-agent workflows (Harness PEV, /fix, /goal, cook, debug)."""
        from src.core.team_manager import get_team_manager

        if not context and not template:
            console.print("[dim]No task provided. Showing orchestrate help.[/dim]")
            raise typer.Exit(code=0)

        task_prompt = (context or "").strip()
        manager = get_team_manager()

        report = manager.orchestrate(
            template=template or "",
            context=task_prompt,
            count=count,
            delegate=delegate,
            worktree=worktree,
            dry_run=dry_run,
        )

        if json_output:
            console.print_json(data=report.to_dict())
            return

        status_style = "green" if report.status in ("completed", "satisfied", "success") else "yellow"
        console.print(
            Panel(
                f"[bold cyan]Template:[/bold cyan]        {report.template.upper()}\n"
                f"[bold cyan]Mục Tiêu:[/bold cyan]        {report.goal}\n"
                f"[dim]Trạng Thái:[/dim]        [{status_style}]{report.status.upper()}[/{status_style}]\n"
                f"[dim]Đội Ngũ:[/dim]           {report.team_name} ({report.members_count} tác nhân)\n"
                f"[dim]Tiến Độ:[/dim]           {report.tasks_completed}/{report.tasks_total} nhiệm vụ\n"
                f"[dim]Tóm Tắt:[/dim]           {report.summary}\n"
                f"[dim]Handoff Folder:[/dim]    [bold green].orchestrate/latest/[/bold green]\n"
                f"[dim]Báo Cáo Chi Tiết:[/dim]  [bold green]{report.report_file}[/bold green]",
                title="[bold green]✓ Điều Phối Pipeline Hoàn Tất (Orchestration Complete)[/bold green]",
                border_style=status_style,
                box=ROUNDED,
            )
        )


__all__ = ["register_orchestrate_command"]
