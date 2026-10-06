# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AGY (Agent Governance YAML & Antigravity CLI) Command Surface.

Provides CLI workflows for the deep-configured Antigravity stack:
- /agy status: inspect environment, binary paths, macro count
- /agy list:   list available workflows and registered macros
- /agy show:   inspect workflow specification
- /agy plan:   synthesize multi-agent AGY execution plan
- /agy walk:   architecture walkthrough
- /agy new:    scaffold new AGY workflow specification
- /agy bin:    verify binary paths and execution permissions
- /agy chat:   run prompt via AGY print-mode runner
- /agy sync:   reconcile AGY configuration files and macros
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.agy_engine import AGYEngine

agy_app = typer.Typer(
    name="agy",
    help="AGY — Agent Governance YAML & Antigravity CLI Operations",
    no_args_is_help=False,
)
app = agy_app
console = Console()


@agy_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """AGY stack operations and Antigravity CLI management."""
    if ctx.invoked_subcommand is None:
        status(json_output=json_output)


@agy_app.command("status")
def status(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Inspect AGY environment, binary paths, configs, and registered macros."""
    engine = AGYEngine()
    data = engine.get_status()

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            "[bold cyan]AGY — AGENT GOVERNANCE YAML & ANTIGRAVITY STACK[/bold cyan]\n"
            f"[bold green]System Status: {data['status']}[/bold green] | "
            f"Skills: [cyan]{data['metrics']['local_skills_count']}[/cyan] | "
            f"Macros: [yellow]{data['metrics']['slash_macros_count']}[/yellow]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )

    table = Table(title="Binaries & Runtime Shims", box=box.ROUNDED)
    table.add_column("Binary", style="bold cyan")
    table.add_column("Path", style="white")
    table.add_column("Status", style="green")
    table.add_column("Role", style="yellow")

    for name, info in data["binaries"].items():
        status_text = "[green]INSTALLED[/green]" if info["installed"] else "[dim red]NOT FOUND[/dim red]"
        path_text = info["path"] or "None"
        table.add_row(name, path_text, status_text, info["description"])

    console.print(table)


@agy_app.command("list")
def list_workflows(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category or keyword"),
    layer: Optional[str] = typer.Option(None, "--layer", "-l", help="Filter by layer: ceo, product, engineering, ops, business"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum entries to list"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """List available AGY workflow specifications, skills, and macro bindings."""
    engine = AGYEngine()
    workflows = engine.list_workflows(category=category, layer=layer, limit=limit)

    if json_output:
        typer.echo(json.dumps(workflows, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"AGY Workflows & Macro Bindings ({len(workflows)} entries)", box=box.ROUNDED)
    table.add_column("Name", style="bold cyan")
    table.add_column("Layer", style="magenta")
    table.add_column("Macro", style="green")
    table.add_column("Description", style="white")

    for wf in workflows:
        table.add_row(wf["name"], wf["layer"], wf["macro"], wf["description"][:60])

    console.print(table)


@agy_app.command("show")
def show(
    name: str = typer.Argument(..., help="Workflow or skill name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Retrieve detailed AGY specification for a named workflow or skill."""
    engine = AGYEngine()
    data = engine.show_workflow(name)

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if not data.get("ok"):
        console.print(f"[bold red]Error:[/bold red] {data.get('error')}")
        raise typer.Exit(code=1)

    console.print(
        Panel.fit(
            f"[bold cyan]Workflow:[/bold cyan] [bold white]{data['name']}[/bold white]\n"
            f"[bold magenta]Macro:[/bold magenta] {data['macro_binding']} | {data['short_macro']}\n"
            f"[bold yellow]Governance Gate:[/bold yellow] {data['governance_gate']}\n"
            f"[dim]Path: {data['file_path']}[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(data.get("content", ""))


@agy_app.command("plan")
def plan(
    goal: str = typer.Argument(..., help="Goal or objective description"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Synthesize an AGY multi-agent plan for a given goal."""
    engine = AGYEngine()
    plan_data = engine.plan_workflow(goal)

    if json_output:
        typer.echo(json.dumps(plan_data, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold cyan]AGY Multi-Agent Plan: {plan_data['plan_id']}[/bold cyan]\n"
            f"Goal: [bold white]{plan_data['goal']}[/bold white]\n"
            f"Tasks: [yellow]{plan_data['tasks_count']}[/yellow] | "
            f"Budget: [green]{plan_data['estimated_total_tokens']:,} tokens[/green]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )

    table = Table(box=box.ROUNDED)
    table.add_column("Step", style="bold cyan")
    table.add_column("Layer / Role", style="magenta")
    table.add_column("Action", style="white")
    table.add_column("Macro", style="green")
    table.add_column("Gate", style="yellow")

    for t in plan_data["tasks"]:
        table.add_row(
            str(t["step"]),
            f"{t['layer']} ({t['role']})",
            t["action"],
            t["macro"],
            t["gate"],
        )

    console.print(table)


@agy_app.command("walk")
def walk(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display structural architecture walkthrough of the AGY integration."""
    engine = AGYEngine()
    data = engine.get_walkthrough()

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold cyan]{data['title']}[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )

    table = Table(title="Stack Components", box=box.ROUNDED)
    table.add_column("Component", style="bold cyan")
    table.add_column("Path / Binary", style="yellow")
    table.add_column("Purpose", style="white")

    for c in data["components"]:
        path_val = c.get("binary") or c.get("path") or ", ".join(c.get("paths", []))
        table.add_row(c["name"], path_val, c["description"])

    console.print(table)

    console.print("\n[bold green]Macro Patterns:[/bold green]")
    for p in data["macro_patterns"]:
        console.print(f"  • {p}")

    console.print("\n[bold yellow]Slash Commands:[/bold yellow]")
    for cmd in data["slash_commands"]:
        console.print(f"  • {cmd}")


@agy_app.command("new")
def new(
    name: str = typer.Argument(..., help="Workflow or skill name to scaffold"),
    layer: str = typer.Option("engineering", "--layer", "-l", help="Target layer: ceo, product, engineering, ops, business"),
    desc: str = typer.Option("", "--desc", "-d", help="Workflow description"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Scaffold a new AGY workflow specification template."""
    engine = AGYEngine()
    data = engine.scaffold_spec(name=name, layer=layer, description=desc)

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold green]Scaffolded AGY Specification: {data['name']}[/bold green]\n"
            f"Layer: [magenta]{data['layer']}[/magenta] | Macro: [cyan]{data['macro']}[/cyan]",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    console.print(data["yaml_spec"])


@agy_app.command("bin")
def bin_info(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Inspect binary paths, version info, and execute permissions."""
    engine = AGYEngine()
    data = engine.get_binary_info()

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    table = Table(title="AGY Binary Execution Matrix", box=box.ROUNDED)
    table.add_column("Binary", style="bold cyan")
    table.add_column("Path", style="white")
    table.add_column("Exists", style="yellow")
    table.add_column("Executable", style="green")

    for name, info in data["binaries"].items():
        exists_str = "✓" if info["exists"] else "✗"
        exec_str = "✓" if info.get("executable") else "✗"
        table.add_row(name, info["path"], exists_str, exec_str)

    console.print(table)


@agy_app.command("chat")
def chat(
    prompt: str = typer.Argument(..., help="Prompt to execute via AGY"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model ID"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Execute a prompt via AGY print-mode runner or simulated response."""
    engine = AGYEngine()
    res = engine.execute_chat(prompt=prompt, model=model)

    if json_output:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel(res.get("response", ""), title=f"AGY Response ({res.get('mode')})", border_style="cyan"))


@agy_app.command("sync")
def sync(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Reconcile AGY configuration files, macros, and plugin mappings."""
    engine = AGYEngine()
    res = engine.sync_integration()

    if json_output:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold green]✔ Synchronized AGY integration![/bold green] Registered [cyan]{res['macros_registered']}[/cyan] macros at {res['macro_file']}")
