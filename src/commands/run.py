# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Run command — wire MekongCoreRuntimeImpl with real dependencies.

Usage:
    mekong run --goal "Analyze monthly revenue"
    mekong run --goal "Deploy production build" --max-cost-usd 2.50

Autonomy gates are ON by default in this wiring:

- Observability: TelemetrySinkAdapter satisfies protocols.ObservabilitySink
  (emit/flush), so the runtime's observe()/commit() telemetry calls work.
- Governance: goals classified FORBIDDEN are always blocked; goals classified
  REVIEW_REQUIRED (e.g. "deploy production build") are blocked unless
  GOVERNANCE_AUTO_APPROVE=true|1|yes is set. There is no CLI bypass.
- Cost ceiling: defaults to $5.00 per mission; override with the
  MEKONG_MAX_COST_USD env var or the --max-cost-usd option (option wins).
- Mission tracing: a MissionTracer is attached via runtime.start_mission()
  before the loop runs, so steps and outcomes are correlated per mission.
"""

from __future__ import annotations

import os

import typer
from rich.console import Console
from rich.panel import Panel

from src.core.governance import Governance
from src.core.mission_tracer import MissionTracer
from src.core.telemetry_sink_adapter import TelemetrySinkAdapter

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


def _build_runtime(max_cost_usd: float | None = None):
    """Build MekongCoreRuntimeImpl with real dependencies from core modules.

    Governance is wired ON by default: forbidden goals are blocked and
    review-class goals require GOVERNANCE_AUTO_APPROVE=true|1|yes. The cost
    ceiling defaults to $5.00 per mission (override via MEKONG_MAX_COST_USD
    or the --max-cost-usd CLI option).
    """
    from src.core.runtime_adapter import MekongCoreRuntimeImpl
    from src.core.adapters.memory_store_adapter import MemoryStoreBridge
    from src.core.billing_adapter import BillingAdapter
    from src.core.tool_registry import ToolRegistry

    memory = MemoryStoreBridge()
    billing = BillingAdapter()
    tool_registry = ToolRegistry()
    telemetry = TelemetrySinkAdapter()
    governance = Governance()
    dispatcher = _NullDispatcher()

    return MekongCoreRuntimeImpl(
        dispatcher=dispatcher,
        tool_registry=tool_registry,
        memory_store=memory,
        billing=billing,
        telemetry=telemetry,
        governance=governance,
        max_cost_usd=_resolve_max_cost_usd(max_cost_usd),
        agent_id="cli",
    )


class _NullDispatcher:
    """Minimal dispatcher stub — runtime falls back gracefully when no dispatch()."""

    def dispatch(self, task, agent=None):  # noqa: ANN001, ANN202
        raise NotImplementedError("No dispatcher configured")


@app.command(name="run")
def run_command(
    goal: str = typer.Option(..., "--goal", "-g", help="Goal description for the runtime"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output"),
    max_cost_usd: float | None = typer.Option(
        None,
        "--max-cost-usd",
        help="Per-mission cost ceiling in USD (overrides MEKONG_MAX_COST_USD; default 5.0)",
    ),
) -> None:
    """Run the MekongCoreRuntime with a goal string.

    Review-class goals (e.g. deploy to production) are blocked unless
    GOVERNANCE_AUTO_APPROVE=true is set; forbidden goals are always blocked.
    """
    try:
        runtime = _build_runtime(max_cost_usd=max_cost_usd)
    except Exception as exc:
        console.print(f"[red]Failed to initialize runtime:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    tracer = MissionTracer()
    runtime.start_mission(goal, tracer=tracer)

    # MekongCoreRuntimeImpl.run() is synchronous (src/core/protocols.py);
    # wrapping it in asyncio.run() raises TypeError.
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
