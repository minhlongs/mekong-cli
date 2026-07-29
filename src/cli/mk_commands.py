"""mk command group — prefixed wrapper for ALL Mekong CLI commands.

Creates an independent ``mk`` Typer group that mirrors every command
from the main CLI with a ``mk-`` prefix.  No circular dependency with
app_setup — this module builds its OWN app by directly importing and
re-registering all sub-apps and flat commands.

Usage:
    python -m src.main mk-cook <goal>
    python -m src.main mk-plan <goal>
    python -m src.main mk-agi daemon start
    python -m src.main mk --help
"""

from __future__ import annotations

import typer
from pathlib import Path
import importlib.util


def build_mk_app() -> typer.Typer:
    """Build and return the ``mk`` command group.

    Every command from the main Mekong CLI is registered here with a
    ``mk-`` prefix.  Original commands continue to work unchanged.
    """
    mk = typer.Typer(
        name="mk",
        help="🚀 mk: Mekong CLI with mk- prefix (Harness Engineering)",
        add_completion=False,
    )

    # ---- Sub-apps (imported and re-registered with mk- prefix) ------------
    from src.cli.binh_phap_commands import app as _binh_phap_app
    mk.add_typer(_binh_phap_app, name="mk-binh-phap",
                 help="Binh Pháp Strategy: Infinite loops & Standards")

    # BMAD (importlib because it's a plain .py file, not a package)
    spec = importlib.util.spec_from_file_location(
        "bmad_commands",
        Path(__file__).parent.parent / "cli" / "bmad-commands.py",
    )
    bmad_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bmad_module)
    mk.add_typer(bmad_module.app, name="mk-bmad",
                 help="BMAD workflow management")

    from src.commands.agi import app as _agi_app
    mk.add_typer(_agi_app, name="mk-agi",
                 help="Tom Hum AGI daemon management")

    from src.cli.swarm_commands import swarm_app
    mk.add_typer(swarm_app, name="mk-swarm",
                 help="Swarm: distributed multi-node execution")

    from src.cli.schedule_commands import schedule_app
    mk.add_typer(schedule_app, name="mk-schedule",
                 help="Schedule: autonomous recurring missions")

    from src.cli.memory_commands import memory_app
    mk.add_typer(memory_app, name="mk-memory",
                 help="Memory: execution history & learning")

    from src.cli.goal_commands import goal_app
    mk.add_typer(goal_app, name="mk-goal",
                 help="Goal: persistent autonomous mission execution")

    from src.cli.autonomous_commands import autonomous_app, telegram_app
    mk.add_typer(autonomous_app, name="mk-autonomous",
                 help="Autonomous: AGI loop control")
    mk.add_typer(telegram_app, name="mk-telegram",
                 help="Telegram: remote commander bot")

    from src.cli.tools_browse_collab_commands import tools_app, browse_app, collab_app
    mk.add_typer(tools_app, name="mk-tools",
                 help="Tools: dynamic tool registry & discovery")
    mk.add_typer(browse_app, name="mk-browse",
                 help="Browse: web automation & page analysis")
    mk.add_typer(collab_app, name="mk-collab",
                 help="Collab: multi-agent collaboration & debate")

    # SDLC scaffold sub-apps
    from src.cli.sdlc.spec import spec_app
    mk.add_typer(spec_app, name="mk-spec",
                 help="Spec phase: feature request → requirements")
    from src.cli.sdlc.design import design_app
    mk.add_typer(design_app, name="mk-design",
                 help="Design phase: requirements → architecture")
    from src.cli.sdlc.code import code_app
    mk.add_typer(code_app, name="mk-code",
                 help="Code phase: architecture → task backlog")
    from src.cli.sdlc.deploy import deploy_app
    mk.add_typer(deploy_app, name="mk-deploy",
                 help="Deploy phase: verify gates → ship/hold")

    # Flat command groups
    from src.cli.cook_command import register_cook_command
    register_cook_command(mk)  # registers cook-auto, cook-auto-parallel, cook

    from src.cli.workflow_commands import register_workflow_commands
    register_workflow_commands(mk)  # registers plan, ask, debug, init, list, search, run, ui

    from src.cli.recipe_commands import register_recipe_commands
    register_recipe_commands(mk)

    from src.cli.system_commands import register_system_commands
    register_system_commands(mk)

    from src.cli.studio_commands import register_studio_commands
    register_studio_commands(mk)

    # Phase-03 signals commands
    from src.cli.commands.metrics import register as register_metrics
    register_metrics(mk)
    from src.cli.commands.algo_status import register as register_algo_status
    register_algo_status(mk)
    from src.cli.commands.eval_agent import register as register_eval_agent
    register_eval_agent(mk)

    # Other flat command groups
    from src.commands.core_commands import app as core_app
    mk.add_typer(core_app, name="mk-core",
                 help="Core CLI commands")

    from src.commands.license_commands import app as license_app
    mk.add_typer(license_app, name="mk-license",
                 help="RaaS License Management")

    from src.commands.status import app as status_app
    mk.add_typer(status_app, name="mk-status",
                 help="System health & API status")

    from src.commands.config import app as config_app
    mk.add_typer(config_app, name="mk-config",
                 help="Manage environment variables and API keys")

    from src.commands.doctor import app as doctor_app
    mk.add_typer(doctor_app, name="mk-doctor",
                 help="Diagnostic tool - check system requirements")

    from src.commands.clean import app as clean_app
    mk.add_typer(clean_app, name="mk-clean",
                 help="Clean cache, temp files, build artifacts")

    from src.commands.test import app as test_app
    mk.add_typer(test_app, name="mk-test",
                 help="Run tests with various options")

    from src.commands.build import app as build_app
    mk.add_typer(build_app, name="mk-build",
                 help="Build project with various options")

    from src.commands.deploy import app as deploy_cli_app
    mk.add_typer(deploy_cli_app, name="mk-deploy-cli",
                 help="Deploy applications to various platforms")

    from src.commands.lint import app as lint_app
    mk.add_typer(lint_app, name="mk-lint",
                 help="Static analysis and code quality checks")

    from src.commands.docs import app as docs_app
    mk.add_typer(docs_app, name="mk-docs",
                 help="Generate, serve, and manage documentation")

    from src.commands.monitor import app as monitor_app
    mk.add_typer(monitor_app, name="mk-monitor",
                 help="Monitor system resources, performance, and application health")

    from src.commands.security import app as security_app
    mk.add_typer(security_app, name="mk-security",
                 help="Audit, scan, and secure applications")

    from src.commands.ci import app as ci_app
    mk.add_typer(ci_app, name="mk-ci",
                 help="CI/CD pipeline management")

    from src.commands.env import app as env_app
    mk.add_typer(env_app, name="mk-env",
                 help="Environment management")

    from src.commands.test_advanced import app as test_advanced_app
    mk.add_typer(test_advanced_app, name="mk-test-advanced",
                 help="Advanced testing strategies")

    from src.commands.usage_commands import app as usage_app
    mk.add_typer(usage_app, name="mk-usage",
                 help="Usage metering: track CLI command usage per license key")

    from src.commands.analytics_show_commands import app as analytics_show_app
    mk.add_typer(analytics_show_app, name="mk-analytics",
                 help="ROI analytics: time savings, cost analysis, ROI metrics")

    from src.commands.sync_raas_commands import app as sync_raas_app
    mk.add_typer(sync_raas_app, name="mk-sync-raas",
                 help="RaaS Gateway synchronization: validate, register, track usage")

    from src.commands.auth_commands import app as auth_app
    mk.add_typer(auth_app, name="mk-auth",
                 help="Authentication: login, logout, status, verify")

    from src.commands.ocop_commands import app as ocop_app
    mk.add_typer(ocop_app, name="mk-ocop",
                 help="OCOP: AI-powered agricultural export tools")

    # Platform sub-app + top-level aliases
    from src.cli.platform_commands import (
        app as platform_app,
        platform_up, platform_down, platform_ps,
        platform_logs, platform_restart,
    )
    mk.add_typer(platform_app, name="mk-platform",
                 help="Platform: start/stop/monitor services")
    mk.command("mk-up")(platform_up)
    mk.command("mk-down")(platform_down)
    mk.command("mk-ps")(platform_ps)
    mk.command("mk-logs")(platform_logs)
    mk.command("mk-restart")(platform_restart)

    # Heartbeat / Daemon
    from src.cli.schedule_commands import app as heartbeat_app
    mk.add_typer(heartbeat_app, name="mk-heartbeat",
                 help="HEARTBEAT: schedule tasks from HEARTBEAT.md")

    from src.cli.daemon_commands import app as daemon_app
    mk.add_typer(daemon_app, name="mk-daemon",
                 help="Daemon: monitor and manage daemon army")

    from src.cli.csuite_commands import register_csuite_commands
    register_csuite_commands(mk)

    return mk

