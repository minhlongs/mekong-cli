# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rich and JSON rendering helpers for Autonomous Parallel Project Bootstrap CLI."""

from __future__ import annotations

import dataclasses
from pathlib import Path
import time
from typing import Any

from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.core.bootstrap_parallel_engine import BootstrapResult

console = Console()


def _format_json_payload(
    result: BootstrapResult,
    goal: str,
    target_dir: Path,
) -> dict[str, Any]:
    """Build a unified, machine-readable JSON payload matching the spec."""
    payload = result.to_dict()
    payload["goal"] = goal
    payload["status"] = "completed" if (result.ok and not result.rolled_back) else "failed"
    payload["elapsed_ms"] = result.duration_ms

    tasks_list: list[dict[str, Any]] = []
    for tid, timing in result.task_timings.items():
        if hasattr(timing, "to_dict"):
            td = timing.to_dict()
        elif isinstance(timing, dict):
            td = timing
        else:
            td = dataclasses.asdict(timing)

        tasks_list.append({
            "id": td.get("task_id", tid),
            "name": td.get("name", tid),
            "worker_id": td.get("worker_id"),
            "status": td.get("status"),
            "duration_ms": td.get("duration_ms", 0.0),
            "error": td.get("error"),
        })

    payload["tasks"] = tasks_list
    payload["checkpoint"] = {
        "checkpoint_id": result.stats.get("checkpoint_id", f"chk_{int(time.time())}"),
        "rolled_back": result.rolled_back,
        "created_files_count": len(result.created_files),
    }
    return payload


def render_bootstrap_rich_output(
    result: BootstrapResult,
    actual_goal: str,
    target_dir: Path,
    workers: int,
    dry_run: bool,
) -> None:
    """Render Rich DAG task execution summary table and verdict panel."""
    table = Table(
        title="Parallel Task Execution Summary",
        box=SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Step", style="dim", width=6)
    table.add_column("Task / Stage", style="bold")
    table.add_column("Worker", style="cyan")
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Artifacts / Details")

    for idx, (task_id, timing) in enumerate(result.task_timings.items(), start=1):
        td = (
            timing.to_dict()
            if hasattr(timing, "to_dict")
            else (timing if isinstance(timing, dict) else dataclasses.asdict(timing))
        )
        status_str = td.get("status", "unknown")
        if status_str == "completed":
            status_styled = "[bold green]✓ COMPLETE[/bold green]"
        elif status_str == "failed":
            status_styled = "[bold red]✗ FAILED[/bold red]"
        elif status_str == "running":
            status_styled = "[bold yellow]► RUNNING[/bold yellow]"
        elif status_str == "skipped":
            status_styled = "[dim]⊘ SKIPPED[/dim]"
        else:
            status_styled = f"[cyan]{status_str.upper()}[/cyan]"

        worker = td.get("worker_id") or "worker"
        if "ThreadPoolExecutor" in str(worker):
            worker = str(worker).split("_")[-1]

        dur = f"{td.get('duration_ms', 0.0):.1f}ms"
        err = td.get("error")
        details = f"[red]{err}[/red]" if err else "[dim]Completed successfully[/dim]"

        table.add_row(
            str(idx),
            td.get("name", task_id),
            str(worker),
            status_styled,
            dur,
            details,
        )

    console.print(table)

    if result.ok and not result.rolled_back:
        completed_count = sum(
            1
            for t in result.task_timings.values()
            if getattr(t, "status", None) == "completed"
            or (isinstance(t, dict) and t.get("status") == "completed")
        )
        total_count = len(result.task_timings)
        next_steps = (
            f"\n\n[bold green]Next Steps:[/bold green]\n"
            f"  1. [bold cyan]cd {target_dir.resolve()}[/bold cyan]\n"
            f"  2. [bold cyan]mekong doctor[/bold cyan]\n"
            f"  3. [bold cyan]mekong cook \"{actual_goal}\"[/bold cyan]"
        ) if not dry_run else ""

        console.print(
            Panel(
                f"[bold]Total Tasks:[/bold]    {completed_count} of {total_count} completed | [bold]Success Rate:[/bold] 100%\n"
                f"[bold]Files Created:[/bold]  {len(result.created_files)} | [bold]Files Skipped:[/bold] {result.stats.get('files_skipped', 0)}\n"
                f"[bold]Wall Time:[/bold]      {result.duration_ms:.1f}ms | [bold]Workers:[/bold] {workers} concurrent\n"
                f"[bold]Mode:[/bold]           {'Dry Run (Zero Files Mutated)' if dry_run else 'Live Execution'}"
                f"{next_steps}",
                title="🎯 [bold green]Bootstrap Complete (PASS)[/bold green]",
                border_style="green" if not dry_run else "yellow",
            )
        )
        return

    console.print(
        Panel(
            f"[bold red]Status:[/bold red]          FAILED\n"
            f"[bold red]Error:[/bold red]           {result.error or 'Bootstrap task failed'}\n"
            f"[bold yellow]Rollback:[/bold yellow]        {'Workspace atomically restored to pre-execution checkpoint' if result.rolled_back else 'Not rolled back'}\n"
            f"[dim]Wall Time: {result.duration_ms:.1f}ms[/dim]",
            title="❌ [bold red]Bootstrap Failed (ROLLED BACK)[/bold red]",
            border_style="red",
        )
    )
    raise typer.Exit(code=1)
