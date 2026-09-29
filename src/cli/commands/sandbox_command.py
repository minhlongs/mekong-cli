# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/sandbox_command.py — Secure Agent Sandboxed Execution CLI.

Executes untrusted shell commands and tool invocations within isolated
Docker/container environments or secure subprocess fallbacks.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.sandbox_bridge import SandboxConfig, get_sandbox_harness

console = Console()
sandbox_app = typer.Typer(name="sandbox", help="🛡️ Secure Sandboxed Agent Execution")


@sandbox_app.command(name="run")
def sandbox_run(
    command: str = typer.Argument(
        ...,
        help="Command to execute within the isolated sandbox",
    ),
    image: str = typer.Option(
        "python:3.11-slim",
        "--image",
        "-i",
        help="Container image for sandbox execution (default: python:3.11-slim)",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Execution timeout in seconds",
    ),
    memory: int = typer.Option(
        512,
        "--memory",
        "-m",
        help="Memory limit in megabytes",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON execution telemetry",
    ),
) -> None:
    """Run a shell command inside an isolated container or restricted fallback sandbox."""
    harness = get_sandbox_harness()
    cfg = SandboxConfig(
        image=image,
        timeout_seconds=timeout,
        memory_limit_mb=memory,
    )

    res = harness.execute(command, config=cfg)

    if json_output:
        print(json.dumps(res.to_dict(), indent=2))
        return

    color = "green" if res.exit_code == 0 else "red"
    console.print(
        Panel(
            f"[bold cyan]Command:[/bold cyan] {command}\n"
            f"[bold {color}]Exit Code:[/bold {color}] {res.exit_code}\n"
            f"[dim]Duration:[/dim] {res.duration_ms:.1f}ms | [dim]Backend:[/dim] {res.isolation_backend}\n"
            f"[dim]Container ID:[/dim] {res.container_id or 'N/A'}\n"
            f"[dim]Timed Out:[/dim] {res.timed_out}",
            title="Sandbox Execution Result",
            border_style=color,
        )
    )

    if res.stdout:
        console.print("[bold]Standard Output:[/bold]")
        console.print(f"[dim]{res.stdout.strip()}[/dim]")
    if res.stderr:
        console.print("[bold red]Standard Error:[/bold red]")
        console.print(f"[red]{res.stderr.strip()}[/red]")


@sandbox_app.command(name="status")
def sandbox_status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON sandbox status",
    ),
) -> None:
    """Check container runtime availability and sandboxed execution telemetry."""
    harness = get_sandbox_harness()
    status = harness.get_status()

    if json_output:
        print(json.dumps(status.to_dict(), indent=2))
        return

    table = Table(title="Mekong Agent Sandbox Status", box=ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold")
    table.add_row(
        "Container Daemon",
        "[green]AVAILABLE[/green]" if status.is_docker_available else "[yellow]FALLBACK (Restricted Process)[/yellow]",
    )
    table.add_row("Active Sandboxes", str(status.active_sandboxes))
    table.add_row("Total Executions", str(status.total_executions))
    table.add_row("Failed Executions", str(status.total_failures))
    table.add_row("Default Image", status.default_image)
    console.print(table)


def register_sandbox_command(app: typer.Typer) -> None:
    """Register 'sandbox' sub-app on root Typer application."""
    app.add_typer(sandbox_app, name="sandbox", help="🛡️ Secure Sandboxed Agent Execution")
