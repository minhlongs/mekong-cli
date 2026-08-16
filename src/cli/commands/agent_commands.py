# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain-agent CLI surface — ``mekong agent list``, ``run``, ``info``, ``create``, ``init``.

Registered onto the root Typer app via :func:`register_agent_commands`.
Agents are sourced from :class:`src.core.agent_registry.AgentRegistry`
(auto-discovered from ``.claude/agents/*.md`` and any programmatic
registration site).
"""

from __future__ import annotations

import typer
from pathlib import Path
from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.agent_registry import AgentMeta, get_registry

app = typer.Typer(
    name="agent",
    help="Manage and run domain agents (cto, cmo, coo, cfo, cso, planner, ...)",
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
            f"{len(meta.allowed_tools)} allowed" if meta.allowed_tools else "...",
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
            ", ".join(meta.allowed_tools) if meta.allowed_tools else "...",
            ", ".join(meta.spawnable_agents) if meta.spawnable_agents else "...",
        )

    console.print(table)


@app.command("run")
def agent_run(
    name: str = typer.Argument(..., help="Registered agent name (cto, cmo, coo, cfo, planner, ...)"),
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
        "error": ""
        if success
        else (results[-1].error if results and results[-1].error else "Unknown failure"),
    }

    if json_output:
        # Emit pure JSON on a single line so CliRunner/scripts can parse it.
        console.print_json(data=payload)
    else:
        status_line = (
            "[bold green]Success[/bold green]" if success else "[bold red]Failed[/bold red]"
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
# Agent template for `create`
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Agent create — scaffold .claude/agents/<name>.md
# ---------------------------------------------------------------------------


def _write_agent_file(
    name: str,
    description: str,
    agents_dir: Path,
    *,
    dry_run: bool = False,
) -> str | None:
    """Write the agent markdown file. Returns rendered content when *dry_run*."""
    target = agents_dir / f"{name}.md"
    if target.exists():
        console.print(
            f"[bold red]Agent '{name}' already exists at {target}\n"
            f"Agent '{name}' đã tồn tại tại {target}[/bold red]"
        )
        raise typer.Exit(code=1)

    content = _AGENT_TEMPLATE.format(
        name=name,
        name_title=name.replace("-", " ").title(),
        description=description,
    )

    if dry_run:
        return content

    target.write_text(content, encoding="utf-8")
    return None


@app.command("create")
def agent_create(
    name: str = typer.Argument(..., help="Agent name (kebab-case, e.g. 'content-writer')"),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Short description of what this agent does",
    ),
    role: str = typer.Option(
        "general",
        "--role",
        "-r",
        help="Agent role hint: general | code | marketing | analysis",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview file content without writing"),
) -> None:
    """Scaffold a new agent definition at .claude/agents/<name>.md.

    VN: Tao agent definition file tu template.
    """
    if not name or not name.replace("-", "").replace("_", "").isalnum():
        console.print("[bold red]Invalid name [/bold red][bold]Tên không hợp lệ.[/bold]")
        console.print("Use kebab-case letters and digits only, e.g. 'my-agent'")
        raise typer.Exit(code=1)

    role_hints = {
        "code": "Engineering agent — code review, refactoring, debugging.",
        "marketing": "Marketing agent — copy, SEO, campaigns, brand positioning.",
        "analysis": "Analysis agent — research, data interpretation, insights.",
        "general": "General-purpose agent for Mekong CLI.",
    }
    final_desc = description or role_hints.get(role, role_hints["general"])

    mekong_root = Path(__file__).resolve().parents[4]
    agents_dir = mekong_root / ".claude" / "agents"
    if not agents_dir.is_dir():
        console.print(f"[bold red]Agents directory not found: {agents_dir}[/bold red]")
        raise typer.Exit(code=1)

    result = _write_agent_file(name, final_desc, agents_dir, dry_run=dry_run)
    if result is not None:
        # dry_run: render preview and exit
        console.print(
            Panel(result, title=f"[bold]Preview: {name}.md[/bold]", border_style="yellow")
        )
        return

    console.print(
        f"[bold cyan]{name}[/bold cyan] — [dim].claude/agents/{name}.md[/dim]\n"
        f"Đã tạo agent / Agent scaffolded from template."
    )


# ---------------------------------------------------------------------------
# Agent init — bootstrap agent project
# ---------------------------------------------------------------------------


@app.command("init")
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
    """Bootstrap an agent project directory from a template.

    VN: Khoi tao thu muc project agent.
    """
    target_dir = directory or Path.cwd()
    if not target_dir.is_dir():
        console.print(f"[bold red]Directory not found: {target_dir}[/bold red]")
        raise typer.Exit(code=1)

    agent_md = target_dir / "agent.md"
    if agent_md.exists():
        console.print(f"[bold yellow]agent.md already exists at {agent_md}[/bold yellow]")
        if not typer.confirm("Overwrite existing agent.md? / Ghi de agent.md?"):
            raise typer.Exit(code=0)

    content = _AGENT_TEMPLATE.format(
        name="my-agent",
        name_title="My Agent",
        description="(customize this description)",
    )
    agent_md.write_text(content, encoding="utf-8")

    console.print(
        f"[bold cyan]{agent_md}[/bold cyan]\n"
        f"Đã khởi tạo agent project. / Agent project initialized.\n"
        f"Edit file này to customize. / Edit this file to customize."
    )


# ---------------------------------------------------------------------------
# Registration helper (called from app_setup)
# ---------------------------------------------------------------------------



# --------------------------------------------------------------------------- #
# Assemble — NLU + PEV + Memory + Factory pipeline (B6)                    #
# ---------------------------------------------------------------------------

@app.command("assemble")
def agent_assemble(
    goal: str = typer.Argument(..., help="User goal / intent string"),
    model: str = typer.Option(None, "--model", help="Override engine model"),
    temperature: float = typer.Option(None, "--temperature", help="Override temperature 0-1"),
    memory_limit: int = typer.Option(5, "--memory-limit", help="Max memory entries to surface"),
    json: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Assemble a configured agent from a user goal (B6 Agent Factory).

    Pipeline: NLU classify -> PEV engine params -> Memory Bridge recall -> Factory instantiate.

    Examples:
        mekong agent assemble "deploy my-app to production"
        mekong agent assemble "fix the billing bug" --model claude-opus-4-8
        mekong agent assemble "audit security" --json
    """
    try:
        from src.harness.agents.assembly import AssemblyConfig, assemble_agent
    except ImportError as exc:
        console.print("[bold red]Assembly module unavailable: " + str(exc) + "[/bold red]")
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
        console.print_json(data=payload)
        return

    role_str = str(result.role)
    agent_id_str = str(result.agent_id)
    intent_str = str(result.intent)
    inst_type = type(result.instance).__name__
    tools_str = ", ".join(result.tools) if result.tools else "\u2014"
    panel_content = (
        "[bold]" + role_str + "[/bold] ([cyan]" + agent_id_str + "[/cyan])\n"
        + "Intent: [yellow]" + intent_str + "[/yellow] | "
        + "Type: [green]" + inst_type + "[/green]\n"
        + "Tools: " + tools_str
    )
    console.print(
        Panel(
            panel_content,
            title="[bold]Assembled Agent[/bold]",
            border_style="cyan",
        )
    )
    if result.engine_params:
        ep = result.engine_params
        console.print(
            "[dim]Model:[/dim] " + str(ep.model) + "  "
            + "[dim]Temp:[/dim] " + str(ep.temperature) + "  "
            + "[dim]Tokens:[/dim] " + str(ep.max_tokens)
        )
    if result.memory_context:
        mem_count = str(len(result.memory_context))
        console.print("\n[dim]Memory: " + mem_count + " relevant entry(ies) surfaced[/dim]")
    console.print(
        "\n[bold green]Ready.[/bold green] Run: mekong agent run "
        + agent_id_str + " \"<task>\""
    )

def register_agent_commands(root: typer.Typer) -> None:
    """Add the ``agent`` sub-app to the root Typer app."""
    root.add_typer(
        app,
        name="agent",
        help="Domain agent management (list | run | info | create | init | assemble)",
    )


__all__ = ["app", "register_agent_commands"]
