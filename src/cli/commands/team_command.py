# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/team_command.py — Agent Team Orchestration CLI.

Orchestrate Agent Teams for parallel multi-session collaboration:
- Team management (create, list, assign, dashboard, members, tasks, delete)
- Orchestration templates (research, cook, review, debug, orchestrate)
"""

from __future__ import annotations

import typer
from rich.console import Console

from src.cli.commands._team_inspect_cmds import (
    team_delete,
    team_members,
    team_status,
    team_tasks,
)
from src.cli.commands._team_mgmt_cmds import (
    team_assign,
    team_create,
    team_dashboard,
    team_list,
)
from src.cli.commands._team_orchestrate_cmds import (
    team_cook,
    team_debug,
    team_orchestrate,
    team_research,
    team_review,
)
from src.core.team_manager import TeamManager, get_team_manager

console = Console()

team_app = typer.Typer(
    name="team",
    help="👥 Agent Teams: Parallel multi-session collaboration and autonomous team orchestration",
    no_args_is_help=False,
)


@team_app.callback(invoke_without_command=True)
def team_callback(ctx: typer.Context) -> None:
    """Default handler when 'mekong team' is called without subcommands."""
    if ctx.invoked_subcommand is None:
        team_dashboard(json_output=False)


team_app.command(name="create")(team_create)
team_app.command(name="list")(team_list)
team_app.command(name="assign")(team_assign)
team_app.command(name="dashboard")(team_dashboard)
team_app.command(name="status")(team_status)
team_app.command(name="members")(team_members)
team_app.command(name="tasks")(team_tasks)
team_app.command(name="delete")(team_delete)
team_app.command(name="research")(team_research)
team_app.command(name="cook")(team_cook)
team_app.command(name="review")(team_review)
team_app.command(name="debug")(team_debug)
team_app.command(name="orchestrate")(team_orchestrate)

# Aliases for ClaudeKit & legacy template signatures
team_app.command(name="ck:research", hidden=True)(team_research)
team_app.command(name="ck:cook", hidden=True)(team_cook)
team_app.command(name="ck:review", hidden=True)(team_review)
team_app.command(name="ck:debug", hidden=True)(team_debug)
team_app.command(name="code-review", hidden=True)(team_review)


def register_team_command(root: typer.Typer) -> None:
    """Mount 'team' command group on main Mekong CLI application."""
    root.add_typer(
        team_app,
        name="team",
        help="Agent Teams: Parallel multi-session collaboration & team orchestration",
    )


__all__ = [
    "TeamManager",
    "console",
    "get_team_manager",
    "register_team_command",
    "team_app",
    "team_assign",
    "team_callback",
    "team_cook",
    "team_create",
    "team_dashboard",
    "team_debug",
    "team_delete",
    "team_list",
    "team_members",
    "team_orchestrate",
    "team_research",
    "team_review",
    "team_status",
    "team_tasks",
]
