# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Goal command group for the autonomous engineering OS vertical slice."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.pev_swarm_bridge import PEVSwarmBridge
from src.mekongcli.core.goal_engine import GoalEngine, GoalStatus, SQLiteGoalStore
from src.mekongcli.core.verification import VerificationPipeline
from src.cli.i18n import get_messages as _goal_get_messages

goal_app = typer.Typer(help="Goal: persistent autonomous mission execution")
console = Console()


def _t(lang: str, key: str, default: str = "") -> str:
    return _goal_get_messages(lang).get(key) or default


def _engine(db_path: str | None = None) -> GoalEngine:
    store = SQLiteGoalStore(db_path) if db_path else SQLiteGoalStore()
    return GoalEngine(store=store, cwd=Path.cwd())


def _print_json(payload: dict[str, Any] | list[Any]) -> None:
    typer.echo(json.dumps(payload, indent=2, default=str))


def _validate_profile(profile: str) -> None:
    try:
        VerificationPipeline.validate_profile(profile)
    except ValueError as exc:
        raise typer.BadParameter(
            f"must be one of: {VerificationPipeline.profile_options()}",
            param_hint="--profile",
        ) from exc


def _goal_result_payload(
    engine: GoalEngine,
    goal_id: str,
    title: str,
    status: GoalStatus,
    profile: str,
) -> dict[str, Any]:
    verification = engine.status(goal_id)["verification"] or {}
    verification_results = verification.get("results") or []
    failed_gates = [
        result["name"]
        for result in verification_results
        if result.get("required") and not result.get("passed")
    ]
    return {
        "id": goal_id,
        "status": status.value,
        "title": title,
        "profile": profile,
        "verification_passed": verification.get("passed"),
        "failed_gates": failed_gates,
    }


@goal_app.command(name="create")
def goal_create(
    title: str = typer.Argument(..., help="Mission objective"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Create and persist a goal with a decomposed role-aware task graph."""
    goal = _engine(db_path).create_goal(title)
    payload = {"id": goal.id, "title": goal.title, "status": goal.status.value}
    if json_output:
        _print_json(payload)
        return
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal.id}\n"
            f"[bold]Status:[/bold] [cyan]{goal.status.value}[/cyan]\n"
            f"[bold]Goal:[/bold] {goal.title}",
            title="Goal Created",
            border_style="green",
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
    engine = _engine(db_path)
    try:
        goal = engine.run_goal(
            goal_id,
            verification_profile=profile,
            execute_commands=execute_commands,
        )
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
        if goal.status != GoalStatus.SATISFIED:
            raise typer.Exit(code=1)
        return
    style = "green" if goal.status == GoalStatus.SATISFIED else "yellow"
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal.id}\n"
            f"[bold]Status:[/bold] [{style}]{goal.status.value}[/{style}]\n"
            f"[bold]Verification Profile:[/bold] {profile}",
            title="Goal Run Complete",
            border_style=style,
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
    engine = _engine(db_path)
    try:
        goal = engine.run_goal_parallel(
            goal_id,
            verification_profile=profile,
            execute_commands=execute_commands,
            max_workers=max_workers,
        )
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
    style = "green" if goal.status == GoalStatus.SATISFIED else "yellow"
    console.print(
        Panel(
            f"[bold]ID:[/bold] {goal.id}\n"
            f"[bold]Status:[/bold] [{style}]{goal.status.value}[/{style}]\n"
            f"[bold]Verification Profile:[/bold] {profile}\n"
            f"[bold]Parallel Execution:[/bold] True (max_workers={max_workers})",
            title="Goal Run Parallel Complete",
            border_style=style,
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
    engine = _engine(db_path)
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
    engine = _engine(db_path)
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


@goal_app.command(name="status")
def goal_status(
    goal_id: str = typer.Argument(..., help="Goal ID"),
    db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Show full persisted goal state, including tasks, gates, events, and memory."""
    try:
        snapshot = _engine(db_path).status(goal_id)
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
    goals = _engine(db_path).list_goals()
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
        goal = _engine(db_path).cancel_goal(goal_id)
    except KeyError:
        _nf = "Goal not found:"
        console.print(f'[bold red]{_t(lang, "goal.not_found", _nf)}[/bold red] {goal_id}')
        raise typer.Exit(code=1)
    if json_output:
        _print_json({"id": goal.id, "status": goal.status.value, "title": goal.title})
        return
    console.print(f"[yellow]{_t(lang, 'goal.cancelled', 'Cancelled')}[/yellow] {goal.id}")


@goal_app.command(name="checkpoint")
def goal_checkpoint(
    goal_id: str = typer.Argument(..., help="Goal or mission ID to checkpoint"),
    label: str = typer.Option("manual", "--label", "-l", help="Checkpoint label"),
    files: str | None = typer.Option(None, "--files", "-f", help="Comma-separated files to snapshot"),
    db_path: str | None = typer.Option(None, "--db", help="Override database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Capture an atomic SQLite checkpoint of workspace files and task states."""
    engine = _engine(db_path)
    pev_db_path = Path(db_path) if db_path and "pev" in str(db_path) else None
    bridge = PEVSwarmBridge(db_path=pev_db_path)

    # Validate that goal_id exists
    goal_found = False
    try:
        engine.status(goal_id)
        goal_found = True
    except KeyError:
        pass

    if not goal_found:
        m_stat = bridge.get_mission_status(goal_id)
        if m_stat.get("ok"):
            goal_found = True

    if not goal_found:
        err_msg = f"Goal not found: '{goal_id}'"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "GOAL_NOT_FOUND", "goal_id": goal_id})
        else:
            console.print(Panel(f"[bold red]Goal not found:[/bold red] '{goal_id}'", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    file_list = [f.strip() for f in files.split(",") if f.strip()] if files else None

    try:
        cp_id = bridge.store.capture_checkpoint(
            mission_id=goal_id,
            label=label,
            files=file_list,
        )
        cp_rec = bridge.store.get_checkpoint(cp_id)
        file_count = len(cp_rec.file_snapshots) if cp_rec else 0

        # Also register in goal engine if available
        try:
            engine.store.add_checkpoint(goal_id, label)
        except Exception:
            pass

        payload = {
            "ok": True,
            "status": "captured",
            "checkpoint_id": cp_id,
            "goal_id": goal_id,
            "label": label,
            "file_count": file_count,
            "created_at": cp_rec.created_at if cp_rec else "",
        }
        if json_output:
            _print_json(payload)
            return

        console.print(
            Panel(
                f"[bold]Goal ID:[/bold] {goal_id}\n"
                f"[bold]Checkpoint ID:[/bold] [cyan]{cp_id}[/cyan]\n"
                f"[bold]Label:[/bold] {label}\n"
                f"[bold]Snapshotted Files:[/bold] {file_count}\n"
                f"[bold]Status:[/bold] [green]captured[/green]",
                title="Goal Checkpoint Captured",
                border_style="green",
            )
        )
    except Exception as exc:
        err_msg = f"Failed to capture checkpoint: {exc}"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "CHECKPOINT_FAILED"})
        else:
            console.print(Panel(f"[bold red]{err_msg}[/bold red]", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@goal_app.command(name="rollback")
def goal_rollback(
    goal_id: str = typer.Argument(..., help="Goal or mission ID"),
    checkpoint_id: str = typer.Argument(..., help="Checkpoint ID to restore"),
    no_restore_files: bool = typer.Option(False, "--no-restore-files", help="Do not revert workspace files"),
    db_path: str | None = typer.Option(None, "--db", help="Override database path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Emit machine-readable JSON"),
    lang: str = typer.Option("en", "--lang", help="Output language: en | vi."),
) -> None:
    """Atomically restore workspace files and task states to a specific checkpoint."""
    engine = _engine(db_path)
    pev_db_path = Path(db_path) if db_path and "pev" in str(db_path) else None
    bridge = PEVSwarmBridge(db_path=pev_db_path)

    # 1. Validate goal_id
    goal_found = False
    try:
        engine.status(goal_id)
        goal_found = True
    except KeyError:
        pass

    if not goal_found:
        m_stat = bridge.get_mission_status(goal_id)
        if m_stat.get("ok"):
            goal_found = True

    if not goal_found:
        err_msg = f"Goal not found: '{goal_id}'"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "GOAL_NOT_FOUND", "goal_id": goal_id})
        else:
            console.print(Panel(f"[bold red]Goal not found:[/bold red] '{goal_id}'", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    # 2. Validate checkpoint_id
    try:
        with bridge.store._connect() as conn:
            cp_row = conn.execute(
                "SELECT checkpoint_id, mission_id FROM checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,),
            ).fetchone()
    except Exception as exc:
        err_msg = f"Database error reading checkpoint: {exc}"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "DB_ERROR"})
        else:
            console.print(Panel(f"[bold red]{err_msg}[/bold red]", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    if not cp_row:
        err_msg = f"Checkpoint not found: '{checkpoint_id}'"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "CHECKPOINT_NOT_FOUND", "checkpoint_id": checkpoint_id})
        else:
            console.print(Panel(f"[bold red]Checkpoint not found:[/bold red] '{checkpoint_id}'", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    cp_rec = bridge.store.get_checkpoint(checkpoint_id)
    if not cp_rec:
        err_msg = f"Corrupted checkpoint state: '{checkpoint_id}'"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "CHECKPOINT_CORRUPTED", "checkpoint_id": checkpoint_id})
        else:
            console.print(Panel(f"[bold red]Corrupted checkpoint state:[/bold red] '{checkpoint_id}'", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    if cp_rec.mission_id != goal_id:
        err_msg = f"Checkpoint '{checkpoint_id}' belongs to mission '{cp_rec.mission_id}', not '{goal_id}'"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "CHECKPOINT_MISMATCH", "checkpoint_id": checkpoint_id, "goal_id": goal_id})
        else:
            console.print(Panel(f"[bold red]Checkpoint mismatch:[/bold red] {err_msg}", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    # 3. Perform rollback
    try:
        res = bridge.store.rollback_to_checkpoint(checkpoint_id)
        if not res.get("ok"):
            err_msg = res.get("error", f"Rollback failed for checkpoint {checkpoint_id}")
            if json_output:
                _print_json({
                    "ok": False,
                    "error": err_msg,
                    "code": "ROLLBACK_FAILED",
                    "checkpoint_id": checkpoint_id,
                    "goal_id": goal_id,
                })
            else:
                console.print(
                    Panel(
                        f"[bold red]Rollback failed:[/bold red] {err_msg}",
                        title="Error",
                        border_style="red",
                    )
                )
            raise typer.Exit(code=1)

        # Record rollback event in goal engine if available
        try:
            engine.store.add_event(goal_id, "goal.rollback", f"Rolled back to checkpoint {checkpoint_id}")
        except Exception:
            pass

        restored = res.get("restored_files", [])
        removed = res.get("removed_files", [])
        payload = {
            "ok": True,
            "status": "rolled_back",
            "goal_id": goal_id,
            "checkpoint_id": checkpoint_id,
            "restored_files": restored,
            "removed_files": removed,
            "task_states": res.get("task_states", {}),
            "rolled_back_at": res.get("rolled_back_at", ""),
        }
        if json_output:
            _print_json(payload)
            return

        console.print(
            Panel(
                f"[bold]Goal ID:[/bold] {goal_id}\n"
                f"[bold]Restored to Checkpoint:[/bold] [cyan]{checkpoint_id}[/cyan]\n"
                f"[bold]Restored Files ({len(restored)}):[/bold] {', '.join(restored) if restored else 'None'}\n"
                f"[bold]Removed Extraneous Files ({len(removed)}):[/bold] {', '.join(removed) if removed else 'None'}\n"
                f"[bold]Status:[/bold] [green]rolled back successfully[/green]",
                title="Goal State Rolled Back",
                border_style="green",
            )
        )
    except typer.Exit:
        raise
    except Exception as exc:
        err_msg = f"Unexpected error during rollback: {exc}"
        if json_output:
            _print_json({"ok": False, "error": err_msg, "code": "ROLLBACK_EXCEPTION"})
        else:
            console.print(Panel(f"[bold red]{err_msg}[/bold red]", title="Error", border_style="red"))
        raise typer.Exit(code=1)


