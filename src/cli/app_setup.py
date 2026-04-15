"""
Typer app factory and sub-app + command registration for Mekong CLI.

Creates the root Typer app, wires in all sub-apps (swarm, schedule, memory, etc.),
and registers all flat command groups (cook, plan, recipe, system commands).
Import and call build_app() to get the fully configured app.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import typer


def build_app() -> typer.Typer:
    """Create and return the fully wired Mekong CLI Typer app."""
    # Sub-app imports
    from src.cli.binh_phap_commands import app as binh_phap_app
    from src.commands.agi import app as agi_app
    from src.cli.swarm_commands import swarm_app
    from src.cli.schedule_commands import schedule_app
    from src.cli.memory_commands import memory_app
    from src.cli.autonomous_commands import autonomous_app, telegram_app
    from src.cli.tools_browse_collab_commands import tools_app, browse_app, collab_app

    # Flat command group registrations
    from src.cli.cook_command import register_cook_command
    from src.cli.workflow_commands import register_workflow_commands
    from src.cli.recipe_commands import register_recipe_commands
    from src.cli.system_commands import register_system_commands

    # BMAD uses dash naming — not importable as standard package
    spec = importlib.util.spec_from_file_location(
        "bmad_commands", Path(__file__).parent / "bmad-commands.py"
    )
    bmad_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bmad_module)
    bmad_app = bmad_module.app

    root = typer.Typer(
        name="mekong",
        help="🚀 Mekong CLI: RaaS Agency Operating System",
        add_completion=False,
    )

    # Wire sub-apps
    root.add_typer(bmad_app, name="bmad", help="BMAD workflow management")
    root.add_typer(binh_phap_app, name="binh-phap", help="Binh Pháp Strategy: Infinite loops & Standards")
    root.add_typer(agi_app, name="agi", help="Tom Hum AGI daemon management")
    root.add_typer(swarm_app, name="swarm")
    root.add_typer(schedule_app, name="schedule")
    root.add_typer(memory_app, name="memory")
    root.add_typer(telegram_app, name="telegram")
    root.add_typer(autonomous_app, name="autonomous")
    root.add_typer(tools_app, name="tools")
    root.add_typer(browse_app, name="browse")
    root.add_typer(collab_app, name="collab")

    # Register flat command groups
    register_cook_command(root)
    register_workflow_commands(root)
    register_recipe_commands(root)
    register_system_commands(root)

    return root
