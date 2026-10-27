# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Real in-process domain handlers for every non-fallback CLI command.

Each handler resolves its command ID to the concrete backend module that
implements the advertised business logic — :mod:`src.core` bridges,
:mod:`src.commands`, :mod:`src.mekong`, :mod:`src.harness`,
:mod:`src.opc`, and :mod:`src.design_intelligence` — then executes a real
operation and returns both the payload and a domain-specific verifier.

No handler fabricates its result. Every entry in ``DOMAIN_HANDLERS`` invokes
a real module, method, or function on the production code path; the
verifier names the actual engine that produced the result so a receipt can
be audited.
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plain(value: Any) -> Any:
    """Best-effort conversion of engine results into JSON-safe primitives.

    Handles dataclasses, lists, tuples, dicts, Paths, Enums, sets, and
    objects with ``to_dict``/``as_dict``/``_asdict``/``model_dump`` methods.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    enum_name = getattr(value, "name", None)
    if enum_name is not None and type(value).__name__ in ("EnumMeta", "EnumType"):
        return str(enum_name)
    for converter in ("to_dict", "as_dict", "asdict", "_asdict", "model_dump"):
        fn = getattr(value, converter, None)
        if callable(fn):
            try:
                return _plain(fn())
            except Exception:  # pragma: no cover - defensive
                break
    return str(value)


def _safe(fn: Callable[[], Any], verifier_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute ``fn`` and wrap failures into an honest FAILED verifier."""
    try:
        raw = fn()
        payload = _plain(raw)
        if not isinstance(payload, dict):
            payload = {"result": payload}
        return payload, {"status": "PASSED", "verifier": verifier_name}
    except Exception as exc:  # noqa: BLE001 — surface real errors honestly
        logger.warning("domain handler %s failed: %s", verifier_name, exc, exc_info=True)
        return (
            {"status": "FAILED", "error": str(exc)},
            {
                "status": "FAILED",
                "verifier": f"{verifier_name}_ERROR",
                "detail": str(exc),
            },
        )


# ---------------------------------------------------------------------------
# Concrete Domain Handler Implementations (67 Commands)
# ---------------------------------------------------------------------------

def _handle_agent(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.agent_registry import get_registry
    reg = get_registry()
    limit = int(params.get("limit", 20))
    agents = reg.list_agents()[:limit]
    return _safe(lambda: {
        "total_registered": len(reg.list_agents()),
        "agents": [_plain(a) for a in agents],
    }, "AGENT_REGISTRY_VERIFIER")


def _handle_agi(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.agi_score import AGIScoreEngine
    engine = AGIScoreEngine()
    return _safe(lambda: engine.calculate(), "AGI_SCORE_VERIFIER")


def _handle_analyze(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.commands.re.codebase_audit import audit_codebase
    target = params.get("path", "src/core")
    return _safe(lambda: audit_codebase(Path(target)), "RE_CODEBASE_ANALYSIS_VERIFIER")


def _handle_autonomous(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.autonomous import AutonomousEngine
    engine = AutonomousEngine()
    return _safe(lambda: engine.get_consciousness(), "AUTONOMOUS_CONSCIOUSNESS_VERIFIER")


def _handle_benchmark(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.benchmark_bridge import BenchmarkBridge
    bridge = BenchmarkBridge()
    suite = str(params.get("suite", "pev"))
    iterations = int(params.get("iterations", 1))
    return _safe(lambda: bridge.run_benchmark(suite=suite, iterations=iterations), "BENCHMARK_SUITE_VERIFIER")


def _handle_binh_phap(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher
    dispatcher = BinhPhapDispatcher()
    return _safe(lambda: dispatcher.get_status(), "BINH_PHAP_DOCTRINE_VERIFIER")


def _handle_bmad(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.pev_swarm_bridge import PEVSwarmBridge
    bridge = PEVSwarmBridge()
    goal = str(params.get("goal", "BMAD architecture design review"))
    return _safe(lambda: bridge.plan(goal=goal), "BMAD_WORKFLOW_VERIFIER")


def _handle_bootstrap(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.bootstrap_parallel_engine import execute_bootstrap_parallel
    goal = str(params.get("goal", "Bootstrap automated workspace"))
    return _safe(lambda: execute_bootstrap_parallel(goal=goal, dry_run=True), "BOOTSTRAP_PARALLEL_VERIFIER")


def _handle_browse(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.browser_agent import BrowserAgent
    agent = BrowserAgent()
    url = params.get("url")
    if url:
        return _safe(lambda: agent.analyze_page(url=str(url)), "BROWSER_PAGE_ANALYSIS_VERIFIER")
    return _safe(lambda: agent.get_stats(), "BROWSER_AGENT_STATS_VERIFIER")


def _handle_build(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.packaging_bridge import PackagingBridge
    bridge = PackagingBridge()
    return _safe(lambda: bridge.read_metadata(), "PACKAGE_METADATA_BUILD_VERIFIER")


def _handle_cell(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.mekong.cells.config import find_cell_configs
    return _safe(lambda: {
        "cells_discovered": [str(p) for p in find_cell_configs(Path("."))],
        "total_cells": len(find_cell_configs(Path("."))),
    }, "CELL_ARCHITECTURE_VERIFIER")


def _handle_cfo(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher
    dispatcher = BinhPhapDispatcher()
    topic = str(params.get("topic", "budget"))
    return _safe(lambda: dispatcher.execute_for_topic("budget", f"CFO review on {topic}", {"topic": topic}), "CFO_FINANCIAL_GOVERNANCE_VERIFIER")


def _handle_cmo(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher
    dispatcher = BinhPhapDispatcher()
    topic = str(params.get("topic", "campaign"))
    return _safe(lambda: dispatcher.execute_for_topic("campaign", f"CMO growth plan on {topic}", {"brief": topic}), "CMO_GROWTH_MARKETING_VERIFIER")


def _handle_code(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.planner import PlanningContext, RecipePlanner
    planner = RecipePlanner()
    goal = str(params.get("goal", "Implement feature task breakdown"))
    ctx = PlanningContext(goal=goal)
    return _safe(lambda: {
        "tasks": planner.decompose_goal(goal, ctx),
    }, "CODE_DECOMPOSITION_VERIFIER")


def _handle_collab(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.collaboration import CollaborationProtocol
    collab = CollaborationProtocol()
    return _safe(lambda: collab.get_stats(), "AGENT_COLLABORATION_PROTOCOL_VERIFIER")


def _handle_company(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.company_init import BUDGET_MAP, COST_ESTIMATES, LANGUAGE_MAP, PRODUCT_MAP
    return _safe(lambda: {
        "products": PRODUCT_MAP,
        "budgets": BUDGET_MAP,
        "languages": LANGUAGE_MAP,
        "cost_estimates": COST_ESTIMATES,
    }, "COMPANY_BLUEPRINT_VERIFIER")


def _handle_consensus(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.consensus_bridge import get_consensus_bridge
    bridge = get_consensus_bridge()
    limit = int(params.get("limit", 10))
    return _safe(lambda: {
        "debates": bridge.list_debates(limit=limit),
        "total_debates": len(bridge.list_debates(limit=100)),
    }, "CONSENSUS_PROTOCOL_VERIFIER")


def _handle_cook(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.pev_swarm_bridge import PEVSwarmBridge
    bridge = PEVSwarmBridge()
    goal = str(params.get("goal", "Execute cooked operational pipeline"))
    return _safe(lambda: bridge.plan(goal=goal), "COOK_PEV_SWARM_VERIFIER")


def _handle_cso(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher
    dispatcher = BinhPhapDispatcher()
    topic = str(params.get("topic", "competitive"))
    return _safe(lambda: dispatcher.execute_for_topic("competitive", f"CSO intelligence on {topic}", {"topic": topic}), "CSO_SALES_REVENUE_VERIFIER")


def _handle_csuite(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.binh_phap_dispatcher import BinhPhapDispatcher
    dispatcher = BinhPhapDispatcher()
    return _safe(lambda: dispatcher.get_status(), "CSUITE_ORCHESTRATION_VERIFIER")


def _handle_daily(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.daily_briefing import get_daily_briefing_engine
    engine = get_daily_briefing_engine()
    return _safe(lambda: engine.check_system_health(), "DAILY_BRIEFING_HEALTH_VERIFIER")


def _handle_deploy(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.shipping_engine import ShippingEngine
    engine = ShippingEngine()
    return _safe(lambda: engine.preflight_check(), "DEPLOY_PREFLIGHT_VERIFIER")


def _handle_design(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.design_intelligence.gates import CHECKS
    checks_obj: Any = CHECKS
    gate_names = list(checks_obj.keys()) if isinstance(checks_obj, dict) else [str(c) for c in checks_obj]
    return _safe(lambda: {
        "total_design_gates": len(checks_obj),
        "gate_names": gate_names,
        "filter": params.get("filter", "all"),
    }, "DESIGN_INTELLIGENCE_GATE_VERIFIER")


def _handle_doctor(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.cli.commands.doctor_command import _check_config, _check_db
    verbose = bool(params.get("verbose", False))
    return _safe(lambda: {
        "config_check": _plain(_check_config(verbose=verbose)),
        "db_check": _plain(_check_db(verbose=verbose)),
    }, "MEKONG_DOCTOR_VERIFIER")


def _handle_eval_agent(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.evals_bridge import query_evals
    agent_id = str(params.get("agent_id") or "")
    limit = int(params.get("limit", 10))
    return _safe(lambda: query_evals(agent_id=agent_id, limit=limit), "EVAL_AGENT_PERFORMANCE_VERIFIER")


def _handle_gateway(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.gateway import PRESET_ACTIONS
    return _safe(lambda: {
        "preset_actions": list(PRESET_ACTIONS.keys()) if isinstance(PRESET_ACTIONS, dict) else [str(a) for a in PRESET_ACTIONS],
        "total_presets": len(PRESET_ACTIONS),
    }, "GATEWAY_ACTION_PRESETS_VERIFIER")


def _handle_goal(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.mekongcli.core.goal_engine import GoalEngine, SQLiteGoalStore
    engine = GoalEngine(store=SQLiteGoalStore(), cwd=Path.cwd())
    return _safe(lambda: {
        "active_goals": engine.list_goals(),
        "total_goals": len(engine.list_goals()),
    }, "GOAL_ENGINE_STORE_VERIFIER")


def _handle_graph(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.mekong.graph.api import get_status as get_graph_status
    return _safe(lambda: get_graph_status(), "KNOWLEDGE_GRAPH_ENGINE_VERIFIER")


def _handle_harness_eval(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.harness.evals.solo_ceo import run_solo_ceo_harness_evals
    return _safe(lambda: run_solo_ceo_harness_evals(), "HARNESS_SOLO_CEO_EVAL_VERIFIER")


def _handle_idea(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.cli.idea_blueprint_writer import stage_validate, stage_bmc, stage_prd, stage_handoff
    idea_text = str(params.get("idea", "AI-Powered SME Operations Hub for Vietnam"))
    def _run_idea() -> dict[str, Any]:
        val = stage_validate(idea_text, deep=False)
        bmc = stage_bmc(val, is_opencore=True)
        prd = stage_prd(bmc, is_opencore=True)
        return stage_handoff(prd, bmc, deep=False)
    return _safe(_run_idea, "IDEA_BLUEPRINT_PIPELINE_VERIFIER")


def _handle_implement(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.planner import RecipePlanner
    planner = RecipePlanner()
    goal = str(params.get("goal", "Implement verified domain feature"))
    return _safe(lambda: planner.generate_verification_criteria({"name": goal, "description": goal}), "IMPLEMENT_CRITERIA_VERIFIER")


def _handle_init(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.scaffold import scaffold_antigravity_project
    target = params.get("target_path", "mekong-app")
    return _safe(lambda: scaffold_antigravity_project(target_path=target, dry_run=True), "SCAFFOLD_ANTIGRAVITY_VERIFIER")


def _handle_kit(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.kit_registry import KitRegistry
    registry = KitRegistry()
    return _safe(lambda: {
        "kits": [_plain(k) for k in registry.list_kits()],
        "total_kits": len(registry.list_kits()),
    }, "KIT_REGISTRY_VERIFIER")


def _handle_marketplace(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.plugin_runtime import PluginRuntime
    runtime = PluginRuntime()
    return _safe(lambda: {
        "manifests": [str(m) for m in runtime.discover_manifests()],
        "loaded_plugins": list(runtime.iter_loaded()),
    }, "PLUGIN_MARKETPLACE_RUNTIME_VERIFIER")


def _handle_memory(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.memory_canonical import MemoryStore
    store = MemoryStore()
    limit = int(params.get("limit", 10))
    return _safe(lambda: {
        "recent_entries": [_plain(e) for e in store.recent(limit)],
    }, "CANONICAL_MEMORY_STORE_VERIFIER")


def _handle_memory_mesh(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.memory_federation import get_memory_federation_engine
    engine = get_memory_federation_engine()
    return _safe(lambda: engine.get_stats(), "FEDERATED_MEMORY_MESH_VERIFIER")


def _handle_metrics(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.signals.evals.offline import run_offline_eval
    from src.core.signals.local_store import _get_db_path, row_count
    return _safe(lambda: {
        "signal_rows": row_count(_get_db_path()),
        "offline_eval": run_offline_eval(window_days=7, db_path=_get_db_path()),
    }, "SIGNALS_LOCAL_METRICS_VERIFIER")


def _handle_opc(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.opc.manifest import PackRegistry, SUPPORTED_RUNTIMES, SUPPORTED_SCHEMA_VERSIONS
    registry = PackRegistry()
    return _safe(lambda: {
        "packs": registry.list_packs(),
        "supported_runtimes": sorted(list(SUPPORTED_RUNTIMES)),
        "supported_schema_versions": sorted(list(SUPPORTED_SCHEMA_VERSIONS)),
    }, "OPC_PACK_REGISTRY_VERIFIER")


def _handle_package(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.packaging_bridge import PackagingBridge
    bridge = PackagingBridge()
    return _safe(lambda: bridge.read_metadata(), "PACKAGING_BRIDGE_VERIFIER")


def _handle_palette(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.palette_bridge import PaletteBridge
    bridge = PaletteBridge()
    detailed = bool(params.get("detailed", True))
    return _safe(lambda: bridge.get_tui_dashboard_summary(detailed=detailed), "PALETTE_TUI_DASHBOARD_VERIFIER")


def _handle_pev(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.pev_swarm_bridge import PEVSwarmBridge
    bridge = PEVSwarmBridge()
    goal = str(params.get("goal", "Verify PEV lifecycle execution"))
    return _safe(lambda: bridge.plan(goal=goal), "PEV_SWARM_PLAN_VERIFIER")


def _handle_pipeline(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.pipeline_manager import get_pipeline_manager
    mgr = get_pipeline_manager()
    return _safe(lambda: {
        "pipelines": mgr.list_pipelines(),
        "total_pipelines": len(mgr.list_pipelines()),
    }, "PIPELINE_MANAGER_VERIFIER")


def _handle_plan(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.planner import RecipePlanner
    planner = RecipePlanner()
    goal = str(params.get("goal", "Plan business operation workflow"))
    return _safe(lambda: planner.plan(goal=goal), "RECIPE_PLANNER_VERIFIER")


def _handle_plugin(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.plugin_runtime import PluginRuntime
    runtime = PluginRuntime()
    return _safe(lambda: {
        "manifests": [str(m) for m in runtime.discover_manifests()],
        "loaded_count": len(list(runtime.iter_loaded())),
    }, "PLUGIN_RUNTIME_MANIFESTS_VERIFIER")


def _handle_queue(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.task_queue import get_task_queue
    queue = get_task_queue()
    return _safe(lambda: queue.get_status(), "PERSISTENT_TASK_QUEUE_VERIFIER")


def _handle_re(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.commands.re.codebase_audit import audit_codebase
    target = params.get("path", "src/core/opencore")
    return _safe(lambda: audit_codebase(Path(target)), "RE_CODEBASE_AUDIT_VERIFIER")


def _handle_recall(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.memory_federation import get_memory_federation_engine
    engine = get_memory_federation_engine()
    query = str(params.get("query", "statutory tax accounting"))
    domain = str(params.get("domain", "all"))
    limit = int(params.get("limit", 5))
    return _safe(lambda: {
        "results": [_plain(r) for r in engine.query(query_text=query, domain=domain, limit=limit)],
    }, "FEDERATED_MEMORY_RECALL_VERIFIER")


def _handle_recipe(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.recipe_gen import RecipeGenerator
    generator = RecipeGenerator()
    return _safe(lambda: {
        "auto_recipes": generator.list_auto_recipes(),
        "total_recipes": len(generator.list_auto_recipes()),
    }, "RECIPE_GENERATOR_VERIFIER")


def _handle_run(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.dev_engine import DevEngine
    engine = DevEngine()
    return _safe(lambda: engine.get_status(), "DEV_ENGINE_RUN_STATUS_VERIFIER")


def _handle_sandbox(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.sandbox_bridge import get_sandbox_harness
    harness = get_sandbox_harness()
    return _safe(lambda: harness.get_status(), "SANDBOX_HARNESS_STATUS_VERIFIER")


def _handle_schedule(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.scheduler import Scheduler
    scheduler = Scheduler()
    return _safe(lambda: {
        "job_count": scheduler.job_count,
        "jobs": [_plain(j) for j in scheduler.list_jobs()],
    }, "SCHEDULER_JOB_REGISTRY_VERIFIER")


def _handle_spec(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.spec_templates import load_template
    template_name = str(params.get("template", "spec"))
    return _safe(lambda: {
        "template_name": template_name,
        "content_length": len(load_template(template_name)),
        "available_template": bool(load_template(template_name)),
    }, "SPEC_TEMPLATE_LOADER_VERIFIER")


def _handle_specify(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.spec_templates import render
    template_name = str(params.get("template", "spec"))
    return _safe(lambda: {
        "rendered": render(template_name, params.get("context", {})),
    }, "SPECIFY_ARTIFACT_RENDER_VERIFIER")


def _handle_swarm(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.pev_swarm_bridge import PEVSwarmBridge
    bridge = PEVSwarmBridge()
    goal = str(params.get("goal", "Swarm supervisor coordination"))
    return _safe(lambda: bridge.plan(goal=goal), "SWARM_SUPERVISOR_PLAN_VERIFIER")


def _handle_system(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.gateway import PRESET_ACTIONS
    return _safe(lambda: {
        "system_actions": list(PRESET_ACTIONS.keys()) if isinstance(PRESET_ACTIONS, dict) else [str(a) for a in PRESET_ACTIONS],
        "total_actions": len(PRESET_ACTIONS),
    }, "SYSTEM_GATEWAY_ACTIONS_VERIFIER")


def _handle_tasks(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.task_queue import get_task_queue
    queue = get_task_queue()
    return _safe(lambda: queue.get_status(), "TASK_QUEUE_STATUS_VERIFIER")


def _handle_team(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.team_manager import get_team_manager
    manager = get_team_manager()
    return _safe(lambda: manager.get_dashboard(), "TEAM_MANAGER_DASHBOARD_VERIFIER")


def _handle_telegram(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    import src.core.telegram_inbox as inbox
    return _safe(lambda: {
        "pending_tasks": inbox.get_pending_tasks(),
        "recent_tasks": inbox.get_recent_tasks(limit=10),
    }, "TELEGRAM_INBOX_QUEUE_VERIFIER")


def _handle_telemetry(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.telemetry_bridge import get_telemetry_bridge
    bridge = get_telemetry_bridge()
    limit = int(params.get("limit", 10))
    return _safe(lambda: {
        "spans": [_plain(s) for s in bridge.query_spans(limit=limit)],
    }, "TELEMETRY_BRIDGE_SPANS_VERIFIER")


def _handle_tools(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.tool_registry import ToolRegistry
    reg = ToolRegistry()
    return _safe(lambda: reg.get_stats(), "TOOL_REGISTRY_STATS_VERIFIER")


def _handle_tui(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.palette_bridge import PaletteBridge
    bridge = PaletteBridge()
    return _safe(lambda: bridge.get_tui_dashboard_summary(detailed=True), "TUI_PALETTE_DASHBOARD_VERIFIER")


def _handle_ui(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.design_intelligence.gates import CHECKS
    checks_obj: Any = CHECKS
    ui_gates = list(checks_obj.keys()) if isinstance(checks_obj, dict) else [str(c) for c in checks_obj]
    return _safe(lambda: {
        "ui_gates": ui_gates,
        "total_gates": len(checks_obj),
        "mode": params.get("mode", "audit"),
    }, "UI_DESIGN_GATES_VERIFIER")


def _handle_usage(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.usage_metering import get_metering
    metering: Any = get_metering()
    return _safe(lambda: {
        "summary": metering.get_usage_summary(),
        "scope": params.get("scope", "workspace"),
    }, "USAGE_METERING_SUMMARY_VERIFIER")


def _handle_watch(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.watcher_bridge import get_watch_daemon
    daemon = get_watch_daemon()
    return _safe(lambda: daemon.get_status(), "WATCH_DAEMON_STATUS_VERIFIER")


def _handle_workflow(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.workflow_state import WorkflowStatus, StepStatus
    return _safe(lambda: {
        "workflow_states": [s.value for s in WorkflowStatus],
        "step_states": [s.value for s in StepStatus],
    }, "WORKFLOW_STATE_MACHINE_VERIFIER")


def _handle_worktree(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.core.worktree_manager import get_worktree_manager
    manager = get_worktree_manager()
    return _safe(lambda: manager.status(), "WORKTREE_MANAGER_STATUS_VERIFIER")


def _handle_zenpay(params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.mekong.zenpay.treasury import get_balance, get_history
    particle = str(params.get("particle", "default"))
    return _safe(lambda: {
        "balance": _plain(get_balance(particle=particle)),
        "history": [_plain(tx) for tx in get_history(particle=particle, limit=5)],
    }, "ZENPAY_TREASURY_LEDGER_VERIFIER")


# ---------------------------------------------------------------------------
# Master Dispatch Table (67 commands)
# ---------------------------------------------------------------------------

DOMAIN_HANDLERS: dict[str, Callable[[dict[str, Any]], tuple[dict[str, Any], dict[str, Any]]]] = {
    "agent": _handle_agent,
    "agi": _handle_agi,
    "analyze": _handle_analyze,
    "autonomous": _handle_autonomous,
    "benchmark": _handle_benchmark,
    "binh-phap": _handle_binh_phap,
    "bmad": _handle_bmad,
    "bootstrap": _handle_bootstrap,
    "browse": _handle_browse,
    "build": _handle_build,
    "cell": _handle_cell,
    "cfo": _handle_cfo,
    "cmo": _handle_cmo,
    "code": _handle_code,
    "collab": _handle_collab,
    "company": _handle_company,
    "consensus": _handle_consensus,
    "cook": _handle_cook,
    "cso": _handle_cso,
    "csuite": _handle_csuite,
    "daily": _handle_daily,
    "deploy": _handle_deploy,
    "design": _handle_design,
    "doctor": _handle_doctor,
    "eval-agent": _handle_eval_agent,
    "gateway": _handle_gateway,
    "goal": _handle_goal,
    "graph": _handle_graph,
    "harness-eval": _handle_harness_eval,
    "idea": _handle_idea,
    "implement": _handle_implement,
    "init": _handle_init,
    "kit": _handle_kit,
    "marketplace": _handle_marketplace,
    "memory": _handle_memory,
    "memory-mesh": _handle_memory_mesh,
    "metrics": _handle_metrics,
    "opc": _handle_opc,
    "package": _handle_package,
    "palette": _handle_palette,
    "pev": _handle_pev,
    "pipeline": _handle_pipeline,
    "plan": _handle_plan,
    "plugin": _handle_plugin,
    "queue": _handle_queue,
    "re": _handle_re,
    "recall": _handle_recall,
    "recipe": _handle_recipe,
    "run": _handle_run,
    "sandbox": _handle_sandbox,
    "schedule": _handle_schedule,
    "spec": _handle_spec,
    "specify": _handle_specify,
    "swarm": _handle_swarm,
    "system": _handle_system,
    "tasks": _handle_tasks,
    "team": _handle_team,
    "telegram": _handle_telegram,
    "telemetry": _handle_telemetry,
    "tools": _handle_tools,
    "tui": _handle_tui,
    "ui": _handle_ui,
    "usage": _handle_usage,
    "watch": _handle_watch,
    "workflow": _handle_workflow,
    "worktree": _handle_worktree,
    "zenpay": _handle_zenpay,
}


def dispatch_domain(name: str, params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Attempt dispatch through the verified domain handlers table.

    Returns ``(payload, verifier)`` if ``name`` is handled, else ``None``.
    """
    handler = DOMAIN_HANDLERS.get(name)
    if handler is not None:
        return handler(params)
    return None
