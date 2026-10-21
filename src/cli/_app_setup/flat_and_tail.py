"""Flat command group and final tail registrations for Mekong CLI."""

from __future__ import annotations

import typer


def register_flat_commands(root: typer.Typer) -> None:
    """Register flat command groups onto root."""
    from src.cli.commands.benchmark_command import register_benchmark_command
    from src.cli.commands.bootstrap_command import register_bootstrap_command
    from src.cli.commands.consensus_command import register_consensus_command
    from src.cli.commands.consulting_command import register_consulting_command
    from src.cli.commands.content_command import register_content_command
    from src.cli.commands.copywriting_command import register_copywriting_command
    from src.cli.commands.cto_command import register_cto_command
    from src.cli.commands.daily_command import register_daily_command
    from src.cli.commands.dev_command import register_dev_command
    from src.cli.commands.fix_command import register_fix_command
    from src.cli.commands.gateway_command import register_gateway_command
    from src.cli.commands.harness_command import register_harness_command
    from src.cli.commands.init_command import register_init_command
    from src.cli.commands.marketing_command import register_marketing_command
    from src.cli.commands.ops_command import register_ops_command
    from src.cli.commands.orchestrate_command import register_orchestrate_command
    from src.cli.commands.package_command import register_package_command
    from src.cli.commands.palette_command import register_palette_command
    from src.cli.commands.pipeline_command import register_pipeline_command
    from src.cli.commands.queue_command import register_queue_command
    from src.cli.commands.quick_start_command import register_quick_start_command
    from src.cli.commands.recall_command import (
        register_memory_mesh_command,
        register_recall_command,
    )
    from src.cli.commands.revenue_command import register_revenue_command
    from src.cli.commands.sales_command import register_sales_command
    from src.cli.commands.sandbox_command import register_sandbox_command
    from src.cli.commands.ship_command import register_ship_command
    from src.cli.commands.support_command import register_support_command
    from src.cli.commands.team_command import register_team_command
    from src.cli.commands.telemetry_command import register_telemetry_command
    from src.cli.commands.tui_command import register_tui_command
    from src.cli.commands.watch_command import register_watch_command
    from src.cli.commands.worktree_command import register_worktree_command
    from src.cli.cook_command import register_cook_command
    from src.cli.recipe_commands import register_recipe_commands
    from src.cli.system_commands import register_system_commands
    from src.cli.workflow_commands import register_workflow_commands
    from src.commands.run import register_run_command

    register_cook_command(root)
    register_orchestrate_command(root)
    register_fix_command(root)
    register_harness_command(root)
    register_workflow_commands(root)
    register_recipe_commands(root)
    register_init_command(root)
    register_bootstrap_command(root)
    register_palette_command(root)
    register_tui_command(root)
    register_benchmark_command(root)
    register_gateway_command(root)
    register_watch_command(root)
    register_package_command(root)
    register_sandbox_command(root)
    register_consensus_command(root)
    register_recall_command(root)
    register_memory_mesh_command(root)
    register_telemetry_command(root)
    register_queue_command(root)
    register_pipeline_command(root)
    register_worktree_command(root)
    register_team_command(root)
    register_ship_command(root)
    register_daily_command(root)
    register_quick_start_command(root)
    register_cto_command(root)
    register_sales_command(root)
    register_marketing_command(root)
    register_dev_command(root)
    register_ops_command(root)
    register_support_command(root)
    register_consulting_command(root)
    register_revenue_command(root)
    register_content_command(root)
    register_copywriting_command(root)
    register_system_commands(root)
    register_run_command(root)


def register_tail_subapps(root: typer.Typer) -> None:
    """Register plan, build, founder, particle, governance, plugin, and pilot groups."""
    from src.cli.commands.agent_commands import register_agent_commands
    from src.cli.commands.build import app as build_app
    from src.cli.commands.eval_agent import register as register_eval_agent
    from src.cli.commands.founder import founder_app
    from src.cli.commands.marketplace_commands import register as register_marketplace
    from src.cli.commands.metrics import register as register_metrics
    from src.cli.commands.particle_cell import cell_app
    from src.cli.commands.particle_graph import graph_app
    from src.cli.commands.particle_init import particle_app
    from src.cli.commands.particle_zenpay import zenpay_app
    from src.cli.commands.plan import app as plan_app
    from src.cli.commands.plugin_install import register_plugin_commands
    from src.cli.commands.vendor_marketplace import register as register_vendor
    from src.cli.governance_commands import register as register_governance
    from src.cli.plugin_integration import bind_plugin_commands
    from src.commands.pilot_command import pilot_app
    from src.core.plugin_runtime import PluginRuntime

    root.add_typer(plan_app, name="plan", help="Plan generation from company init")
    root.add_typer(build_app, name="build", help="Build task generation from spec")
    root.add_typer(
        founder_app,
        name="founder",
        help="Founder genome assessment -- personality, risk, bias profiling",
    )
    root.add_typer(particle_app, name="particle", help="ZenOS particle lifecycle management")
    particle_app.add_typer(graph_app, name="graph", help="Behavior graph -- trust & collusion detection")
    particle_app.add_typer(cell_app, name="cell", help="AI Cell Runtime Engine -- execute and audit autonomous cells")
    particle_app.add_typer(zenpay_app, name="zenpay", help="Constitutional Treasury -- record transactions and manage budgets")

    register_metrics(root)
    register_eval_agent(root)
    register_governance(root)
    register_agent_commands(root)
    register_plugin_commands(root)
    register_marketplace(root)
    register_vendor(root)
    root.add_typer(pilot_app, name="pilot")

    _plugin_runtime = PluginRuntime()
    _plugin_runtime.load_all()
    bind_plugin_commands(root, _plugin_runtime)
