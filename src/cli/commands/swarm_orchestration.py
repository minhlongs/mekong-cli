"""``mekong swarm <goal>`` — C1 Agent Orchestration CLI command.

Delegates a high-level goal to a SupervisorAgent that:
  - Decomposes into role-assigned sub-tasks
  - Delegates each sub-task to a specialised agent via AgentFactory
  - Auto-retries failed children via C3 ExponentialBackoff
  - Aggregates + ranks results

Registered onto the root Typer app in app_setup.py via
``register_swarm_commands(root)``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.harness.orchestration import SupervisorAgent, SupervisorConfig, run_swarm

console = Console()
swarm_app = typer.Typer(
    name="swarm",
    help="C1 Agent Orchestration: supervisor + multi-agent delegation",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


# ── Shared options ───────────────────────────────────────────────────────────


def _default_db() -> str:
    return os.environ.get(
        "MEKONG_GOAL_DB",
        os.path.join(os.getcwd(), ".mekong", "goals.db"),
    )


# ── Commands ─────────────────────────────────────────────────────────────────


@swarm_app.command(name="run")
def swarm_run(
    goal: str = typer.Argument(..., help="High-level goal to delegate"),
    max_retries: int = typer.Option(3, "--retries", "-r", help="Max retries per child"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Run children in parallel"),
    max_workers: int = typer.Option(3, "--workers", "-w", help="Max parallel threads"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit JSON result"),
    db_path: Optional[str] = typer.Option(None, "--db", help="Goal database path"),
) -> None:
    """Run a goal through the C1 supervisor swarm.

    Examples::

        mekong swarm "build a REST API for inventory management"
        mekong swarm "audit security and fix vulnerabilities" --retries 5 --json
        mekong swarm "create a marketing campaign and write blog posts" --parallel
    """
    try:
        swarm_result = run_swarm(
            goal,
            max_retries=max_retries,
            parallel=parallel,
            max_workers=max_workers,
        )
    except Exception as exc:
        console.print(f"[bold red]Swarm execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if json_output:
        payload = {
            "goal": swarm_result.goal,
            "supervisor_id": swarm_result.supervisor_id,
            "overall_success": swarm_result.overall_success,
            "succeeded": swarm_result.succeeded_count,
            "failed": swarm_result.failed_count,
            "total": len(swarm_result.child_results),
            "ranked_outputs": swarm_result.ranked_outputs,
        }
        console.print_json(data=payload)
        if not swarm_result.overall_success:
            raise typer.Exit(code=1)
        return

    _render_swarm_result(swarm_result)
    if not swarm_result.overall_success:
        raise typer.Exit(code=1)


@swarm_app.command(name="supervise")
def swarm_supervise(
    goal: str = typer.Argument(..., help="Goal for the supervisor"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show supervisor plan (decomposition) without executing."""
    try:
        from src.harness.orchestration import SupervisorAgent, SupervisorConfig
    except ImportError as exc:
        console.print(f"[bold red]Orchestration module unavailable:[/bold red] {exc}")
        raise typer.Exit(code=1)

    sup = SupervisorAgent(name=f"preview-{id(goal) & 0xFFFF:04x}")
    children = sup._decompose(goal)

    if json_output:
        payload = {
            "goal": goal,
            "supervisor": sup.name,
            "children": [
                {
                    "id": c.id,
                    "agent_id": c.agent_id,
                    "description": c.description,
                }
                for c in children
            ],
        }
        console.print_json(data=payload)
        return

    table = Table(title=f"Supervisor Plan — {goal[:60]}")
    table.add_column("Child ID", style="cyan", no_wrap=True)
    table.add_column("Agent", style="bold", no_wrap=True)
    table.add_column("Description", style="dim")

    for c in children:
        table.add_row(c.id, c.agent_id, c.description)

    console.print(table)
    console.print(f"\n[dim]{len(children)} child task(s) — run with: mekong swarm run \"{goal}\"[/dim]")


# ── Rendering helpers ────────────────────────────────────────────────────────


def _render_swarm_result(swarm) -> None:
    style = "green" if swarm.overall_success else "red"
    summary_line = (
        f"[bold]{swarm.succeeded_count}/{len(swarm.child_results)}[/bold] "
        f"child tasks succeeded"
    )
    console.print(
        Panel(
            f"[bold]Goal:[/bold] {swarm.goal}\n"
            f"[bold]Supervisor:[/bold] {swarm.supervisor_id}\n"
            f"[bold]Result:[/bold] [{style}]{summary_line}[/{style}]",
            title="Swarm Run Complete",
            border_style=style,
        )
    )

    if not swarm.ranked_outputs:
        return

    table = Table(title="Child Task Results (ranked)")
    table.add_column("Rank", style="cyan", no_wrap=True, width=5)
    table.add_column("Agent", style="bold", no_wrap=True, width=12)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Output", style="dim")

    for i, entry in enumerate(swarm.ranked_outputs, start=1):
        status = "[green]ok[/green]" if entry["success"] else "[red]FAIL[/red]"
        output_preview = _truncate(entry.get("output") or entry.get("error", ""), 80)
        table.add_row(f"#{i}", entry["agent_id"], status, output_preview)

    console.print(table)


def _truncate(text: str, max_len: int) -> str:
    """Truncate *text* to *max_len* characters, appending '…' if trimmed."""
    if not text:
        return ""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


# ── Registration ─────────────────────────────────────────────────────────────


def register_swarm_commands(root: typer.Typer) -> None:
    """Add C1 swarm orchestration sub-commands under ``mekong swarm``.

    Replaces the previous distributed-swarm-only sub-commands with the
    supervisor pattern (goal → delegate → aggregate → retry).
    """
    root.add_typer(
        swarm_app,
        name="swarm",
        help="C1 Agent Orchestration: supervisor + multi-agent delegation",
    )


__all__ = ["swarm_app", "register_swarm_commands"]
