"""Mekong namespace — mk agent / skill / subagent dispatcher.

Avoids confusion with external namespaces:
- /ak:  → Antigravity
- /ck:  → Claudekit
- /mk:  → Mekong-native agents + skills
"""
from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

app = typer.Typer(
    name="mk",
    help="Mekong namespace — agents, skills, subagents",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

_AGENTS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "agents"
_SKILLS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "skills"


def _list_agents() -> list[str]:
    if not _AGENTS_DIR.is_dir():
        return []
    return sorted(p.stem for p in _AGENTS_DIR.glob("*.md") if p.is_file())


def _list_skills() -> list[str]:
    if not _SKILLS_DIR.is_dir():
        return []
    return sorted(p.name for p in _SKILLS_DIR.iterdir() if p.is_dir())


@app.command(name="agent")
def agent_list() -> None:
    """List available Mekong agents."""
    agents = _list_agents()
    if not agents:
        console.print("[yellow]No agents found in .claude/agents/[/]")
        return
    table = Table(title="Mekong Agents")
    table.add_column("Name", style="cyan", no_wrap=True)
    for name in agents:
        table.add_row(name)
    console.print(table)


@app.command(name="skill")
def skill_list() -> None:
    """List available Mekong skills."""
    skills = _list_skills()
    if not skills:
        console.print("[yellow]No skills found in .claude/skills/[/]")
        return
    table = Table(title="Mekong Skills")
    table.add_column("Name", style="green")
    for name in skills:
        table.add_row(name)


@app.command(name="subagent")
def subagent_launch(
    name: str = typer.Argument(..., help="Subagent name to launch"),
) -> None:
    """Launch a Mekong subagent by name."""
    agents = _list_agents()
    if name not in agents:
        console.print(f"[red]Subagent '{name}' not found.[/]")
        console.print(f"[dim]Available: {', '.join(agents)[:120]}[/]")
        raise typer.Exit(code=1)
    console.print(f"[green]Launching subagent[/] [cyan]{name}[/]...")
    console.print(
        f"[yellow]Note:[/] Subagent execution is handled by the runtime.\n"
        f"Agent file: .claude/agents/{name}.md"
    )
