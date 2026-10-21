# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Run command — wire MekongCoreRuntimeImpl with real dependencies.

Usage:
    mekong run --goal "Analyze monthly revenue"
    mekong run --goal "Deploy production build" --max-cost-usd 2.50
"""

from __future__ import annotations

import logging
import os

import typer
from rich.console import Console
from rich.panel import Panel

from src.commands.run_dispatchers import _NullDispatcher, _RegistryDispatcher
from src.core.adapters.goal_engine_adapter import make_goal_engine_adapter
from src.core.capability import CapabilityBus, InMemoryCapabilityBus
from src.core.governance import Governance
from src.core.mission_tracer import MissionTracer
from src.core.telemetry_sink_adapter import TelemetrySinkAdapter

logger = logging.getLogger(__name__)

app = typer.Typer()
console = Console()

_DEFAULT_MAX_COST_USD = 5.0


def _resolve_max_cost_usd(cli_value: float | None) -> float:
    """Resolve the per-mission cost ceiling: CLI option > env var > default."""
    if cli_value is not None:
        return cli_value
    raw = os.getenv("MEKONG_MAX_COST_USD", "")
    if raw:
        try:
            return float(raw)
        except ValueError:
            console.print(
                f"[yellow]Invalid MEKONG_MAX_COST_USD={raw!r}; "
                f"falling back to ${_DEFAULT_MAX_COST_USD:.2f}[/yellow]"
            )
    return _DEFAULT_MAX_COST_USD


def _build_runtime(max_cost_usd: float | None = None, with_capabilities: bool = True):
    """Build MekongCoreRuntimeImpl with real dependencies from core modules."""
    from src.core.adapters.mcp_capability_adapter import MCPCapabilityAdapter
    from src.core.adapters.memory_store_adapter import MemoryStoreBridge
    from src.core.adapters.tool_capability_adapter import ToolCapabilityAdapter
    from src.core.billing_adapter import BillingAdapter
    from src.core.runtime_adapter import MekongCoreRuntimeImpl
    from src.core.tool_registry import ToolRegistry

    memory = MemoryStoreBridge()
    billing = BillingAdapter()
    tool_registry = ToolRegistry()
    telemetry = TelemetrySinkAdapter()
    governance = Governance()
    try:
        dispatcher = _RegistryDispatcher()
    except Exception as exc:
        logger.warning("Registry dispatcher init failed, falling back to null: %s", exc)
        dispatcher = _NullDispatcher()

    capability_bus: CapabilityBus | None = None
    if with_capabilities:
        try:
            capability_bus = InMemoryCapabilityBus()
            ToolCapabilityAdapter(tool_registry).sync_to_bus(capability_bus)
            try:
                MCPCapabilityAdapter(bus=capability_bus).sync_from_mcp()
            except Exception as exc:
                logger.warning("MCP capability sync failed, continuing without: %s", exc)
        except Exception as exc:
            logger.warning("Capability bus init failed, continuing without: %s", exc)
            capability_bus = None

    return MekongCoreRuntimeImpl(
        dispatcher=dispatcher,
        tool_registry=tool_registry,
        memory_store=memory,
        billing=billing,
        telemetry=telemetry,
        governance=governance,
        capability_bus=capability_bus,
        max_cost_usd=_resolve_max_cost_usd(max_cost_usd),
        agent_id="cli",
        goal_engine=make_goal_engine_adapter(),
    )


@app.command(name="run")
def run_command(
    goal: str = typer.Option(..., "--goal", "-g", help="Goal description for the runtime"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output"),
    max_cost_usd: float | None = typer.Option(
        None,
        "--max-cost-usd",
        help="Per-mission cost ceiling in USD (overrides MEKONG_MAX_COST_USD; default 5.0)",
    ),
    with_capabilities: bool = typer.Option(
        True,
        "--with-capabilities/--no-capabilities",
        help="Enable capability bus with builtin tools (default: ON). Failure-tolerant.",
    ),
) -> None:
    """Run the MekongCoreRuntime with a goal string."""
    try:
        runtime = _build_runtime(max_cost_usd=max_cost_usd, with_capabilities=with_capabilities)
    except Exception as exc:
        console.print(f"[red]Failed to initialize runtime:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    runtime.start_mission(goal, tracer=MissionTracer())

    try:
        result = runtime.run(goal)
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


__all__ = [
    "_DEFAULT_MAX_COST_USD",
    "_NullDispatcher",
    "_RegistryDispatcher",
    "_build_runtime",
    "_resolve_max_cost_usd",
    "app",
    "console",
    "register_run_command",
    "run_command",
]
