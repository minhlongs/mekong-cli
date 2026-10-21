"""Core sub-apps and flat command group registration for Mekong CLI."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import typer

_BPHAP_HELP = "Binh Phap Strategy: Infinite loops & Standards"
_IDEA_HELP = "Idea pipeline: validate -> BMC -> PRD -> execution handoff"


def _load_bmad_app() -> typer.Typer:
    """Load optional BMAD sub-app or degrade gracefully."""
    spec = importlib.util.spec_from_file_location(
        "bmad_commands",
        Path(__file__).resolve().parent.parent / "bmad-commands.py",
    )
    if spec is None or spec.loader is None:
        return typer.Typer(name="bmad", help="BMAD workflow management")
    bmad_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(bmad_module)
        return bmad_module.app
    except (ImportError, KeyError):
        return typer.Typer(name="bmad", help="BMAD workflow management")


def register_core_subapps(root: typer.Typer) -> None:
    """Wire core, SDD, SDLC, and design-intelligence sub-apps onto root."""
    from src.cli.autonomous_commands import autonomous_app, telegram_app
    from src.cli.billing_commands import app as billing_app
    from src.cli.binh_phap_commands import app as binh_phap_app
    from src.cli.commands.analyze import analyze_app
    from src.cli.commands.company_init import app as company_app
    from src.cli.commands.doctor_command import register as register_doctor
    from src.cli.commands.harness_eval_command import register_harness_eval_command
    from src.cli.commands.implement import implement_app
    from src.cli.commands.specify import specify_app
    from src.cli.commands.swarm_orchestration import register_swarm_commands
    from src.cli.commands.tasks import tasks_app
    from src.cli.csuite_commands import register_csuite_commands
    from src.cli.goal_commands import goal_app
    from src.cli.idea_commands import app as idea_app
    from src.cli.memory_commands import memory_app
    from src.cli.pev_commands import pev_app
    from src.cli.schedule_commands import schedule_app
    from src.cli.sdlc.code import code_app
    from src.cli.sdlc.deploy import deploy_app
    from src.cli.sdlc.design import design_app
    from src.cli.sdlc.spec import spec_app
    from src.cli.tools_browse_collab_commands import browse_app, collab_app, tools_app
    from src.cli.ui_commands import register_ui_commands
    from src.cli.usage_commands import app as usage_app
    from src.commands.agi import app as agi_app

    bmad_app = _load_bmad_app()
    root.add_typer(bmad_app, name="bmad", help="BMAD workflow management")
    root.add_typer(binh_phap_app, name="binh-phap", help=_BPHAP_HELP)
    root.add_typer(goal_app, name="goal", help="Goal: persistent autonomous mission execution")
    root.add_typer(goal_app, name="g", help="Goal alias (/g): persistent autonomous mission execution")
    root.add_typer(idea_app, name="idea", help=_IDEA_HELP)
    root.add_typer(agi_app, name="agi", help="Tom Hum AGI daemon management")
    register_swarm_commands(root)
    root.add_typer(schedule_app, name="schedule")
    root.add_typer(memory_app, name="memory")
    root.add_typer(telegram_app, name="telegram")
    root.add_typer(autonomous_app, name="autonomous")
    root.add_typer(tools_app, name="tools")
    root.add_typer(browse_app, name="browse")
    root.add_typer(collab_app, name="collab")
    root.add_typer(billing_app, name="billing")
    root.add_typer(pev_app, name="pev")
    root.add_typer(usage_app, name="usage")
    register_doctor(root)
    register_harness_eval_command(root)
    register_csuite_commands(root)

    root.add_typer(specify_app, name="specify", help="SDD: generate feature spec from template")
    root.add_typer(tasks_app, name="tasks", help="SDD: generate TDD task list from spec")
    root.add_typer(implement_app, name="implement", help="SDD: execute implementation from task list")
    root.add_typer(analyze_app, name="analyze", help="SDD: cross-artifact consistency check")

    root.add_typer(spec_app, name="spec", help="Spec phase: feature request -> requirements")
    root.add_typer(design_app, name="design", help="Design phase: requirements -> architecture")
    root.add_typer(code_app, name="code", help="Code phase: architecture -> task backlog")
    root.add_typer(deploy_app, name="deploy", help="Deploy phase: verify gates -> ship/hold")

    register_ui_commands(root)
    root.add_typer(company_app, name="company", help="Company / workspace configuration")
