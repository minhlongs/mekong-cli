# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Agent Factory assembly command: `mekong agent assemble`."""

from __future__ import annotations

import typer
from rich.panel import Panel


def agent_assemble(
    goal: str = typer.Argument(..., help="User goal / intent string"),
    model: str = typer.Option(None, "--model", help="Override engine model"),
    temperature: float = typer.Option(
        None, "--temperature", help="Override temperature 0-1"
    ),
    memory_limit: int = typer.Option(
        5, "--memory-limit", help="Max memory entries to surface"
    ),
    json: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Assemble a configured agent from a user goal (B6 Agent Factory)."""
    import src.cli.commands.agent_commands as _mod

    try:
        from src.harness.agents.assembly import AssemblyConfig, assemble_agent
    except ImportError as exc:
        _mod.console.print(
            "[bold red]Assembly module unavailable: " + str(exc) + "[/bold red]"
        )
        raise typer.Exit(code=1)

    cfg = AssemblyConfig(
        memory_limit=memory_limit,
        model_override=model,
        temperature_override=temperature,
    )
    result = assemble_agent(goal, config=cfg)

    if json:
        payload = {
            "agent_id": result.agent_id,
            "role": result.role,
            "intent": result.intent,
            "tools": result.tools,
            "instance_type": type(result.instance).__name__,
            "memory_entries": len(result.memory_context),
            "assembly_trace": result.assembly_trace,
        }
        if result.engine_params:
            ep = result.engine_params
            payload["engine_params"] = {
                "model": ep.model,
                "temperature": ep.temperature,
                "max_tokens": ep.max_tokens,
                "timeout_s": ep.timeout_s,
            }
        _mod.console.print_json(data=payload)
        return

    role_str = str(result.role)
    agent_id_str = str(result.agent_id)
    intent_str = str(result.intent)
    inst_type = type(result.instance).__name__
    tools_str = ", ".join(result.tools) if result.tools else "—"
    panel_content = (
        "[bold]"
        + role_str
        + "[/bold] ([cyan]"
        + agent_id_str
        + "[/cyan])\n"
        + "Intent: [yellow]"
        + intent_str
        + "[/yellow] | "
        + "Type: [green]"
        + inst_type
        + "[/green]\n"
        + "Tools: "
        + tools_str
    )
    _mod.console.print(
        Panel(
            panel_content,
            title="[bold]Assembled Agent[/bold]",
            border_style="cyan",
        )
    )
    if result.engine_params:
        ep = result.engine_params
        _mod.console.print(
            "[dim]Model:[/dim] "
            + str(ep.model)
            + "  "
            + "[dim]Temp:[/dim] "
            + str(ep.temperature)
            + "  "
            + "[dim]Tokens:[/dim] "
            + str(ep.max_tokens)
        )
    if result.memory_context:
        mem_count = str(len(result.memory_context))
        _mod.console.print(
            "\n[dim]Memory: " + mem_count + " relevant entry(ies) surfaced[/dim]"
        )
    _mod.console.print(
        "\n[bold green]Ready.[/bold green] Run: mekong agent run "
        + agent_id_str
        + ' "<task>"'
    )
