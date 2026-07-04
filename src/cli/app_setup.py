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

    # SDLC scaffold sub-apps (phase-04)
    from src.cli.sdlc.spec import spec_app
    from src.cli.sdlc.design import design_app
    from src.cli.sdlc.code import code_app
    from src.cli.sdlc.deploy import deploy_app

    # Phase-03 flat commands (signals loop)
    from src.cli.commands.metrics import register as register_metrics
    from src.cli.commands.eval_agent import register as register_eval_agent

    # Flat command group registrations
    from src.cli.cook_command import register_cook_command
    from src.cli.workflow_commands import register_workflow_commands
    from src.cli.recipe_commands import register_recipe_commands
    from src.cli.system_commands import register_system_commands

    # Phase-01: company-init CLI surface (mekong company init | reset | status)
    from src.cli.commands.company_init import app as company_app

    # Phase-03: particle init CLI surface (mekong particle init)
    from src.cli.commands.particle_init import particle_app

    # Phase-04: particle graph CLI surface (mekong particle graph)
    from src.cli.commands.particle_graph import graph_app

    # Phase-01: AI Cell runtime (mekong cell run)
    from src.cli.commands.particle_cell import cell_app

    # Phase-02: plan CLI surface (mekong plan from-init)
    from src.cli.commands.plan import app as plan_app

    # Phase-02: build CLI surface (mekong build from-plan)
    from src.cli.commands.build import app as build_app

    # Phase-02: founder genome assessment (mekong founder assess | review | list)
    from src.cli.commands.founder import founder_app

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

    # Wire SDLC scaffold sub-apps (phase-04)
    root.add_typer(spec_app, name="spec", help="Spec phase: feature request → requirements")
    root.add_typer(design_app, name="design", help="Design phase: requirements → architecture")
    root.add_typer(code_app, name="code", help="Code phase: architecture → task backlog")
    root.add_typer(deploy_app, name="deploy", help="Deploy phase: verify gates → ship/hold")

    # Register flat command groups
    register_cook_command(root)
    register_workflow_commands(root)
    register_recipe_commands(root)
    register_system_commands(root)

    root.add_typer(
        company_app,
        name="company",
        help="Company / workspace configuration",
    )

    # Phase-02: plan and build sub-apps
    root.add_typer(
        plan_app,
        name="plan",
        help="Plan generation from company init",
    )
    root.add_typer(
        build_app,
        name="build",
        help="Build task generation from spec",
    )

    # Phase-02: founder genome sub-app (mekong founder assess|review|list)
    root.add_typer(
        founder_app,
        name="founder",
        help="Founder genome assessment — personality, risk, bias profiling",
    )

    # Phase-03: particle management
    root.add_typer(
        particle_app,
        name="particle",
        help="ZenOS particle lifecycle management",
    )

    # Phase-04: particle graph sub-app (mekong particle graph ...)
    particle_app.add_typer(
        graph_app,
        name="graph",
        help="Behavior graph — trust & collusion detection",
    )

    # Phase-01: AI Cell runtime sub-app (mekong cell run ...)
    particle_app.add_typer(
        cell_app,
        name="cell",
        help="AI Cell Runtime Engine — execute and audit autonomous cells",
    )

    # Phase-03 signals commands (metrics + offline evals)
    register_metrics(root)
    register_eval_agent(root)

    return root
