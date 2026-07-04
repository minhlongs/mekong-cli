"""Pipeline command: run multi-agent pipeline (file-picker -> editor -> reviewer).

Usage:
    mekong pipeline <goal>
    mekong pipeline <goal> --stages file-picker,editor,reviewer
    mekong pipeline <goal> --json
"""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.pipeline_orchestrator import (
    DEFAULT_PIPELINE,
    PipelineOrchestrator,
    PipelineResult,
    StageStatus,
)

console = Console()


def register_pipeline_command(app: typer.Typer) -> None:
    """Register the pipeline command onto the typer app."""

    @app.command()
    def pipeline(
        goal: str = typer.Argument(..., help="High-level goal for the pipeline"),
        stages: str | None = typer.Option(
            None,
            "--stages",
            help="Comma-separated agent names (default: file-picker,editor,reviewer)",
        ),
        json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Show stage details"),
    ) -> None:
        """Run multi-agent pipeline (FilePicker -> Editor -> Reviewer)."""
        stage_list = _parse_stages(stages)

        orchestrator = PipelineOrchestrator(stages=stage_list)
        result: PipelineResult = orchestrator.run(goal)

        if json_output:
            _print_json(result, verbose)
            if result.final_status != "completed":
                raise typer.Exit(code=1)
            return

        _print_rich(result, verbose)

        if result.final_status != "completed":
            raise typer.Exit(code=1)


def _parse_stages(raw: str | None) -> list[str]:
    """Parse --stages value into a list of agent names."""
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return list(DEFAULT_PIPELINE)


def _print_json(result: PipelineResult, verbose: bool) -> None:
    """Print pipeline result as JSON."""
    data = {
        "pipeline_id": result.pipeline_id,
        "goal": result.goal,
        "status": result.final_status,
        "success_rate": result.success_rate,
        "duration_ms": round(result.total_duration_ms, 1),
        "stages": [
            {
                "agent": s.agent_name,
                "status": s.status.value,
                "duration_ms": round(s.duration_ms, 1),
                "output": s.output,
                "error": s.error,
            }
            for s in result.stages
        ],
    }
    if verbose:
        data["stage_outputs"] = result.stage_outputs()
    console.print(json.dumps(data, indent=2))


def _print_rich(result: PipelineResult, verbose: bool) -> None:
    """Print pipeline result with rich formatting."""
    # Summary header
    status_color = "green" if result.final_status == "completed" else "red"
    console.print(
        Panel(
            f"[bold]Goal:[/bold] {result.goal}\n"
            f"[bold]Status:[/bold] [{status_color}]{result.final_status}[/{status_color}]\n"
            f"[bold]Success rate:[/bold] {result.success_rate:.0f}%\n"
            f"[bold]Duration:[/bold] {result.total_duration_ms:.0f}ms",
            title=f"Pipeline {result.pipeline_id}",
            border_style=status_color,
        )
    )

    # Stage table
    table = Table(title="Stages")
    table.add_column("#", style="bold cyan", justify="right")
    table.add_column("Agent", style="bold")
    table.add_column("Status")
    table.add_column("Duration", style="dim", justify="right")

    for i, stage in enumerate(result.stages, 1):
        status_str = stage.status.value.upper()
        status_style = "green" if stage.status == StageStatus.PASSED else "red"
        table.add_row(
            str(i),
            stage.agent_name,
            f"[{status_style}]{status_str}[/{status_style}]",
            f"{stage.duration_ms:.0f}ms",
        )

    console.print(table)

    # Errors
    if result.errors:
        console.print(
            Panel(
                "\n".join(f"• {e}" for e in result.errors),
                title="[red]Errors[/red]",
                border_style="red",
            )
        )

    # Per-stage output (verbose)
    if verbose:
        for stage in result.stages:
            if stage.output:
                console.print(
                    Panel(
                        stage.output[:500],
                        title=f"[bold]{stage.agent_name} output[/bold]",
                        border_style="dim",
                    )
                )

    # Final message
    if result.final_status == "completed":
        console.print("\n[bold green]Pipeline complete.[/bold green]")
    else:
        console.print("\n[bold red]Pipeline failed.[/bold red]")
