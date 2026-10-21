# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cook-auto and cook-auto-parallel command handlers."""

from __future__ import annotations

import typer
from engine.billing.tier_config import Tier
from engine.license.license_enforcer import require_tier
from rich.panel import Panel

from src.cli.cook_command.payload import (
    _cook_auto_panel_body,
    _cook_auto_payload,
    _goal_engine,
    _print_json,
    _validate_profile,
)
from src.cli.cook_command.preview import _render_cook_auto_dry_run, console
from src.core.pev_swarm_bridge import PEVSwarmBridge
from src.mekongcli.core.goal_engine import GoalStatus


def register_cook_auto_commands(app: typer.Typer) -> None:
    """Register cook-auto and cook-auto-parallel onto the Typer app."""

    @require_tier(Tier.FREE)
    @app.command(name="cook-auto")
    def cook_auto(
        goal: list[str] = typer.Argument(..., help="High-level goal to execute autonomously"),
        max_cycles: int = typer.Option(3, "--max-cycles", "-c", help="Maximum autonomous PEV cycles"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview planned multi-agent delegation hierarchy"),
        checkpoint_id: str | None = typer.Option(None, "--checkpoint-id", help="Resume from or target specific checkpoint ID"),
        profile: str = typer.Option("smoke", "--profile", help="Verification profile: standard|smoke|none"),
        execute_commands: bool = typer.Option(False, "--execute-commands", help="Run task commands when present"),
        auto: bool = typer.Option(False, "--auto", help="Accept AGY auto mode"),
        timeout_seconds: float | None = typer.Option(None, "--timeout", help="Max seconds before cancelling goal execution"),
        db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Machine-readable JSON output"),
    ) -> None:
        """Create, run, checkpoint, and verify a durable autonomous goal."""
        _validate_profile(profile)
        if max_cycles <= 0:
            raise typer.BadParameter("max-cycles must be positive", param_hint="--max-cycles")
        goal_title = " ".join(goal).strip()
        if not goal_title:
            raise typer.BadParameter("goal cannot be empty", param_hint="GOAL")

        bridge = PEVSwarmBridge()

        if checkpoint_id:
            cp = bridge.store.get_checkpoint(checkpoint_id)
            if not cp:
                err_msg = f"Checkpoint not found or corrupted: '{checkpoint_id}'"
                if json_output:
                    _print_json({"ok": False, "error": err_msg, "code": "CHECKPOINT_NOT_FOUND"})
                else:
                    console.print(
                        Panel(
                            f"[bold red]Checkpoint not found or corrupted:[/bold red] '{checkpoint_id}'",
                            title="Error",
                            border_style="red",
                        )
                    )
                raise typer.Exit(code=1)

        if dry_run:
            plan = bridge.plan(goal_title)
            if json_output:
                _print_json({
                    "ok": True,
                    "status": "dry_run",
                    "goal": goal_title,
                    "profile": profile,
                    "max_cycles": max_cycles,
                    "checkpoint_id": checkpoint_id,
                    "plan": plan.to_dict(),
                })
            else:
                _render_cook_auto_dry_run(
                    plan=plan,
                    goal_title=goal_title,
                    profile=profile,
                    max_cycles=max_cycles,
                    checkpoint_id=checkpoint_id,
                )
            return

        if checkpoint_id:
            bridge.store.rollback_to_checkpoint(checkpoint_id)

        engine = _goal_engine(db_path)
        created = engine.create_goal(goal_title)
        completed = engine.run_goal(
            created.id,
            verification_profile=profile,
            execute_commands=execute_commands,
            timeout_seconds=timeout_seconds,
        )
        snapshot = engine.status(created.id)
        payload = _cook_auto_payload(
            completed.status, completed.id, completed.title, profile, snapshot, db_path, auto
        )

        if json_output:
            _print_json(payload)
        else:
            style = "green" if completed.status == GoalStatus.SATISFIED else "red"
            console.print(Panel(_cook_auto_panel_body(payload), title="Cook Auto Complete", border_style=style))

        if completed.status != GoalStatus.SATISFIED:
            raise typer.Exit(code=1)

    @require_tier(Tier.FREE)
    @app.command(name="cook-auto-parallel")
    def cook_auto_parallel(
        goal: list[str] = typer.Argument(..., help="High-level goal to execute autonomously in parallel"),
        profile: str = typer.Option("smoke", "--profile", help="Verification profile: standard|smoke|none"),
        execute_commands: bool = typer.Option(False, "--execute-commands", help="Run task commands when present"),
        auto: bool = typer.Option(False, "--auto", help="Accept AGY auto mode"),
        db_path: str | None = typer.Option(None, "--db", help="Override goal database path"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Machine-readable JSON output"),
        max_workers: int = typer.Option(3, "--workers", help="Max parallel execution threads"),
        timeout_seconds: float | None = typer.Option(None, "--timeout", help="Max seconds before cancelling goal execution"),
    ) -> None:
        """Create, run in parallel, checkpoint, and verify a durable autonomous goal."""
        _validate_profile(profile)
        if max_workers <= 0:
            raise typer.BadParameter("workers must be a positive integer", param_hint="--workers")
        goal_title = " ".join(goal).strip()
        if not goal_title:
            raise typer.BadParameter("goal cannot be empty", param_hint="GOAL")
        engine = _goal_engine(db_path)
        created = engine.create_goal(goal_title)
        completed = engine.run_goal_parallel(
            created.id,
            verification_profile=profile,
            execute_commands=execute_commands,
            max_workers=max_workers,
            timeout_seconds=timeout_seconds,
        )
        snapshot = engine.status(created.id)
        payload = _cook_auto_payload(
            completed.status, completed.id, completed.title, profile, snapshot, db_path, auto
        )

        if json_output:
            _print_json(payload)
        else:
            style = "green" if completed.status == GoalStatus.SATISFIED else "red"
            console.print(Panel(_cook_auto_panel_body(payload), title="Cook Auto Parallel Complete", border_style=style))

        if completed.status != GoalStatus.SATISFIED:
            raise typer.Exit(code=1)
