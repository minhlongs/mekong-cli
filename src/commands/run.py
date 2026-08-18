# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Run command — wire MekongCoreRuntimeImpl with real dependencies.

Usage:
    mekong run --goal "Analyze monthly revenue"
    mekong run --goal "Deploy production build"
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer()
console = Console()


def _build_runtime():
    """Build MekongCoreRuntimeImpl with real dependencies from core modules."""
    from src.core.runtime_adapter import MekongCoreRuntimeImpl
    from src.core.adapters.memory_store_adapter import MemoryStoreBridge
    from src.core.billing_adapter import BillingAdapter
    from src.core.tool_registry import ToolRegistry

    memory = MemoryStoreBridge()
    billing = BillingAdapter()
    tool_registry = ToolRegistry()
    telemetry = _NullTelemetry()
    dispatcher = _NullDispatcher()

    return MekongCoreRuntimeImpl(
        dispatcher=dispatcher,
        tool_registry=tool_registry,
        memory_store=memory,
        billing=billing,
        telemetry=telemetry,
        agent_id="cli",
    )


class _NullDispatcher:
    """Minimal dispatcher stub — runtime falls back gracefully when no dispatch()."""

    def dispatch(self, task):  # noqa: ANN001, ANN202
        raise NotImplementedError("No dispatcher configured")


class _NullTelemetry:
    """Minimal telemetry stub — runtime skips record_event via hasattr check."""

    def record_event(self, _name: str, **_kwargs: object) -> None:
        pass


@app.command(name="run")
def run_command(
    goal: str = typer.Option(..., "--goal", "-g", help="Goal description for the runtime"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output"),
) -> None:
    """Run the MekongCoreRuntime with a goal string."""
    try:
        runtime = _build_runtime()
    except Exception as exc:
        console.print(f"[red]Failed to initialize runtime:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        result = asyncio.run(runtime.run(goal))
    except Exception as exc:
        console.print(f"[red]Runtime error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if result.error:
        console.print(
            Panel(
                f"[bold red]Goal failed:[/bold red] {goal}\n[red]Error:[/red] {result.error}",
                title="Run Result",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    output = result.output if result.output is not None else "(no output)"
    if verbose:
        console.print(
            Panel(
                f"[bold]Goal:[/bold] {goal}\n[bold]Task:[/bold] {result.task_id}\n[bold]Output:[/bold] {output}",
                title="Run Result",
                border_style="green",
            )
        )
    else:
        console.print(f"[green]OK[/green] — {output}")


def register_run_command(app: typer.Typer) -> None:
    """Register the run command onto the main typer app."""
    app.command(name="run")(run_command)
