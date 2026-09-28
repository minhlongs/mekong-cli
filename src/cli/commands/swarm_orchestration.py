# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

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

import difflib
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from src.core.pev_swarm_bridge import (
    PEVSwarmBridge,
    ROLE_CONTEXT_BUDGETS,
    ROLE_TOOL_ALLOWLISTS,
)
from src.core.subagent_dispatch import VALID_SUBAGENTS
from src.harness.orchestration import run_swarm

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
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        "-a",
        help="Comma-separated agent roles (e.g. cto,eng,tester)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview swarm delegation tree",
    ),
    max_retries: int = typer.Option(3, "--retries", "-r", help="Max retries per child"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Run children in parallel"),
    max_workers: int = typer.Option(3, "--workers", "-w", help="Max parallel threads"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit JSON result"),
    db_path: Optional[str] = typer.Option(None, "--db", help="Goal database path"),
) -> None:
    """Run a goal through the C1 supervisor swarm.

    Examples::

        mekong swarm run "build a REST API for inventory management"
        mekong swarm run "audit security and fix vulnerabilities" --dry-run
        mekong swarm run "build a REST API" --agents cto,eng,tester --dry-run
    """
    clean_goal = (goal or "").strip()
    if not clean_goal:
        err_msg = "Goal cannot be empty"
        if json_output:
            console.print_json(data={"ok": False, "error": err_msg, "code": "EMPTY_GOAL"})
        else:
            console.print(f"[bold red]Invalid goal:[/bold red] {err_msg}.")
        raise typer.Exit(code=1)

    parsed_agents: list[str] = []
    if agents:
        tokens = [a.strip() for a in agents.split(",") if a.strip()]
        for token in tokens:
            norm = token.lower().replace("_", "-")
            if norm not in VALID_SUBAGENTS:
                matches = difflib.get_close_matches(norm, VALID_SUBAGENTS, n=1, cutoff=0.4)
                suggestion = matches[0] if matches else None
                if json_output:
                    console.print_json(
                        data={
                            "ok": False,
                            "error": f"Unknown agent role '{token}'",
                            "did_you_mean": suggestion,
                            "available_roles": sorted(VALID_SUBAGENTS),
                            "code": "UNKNOWN_AGENT_ROLE",
                        }
                    )
                else:
                    msg = f"[bold red]Unknown agent role:[/bold red] '{token}'"
                    if suggestion:
                        msg += f" (Did you mean [bold yellow]'{suggestion}'[/bold yellow]?)"
                    console.print(msg)
                    console.print(
                        f"[dim]Available roles ({len(VALID_SUBAGENTS)}):[/dim] {', '.join(sorted(VALID_SUBAGENTS))}"
                    )
                raise typer.Exit(code=1)
            parsed_agents.append(norm)

    if dry_run:
        bridge = PEVSwarmBridge(db_path=db_path)
        plan = bridge.plan(clean_goal)

        if parsed_agents:
            active_roles = parsed_agents
        else:
            active_roles = [t.role for t in plan.tasks]

        supervisor_id = f"swarm-supervisor-{id(clean_goal) & 0xFFFF:04x}"

        preview_tasks = []
        if parsed_agents:
            for i, role in enumerate(parsed_agents, start=1):
                budget = ROLE_CONTEXT_BUDGETS.get(role, 20000)
                tools = ROLE_TOOL_ALLOWLISTS.get(role, ["Read", "Bash", "Task"])
                preview_tasks.append(
                    {
                        "task_id": f"task_{i:02d}",
                        "title": f"Delegated subtask for {role}",
                        "description": f"Execute mission segment for: {clean_goal}",
                        "role": role,
                        "phase": "execute",
                        "context_budget": budget,
                        "allowed_tools": tools,
                    }
                )
        else:
            for t in plan.tasks:
                preview_tasks.append(
                    {
                        "task_id": t.task_id,
                        "title": t.title,
                        "description": t.description,
                        "role": t.role,
                        "phase": t.phase.value,
                        "context_budget": t.context_budget,
                        "allowed_tools": t.allowed_tools,
                    }
                )

        if json_output:
            payload = {
                "ok": True,
                "dry_run": True,
                "goal": clean_goal,
                "supervisor_id": supervisor_id,
                "agents": active_roles,
                "retries": max_retries,
                "parallel": parallel,
                "max_workers": max_workers,
                "tasks": preview_tasks,
            }
            console.print_json(data=payload)
            return

        agents_summary = ", ".join(active_roles) if active_roles else "auto-routed"
        console.print(
            Panel(
                f"[bold]Goal:[/bold] {clean_goal}\n"
                f"[bold]Target Agents:[/bold] {agents_summary} | "
                f"[bold]Retries:[/bold] {max_retries} | "
                f"[bold]Parallel:[/bold] {parallel} | "
                f"[bold]Workers:[/bold] {max_workers}",
                title="[bold yellow]Swarm Run Preview (Dry Run)[/bold yellow]",
                border_style="yellow",
            )
        )

        root_tree = Tree(f"[bold cyan]🛡️  Supervisor:[/bold cyan] {supervisor_id}")
        root_tree.add(f"[bold]🎯 Goal:[/bold] {clean_goal}")
        for i, pt in enumerate(preview_tasks, start=1):
            role_to_show = pt["role"]
            budget = pt["context_budget"]
            tools = pt["allowed_tools"]
            phase_node = root_tree.add(f"[bold yellow]📌 Phase {i}: {pt['title']}[/bold yellow]")
            agent_node = phase_node.add(
                f"[bold green]🤖 {role_to_show.upper()} ({role_to_show})[/bold green] "
                f"[dim][Budget: {budget:,} tokens][/dim]"
            )
            agent_node.add(f"[dim]Task: {pt['description']}[/dim]")
            agent_node.add(f"[dim]Tools: {', '.join(tools)}[/dim]")

        console.print("\n[bold]Multi-Agent Swarm Delegation Tree:[/bold]")
        console.print(root_tree)
        console.print("\n[dim]Dry-run complete. Multi-agent delegation tree previewed successfully.[/dim]")
        console.print(f"[yellow]To execute for real:[/yellow] mekong swarm run \"{clean_goal}\"\n")
        return

    try:
        swarm_result = run_swarm(
            clean_goal,
            max_retries=max_retries,
            parallel=parallel,
            max_workers=max_workers,
        )
    except Exception as exc:
        if json_output:
            console.print_json(data={"ok": False, "error": str(exc), "code": "SWARM_ERROR"})
        else:
            console.print(f"[bold red]Swarm execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if json_output:
        payload = {
            "ok": swarm_result.overall_success,
            "goal": swarm_result.goal,
            "supervisor_id": swarm_result.supervisor_id,
            "agents": parsed_agents if parsed_agents else [e["agent_id"] for e in swarm_result.ranked_outputs],
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
        from src.harness.orchestration import SupervisorAgent
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
