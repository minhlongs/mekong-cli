# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cook command: Plan -> Execute -> Verify (PEV) workflow."""

from __future__ import annotations

import typer

from src.cli.cook_command.cook_auto import register_cook_auto_commands
from src.cli.cook_command.cook_run import register_canonical_cook
from src.cli.cook_command.payload import (
    _cook_auto_panel_body,
    _cook_auto_payload,
    _goal_engine,
    _print_json,
    _validate_profile,
)
from src.cli.cook_command.preview import (
    _get_role_layer,
    _render_cook_auto_dry_run,
    console,
)
from src.core.pev_swarm_bridge import PEVSwarmBridge, PevPhase
from src.mekongcli.core.goal_engine import GoalEngine, GoalStatus, SQLiteGoalStore
from src.mekongcli.core.verification import VerificationPipeline


def register_cook_command(app: typer.Typer) -> None:
    """Register the cook commands onto the typer app."""
    register_cook_auto_commands(app)
    register_canonical_cook(app)


__all__ = [
    "GoalEngine",
    "GoalStatus",
    "PEVSwarmBridge",
    "PevPhase",
    "SQLiteGoalStore",
    "VerificationPipeline",
    "_cook_auto_panel_body",
    "_cook_auto_payload",
    "_get_role_layer",
    "_goal_engine",
    "_print_json",
    "_render_cook_auto_dry_run",
    "_validate_profile",
    "console",
    "register_cook_command",
]
