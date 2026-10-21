# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Execution and verification commands for goal command group."""

from __future__ import annotations

import typer
from rich.panel import Panel

from src.cli.goal_commands.helpers import (
    _goal_result_payload, _mod, _print_json, _t, _validate_profile, console, goal_app,
)
from src.mekongcli.core.goal_engine import GoalStatus


@goal_app.command(name="create")
def goal_create(
    title: str = typer.Argument(..., help="Mission objective"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Create and persist a goal with a decomposed role-aware task graph."""
    goal = _mod()._engine(db_path).create_goal(title)
    payload = {"id": goal.id, "title": goal.title, "status": goal.status.value}
    if json_output:
        _print_json(payload)
        return
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal.id}\n[bold]Status:[/bold] [cyan]{goal.status.value}[/cyan]\n[bold]Goal:[/bold] {goal.title}",
            title="Goal Created", border_style="green",
        )
    )


@goal_app.command(name="run")
def goal_run(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    profile: str = typer.Option("standard", "--profile", help="Verification profile: standard|smoke|none"),
    execute_commands: bool = typer.Option(False, "--execute-commands", help="Run task commands when present"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Run pending goal tasks, checkpoint progress, then verify."""
    _validate_profile(profile)
    engine = _mod()._engine(db_path)
    try:
        goal = engine.run_goal(goal_id, verification_profile=profile, execute_commands=execute_commands)
    except KeyError:
        console.print(f'[bold red]{_t(lang, "goal.not_found", "Goal not found:")}[/bold red] {goal_id}')
        raise typer.Exit(code=1)
    except RuntimeError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1)

    payload = _goal_result_payload(engine, goal.id, goal.title, goal.status, profile)
    if json_output:
        _print_json(payload)
        if goal.status != GoalStatus.SATISFIED:
            raise typer.Exit(code=1)
        return
    style = "green" if goal.status == GoalStatus.SATISFIED else "yellow"
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal.id}\n[bold]Status:[/bold] [{style}]{goal.status.value}[/{style}]\n[bold]Verification Profile:[/bold] {profile}",
            title="Goal Run Complete", border_style=style,
        )
    )
    if goal.status != GoalStatus.SATISFIED:
        raise typer.Exit(code=1)


@goal_app.command(name="run-parallel")
def goal_run_parallel(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    profile: str = typer.Option("standard", "--profile", help="Verification profile: standard|smoke|none"),
    execute_commands: bool = typer.Option(False, "--execute-commands", help="Run task commands when present"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    max_workers: int = typer.Option(3, "--workers", help="Max parallel execution threads"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Run pending goal tasks in parallel, checkpoint progress, then verify."""
    _validate_profile(profile)
    engine = _mod()._engine(db_path)
    try:
        goal = engine.run_goal_parallel(
            goal_id, verification_profile=profile, execute_commands=execute_commands, max_workers=max_workers,
        )
    except KeyError:
        console.print(f'[bold red]{_t(lang, "goal.not_found", "Goal not found:")}[/bold red] {goal_id}')
        raise typer.Exit(code=1)
    except RuntimeError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1)

    payload = _goal_result_payload(engine, goal.id, goal.title, goal.status, profile)
    if json_output:
        _print_json(payload)
        return
    style = "green" if goal.status == GoalStatus.SATISFIED else "yellow"
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal.id}\n[bold]Status:[/bold] [{style}]{goal.status.value}[/{style}]\n"
            f"[bold]Verification Profile:[/bold] {profile}\n[bold]Parallel Execution:[/bold] True (max_workers={max_workers})",
            title="Goal Run Parallel Complete", border_style=style,
        )
    )
    if goal.status != GoalStatus.SATISFIED:
        raise typer.Exit(code=1)


@goal_app.command(name="resume")
def goal_resume(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    profile: str = typer.Option("standard", "--profile", help="Verification profile: standard|smoke|none"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Resume a goal from persisted checkpoints."""
    _validate_profile(profile)
    engine = _mod()._engine(db_path)
    try:
        goal = engine.resume_goal(goal_id, verification_profile=profile)
    except KeyError:
        _nf = "Goal not found:"
        console.print(f'[bold red]{_t(lang, "goal.not_found", _nf)}[/bold red] {goal_id}')
        raise typer.Exit(code=1)
    except RuntimeError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1)

    payload = _goal_result_payload(engine, goal.id, goal.title, goal.status, profile)
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]{_t(lang, 'goal.resumed', 'Resumed')}[/green] {goal.id}: {goal.status.value}")
    if goal.status != GoalStatus.SATISFIED:
        raise typer.Exit(code=1)


@goal_app.command(name="verify")
def goal_verify(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    profile: str = typer.Option("standard", "--profile", help="Verification profile: standard|smoke|none"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Run verification gates and update goal satisfaction state."""
    _validate_profile(profile)
    engine = _mod()._engine(db_path)
    try:
        goal = engine.verify_goal(goal_id, verification_profile=profile)
    except KeyError:
        _nf = "Goal not found:"
        console.print(f'[bold red]{_t(lang, "goal.not_found", _nf)}[/bold red] {goal_id}')
        raise typer.Exit(code=1)

    payload = _goal_result_payload(engine, goal.id, goal.title, goal.status, profile)
    if json_output:
        _print_json(payload)
        return
    if goal.status != GoalStatus.SATISFIED:
        raise typer.Exit(code=1)
    style = "green" if goal.status == GoalStatus.SATISFIED else "red"
    console.print(f"[{style}]{goal.id}: {goal.status.value}[/{style}]")
    if goal.status != GoalStatus.SATISFIED:
        raise typer.Exit(code=1)
