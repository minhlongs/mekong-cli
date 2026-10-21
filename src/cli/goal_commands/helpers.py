# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shared helpers and Typer app for goal commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from src.cli.i18n import get_messages as _goal_get_messages
from src.mekongcli.core.goal_engine import GoalEngine, GoalStatus, SQLiteGoalStore
from src.mekongcli.core.verification import VerificationPipeline

goal_app = typer.Typer(help="Goal: persistent autonomous mission execution")
console = Console()


def _mod() -> Any:
    return sys.modules.get("src.cli.goal_commands", sys.modules[__name__])


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
