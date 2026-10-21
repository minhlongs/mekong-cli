# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dry-run preview rendering for cook-auto."""

from __future__ import annotations

from typing import Any

from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from src.core.pev_swarm_bridge import PevPhase

console = Console()


def _get_role_layer(role: str) -> str:
    r = (role or "").lower().replace("_", "-")
    if r in ("ceo", "sun-tzu", "kongming"):
        return "Strategy"
    if r in (
        "cto",
        "eng",
        "fullstack-developer",
        "debugger",
        "tester",
        "code-reviewer",
        "code-simplifier",
        "git-manager",
        "docs-manager",
    ):
        return "Engineering"
    if r in (
        "pm",
        "planner",
        "project-manager",
        "researcher",
        "ui-ux-designer",
        "brainstormer",
    ):
        return "Product"
    if r in ("ae", "cfo", "cmo", "cso"):
        return "Business"
    if r in ("ops", "coo", "journal-writer"):
        return "Operations"
    return "Engineering"


def _render_cook_auto_dry_run(
    plan: Any,
    goal_title: str,
    profile: str,
    max_cycles: int,
    checkpoint_id: str | None,
) -> None:
    """Render comprehensive PEV plan preview using Rich tree and tables."""
    console.print(
        Panel(
            f"[bold]Goal:[/bold] {goal_title}\n"
            f"[bold]Verification Profile:[/bold] {profile} | "
            f"[bold]Max Cycles:[/bold] {max_cycles} | "
            f"[bold]Checkpoint Resumption:[/bold] {checkpoint_id or 'None'}\n"
            f"[bold]Total Context Ceiling:[/bold] 40,000 tokens | "
            f"[bold]Engine:[/bold] PEV Swarm Orchestrator",
            title="[bold yellow]Cook Auto Preview (Dry Run)[/bold yellow]",
            border_style="yellow",
        )
    )

    root_tree = Tree(f"[bold cyan]🎯 Goal:[/bold cyan] {goal_title}")
    phases_map = {
        PevPhase.PLAN: ("📋 Phase 1: Plan", "yellow"),
        PevPhase.EXECUTE: ("⚡ Phase 2: Execute", "cyan"),
        PevPhase.VERIFY: ("🔍 Phase 3: Verify", "green"),
    }
    for phase_enum, (phase_title, phase_color) in phases_map.items():
        phase_tasks = [t for t in plan.tasks if t.phase == phase_enum]
        if phase_tasks:
            phase_node = root_tree.add(
                f"[bold {phase_color}]{phase_title}[/bold {phase_color}] [dim](PENDING)[/dim]"
            )
            for t in phase_tasks:
                agent_node = phase_node.add(
                    f"[bold green]🤖 Agent:[/bold green] [cyan]{t.role}[/cyan] "
                    f"[dim](Budget: {t.context_budget:,} tokens)[/dim]"
                )
                agent_node.add(f"[bold]Task:[/bold] {t.title}")
                agent_node.add(f"[dim]Tools: {', '.join(t.allowed_tools)}[/dim]")

    console.print("\n[bold]PEV Swarm Delegation Hierarchy:[/bold]")
    console.print(root_tree)

    table = Table(
        title="Subagent Context Budgets & Guardrails",
        box=SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Subagent Role", style="bold", width=20)
    table.add_column("Layer", style="dim", width=14)
    table.add_column("Model Tier", style="cyan", width=12)
    table.add_column("Context Budget", justify="right", width=16)
    table.add_column("Tool Allowlist", style="dim")
    table.add_column("CEO Override", justify="center", width=14)

    seen_roles: set[str] = set()
    for t in plan.tasks:
        if t.role in seen_roles:
            continue
        seen_roles.add(t.role)
        layer = _get_role_layer(t.role)
        tier = "pro" if t.role in ("ceo", "sun-tzu", "cto") else "flash"
        tools_str = ", ".join(t.allowed_tools)
        override_str = (
            "[green]YES[/green]" if t.role in ("ceo", "sun-tzu") else "[dim]Gate Req.[/dim]"
        )
        table.add_row(t.role, layer, tier, f"{t.context_budget:,} tokens", tools_str, override_str)

    console.print("\n")
    console.print(table)

    gates_table = Table(
        title="Verification Gates & Acceptance Rubrics",
        box=SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    gates_table.add_column("Gate Name", style="bold", width=28)
    gates_table.add_column("Target Command / Rubric", style="dim")
    gates_table.add_column("Profile", width=10)
    gates_table.add_column("Gate Type", justify="center", width=14)

    for t in plan.tasks:
        vc = t.verification_criteria
        if vc.test_command:
            gates_table.add_row(
                f"{t.title[:26]}", vc.test_command, profile, "[bold red]BLOCKING[/bold red]"
            )
        if vc.rubric_prompt:
            gates_table.add_row(
                f"Rubric: {t.role}", vc.rubric_prompt, profile, "[bold yellow]EVALUATED[/bold yellow]"
            )

    gates_table.add_row(
        "Core Boundary Check", "pytest tests/test_core_boundary.py", profile, "[bold red]BLOCKING[/bold red]"
    )
    gates_table.add_row(
        "Antigravity Health", "python3 scripts/antigravity_healthcheck.py", profile, "[bold red]BLOCKING[/bold red]"
    )

    console.print("\n")
    console.print(gates_table)
    console.print("\n[dim]Dry-run complete. No processes executed, no files modified.[/dim]")
    console.print(
        f"[yellow]To execute for real:[/yellow] mekong cook-auto \"{goal_title}\" --profile {profile}\n"
    )
