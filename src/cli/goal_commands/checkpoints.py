# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Checkpoint and rollback commands for goal command group."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel

from src.cli.goal_commands.helpers import _mod, _print_json, console, goal_app


def _check_goal_exists(engine: object, bridge: object, goal_id: str) -> bool:
    try:
        engine.status(goal_id)  # type: ignore[attr-defined]
        return True
    except KeyError:
        return bool(bridge.get_mission_status(goal_id).get("ok"))  # type: ignore[attr-defined]


def _fail(json_output: bool, payload: dict[str, object], msg: str) -> None:
    if json_output:
        _print_json(payload)
    else:
        console.print(Panel(msg, title="Error", border_style="red"))
    raise typer.Exit(code=1)


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
    m = _mod()
    engine = m._engine(db_path)
    bridge = m.PEVSwarmBridge(db_path=Path(db_path) if db_path and "pev" in str(db_path) else None)

    if not _check_goal_exists(engine, bridge, goal_id):
        _fail(
            json_output,
            {"ok": False, "error": f"Goal not found: '{goal_id}'", "code": "GOAL_NOT_FOUND", "goal_id": goal_id},
            f"[bold red]Goal not found:[/bold red] '{goal_id}'",
        )

    file_list = [f.strip() for f in files.split(",") if f.strip()] if files else None
    try:
        cp_id = bridge.store.capture_checkpoint(mission_id=goal_id, label=label, files=file_list)
        cp_rec = bridge.store.get_checkpoint(cp_id)
        file_count = len(cp_rec.file_snapshots) if cp_rec else 0
        try:
            engine.store.add_checkpoint(goal_id, label)
        except Exception:
            pass

        payload = {
            "ok": True, "status": "captured", "checkpoint_id": cp_id, "goal_id": goal_id,
            "label": label, "file_count": file_count, "created_at": cp_rec.created_at if cp_rec else "",
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
                title="Goal Checkpoint Captured", border_style="green",
            )
        )
    except Exception as exc:
        err_msg = f"Failed to capture checkpoint: {exc}"
        _fail(json_output, {"ok": False, "error": err_msg, "code": "CHECKPOINT_FAILED"}, f"[bold red]{err_msg}[/bold red]")


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
    m = _mod()
    engine = m._engine(db_path)
    pev_db_path = Path(db_path) if db_path and "pev" in str(db_path) else None
    bridge = m.PEVSwarmBridge(db_path=pev_db_path)

    if not _check_goal_exists(engine, bridge, goal_id):
        _fail(
            json_output,
            {"ok": False, "error": f"Goal not found: '{goal_id}'", "code": "GOAL_NOT_FOUND", "goal_id": goal_id},
            f"[bold red]Goal not found:[/bold red] '{goal_id}'",
        )

    try:
        with bridge.store._connect() as conn:
            cp_row = conn.execute(
                "SELECT checkpoint_id, mission_id FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,),
            ).fetchone()
    except Exception as exc:
        err_msg = f"Database error reading checkpoint: {exc}"
        _fail(json_output, {"ok": False, "error": err_msg, "code": "DB_ERROR"}, f"[bold red]{err_msg}[/bold red]")

    if not cp_row:
        _fail(
            json_output,
            {"ok": False, "error": f"Checkpoint not found: '{checkpoint_id}'", "code": "CHECKPOINT_NOT_FOUND", "checkpoint_id": checkpoint_id},
            f"[bold red]Checkpoint not found:[/bold red] '{checkpoint_id}'",
        )

    cp_rec = bridge.store.get_checkpoint(checkpoint_id)
    if not cp_rec:
        _fail(
            json_output,
            {"ok": False, "error": f"Corrupted checkpoint state: '{checkpoint_id}'", "code": "CHECKPOINT_CORRUPTED", "checkpoint_id": checkpoint_id},
            f"[bold red]Corrupted checkpoint state:[/bold red] '{checkpoint_id}'",
        )

    if cp_rec.mission_id != goal_id:
        err_msg = f"Checkpoint '{checkpoint_id}' belongs to mission '{cp_rec.mission_id}', not '{goal_id}'"
        _fail(
            json_output,
            {"ok": False, "error": err_msg, "code": "CHECKPOINT_MISMATCH", "checkpoint_id": checkpoint_id, "goal_id": goal_id},
            f"[bold red]Checkpoint mismatch:[/bold red] {err_msg}",
        )

    try:
        res = bridge.store.rollback_to_checkpoint(checkpoint_id)
        if not res.get("ok"):
            err_msg = res.get("error", f"Rollback failed for checkpoint {checkpoint_id}")
            _fail(
                json_output,
                {"ok": False, "error": err_msg, "code": "ROLLBACK_FAILED", "checkpoint_id": checkpoint_id, "goal_id": goal_id},
                f"[bold red]Rollback failed:[/bold red] {err_msg}",
            )

        try:
            engine.store.add_event(goal_id, "goal.rollback", f"Rolled back to checkpoint {checkpoint_id}")
        except Exception:
            pass

        restored, removed = res.get("restored_files", []), res.get("removed_files", [])
        payload = {
            "ok": True, "status": "rolled_back", "goal_id": goal_id, "checkpoint_id": checkpoint_id,
            "restored_files": restored, "removed_files": removed,
            "task_states": res.get("task_states", {}), "rolled_back_at": res.get("rolled_back_at", ""),
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
                title="Goal State Rolled Back", border_style="green",
            )
        )
    except typer.Exit:
        raise
    except Exception as exc:
        err_msg = f"Unexpected error during rollback: {exc}"
        _fail(json_output, {"ok": False, "error": err_msg, "code": "ROLLBACK_EXCEPTION"}, f"[bold red]{err_msg}[/bold red]")
