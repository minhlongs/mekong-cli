"""Typer app factory and sub-app + command registration for Mekong CLI.

Creates the root Typer app, wires in all sub-apps (swarm, schedule, memory, etc.),
and registers all flat command groups (cook, plan, recipe, system commands).
Import and call build_app() to get the fully configured app.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import typer


class MekongGroup(typer.core.TyperGroup):
    """Lazy-loads the mk sub-app on first access to avoid import cascade.

    Also transparently routes ``mk-<name>`` invocations to the corresponding
    command inside the ``mk`` sub-group, so both
    ``python -m src.main mk cook`` and ``python -m src.main mk-cook`` work.
    """

    _mk_built: bool = False

    def _ensure_mk_built(self) -> None:
        if self._mk_built:
            return
        self._mk_built = True
        from src.cli.mk_commands import build_mk_app as _build
        mk_app = _build()
        from typer.main import get_group
        mk_click_group = get_group(mk_app)
        self.add_command(mk_click_group)

    def _resolve_mk_alias(self, cmd_name: str):
        """If cmd_name looks like ``mk-<leaf>``, return the command from the mk group."""
        if not cmd_name.startswith("mk-"):
            return None
        self._ensure_mk_built()
        leaf = cmd_name[len("mk-"):]          # e.g. "mk-cook" → "cook"
        mk_group = self.commands.get("mk")
        if mk_group is None:
            return None
        # Try exact match first (for commands already named mk-* in mk group)
        cmd = mk_group.commands.get(cmd_name)
        if cmd is not None:
            return cmd
        # Try stripping mk- prefix to find the original command
        cmd = mk_group.commands.get(leaf)
        return cmd

    def list_commands(self, ctx):
        self._ensure_mk_built()
        return super().list_commands(ctx)

    def get_command(self, ctx, cmd_name):
        # Try mk-* alias routing first
        alias_cmd = self._resolve_mk_alias(cmd_name)
        if alias_cmd is not None:
            return alias_cmd
        self._ensure_mk_built()
        return super().get_command(ctx, cmd_name)

    def invoke(self, ctx):
        self._ensure_mk_built()
        return super().invoke(ctx)


def build_app() -> typer.Typer:
    """Create and return the fully wired Mekong CLI Typer app."""
    # Sub-app imports
    from src.cli.binh_phap_commands import app as binh_phap_app
    from src.commands.agi import app as agi_app
    from src.cli.swarm_commands import swarm_app
    from src.cli.schedule_commands import schedule_app
    from src.cli.memory_commands import memory_app
    from src.cli.goal_commands import goal_app
    from src.cli.autonomous_commands import autonomous_app, telegram_app
    from src.cli.tools_browse_collab_commands import tools_app, browse_app, collab_app

    # SDLC scaffold sub-apps (phase-04)
    from src.cli.sdlc.spec import spec_app
    from src.cli.sdlc.design import design_app
    from src.cli.sdlc.code import code_app
    from src.cli.sdlc.deploy import deploy_app

    # Phase-03 flat commands (signals loop)
    from src.cli.commands.metrics import register as register_metrics
    from src.cli.commands.algo_status import register as register_algo_status
    from src.cli.commands.eval_agent import register as register_eval_agent

    # Flat command group registrations
    from src.cli.cook_command import register_cook_command
    from src.cli.workflow_commands import register_workflow_commands
    from src.cli.recipe_commands import register_recipe_commands
    from src.cli.system_commands import register_system_commands
    from src.cli.studio_commands import register_studio_commands

    # BMAD uses dash naming - not importable as standard package
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
        cls=MekongGroup,
    )

    # Wire sub-apps
    root.add_typer(bmad_app, name="bmad", help="BMAD workflow management")
    root.add_typer(binh_phap_app, name="binh-phap", help="Binh Pháp Strategy: Infinite loops & Standards")
    root.add_typer(agi_app, name="agi", help="Tom Hum AGI daemon management")
    root.add_typer(swarm_app, name="swarm")
    root.add_typer(schedule_app, name="schedule")
    root.add_typer(memory_app, name="memory")
    root.add_typer(goal_app, name="goal")
    root.add_typer(telegram_app, name="telegram")
    root.add_typer(autonomous_app, name="autonomous")
    root.add_typer(tools_app, name="tools")
    root.add_typer(browse_app, name="browse")
    root.add_typer(collab_app, name="collab")

    # Wire SDLC scaffold sub-apps (phase-04)
    root.add_typer(spec_app, name="spec", help="Spec phase: feature request - requirements")
    root.add_typer(design_app, name="design", help="Design phase: requirements - architecture")
    root.add_typer(code_app, name="code", help="Code phase: architecture - task backlog")
    root.add_typer(deploy_app, name="deploy", help="Deploy phase: verify gates - ship/hold")

    # Register flat command groups
    register_cook_command(root)
    register_workflow_commands(root)
    register_recipe_commands(root)
    register_system_commands(root)
    register_studio_commands(root)

    # Phase-03 signals commands (metrics + offline evals)
    register_metrics(root)
    register_algo_status(root)
    register_eval_agent(root)

    # mk group is registered lazily by MekongGroup - no eager call here
    return root
