# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Core domain-agent commands: list, run, info."""

from __future__ import annotations

import typer
from rich.box import SIMPLE_HEAVY
from rich.panel import Panel
from rich.table import Table

from src.core.agent_registry import AgentMeta


def _find(name: str) -> AgentMeta:
    """Look up *name* in the registry or exit(1)."""
    import src.cli.commands.agent_commands as _mod

    registry = _mod.get_registry()
    meta = registry.get_meta_obj(name)
    if meta is None:
        available = ", ".join(repr(n) for n in registry.list())
        _mod.console.print(f"[bold red]Unknown agent:[/bold red] {name!r}\nAvailable: {available}")
        raise typer.Exit(code=1)
    return meta


def _render_list(agents: list[AgentMeta]) -> None:
    import src.cli.commands.agent_commands as _mod

    if not agents:
        _mod.console.print("[yellow]No agents registered.[/yellow]")
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
            f"{len(meta.allowed_tools)} allowed" if meta.allowed_tools else "...",
        )
    _mod.console.print(table)


def agent_list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show spawnable/delegate info"),
) -> None:
    """List all available domain agents with descriptions."""
    import src.cli.commands.agent_commands as _mod

    agents = _mod.get_registry().discover()
    if not verbose:
        _mod._render_list(agents)
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
            ", ".join(meta.allowed_tools) if meta.allowed_tools else "...",
            ", ".join(meta.spawnable_agents) if meta.spawnable_agents else "...",
        )
    _mod.console.print(table)


def agent_run(
    name: str = typer.Argument(..., help="Registered agent name (cto, cmo, coo, cfo, planner, ...)"),
    task: str = typer.Argument(..., help="Task description to execute"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON result"),
) -> None:
    """Spawn an agent with *task* and emit a structured result."""
    import src.cli.commands.agent_commands as _mod

    meta = _mod._find(name)
    if not json_output:
        _mod.console.print(Panel(meta.description, title=f"[bold]{meta.name}[/bold]", border_style="cyan"))
        _mod.console.print(f"[dim]Task:[/dim] {task}\n")

    try:
        agent = meta.cls(name=name)
        results = agent.run(task)
    except Exception as exc:  # noqa: BLE001
        payload = {"success": False, "agent": name, "task": task, "output": "", "error": str(exc)}
        if json_output:
            _mod.console.print_json(data=payload)
        else:
            _mod.console.print(f"[bold red]Execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1)

    output_chunks: list[str] = []
    success = True
    for result in results:
        if not result.success:
            success = False
        if result.error:
            output_chunks.append(f"ERROR: {result.error}")
        elif result.output:
            output_chunks.append(str(result.output))

    final_output = "\n".join(output_chunks) or ("" if success else "Agent reported failure with no message.")
    err_msg = "" if success else (results[-1].error if results and results[-1].error else "Unknown failure")
    payload = {"success": success, "agent": name, "task": task, "output": final_output, "error": err_msg}

    if json_output:
        _mod.console.print_json(data=payload)
    else:
        status_line = "[bold green]Success[/bold green]" if success else "[bold red]Failed[/bold red]"
        _mod.console.print(f"Status: {status_line}")
        if final_output:
            _mod.console.print(Panel(final_output, title="Output", border_style="green" if success else "red"))

    if not success:
        raise typer.Exit(code=1)


def agent_info(
    name: str = typer.Argument(..., help="Registered agent name"),
) -> None:
    """Show detailed info for a single agent."""
    import src.cli.commands.agent_commands as _mod

    meta = _mod._find(name)
    _mod.console.print(Panel(meta.description, title=f"[bold]{meta.name}[/bold]", border_style="cyan"))

    if meta.allowed_tools or meta.spawnable_agents:
        details = Table(box=SIMPLE_HEAVY, show_header=False)
        details.add_column("Key", style="bold cyan", no_wrap=True)
        details.add_column("Value", style="dim")
        if meta.allowed_tools:
            details.add_row("Allowed tools", ", ".join(meta.allowed_tools))
        if meta.spawnable_agents:
            details.add_row("Delegates to", ", ".join(meta.spawnable_agents))
        _mod.console.print(details)
