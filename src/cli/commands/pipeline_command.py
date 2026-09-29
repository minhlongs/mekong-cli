# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/pipeline_command.py — Multi-Agent Sequential Pipeline CLI.

Coordinates specialized domain agents (FilePicker -> Editor -> Reviewer)
to execute end-to-end software development workflows with automated validation.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.pipeline_manager import PipelineStatus, get_pipeline_manager

console = Console()


def register_pipeline_command(app: typer.Typer) -> None:
    """Register the 'pipeline' command onto the main Typer application."""

    @app.command(name="pipeline")
    def pipeline(
        goal: str = typer.Argument(
            ...,
            help="Goal or task description for the multi-agent pipeline to execute",
        ),
        stages: str = typer.Option(
            "file-picker,editor,reviewer",
            "--stages",
            "-s",
            help="Comma-separated agent names (e.g. file-picker,editor,reviewer)",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON pipeline result",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="Show detailed per-stage output and diagnostics",
        ),
    ) -> None:
        """Run multi-agent pipeline (FilePicker -> Editor -> Reviewer). 3-5 MCU."""
        # Parse stages
        stage_list = [s.strip() for s in stages.split(",") if s.strip()]
        if not stage_list:
            stage_list = ["file-picker", "editor", "reviewer"]

        pm = get_pipeline_manager()

        if not json_output:
            console.print(
                Panel(
                    f"[bold cyan]⚡ Multi-Agent Sequential Pipeline[/bold cyan]\n"
                    f"[dim]Goal:[/dim]   {goal}\n"
                    f"[dim]Stages:[/dim] {' → '.join(stage_list)}\n"
                    f"[dim]Flow:[/dim]   FilePicker (plan) → Editor (execute) → Reviewer (verify)",
                    title="Mekong Agentic Pipeline",
                    border_style="cyan",
                    box=ROUNDED,
                )
            )

        # Run pipeline
        try:
            result = pm.run_multi_agent_pipeline(goal=goal, stages=stage_list)
        except Exception as exc:
            if json_output:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": str(exc),
                            "goal": goal,
                            "status": PipelineStatus.FAILED.value,
                        },
                        indent=2,
                    )
                )
            else:
                console.print(f"[bold red]Pipeline initialization failed:[/bold red] {exc}")
            raise typer.Exit(code=1)

        aggregated = pm.aggregate_results(result.pipeline_id)
        aggregated["goal"] = goal

        if json_output:
            print(json.dumps(aggregated, indent=2))
            if result.status != PipelineStatus.COMPLETED:
                raise typer.Exit(code=1)
            return

        # Console Summary Table
        table = Table(
            title="Pipeline Execution Summary",
            header_style="bold magenta",
            border_style="dim",
            box=ROUNDED,
        )
        table.add_column("Order", justify="center", style="dim", width=6)
        table.add_column("Stage", style="cyan bold", width=16)
        table.add_column("Status", justify="center", width=14)
        table.add_column("Duration", justify="right", style="green", width=12)
        table.add_column("Summary / Artifacts", style="white")

        for stage in result.stages:
            st_name = stage.name or stage.id
            if stage.status == "completed":
                status_str = "[bold green]✓ Completed[/bold green]"
            elif stage.status == "failed":
                status_str = "[bold red]✗ Failed[/bold red]"
            elif stage.status == "skipped":
                status_str = "[bold yellow]○ Skipped[/bold yellow]"
            else:
                status_str = f"[bold cyan]{stage.status}[/bold cyan]"

            duration_str = f"{stage.duration_ms:.1f}ms" if stage.duration_ms > 0 else "-"

            # First non-empty line of output or error
            summary_snippet = ""
            if stage.error:
                summary_snippet = f"[red]{stage.error[:80]}[/red]"
            elif stage.output:
                first_line = stage.output.strip().split("\n")[0]
                summary_snippet = first_line[:80]
            else:
                summary_snippet = "[dim]No output[/dim]"

            table.add_row(
                str(stage.order),
                st_name,
                status_str,
                duration_str,
                summary_snippet,
            )

        console.print(table)

        # Per-stage verbose output
        if verbose:
            for stage in result.stages:
                st_name = stage.name or stage.id
                content = stage.output or stage.error or "(No output)"
                border_color = "green" if stage.status == "completed" else ("red" if stage.status == "failed" else "yellow")
                console.print(
                    Panel(
                        content.strip(),
                        title=f"Stage [{stage.order}] {st_name} ({stage.status})",
                        border_style=border_color,
                        box=ROUNDED,
                    )
                )

        # Final Verdict
        if result.status == PipelineStatus.COMPLETED:
            console.print(
                Panel(
                    f"[bold green]✓ Pipeline Completed Successfully[/bold green]\n"
                    f"[dim]Total Stages:[/dim] {result.total_stages} | "
                    f"[dim]Success Rate:[/dim] {result.success_rate:.0f}% | "
                    f"[dim]Duration:[/dim] {result.total_duration_ms:.1f}ms\n"
                    f"[dim]Pipeline ID:[/dim]  {result.pipeline_id}",
                    title="Verdict: PASS",
                    border_style="green",
                    box=ROUNDED,
                )
            )
        else:
            err_msg = "; ".join(result.errors) if result.errors else "One or more stages failed"
            console.print(
                Panel(
                    f"[bold red]✗ Pipeline Execution Incomplete[/bold red]\n"
                    f"[dim]Status:[/dim]       {result.status.value.upper()}\n"
                    f"[dim]Failed Stages:[/dim] {result.failed_stages} of {result.total_stages}\n"
                    f"[dim]Errors:[/dim]        {err_msg}\n"
                    f"[dim]Pipeline ID:[/dim]  {result.pipeline_id}",
                    title="Verdict: FAIL",
                    border_style="red",
                    box=ROUNDED,
                )
            )
            raise typer.Exit(code=1)
