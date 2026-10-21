# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Validation and workflow orchestration for Autonomous Parallel Project Bootstrap."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
import typer

from src.cli.commands.bootstrap_views import (
    _format_json_payload,
    render_bootstrap_rich_output,
)
from src.core.bootstrap_parallel_engine import execute_bootstrap_parallel

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


def _fail_validation(
    err_msg: str, actual_goal: str, target_dir: Path, profile: str,
    template: str, workers: int, dry_run: bool, json_output: bool,
) -> None:
    """Emit validation error in JSON or Rich format and exit with code 1."""
    if json_output:
        print(json.dumps({
            "ok": False, "status": "failed", "goal": actual_goal,
            "target_path": str(target_dir.resolve()), "profile": profile,
            "template": template, "workers": workers, "dry_run": dry_run, "error": err_msg,
        }, indent=2))
        raise typer.Exit(code=1)
    console.print(f"[bold red]Validation Error:[/bold red] {err_msg}")
    raise typer.Exit(code=1)


def _run_bootstrap_workflow(
    goal_input: Optional[List[str] | str], default_goal: str, workers: int, profile: str,
    template: str, target: Optional[Path], dry_run: bool, json_output: bool, force: bool,
) -> None:
    """Execute the bootstrap pipeline with validation, error handling, and formatting."""
    actual_goal = _normalize_goal(goal_input, default_goal)
    target_dir = target if target is not None else Path.cwd()

    if workers < 1 or workers > 32:
        _fail_validation(f"Invalid worker count {workers}. Workers must be between 1 and 32.", actual_goal, target_dir, profile, template, workers, dry_run, json_output)

    norm_profile = "smoke" if profile.lower() == "minimal" else profile.lower()
    if norm_profile not in VALID_PROFILES:
        _fail_validation(f"Unknown profile '{profile}'. Expected one of: {', '.join(sorted(VALID_PROFILES))}", actual_goal, target_dir, profile, template, workers, dry_run, json_output)

    norm_template = template.lower()
    if norm_template not in VALID_TEMPLATES:
        _fail_validation(f"Unknown template '{template}'. Expected one of: {', '.join(sorted(VALID_TEMPLATES))}", actual_goal, target_dir, norm_profile, template, workers, dry_run, json_output)

    if not json_output:
        mode_desc = "Dry Run (Zero Files Mutated)" if dry_run else "Live Execution (Atomic Checkpointing Enabled)"
        console.print(Panel(
            f"[bold]Goal:[/bold]        {actual_goal}\n[bold]Target:[/bold]      {target_dir.resolve()}\n"
            f"[bold]Profile:[/bold]     {norm_profile} | [bold]Template:[/bold] {norm_template}\n"
            f"[bold]Concurrency:[/bold] {workers} workers (ThreadPoolExecutor DAG)\n[bold]Mode:[/bold]        {mode_desc}",
            title="⚡ [bold cyan]Mekong Autonomous Parallel Bootstrap Engine[/bold cyan]",
            border_style="yellow" if dry_run else "cyan",
        ))
        with console.status(f"[bold cyan]Executing topological DAG tasks across {workers} workers...[/bold cyan]"):
            try:
                result = execute_bootstrap_parallel(
                    goal=actual_goal, target_path=target_dir, workers=workers,
                    profile=norm_profile, template=norm_template, dry_run=dry_run, force=force,
                )
            except Exception as exc:
                console.print(f"[bold red]Bootstrap Execution Error:[/bold red] {exc}")
                raise typer.Exit(code=1)
    else:
        try:
            result = execute_bootstrap_parallel(
                goal=actual_goal, target_path=target_dir, workers=workers,
                profile=norm_profile, template=norm_template, dry_run=dry_run, force=force,
            )
        except Exception as exc:
            _fail_validation(str(exc), actual_goal, target_dir, norm_profile, norm_template, workers, dry_run, json_output=True)

    if json_output:
        print(json.dumps(_format_json_payload(result, actual_goal, target_dir), indent=2))
        if not result.ok or result.rolled_back:
            raise typer.Exit(code=1)
        return

    render_bootstrap_rich_output(result, actual_goal, target_dir, workers, dry_run)
