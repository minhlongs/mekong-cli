# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Goal command group for the autonomous engineering OS vertical slice."""

from __future__ import annotations

from src.cli.goal_commands.checkpoints import goal_checkpoint, goal_rollback
from src.cli.goal_commands.execution import (
    goal_create,
    goal_resume,
    goal_run,
    goal_run_parallel,
    goal_verify,
)
from src.cli.goal_commands.helpers import (
    _engine,
    _goal_get_messages,
    _goal_result_payload,
    _print_json,
    _t,
    _validate_profile,
    console,
    goal_app,
)
from src.cli.goal_commands.inspection import goal_cancel, goal_list, goal_status
from src.core.pev_swarm_bridge import PEVSwarmBridge
from src.mekongcli.core.goal_engine import GoalEngine, GoalStatus, SQLiteGoalStore
from src.mekongcli.core.verification import VerificationPipeline

__all__ = [
    "GoalEngine",
    "GoalStatus",
    "PEVSwarmBridge",
    "SQLiteGoalStore",
    "VerificationPipeline",
    "_engine",
    "_goal_get_messages",
    "_goal_result_payload",
    "_print_json",
    "_t",
    "_validate_profile",
    "console",
    "goal_app",
    "goal_cancel",
    "goal_checkpoint",
    "goal_create",
    "goal_list",
    "goal_resume",
    "goal_rollback",
    "goal_run",
    "goal_run_parallel",
    "goal_status",
    "goal_verify",
]
