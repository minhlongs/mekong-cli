# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Payload formatting and GoalEngine helper functions for cook commands."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

import typer

from src.mekongcli.core.goal_engine import GoalEngine, GoalStatus, SQLiteGoalStore
from src.mekongcli.core.verification import VerificationPipeline


def _goal_engine(db_path: str | None = None) -> GoalEngine:
    store = SQLiteGoalStore(db_path) if db_path else SQLiteGoalStore()
    return GoalEngine(store=store, cwd=Path.cwd())


def _print_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2, default=str))


def _validate_profile(profile: str) -> None:
    try:
        VerificationPipeline.validate_profile(profile)
    except ValueError as exc:
        raise typer.BadParameter(
            f"must be one of: {VerificationPipeline.profile_options()}",
            param_hint="--profile",
        ) from exc


def _cook_auto_payload(
    completed: GoalStatus,
    goal_id: str,
    title: str,
    profile: str,
    snapshot: dict[str, Any],
    db_path: str | None = None,
    auto: bool = False,
) -> dict[str, Any]:
    verification = snapshot.get("verification") or {}
    verification_results = verification.get("results") or []
    failed_gates = [
        result["name"]
        for result in verification_results
        if result.get("required") and not result.get("passed")
    ]
    db_option = f" --db {shlex.quote(db_path)}" if db_path else ""
    return {
        "id": goal_id,
        "status": completed.value,
        "title": title,
        "profile": profile,
        "auto": auto,
        "tasks_total": len(snapshot.get("tasks", [])),
        "tasks_completed": len(
            [t for t in snapshot.get("tasks", []) if t.get("status") == "completed"]
        ),
        "verification_runs": 1 if verification else 0,
        "verification_passed": verification.get("passed"),
        "failed_gates": failed_gates,
        "status_command": f"mekong goal status {goal_id}{db_option}",
        "resume_command": f"mekong goal resume {goal_id} --profile {profile}{db_option}",
        "verify_command": f"mekong goal verify {goal_id} --profile {profile}{db_option}",
        "status_json_command": f"mekong goal status {goal_id}{db_option} --json",
        "resume_json_command": f"mekong goal resume {goal_id} --profile {profile}{db_option} --json",
        "verify_json_command": f"mekong goal verify {goal_id} --profile {profile}{db_option} --json",
    }


def _cook_auto_panel_body(payload: dict[str, Any]) -> str:
    lines = [
        f"[bold]ID:[/bold] {payload['id']}",
        f"[bold]Status:[/bold] {payload['status']}",
        f"[bold]Verification Profile:[/bold] {payload['profile']}",
        f"[bold]Tasks:[/bold] {payload['tasks_completed']}/{payload['tasks_total']}",
    ]
    if payload.get("verification_passed") is not None:
        lines.append(f"[bold]Verification Passed:[/bold] {payload['verification_passed']}")
    if payload.get("failed_gates"):
        lines.append(f"[bold red]Failed Gates:[/bold red] {', '.join(payload['failed_gates'])}")
    lines.append(f"[bold]Status Command:[/bold] {payload['status_command']}")
    lines.append(f"[bold]Resume Command:[/bold] {payload['resume_command']}")
    lines.append(f"[bold]Verify Command:[/bold] {payload['verify_command']}")
    lines.append(f"[bold]Status JSON:[/bold] {payload['status_json_command']}")
    lines.append(f"[bold]Resume JSON:[/bold] {payload['resume_json_command']}")
    lines.append(f"[bold]Verify JSON:[/bold] {payload['verify_json_command']}")
    return "\n".join(lines)
