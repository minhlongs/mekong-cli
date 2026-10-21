# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Inspection and lifecycle management commands for goal command group."""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from src.cli.goal_commands.helpers import (
    _mod,
    _print_json,
    _t,
    console,
    goal_app,
)


@goal_app.command(name="status")
def goal_status(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Show full persisted goal state, including tasks, gates, events, and memory."""
    try:
        snapshot = _mod()._engine(db_path).status(goal_id)
    except KeyError:
        _nf = "Goal not found:"
        console.print(f'[bold red]{_t(lang, "goal.not_found", _nf)}[/bold red] {goal_id}')
        raise typer.Exit(code=1)
    if json_output:
        _print_json(snapshot)
        return

    goal = snapshot["goal"]
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal['id']}\n"
            f"[bold]Status:[/bold] {goal['status']}\n"
            f"[bold]Title:[/bold] {goal['title']}",
            title="Goal Status",
            border_style="cyan",
        )
    )
    table = Table(title="Tasks")
    table.add_column("Role", style="cyan")
    table.add_column("Status")
    table.add_column("Title")
    for task in snapshot["tasks"]:
        table.add_row(task["role"], task["status"], task["title"])
    console.print(table)

    criteria = snapshot.get("criteria") or []
    if criteria:
        ct = Table(title="Criteria")
        ct.add_column("Satisfied", style="green")
        ct.add_column("Description")
        for c in criteria:
            mark = "[green]✓" if c.get("satisfied") else "[red]✗"
            ct.add_row(mark, c.get("description", ""))
        console.print(ct)

    verification = snapshot.get("verification") or {}
    if verification:
        vp = verification.get("passed")
        vstyle = "green" if vp else "red"
        vtext = "passed" if vp else "failed"
        console.print(f"[bold]Verification:[/bold] [{vstyle}]{vtext}[/{vstyle}] (profile={verification.get('profile', '?')})")

    checkpoints = snapshot.get("checkpoints") or []
    if checkpoints:
        cpt = Table(title="Checkpoints")
        cpt.add_column("Label", style="cyan")
        cpt.add_column("Time")
        for cp in checkpoints:
            cpt.add_row(cp.get("label", ""), str(cp.get("created_at", "")))
        console.print(cpt)

    events = snapshot.get("events") or []
    if events:
        et = Table(title="Events")
        et.add_column("Event", style="cyan")
        et.add_column("Time")
        for ev in events:
            et.add_row(ev.get("event_name", ""), str(ev.get("created_at", "")))
        console.print(et)

    memory = snapshot.get("memory") or []
    if memory:
        mt = Table(title="Memory")
        mt.add_column("Kind", style="cyan")
        mt.add_column("Content")
        for m in memory:
            mt.add_row(m.get("kind", ""), m.get("content", ""))
        console.print(mt)


@goal_app.command(name="list")
def goal_list(
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """List persisted goals."""
    goals = _mod()._engine(db_path).list_goals()
    payload = [{"id": goal.id, "title": goal.title, "status": goal.status.value} for goal in goals]
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"Goals ({len(goals)})")
    table.add_column("ID", style="cyan")
    table.add_column("Status")
    table.add_column("Title")
    for goal in goals:
        table.add_row(goal.id, goal.status.value, goal.title)
    console.print(table)


@goal_app.command(name="cancel")
def goal_cancel(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Cancel a goal and prevent future execution."""
    try:
        goal = _mod()._engine(db_path).cancel_goal(goal_id)
    except KeyError:
        _nf = "Goal not found:"
        console.print(f'[bold red]{_t(lang, "goal.not_found", _nf)}[/bold red] {goal_id}')
        raise typer.Exit(code=1)
    if json_output:
        _print_json({"id": goal.id, "status": goal.status.value, "title": goal.title})
        return
    console.print(f"[yellow]{_t(lang, 'goal.cancelled', 'Cancelled')}[/yellow] {goal.id}")
