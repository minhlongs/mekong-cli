# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Agent scaffolding commands: create and init."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel

_AGENT_TEMPLATE = """\
---
name: {name}
description: {description}
model: sonnet
memory: true
tools:
  - Read
  - Bash
  - Grep
  - Glob
---

## Role

You are the {name_title} agent.

## Responsibility

Define what this agent delivers.

## Guidelines

- Always reason step-by-step before producing output.
- Cite sources or file paths when referencing code or docs.
- Respect QUÂN DOANH read-only policy: never modify `mekong/`, `.claude/hooks/`, or
  `constitution/` without `/binh-phap win`.
## Output Format

Summarize findings; separate analysis from recommendations.
"""


def _write_agent_file(
    name: str,
    description: str,
    agents_dir: Path,
    *,
    dry_run: bool = False,
) -> str | None:
    """Write the agent markdown file. Returns rendered content when *dry_run*."""
    import src.cli.commands.agent_commands as _mod

    target = agents_dir / f"{name}.md"
    if target.exists():
        _mod.console.print(
            f"[bold red]Agent '{name}' already exists at {target}\n"
            f"Agent '{name}' đã tồn tại tại {target}[/bold red]"
        )
        raise typer.Exit(code=1)

    content = _mod._AGENT_TEMPLATE.format(
        name=name,
        name_title=name.replace("-", " ").title(),
        description=description,
    )

    if dry_run:
        return content

    target.write_text(content, encoding="utf-8")
    return None


def agent_create(
    name: str = typer.Argument(
        ..., help="Agent name (kebab-case, e.g. 'content-writer')"
    ),
    description: str = typer.Option(
        "", "--description", "-d", help="Short description of what this agent does"
    ),
    role: str = typer.Option(
        "general",
        "--role",
        "-r",
        help="Agent role hint: general | code | marketing | analysis",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview file content without writing"
    ),
) -> None:
    """Scaffold a new agent definition at .claude/agents/<name>.md."""
    import src.cli.commands.agent_commands as _mod

    if not name or not name.replace("-", "").replace("_", "").isalnum():
        _mod.console.print(
            "[bold red]Invalid name [/bold red][bold]Tên không hợp lệ.[/bold]"
        )
        _mod.console.print("Use kebab-case letters and digits only, e.g. 'my-agent'")
        raise typer.Exit(code=1)

    role_hints = {
        "code": "Engineering agent — code review, refactoring, debugging.",
        "marketing": "Marketing agent — copy, SEO, campaigns, brand positioning.",
        "analysis": "Analysis agent — research, data interpretation, insights.",
        "general": "General-purpose agent for Mekong CLI.",
    }
    final_desc = description or role_hints.get(role, role_hints["general"])

    mekong_root = Path(_mod.__file__).resolve().parents[4]
    agents_dir = mekong_root / ".claude" / "agents"
    if not agents_dir.is_dir():
        _mod.console.print(
            f"[bold red]Agents directory not found: {agents_dir}[/bold red]"
        )
        raise typer.Exit(code=1)

    result = _mod._write_agent_file(name, final_desc, agents_dir, dry_run=dry_run)
    if result is not None:
        _mod.console.print(
            Panel(
                result,
                title=f"[bold]Preview: {name}.md[/bold]",
                border_style="yellow",
            )
        )
        return

    _mod.console.print(
        f"[bold cyan]{name}[/bold cyan] — [dim].claude/agents/{name}.md[/dim]\n"
        f"Đã tạo agent / Agent scaffolded from template."
    )


def agent_init(
    directory: Path = typer.Option(
        None,
        "--dir",
        "-d",
        help="Target directory for agent scaffold (default: current dir)",
    ),
    template: str = typer.Option(
        "default",
        "--template",
        "-t",
        help="Scaffold template: default | minimal | full",
    ),
) -> None:
    """Bootstrap an agent project directory from a template."""
    import src.cli.commands.agent_commands as _mod

    target_dir = directory or Path.cwd()
    if not target_dir.is_dir():
        _mod.console.print(f"[bold red]Directory not found: {target_dir}[/bold red]")
        raise typer.Exit(code=1)

    agent_md = target_dir / "agent.md"
    if agent_md.exists():
        _mod.console.print(
            f"[bold yellow]agent.md already exists at {agent_md}[/bold yellow]"
        )
        if not typer.confirm("Overwrite existing agent.md? / Ghi de agent.md?"):
            raise typer.Exit(code=0)

    content = _mod._AGENT_TEMPLATE.format(
        name="my-agent",
        name_title="My Agent",
        description="(customize this description)",
    )
    agent_md.write_text(content, encoding="utf-8")

    _mod.console.print(
        f"[bold cyan]{agent_md}[/bold cyan]\n"
        f"Đã khởi tạo agent project. / Agent project initialized.\n"
        f"Edit file này to customize. / Edit this file to customize."
    )
