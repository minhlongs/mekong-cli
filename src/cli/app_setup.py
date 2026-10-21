# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Typer app factory and sub-app + command registration for Mekong CLI.

Creates the root Typer app, wires in all sub-apps (swarm, schedule, memory, etc.),
and registers all flat command groups (cook, plan, recipe, system commands).
Import and call build_app() to get the fully configured app.
"""

from __future__ import annotations

import typer

from src.cli._app_setup.core_setup import (
    _BPHAP_HELP,
    _IDEA_HELP,
    register_core_subapps,
)
from src.cli._app_setup.domain_groups import register_domain_groups
from src.cli._app_setup.flat_and_tail import (
    register_flat_commands,
    register_tail_subapps,
)

__all__ = ["_BPHAP_HELP", "_IDEA_HELP", "build_app"]


def build_app() -> typer.Typer:
    """Create and return the fully wired Mekong CLI Typer app."""
    root = typer.Typer(
        name="mekong",
        help="🚀 Mekong CLI: RaaS Agency Operating System",
        add_completion=False,
    )
    register_core_subapps(root)
    register_flat_commands(root)
    register_domain_groups(root)
    register_tail_subapps(root)
    return root
