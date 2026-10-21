# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for the AI Cell Runtime Engine (``mekong cell run``).

Wires into ``particle_app`` in ``app_setup.py`` as a sub-app::

    mekong cell run <role> --particle <dir> --prompt "analyze ..."
    mekong cell run <role> --particle <dir> --prompt "analyze" --auto-compliance
"""

from __future__ import annotations

import typer

from src.cli.commands.particle_cell_ops import (
    connect_cmd,
    guardian_cmd,
    history_cmd,
    list_cmd,
    status_cmd,
)
from src.cli.commands.particle_cell_run import _fail, run_cmd
from src.cli.commands.particle_init import particle_app
from src.mekong.cells.config import (
    find_cell_configs,
    load_cell_config,
    resolve_particle_config,
)
from src.mekong.cells.guardian import load_guardian_thresholds, run_guardian_review
from src.mekong.cells.runner import (
    run_cell,
    run_compliance,
    run_strategist,
    run_strategist_with_compliance,
)
from src.mekong.cells.types import CellConfig
from src.mekong.graph.network import (
    connect_particles,
    cross_particle_strategist,
    particle_network_status,
)
from src.mekong.graph.store import get_behaviors, open_db

cell_app = typer.Typer(
    name="cell",
    help="AI Cell Runtime Engine — execute and audit autonomous cells",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

cell_app.command(name="run")(run_cmd)
cell_app.command(name="list")(list_cmd)
cell_app.command(name="history")(history_cmd)
cell_app.command(name="guardian")(guardian_cmd)

particle_app.command(name="connect")(connect_cmd)
particle_app.command(name="status")(status_cmd)

__all__ = [
    "CellConfig",
    "_fail",
    "cell_app",
    "connect_cmd",
    "connect_particles",
    "cross_particle_strategist",
    "find_cell_configs",
    "get_behaviors",
    "guardian_cmd",
    "history_cmd",
    "list_cmd",
    "load_cell_config",
    "load_guardian_thresholds",
    "open_db",
    "particle_app",
    "particle_network_status",
    "resolve_particle_config",
    "run_cell",
    "run_cmd",
    "run_compliance",
    "run_guardian_review",
    "run_strategist",
    "run_strategist_with_compliance",
    "status_cmd",
]
