# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Parallel Project Bootstrap CLI Commands.

Exposes:
- `bootstrap-auto-parallel`: Primary command with configurable workers, profiles, templates.
- `bootstrap-auto`: Sequential or standard autonomous bootstrap companion alias.
- `bootstrap-auto-fast`: High-speed autonomous bootstrap with smoke profile and maximum parallelism.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from rich.console import Console
import typer

from src.cli.commands.bootstrap_views import _format_json_payload
from src.cli.commands.bootstrap_workflow import (
    VALID_PROFILES,
    VALID_TEMPLATES,
    _normalize_goal,
    _run_bootstrap_workflow,
)

console = Console()


def register_bootstrap_command(root: typer.Typer) -> None:
    """Attach bootstrap commands and companion aliases to the root Typer application."""

    @root.command(name="bootstrap-auto-parallel")
    def bootstrap_auto_parallel_cmd(
        goal: Optional[List[str]] = typer.Argument(
            None, help="High-level goal or description for the parallel bootstrap process",
        ),
        workers: int = typer.Option(
            4, "--workers", "-w", help="Number of concurrent worker threads (1-32, default: 4)",
        ),
        profile: str = typer.Option(
            "standard", "--profile", "-p", help="Scaffolding verification profile: smoke | standard | full (default: standard)",
        ),
        template: str = typer.Option(
            "default", "--template", "-t", help="Project template preset: default | vas | fintech | agent (default: default)",
        ),
        target: Optional[Path] = typer.Option(
            None, "--target", "--path", help="Target directory for project workspace (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Preview topological DAG and tasks without disk mutations",
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="Output machine-readable JSON result (ideal for headless CI/CD & MCP)",
        ),
        force: bool = typer.Option(
            False, "--force", "-f", help="Overwrite existing files in target directory",
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
            None, help="High-level goal for autonomous project bootstrap",
        ),
        profile: str = typer.Option(
            "standard", "--profile", "-p", help="Scaffolding verification profile: smoke | standard | full (default: standard)",
        ),
        template: str = typer.Option(
            "default", "--template", "-t", help="Project template preset: default | vas | fintech | agent (default: default)",
        ),
        target: Optional[Path] = typer.Option(
            None, "--target", "--path", help="Target directory for project workspace (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Preview tasks without disk mutations",
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="Output machine-readable JSON result",
        ),
        force: bool = typer.Option(
            False, "--force", "-f", help="Overwrite existing files in target directory",
        ),
        workers: int = typer.Option(
            4, "--workers", "-w", help="Number of concurrent worker threads (1-32, default: 4)",
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
            None, help="High-level goal for fast autonomous bootstrap",
        ),
        target: Optional[Path] = typer.Option(
            None, "--target", "--path", help="Target directory for project workspace (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Preview tasks without disk mutations",
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="Output machine-readable JSON result",
        ),
        force: bool = typer.Option(
            False, "--force", "-f", help="Overwrite existing files in target directory",
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


__all__ = [
    "VALID_PROFILES",
    "VALID_TEMPLATES",
    "_format_json_payload",
    "_normalize_goal",
    "_run_bootstrap_workflow",
    "console",
    "register_bootstrap_command",
]
