# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Parallel Project Bootstrap CLI Commands.

Exposes:
- `bootstrap-auto-parallel`: Primary command with configurable workers, profiles, templates.
- `bootstrap-auto`: Sequential or standard autonomous bootstrap companion alias.
- `bootstrap-auto-fast`: High-speed autonomous bootstrap with smoke profile and maximum parallelism.

Supports interactive Rich UX (DAG summary tables, live progress, pass/fail cards)
and machine-readable JSON output (--json) for headless CI/CD and subagent consumption.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import time
from typing import Any, List, Optional

import typer
from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.bootstrap_parallel_engine import (
    BootstrapResult,
    execute_bootstrap_parallel,
)

console = Console()

VALID_PROFILES: frozenset[str] = frozenset({"smoke", "standard", "full"})
VALID_TEMPLATES: frozenset[str] = frozenset({"default", "vas", "fintech", "agent"})


def _normalize_goal(goal: Optional[List[str] | str], default: str) -> str:
    """Normalize goal input into a trimmed string or fallback default."""
    if isinstance(goal, str):
        trimmed = goal.strip()
        return trimmed if trimmed else default
    if isinstance(goal, (list, tuple)):
        joined = " ".join(str(item) for item in goal).strip()
        return joined if joined else default
    return default


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


def _run_bootstrap_workflow(
    goal_input: Optional[List[str] | str],
    default_goal: str,
    workers: int,
    profile: str,
    template: str,
    target: Optional[Path],
    dry_run: bool,
    json_output: bool,
    force: bool,
) -> None:
    """Execute the bootstrap pipeline with validation, error handling, and formatting."""
    actual_goal = _normalize_goal(goal_input, default_goal)
    target_dir = target if target is not None else Path.cwd()

    # 1. Concurrency range validation (1-32)
    if workers < 1 or workers > 32:
        err_msg = f"Invalid worker count {workers}. Workers must be between 1 and 32."
        if json_output:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "status": "failed",
                        "goal": actual_goal,
                        "target_path": str(target_dir.resolve()),
                        "profile": profile,
                        "template": template,
                        "workers": workers,
                        "dry_run": dry_run,
                        "error": err_msg,
                    },
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[bold red]Validation Error:[/bold red] {err_msg}")
        raise typer.Exit(code=1)

    # 2. Profile validation
    norm_profile = profile.lower()
    if norm_profile == "minimal":
        norm_profile = "smoke"
    if norm_profile not in VALID_PROFILES:
        err_msg = (
            f"Unknown profile '{profile}'. Expected one of: "
            f"{', '.join(sorted(VALID_PROFILES))}"
        )
        if json_output:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "status": "failed",
                        "goal": actual_goal,
                        "target_path": str(target_dir.resolve()),
                        "profile": profile,
                        "template": template,
                        "workers": workers,
                        "dry_run": dry_run,
                        "error": err_msg,
                    },
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[bold red]Validation Error:[/bold red] {err_msg}")
        raise typer.Exit(code=1)

    # 3. Template validation
    norm_template = template.lower()
    if norm_template not in VALID_TEMPLATES:
        err_msg = (
            f"Unknown template '{template}'. Expected one of: "
            f"{', '.join(sorted(VALID_TEMPLATES))}"
        )
        if json_output:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "status": "failed",
                        "goal": actual_goal,
                        "target_path": str(target_dir.resolve()),
                        "profile": norm_profile,
                        "template": template,
                        "workers": workers,
                        "dry_run": dry_run,
                        "error": err_msg,
                    },
                    indent=2,
                )
            )
            raise typer.Exit(code=1)
        console.print(f"[bold red]Validation Error:[/bold red] {err_msg}")
        raise typer.Exit(code=1)

    # 4. Engine execution
    if not json_output:
        mode_desc = (
            "Dry Run (Zero Files Mutated)"
            if dry_run
            else "Live Execution (Atomic Checkpointing Enabled)"
        )
        console.print(
            Panel(
                f"[bold]Goal:[/bold]        {actual_goal}\n"
                f"[bold]Target:[/bold]      {target_dir.resolve()}\n"
                f"[bold]Profile:[/bold]     {norm_profile} | [bold]Template:[/bold] {norm_template}\n"
                f"[bold]Concurrency:[/bold] {workers} workers (ThreadPoolExecutor DAG)\n"
                f"[bold]Mode:[/bold]        {mode_desc}",
                title="⚡ [bold cyan]Mekong Autonomous Parallel Bootstrap Engine[/bold cyan]",
                border_style="yellow" if dry_run else "cyan",
            )
        )
        with console.status(
            f"[bold cyan]Executing topological DAG tasks across {workers} workers...[/bold cyan]"
        ):
            try:
                result = execute_bootstrap_parallel(
                    goal=actual_goal,
                    target_path=target_dir,
                    workers=workers,
                    profile=norm_profile,
                    template=norm_template,
                    dry_run=dry_run,
                    force=force,
                )
            except Exception as exc:
                console.print(f"[bold red]Bootstrap Execution Error:[/bold red] {exc}")
                raise typer.Exit(code=1)
    else:
        try:
            result = execute_bootstrap_parallel(
                goal=actual_goal,
                target_path=target_dir,
                workers=workers,
                profile=norm_profile,
                template=norm_template,
                dry_run=dry_run,
                force=force,
            )
        except Exception as exc:
            err_payload = {
                "ok": False,
                "status": "failed",
                "goal": actual_goal,
                "target_path": str(target_dir.resolve()),
                "profile": norm_profile,
                "template": norm_template,
                "workers": workers,
                "dry_run": dry_run,
                "error": str(exc),
            }
            print(json.dumps(err_payload, indent=2))
            raise typer.Exit(code=1)

    # 5. Output rendering
    if json_output:
        payload = _format_json_payload(result, actual_goal, target_dir)
        print(json.dumps(payload, indent=2))
        if not result.ok or result.rolled_back:
            raise typer.Exit(code=1)
        return

    # Rich DAG task execution summary table
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

    # Summary Verdict Panel
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
    else:
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


def register_bootstrap_command(root: typer.Typer) -> None:
    """Attach bootstrap commands and companion aliases to the root Typer application."""

    @root.command(name="bootstrap-auto-parallel")
    def bootstrap_auto_parallel_cmd(
        goal: Optional[List[str]] = typer.Argument(
            None,
            help="High-level goal or description for the parallel bootstrap process",
        ),
        workers: int = typer.Option(
            4,
            "--workers",
            "-w",
            help="Number of concurrent worker threads (1-32, default: 4)",
        ),
        profile: str = typer.Option(
            "standard",
            "--profile",
            "-p",
            help="Scaffolding verification profile: smoke | standard | full (default: standard)",
        ),
        template: str = typer.Option(
            "default",
            "--template",
            "-t",
            help="Project template preset: default | vas | fintech | agent (default: default)",
        ),
        target: Optional[Path] = typer.Option(
            None,
            "--target",
            "--path",
            help="Target directory for project workspace (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview topological DAG and tasks without disk mutations",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON result (ideal for headless CI/CD & MCP)",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            "-f",
            help="Overwrite existing files in target directory",
        ),
    ) -> None:
        """⚡ Autonomous Parallel Bootstrap: Multi-worker DAG scaffolding with atomic rollback."""
        _run_bootstrap_workflow(
            goal_input=goal,
            default_goal="Bootstrap project setup and configuration in parallel",
            workers=workers,
            profile=profile,
            template=template,
            target=target,
            dry_run=dry_run,
            json_output=json_output,
            force=force,
        )

    @root.command(name="bootstrap-auto")
    def bootstrap_auto_cmd(
        goal: Optional[List[str]] = typer.Argument(
            None,
            help="High-level goal for autonomous project bootstrap",
        ),
        profile: str = typer.Option(
            "standard",
            "--profile",
            "-p",
            help="Scaffolding verification profile: smoke | standard | full (default: standard)",
        ),
        template: str = typer.Option(
            "default",
            "--template",
            "-t",
            help="Project template preset: default | vas | fintech | agent (default: default)",
        ),
        target: Optional[Path] = typer.Option(
            None,
            "--target",
            "--path",
            help="Target directory for project workspace (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview tasks without disk mutations",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON result",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            "-f",
            help="Overwrite existing files in target directory",
        ),
        workers: int = typer.Option(
            4,
            "--workers",
            "-w",
            help="Number of concurrent worker threads (1-32, default: 4)",
        ),
    ) -> None:
        """Create, run, checkpoint, and verify a durable autonomous goal (bootstrap alias)."""
        _run_bootstrap_workflow(
            goal_input=goal,
            default_goal="Bootstrap project setup and configuration",
            workers=workers,
            profile=profile,
            template=template,
            target=target,
            dry_run=dry_run,
            json_output=json_output,
            force=force,
        )

    @root.command(name="bootstrap-auto-fast")
    def bootstrap_auto_fast_cmd(
        goal: Optional[List[str]] = typer.Argument(
            None,
            help="High-level goal for fast autonomous bootstrap",
        ),
        target: Optional[Path] = typer.Option(
            None,
            "--target",
            "--path",
            help="Target directory for project workspace (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview tasks without disk mutations",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON result",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            "-f",
            help="Overwrite existing files in target directory",
        ),
    ) -> None:
        """Fast autonomous bootstrap using smoke profile and maximized parallel concurrency."""
        _run_bootstrap_workflow(
            goal_input=goal,
            default_goal="Fast bootstrap project setup and configuration",
            workers=8,
            profile="smoke",
            template="default",
            target=target,
            dry_run=dry_run,
            json_output=json_output,
            force=force,
        )
