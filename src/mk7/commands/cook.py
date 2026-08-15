"""Mekong CLI 7 — cook command (PEV pipeline)."""

from __future__ import annotations

import json

import typer
from rich.console import Console

from ..core.agents import run_agent
from ..core.llm import LLMClient
from ..core.pev import Goal, Step, plan_goal, save_goal

console = Console()


def cook_cmd(
    task: str = typer.Argument(..., help="Task/goal to cook"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan only, no execution"),
    auto: bool = typer.Option(False, "--auto", help="Autonomous: no confirmation between steps"),
) -> None:
    """Cook: Plan -> Execute -> Verify workflow."""
    client = LLMClient()
    goal = Goal(title=task)
    console.print(f"[bold]Plan:[/] {task}")
    goal.steps = plan_goal(task, client)
    goal.status = "planned"
    save_goal(goal)

    console.print(f"[bold]Steps ({len(goal.steps)}):[/]")
    for i, s in enumerate(goal.steps, 1):
        console.print(f"  {i}. {s.name} — {s.task[:80]}")

    if dry_run:
        console.print("[yellow]Dry-run: plan only, not executing.[/]")
        raise typer.Exit(0)

    for i, step in enumerate(goal.steps, 1):
        console.print(f"\n[bold cyan]==> Step {i}/{len(goal.steps)}: {step.name}[/]")
        if not auto:
            if not typer.confirm("Execute this step?", default=True):
                step.status = "failed"
                step.error = "skipped by user"
                save_goal(goal)
                raise typer.Exit(2)
        step.status = "running"
        save_goal(goal)
        try:
            result = run_agent("eng", step.task, client, max_tokens=8192, execute_tools=True)
            step.status = "done"
            step.result = result[:2000]
            console.print(result[:1200])
        except Exception as e:
            step.status = "failed"
            step.error = str(e)[:500]
            save_goal(goal)
            console.print(f"[bold red]Step failed: {e}[/]")
            raise typer.Exit(1)
        save_goal(goal)

    goal.status = "done"
    save_goal(goal)
    console.print(f"\n[bold green]✔ Cook complete — checkpoint: {goal.slug}[/]")
