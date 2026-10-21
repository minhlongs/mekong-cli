# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""cli/commands/pipeline_command.py — Multi-Agent Sequential Pipeline CLI."""

from __future__ import annotations

import json

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
        goal: str = typer.Argument(..., help="Goal or task description for the multi-agent pipeline to execute"),
        stages: str = typer.Option("file-picker,editor,reviewer", "--stages", "-s", help="Comma-separated agent names"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON pipeline result"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed per-stage output and diagnostics"),
    ) -> None:
        """Run multi-agent pipeline (FilePicker -> Editor -> Reviewer). 3-5 MCU."""
        stage_list = [s.strip() for s in stages.split(",") if s.strip()] or ["file-picker", "editor", "reviewer"]
        pm = get_pipeline_manager()

        if not json_output:
            console.print(Panel(
                f"[bold cyan]⚡ Multi-Agent Sequential Pipeline[/bold cyan]\n"
                f"[dim]Goal:[/dim]   {goal}\n[dim]Stages:[/dim] {' → '.join(stage_list)}\n"
                f"[dim]Flow:[/dim]   FilePicker (plan) → Editor (execute) → Reviewer (verify)",
                title="Mekong Agentic Pipeline", border_style="cyan", box=ROUNDED,
            ))

        try:
            result = pm.run_multi_agent_pipeline(goal=goal, stages=stage_list)
        except Exception as exc:
            if json_output:
                print(json.dumps({"ok": False, "error": str(exc), "goal": goal, "status": PipelineStatus.FAILED.value}, indent=2))
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

        table = Table(title="Pipeline Execution Summary", header_style="bold magenta", border_style="dim", box=ROUNDED)
        for col, kw in [
            ("Order", {"justify": "center", "style": "dim", "width": 6}), ("Stage", {"style": "cyan bold", "width": 16}),
            ("Status", {"justify": "center", "width": 14}), ("Duration", {"justify": "right", "style": "green", "width": 12}),
            ("Summary / Artifacts", {"style": "white"}),
        ]:
            table.add_column(col, **kw)

        status_map = {"completed": "[bold green]✓ Completed[/bold green]", "failed": "[bold red]✗ Failed[/bold red]", "skipped": "[bold yellow]○ Skipped[/bold yellow]"}
        for stage in result.stages:
            status_str = status_map.get(stage.status, f"[bold cyan]{stage.status}[/bold cyan]")
            duration_str = f"{stage.duration_ms:.1f}ms" if stage.duration_ms > 0 else "-"
            summary_snippet = f"[red]{stage.error[:80]}[/red]" if stage.error else (stage.output.strip().split("\n")[0][:80] if stage.output else "[dim]No output[/dim]")
            table.add_row(str(stage.order), stage.name or stage.id, status_str, duration_str, summary_snippet)
        console.print(table)

        if verbose:
            for stage in result.stages:
                border_color = "green" if stage.status == "completed" else ("red" if stage.status == "failed" else "yellow")
                console.print(Panel((stage.output or stage.error or "(No output)").strip(), title=f"Stage [{stage.order}] {stage.name or stage.id} ({stage.status})", border_style=border_color, box=ROUNDED))

        if result.status == PipelineStatus.COMPLETED:
            console.print(Panel(
                f"[bold green]✓ Pipeline Completed Successfully[/bold green]\n"
                f"[dim]Total Stages:[/dim] {result.total_stages} | [dim]Success Rate:[/dim] {result.success_rate:.0f}% | [dim]Duration:[/dim] {result.total_duration_ms:.1f}ms\n"
                f"[dim]Pipeline ID:[/dim]  {result.pipeline_id}",
                title="Verdict: PASS", border_style="green", box=ROUNDED,
            ))
        else:
            err_msg = "; ".join(result.errors) if result.errors else "One or more stages failed"
            console.print(Panel(
                f"[bold red]✗ Pipeline Execution Incomplete[/bold red]\n"
                f"[dim]Status:[/dim]       {result.status.value.upper()}\n[dim]Failed Stages:[/dim] {result.failed_stages} of {result.total_stages}\n"
                f"[dim]Errors:[/dim]        {err_msg}\n[dim]Pipeline ID:[/dim]  {result.pipeline_id}",
                title="Verdict: FAIL", border_style="red", box=ROUNDED,
            ))
            raise typer.Exit(code=1)
