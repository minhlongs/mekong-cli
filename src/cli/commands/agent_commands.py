# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain-agent CLI surface — ``mekong agent list``, ``run``, ``info``, ``create``, ``init``."""

from __future__ import annotations

import typer
from rich.console import Console

from src.cli.commands._agent_assemble_cmds import agent_assemble
from src.cli.commands._agent_core_cmds import (
    _find,
    _render_list,
    agent_info,
    agent_list,
    agent_run,
)
from src.cli.commands._agent_scaffold_cmds import (
    _AGENT_TEMPLATE,
    _write_agent_file,
    agent_create,
    agent_init,
)
from src.cli.commands._agent_spawn_cmds import agent_spawn
from src.core.agent_registry import AgentMeta, get_registry

app = typer.Typer(
    name="agent",
    help="Manage and run domain agents (cto, cmo, coo, cfo, cso, planner, ...)",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()

app.command("list")(agent_list)
app.command("run")(agent_run)
app.command("info")(agent_info)
app.command("create")(agent_create)
app.command("init")(agent_init)
app.command("assemble")(agent_assemble)
app.command("spawn")(agent_spawn)


def register_agent_commands(root: typer.Typer) -> None:
    """Add the ``agent`` sub-app to the root Typer app."""
    root.add_typer(
        app,
        name="agent",
        help="Domain agent management (list | run | info | create | init | assemble | spawn)",
    )


__all__ = [
    "AgentMeta",
    "_AGENT_TEMPLATE",
    "_find",
    "_render_list",
    "_write_agent_file",
    "agent_assemble",
    "agent_create",
    "agent_info",
    "agent_init",
    "agent_list",
    "agent_run",
    "agent_spawn",
    "app",
    "console",
    "get_registry",
    "register_agent_commands",
]
