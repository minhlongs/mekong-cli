# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/ship_command.py — Autonomous Production Shipping CLI.

Coordinates the canonical shipping pipeline:
Pre-flight check -> Linting -> Testing -> Staging -> Commit synthesis -> Remote push.
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

from src.core.shipping_engine import (
    ShipPhase,
    ShippingEngine,
    ShippingReport,
    get_shipping_engine,
)

console = Console()


def register_ship_command(app: typer.Typer) -> None:
    """Register the 'ship' command onto the main Typer application."""

    @app.command(name="ship")
    def ship_cmd(
        message: Optional[str] = typer.Argument(
            None,
            help="Optional commit message description (e.g. 'fix payment webhook timeout')",
        ),
        lint: bool = typer.Option(
            True,
            "--lint/--no-lint",
            help="Run project linters before committing",
        ),
        test: bool = typer.Option(
            True,
            "--test/--no-test",
            help="Run automated test suite before committing",
        ),
        push: bool = typer.Option(
            True,
            "--push/--no-push",
            help="Push committed branch to remote upstream",
        ),
        preflight_only: bool = typer.Option(
            False,
            "--preflight-only",
            help="Execute only repository pre-flight inspection",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Simulate validation, commit message generation, and push without mutating git",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON report",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="Print detailed test and linter outputs",
        ),
    ) -> None:
        """🚀 Ship code to production — lint, test, commit, push, deploy."""
        engine = get_shipping_engine()

        if preflight_only:
            pre = engine.preflight_check()
            if json_output:
                print(json.dumps(pre, indent=2))
                return
            if not pre.get("ok"):
                console.print(f"[bold red]Preflight check failed:[/bold red] {pre.get('error')}")
                raise typer.Exit(code=1)

            console.print(
                Panel(
                    f"[bold cyan]Branch:[/bold cyan]        {pre.get('branch')}\n"
                    f"[dim]Remote:[/dim]        {pre.get('remote_url')}\n"
                    f"[dim]Dirty Files:[/dim]   {pre.get('dirty_count')} uncommitted\n"
                    f"[dim]Upstream:[/dim]      Ahead {pre.get('ahead', 0)} / Behind {pre.get('behind', 0)}",
                    title="🚀 Ship Pre-Flight Check",
                    border_style="cyan",
                    box=ROUNDED,
                )
            )
            return

        if not json_output:
            console.print(
                Panel(
                    f"[bold cyan]🚀 Production Shipping Pipeline[/bold cyan]\n"
                    f"[dim]Linters:[/dim]  {'enabled' if lint else 'disabled'}  |  "
                    f"[dim]Tests:[/dim]  {'enabled' if test else 'disabled'}  |  "
                    f"[dim]Push:[/dim]  {'enabled' if push else 'disabled'}"
                    + (" [yellow](DRY RUN)[/yellow]" if dry_run else ""),
                    title="Mekong Ship",
                    border_style="yellow" if dry_run else "cyan",
                    box=ROUNDED,
                )
            )

        report = engine.ship(
            message=message,
            run_lint=lint,
            run_tests=test,
            push=push,
            dry_run=dry_run,
        )

        if json_output:
            print(json.dumps(report.to_dict(), indent=2))
            if not report.ok:
                raise typer.Exit(code=1)
            return

        # Console rendering
        if report.validations:
            table = Table(title="Validation Steps", box=ROUNDED)
            table.add_column("Validator", style="cyan")
            table.add_column("Command", style="dim")
            table.add_column("Status")
            table.add_column("Duration", justify="right")

            for v in report.validations:
                if v.skipped:
                    status = "[yellow]SKIPPED[/yellow]"
                elif v.passed:
                    status = "[green]PASSED[/green]"
                else:
                    status = "[red]FAILED[/red]"
                table.add_row(v.name, " ".join(v.command), status, f"{v.duration_ms:.1f}ms")

            console.print(table)

            if verbose:
                for v in report.validations:
                    if v.output and not v.skipped:
                        console.print(Panel(v.output, title=f"Output: {v.name}", box=ROUNDED, style="dim"))

        if not report.ok:
            console.print(f"[bold red]✗ Shipping pipeline failed during {report.phase.value}:[/bold red] {report.error}")
            raise typer.Exit(code=1)

        border = "yellow" if dry_run else "green"
        prefix_title = "[yellow][DRY RUN][/yellow] " if dry_run else ""
        console.print(
            Panel(
                f"[bold green]✓ Successfully Shipped![/bold green]\n"
                f"[dim]Branch:[/dim]   [bold cyan]{report.branch}[/bold cyan]\n"
                f"[dim]Commit:[/dim]   {report.commit_sha[:10]} — {report.commit_message}\n"
                f"[dim]Pushed:[/dim]   {'Yes -> ' + report.remote_url if report.pushed else 'No (skipped or local)'}\n"
                f"[dim]Staged:[/dim]   {len(report.files_staged)} files\n"
                f"[dim]Time:[/dim]     {report.duration_ms:.1f}ms",
                title=f"{prefix_title}Ship Complete",
                border_style=border,
                box=ROUNDED,
            )
        )
