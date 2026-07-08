"""Domain-agent CLI surface — ``mekong agent list`` and ``mekong agent run``.

Registered onto the root Typer app via :func:`register_agent_commands`.
Agents are sourced from :class:`src.core.agent_registry.AgentRegistry`
(auto-discovered from ``.claude/agents/*.md`` and any programmatic
registration site).
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.agent_registry import AgentMeta, get_registry

app = typer.Typer(
    name="agent",
    help="Manage and run domain agents (cto, cmo, coo, cfo, cso, planner, …)",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find(name: str) -> AgentMeta:
    """Look up *name* in the registry.

    Returns the matching :class:`AgentMeta` or raises ``typer.Exit(1)`` with
    a helpful message — never returns ``None``.
    """
    registry = get_registry()
    meta = registry.get_meta_obj(name)
    if meta is None:
        available = ", ".join(repr(n) for n in registry.list())
        console.print(f"[bold red]Unknown agent:[/bold red] {name!r}\nAvailable: {available}")
        raise typer.Exit(code=1)
    return meta


def _render_list(agents: list[AgentMeta]) -> None:
    if not agents:
        console.print("[yellow]No agents registered.[/yellow]")
        return

    table = Table(
        title=f"Registered agents ({len(agents)})",
        box=SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="bold", no_wrap=True, min_width=12)
    table.add_column("Description", style="dim")
    table.add_column("Tools", style="green", justify="right", width=14)

    for meta in agents:
        table.add_row(
            meta.name,
            meta.description,
            f"{len(meta.allowed_tools)} allowed" if meta.allowed_tools else "—",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("list")
def agent_list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show spawnable/delegate info"),
) -> None:
    """List all available domain agents with descriptions."""
    registry = get_registry()
    agents = registry.discover()

    if not verbose:
        _render_list(agents)
        return

    table = Table(
        title=f"Registered agents ({len(agents)})",
        box=SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="bold", no_wrap=True, min_width=12)
    table.add_column("Description", style="dim", min_width=30)
    table.add_column("Allowed Tools", style="green")
    table.add_column("Delegates To", style="yellow")

    for meta in agents:
        table.add_row(
            meta.name,
            meta.description,
            ", ".join(meta.allowed_tools) if meta.allowed_tools else "—",
            ", ".join(meta.spawnable_agents) if meta.spawnable_agents else "—",
        )

    console.print(table)


@app.command("run")
def agent_run(
    name: str = typer.Argument(..., help="Registered agent name (cto, cmo, coo, cfo, planner, …)"),
    task: str = typer.Argument(..., help="Task description to execute"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON result"),
) -> None:
    """Spawn an agent with *task* and emit a structured result.

    Result schema::

        {"success": true|false, "agent": "<name>", "task": "<truncated>",
         "output": "<agent output or empty>", "error": "<error or empty>"}
    """
    meta = _find(name)
    if not json_output:
        console.print(
            Panel(meta.description, title=f"[bold]{meta.name}[/bold]", border_style="cyan")
        )
        console.print(f"[dim]Task:[/dim] {task}\n")

    try:
        agent_cls = meta.cls
        agent = agent_cls(name=name)
        results = agent.run(task)
    except Exception as exc:  # noqa: BLE001
        payload = {"success": False, "agent": name, "task": task, "output": "", "error": str(exc)}
        if json_output:
            console.print_json(data=payload)
        else:
            console.print(f"[bold red]Execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1)

    output_chunks: list[str] = []
    success = True
    for result in results:
        if not result.success:
            success = False
            if result.error:
                output_chunks.append(f"ERROR: {result.error}")
        else:
            if result.output:
                output_chunks.append(str(result.output))

    final_output = "\n".join(output_chunks)
    if not success and not final_output:
        final_output = "Agent reported failure with no message."

    payload = {
        "success": success,
        "agent": name,
        "task": task,
        "output": final_output,
        "error": "" if success else (results[-1].error if results and results[-1].error else "Unknown failure"),
    }

    if json_output:
        # Emit pure JSON on a single line so CliRunner/scripts can parse it.
        console.print_json(data=payload)
    else:
        status_line = (
            "[bold green]✓ Success[/bold green]" if success else "[bold red]✗ Failed[/bold red]"
        )
        console.print(f"Status: {status_line}")
        if final_output:
            console.print(
                Panel(final_output, title="Output", border_style="green" if success else "red")
            )

    if not success:
        raise typer.Exit(code=1)


@app.command("info")
def agent_info(
    name: str = typer.Argument(..., help="Registered agent name"),
) -> None:
    """Show detailed info for a single agent."""
    meta = _find(name)

    console.print(Panel(meta.description, title=f"[bold]{meta.name}[/bold]", border_style="cyan"))

    if meta.allowed_tools or meta.spawnable_agents:
        details = Table(box=SIMPLE_HEAVY, show_header=False)
        details.add_column("Key", style="bold cyan", no_wrap=True)
        details.add_column("Value", style="dim")
        if meta.allowed_tools:
            details.add_row("Allowed tools", ", ".join(meta.allowed_tools))
        if meta.spawnable_agents:
            details.add_row("Delegates to", ", ".join(meta.spawnable_agents))
        console.print(details)


# ---------------------------------------------------------------------------
# Registration helper (called from app_setup)
# ---------------------------------------------------------------------------


def register_agent_commands(app: typer.Typer) -> None:
    """Add the ``agent`` sub-app to *app*."""
    app.add_typer(
        app,
        name="agent",
        help="Domain agent management (list | run | info)",
    )


__all__ = ["app", "register_agent_commands"]
