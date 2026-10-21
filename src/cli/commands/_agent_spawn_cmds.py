# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Subagent dispatch command: `mekong agent spawn`."""

from __future__ import annotations

import difflib

import typer
from rich.box import SIMPLE_HEAVY
from rich.panel import Panel
from rich.table import Table


def agent_spawn(
    role: str = typer.Argument(
        ...,
        help="Subagent role ID (e.g. cto, sun-tzu, pm, cfo, debugger, ...)",
    ),
    task: str = typer.Option(
        ...,
        "--task",
        "-t",
        help="Task description or goal for the subagent to execute",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview generated agent execution prompt and environment without running",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit structured machine-readable JSON execution summary",
    ),
    model_tier: str | None = typer.Option(
        None,
        "--model-tier",
        "--model",
        "-m",
        help="Override model tier (pro, flash, inherit)",
    ),
) -> None:
    """Spawn an Antigravity domain subagent with role validation and context constraints."""
    import src.cli.commands.agent_commands as _mod
    from src.core.subagent_dispatch import VALID_SUBAGENTS, spawn

    result = spawn(
        role=role,
        task=task,
        dry_run=dry_run,
        json_output=json_output,
        model_tier=model_tier,
    )

    if not result.get("ok"):
        if json_output:
            _mod.console.print_json(data=result)
        else:
            norm_role = (role or "").strip().lower()
            matches = difflib.get_close_matches(
                norm_role, VALID_SUBAGENTS, n=3, cutoff=0.3
            )
            _mod.console.print(f"[bold red]Unknown agent role:[/bold red] {role!r}")
            if matches:
                _mod.console.print(
                    f"[yellow]Did you mean:[/yellow] {', '.join(repr(m) for m in matches)}?"
                )
            _mod.console.print(
                f"[dim]Available roles ({len(VALID_SUBAGENTS)}):[/dim] {', '.join(sorted(VALID_SUBAGENTS))}"
            )
        raise typer.Exit(code=1)

    if dry_run:
        if json_output:
            _mod.console.print_json(data=result)
            return

        name = result.get("name", role)
        role_id = result.get("role", role)
        description = result.get("description", "")
        functional_role = result.get("functional_role", "Specialized Agent")
        resolved_tier = result.get("model_tier", "inherit")
        context_budget = result.get("context_budget", 20000)
        allowed_tools = result.get("allowed_tools", [])
        can_override = result.get("can_override", False)
        def_path_str = result.get("definition_path", "")
        system_prompt = result.get("system_prompt", "")

        _mod.console.print(
            Panel(
                f"[bold cyan]{name}[/bold cyan] [dim]({role_id})[/dim]\n[dim]{description}[/dim]",
                title="[bold yellow]Agent Spawn Preview (Dry Run)[/bold yellow]",
                border_style="yellow",
            )
        )

        meta_table = Table(box=SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
        meta_table.add_column("Property", style="bold", width=18)
        meta_table.add_column("Configuration", style="dim")
        meta_table.add_row("Role ID", role_id)
        meta_table.add_row("Functional Layer", functional_role)
        meta_table.add_row(
            "Model Tier", f"{resolved_tier}{' (overridden)' if model_tier else ''}"
        )
        meta_table.add_row(
            "Context Budget", f"{context_budget:,} tokens (Ceiling: 40,000)"
        )
        meta_table.add_row(
            "Allowed Tools", ", ".join(allowed_tools) if allowed_tools else "None"
        )
        meta_table.add_row(
            "Override Authority",
            "[bold green]YES[/bold green]"
            if can_override
            else "[dim]NO (CEO Approval Gate)[/dim]",
        )
        meta_table.add_row("Definition File", def_path_str)
        _mod.console.print(meta_table)

        _mod.console.print(
            Panel(
                task,
                title="[bold yellow]Target Task[/bold yellow]",
                border_style="yellow",
            )
        )
        _mod.console.print(
            Panel(
                system_prompt,
                title=f"[bold green]Injected System Prompt ({role_id})[/bold green]",
                border_style="green",
            )
        )
        _mod.console.print(
            "[dim]Dry-run complete. No agent processes were spawned.[/dim]\n"
        )
        return

    if json_output:
        _mod.console.print_json(data=result)
    else:
        status_style = (
            "[bold green]SUCCESS[/bold green]"
            if result.get("status") == "success"
            else "[bold red]FAILED[/bold red]"
        )
        role_val = result.get("role", role)
        tier_val = result.get("model_tier", "inherit")
        time_val = result.get("elapsed_time", 0.0)
        artifacts_val = result.get("artifacts", [])
        _mod.console.print(
            Panel(
                f"Status: {status_style} | Role: [bold]{role_val}[/bold] | Model: [cyan]{tier_val}[/cyan] | Time: [yellow]{time_val}s[/yellow]\n"
                f"Artifacts: {', '.join(artifacts_val) if artifacts_val else 'None'}",
                title="[bold]Agent Execution Summary[/bold]",
                border_style="green" if result.get("status") == "success" else "red",
            )
        )
        output_text = result.get("output", "")
        if output_text:
            _mod.console.print(
                Panel(
                    output_text,
                    title="Output",
                    border_style="green"
                    if result.get("status") == "success"
                    else "red",
                )
            )

    if result.get("status") != "success":
        raise typer.Exit(code=1)
