# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

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


_BPHAP_HELP = "Binh Phap Strategy: Infinite loops & Standards"
_IDEA_HELP = "Idea pipeline: validate -> BMC -> PRD -> execution handoff"


def build_app() -> typer.Typer:
    """Create and return the fully wired Mekong CLI Typer app."""
    # Sub-app imports
    from src.cli.autonomous_commands import autonomous_app, telegram_app
    from src.cli.billing_commands import app as billing_app
    from src.cli.binh_phap_commands import app as binh_phap_app
    from src.cli.pev_commands import pev_app
    from src.cli.usage_commands import app as usage_app

    # Phase-02: build CLI surface (mekong build from-plan)
    from src.cli.commands.build import app as build_app

    # Phase-01: company-init CLI surface (mekong company init | reset | status)
    from src.cli.commands.company_init import app as company_app
    from src.cli.commands.doctor_command import register as register_doctor
    from src.cli.commands.eval_agent import register as register_eval_agent
    from src.cli.commands.harness_eval_command import register_harness_eval_command

    # Phase-02: founder genome assessment (mekong founder assess | review | list)
    from src.cli.commands.founder import founder_app

    # Phase-03 flat commands (signals loop)
    from src.cli.commands.metrics import register as register_metrics

    # Phase-01: AI Cell runtime (mekong cell run)
    from src.cli.commands.particle_cell import cell_app

    # Phase-04: particle graph CLI surface (mekong particle graph)
    from src.cli.commands.particle_graph import graph_app

    # Phase-03: particle init CLI surface (mekong particle init)
    from src.cli.commands.particle_init import particle_app

    # Phase-06: particle zenpay CLI surface (mekong particle zenpay)
    from src.cli.commands.particle_zenpay import zenpay_app

    # Phase-02: plan CLI surface (mekong plan from-init)
    from src.cli.commands.plan import app as plan_app

    # Flat command group registrations
    from src.cli.cook_command import register_cook_command
    from src.cli.goal_commands import goal_app as goal_app
    from src.cli.idea_commands import app as idea_app
    from src.cli.memory_commands import memory_app
    from src.cli.recipe_commands import register_recipe_commands
    from src.cli.commands.init_command import register_init_command
    from src.cli.commands.palette_command import register_palette_command
    from src.cli.commands.tui_command import register_tui_command
    from src.cli.commands.benchmark_command import register_benchmark_command
    from src.cli.commands.gateway_command import register_gateway_command
    from src.cli.commands.watch_command import register_watch_command
    from src.cli.commands.package_command import register_package_command
    from src.cli.commands.sandbox_command import register_sandbox_command
    from src.cli.commands.consensus_command import register_consensus_command
    from src.cli.commands.recall_command import register_recall_command, register_memory_mesh_command
    from src.cli.commands.telemetry_command import register_telemetry_command
    from src.cli.commands.queue_command import register_queue_command
    from src.cli.commands.pipeline_command import register_pipeline_command
    from src.cli.commands.worktree_command import register_worktree_command
    from src.cli.commands.ship_command import register_ship_command
    from src.cli.commands.daily_command import register_daily_command
    from src.cli.commands.quick_start_command import register_quick_start_command
    from src.cli.commands.cto_command import register_cto_command
    from src.cli.commands.sales_command import register_sales_command
    from src.cli.commands.marketing_command import register_marketing_command
    from src.cli.commands.dev_command import register_dev_command
    from src.cli.commands.ops_command import register_ops_command
    from src.cli.commands.support_command import register_support_command
    from src.cli.commands.consulting_command import register_consulting_command
    from src.cli.commands.revenue_command import register_revenue_command
    from src.cli.commands.content_command import register_content_command
    from src.cli.commands.copywriting_command import register_copywriting_command
    from src.cli.schedule_commands import schedule_app
    from src.cli.sdlc.code import code_app
    from src.cli.sdlc.deploy import deploy_app
    from src.cli.sdlc.design import design_app

    # SDD sub-apps (spec-kit port)
    from src.cli.commands.specify import specify_app
    from src.cli.commands.tasks import tasks_app
    from src.cli.commands.implement import implement_app
    from src.cli.commands.analyze import analyze_app

    # SDLC scaffold sub-apps (phase-04)
    from src.cli.sdlc.spec import spec_app
    from src.cli.commands.swarm_orchestration import register_swarm_commands
    from src.cli.system_commands import register_system_commands
    from src.cli.tools_browse_collab_commands import (
        browse_app,
        collab_app,
        tools_app,
    )
    from src.cli.workflow_commands import register_workflow_commands
    from src.cli.csuite_commands import register_csuite_commands  # noqa: E402
    from src.commands.agi import app as agi_app

    # BMAD uses dash naming -- not importable as standard package.
    # bmad-commands imports the optional packages.* tree; when that tree is
    # absent or its namespace package state is unusable, degrade to an empty
    # group instead of crashing build_app().
    spec = importlib.util.spec_from_file_location(
        "bmad_commands",
        Path(__file__).parent / "bmad-commands.py",
    )
    bmad_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(bmad_module)
        bmad_app = bmad_module.app
    except (ImportError, KeyError):
        bmad_app = typer.Typer(name="bmad", help="BMAD workflow management")

    root = typer.Typer(
        name="mekong",
        help="🚀 Mekong CLI: RaaS Agency Operating System",
        add_completion=False,
    )

    # Wire sub-apps
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

    # Register C-suite commands directly on root (no mk- prefix)
    register_csuite_commands(root)

    # Wire SDD sub-apps (spec-kit port)
    root.add_typer(
        specify_app,
        name="specify",
        help="SDD: generate feature spec from template",
    )
    root.add_typer(
        tasks_app,
        name="tasks",
        help="SDD: generate TDD task list from spec",
    )
    root.add_typer(
        implement_app,
        name="implement",
        help="SDD: execute implementation from task list",
    )
    root.add_typer(
        analyze_app,
        name="analyze",
        help="SDD: cross-artifact consistency check",
    )

    # Wire SDLC scaffold sub-apps (phase-04)
    root.add_typer(spec_app, name="spec", help="Spec phase: feature request -> requirements")
    root.add_typer(design_app, name="design", help="Design phase: requirements -> architecture")
    root.add_typer(code_app, name="code", help="Code phase: architecture -> task backlog")
    root.add_typer(deploy_app, name="deploy", help="Deploy phase: verify gates -> ship/hold")

    # Phase-05: design intelligence sub-app (Hallmark verbs, MIT).
    # `design` is taken by the SDLC design phase, so the design-intelligence
    # verbs live under `ui` (audit/study/redesign/build/benchmark).
    from src.cli.ui_commands import register_ui_commands  # noqa: E402

    register_ui_commands(root)

    # Register flat command groups
    register_cook_command(root)
    register_workflow_commands(root)
    register_recipe_commands(root)
    register_init_command(root)
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

    from src.commands.run import register_run_command  # noqa: E402
    register_run_command(root)

    # Vietnam funnel commands — reconnects Zalo OA, tax, accounting, and BHXH to the
    # binary (previously reachable only via `python -m`).
    from src.cli.funnel_commands import (  # noqa: E402
        bhxh_app,
        ke_toan_app,
        thue_app,
        vietqr_app,
        zalo_app,
    )

    root.add_typer(
        company_app,
        name="company",
        help="Company / workspace configuration",
    )

    # Vietnam funnel commands (gap #10) — reconnects Zalo OA, tax, and
    # accounting to the binary. Previously reachable only via `python -m`.
    root.add_typer(
        zalo_app,
        name="zalo-oa",
        help="Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài",
    )
    root.add_typer(
        thue_app,
        name="thue",
        help="Thuế VN — TNCN lũy tiến, TNDN, GTGT (offline)",
    )
    root.add_typer(
        ke_toan_app,
        name="ke-toan",
        help="Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML",
    )
    root.add_typer(
        bhxh_app,
        name="bhxh",
        help="Bảo hiểm xã hội VN — BHXH, BHYT, BHTN, hồ sơ D02-LT (NĐ 73/2024)",
    )
    from src.commands.ocop_commands import app as ocop_app  # noqa: E402
    root.add_typer(
        ocop_app,
        name="ocop",
        help="OCOP — nông sản Việt Nam, xếp hạng sao OCOP & xuất khẩu",
    )
    root.add_typer(
        vietqr_app,
        name="vietqr",
        help="VietQR — thanh toán chuyển khoản Napas 247, mã QR EMVCo & đối soát",
    )
    from src.cli.commands.audit_command import audit_app  # noqa: E402
    root.add_typer(
        audit_app,
        name="audit",
        help="Audit — Enterprise SOX 404, ITGC & COSO internal controls audit engine",
    )
    from src.cli.commands.payroll_command import payroll_app  # noqa: E402
    root.add_typer(
        payroll_app,
        name="payroll",
        help="Payroll — Vietnamese statutory payroll, Gross-to-Net & compensation engine",
    )
    from src.cli.commands.corporate_command import corporate_app  # noqa: E402
    root.add_typer(
        corporate_app,
        name="corporate",
        help="Corporate — Vietnamese corporate governance, incorporation & statutory legal filings",
    )
    from src.cli.commands.fdi_command import fdi_app  # noqa: E402
    root.add_typer(
        fdi_app,
        name="fdi",
        help="FDI — Foreign Direct Investment & SBV capital compliance engine",
    )
    from src.cli.commands.ip_command import ip_app  # noqa: E402
    root.add_typer(
        ip_app,
        name="ip",
        help="IP — Intellectual Property, Trademarks, Patents & Software Copyright",
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
        help="Founder genome assessment -- personality, risk, bias profiling",
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
        help="Behavior graph -- trust & collusion detection",
    )

    # Phase-01: AI Cell runtime sub-app (mekong cell run ...)
    particle_app.add_typer(
        cell_app,
        name="cell",
        help="AI Cell Runtime Engine -- execute and audit autonomous cells",
    )

    # Phase-06: Constitutional Treasury sub-app (mekong particle zenpay ...)
    particle_app.add_typer(
        zenpay_app,
        name="zenpay",
        help="Constitutional Treasury -- record transactions and manage budgets",
    )

    # Phase-03 signals commands (metrics + offline evals)
    register_metrics(root)
    register_eval_agent(root)
    # Phase-F kickoff: ZenOS Commons governance CLI surface (amend / vote / tally)
    from src.cli.governance_commands import register as register_governance  # noqa: E402
    register_governance(root)

   # Step 7 Phase B: domain-agent CLI surface (mekong agent list | run | info)
    from src.cli.commands.agent_commands import register_agent_commands  # noqa: E402
    register_agent_commands(root)

    # Plugin CLI surface (mekong plugin init|install|list|uninstall)
    from src.cli.commands.plugin_install import register_plugin_commands  # noqa: E402
    register_plugin_commands(root)

    # Phase-??: plugin marketplace + vendor CLI surface
    from src.cli.commands.marketplace_commands import register as register_marketplace # noqa: E402
    from src.cli.commands.vendor_marketplace import register as register_vendor # noqa: E402
    register_marketplace(root)
    register_vendor(root)

    # E4d: bind loaded plugin commands into Typer root (mekong <plugin-id> <cmd>)
    from src.cli.plugin_integration import bind_plugin_commands  # noqa: E402
    from src.core.plugin_runtime import PluginRuntime  # noqa: E402
    _plugin_runtime = PluginRuntime()
    _plugin_runtime.load_all()
    bind_plugin_commands(root, _plugin_runtime)

    return root
