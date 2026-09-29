# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI — MCP Server for AI OS capabilities.

Provides 25 MCP tools wrapping Mekong AI OS core services.
Designed to run as a standalone MCP server (stdio or SSE) or be imported.

Usage:
    python -m src.core.mcp_server                           # stdio mode
    python -m src.core.mcp_server --transport sse --port 8000  # SSE mode
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detect MCP SDK availability
# ---------------------------------------------------------------------------
_HAS_MCP = False
try:
    from mcp.server.fastmcp import FastMCP  # type: ignore[import-untyped]

    _HAS_MCP = True
except ImportError:
    FastMCP = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Core module availability flags (graded — each tool checks its own dependency)
# ---------------------------------------------------------------------------
_HAS_MEMORY = False
_HAS_MEMORY_STORE = False
_HAS_AGENT_REGISTRY = False
_HAS_PLUGIN_REGISTRY = False
_HAS_COST = False
_HAS_ROUTER = False
_HAS_MCP_TASK_STORE = False
_HAS_MCP_PLAN_STORE = False

try:
    from src.core.memory_client import get_memory_provider

    _HAS_MEMORY = True
except ImportError:
    pass

try:
    from src.core.memory_canonical import MemoryStore

    _HAS_MEMORY_STORE = True
except ImportError:
    pass

try:
    from src.core.agent_registry import AgentRegistry

    _HAS_AGENT_REGISTRY = True
except ImportError:
    pass

try:
    from src.core.plugin_registry import PluginRegistry

    _HAS_PLUGIN_REGISTRY = True
except ImportError:
    pass

_HAS_MCU = importlib.util.find_spec("src.core.mcu_gate") is not None
_HAS_COST = importlib.util.find_spec("src.core.cost_estimator") is not None
_HAS_ROUTER = importlib.util.find_spec("src.core.hybrid_router") is not None

try:
    from src.core.mcp_task_store import get_task_store

    _HAS_MCP_TASK_STORE = True
except ImportError:
    _HAS_MCP_TASK_STORE = False

try:
    from src.core.mcp_plan_store import get_plan_store

    _HAS_MCP_PLAN_STORE = True
except ImportError:
    _HAS_MCP_PLAN_STORE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(data: Any) -> str:
    """Wrap result as success JSON."""
    return json.dumps({"ok": True, "data": data}, indent=2, default=str)


def _err(msg: str) -> str:
    """Wrap error as failure JSON."""
    return json.dumps({"ok": False, "error": msg}, indent=2)


def _missing(capability: str) -> str:
    """Return a consistent 'not available' message."""
    return _err(
        f"'{capability}' is not available — the required Mekong core "
        f"module could not be loaded. Install it or run in a full Mekong environment."
    )


def _clean_str(val: Any) -> str | None:
    """Extract stripped string, returning None if empty or not a string."""
    if isinstance(val, str):
        s = val.strip()
        return s if s else None
    return None


# ---------------------------------------------------------------------------
# Lazy singletons (initialised on first use)
# ---------------------------------------------------------------------------
_memory: Any = None
_memory_store: Any = None
_agent_registry: Any = None
_plugin_registry: Any = None


def _get_memory() -> Any:
    """Get or create the memory provider singleton."""
    global _memory
    if _memory is None and _HAS_MEMORY:
        _memory = get_memory_provider()
    return _memory


def _get_memory_store() -> Any:
    """Get or create the memory store singleton."""
    global _memory_store
    if _memory_store is None and _HAS_MEMORY_STORE:
        _memory_store = MemoryStore()
    return _memory_store


def _get_agent_registry() -> Any:
    """Get or create the agent registry singleton."""
    global _agent_registry
    if _agent_registry is None and _HAS_AGENT_REGISTRY:
        _agent_registry = AgentRegistry()
    return _agent_registry


def _get_plugin_registry() -> Any:
    """Get or create the plugin registry singleton."""
    global _plugin_registry
    if _plugin_registry is None and _HAS_PLUGIN_REGISTRY:
        _plugin_registry = PluginRegistry()
    return _plugin_registry


# ===================================================================
# MekongMcpServer
# ===================================================================


class MekongMcpServer:
    """MCP server exposing Mekong AI OS capabilities as tools.

    Wraps 25 tool handlers that proxy to Mekong core modules with
    graceful degradation when modules are unavailable.

    Usage:
        server = MekongMcpServer()
        app = server.create_app()
        app.run(transport="stdio")
    """

    def __init__(self, name: str = "mekong-ai-os") -> None:
        self.name = name
        self._app: Any = None
        self._tools: list[dict[str, str]] = []

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    def create_app(self) -> Any:
        """Create the FastMCP application with all 25 tools registered.

        Returns:
            FastMCP instance (or raises RuntimeError if mcp SDK missing).

        """
        if not _HAS_MCP:
            msg = (
                "MCP SDK is not installed. Run: pip install mcp"
            )
            raise RuntimeError(msg)

        app: Any = FastMCP(self.name, log_level="ERROR")
        self._register_tools(app)
        self._tools = [
            {"name": t.name, "description": t.description or ""}
            for t in app._tool_manager.list_tools()
        ]
        self._app = app
        return app

    # ------------------------------------------------------------------
    # Runner
    # ------------------------------------------------------------------

    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server.

        Args:
            transport: ``"stdio"`` for stdin/stdout (OpenCode/Claude),
                       ``"sse"`` for HTTP SSE transport (gateway).

        """
        app = self.create_app()
        os.environ["LANG"] = os.environ.get("LANG", "en_US.UTF-8")
        os.environ["TERM"] = os.environ.get("TERM", "xterm-256color")
        app.run(transport=transport)

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def _register_tools(self, app: Any) -> None:
        """Register all 24 MCP tools on the FastMCP instance."""

        # ── Memory ────────────────────────────────────────────────────

        @app.tool(description="Search Mekong AI OS persistent memory")
        def cc_memory_search(query: str, limit: int = 10) -> str:
            return self._handle_memory_search(query, limit)

        @app.tool(description="Consolidate session memories into long-term memory")
        def cc_memory_consolidate() -> str:
            return self._handle_memory_consolidate()

        # ── Tasks ─────────────────────────────────────────────────────

        @app.tool(
            description="List Mekong tasks (omit status for all, or: todo / in-progress / done)"
        )
        def cc_tasks_list(status: str = "") -> str:
            return self._handle_tasks_list(status)

        @app.tool(description="Create a new task with a subject line")
        def cc_tasks_create(subject: str) -> str:
            return self._handle_tasks_create(subject)

        @app.tool(description="Mark a task as done by ID")
        def cc_tasks_done(task_id: str) -> str:
            return self._handle_tasks_done(task_id)

        @app.tool(description="Mark a task as in-progress by ID")
        def cc_tasks_start(task_id: str) -> str:
            return self._handle_tasks_start(task_id)

        @app.tool(description="Delete a task by ID")
        def cc_tasks_delete(task_id: str) -> str:
            return self._handle_tasks_delete(task_id)

        # ── Agents ────────────────────────────────────────────────────

        @app.tool(description="List registered Mekong background agents")
        def cc_agents_list() -> str:
            return self._handle_agents_list()

        @app.tool(
            description="Start an autonomous agent "
            "(research_assistant / auto_bug_fixer / paper_writer / auto_coder)"
        )
        def cc_agents_start(template: str, args: str = "") -> str:
            return self._handle_agents_start(template, args)

        @app.tool(description="Stop a running agent by name")
        def cc_agents_stop(name: str) -> str:
            return self._handle_agents_stop(name)

        # ── Skills ────────────────────────────────────────────────────

        @app.tool(description="List available Mekong skills")
        def cc_skills_list() -> str:
            return self._handle_skills_list()

        # ── MCP System ────────────────────────────────────────────────

        @app.tool(description="List Mekong MCP servers and their tools")
        def cc_mcp_list() -> str:
            return self._handle_mcp_list()

        # ── Plugins ───────────────────────────────────────────────────

        @app.tool(description="List Mekong plugins")
        def cc_plugins_list() -> str:
            return self._handle_plugins_list()

        @app.tool(description="Install a Mekong plugin by name@url")
        def cc_plugins_install(name_url: str) -> str:
            return self._handle_plugins_install(name_url)

        # ── Brainstorm ────────────────────────────────────────────────

        @app.tool(description="Run multi-persona brainstorm on a topic via Mekong")
        def cc_brainstorm(topic: str) -> str:
            return self._handle_brainstorm(topic)

        # ── Research Lab ──────────────────────────────────────────────

        @app.tool(
            description="Start a research lab session on a topic. "
            "Creates a tracked lab session with LLM analysis."
        )
        def cc_lab_start(topic: str) -> str:
            return self._handle_lab_start(topic)

        @app.tool(description="List active and recent research lab sessions")
        def cc_lab_status() -> str:
            return self._handle_lab_status()

        # ── Trading ───────────────────────────────────────────────────

        @app.tool(
            description="Analyze a trading symbol using LLM. "
            "Returns multi-perspective analysis (technical, fundamental, sentiment). "
            "Note: AI-generated analysis, not financial advice."
        )
        def cc_trading_analyze(symbol: str) -> str:
            return self._handle_trading_analyze(symbol)

        @app.tool(
            description="Get LLM-informed analysis for a trading symbol's price context. "
            "Note: AI-generated context, not real-time market data."
        )
        def cc_trading_price(symbol: str) -> str:
            return self._handle_trading_price(symbol)

        # ── Monitor ───────────────────────────────────────────────────

        @app.tool(
            description="Start monitoring a topic or subscription. "
            "Creates a tracked monitor session that periodically checks the topic."
        )
        def cc_monitor_run(topic: str = "") -> str:
            return self._handle_monitor_run(topic)

        @app.tool(description="List active and recent monitor sessions")
        def cc_monitor_status() -> str:
            return self._handle_monitor_status()

        # ── Plan Mode ─────────────────────────────────────────────────

        @app.tool(
            description="Enter plan mode — decomposes a goal into a task tree. "
            "Uses PlanStore for persistence. Returns plan_id and task list."
        )
        def cc_plan_start(description: str) -> str:
            return self._handle_plan_start(description)

        @app.tool(
            description="List saved plans. "
            "Pass status='active' or status='completed' to filter."
        )
        def cc_plan_list(status: str = "") -> str:
            return self._handle_plan_list(status)

        @app.tool(
            description="Mark a plan as done by plan_id. "
            "Sets all remaining tasks to 'done' and closes the plan."
        )
        def cc_plan_done(plan_id: str) -> str:
            return self._handle_plan_done(plan_id)

        # ── SSJ (Developer Power Menu) ────────────────────────────────

        @app.tool(
            description="SSJ Developer Mode — run diagnostics, health check, memory stats, "
            "plugin status, toggle logging, or reload config. "
            "Pass action=all (default) or one of: diagnostics / toggle-logging / reload-config / "
            "health-check / memory-stats / plugin-status"
        )
        def cc_ssj(action: str = "all") -> str:
            return self._handle_ssj(action)

        # ── Command Fabric ────────────────────────────────────────────

        @app.tool(
            description="List universal command fabric manifests for IDEs, agents, and MCP"
        )
        def cc_command_fabric_list(scope: str = "project", adapter: str = "mcp") -> str:
            return self._handle_command_fabric_list(scope=scope, adapter=adapter)

        @app.tool(
            description="Execute or inspect a command through universal command fabric"
        )
        def cc_command_fabric_run(command: str, args: str = "", scope: str = "project") -> str:
            return self._handle_command_fabric_run(command=command, args=args, scope=scope)

        # ── Subagent Bridge ───────────────────────────────────────────

        @app.tool(
            name="mekong_subagent_dispatch",
            description="Dynamic subagent bridge: generates define_subagent and invoke_subagent payloads for Antigravity with HARNESS.md guardrails.",
        )
        def mekong_subagent_dispatch(role: str, task: str, model_tier: str = "inherit") -> str:
            return self._handle_subagent_dispatch(role=role, task=task, model_tier=model_tier)

        # ── PEV & Swarm Autonomous Tools ──────────────────────────────

        @app.tool(
            name="mekong_pev_plan",
            description="Generate structured PEV execution plan, tasks, and subagent assignments from a goal.",
        )
        def mekong_pev_plan(goal: str, mission_id: str = "") -> str:
            return self._handle_pev_plan(goal=goal, mission_id=mission_id)

        @app.tool(
            name="mekong_pev_checkpoint",
            description="Capture atomic SQLite checkpoint of workspace files and task states.",
        )
        def mekong_pev_checkpoint(
            mission_id: str,
            label: str = "manual",
            files: list[str] | None = None,
            test_results: dict[str, Any] | None = None,
        ) -> str:
            return self._handle_pev_checkpoint(
                mission_id=mission_id, label=label, files=files, test_results=test_results
            )

        @app.tool(
            name="mekong_pev_rollback",
            description="Atomically restore workspace files and task states to a specific checkpoint.",
        )
        def mekong_pev_rollback(checkpoint_id: str) -> str:
            return self._handle_pev_rollback(checkpoint_id=checkpoint_id)

        @app.tool(
            name="mekong_swarm_status",
            description="Inspect active multi-agent PEV mission progress, cycles, and health.",
        )
        def mekong_swarm_status(mission_id: str = "") -> str:
            return self._handle_swarm_status(mission_id=mission_id)

        # ── Continuous Learning & Evals ───────────────────────────────

        @app.tool(
            name="mekong_eval_query",
            description="Query offline mission evaluations, p95 durations, failure clusters, and continuous learning recommendations.",
        )
        def mekong_eval_query(agent_id: str = "all", days: int = 7, limit: int = 50) -> str:
            return self._handle_eval_query(agent_id=agent_id, days=days, limit=limit)

        @app.tool(
            name="mekong_recipe_evolve",
            description="Trigger self-improvement and recipe evolution for a goal or recipe based on failure clusters.",
        )
        def mekong_recipe_evolve(recipe_name: str = "", goal: str = "", force: bool = False) -> str:
            return self._handle_recipe_evolve(recipe_name=recipe_name, goal=goal, force=force)

        @app.tool(
            name="mekong_mission_metrics",
            description="Retrieve aggregated telemetry metrics, credit usage, and failure breakdowns across agents.",
        )
        def mekong_mission_metrics(agent_id: str = "all", days: int = 7) -> str:
            return self._handle_mission_metrics(agent_id=agent_id, days=days)

        @app.tool(
            name="mekong_palette_search",
            description="Fuzzy search across Mekong CLI commands, Antigravity skills, and domain subagents using Vietnamese or English natural language.",
        )
        def mekong_palette_search(query: str, category: str = "all", limit: int = 5) -> str:
            return self._handle_palette_search(query=query, category=category, limit=limit)

        @app.tool(
            name="mekong_tui_dashboard_status",
            description="Retrieve real-time telemetry, AGI subsystem health, checkpoints, and system performance summary for the Mekong TUI dashboard.",
        )
        def mekong_tui_dashboard_status(detailed: bool = False) -> str:
            return self._handle_tui_dashboard_status(detailed=detailed)

        @app.tool(
            name="mekong_benchmark_run",
            description="Run autonomous benchmark suites across PEV, checkpoints, subagents, and chaos scenarios.",
        )
        def mekong_benchmark_run(suite: str = "all", iterations: int = 1, chaos_level: str = "none") -> str:
            return self._handle_benchmark_run(suite=suite, iterations=iterations, chaos_level=chaos_level)

        @app.tool(
            name="mekong_chaos_simulate",
            description="Simulate chaos fault injection against checkpoints, tools, or payloads to test self-healing resilience.",
        )
        def mekong_chaos_simulate(target: str = "checkpoint", error_type: str = "corrupt_file") -> str:
            return self._handle_chaos_simulate(target=target, error_type=error_type)

        @app.tool(
            name="mekong_gateway_status",
            description="Query Mekong Gateway server health, uptime, active SSE streams, and system metrics.",
        )
        def mekong_gateway_status() -> str:
            return self._handle_gateway_status()

        @app.tool(
            name="mekong_gateway_rate_limit",
            description="Query tenant rate limit quota, tokens remaining, and reset timestamp.",
        )
        def mekong_gateway_rate_limit(tenant_id: str = "default") -> str:
            return self._handle_gateway_rate_limit(tenant_id=tenant_id)

        @app.tool(
            name="mekong_watch_status",
            description="Query active Mekong file watcher daemon state, monitored directories, recent change events, and repair metrics.",
        )
        def mekong_watch_status() -> str:
            return self._handle_watch_status()

        @app.tool(
            name="mekong_self_repair",
            description="Perform AST syntax diagnostics and automated self-healing repair (or checkpoint rollback) on a file.",
        )
        def mekong_self_repair(file_path: str, error_detail: str = "", mode: str = "auto") -> str:
            return self._handle_self_repair(file_path=file_path, error_detail=error_detail, mode=mode)

        @app.tool(
            name="mekong_package_build",
            description="Build multi-platform distribution packages, Homebrew formulas, and Docker assets.",
        )
        def mekong_package_build(target: str = "all", output_dir: str = "dist") -> str:
            return self._handle_package_build(target=target, output_dir=output_dir)

        @app.tool(
            name="mekong_sandbox_exec",
            description="Execute a shell command inside an isolated container or secure subprocess sandbox.",
        )
        def mekong_sandbox_exec(command: str, timeout: int = 30, memory_limit_mb: int = 512, image: str = "python:3.11-slim") -> str:
            return self._handle_sandbox_exec(command=command, timeout=timeout, memory_limit_mb=memory_limit_mb, image=image)

        @app.tool(
            name="mekong_consensus_vote",
            description="Execute a multi-agent quorum vote on a proposal (majority, supermajority, unanimous, weighted).",
        )
        def mekong_consensus_vote(proposal: str, quorum: str = "majority", agents: list[str] | None = None) -> str:
            return self._handle_consensus_vote(proposal=proposal, quorum=quorum, agents=agents)

        @app.tool(
            name="mekong_consensus_debate",
            description="Conduct a structured multi-round debate between domain roles with synthetic consensus.",
        )
        def mekong_consensus_debate(topic: str, proponent: str = "cto", opponent: str = "sre", moderator: str = "ceo", rounds: int = 2) -> str:
            return self._handle_consensus_debate(topic=topic, proponent=proponent, opponent=opponent, moderator=moderator, rounds=rounds)

        @app.tool(
            name="mekong_semantic_recall",
            description="Perform associative semantic and BM25 search across federated memory domains.",
        )
        def mekong_semantic_recall(query: str, domain: str = "all", limit: int = 5) -> str:
            return self._handle_semantic_recall(query=query, domain=domain, limit=limit)

        @app.tool(
            name="mekong_knowledge_graph_query",
            description="Traverse relational codebase and architectural knowledge graph around an entity.",
        )
        def mekong_knowledge_graph_query(entity: str, depth: int = 2) -> str:
            return self._handle_knowledge_graph_query(entity=entity, depth=depth)

        @app.tool(
            name="mekong_telemetry_metrics",
            description="Export or inspect standard Prometheus exposition metrics or structured JSON.",
        )
        def mekong_telemetry_metrics(format_type: str = "prometheus") -> str:
            return self._handle_telemetry_metrics(format_type=format_type)

        @app.tool(
            name="mekong_trace_query",
            description="Query distributed tracing spans, latency timings, and W3C traceparent headers.",
        )
        def mekong_trace_query(trace_id: str | None = None, limit: int = 20) -> str:
            return self._handle_trace_query(trace_id=trace_id, limit=limit)

        @app.tool(
            name="mekong_queue_enqueue",
            description="Schedule a new task for prioritized execution in the distributed task queue.",
        )
        def mekong_queue_enqueue(name: str, priority: str = "normal", payload: dict | None = None, max_retries: int = 3, delay_sec: float = 0.0) -> str:
            return self._handle_queue_enqueue(name=name, priority=priority, payload=payload, max_retries=max_retries, delay_sec=delay_sec)

        @app.tool(
            name="mekong_queue_status",
            description="Inspect queue depth, active worker leases, and dead-letter counts.",
        )
        def mekong_queue_status() -> str:
            return self._handle_queue_status()

        @app.tool(
            name="mekong_queue_dlq_action",
            description="Inspect, retry, or clear tasks residing in the dead-letter queue.",
        )
        def mekong_queue_dlq_action(action: str = "list", task_id: str | None = None) -> str:
            return self._handle_queue_dlq_action(action=action, task_id=task_id)

        @app.tool(
            name="mekong_pipeline_run",
            description="Run multi-agent sequential pipeline (FilePicker -> Editor -> Reviewer) for software engineering tasks.",
        )
        def mekong_pipeline_run(goal: str, stages: list[str] | None = None) -> str:
            return self._handle_pipeline_run(goal=goal, stages=stages)

        @app.tool(
            name="mekong_pipeline_status",
            description="Inspect status, stage outcomes, and timings for a pipeline execution.",
        )
        def mekong_pipeline_status(pipeline_id: str = "") -> str:
            return self._handle_pipeline_status(pipeline_id=pipeline_id)

        @app.tool(
            name="mekong_worktree_create",
            description="Create a new isolated git worktree branching from the base branch.",
        )
        def mekong_worktree_create(feature: str, prefix: str | None = None, base_branch: str | None = None, no_prefix: bool = False, root: str | None = None, dry_run: bool = False) -> str:
            return self._handle_worktree_create(feature=feature, prefix=prefix, base_branch=base_branch, no_prefix=no_prefix, root=root, dry_run=dry_run)

        @app.tool(
            name="mekong_worktree_list",
            description="List all registered git worktrees in the repository.",
        )
        def mekong_worktree_list() -> str:
            return self._handle_worktree_list()

        @app.tool(
            name="mekong_worktree_status",
            description="Inspect status, uncommitted changes, and divergence against base branch.",
        )
        def mekong_worktree_status(path_or_branch: str | None = None) -> str:
            return self._handle_worktree_status(path_or_branch=path_or_branch)

        @app.tool(
            name="mekong_worktree_remove",
            description="Remove an isolated git worktree workspace.",
        )
        def mekong_worktree_remove(path_or_name: str, force: bool = False) -> str:
            return self._handle_worktree_remove(path_or_name=path_or_name, force=force)

        @app.tool(
            name="mekong_ship_preflight",
            description="Inspect repository topology, branch, remote, and dirty files before shipping.",
        )
        def mekong_ship_preflight() -> str:
            return self._handle_ship_preflight()

        @app.tool(
            name="mekong_ship_run",
            description="Run the production shipping pipeline: lint, test, stage, commit, and push.",
        )
        def mekong_ship_run(message: str = "", run_lint: bool = True, run_tests: bool = True, push: bool = True, dry_run: bool = False) -> str:
            return self._handle_ship_run(message=message, run_lint=run_lint, run_tests=run_tests, push=push, dry_run=dry_run)

        @app.tool(
            name="mekong_daily_report",
            description="Produce an executive daily standup report: git commit velocity, uncommitted files, codebase debt, and mesh queue depth.",
        )
        def mekong_daily_report(since: str = "24 hours ago", include_todos: bool = True) -> str:
            return self._handle_daily_report(since=since, include_todos=include_todos)

        @app.tool(
            name="mekong_daily_focus",
            description="Retrieve prioritized strategic daily focus recommendations synthesized from repository and queue signals.",
        )
        def mekong_daily_focus() -> str:
            return self._handle_daily_focus()

        @app.tool(
            name="mekong_quick_start_plan",
            description="Simulate and retrieve the 5-step project kickoff blueprint, architecture PRD, and milestone checklist without writing files.",
        )
        def mekong_quick_start_plan(project_name: str = "mekong-app", project_type: str = "agent") -> str:
            return self._handle_quick_start_plan(project_name=project_name, project_type=project_type)

        @app.tool(
            name="mekong_quick_start_create",
            description="Execute the end-to-end 5-step project kickoff: brainstorm, plan, scaffold, verify & git commit, and monetization roadmap.",
        )
        def mekong_quick_start_create(project_name: str = "mekong-app", project_type: str = "agent", target_dir: str = "", dry_run: bool = False, init_git: bool = True) -> str:
            return self._handle_quick_start_create(project_name=project_name, project_type=project_type, target_dir=target_dir, dry_run=dry_run, init_git=init_git)

        @app.tool(
            name="mekong_cto_scorecard",
            description="Calculate composite engineering health score, grade, test coverage, and security posture.",
        )
        def mekong_cto_scorecard() -> str:
            return self._handle_cto_scorecard()

        @app.tool(
            name="mekong_cto_review",
            description="Conduct automated code quality, anti-pattern, dynamic execution, and security review.",
        )
        def mekong_cto_review(target_path: str = "") -> str:
            return self._handle_cto_review(target_path=target_path)

        @app.tool(
            name="mekong_cto_architect",
            description="Generate an Architecture Decision Record (ADR) with context, decision, consequences, and alternatives.",
        )
        def mekong_cto_architect(title: str, context: str = "", decision: str = "") -> str:
            return self._handle_cto_architect(title=title, context=context, decision=decision)

        @app.tool(
            name="mekong_sales_pipeline",
            description="Query sales pipeline metrics, weighted revenue forecasts, and opportunities by stage.",
        )
        def mekong_sales_pipeline(stage: str = "") -> str:
            return self._handle_sales_pipeline(stage=stage)

        @app.tool(
            name="mekong_sales_deal_add",
            description="Add a new deal opportunity to the sales pipeline ledger.",
        )
        def mekong_sales_deal_add(name: str, company: str, value: float, stage: str = "lead", email: str = "") -> str:
            return self._handle_sales_deal_add(name=name, company=company, value=value, stage=stage, email=email)

        @app.tool(
            name="mekong_sales_outreach",
            description="Generate tailored multi-channel outreach copy and cadence (email, linkedin, zalo).",
        )
        def mekong_sales_outreach(company: str, persona: str = "CTO", channel: str = "email") -> str:
            return self._handle_sales_outreach(company=company, persona=persona, channel=channel)

        @app.tool(
            name="mekong_marketing_metrics",
            description="Query aggregated marketing metrics, active campaigns, total spend, and conversions.",
        )
        def mekong_marketing_metrics() -> str:
            return self._handle_marketing_metrics()

        @app.tool(
            name="mekong_marketing_campaign_create",
            description="Create and register a promotional or growth marketing campaign.",
        )
        def mekong_marketing_campaign_create(name: str, channel: str = "social", budget: float = 1000.0, target_audience: str = "") -> str:
            return self._handle_marketing_campaign_create(name=name, channel=channel, budget=budget, target_audience=target_audience)

        @app.tool(
            name="mekong_marketing_content_generate",
            description="Synthesize ready-to-use marketing copy and creative with hashtags and call-to-action.",
        )
        def mekong_marketing_content_generate(topic: str, channel: str = "social", content_type: str = "post") -> str:
            return self._handle_marketing_content_generate(topic=topic, channel=channel, content_type=content_type)

        @app.tool(
            name="mekong_dev_audit",
            description="Perform static AST and security audit across the codebase or specific module.",
        )
        def mekong_dev_audit(path: str = "") -> str:
            return self._handle_dev_audit(path=path)

        @app.tool(
            name="mekong_dev_scaffold",
            description="Scaffold a new structured Python module, service, API, or agent with unit tests.",
        )
        def mekong_dev_scaffold(name: str, module_type: str = "service", dry_run: bool = True) -> str:
            return self._handle_dev_scaffold(name=name, module_type=module_type, dry_run=dry_run)

        @app.tool(
            name="mekong_dev_review",
            description="Review working tree git diff for safety, technical debt, and quality hazards.",
        )
        def mekong_dev_review() -> str:
            return self._handle_dev_review()

        @app.tool(
            name="mekong_ops_health_sweep",
            description="Run comprehensive system health audit across runtime, storage, databases, git & configs.",
        )
        def mekong_ops_health_sweep(save_report: bool = False) -> str:
            return self._handle_ops_health_sweep(save_report=save_report)

        @app.tool(
            name="mekong_ops_incident_create",
            description="Create and track a new SRE incident in the operations ledger.",
        )
        def mekong_ops_incident_create(title: str, severity: str = "SEV3", service: str = "core", summary: str = "") -> str:
            return self._handle_ops_incident_create(title=title, severity=severity, service=service, summary=summary)

        @app.tool(
            name="mekong_ops_incident_list",
            description="List tracked SRE incidents filtered by status.",
        )
        def mekong_ops_incident_list(status: str = "ALL") -> str:
            return self._handle_ops_incident_list(status=status)

        @app.tool(
            name="mekong_support_onboard_status",
            description="Query current project onboarding milestones, completed steps, and progress percentage.",
        )
        def mekong_support_onboard_status() -> str:
            return self._handle_support_onboard_status()

        @app.tool(
            name="mekong_support_feedback_submit",
            description="Record customer satisfaction, feedback comments, or Net Promoter Score (NPS).",
        )
        def mekong_support_feedback_submit(nps_score: Optional[int] = None, feedback_text: str = "", category: str = "general") -> str:
            return self._handle_support_feedback_submit(nps_score=nps_score, feedback_text=feedback_text, category=category)

        @app.tool(
            name="mekong_support_triage",
            description="Perform smart AI/heuristic triage for user issues, error traces, and operational bugs.",
        )
        def mekong_support_triage(issue_text: str) -> str:
            return self._handle_support_triage(issue_text=issue_text)

        @app.tool(
            name="mekong_consulting_pricing",
            description="Show standardized AI agent consulting packages, pricing, and deliverables.",
        )
        def mekong_consulting_pricing(currency: str = "USD") -> str:
            return self._handle_consulting_pricing(currency=currency)

        @app.tool(
            name="mekong_consulting_proposal",
            description="Synthesize a customized commercial consulting proposal for a prospect.",
        )
        def mekong_consulting_proposal(prospect_name: str, service_tier: str = "custom_agent", requirements: str = "") -> str:
            return self._handle_consulting_proposal(prospect_name=prospect_name, service_tier=service_tier, requirements=requirements)

        @app.tool(
            name="mekong_consulting_outreach",
            description="Generate multi-channel B2B cold/warm outreach templates (Email, LinkedIn, Zalo).",
        )
        def mekong_consulting_outreach(prospect_name: str, service_tier: str = "custom_agent", role: str = "CTO") -> str:
            return self._handle_consulting_outreach(prospect_name=prospect_name, service_tier=service_tier, role=role)

        @app.tool(
            name="mekong_revenue_metrics",
            description="Calculate current MRR, ARR, ARPU, LTV, churn rate, and MRR waterfall economics.",
        )
        def mekong_revenue_metrics(period: str = "month") -> str:
            return self._handle_revenue_metrics(period=period)

        @app.tool(
            name="mekong_revenue_record",
            description="Record a payment transaction into the revenue ledger and update active subscriptions.",
        )
        def mekong_revenue_record(
            customer_id: str,
            amount: float,
            customer_name: str = "",
            currency: str = "USD",
            tier: str = "starter",
            txn_type: str = "subscription",
            gateway: str = "stripe",
        ) -> str:
            return self._handle_revenue_record(
                customer_id=customer_id,
                amount=amount,
                customer_name=customer_name,
                currency=currency,
                tier=tier,
                txn_type=txn_type,
                gateway=gateway,
            )

        @app.tool(
            name="mekong_revenue_forecast",
            description="Project future MRR, ARR, and cumulative cash flows across growth scenarios.",
        )
        def mekong_revenue_forecast(months: int = 6, scenario: str = "base") -> str:
            return self._handle_revenue_forecast(months=months, scenario=scenario)

        @app.tool(
            name="mekong_content_generate",
            description="Generate structured, ready-to-publish content for any pillar and format.",
        )
        def mekong_content_generate(pillar: str, format_type: str = "blog", topic: str = "", channel: str = "") -> str:
            return self._handle_content_generate(pillar=pillar, format_type=format_type, topic=topic, channel=channel)

        @app.tool(
            name="mekong_content_calendar",
            description="Query editorial publication calendar, frequencies, and upcoming deadlines.",
        )
        def mekong_content_calendar() -> str:
            return self._handle_content_calendar()

        @app.tool(
            name="mekong_content_channels",
            description="Query distribution channels, audience reach, and publication metrics.",
        )
        def mekong_content_channels() -> str:
            return self._handle_content_channels()

        @app.tool(
            name="mekong_copywriting_generate",
            description="Generate high-converting marketing and product copy using proven psychological frameworks.",
        )
        def mekong_copywriting_generate(
            product_name: str = "Mekong CLI",
            target_audience: str = "Founders & Engineers",
            formula: str = "pas",
            copy_type: str = "landing_page",
            key_benefit: str = "",
            style: str = "direct_response",
        ) -> str:
            return self._handle_copywriting_generate(
                product_name=product_name,
                target_audience=target_audience,
                formula=formula,
                copy_type=copy_type,
                key_benefit=key_benefit,
                style=style,
            )

        @app.tool(
            name="mekong_copywriting_headline",
            description="Generate high-conversion headline variations across psychological angles.",
        )
        def mekong_copywriting_headline(
            product_name: str = "Mekong CLI",
            value_prop: str = "automate engineering workflows",
            count: int = 5,
        ) -> str:
            return self._handle_copywriting_headline(
                product_name=product_name,
                value_prop=value_prop,
                count=count,
            )

        @app.tool(
            name="mekong_copywriting_cta",
            description="Generate conversion call-to-action button variations with risk reversals.",
        )
        def mekong_copywriting_cta(
            action_goal: str = "start free trial",
            risk_reversal: str = "",
        ) -> str:
            return self._handle_copywriting_cta(
                action_goal=action_goal,
                risk_reversal=risk_reversal,
            )

        @app.tool(
            name="mekong_billing_simulate",
            description="Simulate an itemized billing invoice based on accrued usage events and pricing tiers.",
        )
        def mekong_billing_simulate(
            license_key: str = "mekong_lic_default",
            tier: str = "pro",
            period_days: int = 30,
        ) -> str:
            return self._handle_billing_simulate(
                license_key=license_key,
                tier=tier,
                period_days=period_days,
            )

        @app.tool(
            name="mekong_billing_record_usage",
            description="Ingest and meter a billable usage event with idempotent deduplication and pricing.",
        )
        def mekong_billing_record_usage(
            license_key: str = "mekong_lic_default",
            event_type: str = "llm_tokens",
            quantity: float = 1.0,
            idempotency_key: str = "",
            tier: str = "pro",
        ) -> str:
            return self._handle_billing_record_usage(
                license_key=license_key,
                event_type=event_type,
                quantity=quantity,
                idempotency_key=idempotency_key,
                tier=tier,
            )

        @app.tool(
            name="mekong_billing_status",
            description="Retrieve real-time billing quotas, consumption, unbilled charges, and health status for a license.",
        )
        def mekong_billing_status(
            license_key: str = "mekong_lic_default",
        ) -> str:
            return self._handle_billing_status(
                license_key=license_key,
            )

        @app.tool(
            name="mekong_vendor_onboard",
            description="Register and onboard a third-party vendor, plugin, model, or tool provider.",
        )
        def mekong_vendor_onboard(
            name: str,
            vendor_type: str = "agent",
            version: str = "1.0.0",
            description: str = "",
            author: str = "Community Builder",
            trust_score: float = 85.0,
        ) -> str:
            return self._handle_vendor_onboard(
                name=name,
                vendor_type=vendor_type,
                version=version,
                description=description,
                author=author,
                trust_score=trust_score,
            )

        @app.tool(
            name="mekong_vendor_list",
            description="List registered vendors with optional filtering by type and operational status.",
        )
        def mekong_vendor_list(
            vendor_type: str = "all",
            status: str = "all",
            limit: int = 50,
        ) -> str:
            return self._handle_vendor_list(
                vendor_type=vendor_type,
                status=status,
                limit=limit,
            )

        @app.tool(
            name="mekong_vendor_assess",
            description="Run an automated security, compliance, or performance audit on a vendor provider.",
        )
        def mekong_vendor_assess(
            name: str,
            audit_type: str = "security",
        ) -> str:
            return self._handle_vendor_assess(
                name=name,
                audit_type=audit_type,
            )

        @app.tool(
            name="mekong_founder_assess",
            description="Assess a founder genome with personality, core values, fears, risk tolerance, and cognitive biases.",
        )
        def mekong_founder_assess(
            name: str = "",
            mission: str = "",
            tipi_responses: Optional[dict[str, int]] = None,
            values: Optional[list[str]] = None,
            fears: Optional[list[dict[str, Any]]] = None,
            risk_ratings: Optional[dict[str, int]] = None,
            bias_responses: Optional[dict[str, bool]] = None,
            particle_id: Optional[str] = None,
        ) -> str:
            return self._handle_founder_assess(
                name=name,
                mission=mission,
                tipi_responses=tipi_responses or {},
                values=values or [],
                fears=fears or [],
                risk_ratings=risk_ratings or {},
                bias_responses=bias_responses or {},
                particle_id=particle_id,
            )

        @app.tool(
            name="mekong_founder_review",
            description="Load and inspect a complete founder genome profile from the registry.",
        )
        def mekong_founder_review(
            founder_id: str,
        ) -> str:
            return self._handle_founder_review(
                founder_id=founder_id,
            )

        @app.tool(
            name="mekong_founder_list",
            description="List assessed founder genome profiles with optional risk level filtering.",
        )
        def mekong_founder_list(
            risk_level: str = "all",
            limit: int = 50,
        ) -> str:
            return self._handle_founder_list(
                risk_level=risk_level,
                limit=limit,
            )

        @app.tool(
            name="mekong_governance_propose",
            description="Draft and submit a new constitutional amendment proposal.",
        )
        def mekong_governance_propose(
            title: str,
            description: str,
            text: str,
            proposer: str = "founder",
            tier: str = "soft",
            co_sponsors: Optional[list[str]] = None,
        ) -> str:
            return self._handle_governance_propose(
                title=title,
                description=description,
                text=text,
                proposer=proposer,
                tier=tier,
                co_sponsors=co_sponsors or [],
            )

        @app.tool(
            name="mekong_governance_vote",
            description="Cast a weighted cryptographic ballot on an active governance proposal.",
        )
        def mekong_governance_vote(
            proposal_id: str,
            choice: str = "yes",
            voter: str = "founder",
            weight: float = 1.0,
        ) -> str:
            return self._handle_governance_vote(
                proposal_id=proposal_id,
                choice=choice,
                voter=voter,
                weight=weight,
            )

        @app.tool(
            name="mekong_governance_tally",
            description="Tally ballots, compute quorum satisfaction, and finalize proposal outcome.",
        )
        def mekong_governance_tally(
            proposal_id: str,
        ) -> str:
            return self._handle_governance_tally(
                proposal_id=proposal_id,
            )

        @app.tool(
            name="mekong_governance_list",
            description="List constitutional governance proposals filtered by status and tier.",
        )
        def mekong_governance_list(
            status: str = "all",
            tier: str = "all",
            limit: int = 50,
        ) -> str:
            return self._handle_governance_list(
                status=status,
                tier=tier,
                limit=limit,
            )

        @app.tool(
            name="mekong_particle_init",
            description="Create and register a new ZenOS particle with constitutional mission.",
        )
        def mekong_particle_init(
            name: str,
            mission: str = "",
            template: str = "skel",
        ) -> str:
            return self._handle_particle_init(
                name=name,
                mission=mission,
                template=template,
            )

        @app.tool(
            name="mekong_particle_status",
            description="Show a ZenOS particle's network status, connections, trust score, and collusion check.",
        )
        def mekong_particle_status(
            particle_id: str = "default",
        ) -> str:
            return self._handle_particle_status(
                particle_id=particle_id,
            )

        @app.tool(
            name="mekong_particle_connect",
            description="Establish a bidirectional trust relationship between two ZenOS particles.",
        )
        def mekong_particle_connect(
            particle_a: str,
            particle_b: str,
            trust_score: float = 50.0,
        ) -> str:
            return self._handle_particle_connect(
                particle_a=particle_a,
                particle_b=particle_b,
                trust_score=trust_score,
            )

        @app.tool(
            name="mekong_particle_cell_run",
            description="Execute an autonomous AI cell role within particle constitutional context.",
        )
        def mekong_particle_cell_run(
            role: str,
            prompt: str,
            particle_id: str = "default",
            auto_compliance: bool = False,
        ) -> str:
            return self._handle_particle_cell_run(
                role=role,
                prompt=prompt,
                particle_id=particle_id,
                auto_compliance=auto_compliance,
            )

        @app.tool(
            name="mekong_thue_tncn",
            description="Calculate progressive Personal Income Tax (TNCN) under Vietnamese tax regulations (Điều 22).",
        )
        def mekong_thue_tncn(
            monthly_income: float,
            dependents: int = 0,
        ) -> str:
            return self._handle_thue_tncn(
                monthly_income=monthly_income,
                dependents=dependents,
            )

        @app.tool(
            name="mekong_thue_tndn",
            description="Calculate Corporate Income Tax (TNDN) with standard 20% or SME 17% preferential rate.",
        )
        def mekong_thue_tndn(
            annual_revenue: float,
            profit: float = 0.0,
            is_sme: bool = True,
        ) -> str:
            return self._handle_thue_tndn(
                annual_revenue=annual_revenue,
                profit=profit,
                is_sme=is_sme,
            )

        @app.tool(
            name="mekong_thue_gtgt",
            description="Calculate Value Added Tax (GTGT / VAT 0%, 5%, 8%, 10%) under Decree 123 & Circular 78.",
        )
        def mekong_thue_gtgt(
            amount: float,
            rate: int = 10,
        ) -> str:
            return self._handle_thue_gtgt(
                amount=amount,
                rate=rate,
            )

        @app.tool(
            name="mekong_thue_status",
            description="Retrieve Vietnamese tax engine status, statutory deduction rates, and historical simulation summaries.",
        )
        def mekong_thue_status() -> str:
            return self._handle_thue_status()

        @app.tool(
            name="mekong_ke_toan_create",
            description="Create an electronic invoice compliant with Decree 123 & Circular 78 and save to accounting database.",
        )
        def mekong_ke_toan_create(
            amount: float,
            buyer: str,
            vat_rate: int = 10,
            seller: str = "Doanh Nghiệp",
            seller_tax_code: str = "0000000000",
            buyer_tax_code: str = "",
            description: str = "Hàng hóa/Dịch vụ",
        ) -> str:
            return self._handle_ke_toan_create(
                amount=amount,
                buyer=buyer,
                vat_rate=vat_rate,
                seller=seller,
                seller_tax_code=seller_tax_code,
                buyer_tax_code=buyer_tax_code,
                description=description,
            )

        @app.tool(
            name="mekong_ke_toan_xml",
            description="Generate electronic invoice XML complying with Circular 78/2021/TT-BTC schema.",
        )
        def mekong_ke_toan_xml(
            amount: float,
            buyer: str,
            vat_rate: int = 10,
            seller: str = "Doanh Nghiệp",
            seller_tax_code: str = "0000000000",
            description: str = "Hàng hóa/Dịch vụ",
        ) -> str:
            return self._handle_ke_toan_xml(
                amount=amount,
                buyer=buyer,
                vat_rate=vat_rate,
                seller=seller,
                seller_tax_code=seller_tax_code,
                description=description,
            )

        @app.tool(
            name="mekong_ke_toan_journal",
            description="Generate balanced VAS double-entry journal entry (Nợ 131 / Có 511, Có 3331) for sales revenue.",
        )
        def mekong_ke_toan_journal(
            amount: float,
            buyer: str,
            vat_rate: int = 10,
            seller: str = "Doanh Nghiệp",
            seller_tax_code: str = "0000000000",
            description: str = "Hàng hóa/Dịch vụ",
        ) -> str:
            return self._handle_ke_toan_journal(
                amount=amount,
                buyer=buyer,
                vat_rate=vat_rate,
                seller=seller,
                seller_tax_code=seller_tax_code,
                description=description,
            )

        @app.tool(
            name="mekong_ke_toan_status",
            description="Retrieve Vietnamese accounting system status, invoice totals, VAT output, and general ledger statistics.",
        )
        def mekong_ke_toan_status() -> str:
            return self._handle_ke_toan_status()

        @app.tool(
            name="mekong_zalo_send",
            description="Send direct message to a Zalo OA follower.",
        )
        def mekong_zalo_send(user_id: str, message: str, template: str = "") -> str:
            return self._handle_zalo_send(user_id=user_id, message=message, template=template)

        @app.tool(
            name="mekong_zalo_broadcast",
            description="Create and dispatch a broadcast campaign to Zalo OA followers.",
        )
        def mekong_zalo_broadcast(message: str, title: str = "Thông báo Zalo OA", target_segment: str = "all") -> str:
            return self._handle_zalo_broadcast(message=message, title=title, target_segment=target_segment)

        @app.tool(
            name="mekong_zalo_followers",
            description="List and filter Zalo OA followers and customer profiles.",
        )
        def mekong_zalo_followers(segment: str = "all", limit: int = 50) -> str:
            return self._handle_zalo_followers(segment=segment, limit=limit)

        @app.tool(
            name="mekong_zalo_caption",
            description="Generate social marketing caption for Zalo with multiple tones and hashtags.",
        )
        def mekong_zalo_caption(topic: str = "Sản phẩm", tone: str = "vui_ve") -> str:
            return self._handle_zalo_caption(topic=topic, tone=tone)

        @app.tool(
            name="mekong_zalo_status",
            description="Retrieve Zalo OA customer messaging, broadcast, and follower statistics.",
        )
        def mekong_zalo_status() -> str:
            return self._handle_zalo_status()

        @app.tool(
            name="mekong_bhxh_calc",
            description="Calculate statutory Vietnamese social insurance (BHXH 8%/17.5%, BHYT 1.5%/3%, BHTN 1%/1%) with salary ceilings.",
        )
        def mekong_bhxh_calc(
            salary: float,
            region: int = 1,
            include_kpcd: bool = False,
            employee_id: str = "ADHOC",
        ) -> str:
            return self._handle_bhxh_calc(
                salary=salary,
                region=region,
                include_kpcd=include_kpcd,
                employee_id=employee_id,
            )

        @app.tool(
            name="mekong_bhxh_employees",
            description="List registered employees for social insurance reporting and declarations.",
        )
        def mekong_bhxh_employees(status: str = "all") -> str:
            return self._handle_bhxh_employees(status=status)

        @app.tool(
            name="mekong_bhxh_declaration",
            description="Generate statutory electronic declaration D02-LT (bao_tang, bao_giam, dieu_chinh_luong).",
        )
        def mekong_bhxh_declaration(
            change_type: str,
            employee_id: str,
            effective_month: str = "",
            new_salary: float = 0.0,
            note: str = "",
        ) -> str:
            return self._handle_bhxh_declaration(
                change_type=change_type,
                employee_id=employee_id,
                effective_month=effective_month,
                new_salary=new_salary,
                note=note,
            )

        @app.tool(
            name="mekong_bhxh_status",
            description="Retrieve Vietnamese social insurance regulatory status, contribution totals, and active employee metrics.",
        )
        def mekong_bhxh_status() -> str:
            return self._handle_bhxh_status()

        @app.tool(
            name="mekong_ocop_eval",
            description="Evaluate Vietnamese agricultural product OCOP star classification (1 to 5 stars) under Decision 148/QĐ-TTg.",
        )
        def mekong_ocop_eval(
            product_name: str,
            part_a: float = 30.0,
            part_b: float = 22.0,
            part_c: float = 38.0,
        ) -> str:
            return self._handle_ocop_eval(
                product_name=product_name,
                part_a=part_a,
                part_b=part_b,
                part_c=part_c,
            )

        @app.tool(
            name="mekong_ocop_products",
            description="Browse registered Vietnamese OCOP products, HS code classifications, and international certifications.",
        )
        def mekong_ocop_products(min_stars: int = 1, province: str = "all") -> str:
            return self._handle_ocop_products(min_stars=min_stars, province=province)

        @app.tool(
            name="mekong_ocop_listing",
            description="Synthesize international B2B export marketplace listing and trade compliance audit (Alibaba, Amazon, Shopee).",
        )
        def mekong_ocop_listing(
            product_id: str,
            target_market: str = "EU",
            platform: str = "alibaba",
        ) -> str:
            return self._handle_ocop_listing(
                product_id=product_id,
                target_market=target_market,
                platform=platform,
            )

        @app.tool(
            name="mekong_ocop_compliance",
            description="Inspect technical trade barriers, tariff preferences under FTAs (EVFTA, CPTPP, RCEP), and required food safety certs.",
        )
        def mekong_ocop_compliance(market: str = "EU") -> str:
            return self._handle_ocop_compliance(market=market)

        @app.tool(
            name="mekong_ocop_status",
            description="Retrieve national OCOP program telemetry, star breakdown, and registered export listings.",
        )
        def mekong_ocop_status() -> str:
            return self._handle_ocop_status()

        @app.tool(
            name="mekong_vietqr_generate",
            description="Construct EMVCo VietQR string and Napas 247 QuickLink for instant interbank fund transfers.",
        )
        def mekong_vietqr_generate(
            amount: int = 0,
            memo: str = "",
            bank: str = "MB",
            account_number: str = "",
            account_name: str = "",
        ) -> str:
            return self._handle_vietqr_generate(
                amount=amount,
                memo=memo,
                bank=bank,
                account_number=account_number,
                account_name=account_name,
            )

        @app.tool(
            name="mekong_vietqr_banks",
            description="Lookup Vietnamese Napas 247 participant banks, BIN codes, and short names.",
        )
        def mekong_vietqr_banks() -> str:
            return self._handle_vietqr_banks()

        @app.tool(
            name="mekong_vietqr_transactions",
            description="List recent incoming bank transfer transactions and payment reconciliation records.",
        )
        def mekong_vietqr_transactions(limit: int = 20) -> str:
            return self._handle_vietqr_transactions(limit=limit)

        @app.tool(
            name="mekong_vietqr_record",
            description="Record and reconcile an incoming bank payment transaction idempotently.",
        )
        def mekong_vietqr_record(
            bank_tx_id: str,
            amount_vnd: int,
            memo: str = "",
            bin_code: str = "970422",
            matched_order_id: str = "",
        ) -> str:
            return self._handle_vietqr_record(
                bank_tx_id=bank_tx_id,
                amount_vnd=amount_vnd,
                memo=memo,
                bin_code=bin_code,
                matched_order_id=matched_order_id,
            )

        @app.tool(
            name="mekong_vietqr_status",
            description="Retrieve VietQR payment gateway status, default account, and volume metrics.",
        )
        def mekong_vietqr_status() -> str:
            return self._handle_vietqr_status()

        @app.tool(
            name="mekong_audit_run",
            description="Execute automated SOX 404, ITGC, and internal controls testing across all control domains.",
        )
        def mekong_audit_run(framework: str = "all") -> str:
            return self._handle_audit_run(framework=framework)

        @app.tool(
            name="mekong_audit_controls",
            description="Browse internal controls catalog, risk ratings, and validation procedures across AC, CM, CO, and SD domains.",
        )
        def mekong_audit_controls(domain: str = "all", framework: str = "all") -> str:
            return self._handle_audit_controls(domain=domain, framework=framework)

        @app.tool(
            name="mekong_audit_findings",
            description="Inspect open audit deficiencies, material weaknesses, and remediation action plans.",
        )
        def mekong_audit_findings(min_severity: str = "all") -> str:
            return self._handle_audit_findings(min_severity=min_severity)

        @app.tool(
            name="mekong_audit_status",
            description="Retrieve executive internal controls audit posture, latest compliance score, and audit opinion.",
        )
        def mekong_audit_status() -> str:
            return self._handle_audit_status()

        @app.tool(
            name="mekong_payroll_gross_to_net",
            description="Calculate Vietnamese Net take-home pay, employee insurance, PIT tax, and employer burden from Gross salary.",
        )
        def mekong_payroll_gross_to_net(
            gross: float,
            dependents: int = 0,
            region: int = 1,
            lunch_allowance: float = 730000.0,
        ) -> str:
            return self._handle_payroll_gross_to_net(
                gross=gross,
                dependents=dependents,
                region=region,
                lunch_allowance=lunch_allowance,
            )

        @app.tool(
            name="mekong_payroll_net_to_gross",
            description="Convert desired Net take-home salary to required contractual Gross salary and employer cost.",
        )
        def mekong_payroll_net_to_gross(
            net: float,
            dependents: int = 0,
            region: int = 1,
            lunch_allowance: float = 730000.0,
        ) -> str:
            return self._handle_payroll_net_to_gross(
                net=net,
                dependents=dependents,
                region=region,
                lunch_allowance=lunch_allowance,
            )

        @app.tool(
            name="mekong_payroll_payslip",
            description="Generate and persist an itemized electronic payslip for an employee.",
        )
        def mekong_payroll_payslip(
            employee_name: str,
            gross: float,
            employee_id: str = "",
            month: str = "",
            dependents: int = 0,
            region: int = 1,
            bonus: float = 0.0,
        ) -> str:
            return self._handle_payroll_payslip(
                employee_name=employee_name,
                gross=gross,
                employee_id=employee_id,
                month=month,
                dependents=dependents,
                region=region,
                bonus=bonus,
            )

        @app.tool(
            name="mekong_payroll_list",
            description="Query historical electronic payslips and compensation disbursement records.",
        )
        def mekong_payroll_list(month: str = "", limit: int = 20) -> str:
            return self._handle_payroll_list(month=month, limit=limit)

        @app.tool(
            name="mekong_payroll_status",
            description="Retrieve Vietnamese payroll system status, statutory parameters, and total disburse metrics.",
        )
        def mekong_payroll_status() -> str:
            return self._handle_payroll_status()

        @app.tool(
            name="mekong_corporate_charter",
            description="Synthesize a complete 10-chapter Corporate Charter (Điều lệ công ty) complying with Article 24 Law on Enterprises 2020.",
        )
        def mekong_corporate_charter(
            company_name: str,
            entity_type: str = "TNHH_1TV",
            charter_capital: int = 1000000000,
            legal_rep_name: str = "Nguyễn Văn A",
            address: str = "Hà Nội, Việt Nam",
        ) -> str:
            return self._handle_corporate_charter(
                company_name=company_name,
                entity_type=entity_type,
                charter_capital=charter_capital,
                legal_rep_name=legal_rep_name,
                address=address,
            )

        @app.tool(
            name="mekong_corporate_resolution",
            description="Draft statutory Board / Member Council resolution and meeting minutes.",
        )
        def mekong_corporate_resolution(
            company_name: str,
            resolution_type: str = "APPOINTMENT",
            title: str = "",
        ) -> str:
            return self._handle_corporate_resolution(
                company_name=company_name,
                resolution_type=resolution_type,
                title=title,
            )

        @app.tool(
            name="mekong_corporate_dossier",
            description="Synthesize complete statutory business incorporation dossier under Decree 01/2021/NĐ-CP.",
        )
        def mekong_corporate_dossier(
            company_name: str,
            entity_type: str = "TNHH_1TV",
            charter_capital: int = 1000000000,
            legal_rep_name: str = "Nguyễn Văn A",
            address: str = "Hà Nội, Việt Nam",
            main_industry: str = "6201",
        ) -> str:
            return self._handle_corporate_dossier(
                company_name=company_name,
                entity_type=entity_type,
                charter_capital=charter_capital,
                legal_rep_name=legal_rep_name,
                address=address,
                main_industry=main_industry,
            )

        @app.tool(
            name="mekong_corporate_list",
            description="Query historical corporate filings, charters, and statutory governance documents.",
        )
        def mekong_corporate_list(limit: int = 20) -> str:
            return self._handle_corporate_list(limit=limit)

        @app.tool(
            name="mekong_corporate_status",
            description="Retrieve corporate governance engine metrics, registered entity counts, and legal framework.",
        )
        def mekong_corporate_status() -> str:
            return self._handle_corporate_status()

        @app.tool(
            name="mekong_fdi_market_access",
            description="Evaluate foreign ownership limits, market access conditions, and international treaties (WTO/CPTPP/EVFTA).",
        )
        def mekong_fdi_market_access(
            sector_code: str,
            investor_nationality: str = "US",
            ownership_pct: float = 100.0,
        ) -> str:
            return self._handle_fdi_market_access(
                sector_code=sector_code,
                investor_nationality=investor_nationality,
                ownership_pct=ownership_pct,
            )

        @app.tool(
            name="mekong_fdi_remittance",
            description="Verify offshore profit remittance eligibility, statutory DICA account, tax clearance, and legal reserve rules.",
        )
        def mekong_fdi_remittance(
            fiscal_year: int,
            audited_profit_vnd: float,
            tax_cleared: bool = True,
            retained_reserve_pct: float = 5.0,
            dica_verified: bool = True,
            losses_carried_forward_vnd: float = 0.0,
        ) -> str:
            return self._handle_fdi_remittance(
                fiscal_year=fiscal_year,
                audited_profit_vnd=audited_profit_vnd,
                tax_cleared=tax_cleared,
                retained_reserve_pct=retained_reserve_pct,
                dica_verified=dica_verified,
                losses_carried_forward_vnd=losses_carried_forward_vnd,
            )

        @app.tool(
            name="mekong_fdi_foreign_loan",
            description="Evaluate offshore foreign loan compliance, SBV registration triggers, and foreign debt ceiling limit.",
        )
        def mekong_fdi_foreign_loan(
            loan_amount: float,
            currency: str = "USD",
            tenure_months: int = 24,
            interest_rate_pct: float = 6.5,
            project_capital_gap: float = 0.0,
        ) -> str:
            return self._handle_fdi_foreign_loan(
                loan_amount=loan_amount,
                currency=currency,
                tenure_months=tenure_months,
                interest_rate_pct=interest_rate_pct,
                project_capital_gap=project_capital_gap,
            )

        @app.tool(
            name="mekong_fdi_irc",
            description="Synthesize statutory Investment Registration Certificate (IRC) application dossier under Law on Investment 2020.",
        )
        def mekong_fdi_irc(
            project_name: str,
            sector_code: str,
            total_investment_vnd: float,
            investor_name: str,
            investor_country: str = "US",
            project_location: str = "TP. Hồ Chí Minh",
        ) -> str:
            return self._handle_fdi_irc(
                project_name=project_name,
                sector_code=sector_code,
                total_investment_vnd=total_investment_vnd,
                investor_name=investor_name,
                investor_country=investor_country,
                project_location=project_location,
            )

        @app.tool(
            name="mekong_fdi_status",
            description="Retrieve FDI & SBV capital compliance engine metrics, registered projects, and legal framework.",
        )
        def mekong_fdi_status() -> str:
            return self._handle_fdi_status()

        @app.tool(
            name="mekong_ip_trademark",
            description="Register a trademark application conforming to Nice Classification 12-2024 and Law on Intellectual Property.",
        )
        def mekong_ip_trademark(
            mark_name: str,
            nice_class: str = "09",
            applicant_name: str = "Công Ty Công Nghệ Mekong",
            goods_services_spec: str = "",
        ) -> str:
            return self._handle_ip_trademark(
                mark_name=mark_name,
                nice_class=nice_class,
                applicant_name=applicant_name,
                goods_services_spec=goods_services_spec,
            )

        @app.tool(
            name="mekong_ip_search",
            description="Search phonetical and orthographical trademark conflicts and assess likelihood of confusion under Article 74.",
        )
        def mekong_ip_search(
            mark_name: str,
            nice_class: str = "09",
        ) -> str:
            return self._handle_ip_search(
                mark_name=mark_name,
                nice_class=nice_class,
            )

        @app.tool(
            name="mekong_ip_patent",
            description="Draft statutory patent specification and independent/dependent claims under Article 102 Law on IP.",
        )
        def mekong_ip_patent(
            title: str,
            technical_field: str,
            applicant_name: str = "Tổ chức Nghiên cứu Mekong",
            independent_claims: int = 1,
            dependent_claims: int = 2,
        ) -> str:
            return self._handle_ip_patent(
                title=title,
                technical_field=technical_field,
                applicant_name=applicant_name,
                independent_claims=independent_claims,
                dependent_claims=dependent_claims,
            )

        @app.tool(
            name="mekong_ip_copyright",
            description="Synthesize software computer program copyright registration dossier under Decree 17/2023/ND-CP.",
        )
        def mekong_ip_copyright(
            software_name: str,
            author_name: str,
            version: str = "1.0.0",
            repository_url: str = "",
            lines_of_code: int = 10000,
        ) -> str:
            return self._handle_ip_copyright(
                software_name=software_name,
                author_name=author_name,
                version=version,
                repository_url=repository_url,
                lines_of_code=lines_of_code,
            )

        @app.tool(
            name="mekong_ip_fees",
            description="Calculate itemized state official IP registration fees under Circular 263/2016/TT-BTC.",
        )
        def mekong_ip_fees(
            trademark_classes: int = 1,
            patent_claims: int = 1,
            software_copyrights: int = 1,
        ) -> str:
            return self._handle_ip_fees(
                trademark_classes=trademark_classes,
                patent_claims=patent_claims,
                software_copyrights=software_copyrights,
            )

        @app.tool(
            name="mekong_ip_status",
            description="Retrieve IP engine telemetry, Nice classification support, and registered asset counts.",
        )
        def mekong_ip_status() -> str:
            return self._handle_ip_status()

        @app.tool(
            name="mekong_customs_hs_lookup",
            description="Look up 8-digit AHTN HS code tariff rates, MFN duty, import VAT, and preferential FTA rates.",
        )
        def mekong_customs_hs_lookup(
            hs_code: str,
            fta: str = "MFN",
        ) -> str:
            return self._handle_customs_hs_lookup(
                hs_code=hs_code,
                fta=fta,
            )

        @app.tool(
            name="mekong_customs_duty_calc",
            description="Calculate itemized CIF valuation, import duty, and import VAT obligations.",
        )
        def mekong_customs_duty_calc(
            invoice_value_usd: float,
            hs_code: str = "8471.30.20",
            freight_usd: float = 0.0,
            insurance_usd: float = 0.0,
            fta: str = "MFN",
        ) -> str:
            return self._handle_customs_duty_calc(
                invoice_value_usd=invoice_value_usd,
                hs_code=hs_code,
                freight_usd=freight_usd,
                insurance_usd=insurance_usd,
                fta=fta,
            )

        @app.tool(
            name="mekong_customs_channel",
            description="Evaluate VNACCS automated risk criteria and determine Green, Yellow, or Red customs channel.",
        )
        def mekong_customs_channel(
            enterprise_tax_id: str,
            hs_code: str,
            invoice_value_usd: float,
            origin_country: str = "US",
            compliance_tier: str = "TIER_2_NORMAL",
            has_valid_co: bool = True,
        ) -> str:
            return self._handle_customs_channel(
                enterprise_tax_id=enterprise_tax_id,
                hs_code=hs_code,
                invoice_value_usd=invoice_value_usd,
                origin_country=origin_country,
                compliance_tier=compliance_tier,
                has_valid_co=has_valid_co,
            )

        @app.tool(
            name="mekong_customs_declare",
            description="Synthesize and submit a formal VNACCS/VCIS electronic customs declaration.",
        )
        def mekong_customs_declare(
            enterprise_tax_id: str,
            hs_code: str,
            commodity_name: str,
            invoice_value_usd: float,
            origin_country: str = "US",
            declaration_type: str = "IMPORT_BUSINESS",
            compliance_tier: str = "TIER_2_NORMAL",
            has_valid_co: bool = True,
        ) -> str:
            return self._handle_customs_declare(
                enterprise_tax_id=enterprise_tax_id,
                hs_code=hs_code,
                commodity_name=commodity_name,
                invoice_value_usd=invoice_value_usd,
                origin_country=origin_country,
                declaration_type=declaration_type,
                compliance_tier=compliance_tier,
                has_valid_co=has_valid_co,
            )

        @app.tool(
            name="mekong_customs_origin",
            description="Verify Rules of Origin (RVC >= 40% and CTC criteria) for preferential C/O certification.",
        )
        def mekong_customs_origin(
            form_type: str,
            hs_code: str,
            fob_value_usd: float,
            non_originating_value_usd: float,
            exporter_name: str = "Doanh Nghiệp Xuất Khẩu Việt Nam",
            importer_country: str = "DE",
        ) -> str:
            return self._handle_customs_origin(
                form_type=form_type,
                hs_code=hs_code,
                fob_value_usd=fob_value_usd,
                non_originating_value_usd=non_originating_value_usd,
                exporter_name=exporter_name,
                importer_country=importer_country,
            )

        @app.tool(
            name="mekong_customs_status",
            description="Retrieve customs engine telemetry, VNACCS channel distribution, and total duty collected.",
        )
        def mekong_customs_status() -> str:
            return self._handle_customs_status()

        @app.tool(
            name="mekong_contract_draft",
            description="Synthesize standard commercial contract complying with Vietnamese law (SOFTWARE_DEV, COMMERCIAL_SALE, NDA, DISTRIBUTION).",
        )
        def mekong_contract_draft(
            template_type: str,
            party_a_name: str,
            party_b_name: str,
            contract_value_vnd: float = 0.0,
            party_a_tax_id: str = "0100000001",
            party_b_tax_id: str = "0300000002",
            scope_summary: str = "",
            penalty_rate_pct: float = 8.0,
            dispute_forum: str = "VIAC",
        ) -> str:
            return self._handle_contract_draft(
                template_type=template_type,
                party_a_name=party_a_name,
                party_b_name=party_b_name,
                contract_value_vnd=contract_value_vnd,
                party_a_tax_id=party_a_tax_id,
                party_b_tax_id=party_b_tax_id,
                scope_summary=scope_summary,
                penalty_rate_pct=penalty_rate_pct,
                dispute_forum=dispute_forum,
            )

        @app.tool(
            name="mekong_contract_risk_check",
            description="Scan contract clauses for legal risks, penalty breach (>8%), missing force majeure, and redline recommendations.",
        )
        def mekong_contract_risk_check(
            contract_text: str,
            penalty_pct: float = 8.0,
        ) -> str:
            return self._handle_contract_risk_check(
                contract_text=contract_text,
                penalty_pct=penalty_pct,
            )

        @app.tool(
            name="mekong_contract_sign",
            description="Sign a commercial contract electronically with cryptographic SHA-256 digest and TSA timestamp under Law on Electronic Transactions 2023.",
        )
        def mekong_contract_sign(
            contract_id: str,
            signer_name: str,
            signer_title: str = "Giám đốc điều hành",
            signer_tax_id: str = "0100000001",
            organization_name: str = "",
        ) -> str:
            return self._handle_contract_sign(
                contract_id=contract_id,
                signer_name=signer_name,
                signer_title=signer_title,
                signer_tax_id=signer_tax_id,
                organization_name=organization_name,
            )

        @app.tool(
            name="mekong_contract_verify",
            description="Verify authenticity, integrity, and timestamp of an electronic contract signature.",
        )
        def mekong_contract_verify(
            signature_id: str,
        ) -> str:
            return self._handle_contract_verify(
                signature_id=signature_id,
            )

        @app.tool(
            name="mekong_contract_list",
            description="Query historical commercial contracts and execution/signing status.",
        )
        def mekong_contract_list(
            status: str = "ALL",
            limit: int = 20,
        ) -> str:
            return self._handle_contract_list(
                status=status,
                limit=limit,
            )

        @app.tool(
            name="mekong_contract_status",
            description="Retrieve contract engine telemetry, active e-signatures, template catalog, and risk metrics.",
        )
        def mekong_contract_status() -> str:
            return self._handle_contract_status()

        @app.tool(
            name="mekong_tender_method",
            description="Evaluate and advise statutory procurement method (Open Bidding, Direct Contracting, Competitive Quotation) under Bidding Law 2023.",
        )
        def mekong_tender_method(
            package_type: str,
            budget_vnd: float,
            urgent: bool = False,
            proprietary: bool = False,
        ) -> str:
            return self._handle_tender_method(
                package_type=package_type,
                budget_vnd=budget_vnd,
                urgent=urgent,
                proprietary=proprietary,
            )

        @app.tool(
            name="mekong_tender_create",
            description="Synthesize and publish an electronic tender dossier (E-HSMT) on National E-GP under Decree 24/2024/ND-CP.",
        )
        def mekong_tender_create(
            package_name: str,
            procuring_entity: str,
            budget_vnd: float,
            package_type: str = "GOODS",
            procurement_method: str = "",
            submission_days: int = 15,
        ) -> str:
            return self._handle_tender_create(
                package_name=package_name,
                procuring_entity=procuring_entity,
                budget_vnd=budget_vnd,
                package_type=package_type,
                procurement_method=procurement_method,
                submission_days=submission_days,
            )

        @app.tool(
            name="mekong_tender_eval",
            description="Execute statutory 4-step E-HSDT bid evaluation (eligibility, capacity/experience, technical floor, financial/savings).",
        )
        def mekong_tender_eval(
            tender_id: str,
            bidder_name: str,
            bid_price_vnd: float,
            bidder_tax_id: str = "0101234567",
            revenue_3yr_avg_vnd: float = 0.0,
            similar_contract_val_vnd: float = 0.0,
            tech_score: float = 85.0,
            has_valid_security: bool = True,
        ) -> str:
            return self._handle_tender_eval(
                tender_id=tender_id,
                bidder_name=bidder_name,
                bid_price_vnd=bid_price_vnd,
                bidder_tax_id=bidder_tax_id,
                revenue_3yr_avg_vnd=revenue_3yr_avg_vnd,
                similar_contract_val_vnd=similar_contract_val_vnd,
                tech_score=tech_score,
                has_valid_security=has_valid_security,
            )

        @app.tool(
            name="mekong_tender_collusion_scan",
            description="Scan submitted tender bids for anti-competitive collusion, abnormal price clustering, and affiliate conflicts under Article 16 Bidding Law 2023.",
        )
        def mekong_tender_collusion_scan(
            tender_id: str,
        ) -> str:
            return self._handle_tender_collusion_scan(
                tender_id=tender_id,
            )

        @app.tool(
            name="mekong_tender_list",
            description="Query registered tender packages and active biddings on National E-GP.",
        )
        def mekong_tender_list(
            status: str = "ALL",
            limit: int = 20,
        ) -> str:
            return self._handle_tender_list(
                status=status,
                limit=limit,
            )

        @app.tool(
            name="mekong_tender_status",
            description="Retrieve public procurement telemetry, budget, savings rate, and E-GP bidding metrics.",
        )
        def mekong_tender_status() -> str:
            return self._handle_tender_status()

        @app.tool(
            name="mekong_realestate_finance",
            description="Calculate complete commercial/industrial leasing cash flow schedule, security deposit, and total value.",
        )
        def mekong_realestate_finance(
            category: str,
            area_sqm: float,
            unit_rent_usd: float,
            lease_term_months: int = 36,
            maintenance_fee_usd: float = 0.5,
            deposit_months: int = 3,
            annual_escalation_pct: float = 3.0,
        ) -> str:
            return self._handle_realestate_finance(
                category=category,
                area_sqm=area_sqm,
                unit_rent_usd=unit_rent_usd,
                lease_term_months=lease_term_months,
                maintenance_fee_usd=maintenance_fee_usd,
                deposit_months=deposit_months,
                annual_escalation_pct=annual_escalation_pct,
            )

        @app.tool(
            name="mekong_realestate_density",
            description="Validate industrial/commercial site density (<=70%) and green space ratio (>=10%) against QCVN 01:2021/BXD.",
        )
        def mekong_realestate_density(
            lot_area_sqm: float,
            building_footprint_sqm: float,
            green_space_sqm: float,
            building_height_tier: str = "UP_TO_20M",
        ) -> str:
            return self._handle_realestate_density(
                lot_area_sqm=lot_area_sqm,
                building_footprint_sqm=building_footprint_sqm,
                green_space_sqm=green_space_sqm,
                building_height_tier=building_height_tier,
            )

        @app.tool(
            name="mekong_realestate_audit",
            description="Audit legal title, construction readiness, fire safety cert, and statutory conditions for real estate leasing.",
        )
        def mekong_realestate_audit(
            project_name: str,
            category: str,
            land_area_sqm: float,
            has_land_cert: bool = True,
            has_construction_permit: bool = True,
            has_fire_safety_cert: bool = True,
            tenure_remaining_years: float = 35.0,
            payment_term: str = "ANNUAL_RENT",
            has_disputes: bool = False,
            is_mortgaged_to_bank: bool = False,
        ) -> str:
            return self._handle_realestate_audit(
                project_name=project_name,
                category=category,
                land_area_sqm=land_area_sqm,
                has_land_cert=has_land_cert,
                has_construction_permit=has_construction_permit,
                has_fire_safety_cert=has_fire_safety_cert,
                tenure_remaining_years=tenure_remaining_years,
                payment_term=payment_term,
                has_disputes=has_disputes,
                is_mortgaged_to_bank=is_mortgaged_to_bank,
            )

        @app.tool(
            name="mekong_realestate_draft",
            description="Synthesize a complete commercial/industrial lease agreement complying with Decree 96/2024/ND-CP.",
        )
        def mekong_realestate_draft(
            property_id: str,
            lessor_name: str,
            lessee_name: str,
            leased_area_sqm: float,
            unit_rent_usd: float,
            lease_term_months: int = 36,
            maintenance_fee_usd: float = 0.5,
            deposit_months: int = 3,
            dispute_resolution: str = "VIAC",
        ) -> str:
            return self._handle_realestate_draft(
                property_id=property_id,
                lessor_name=lessor_name,
                lessee_name=lessee_name,
                leased_area_sqm=leased_area_sqm,
                unit_rent_usd=unit_rent_usd,
                lease_term_months=lease_term_months,
                maintenance_fee_usd=maintenance_fee_usd,
                deposit_months=deposit_months,
                dispute_resolution=dispute_resolution,
            )

        @app.tool(
            name="mekong_realestate_list",
            description="Query registered real estate properties and industrial parks.",
        )
        def mekong_realestate_list(
            category: str = "ALL",
            limit: int = 20,
        ) -> str:
            return self._handle_realestate_list(
                category=category,
                limit=limit,
            )

        @app.tool(
            name="mekong_realestate_status",
            description="Retrieve commercial real estate engine telemetry, total managed area, active leases, and metrics.",
        )
        def mekong_realestate_status() -> str:
            return self._handle_realestate_status()

        @app.tool(
            name="mekong_esg_ghg",
            description="Compute enterprise greenhouse gas (GHG) emissions inventory across Scope 1, 2, 3 under ISO 14064-1 & Decision 13/2024/QD-TTg.",
        )
        def mekong_esg_ghg(
            enterprise_name: str,
            reporting_year: int,
            fuel_diesel_liters: float = 0.0,
            fuel_gasoline_liters: float = 0.0,
            coal_tons: float = 0.0,
            lpg_kg: float = 0.0,
            electricity_kwh: float = 0.0,
            scope3_logistics_tco2e: float = 0.0,
        ) -> str:
            return self._handle_esg_ghg(
                enterprise_name=enterprise_name,
                reporting_year=reporting_year,
                fuel_diesel_liters=fuel_diesel_liters,
                fuel_gasoline_liters=fuel_gasoline_liters,
                coal_tons=coal_tons,
                lpg_kg=lpg_kg,
                electricity_kwh=electricity_kwh,
                scope3_logistics_tco2e=scope3_logistics_tco2e,
            )

        @app.tool(
            name="mekong_esg_cbam",
            description="Evaluate EU CBAM embedded emissions and financial certificate liability for Vietnam exports (Regulation EU 2023/956).",
        )
        def mekong_esg_cbam(
            product_type: str,
            export_volume_tons: float,
            direct_emissions_tco2: float,
            indirect_emissions_tco2: float = 0.0,
            cbam_carbon_price_eur_per_ton: float = 75.0,
        ) -> str:
            return self._handle_esg_cbam(
                product_type=product_type,
                export_volume_tons=export_volume_tons,
                direct_emissions_tco2=direct_emissions_tco2,
                indirect_emissions_tco2=indirect_emissions_tco2,
                cbam_carbon_price_eur_per_ton=cbam_carbon_price_eur_per_ton,
            )

        @app.tool(
            name="mekong_esg_audit",
            description="Audit and synthesize corporate ESG composite score and rating under Circular 96/2020/TT-BTC & GRI standards.",
        )
        def mekong_esg_audit(
            enterprise_name: str,
            has_iso_14001: bool = True,
            renewable_energy_ratio_pct: float = 20.0,
            has_waste_treatment_license: bool = True,
            full_social_insurance_compliance: bool = True,
            workplace_accident_rate: float = 0.0,
            female_leadership_ratio_pct: float = 30.0,
            independent_board_members_ratio_pct: float = 33.3,
            has_anti_corruption_policy: bool = True,
            has_audited_financial_report: bool = True,
        ) -> str:
            return self._handle_esg_audit(
                enterprise_name=enterprise_name,
                has_iso_14001=has_iso_14001,
                renewable_energy_ratio_pct=renewable_energy_ratio_pct,
                has_waste_treatment_license=has_waste_treatment_license,
                full_social_insurance_compliance=full_social_insurance_compliance,
                workplace_accident_rate=workplace_accident_rate,
                female_leadership_ratio_pct=female_leadership_ratio_pct,
                independent_board_members_ratio_pct=independent_board_members_ratio_pct,
                has_anti_corruption_policy=has_anti_corruption_policy,
                has_audited_financial_report=has_audited_financial_report,
            )

        @app.tool(
            name="mekong_esg_carbon_trade",
            description="Execute carbon credit transaction or offset surrender under Articles 93 & 94 Environmental Law 2020.",
        )
        def mekong_esg_carbon_trade(
            project_name: str,
            credit_type: str,
            quantity_tco2e: float,
            unit_price_usd: float,
            action: str = "BUY",
            counterparty: str = "Sàn giao dịch Carbon Quốc gia",
        ) -> str:
            return self._handle_esg_carbon_trade(
                project_name=project_name,
                credit_type=credit_type,
                quantity_tco2e=quantity_tco2e,
                unit_price_usd=unit_price_usd,
                action=action,
                counterparty=counterparty,
            )

        @app.tool(
            name="mekong_esg_list",
            description="Query registered enterprise GHG inventories and carbon transaction ledger.",
        )
        def mekong_esg_list(
            limit: int = 20,
        ) -> str:
            return self._handle_esg_list(
                limit=limit,
            )

        @app.tool(
            name="mekong_esg_status",
            description="Retrieve ESG compliance telemetry, tracked emissions, carbon trades, and green metrics.",
        )
        def mekong_esg_status() -> str:
            return self._handle_esg_status()

        @app.tool(
            name="mekong_supplychain_plot",
            description="Register agricultural or forestry production plot with EUDR coordinates (Regulation EU 2023/1115).",
        )
        def mekong_supplychain_plot(
            farmer_name: str,
            province: str,
            commodity: str,
            latitude: float,
            longitude: float,
            area_hectares: float,
            district: str = "Tây Nguyên",
            deforestation_free_post_2020: bool = True,
            legal_land_cert: str = "Sổ đỏ nông nghiệp / Giấy chứng nhận QSDĐ",
        ) -> str:
            return self._handle_supplychain_plot(
                farmer_name=farmer_name,
                province=province,
                commodity=commodity,
                latitude=latitude,
                longitude=longitude,
                area_hectares=area_hectares,
                district=district,
                deforestation_free_post_2020=deforestation_free_post_2020,
                legal_land_cert=legal_land_cert,
            )

        @app.tool(
            name="mekong_supplychain_batch",
            description="Initialize export traceability batch with plot linkage and SHA-256 fingerprint.",
        )
        def mekong_supplychain_batch(
            batch_code: str,
            commodity: str,
            quantity_kg: float,
            processor_name: str,
            plot_ids: list[str] = None,
            certifications: list[str] = None,
        ) -> str:
            return self._handle_supplychain_batch(
                batch_code=batch_code,
                commodity=commodity,
                quantity_kg=quantity_kg,
                processor_name=processor_name,
                plot_ids=plot_ids,
                certifications=certifications,
            )

        @app.tool(
            name="mekong_supplychain_event",
            description="Record EPCIS custody transfer event with cryptographic hash chaining (GS1 EPCIS 2.0).",
        )
        def mekong_supplychain_event(
            batch_code: str,
            event_type: str,
            location: str,
            actor_name: str,
            notes: str = "",
        ) -> str:
            return self._handle_supplychain_event(
                batch_code=batch_code,
                event_type=event_type,
                location=location,
                actor_name=actor_name,
                notes=notes,
            )

        @app.tool(
            name="mekong_supplychain_eudr",
            description="Synthesize official EUDR Due Diligence Statement (DDS) dossier for EU export customs.",
        )
        def mekong_supplychain_eudr(
            batch_code: str,
            exporter_name: str,
            importer_name: str,
            destination_country: str = "Germany",
        ) -> str:
            return self._handle_supplychain_eudr(
                batch_code=batch_code,
                exporter_name=exporter_name,
                importer_name=importer_name,
                destination_country=destination_country,
            )

        @app.tool(
            name="mekong_supplychain_trace",
            description="Retrieve complete end-to-end provenance timeline and custody chain for an export batch.",
        )
        def mekong_supplychain_trace(
            batch_code: str,
        ) -> str:
            return self._handle_supplychain_trace(
                batch_code=batch_code,
            )

        @app.tool(
            name="mekong_supplychain_status",
            description="Retrieve supply chain engine telemetry, monitored area, and volume metrics.",
        )
        def mekong_supplychain_status() -> str:
            return self._handle_supplychain_status()

        @app.tool(
            name="mekong_labor_permit",
            description="Assess foreign worker eligibility for work permit or statutory exemption under Decree 152/2020 & 70/2023.",
        )
        def mekong_labor_permit(
            worker_name: str,
            nationality: str,
            position: str,
            job_title: str,
            degree: str = "BACHELOR",
            exp: float = 3.0,
            capital: float = 0.0,
            wto: bool = False,
            married_vn: bool = False,
            passport: str = "PASS-DEFAULT",
        ) -> str:
            return self._handle_labor_permit(
                worker_name=worker_name,
                nationality=nationality,
                position=position,
                job_title=job_title,
                degree=degree,
                exp=exp,
                capital=capital,
                wto=wto,
                married_vn=married_vn,
                passport=passport,
            )

        @app.tool(
            name="mekong_labor_overtime",
            description="Calculate statutory overtime pay and night shift rates under Labor Code 2019 Article 98.",
        )
        def mekong_labor_overtime(
            hourly_rate: float,
            weekday_ot: float = 0.0,
            weekend_ot: float = 0.0,
            holiday_ot: float = 0.0,
            night_regular: float = 0.0,
            night_ot: float = 0.0,
        ) -> str:
            return self._handle_labor_overtime(
                hourly_rate=hourly_rate,
                weekday_ot=weekday_ot,
                weekend_ot=weekend_ot,
                holiday_ot=holiday_ot,
                night_regular=night_regular,
                night_ot=night_ot,
            )

        @app.tool(
            name="mekong_labor_caps",
            description="Audit monthly and annual overtime working hours against Article 107 statutory limits.",
        )
        def mekong_labor_caps(
            employee_id: str,
            employee_name: str,
            monthly_ot_hours: float,
            yearly_cumulative_hours: float,
            industry: str = "GENERAL",
            exceptional: bool = False,
        ) -> str:
            return self._handle_labor_caps(
                employee_id=employee_id,
                employee_name=employee_name,
                monthly_ot_hours=monthly_ot_hours,
                yearly_cumulative_hours=yearly_cumulative_hours,
                industry=industry,
                exceptional=exceptional,
            )

        @app.tool(
            name="mekong_labor_severance",
            description="Calculate statutory severance pay (Article 46) or job loss allowance (Article 47).",
        )
        def mekong_labor_severance(
            employee_name: str,
            average_salary: float,
            total_years: float,
            bhtn_years: float = 0.0,
            allowance_type: str = "SEVERANCE",
        ) -> str:
            return self._handle_labor_severance(
                employee_name=employee_name,
                average_salary=average_salary,
                total_years=total_years,
                bhtn_years=bhtn_years,
                allowance_type=allowance_type,
            )

        @app.tool(
            name="mekong_labor_regulations",
            description="Audit Internal Labor Regulations (NQLD) compliance under Article 118 for enterprises with 10+ employees.",
        )
        def mekong_labor_regulations(
            enterprise_name: str,
            total_employees: int,
            has_written_regulations: bool = True,
            is_registered: bool = True,
            dialogue: bool = True,
            safety_council: bool = True,
            docket: str = "NQLD-2026-DOLAB",
        ) -> str:
            return self._handle_labor_regulations(
                enterprise_name=enterprise_name,
                total_employees=total_employees,
                has_written_regulations=has_written_regulations,
                is_registered=is_registered,
                dialogue=dialogue,
                safety_council=safety_council,
                docket=docket,
            )

        @app.tool(
            name="mekong_labor_list",
            description="Query registered foreign worker permit dossiers and audit records.",
        )
        def mekong_labor_list(
            category: str = "ALL",
            limit: int = 50,
        ) -> str:
            return self._handle_labor_list(
                category=category,
                limit=limit,
            )

        @app.tool(
            name="mekong_labor_status",
            description="Retrieve Vietnamese labor compliance engine metrics, telemetry, and statutory threshold status.",
        )
        def mekong_labor_status() -> str:
            return self._handle_labor_status()

        @app.tool(
            name="mekong_maritime_vessel",
            description="Register commercial vessel call, schedule berthing, and audit channel draft requirements.",
        )
        def mekong_maritime_vessel(
            name: str,
            imo: str,
            flag: str,
            dwt: float,
            grt: float,
            loa: float,
            draft: float,
            port_code: str,
            terminal: str,
            eta: str,
            etd: str,
            call_sign: str = "3XYZ",
        ) -> str:
            return self._handle_maritime_vessel(
                name=name,
                imo=imo,
                flag=flag,
                dwt=dwt,
                grt=grt,
                loa=loa,
                draft=draft,
                port_code=port_code,
                terminal=terminal,
                eta=eta,
                etd=etd,
                call_sign=call_sign,
            )

        @app.tool(
            name="mekong_maritime_container",
            description="Record container inventory, 3D yard slot location, and SOLAS VGM gross mass compliance.",
        )
        def mekong_maritime_container(
            container_no: str,
            container_type: str,
            gross_weight: float,
            seal: str,
            booking_or_bl: str,
            slot: str = "YARD-B01-R03-T2",
            tare: float = 2300.0,
            reefer: bool = False,
            dg: bool = False,
        ) -> str:
            return self._handle_maritime_container(
                container_no=container_no,
                container_type=container_type,
                gross_weight=gross_weight,
                seal=seal,
                booking_or_bl=booking_or_bl,
                slot=slot,
                tare=tare,
                reefer=reefer,
                dg=dg,
            )

        @app.tool(
            name="mekong_maritime_tariff",
            description="Compute statutory berth dues, pilotage fees, and container LoLo stevedoring tariffs (Circular 39/2023).",
        )
        def mekong_maritime_tariff(
            vessel_call: str,
            group: str,
            grt: float,
            berth_hours: float,
            distance: float = 18.0,
            f20: int = 0,
            f40: int = 0,
            e20: int = 0,
            e40: int = 0,
            reefer_hrs: float = 0.0,
            reefer_cnt: int = 0,
            terminal: str = "Tân Cảng Cát Lái",
        ) -> str:
            return self._handle_maritime_tariff(
                vessel_call=vessel_call,
                group=group,
                grt=grt,
                berth_hours=berth_hours,
                distance=distance,
                f20=f20,
                f40=f40,
                e20=e20,
                e40=e40,
                reefer_hrs=reefer_hrs,
                reefer_cnt=reefer_cnt,
                terminal=terminal,
            )

        @app.tool(
            name="mekong_maritime_manifest",
            description="Submit electronic sea cargo e-Manifest to VNACCS / National Single Window.",
        )
        def mekong_maritime_manifest(
            vessel_call: str,
            bl: str,
            shipper: str,
            consignee: str,
            cargo: str,
            containers: int,
            gross_kg: float,
            decl_no: typing.Optional[str] = None,
        ) -> str:
            return self._handle_maritime_manifest(
                vessel_call=vessel_call,
                bl=bl,
                shipper=shipper,
                consignee=consignee,
                cargo=cargo,
                containers=containers,
                gross_kg=gross_kg,
                decl_no=decl_no,
            )

        @app.tool(
            name="mekong_maritime_list",
            description="Query scheduled vessel calls or container inventory in terminal yards and ICD depots.",
        )
        def mekong_maritime_list(
            item_type: str = "vessels",
            yard: str = "ALL",
            limit: int = 50,
        ) -> str:
            return self._handle_maritime_list(
                item_type=item_type,
                yard=yard,
                limit=limit,
            )

        @app.tool(
            name="mekong_maritime_status",
            description="Retrieve Vietnamese maritime logistics, vessel schedule, and terminal yard metrics.",
        )
        def mekong_maritime_status() -> str:
            return self._handle_maritime_status()

        @app.tool(
            name="mekong_energy_solar",
            description="Evaluate rooftop solar (ĐMTMN) self-consumption, Decree 135/2024 surplus caps, and carbon offsets.",
        )
        def mekong_energy_solar(
            project_id: str,
            capacity_kwp: float,
            location: str = "Binh Thuan",
            self_consumption_pct: float = 80.0,
            grid_connection: str = "connected",
            battery_storage_kwh: float = 0.0,
        ) -> str:
            return self._handle_energy_solar(
                project_id=project_id,
                capacity_kwp=capacity_kwp,
                location=location,
                self_consumption_pct=self_consumption_pct,
                grid_connection=grid_connection,
                battery_storage_kwh=battery_storage_kwh,
            )

        @app.tool(
            name="mekong_energy_dppa",
            description="Evaluate Direct Power Purchase Agreement (DPPA) under Decree 80/2024, private wire vs national grid CfD settlement.",
        )
        def mekong_energy_dppa(
            contract_id: str,
            buyer_id: str,
            seller_id: str,
            mechanism: str = "direct",
            contract_kwh_month: float = 500000.0,
            strike_price_vnd_kwh: float = 1800.0,
            spot_price_vnd_kwh: float = 1650.0,
        ) -> str:
            return self._handle_energy_dppa(
                contract_id=contract_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                mechanism=mechanism,
                contract_kwh_month=contract_kwh_month,
                strike_price_vnd_kwh=strike_price_vnd_kwh,
                spot_price_vnd_kwh=spot_price_vnd_kwh,
            )

        @app.tool(
            name="mekong_energy_ev",
            description="Simulate EV charging station session, TCVN 13078 / IEC 61851 charger specs, Decision 2699 TOU billing, and CO2 offset.",
        )
        def mekong_energy_ev(
            session_id: str,
            station_id: str,
            charger_type: str = "DC_120kW",
            energy_kwh: float = 45.0,
            tou_period: str = "normal",
            ev_model: str = "VF8",
        ) -> str:
            return self._handle_energy_ev(
                session_id=session_id,
                station_id=station_id,
                charger_type=charger_type,
                energy_kwh=energy_kwh,
                tou_period=tou_period,
                ev_model=ev_model,
            )

        @app.tool(
            name="mekong_energy_list",
            description="Query registered rooftop solar projects, DPPA bilateral contracts, or EV charging stations.",
        )
        def mekong_energy_list(
            item_type: str = "solar",
            limit: int = 50,
        ) -> str:
            return self._handle_energy_list(
                item_type=item_type,
                limit=limit,
            )

        @app.tool(
            name="mekong_energy_status",
            description="Retrieve Vietnamese renewable energy grid metrics, DPPA settlements, and EV charging network summary.",
        )
        def mekong_energy_status() -> str:
            return self._handle_energy_status()

        @app.tool(
            name="mekong_privacy_audit",
            description="Audit enterprise compliance against Decree 13/2023/ND-CP (PDPD), identify gaps, and recommend DPO / DPIA actions.",
        )
        def mekong_privacy_audit(
            enterprise_name: str,
            controller_type: str = "CONTROLLER_AND_PROCESSOR",
            has_sensitive_data: bool = False,
            has_dpo: bool = False,
            has_cross_border: bool = False,
            has_dpia_dossier: bool = True,
        ) -> str:
            return self._handle_privacy_audit(
                enterprise_name=enterprise_name,
                controller_type=controller_type,
                has_sensitive_data=has_sensitive_data,
                has_dpo=has_dpo,
                has_cross_border=has_cross_border,
                has_dpia_dossier=has_dpia_dossier,
            )

        @app.tool(
            name="mekong_privacy_dpia",
            description="Create Personal Data Processing Impact Assessment (DPIA Form 04) under Article 24 Decree 13/2023/ND-CP for A05 filing.",
        )
        def mekong_privacy_dpia(
            activity_name: str,
            processing_purpose: str,
            data_categories: list[str],
            legal_basis: str = "CONSENT",
            security_measures: str = "AES-256 Encryption, RBAC, TLS 1.3",
        ) -> str:
            return self._handle_privacy_dpia(
                activity_name=activity_name,
                processing_purpose=processing_purpose,
                data_categories=data_categories,
                legal_basis=legal_basis,
                security_measures=security_measures,
            )

        @app.tool(
            name="mekong_privacy_transfer",
            description="Evaluate overseas cross-border data transfer compliance and SCC agreement under Article 25 Decree 13/2023/ND-CP.",
        )
        def mekong_privacy_transfer(
            transfer_name: str,
            recipient_entity: str,
            destination_country: str,
            data_types: list[str],
            record_count: int = 1000,
            has_scc: bool = True,
        ) -> str:
            return self._handle_privacy_transfer(
                transfer_name=transfer_name,
                recipient_entity=recipient_entity,
                destination_country=destination_country,
                data_types=data_types,
                record_count=record_count,
                has_scc=has_scc,
            )

        @app.tool(
            name="mekong_privacy_breach",
            description="Report personal data breach incident, track mitigation, and enforce 72-hour statutory notification to A05 (Article 26).",
        )
        def mekong_privacy_breach(
            incident_name: str,
            severity: str,
            affected_count: int,
            breach_type: str,
            hours_elapsed: float = 2.0,
            mitigation_plan: str = "Revoked compromised tokens, enabled network isolation, activated incident team",
        ) -> str:
            return self._handle_privacy_breach(
                incident_name=incident_name,
                severity=severity,
                affected_count=affected_count,
                breach_type=breach_type,
                hours_elapsed=hours_elapsed,
                mitigation_plan=mitigation_plan,
            )

        @app.tool(
            name="mekong_privacy_dsar",
            description="Process Article 9 Data Subject Access Request (access, delete, withdraw consent, restrict processing).",
        )
        def mekong_privacy_dsar(
            request_type: str,
            subject_id: str,
            details: str = "Request under Article 9 PDPD",
        ) -> str:
            return self._handle_privacy_dsar(
                request_type=request_type,
                subject_id=subject_id,
                details=details,
            )

        @app.tool(
            name="mekong_privacy_list",
            description="Query registered DPIA assessments, cross-border transfers, data breach incidents, or DSAR requests.",
        )
        def mekong_privacy_list(
            item_type: str = "dpia",
            limit: int = 50,
        ) -> str:
            return self._handle_privacy_list(
                item_type=item_type,
                limit=limit,
            )

        @app.tool(
            name="mekong_privacy_status",
            description="Retrieve Vietnamese Personal Data Protection Decree (PDPD Decree 13/2023) compliance metrics and telemetry.",
        )
        def mekong_privacy_status() -> str:
            return self._handle_privacy_status()

        @app.tool(
            name="mekong_aviation_flight",
            description="Register commercial flight movement, aircraft specs (MTOW), and apron/gate parking allocation.",
        )
        def mekong_aviation_flight(
            flight_no: str,
            aircraft_type: str,
            origin_airport: str,
            dest_airport: str,
            mtow_tons: float = 90.0,
            parking_hours: float = 2.0,
            is_international: bool = True,
        ) -> str:
            return self._handle_aviation_flight(
                flight_no=flight_no,
                aircraft_type=aircraft_type,
                origin_airport=origin_airport,
                dest_airport=dest_airport,
                mtow_tons=mtow_tons,
                parking_hours=parking_hours,
                is_international=is_international,
            )

        @app.tool(
            name="mekong_aviation_cargo",
            description="Calculate IATA volumetric chargeable weight (1 CBM = 166.67 kg) and air freight density rating.",
        )
        def mekong_aviation_cargo(
            mawb_no: str,
            origin_airport: str,
            dest_airport: str,
            piece_count: int,
            gross_weight_kg: float,
            volume_cbm: float,
            cargo_type: str = "GENERAL",
            temperature_regime: str = "AMBIENT",
        ) -> str:
            return self._handle_aviation_cargo(
                mawb_no=mawb_no,
                origin_airport=origin_airport,
                dest_airport=dest_airport,
                piece_count=piece_count,
                gross_weight_kg=gross_weight_kg,
                volume_cbm=volume_cbm,
                cargo_type=cargo_type,
                temperature_regime=temperature_regime,
            )

        @app.tool(
            name="mekong_aviation_tariff",
            description="Calculate statutory landing/takeoff, aircraft parking, security screening, and ramp handling fees (Circular 53/2019).",
        )
        def mekong_aviation_tariff(
            flight_no: str,
            airport_code: str,
            mtow_tons: float,
            parking_hours: float = 2.0,
            cargo_tons: float = 10.0,
            is_international: bool = True,
        ) -> str:
            return self._handle_aviation_tariff(
                flight_no=flight_no,
                airport_code=airport_code,
                mtow_tons=mtow_tons,
                parking_hours=parking_hours,
                cargo_tons=cargo_tons,
                is_international=is_international,
            )

        @app.tool(
            name="mekong_aviation_dg",
            description="Evaluate Dangerous Goods declaration under IATA DGR and enforce passenger aircraft prohibitions (PAX vs CAO).",
        )
        def mekong_aviation_dg(
            un_number: str,
            proper_shipping_name: str,
            hazard_class: str,
            packing_group: str = "II",
            quantity_kg: float = 10.0,
            aircraft_type: str = "PAX_AND_CARGO",
        ) -> str:
            return self._handle_aviation_dg(
                un_number=un_number,
                proper_shipping_name=proper_shipping_name,
                hazard_class=hazard_class,
                packing_group=packing_group,
                quantity_kg=quantity_kg,
                aircraft_type=aircraft_type,
            )

        @app.tool(
            name="mekong_aviation_list",
            description="Query registered flight schedules, air cargo shipments, or Dangerous Goods declarations.",
        )
        def mekong_aviation_list(
            item_type: str = "flights",
            limit: int = 50,
        ) -> str:
            return self._handle_aviation_list(
                item_type=item_type,
                limit=limit,
            )

        @app.tool(
            name="mekong_aviation_status",
            description="Retrieve Vietnamese civil aviation network metrics, airport revenue, and air freight telemetry.",
        )
        def mekong_aviation_status() -> str:
            return self._handle_aviation_status()

        @app.tool(
            name="mekong_ecom_fct",
            description="Calculate digital services Foreign Contractor Tax (FCT - VAT & CIT) under Decree 126/2020 & Circular 80/2021.",
        )
        def mekong_ecom_fct(
            foreign_supplier_name: str,
            supplier_etax_code: str,
            service_category: str,
            revenue_usd: float = 0.0,
            revenue_vnd: float = 0.0,
            quarter: str = "Q1-2026",
        ) -> str:
            return self._handle_ecom_fct(
                foreign_supplier_name=foreign_supplier_name,
                supplier_etax_code=supplier_etax_code,
                service_category=service_category,
                revenue_usd=revenue_usd,
                revenue_vnd=revenue_vnd,
                quarter=quarter,
            )

        @app.tool(
            name="mekong_ecom_audit",
            description="Audit e-commerce platform compliance and statutory licensing under Decree 52/2013 & Decree 85/2021.",
        )
        def mekong_ecom_audit(
            platform_name: str,
            domain_url: str,
            platform_type: str = "MARKETPLACE",
            enterprise_tax_id: str = "0109999999",
            has_operating_regulations: bool = True,
            has_dispute_mechanism: bool = True,
            has_seller_kyc: bool = True,
            has_data_retention_3yr: bool = True,
            has_tax_reporting_system: bool = True,
        ) -> str:
            return self._handle_ecom_audit(
                platform_name=platform_name,
                domain_url=domain_url,
                platform_type=platform_type,
                enterprise_tax_id=enterprise_tax_id,
                has_operating_regulations=has_operating_regulations,
                has_dispute_mechanism=has_dispute_mechanism,
                has_seller_kyc=has_seller_kyc,
                has_data_retention_3yr=has_data_retention_3yr,
                has_tax_reporting_system=has_tax_reporting_system,
            )

        @app.tool(
            name="mekong_ecom_order",
            description="Settle marketplace order finances, compute seller net payout, and generate electronic invoice under Decree 123/2020.",
        )
        def mekong_ecom_order(
            order_code: str,
            platform_id: str,
            seller_id: str,
            buyer_id: str,
            gmv_gross_vnd: float,
            platform_commission_pct: float = 6.0,
            payment_fee_pct: float = 2.5,
            shop_voucher_vnd: float = 0.0,
            platform_voucher_vnd: float = 0.0,
            shipping_fee_vnd: float = 30000.0,
            vat_rate_pct: int = 10,
        ) -> str:
            return self._handle_ecom_order(
                order_code=order_code,
                platform_id=platform_id,
                seller_id=seller_id,
                buyer_id=buyer_id,
                gmv_gross_vnd=gmv_gross_vnd,
                platform_commission_pct=platform_commission_pct,
                payment_fee_pct=payment_fee_pct,
                shop_voucher_vnd=shop_voucher_vnd,
                platform_voucher_vnd=platform_voucher_vnd,
                shipping_fee_vnd=shipping_fee_vnd,
                vat_rate_pct=vat_rate_pct,
            )

        @app.tool(
            name="mekong_ecom_parcel",
            description="Evaluate cross-border express parcel customs duty & VAT exemption threshold under statutory de minimis rules.",
        )
        def mekong_ecom_parcel(
            tracking_no: str,
            shipper_country: str,
            consignee_name: str,
            item_description: str,
            customs_value_usd: float = 0.0,
            customs_value_vnd: float = 0.0,
            import_duty_pct: float = 10.0,
        ) -> str:
            return self._handle_ecom_parcel(
                tracking_no=tracking_no,
                shipper_country=shipper_country,
                consignee_name=consignee_name,
                item_description=item_description,
                customs_value_usd=customs_value_usd,
                customs_value_vnd=customs_value_vnd,
                import_duty_pct=import_duty_pct,
            )

        @app.tool(
            name="mekong_ecom_list",
            description="Query registered e-commerce platforms, FCT tax declarations, marketplace orders, or cross-border parcels.",
        )
        def mekong_ecom_list(
            item_type: str = "platforms",
            limit: int = 50,
        ) -> str:
            return self._handle_ecom_list(
                item_type=item_type,
                limit=limit,
            )

        @app.tool(
            name="mekong_ecom_status",
            description="Retrieve Vietnamese e-commerce compliance telemetry, digital tax metrics, and order settlement statistics.",
        )
        def mekong_ecom_status() -> str:
            return self._handle_ecom_status()

        @app.tool(
            name="mekong_telecom_spectrum",
            description="Calculate spectrum auction reserve valuation, deposit, and network rollout obligations under Decree 63/2023/ND-CP.",
        )
        def mekong_telecom_spectrum(
            band_code: str,
            license_years: int = 15,
            deposit_pct: float = 10.0,
            custom_reserve_price_vnd: float = 0.0,
        ) -> str:
            return self._handle_telecom_spectrum(
                band_code=band_code,
                license_years=license_years,
                deposit_pct=deposit_pct,
                custom_reserve_price_vnd=custom_reserve_price_vnd,
            )

        @app.tool(
            name="mekong_telecom_ott",
            description="Audit OTT messaging, VoIP & digital communication service compliance under Telecommunications Law 2023.",
        )
        def mekong_telecom_ott(
            service_name: str,
            provider_name: str,
            service_category: str = "OTT_MESSAGING_VOICE",
            registered_users: int = 1000000,
            has_kyc_verification: bool = True,
            has_encryption_e2ee: bool = True,
            has_local_data_storage: bool = True,
            has_vnta_notification: bool = True,
            has_consumer_dispute_system: bool = True,
        ) -> str:
            return self._handle_telecom_ott(
                service_name=service_name,
                provider_name=provider_name,
                service_category=service_category,
                registered_users=registered_users,
                has_kyc_verification=has_kyc_verification,
                has_encryption_e2ee=has_encryption_e2ee,
                has_local_data_storage=has_local_data_storage,
                has_vnta_notification=has_vnta_notification,
                has_consumer_dispute_system=has_consumer_dispute_system,
            )

        @app.tool(
            name="mekong_telecom_bts",
            description="Evaluate base transceiver station (BTS) electromagnetic field (EMF) exposure safety against QCVN 08:2020/BTTTT.",
        )
        def mekong_telecom_bts(
            station_id: str,
            location: str,
            antenna_height_m: float = 30.0,
            transmit_power_watts: float = 80.0,
            frequency_mhz: float = 2600.0,
            antenna_gain_dbi: float = 18.0,
            distance_residential_m: float = 25.0,
        ) -> str:
            return self._handle_telecom_bts(
                station_id=station_id,
                location=location,
                antenna_height_m=antenna_height_m,
                transmit_power_watts=transmit_power_watts,
                frequency_mhz=frequency_mhz,
                antenna_gain_dbi=antenna_gain_dbi,
                distance_residential_m=distance_residential_m,
            )

        @app.tool(
            name="mekong_telecom_number",
            description="Allocate national telecom numbering resources (1900, 1800, Mobile) and compute maintenance fees under Circular 25/2015.",
        )
        def mekong_telecom_number(
            number_prefix: str,
            assigned_operator: str,
            block_size: int = 10000,
            service_purpose: str = "MOBILE_SUBSCRIBER",
        ) -> str:
            return self._handle_telecom_number(
                number_prefix=number_prefix,
                assigned_operator=assigned_operator,
                block_size=block_size,
                service_purpose=service_purpose,
            )

        @app.tool(
            name="mekong_telecom_list",
            description="Query registered spectrum auctions, OTT compliance audits, BTS safety evals, or numbering resources.",
        )
        def mekong_telecom_list(
            item_type: str = "spectrum",
            limit: int = 50,
        ) -> str:
            return self._handle_telecom_list(
                item_type=item_type,
                limit=limit,
            )

        @app.tool(
            name="mekong_telecom_status",
            description="Retrieve Vietnamese telecommunications telemetry, spectrum auctions, and OTT compliance status.",
        )
        def mekong_telecom_status() -> str:
            return self._handle_telecom_status()













    # ==============================================================
    # Handler implementations
    # ==============================================================

    # ── Memory ────────────────────────────────────────────────────────

    def _handle_memory_search(self, query: str, limit: int = 10) -> str:
        """Search AI OS memory by query using NeuralMemory or MemoryStore."""
        # Try NeuralMemory provider first
        mem = _get_memory()
        if mem is not None:
            try:
                # Try query_memory (NeuralMemoryClient) or search (Mem0 facade)
                if hasattr(mem, "query_memory"):
                    result = mem.query_memory(query, depth=limit)
                    if result:
                        return _ok({"query": query, "results": result[:2000]})
                elif hasattr(mem, "search"):
                    hits = mem.search(query, user_id="mekong:mcp")
                    if hits:
                        return _ok({"query": query, "results": str(hits)[:2000]})
                return _ok({"query": query, "results": [], "note": "No matching memories"})
            except Exception as exc:
                logger.warning("Memory search failed: %s", exc)
                return _err(f"Memory search error: {exc}")

        # Fallback: YAML MemoryStore
        store = _get_memory_store()
        if store is not None:
            try:
                entries = store.query(query)
                results = [
                    {
                        "goal": e.goal,
                        "status": e.status,
                        "timestamp": getattr(e, "timestamp", 0),
                        "error_summary": getattr(e, "error_summary", ""),
                    }
                    for e in (entries or [])[:limit]
                ]
                return _ok({"query": query, "results": results})
            except Exception as exc:
                logger.warning("MemoryStore search failed: %s", exc)
                return _err(f"MemoryStore search error: {exc}")

        return _missing("memory_search")

    def _handle_memory_consolidate(self) -> str:
        """Consolidate memories by compressing old entries in MemoryStore."""
        store = _get_memory_store()
        if store is not None:
            try:
                count = store.compress_old_memories(days_threshold=7, keep_recent=100)
                stats = store.stats()
                return _ok({
                    "compressed": count,
                    "total_entries": stats.get("total", 0),
                    "success_rate": stats.get("success_rate", 0),
                })
            except Exception as exc:
                logger.warning("Memory consolidate failed: %s", exc)
                return _err(f"Memory consolidate error: {exc}")

        # If MemoryStore not available, report but don't fail
        return _ok({
            "compressed": 0,
            "note": "Memory consolidation requires MemoryStore (YAML-backed)",
        })

    # ── Tasks ─────────────────────────────────────────────────────────

    def _handle_tasks_list(self, status: str = "") -> str:
        """List tasks from McpTaskStore."""
        try:
            store = get_task_store()
            tasks = store.list(status=status)
            return _ok({
                "tasks": [t.to_dict() for t in tasks],
                "count": len(tasks),
                "stats": store.stats(),
            })
        except Exception as exc:
            logger.warning("Task list failed: %s", exc)
            return _err(f"Task list error: {exc}")

    def _handle_tasks_create(self, subject: str) -> str:
        try:
            store = get_task_store()
            task = store.create(subject)
            return _ok({
                "created": True,
                "task": task.to_dict(),
            })
        except Exception as exc:
            logger.warning("Task create failed: %s", exc)
            return _err(f"Task create error: {exc}")

    def _handle_tasks_done(self, task_id: str) -> str:
        try:
            store = get_task_store()
            task = store.update_status(task_id, "done")
            if task is None:
                return _err(f"Task '{task_id}' not found")
            return _ok({
                "updated": True,
                "task": task.to_dict(),
            })
        except Exception as exc:
            logger.warning("Task done failed: %s", exc)
            return _err(f"Task done error: {exc}")

    def _handle_tasks_start(self, task_id: str) -> str:
        try:
            store = get_task_store()
            task = store.update_status(task_id, "in-progress")
            if task is None:
                return _err(f"Task '{task_id}' not found")
            return _ok({
                "updated": True,
                "task": task.to_dict(),
            })
        except Exception as exc:
            logger.warning("Task start failed: %s", exc)
            return _err(f"Task start error: {exc}")

    def _handle_tasks_delete(self, task_id: str) -> str:
        try:
            store = get_task_store()
            if store.delete(task_id):
                return _ok({"deleted": True, "task_id": task_id})
            return _err(f"Task '{task_id}' not found")
        except Exception as exc:
            logger.warning("Task delete failed: %s", exc)
            return _err(f"Task delete error: {exc}")

    # ── Agents ────────────────────────────────────────────────────────

    def _handle_agents_list(self) -> str:
        """List registered agents from AgentRegistry."""
        reg = _get_agent_registry()
        if reg is not None:
            try:
                agents = reg.list_agents()
                return _ok({"agents": agents, "count": len(agents)})
            except Exception as exc:
                logger.warning("Agent list failed: %s", exc)
                return _err(f"Agent list error: {exc}")
        return _missing("agent_registry")

    def _handle_agents_start(self, template: str, args: str = "") -> str:
        """Start an agent — delegates to agent dispatcher."""
        if not _HAS_AGENT_REGISTRY:
            return _missing("agent_registry")

        try:
            from src.core.agent_dispatcher import load_agent_prompt

            prompt = load_agent_prompt(template)
            return _ok({
                "agent": template,
                "prompt": prompt[:500],
                "note": (
                    f"Agent '{template}' prompt loaded. "
                    "Full autonomous agent execution requires the Mekong "
                    "orchestrator pipeline (hybrid_router). "
                    "Use `mekong agent start <template>` in the CLI."
                ),
            })
        except Exception as exc:
            logger.warning("Agent start failed: %s", exc)
            return _err(f"Agent start error: {exc}")

    def _handle_agents_stop(self, name: str) -> str:
        """Stop an agent — placeholder until agent lifecycle is in core."""
        return _ok({
            "stopped": False,
            "note": (
                f"Agent '{name}' stop requested. "
                "Agent lifecycle management is available via "
                "`mekong agent stop <name>` in the CLI."
            ),
        })

    # ── Skills ────────────────────────────────────────────────────────

    def _handle_skills_list(self) -> str:
        """List available skills by scanning .opencode/skills/ and .claude/skills/."""
        skills: list[dict[str, str]] = []
        skill_dirs = [
            Path(os.path.expanduser("~/.opencode/skills")),
            Path(os.path.expanduser("~/.claude/skills")),
        ]
        for sdir in skill_dirs:
            if sdir.exists():
                try:
                    for child in sorted(sdir.iterdir()):
                        if child.is_dir():
                            skills.append({
                                "name": child.name,
                                "source": str(sdir),
                            })
                except PermissionError:
                    logger.warning("Cannot read skill directory: %s", sdir)

        return _ok({"skills": skills, "count": len(skills)})

    # ── MCP System ────────────────────────────────────────────────────

    def _handle_mcp_list(self) -> str:
        """List this MCP server's own tools and any discovered MCP servers."""
        return _ok({
            "mcp_servers": [{"name": self.name, "tools_count": len(self._tools)}],
            "tools": self._tools,
        })

    # ── Plugins ───────────────────────────────────────────────────────

    def _handle_plugins_list(self) -> str:
        """List plugins from PluginRegistry."""
        reg = _get_plugin_registry()
        if reg is not None:
            try:
                # Auto-discover on every list to pick up new plugins
                reg.discover()
                manifests = reg.list_plugins()
                plugins = [
                    {
                        "name": m.name,
                        "version": m.version,
                        "type": m.plugin_type.value if hasattr(m.plugin_type, "value") else str(m.plugin_type),
                        "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                        "source": m.source,
                    }
                    for m in manifests
                ]
                return _ok({"plugins": plugins, "count": len(plugins)})
            except Exception as exc:
                logger.warning("Plugin list failed: %s", exc)
                return _err(f"Plugin list error: {exc}")
        return _missing("plugin_registry")

    def _handle_plugins_install(self, name_url: str) -> str:
        """Install a plugin via PluginRegistry."""
        reg = _get_plugin_registry()
        if reg is not None:
            try:
                manifest = reg.install(name_url)
                return _ok({
                    "installed": True,
                    "name": manifest.name,
                    "version": manifest.version,
                    "source": manifest.source,
                    "status": manifest.status.value if hasattr(manifest.status, "value") else str(manifest.status),
                })
            except RuntimeError as exc:
                return _err(f"Plugin install failed: {exc}")
            except Exception as exc:
                logger.warning("Plugin install error: %s", exc)
                return _err(f"Plugin install error: {exc}")
        return _missing("plugin_registry")

    # ── Brainstorm ────────────────────────────────────────────────────

    def _handle_brainstorm(self, topic: str) -> str:
        """Multi-persona brainstorm using the LLM client."""
        try:
            from src.providers.llm.client import get_client as get_llm_client

            client = get_llm_client()
            prompt = (
                f"You are a multi-persona brainstorming facilitator. "
                f"Generate diverse perspectives on the topic: '{topic}'. "
                f"Include viewpoints from a CTO, CMO, COO, and a domain expert. "
                f"Provide structured insights with pros and cons for each perspective."
            )
            response = client.generate(prompt, max_tokens=2000)
            text = response if isinstance(response, str) else getattr(response, "content", str(response))
            return _ok({"topic": topic, "brainstorm": text[:4000]})
        except ImportError:
            return _missing("llm_client (brainstorm)")
        except Exception as exc:
            logger.warning("Brainstorm failed: %s", exc)
            return _err(f"Brainstorm error: {exc}")

    # ── Research Lab ──────────────────────────────────────────────────

    def _handle_lab_start(self, topic: str) -> str:
        """Start a research lab session on a topic."""
        now = datetime.now(tz=timezone.utc).isoformat()
        session = {
            "topic": topic,
            "started_at": now,
            "status": "active",
            "session_id": uuid.uuid4().hex[:12],
        }
        store = _get_memory_store()
        if store is not None:
            try:
                store.save(f"lab:{session['session_id']}", session)
            except Exception:
                pass
        return _ok({
            "lab_started": True,
            "session": session,
            "note": f"Lab session started for '{topic}'. Use cc_lab_status to check active sessions.",
        })

    def _handle_lab_status(self) -> str:
        """List active and recent lab sessions."""
        store = _get_memory_store()
        sessions: list[dict[str, Any]] = []
        if store is not None:
            try:
                all_keys = store.list_keys() if hasattr(store, "list_keys") else []
                lab_keys = [k for k in all_keys if isinstance(k, str) and k.startswith("lab:")]
                for key in lab_keys:
                    data = store.load(key)
                    if data:
                        sessions.append(data)
            except Exception:
                pass
        return _ok({
            "status": "active" if sessions else "idle",
            "active_labs": sessions,
            "count": len(sessions),
        })

    # ── Trading ───────────────────────────────────────────────────────

    def _handle_trading_analyze(self, symbol: str) -> str:
        """Analyze a trading symbol using LLM."""
        try:
            from src.providers.llm.client import get_client as get_llm_client
            client = get_llm_client()
            prompt = (
                f"Provide a multi-perspective analysis of {symbol} as a trading asset. "
                f"Include: 1) Technical analysis overview, 2) Fundamental factors, "
                f"3) Market sentiment, 4) Key support/resistance levels (hypothetical), "
                f"5) Risk factors. Label clearly that this is AI-generated analysis, "
                f"not financial advice. Be concise (max 600 words)."
            )
            response = client.generate(prompt, max_tokens=2000)
            text = response if isinstance(response, str) else getattr(response, "content", str(response))
            return _ok({
                "symbol": symbol.upper(),
                "analysis": text[:4000],
                "disclaimer": "AI-generated analysis for educational purposes only. Not financial advice.",
            })
        except ImportError:
            return _ok({
                "symbol": symbol.upper(),
                "analysis": "LLM client not available for analysis.",
                "disclaimer": "Install llm_client to enable AI-powered trading analysis.",
            })
        except Exception as exc:
            logger.warning("Trading analysis failed: %s", exc)
            return _err(f"Trading analysis error: {exc}")

    def _handle_trading_price(self, symbol: str) -> str:
        """Get AI-informed analysis for a trading symbol's price context."""
        try:
            from src.providers.llm.client import get_client as get_llm_client
            client = get_llm_client()
            prompt = (
                f"Provide recent price context and market conditions for {symbol}. "
                f"Discuss typical price ranges, volatility patterns, and any notable "
                f"market events affecting this asset. Be concise (max 300 words). "
                f"Clearly state this is AI-generated context, not real-time pricing."
            )
            response = client.generate(prompt, max_tokens=1000)
            text = response if isinstance(response, str) else getattr(response, "content", str(response))
            return _ok({
                "symbol": symbol.upper(),
                "price_context": text[:2000],
                "disclaimer": (
                    "AI-generated context, not real-time market data. "
                    "Use a dedicated price feed API for current prices."
                ),
            })
        except ImportError:
            return _ok({
                "symbol": symbol.upper(),
                "price_context": "LLM client not available.",
                "disclaimer": "Install llm_client for AI-powered price context.",
            })
        except Exception as exc:
            logger.warning("Trading price lookup failed: %s", exc)
            return _err(f"Trading price error: {exc}")

    # ── Monitor ───────────────────────────────────────────────────────

    def _handle_monitor_run(self, topic: str = "") -> str:
        """Start monitoring a topic or subscription."""
        now = datetime.now(tz=timezone.utc).isoformat()
        topic = topic.strip() or "all subscriptions"
        monitor_id = uuid.uuid4().hex[:12]
        session = {
            "monitor_id": monitor_id,
            "topic": topic,
            "started_at": now,
            "interval_seconds": 300,
            "status": "active",
        }
        store = _get_memory_store()
        if store is not None:
            try:
                store.save(f"monitor:{monitor_id}", session)
            except Exception:
                pass
        return _ok({
            "monitor_started": True,
            "session": session,
            "note": f"Monitoring '{topic}'. Use cc_monitor_status to check active monitors.",
        })

    def _handle_monitor_status(self) -> str:
        """List active and recent monitor sessions."""
        store = _get_memory_store()
        sessions: list[dict[str, Any]] = []
        if store is not None:
            try:
                all_keys = store.list_keys() if hasattr(store, "list_keys") else []
                monitor_keys = [k for k in all_keys if isinstance(k, str) and k.startswith("monitor:")]
                for key in monitor_keys:
                    data = store.load(key)
                    if data:
                        sessions.append(data)
            except Exception:
                pass
        return _ok({
            "status": "active" if sessions else "idle",
            "active_monitors": sessions,
            "count": len(sessions),
        })

    # ── Plan Mode ─────────────────────────────────────────────────────

    def _handle_plan_start(self, description: str) -> str:
        """Enter plan mode — decomposes goal into tasks via PlanStore."""
        if not _HAS_MCP_PLAN_STORE:
            return _missing("mcp_plan_store")
        try:
            store = get_plan_store()
            plan = store.create(description)
            return _ok({
                "plan_started": True,
                "plan_id": plan.plan_id,
                "description": description,
                "tasks": plan.tasks,
                "task_count": len(plan.tasks),
                "note": f"Plan {plan.plan_id} created with {len(plan.tasks)} tasks. "
                "Use cc_plan_list to view all plans, cc_plan_done to close.",
            })
        except Exception as exc:
            logger.warning("Plan start failed: %s", exc)
            return _err(f"Plan start error: {exc}")

    def _handle_plan_list(self, status: str = "") -> str:
        """List saved plans from PlanStore."""
        if not _HAS_MCP_PLAN_STORE:
            return _missing("mcp_plan_store")
        try:
            store = get_plan_store()
            plans = store.list(status=status)
            return _ok({
                "plans": [p.to_dict() for p in plans],
                "count": len(plans),
            })
        except Exception as exc:
            logger.warning("Plan list failed: %s", exc)
            return _err(f"Plan list error: {exc}")

    def _handle_plan_done(self, plan_id: str) -> str:
        """Mark a plan as completed."""
        if not _HAS_MCP_PLAN_STORE:
            return _missing("mcp_plan_store")
        try:
            store = get_plan_store()
            plan = store.complete(plan_id)
            if plan is None:
                return _err(f"Plan '{plan_id}' not found")
            return _ok({
                "plan_done": True,
                "plan_id": plan_id,
                "tasks_completed": len(plan.tasks),
                "note": f"Plan {plan_id} completed with {len(plan.tasks)} tasks.",
            })
        except Exception as exc:
            logger.warning("Plan done failed: %s", exc)
            return _err(f"Plan done error: {exc}")

    # ── SSJ ───────────────────────────────────────────────────────────

    def _handle_ssj(self, action: str = "all") -> str:
        """SSJ Developer Mode power menu."""
        actions = {
            "all": self._ssj_all,
            "diagnostics": self._ssj_diagnostics,
            "toggle-logging": self._ssj_toggle_logging,
            "reload-config": self._ssj_reload_config,
            "health-check": self._ssj_health_check,
            "memory-stats": self._ssj_memory_stats,
            "plugin-status": self._ssj_plugin_status,
        }
        handler = actions.get(action)
        if handler is None:
            return _err(
                f"Unknown SSJ action '{action}'. "
                f"Available: {', '.join(sorted(actions))}"
            )
        return handler()

    # ── Command Fabric ────────────────────────────────────────────────

    def _handle_command_fabric_list(self, scope: str = "project", adapter: str = "mcp") -> str:
        """List command fabric adapter manifest."""
        try:
            from src.command_fabric.runtime import command_fabric_manifest
            payload = command_fabric_manifest(adapter=adapter, scope=scope)  # type: ignore[arg-type]
            return _ok(payload)
        except Exception as exc:
            logger.warning("Command fabric list failed: %s", exc)
            return _err(f"Command fabric list error: {exc}")

    def _handle_command_fabric_run(
        self, command: str, args: str = "", scope: str = "project"
    ) -> str:
        """Run or inspect a command fabric definition."""
        if scope not in ("project", "global"):
            return _err(f"Invalid scope '{scope}'. Must be 'project' or 'global'.")
        clean_cmd = command.strip()
        if not clean_cmd:
            return _err("Command cannot be empty.")
        if any(ch in clean_cmd for ch in ("/", "\\", "\0", ";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r", " ")):
            return _err(f"Invalid command name '{clean_cmd}'. Shell metacharacters and path separators are forbidden.")
        if any(ch in args for ch in ("\0", "\n", "\r", ";", "&", "|", "`", "$(")):
            return _err("Command arguments contain forbidden control or shell metacharacters.")
        try:
            from src.command_fabric.runtime import invoke_command_fabric
            result = invoke_command_fabric(command=clean_cmd, args=args, scope=scope)  # type: ignore[arg-type]
            return _ok(result.to_dict())
        except Exception as exc:
            logger.warning("Command fabric run failed: %s", exc)
            return _err(f"Command fabric run error: {exc}")

    def _check_llm_available(self) -> bool:
        """Check if LLM client is available and connected."""
        try:
            from src.providers.llm.client import get_client
            return get_client().is_available
        except Exception:
            return False

    def _ssj_diagnostics(self) -> str:
        """Run system diagnostics."""
        info: dict[str, Any] = {"python": __import__("sys").version}

        try:
            from src.providers.llm.client import get_client
            client = get_client()
            info["llm_available"] = client.is_available
            info["llm_providers"] = [
                p.name for p in client.providers if p.name != "offline"
            ]
        except Exception as exc:
            info["llm"] = f"error: {exc}"

        info["memory_available"] = _HAS_MEMORY or _HAS_MEMORY_STORE
        info["agent_registry"] = _HAS_AGENT_REGISTRY
        info["plugin_registry"] = _HAS_PLUGIN_REGISTRY
        info["mcp_sdk"] = _HAS_MCP

        try:
            import psutil
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            info["memory_percent"] = psutil.virtual_memory().percent
            info["disk_percent"] = psutil.disk_usage("/").percent
        except ImportError:
            pass

        return _ok({"diagnostics": info})

    def _ssj_toggle_logging(self) -> str:
        """Toggle verbose logging on/off."""
        current = os.environ.get("LOG_LEVEL", "WARNING").upper()
        new = "DEBUG" if current == "WARNING" else "WARNING"
        os.environ["LOG_LEVEL"] = new
        logging.getLogger().setLevel(getattr(logging, new, logging.WARNING))
        return _ok({"log_level": new, "previous": current})

    def _ssj_reload_config(self) -> str:
        """Reload .env config file."""
        try:
            from dotenv import load_dotenv  # type: ignore[import-untyped]
        except ImportError:
            return _err("python-dotenv not installed — pip install python-dotenv")

        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            return _err(f"No .env file found at {env_path}")
        try:
            loaded = load_dotenv(env_path, override=True)
            return _ok({
                "reloaded": loaded,
                "path": str(env_path),
            })
        except Exception as exc:
            return _err(f"Reload config error: {exc}")

    def _ssj_health_check(self) -> str:
        """System health check."""
        checks: dict[str, Any] = {}

        try:
            import psutil
            mem = psutil.virtual_memory()
            checks["memory"] = {
                "total_gb": round(mem.total / 1e9, 1),
                "used_gb": round(mem.used / 1e9, 1),
                "percent": mem.percent,
            }
            checks["disk"] = {
                "total_gb": round(psutil.disk_usage("/").total / 1e9, 1),
                "free_gb": round(psutil.disk_usage("/").free / 1e9, 1),
                "percent": psutil.disk_usage("/").percent,
            }
            checks["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            checks["boot_time"] = datetime.fromtimestamp(
                psutil.boot_time(), tz=timezone.utc
            ).isoformat()
        except ImportError:
            checks["note"] = "Install psutil for detailed health metrics"

        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp_c = int(f.read().strip()) / 1000
                checks["thermal_c"] = temp_c
        except OSError:
            pass

        checks["llm_available"] = (
            _HAS_MCP and self._check_llm_available()
        )

        return _ok({"health": checks})

    def _ssj_memory_stats(self) -> str:
        """Get memory store statistics."""
        store = _get_memory_store()
        if store is not None:
            try:
                stats = store.stats() if hasattr(store, "stats") else {}
                return _ok({"memory_stats": stats})
            except Exception as exc:
                return _err(f"Memory stats error: {exc}")

        mem = _get_memory()
        if mem is not None:
            return _ok({
                "memory_stats": "Mem0 provider active (query via cc_memory_search)"
            })
        return _missing("memory_store")

    def _ssj_plugin_status(self) -> str:
        """Get plugin registry status."""
        reg = _get_plugin_registry()
        if reg is not None:
            try:
                manifests = reg.list_plugins()
                return _ok({
                    "plugin_count": len(manifests),
                    "plugins": [
                        {
                            "name": m.name,
                            "version": m.version,
                            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                        }
                        for m in manifests
                    ],
                })
            except Exception as exc:
                return _err(f"Plugin status error: {exc}")
        return _missing("plugin_registry")

    def _ssj_all(self) -> str:
        """Return SSJ menu with a summary of all statuses."""
        diag = json.loads(self._ssj_diagnostics())
        health = json.loads(self._ssj_health_check())
        return _ok({
            "ssj_menu": [
                {"action": "diagnostics", "label": "Run diagnostics"},
                {"action": "toggle-logging", "label": f"Toggle verbose logging (currently {os.environ.get('LOG_LEVEL', 'WARNING')})"},
                {"action": "reload-config", "label": "Reload .env config"},
                {"action": "health-check", "label": "System health check"},
                {"action": "memory-stats", "label": "Memory stats"},
                {"action": "plugin-status", "label": "Plugin status"},
            ],
            "summary": {
                "llm": diag.get("data", {}).get("diagnostics", {}).get("llm_available", "unknown"),
                "health": health.get("data", {}).get("health", {}),
            },
            "note": "Run cc_ssj with a specific action parameter for detailed results.",
        })

    # ── Subagent Bridge ───────────────────────────────────────────────

    def _handle_subagent_dispatch(
        self, role: str, task: str, model_tier: str = "inherit"
    ) -> str:
        """Dynamic subagent bridge returning define_subagent and invoke_subagent payloads."""
        from src.core.subagent_dispatch import handle_subagent_dispatch

        return handle_subagent_dispatch(
            {"role": role, "task": task, "model_tier": model_tier}
        )

    _handle_mekong_subagent_dispatch = _handle_subagent_dispatch

    # ── PEV & Swarm Autonomous Tools ──────────────────────────────────

    def _handle_pev_plan(self, goal: str, mission_id: str = "") -> str:
        """Generate structured PEV plan, tasks, and subagent assignments."""
        goal_clean = _clean_str(goal)
        if not goal_clean:
            return json.dumps(
                {
                    "ok": False,
                    "error": "Goal parameter is required",
                    "code": "EMPTY_GOAL",
                },
                indent=2,
            )
        mission_id_clean = _clean_str(mission_id)
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        try:
            bridge = PEVSwarmBridge()
            plan = bridge.plan(goal=goal_clean, mission_id=mission_id_clean)
            return json.dumps({"ok": True, "plan": plan.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_pev_checkpoint(
        self,
        mission_id: str,
        label: str = "manual",
        files: list[str] | None = None,
        test_results: dict[str, Any] | None = None,
    ) -> str:
        """Capture atomic SQLite checkpoint of workspace files and task states."""
        mid_clean = _clean_str(mission_id)
        if not mid_clean:
            return json.dumps(
                {
                    "ok": False,
                    "error": "mission_id parameter is required",
                    "code": "EMPTY_MISSION_ID",
                },
                indent=2,
            )
        label_clean = _clean_str(label) or "manual"

        if files is not None:
            if isinstance(files, str):
                cleaned_files = [files]
            elif isinstance(files, (list, tuple)):
                if not all(isinstance(f, str) for f in files):
                    return json.dumps(
                        {
                            "ok": False,
                            "error": "files parameter must be an array of strings",
                            "code": "INVALID_FILES_PARAMETER",
                        },
                        indent=2,
                    )
                cleaned_files = [str(f) for f in files if f]
            else:
                return json.dumps(
                    {
                        "ok": False,
                        "error": "files parameter must be an array of strings",
                        "code": "INVALID_FILES_PARAMETER",
                    },
                    indent=2,
                )
        else:
            cleaned_files = None

        if test_results is not None and not isinstance(test_results, dict):
            return json.dumps(
                {
                    "ok": False,
                    "error": "test_results parameter must be an object (dictionary)",
                    "code": "INVALID_TEST_RESULTS_PARAMETER",
                },
                indent=2,
            )

        from src.core.pev_swarm_bridge import PEVSwarmBridge

        try:
            bridge = PEVSwarmBridge()
            cp_id = bridge.store.capture_checkpoint(
                mission_id=mid_clean,
                label=label_clean,
                files=cleaned_files,
                test_results=test_results,
            )
            cp_rec = bridge.store.get_checkpoint(cp_id)
            return json.dumps(
                {
                    "ok": True,
                    "checkpoint_id": cp_id,
                    "mission_id": mid_clean,
                    "label": label_clean,
                    "file_count": len(cp_rec.file_snapshots) if cp_rec else 0,
                    "status": "captured",
                },
                indent=2,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_pev_rollback(self, checkpoint_id: str) -> str:
        """Atomically restore workspace files and task states to a specific checkpoint."""
        cpid_clean = _clean_str(checkpoint_id)
        if not cpid_clean:
            return json.dumps(
                {
                    "ok": False,
                    "error": "checkpoint_id parameter is required",
                    "code": "EMPTY_CHECKPOINT_ID",
                },
                indent=2,
            )
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        try:
            bridge = PEVSwarmBridge()
            res = bridge.store.rollback_to_checkpoint(cpid_clean)
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_swarm_status(self, mission_id: str = "") -> str:
        """Inspect active multi-agent PEV mission progress, cycles, and health."""
        mid_clean = _clean_str(mission_id)
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        try:
            bridge = PEVSwarmBridge()
            if mid_clean:
                res = bridge.get_mission_status(mid_clean)
            else:
                cps = bridge.store.list_checkpoints()
                res = {
                    "ok": True,
                    "active_missions_count": len(cps),
                    "checkpoints": cps[:10],
                    "status": "idle" if not cps else "active",
                }
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    _handle_mekong_pev_plan = _handle_pev_plan
    _handle_mekong_pev_checkpoint = _handle_pev_checkpoint
    _handle_mekong_pev_rollback = _handle_pev_rollback
    _handle_mekong_swarm_status = _handle_swarm_status

    def _handle_eval_query(self, agent_id: str = "all", days: int = 7, limit: int = 50) -> str:
        """Query offline mission evaluations, p95 durations, failure clusters, and recommendations."""
        from src.core.evals_bridge import query_evals

        try:
            aid = _clean_str(agent_id) or "all"
            d = int(days) if days is not None else 7
            lim = int(limit) if limit is not None else 50
            res = query_evals(agent_id=aid, window_days=d, limit=lim)
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_recipe_evolve(self, recipe_name: str = "", goal: str = "", force: bool = False) -> str:
        """Trigger self-improvement and recipe evolution for a goal or recipe based on failure clusters."""
        from src.core.memory_canonical import MemoryStore
        from src.core.recipe_gen import RecipeGenerator
        from src.core.self_improve import SelfImprover

        try:
            rname = _clean_str(recipe_name) or ""
            gtext = _clean_str(goal) or ""
            improver = SelfImprover(MemoryStore(), RecipeGenerator())
            if rname:
                entry = improver.evolve_recipe(recipe_name=rname, target_goal=gtext, force=bool(force))
                stats = improver.get_evolution_stats()
                return json.dumps(
                    {
                        "ok": True,
                        "evolved": entry is not None,
                        "recipe_name": rname,
                        "action": entry.action if entry else "skipped",
                        "reason": entry.reason if entry else "Already at latest version",
                        "details": entry.data if entry else {},
                        "stats": stats,
                    },
                    indent=2,
                )
            else:
                entries = improver.analyze_and_improve()
                stats = improver.get_evolution_stats()
                return json.dumps(
                    {
                        "ok": True,
                        "evolved": len(entries) > 0,
                        "total_actions": len(entries),
                        "actions": [e.to_dict() for e in entries],
                        "stats": stats,
                    },
                    indent=2,
                )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_mission_metrics(self, agent_id: str = "all", days: int = 7) -> str:
        """Retrieve aggregated telemetry metrics, credit usage, and failure breakdowns across agents."""
        from src.core.evals_bridge import query_evals

        try:
            aid = _clean_str(agent_id) or "all"
            d = int(days) if days is not None else 7
            res = query_evals(agent_id=aid, window_days=d, limit=10)
            summary = {
                "ok": True,
                "agent_id": aid,
                "window_days": d,
                "total_missions": res.get("total_missions", 0),
                "successful_missions": res.get("successful_missions", 0),
                "failed_missions": res.get("failed_missions", 0),
                "success_rate_pct": res.get("success_rate_pct", 0.0),
                "p95_duration_ms": res.get("p95_duration_ms", 0),
                "avg_duration_ms": res.get("avg_duration_ms", 0.0),
                "avg_credits": res.get("avg_credits", 0.0),
                "total_credits": res.get("total_credits", 0.0),
                "failure_clusters_count": len(res.get("failure_clusters", [])),
                "top_cluster": res["failure_clusters"][0]["category"] if res.get("failure_clusters") else "None",
                "recommendations": res.get("recommendations", []),
            }
            return json.dumps(summary, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    _handle_mekong_eval_query = _handle_eval_query
    _handle_mekong_recipe_evolve = _handle_recipe_evolve
    _handle_mekong_mission_metrics = _handle_mission_metrics

    def _handle_palette_search(self, query: str = "", category: str = "all", limit: int = 5) -> str:
        """Fuzzy search across Mekong CLI commands, Antigravity skills, and domain subagents."""
        from src.core.palette_bridge import PaletteBridge

        try:
            q = _clean_str(query)
            cat = _clean_str(category) or "all"
            lim = int(limit) if limit is not None else 5
            bridge = PaletteBridge()
            matches = bridge.search(query=q, category=cat, limit=lim)
            return json.dumps(
                {
                    "ok": True,
                    "query": q,
                    "category": cat,
                    "total_matches": len(matches),
                    "matches": [m.to_dict() for m in matches],
                },
                indent=2,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_tui_dashboard_status(self, detailed: bool = False) -> str:
        """Retrieve real-time telemetry, AGI subsystem health, checkpoints, and system performance summary."""
        from src.core.palette_bridge import PaletteBridge

        try:
            bridge = PaletteBridge()
            summary = bridge.get_tui_dashboard_summary(detailed=bool(detailed))
            return json.dumps(summary, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_benchmark_run(self, suite: str = "all", iterations: int = 1, chaos_level: str = "none") -> str:
        """Run autonomous benchmark suites across PEV, checkpoints, subagents, and chaos scenarios."""
        from src.core.benchmark_bridge import BenchmarkBridge

        try:
            bridge = BenchmarkBridge()
            report = bridge.run_benchmark(
                suite=_clean_str(suite) or "all",
                iterations=int(iterations) if iterations is not None else 1,
                chaos_level=_clean_str(chaos_level) or "none",
            )
            res = report.to_dict()
            res["ok"] = (report.total_failed == 0)
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_chaos_simulate(self, target: str = "checkpoint", error_type: str = "corrupt_file") -> str:
        """Simulate chaos fault injection against checkpoints, tools, or payloads to test self-healing resilience."""
        from src.core.benchmark_bridge import BenchmarkBridge

        try:
            bridge = BenchmarkBridge()
            result = bridge.simulate_chaos(
                target=_clean_str(target) or "checkpoint",
                error_type=_clean_str(error_type) or "corrupt_file",
            )
            res = result.to_dict()
            res["ok"] = result.self_healed
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    def _handle_gateway_status(self, args: Optional[dict[str, Any]] = None, **kwargs: Any) -> str:
        """Query Mekong Gateway server health, uptime, active SSE streams, and system metrics."""
        try:
            from src.core.gateway.streaming import get_mission_streaming_broker
            from src.core.gateway.rate_limiter import get_rate_limiter, get_telemetry_hub

            broker = get_mission_streaming_broker()
            limiter = get_rate_limiter()
            telemetry = get_telemetry_hub()

            broker_stats = broker.get_stats() if hasattr(broker, "get_stats") else {}
            metrics = telemetry.get_metrics() if hasattr(telemetry, "get_metrics") else {}
            health = telemetry.get_health() if hasattr(telemetry, "get_health") else {}

            active_streams = broker_stats.get(
                "active_subscribers",
                metrics.get("active_subscribers", metrics.get("active_streams", 0)),
            )
            active_ws = broker_stats.get("active_ws_connections", 0)
            uptime = broker_stats.get("uptime_seconds", health.get("uptime_seconds", 0.0))
            status_val = broker_stats.get("status", health.get("status", "healthy"))

            res = {
                "ok": True,
                "status": status_val,
                "uptime_seconds": uptime,
                "active_streams": active_streams,
                "active_ws_connections": active_ws,
                "system_metrics": {
                    "rate_limit_rejections": metrics.get("rate_limit_rejections", 0),
                    "total_requests": metrics.get("total_requests", 0),
                    "latency_percentiles": metrics.get(
                        "latency_percentiles",
                        {
                            "p50_ms": metrics.get("p50_ms", 0.0),
                            "p90_ms": metrics.get("p90_ms", 0.0),
                            "p99_ms": metrics.get("p99_ms", 0.0),
                        },
                    ),
                    "p50_latency_ms": metrics.get("p50_ms", 0.0),
                    "p90_latency_ms": metrics.get("p90_ms", 0.0),
                    "p99_latency_ms": metrics.get("p99_ms", 0.0),
                    "total_events_emitted": broker_stats.get("total_events_emitted", 0),
                    "active_missions": broker_stats.get("active_missions", 0),
                },
            }
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Gateway status error: {exc}"}, indent=2)

    def _handle_gateway_rate_limit(
        self,
        args: Optional[dict[str, Any] | str] = None,
        tenant_id: str = "default",
        **kwargs: Any,
    ) -> str:
        """Query tenant rate limit quota, tokens remaining, and reset timestamp."""
        import time

        if isinstance(args, dict):
            resolved_tenant = _clean_str(args.get("tenant_id")) or tenant_id
        elif isinstance(args, str) and args.strip():
            resolved_tenant = args.strip()
        else:
            resolved_tenant = tenant_id or "default"

        resolved_tenant = _clean_str(resolved_tenant) or "default"

        try:
            from src.core.gateway.rate_limiter import get_rate_limiter

            limiter = get_rate_limiter()
            quota = limiter.get_quota(resolved_tenant)

            limit_val = quota.get("limit", quota.get("capacity", 60))
            remaining_val = quota.get("remaining", limit_val)
            reset_ts = quota.get("reset_timestamp", int(time.time()))
            now_ts = int(time.time())
            reset_in = max(0, reset_ts - now_ts)
            retry_after = 0 if remaining_val > 0 else max(1, reset_in)

            res = {
                "ok": True,
                "tenant_id": quota.get("tenant_id", resolved_tenant),
                "tier": quota.get("tier", "free"),
                "limit": limit_val,
                "quota_limit": limit_val,
                "remaining": remaining_val,
                "tokens_remaining": remaining_val,
                "reset_timestamp": reset_ts,
                "reset_in_seconds": reset_in,
                "retry_after": retry_after,
            }
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Gateway rate limit error: {exc}"}, indent=2)

    def _handle_watch_status(self, args: Optional[dict[str, Any]] = None, **kwargs: Any) -> str:
        """Query active Mekong file watcher daemon state, monitored directories, recent change events, and repair metrics."""
        try:
            from src.core.watcher_bridge import get_watch_daemon

            daemon = get_watch_daemon()
            status_dict = daemon.get_status()
            res = {
                "ok": True,
                "status": "running" if daemon.is_running() else "idle",
                "data": status_dict,
            }
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Watch status error: {exc}"}, indent=2)

    def _handle_self_repair(
        self,
        args: Optional[dict[str, Any] | str] = None,
        file_path: str = "",
        error_detail: str = "",
        mode: str = "auto",
        **kwargs: Any,
    ) -> str:
        """Perform AST syntax diagnostics and automated self-healing repair (or checkpoint rollback) on a file."""
        if isinstance(args, dict):
            resolved_path = _clean_str(args.get("file_path")) or file_path
            resolved_error = _clean_str(args.get("error_detail")) or error_detail
            resolved_mode = _clean_str(args.get("mode")) or mode
        elif isinstance(args, str) and args.strip():
            resolved_path = args.strip()
            resolved_error = error_detail
            resolved_mode = mode
        else:
            resolved_path = file_path
            resolved_error = error_detail
            resolved_mode = mode

        resolved_path = _clean_str(resolved_path) or ""
        resolved_error = _clean_str(resolved_error) or ""
        resolved_mode = _clean_str(resolved_mode) or "auto"

        if not resolved_path:
            return json.dumps({"ok": False, "error": "Missing required argument: file_path"}, indent=2)

        try:
            from src.core.watcher_bridge import get_watch_daemon

            daemon = get_watch_daemon()
            res = daemon.trigger_self_repair(resolved_path, mode=resolved_mode)
            return json.dumps({"ok": True, "data": res}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Self repair error: {exc}"}, indent=2)

    def _handle_package_build(
        self,
        args: Optional[dict[str, Any]] = None,
        target: str = "all",
        output_dir: str = "dist",
        **kwargs: Any,
    ) -> str:
        """Build multi-platform distribution packages, Homebrew formulas, and Docker assets."""
        if isinstance(args, dict):
            resolved_target = _clean_str(args.get("target")) or target
            resolved_dir = _clean_str(args.get("output_dir")) or output_dir
        else:
            resolved_target = target
            resolved_dir = output_dir

        resolved_target = _clean_str(resolved_target) or "all"
        resolved_dir = _clean_str(resolved_dir) or "dist"

        try:
            from pathlib import Path
            from src.core.packaging_bridge import PackagingBridge

            bridge = PackagingBridge()
            report = bridge.build_distribution_package(target=resolved_target, output_dir=Path(resolved_dir))
            return json.dumps({"ok": True, "data": report.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Package build error: {exc}"}, indent=2)

    def _handle_sandbox_exec(
        self,
        args: Optional[dict[str, Any] | str] = None,
        command: str = "",
        timeout: int = 30,
        memory_limit_mb: int = 512,
        image: str = "python:3.11-slim",
        **kwargs: Any,
    ) -> str:
        """Execute a shell command inside an isolated container or secure subprocess sandbox."""
        if isinstance(args, dict):
            resolved_cmd = _clean_str(args.get("command")) or command
            resolved_timeout = int(args.get("timeout", timeout))
            resolved_mem = int(args.get("memory_limit_mb", memory_limit_mb))
            resolved_img = _clean_str(args.get("image")) or image
        elif isinstance(args, str) and args.strip():
            resolved_cmd = args.strip()
            resolved_timeout = timeout
            resolved_mem = memory_limit_mb
            resolved_img = image
        else:
            resolved_cmd = command
            resolved_timeout = timeout
            resolved_mem = memory_limit_mb
            resolved_img = image

        resolved_cmd = _clean_str(resolved_cmd) or ""
        if not resolved_cmd:
            return json.dumps({"ok": False, "error": "Missing required argument: command"}, indent=2)

        try:
            from src.core.sandbox_bridge import SandboxConfig, get_sandbox_harness

            harness = get_sandbox_harness()
            cfg = SandboxConfig(
                image=resolved_img or "python:3.11-slim",
                timeout_seconds=resolved_timeout,
                memory_limit_mb=resolved_mem,
            )
            res = harness.execute(resolved_cmd, config=cfg)
            return json.dumps({"ok": True, "data": res.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Sandbox execution error: {exc}"}, indent=2)

    def _handle_consensus_vote(
        self,
        args: Optional[dict[str, Any]] = None,
        proposal: str = "",
        quorum: str = "majority",
        agents: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Execute a multi-agent quorum vote on a proposal."""
        if isinstance(args, dict):
            resolved_proposal = _clean_str(args.get("proposal")) or proposal
            resolved_quorum = _clean_str(args.get("quorum")) or quorum
            resolved_agents = args.get("agents")
        else:
            resolved_proposal = proposal
            resolved_quorum = quorum
            resolved_agents = agents

        resolved_proposal = _clean_str(resolved_proposal) or ""
        if not resolved_proposal:
            return json.dumps({"ok": False, "error": "Missing required argument: proposal"}, indent=2)

        if isinstance(resolved_agents, str):
            resolved_agents = [a.strip() for a in resolved_agents.split(",") if a.strip()]

        try:
            from src.core.consensus_bridge import get_consensus_bridge

            bridge = get_consensus_bridge()
            ballot = bridge.create_vote(proposal=resolved_proposal, agents=resolved_agents, quorum=resolved_quorum)
            return json.dumps({"ok": True, "data": ballot.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Consensus vote error: {exc}"}, indent=2)

    def _handle_consensus_debate(
        self,
        args: Optional[dict[str, Any]] = None,
        topic: str = "",
        proponent: str = "cto",
        opponent: str = "sre",
        moderator: str = "ceo",
        rounds: int = 2,
        **kwargs: Any,
    ) -> str:
        """Conduct a structured multi-round debate between domain roles with synthetic consensus."""
        if isinstance(args, dict):
            resolved_topic = _clean_str(args.get("topic")) or topic
            resolved_proponent = _clean_str(args.get("proponent")) or proponent
            resolved_opponent = _clean_str(args.get("opponent")) or opponent
            resolved_moderator = _clean_str(args.get("moderator")) or moderator
            resolved_rounds = int(args.get("rounds", rounds))
        else:
            resolved_topic = topic
            resolved_proponent = proponent
            resolved_opponent = opponent
            resolved_moderator = moderator
            resolved_rounds = rounds

        resolved_topic = _clean_str(resolved_topic) or ""
        if not resolved_topic:
            return json.dumps({"ok": False, "error": "Missing required argument: topic"}, indent=2)

        try:
            from src.core.consensus_bridge import get_consensus_bridge

            bridge = get_consensus_bridge()
            session = bridge.conduct_debate(
                topic=resolved_topic,
                proponent=resolved_proponent or "cto",
                opponent=resolved_opponent or "sre",
                moderator=resolved_moderator or "ceo",
                rounds=resolved_rounds,
            )
            return json.dumps({"ok": True, "data": session.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Consensus debate error: {exc}"}, indent=2)

    def _handle_semantic_recall(
        self,
        args: Optional[dict[str, Any]] = None,
        query: str = "",
        domain: str = "all",
        limit: int = 5,
        **kwargs: Any,
    ) -> str:
        """Perform associative semantic and BM25 search across federated memory domains."""
        if isinstance(args, dict):
            resolved_query = _clean_str(args.get("query")) or query
            resolved_domain = _clean_str(args.get("domain")) or domain
            resolved_limit = int(args.get("limit", limit))
        else:
            resolved_query = query
            resolved_domain = domain
            resolved_limit = limit

        resolved_query = _clean_str(resolved_query) or ""
        if not resolved_query:
            return json.dumps({"ok": False, "error": "Missing required argument: query"}, indent=2)

        try:
            from src.core.memory_federation import get_memory_federation_engine

            engine = get_memory_federation_engine()
            items = engine.query(query_text=resolved_query, domain=resolved_domain, limit=resolved_limit)
            return json.dumps(
                {
                    "ok": True,
                    "data": {
                        "query": resolved_query,
                        "domain": resolved_domain,
                        "total_results": len(items),
                        "items": [item.to_dict() for item in items],
                    },
                },
                indent=2,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Semantic recall error: {exc}"}, indent=2)

    def _handle_knowledge_graph_query(
        self,
        args: Optional[dict[str, Any]] = None,
        entity: str = "",
        depth: int = 2,
        **kwargs: Any,
    ) -> str:
        """Traverse relational codebase and architectural knowledge graph around an entity."""
        if isinstance(args, dict):
            resolved_entity = _clean_str(args.get("entity")) or entity
            resolved_depth = int(args.get("depth", depth))
        else:
            resolved_entity = entity
            resolved_depth = depth

        resolved_entity = _clean_str(resolved_entity) or ""
        if not resolved_entity:
            return json.dumps({"ok": False, "error": "Missing required argument: entity"}, indent=2)

        try:
            from src.core.memory_federation import get_memory_federation_engine

            engine = get_memory_federation_engine()
            graph = engine.query_knowledge_graph(entity=resolved_entity, depth=resolved_depth)
            return json.dumps({"ok": True, "data": graph}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Knowledge graph query error: {exc}"}, indent=2)

    _handle_mekong_palette_search = _handle_palette_search
    _handle_mekong_tui_dashboard_status = _handle_tui_dashboard_status
    _handle_mekong_benchmark_run = _handle_benchmark_run
    _handle_mekong_chaos_simulate = _handle_chaos_simulate
    _handle_mekong_gateway_status = _handle_gateway_status
    _handle_mekong_gateway_rate_limit = _handle_gateway_rate_limit
    _handle_mekong_watch_status = _handle_watch_status
    _handle_mekong_self_repair = _handle_self_repair
    _handle_watch_status = _handle_watch_status
    _handle_self_repair = _handle_self_repair
    _handle_mekong_package_build = _handle_package_build
    _handle_mekong_sandbox_exec = _handle_sandbox_exec
    _handle_package_build = _handle_package_build
    _handle_sandbox_exec = _handle_sandbox_exec
    _handle_mekong_consensus_vote = _handle_consensus_vote
    _handle_mekong_consensus_debate = _handle_consensus_debate
    _handle_consensus_vote = _handle_consensus_vote
    _handle_consensus_debate = _handle_consensus_debate
    _handle_mekong_semantic_recall = _handle_semantic_recall
    _handle_mekong_knowledge_graph_query = _handle_knowledge_graph_query
    _handle_semantic_recall = _handle_semantic_recall
    _handle_knowledge_graph_query = _handle_knowledge_graph_query

    def _handle_telemetry_metrics(
        self,
        args: Optional[dict[str, Any]] = None,
        format_type: str = "prometheus",
        **kwargs: Any,
    ) -> str:
        """Export or inspect standard Prometheus exposition metrics or structured JSON."""
        if isinstance(args, dict):
            fmt = _clean_str(args.get("format_type")) or _clean_str(args.get("format")) or format_type
        else:
            fmt = format_type

        fmt = _clean_str(fmt) or "prometheus"
        try:
            from src.core.telemetry_bridge import get_telemetry_bridge

            bridge = get_telemetry_bridge()
            if fmt.lower() == "json":
                return json.dumps({"ok": True, "data": bridge.metrics.to_dict()}, indent=2)
            return bridge.metrics.to_prometheus_text()
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telemetry metrics error: {exc}"}, indent=2)

    def _handle_trace_query(
        self,
        args: Optional[dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        limit: int = 20,
        **kwargs: Any,
    ) -> str:
        """Query distributed tracing spans, latency timings, and W3C traceparent headers."""
        if isinstance(args, dict):
            resolved_trace_id = _clean_str(args.get("trace_id")) or trace_id
            resolved_limit = int(args.get("limit", limit))
        else:
            resolved_trace_id = trace_id
            resolved_limit = limit

        resolved_trace_id = _clean_str(resolved_trace_id)
        try:
            from src.core.telemetry_bridge import get_telemetry_bridge

            bridge = get_telemetry_bridge()
            spans = bridge.query_spans(trace_id=resolved_trace_id, limit=resolved_limit)
            return json.dumps(
                {
                    "ok": True,
                    "data": {
                        "trace_id": resolved_trace_id,
                        "limit": resolved_limit,
                        "total_spans": len(spans),
                        "spans": [s.to_dict() for s in spans],
                    },
                },
                indent=2,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Trace query error: {exc}"}, indent=2)

    _handle_mekong_telemetry_metrics = _handle_telemetry_metrics
    _handle_mekong_trace_query = _handle_trace_query
    _handle_telemetry_metrics = _handle_telemetry_metrics
    _handle_trace_query = _handle_trace_query

    def _handle_queue_enqueue(
        self,
        args: Optional[dict[str, Any]] = None,
        name: str = "",
        priority: str = "normal",
        payload: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
        delay_sec: float = 0.0,
        **kwargs: Any,
    ) -> str:
        """Schedule a new task for prioritized execution in the distributed task queue."""
        if isinstance(args, dict):
            resolved_name = _clean_str(args.get("name")) or _clean_str(args.get("task_name")) or name
            resolved_priority = _clean_str(args.get("priority")) or priority
            raw_payload = args.get("payload", payload)
            if isinstance(raw_payload, str):
                try:
                    resolved_payload = json.loads(raw_payload)
                except Exception:
                    resolved_payload = {"raw": raw_payload}
            elif isinstance(raw_payload, dict):
                resolved_payload = raw_payload
            else:
                resolved_payload = {}
            resolved_max_retries = int(args.get("max_retries", max_retries))
            resolved_delay = float(args.get("delay_sec", delay_sec))
        else:
            resolved_name = name
            resolved_priority = priority
            resolved_payload = payload or {}
            resolved_max_retries = max_retries
            resolved_delay = delay_sec

        resolved_name = _clean_str(resolved_name)
        if not resolved_name:
            return json.dumps({"ok": False, "error": "Missing required argument: name"}, indent=2)

        try:
            from src.core.task_queue import get_task_queue

            tq = get_task_queue()
            task = tq.enqueue(
                name=resolved_name,
                payload=resolved_payload,
                priority=resolved_priority,
                max_retries=resolved_max_retries,
                delay_sec=resolved_delay,
            )
            return json.dumps({"ok": True, "data": task.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Queue enqueue error: {exc}"}, indent=2)

    def _handle_queue_status(
        self,
        args: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Inspect queue depth, active worker leases, and dead-letter counts."""
        try:
            from src.core.task_queue import get_task_queue

            tq = get_task_queue()
            status = tq.get_status()
            return json.dumps({"ok": True, "data": status}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Queue status error: {exc}"}, indent=2)

    def _handle_queue_dlq_action(
        self,
        args: Optional[dict[str, Any]] = None,
        action: str = "list",
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Inspect, retry, or clear tasks residing in the dead-letter queue."""
        if isinstance(args, dict):
            resolved_action = (_clean_str(args.get("action")) or action).lower()
            resolved_task_id = _clean_str(args.get("task_id")) or task_id
            limit = int(args.get("limit", 50))
        else:
            resolved_action = action.lower()
            resolved_task_id = task_id
            limit = 50

        try:
            from src.core.task_queue import get_task_queue

            tq = get_task_queue()
            if resolved_action == "clear":
                cleared = tq.clear_dlq()
                return json.dumps({"ok": True, "data": {"action": "clear", "cleared_tasks": cleared}}, indent=2)
            elif resolved_action in ("retry_all", "retry-all"):
                retried = tq.retry_all_dlq()
                return json.dumps({"ok": True, "data": {"action": "retry_all", "retried_tasks": retried}}, indent=2)
            elif resolved_action == "retry":
                if not resolved_task_id:
                    return json.dumps({"ok": False, "error": "Missing required argument: task_id"}, indent=2)
                ok = tq.retry_dlq_task(resolved_task_id)
                return json.dumps({"ok": ok, "data": {"action": "retry", "task_id": resolved_task_id}}, indent=2)
            else:
                tasks = tq.get_dlq_tasks(limit=limit)
                return json.dumps(
                    {
                        "ok": True,
                        "data": {
                            "action": "list",
                            "total_dlq": len(tasks),
                            "tasks": [t.to_dict() for t in tasks],
                        },
                    },
                    indent=2,
                )
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Queue DLQ action error: {exc}"}, indent=2)

    _handle_mekong_queue_enqueue = _handle_queue_enqueue
    _handle_mekong_queue_status = _handle_queue_status
    _handle_mekong_queue_dlq_action = _handle_queue_dlq_action
    _handle_queue_enqueue = _handle_queue_enqueue
    _handle_queue_status = _handle_queue_status
    _handle_queue_dlq_action = _handle_queue_dlq_action

    def _handle_pipeline_run(
        self,
        goal: str,
        stages: list[str] | str | None = None,
        **kwargs: Any,
    ) -> str:
        """Run multi-agent sequential pipeline (FilePicker -> Editor -> Reviewer)."""
        goal_str = str(goal).strip() if goal else ""
        if not goal_str:
            return json.dumps({"ok": False, "error": "Missing required argument: goal"}, indent=2)

        resolved_stages = None
        if isinstance(stages, str):
            resolved_stages = [s.strip() for s in stages.split(",") if s.strip()]
        elif isinstance(stages, list):
            resolved_stages = [str(s).strip() for s in stages if str(s).strip()]

        try:
            from src.core.pipeline_manager import get_pipeline_manager

            pm = get_pipeline_manager()
            res = pm.run_multi_agent_pipeline(goal=goal_str, stages=resolved_stages)
            aggregated = pm.aggregate_results(res.pipeline_id)
            aggregated["goal"] = goal_str
            return json.dumps({"ok": res.status.value == "completed", "data": aggregated}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Pipeline run error: {exc}"}, indent=2)

    def _handle_pipeline_status(
        self,
        pipeline_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Inspect status, stage outcomes, and timings for a pipeline execution."""
        resolved_id = str(pipeline_id).strip() if pipeline_id else ""
        try:
            from src.core.pipeline_manager import get_pipeline_manager

            pm = get_pipeline_manager()
            if resolved_id:
                res = pm.get_pipeline(resolved_id)
                if res is None:
                    return json.dumps({"ok": False, "error": f"Pipeline not found: {resolved_id}"}, indent=2)
                aggregated = pm.aggregate_results(resolved_id)
                return json.dumps({"ok": True, "data": aggregated}, indent=2)
            else:
                all_pipelines = pm.list_pipelines()
                return json.dumps(
                    {
                        "ok": True,
                        "data": {
                            "total_pipelines": len(all_pipelines),
                            "pipelines": [pm.aggregate_results(p.pipeline_id) for p in all_pipelines],
                        },
                    },
                    indent=2,
                )
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Pipeline status error: {exc}"}, indent=2)

    _handle_mekong_pipeline_run = _handle_pipeline_run
    _handle_mekong_pipeline_status = _handle_pipeline_status

    def _handle_worktree_create(
        self,
        feature: str,
        prefix: str | None = None,
        base_branch: str | None = None,
        no_prefix: bool = False,
        root: str | None = None,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> str:
        """Create a new isolated git worktree branching from the base branch."""
        feature_str = str(feature).strip() if feature else ""
        if not feature_str:
            return json.dumps({"ok": False, "error": "Missing required argument: feature"}, indent=2)

        try:
            from src.core.worktree_manager import get_worktree_manager

            wm = get_worktree_manager()
            rec = wm.create_worktree(
                feature=feature_str,
                prefix=prefix,
                base_branch=base_branch,
                no_prefix=no_prefix,
                worktree_root=root,
                dry_run=dry_run,
            )
            return json.dumps({"ok": True, "dry_run": dry_run, "worktree": rec.to_dict()}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Worktree create error: {exc}"}, indent=2)

    def _handle_worktree_list(self, **kwargs: Any) -> str:
        """List all registered git worktrees in the repository."""
        try:
            from src.core.worktree_manager import get_worktree_manager

            wm = get_worktree_manager()
            recs = wm.list_worktrees()
            return json.dumps({"ok": True, "worktrees": [r.to_dict() for r in recs], "count": len(recs)}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Worktree list error: {exc}"}, indent=2)

    def _handle_worktree_status(
        self,
        path_or_branch: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Inspect status, uncommitted changes, and divergence against base branch."""
        target = str(path_or_branch).strip() if path_or_branch else None
        try:
            from src.core.worktree_manager import get_worktree_manager

            wm = get_worktree_manager()
            stat = wm.status(path_or_branch=target)
            return json.dumps(stat, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Worktree status error: {exc}"}, indent=2)

    def _handle_worktree_remove(
        self,
        path_or_name: str,
        force: bool = False,
        **kwargs: Any,
    ) -> str:
        """Remove an isolated git worktree workspace."""
        target = str(path_or_name).strip() if path_or_name else ""
        if not target:
            return json.dumps({"ok": False, "error": "Missing required argument: path_or_name"}, indent=2)

        try:
            from src.core.worktree_manager import get_worktree_manager

            wm = get_worktree_manager()
            success = wm.remove_worktree(path_or_name=target, force=force)
            return json.dumps({"ok": success, "target": target, "removed": True}, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Worktree remove error: {exc}"}, indent=2)

    _handle_mekong_worktree_create = _handle_worktree_create
    _handle_mekong_worktree_list = _handle_worktree_list
    _handle_mekong_worktree_status = _handle_worktree_status
    _handle_mekong_worktree_remove = _handle_worktree_remove

    def _handle_ship_preflight(self, **kwargs: Any) -> str:
        """Inspect repository topology, branch, remote, and dirty files before shipping."""
        try:
            from src.core.shipping_engine import get_shipping_engine

            engine = get_shipping_engine()
            res = engine.preflight_check()
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Ship preflight error: {exc}"}, indent=2)

    def _handle_ship_run(
        self,
        message: str = "",
        run_lint: bool = True,
        run_tests: bool = True,
        push: bool = True,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> str:
        """Run the production shipping pipeline: lint, test, stage, commit, and push."""
        msg = str(message).strip() if message else None
        try:
            from src.core.shipping_engine import get_shipping_engine

            engine = get_shipping_engine()
            report = engine.ship(
                message=msg,
                run_lint=run_lint,
                run_tests=run_tests,
                push=push,
                dry_run=dry_run,
            )
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Ship run error: {exc}"}, indent=2)

    _handle_mekong_ship_preflight = _handle_ship_preflight
    _handle_mekong_ship_run = _handle_ship_run

    def _handle_daily_report(self, since: str = "24 hours ago", include_todos: bool = True, **kwargs: Any) -> str:
        """Produce an executive daily standup report."""
        try:
            from src.core.daily_briefing import get_daily_briefing_engine

            engine = get_daily_briefing_engine()
            report = engine.generate_report(since=since, include_debt=include_todos)
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Daily report error: {exc}"}, indent=2)

    def _handle_daily_focus(self, **kwargs: Any) -> str:
        """Retrieve prioritized strategic daily focus recommendations."""
        try:
            from src.core.daily_briefing import get_daily_briefing_engine

            engine = get_daily_briefing_engine()
            report = engine.generate_report(since="24 hours ago", include_debt=True)
            return json.dumps({
                "ok": True,
                "date": report.date,
                "focus_priorities": report.focus_priorities,
            }, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Daily focus error: {exc}"}, indent=2)

    _handle_mekong_daily_report = _handle_daily_report
    _handle_mekong_daily_focus = _handle_daily_focus

    def _handle_quick_start_plan(self, project_name: str = "mekong-app", project_type: str = "agent", **kwargs: Any) -> str:
        """Simulate and retrieve the 5-step project kickoff blueprint without writing files."""
        try:
            from src.core.quick_start_engine import get_quick_start_engine

            engine = get_quick_start_engine()
            report = engine.kickoff(
                project_name=project_name,
                project_type=project_type,
                dry_run=True,
                init_git=False,
            )
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Quick start plan error: {exc}"}, indent=2)

    def _handle_quick_start_create(
        self,
        project_name: str = "mekong-app",
        project_type: str = "agent",
        target_dir: str = "",
        dry_run: bool = False,
        init_git: bool = True,
        **kwargs: Any,
    ) -> str:
        """Execute the end-to-end 5-step project kickoff."""
        try:
            from src.core.quick_start_engine import get_quick_start_engine

            engine = get_quick_start_engine()
            report = engine.kickoff(
                project_name=project_name,
                project_type=project_type,
                target_dir=target_dir if target_dir else None,
                dry_run=dry_run,
                init_git=init_git,
            )
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Quick start create error: {exc}"}, indent=2)

    _handle_mekong_quick_start_plan = _handle_quick_start_plan
    _handle_mekong_quick_start_create = _handle_quick_start_create

    def _handle_cto_scorecard(self, **kwargs: Any) -> str:
        """Calculate composite engineering health score, grade, test coverage, and security posture."""
        try:
            from src.core.cto_engine import get_cto_engine

            engine = get_cto_engine()
            sc = engine.compute_scorecard()
            return json.dumps(sc.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"CTO scorecard error: {exc}"}, indent=2)

    def _handle_cto_review(self, target_path: str = "", **kwargs: Any) -> str:
        """Conduct automated code quality, anti-pattern, dynamic execution, and security review."""
        try:
            from src.core.cto_engine import get_cto_engine

            engine = get_cto_engine()
            report = engine.run_code_review(target_path=target_path if target_path else None)
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"CTO review error: {exc}"}, indent=2)

    def _handle_cto_architect(self, title: str = "Architecture Decision", context: str = "", decision: str = "", **kwargs: Any) -> str:
        """Generate an Architecture Decision Record (ADR) with context, decision, consequences, and alternatives."""
        try:
            from src.core.cto_engine import get_cto_engine

            engine = get_cto_engine()
            adr = engine.generate_adr(title=title, context=context, decision=decision, export=False)
            return json.dumps(adr.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"CTO architect error: {exc}"}, indent=2)

    _handle_mekong_cto_scorecard = _handle_cto_scorecard
    _handle_mekong_cto_review = _handle_cto_review
    _handle_mekong_cto_architect = _handle_cto_architect

    def _handle_sales_pipeline(self, stage: str = "", **kwargs: Any) -> str:
        """Query sales pipeline metrics, weighted revenue forecasts, and opportunities by stage."""
        try:
            from src.core.sales_engine import get_sales_engine

            engine = get_sales_engine()
            metrics = engine.get_pipeline_metrics()
            return json.dumps(metrics.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Sales pipeline error: {exc}"}, indent=2)

    def _handle_sales_deal_add(self, name: str = "New Opportunity", company: str = "Prospective Account", value: float = 10000.0, stage: str = "lead", email: str = "", **kwargs: Any) -> str:
        """Add a new deal opportunity to the sales pipeline ledger."""
        try:
            from src.core.sales_engine import get_sales_engine

            engine = get_sales_engine()
            deal = engine.add_deal(name=name, company=company, value=float(value), stage=stage, contact_email=email)
            return json.dumps(deal.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Sales deal add error: {exc}"}, indent=2)

    def _handle_sales_outreach(self, company: str = "Acme Corp", persona: str = "CTO", channel: str = "email", **kwargs: Any) -> str:
        """Generate tailored multi-channel outreach copy and cadence."""
        try:
            from src.core.sales_engine import get_sales_engine

            engine = get_sales_engine()
            template = engine.generate_outreach(company=company, persona=persona, channel=channel)
            return json.dumps(template.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Sales outreach error: {exc}"}, indent=2)

    _handle_mekong_sales_pipeline = _handle_sales_pipeline
    _handle_mekong_sales_deal_add = _handle_sales_deal_add
    _handle_mekong_sales_outreach = _handle_sales_outreach

    def _handle_marketing_metrics(self, **kwargs: Any) -> str:
        """Query aggregated marketing metrics, active campaigns, total spend, and conversions."""
        try:
            from src.core.marketing_engine import get_marketing_engine

            engine = get_marketing_engine()
            metrics = engine.get_marketing_metrics()
            return json.dumps(metrics.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Marketing metrics error: {exc}"}, indent=2)

    def _handle_marketing_campaign_create(self, name: str = "New Campaign", channel: str = "social", budget: float = 1000.0, target_audience: str = "", **kwargs: Any) -> str:
        """Create and register a promotional or growth marketing campaign."""
        try:
            from src.core.marketing_engine import get_marketing_engine

            engine = get_marketing_engine()
            camp = engine.create_campaign(name=name, channel=channel, budget=float(budget), target_audience=target_audience)
            return json.dumps(camp.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Marketing campaign create error: {exc}"}, indent=2)

    def _handle_marketing_content_generate(self, topic: str = "Autonomous Agent Harnesses", channel: str = "social", content_type: str = "post", **kwargs: Any) -> str:
        """Synthesize ready-to-use marketing copy and creative with hashtags and call-to-action."""
        try:
            from src.core.marketing_engine import get_marketing_engine

            engine = get_marketing_engine()
            item = engine.generate_content(topic=topic, channel=channel, content_type=content_type)
            return json.dumps(item.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Marketing content generate error: {exc}"}, indent=2)

    _handle_mekong_marketing_metrics = _handle_marketing_metrics
    _handle_mekong_marketing_campaign_create = _handle_marketing_campaign_create
    _handle_mekong_marketing_content_generate = _handle_marketing_content_generate

    def _handle_dev_audit(self, path: str = "", **kwargs: Any) -> str:
        """Perform static AST and security audit across the codebase or specific module."""
        try:
            from src.core.dev_engine import get_dev_engine

            engine = get_dev_engine()
            report = engine.audit_codebase(target_path=path if path else None)
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Dev audit error: {exc}"}, indent=2)

    def _handle_dev_scaffold(self, name: str = "sample_service", module_type: str = "service", dry_run: bool = True, **kwargs: Any) -> str:
        """Scaffold a new structured Python module, service, API, or agent with unit tests."""
        try:
            from src.core.dev_engine import get_dev_engine

            engine = get_dev_engine()
            res = engine.scaffold_module(name=name, module_type=module_type, dry_run=dry_run)
            return json.dumps(res.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Dev scaffold error: {exc}"}, indent=2)

    def _handle_dev_review(self, **kwargs: Any) -> str:
        """Review working tree git diff for safety, technical debt, and quality hazards."""
        try:
            from src.core.dev_engine import get_dev_engine

            engine = get_dev_engine()
            report = engine.review_diff()
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Dev review error: {exc}"}, indent=2)

    _handle_mekong_dev_audit = _handle_dev_audit
    _handle_mekong_dev_scaffold = _handle_dev_scaffold
    _handle_mekong_dev_review = _handle_dev_review

    def _handle_ops_health_sweep(self, save_report: bool = False, **kwargs: Any) -> str:
        """Run comprehensive system health audit across runtime, storage, databases, git & configs."""
        try:
            from src.core.ops_engine import get_ops_engine

            engine = get_ops_engine()
            report = engine.health_sweep(save_report=save_report)
            return json.dumps(report.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Ops health sweep error: {exc}"}, indent=2)

    def _handle_ops_incident_create(self, title: str = "System degradation", severity: str = "SEV3", service: str = "core", summary: str = "", **kwargs: Any) -> str:
        """Create and track a new SRE incident in the operations ledger."""
        try:
            from src.core.ops_engine import get_ops_engine

            engine = get_ops_engine()
            rec = engine.create_incident(title=title, severity=severity, service=service, summary=summary)
            return json.dumps(rec.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Ops incident create error: {exc}"}, indent=2)

    def _handle_ops_incident_list(self, status: str = "ALL", **kwargs: Any) -> str:
        """List tracked SRE incidents filtered by status."""
        try:
            from src.core.ops_engine import get_ops_engine

            engine = get_ops_engine()
            incidents = engine.list_incidents(status=status)
            return json.dumps([i.to_dict() for i in incidents], indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Ops incident list error: {exc}"}, indent=2)

    _handle_mekong_ops_health_sweep = _handle_ops_health_sweep
    _handle_mekong_ops_incident_create = _handle_ops_incident_create
    _handle_mekong_ops_incident_list = _handle_ops_incident_list

    def _handle_support_onboard_status(self, **kwargs: Any) -> str:
        """Query current project onboarding milestones, completed steps, and progress percentage."""
        try:
            from src.core.support_engine import get_support_engine

            engine = get_support_engine()
            status = engine.get_onboarding_status()
            return json.dumps(status.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Support onboard status error: {exc}"}, indent=2)

    def _handle_support_feedback_submit(self, nps_score: Optional[int] = None, feedback_text: str = "", category: str = "general", **kwargs: Any) -> str:
        """Record customer satisfaction, feedback comments, or Net Promoter Score (NPS)."""
        try:
            from src.core.support_engine import get_support_engine

            engine = get_support_engine()
            rec = engine.submit_feedback(nps_score=nps_score, feedback_text=feedback_text, category=category)
            return json.dumps(rec.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Support feedback error: {exc}"}, indent=2)

    def _handle_support_triage(self, issue_text: str = "", **kwargs: Any) -> str:
        """Perform smart AI/heuristic triage for user issues, error traces, and operational bugs."""
        try:
            from src.core.support_engine import get_support_engine

            engine = get_support_engine()
            triage = engine.triage_issue(issue_description=issue_text)
            return json.dumps(triage.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Support triage error: {exc}"}, indent=2)

    _handle_mekong_support_onboard_status = _handle_support_onboard_status
    _handle_mekong_support_feedback_submit = _handle_support_feedback_submit
    _handle_mekong_support_triage = _handle_support_triage

    def _handle_consulting_pricing(self, currency: str = "USD", **kwargs: Any) -> str:
        """Show standardized AI agent consulting packages, pricing, and deliverables."""
        try:
            from src.core.consulting_engine import get_consulting_engine

            engine = get_consulting_engine()
            packages = engine.get_service_catalog(currency=currency)
            return json.dumps([p.to_dict() for p in packages], indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Consulting pricing error: {exc}"}, indent=2)

    def _handle_consulting_proposal(self, prospect_name: str = "Prospective Client", service_tier: str = "custom_agent", requirements: str = "", **kwargs: Any) -> str:
        """Synthesize a customized commercial consulting proposal for a prospect."""
        try:
            from src.core.consulting_engine import get_consulting_engine

            engine = get_consulting_engine()
            prop = engine.generate_proposal(prospect_name=prospect_name, service_tier=service_tier, requirements=requirements)
            return json.dumps(prop.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Consulting proposal error: {exc}"}, indent=2)

    def _handle_consulting_outreach(self, prospect_name: str = "Acme Corp", service_tier: str = "custom_agent", role: str = "CTO", **kwargs: Any) -> str:
        """Generate multi-channel B2B cold/warm outreach templates (Email, LinkedIn, Zalo)."""
        try:
            from src.core.consulting_engine import get_consulting_engine

            engine = get_consulting_engine()
            out = engine.generate_outreach(prospect_name=prospect_name, service_tier=service_tier, role=role)
            return json.dumps(out.to_dict(), indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Consulting outreach error: {exc}"}, indent=2)

    _handle_mekong_consulting_pricing = _handle_consulting_pricing
    _handle_mekong_consulting_proposal = _handle_consulting_proposal
    _handle_mekong_consulting_outreach = _handle_consulting_outreach

    def _handle_revenue_metrics(self, period: str = "month", **kwargs: Any) -> str:
        """Calculate current MRR, ARR, ARPU, LTV, churn rate, and MRR waterfall economics."""
        try:
            from src.core.revenue_engine import get_revenue_engine

            engine = get_revenue_engine()
            metrics = engine.get_metrics(period=period)
            return json.dumps(metrics, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Revenue metrics error: {exc}"}, indent=2)

    def _handle_revenue_record(
        self,
        customer_id: str = "cust_default",
        amount: float = 0.0,
        customer_name: str = "",
        currency: str = "USD",
        tier: str = "starter",
        txn_type: str = "subscription",
        gateway: str = "stripe",
        **kwargs: Any,
    ) -> str:
        """Record a payment transaction into the revenue ledger and update active subscriptions."""
        try:
            from src.core.revenue_engine import get_revenue_engine

            engine = get_revenue_engine()
            res = engine.record_transaction(
                customer_id=customer_id,
                amount=float(amount),
                customer_name=customer_name,
                currency=currency,
                tier=tier,
                type=txn_type,
                gateway=gateway,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Revenue record error: {exc}"}, indent=2)

    def _handle_revenue_forecast(self, months: int = 6, scenario: str = "base", **kwargs: Any) -> str:
        """Project future MRR, ARR, and cumulative cash flows across growth scenarios."""
        try:
            from src.core.revenue_engine import get_revenue_engine

            engine = get_revenue_engine()
            fc = engine.forecast_revenue(months=int(months), scenario=scenario)
            return json.dumps(fc, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Revenue forecast error: {exc}"}, indent=2)

    _handle_mekong_revenue_metrics = _handle_revenue_metrics
    _handle_mekong_revenue_record = _handle_revenue_record
    _handle_mekong_revenue_forecast = _handle_revenue_forecast

    def _handle_content_generate(
        self,
        pillar: str = "ai-agents",
        format_type: str = "blog",
        topic: str = "",
        channel: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate structured, ready-to-publish content for any pillar and format."""
        try:
            from src.core.content_engine import get_content_engine

            engine = get_content_engine()
            item = engine.generate_content(
                pillar=pillar,
                format_type=format_type,
                topic=topic,
                channel=channel,
            )
            return json.dumps(item, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Content generate error: {exc}"}, indent=2)

    def _handle_content_calendar(self, **kwargs: Any) -> str:
        """Query editorial publication calendar, frequencies, and upcoming deadlines."""
        try:
            from src.core.content_engine import get_content_engine

            engine = get_content_engine()
            cal = engine.get_calendar()
            return json.dumps(cal, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Content calendar error: {exc}"}, indent=2)

    def _handle_content_channels(self, **kwargs: Any) -> str:
        """Query distribution channels, audience reach, and publication metrics."""
        try:
            from src.core.content_engine import get_content_engine

            engine = get_content_engine()
            channels = engine.get_channel_stats()
            return json.dumps(channels, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Content channels error: {exc}"}, indent=2)

    _handle_mekong_content_generate = _handle_content_generate
    _handle_mekong_content_calendar = _handle_content_calendar
    _handle_mekong_content_channels = _handle_content_channels

    def _handle_copywriting_generate(
        self,
        product_name: str = "Mekong CLI",
        target_audience: str = "Founders & Engineers",
        formula: str = "pas",
        copy_type: str = "landing_page",
        key_benefit: str = "",
        style: str = "direct_response",
        **kwargs: Any,
    ) -> str:
        """Generate high-converting marketing and product copy using proven psychological frameworks."""
        try:
            from src.core.copywriting_engine import get_copywriting_engine

            engine = get_copywriting_engine()
            res = engine.generate_copy(
                product_name=_clean_str(product_name) or "Mekong CLI",
                target_audience=_clean_str(target_audience) or "Founders & Engineers",
                formula=_clean_str(formula) or "pas",
                copy_type=_clean_str(copy_type) or "landing_page",
                key_benefit=_clean_str(key_benefit) or "",
                style=_clean_str(style) or "direct_response",
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Copywriting generate error: {exc}"}, indent=2)

    def _handle_copywriting_headline(
        self,
        product_name: str = "Mekong CLI",
        value_prop: str = "automate engineering workflows",
        count: int = 5,
        **kwargs: Any,
    ) -> str:
        """Generate high-conversion headline variations across psychological angles."""
        try:
            from src.core.copywriting_engine import get_copywriting_engine

            engine = get_copywriting_engine()
            headlines = engine.generate_headlines(
                product_name=_clean_str(product_name) or "Mekong CLI",
                value_prop=_clean_str(value_prop) or "automate engineering workflows",
                count=int(count) if count else 5,
            )
            return json.dumps(headlines, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Copywriting headline error: {exc}"}, indent=2)

    def _handle_copywriting_cta(
        self,
        action_goal: str = "start free trial",
        risk_reversal: str = "",
        **kwargs: Any,
    ) -> str:
        """Generate conversion call-to-action button variations with risk reversals."""
        try:
            from src.core.copywriting_engine import get_copywriting_engine

            engine = get_copywriting_engine()
            ctas = engine.generate_cta(
                action_goal=_clean_str(action_goal) or "start free trial",
                risk_reversal=_clean_str(risk_reversal) or "",
            )
            return json.dumps(ctas, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Copywriting CTA error: {exc}"}, indent=2)

    _handle_mekong_copywriting_generate = _handle_copywriting_generate
    _handle_mekong_copywriting_headline = _handle_copywriting_headline
    _handle_mekong_copywriting_cta = _handle_copywriting_cta

    def _handle_billing_simulate(
        self,
        license_key: str = "mekong_lic_default",
        tier: str = "pro",
        period_days: int = 30,
        **kwargs: Any,
    ) -> str:
        """Simulate an itemized billing invoice based on accrued usage events and pricing tiers."""
        try:
            from src.core.billing_engine import get_billing_engine

            engine = get_billing_engine()
            invoice = engine.simulate_billing(
                license_key=_clean_str(license_key) or "mekong_lic_default",
                tier=_clean_str(tier) or "pro",
                period_days=int(period_days) if period_days else 30,
            )
            return json.dumps(invoice, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Billing simulate error: {exc}"}, indent=2)

    def _handle_billing_record_usage(
        self,
        license_key: str = "mekong_lic_default",
        event_type: str = "llm_tokens",
        quantity: float = 1.0,
        idempotency_key: str = "",
        tier: str = "pro",
        **kwargs: Any,
    ) -> str:
        """Ingest and meter a billable usage event with idempotent deduplication and pricing."""
        try:
            from src.core.billing_engine import get_billing_engine

            engine = get_billing_engine()
            res = engine.record_usage(
                license_key=_clean_str(license_key) or "mekong_lic_default",
                event_type=_clean_str(event_type) or "llm_tokens",
                quantity=float(quantity) if quantity is not None else 1.0,
                idempotency_key=_clean_str(idempotency_key) or "",
                tier=_clean_str(tier) or "pro",
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Billing record usage error: {exc}"}, indent=2)

    def _handle_billing_status(
        self,
        license_key: str = "mekong_lic_default",
        **kwargs: Any,
    ) -> str:
        """Retrieve real-time billing quotas, consumption, unbilled charges, and health status for a license."""
        try:
            from src.core.billing_engine import get_billing_engine

            engine = get_billing_engine()
            st = engine.get_billing_status(license_key=_clean_str(license_key) or "mekong_lic_default")
            return json.dumps(st, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Billing status error: {exc}"}, indent=2)

    _handle_mekong_billing_simulate = _handle_billing_simulate
    _handle_mekong_billing_record_usage = _handle_billing_record_usage
    _handle_mekong_billing_status = _handle_billing_status

    def _handle_vendor_onboard(
        self,
        name: str,
        vendor_type: str = "agent",
        version: str = "1.0.0",
        description: str = "",
        author: str = "Community Builder",
        trust_score: float = 85.0,
        **kwargs: Any,
    ) -> str:
        """Register and onboard a third-party vendor, plugin, model, or tool provider."""
        try:
            from src.core.vendor_engine import get_vendor_engine

            engine = get_vendor_engine()
            res = engine.onboard_vendor(
                name=_clean_str(name) or "",
                vendor_type=_clean_str(vendor_type) or "agent",
                version=_clean_str(version) or "1.0.0",
                description=_clean_str(description) or "",
                author=_clean_str(author) or "Community Builder",
                trust_score=float(trust_score) if trust_score is not None else 85.0,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Vendor onboard error: {exc}"}, indent=2)

    def _handle_vendor_list(
        self,
        vendor_type: str = "all",
        status: str = "all",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        """List registered vendors with optional filtering by type and operational status."""
        try:
            from src.core.vendor_engine import get_vendor_engine

            engine = get_vendor_engine()
            res = engine.list_vendors(
                vendor_type=_clean_str(vendor_type) or "all",
                status=_clean_str(status) or "all",
                limit=int(limit) if limit is not None else 50,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Vendor list error: {exc}"}, indent=2)

    def _handle_vendor_assess(
        self,
        name: str,
        audit_type: str = "security",
        **kwargs: Any,
    ) -> str:
        """Run an automated security, compliance, or performance audit on a vendor provider."""
        try:
            from src.core.vendor_engine import get_vendor_engine

            engine = get_vendor_engine()
            res = engine.audit_vendor(
                name_or_id=_clean_str(name) or "",
                audit_type=_clean_str(audit_type) or "security",
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Vendor assess error: {exc}"}, indent=2)

    _handle_mekong_vendor_onboard = _handle_vendor_onboard
    _handle_mekong_vendor_list = _handle_vendor_list
    _handle_mekong_vendor_assess = _handle_vendor_assess

    def _handle_founder_assess(
        self,
        name: str = "",
        mission: str = "",
        tipi_responses: Optional[dict[str, int]] = None,
        values: Optional[list[str]] = None,
        fears: Optional[list[dict[str, Any]]] = None,
        risk_ratings: Optional[dict[str, int]] = None,
        bias_responses: Optional[dict[str, bool]] = None,
        particle_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Assess a founder genome with personality, core values, fears, risk tolerance, and cognitive biases."""
        try:
            from src.core.founder_engine import get_founder_engine

            engine = get_founder_engine()
            res = engine.assess_founder(
                name=_clean_str(name) or (f"founder-{mission[:16].replace(' ', '-').lower()}" if mission else "founder-anonymous"),
                mission=_clean_str(mission) or "",
                tipi_responses=tipi_responses if isinstance(tipi_responses, dict) else {},
                values=values if isinstance(values, list) else [],
                fears=fears if isinstance(fears, list) else [],
                risk_ratings=risk_ratings if isinstance(risk_ratings, dict) else {},
                bias_responses=bias_responses if isinstance(bias_responses, dict) else {},
                particle_id=_clean_str(particle_id) or None,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Founder assess error: {exc}"}, indent=2)

    def _handle_founder_review(
        self,
        founder_id: str,
        **kwargs: Any,
    ) -> str:
        """Load and inspect a complete founder genome profile from the registry."""
        try:
            from src.core.founder_engine import get_founder_engine

            engine = get_founder_engine()
            res = engine.get_founder(_clean_str(founder_id) or "")
            if res is None:
                return json.dumps({"ok": False, "error": f"Founder '{founder_id}' not found"}, indent=2)
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Founder review error: {exc}"}, indent=2)

    def _handle_founder_list(
        self,
        risk_level: str = "all",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        """List assessed founder genome profiles with optional risk level filtering."""
        try:
            from src.core.founder_engine import get_founder_engine

            engine = get_founder_engine()
            res = engine.list_founders(
                risk_level=_clean_str(risk_level) or "all",
                limit=int(limit) if limit is not None else 50,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Founder list error: {exc}"}, indent=2)

    _handle_mekong_founder_assess = _handle_founder_assess
    _handle_mekong_founder_review = _handle_founder_review
    _handle_mekong_founder_list = _handle_founder_list

    def _handle_governance_propose(
        self,
        title: str,
        description: str,
        text: str,
        proposer: str = "founder",
        tier: str = "soft",
        co_sponsors: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Draft and submit a new constitutional amendment proposal."""
        try:
            from src.core.governance_engine import get_governance_engine

            engine = get_governance_engine()
            res = engine.create_proposal(
                title=_clean_str(title) or "",
                description=_clean_str(description) or "",
                text=_clean_str(text) or "",
                proposer=_clean_str(proposer) or "founder",
                tier=_clean_str(tier) or "soft",
                co_sponsors=co_sponsors if isinstance(co_sponsors, list) else [],
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Governance propose error: {exc}"}, indent=2)

    def _handle_governance_vote(
        self,
        proposal_id: str,
        choice: str = "yes",
        voter: str = "founder",
        weight: float = 1.0,
        **kwargs: Any,
    ) -> str:
        """Cast a weighted cryptographic ballot on an active governance proposal."""
        try:
            from src.core.governance_engine import get_governance_engine

            engine = get_governance_engine()
            res = engine.cast_vote(
                proposal_id=_clean_str(proposal_id) or "",
                voter=_clean_str(voter) or "founder",
                choice=_clean_str(choice) or "yes",
                weight=float(weight) if weight is not None else 1.0,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Governance vote error: {exc}"}, indent=2)

    def _handle_governance_tally(
        self,
        proposal_id: str,
        **kwargs: Any,
    ) -> str:
        """Tally ballots, compute quorum satisfaction, and finalize proposal outcome."""
        try:
            from src.core.governance_engine import get_governance_engine

            engine = get_governance_engine()
            res = engine.tally_votes(proposal_id=_clean_str(proposal_id) or "")
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Governance tally error: {exc}"}, indent=2)

    def _handle_governance_list(
        self,
        status: str = "all",
        tier: str = "all",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        """List constitutional governance proposals filtered by status and tier."""
        try:
            from src.core.governance_engine import get_governance_engine

            engine = get_governance_engine()
            res = engine.list_proposals(
                status=_clean_str(status) or "all",
                tier=_clean_str(tier) or "all",
                limit=int(limit) if limit is not None else 50,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Governance list error: {exc}"}, indent=2)

    _handle_mekong_governance_propose = _handle_governance_propose
    _handle_mekong_governance_vote = _handle_governance_vote
    _handle_mekong_governance_tally = _handle_governance_tally
    _handle_mekong_governance_list = _handle_governance_list

    def _handle_particle_init(
        self,
        name: str = "",
        mission: str = "",
        template: str = "skel",
        **kwargs: Any,
    ) -> str:
        clean_name = _clean_str(name)
        if not clean_name:
            return json.dumps({"ok": False, "error": "Missing required argument 'name'"}, indent=2)

        try:
            from src.core.particle_engine import ParticleEngine

            engine = ParticleEngine()
            res = engine.init_particle(
                name=clean_name,
                mission=_clean_str(mission),
                template=_clean_str(template) or "skel",
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Particle init error: {exc}"}, indent=2)

    def _handle_particle_status(
        self,
        particle_id: str = "default",
        **kwargs: Any,
    ) -> str:
        pid = _clean_str(particle_id) or "default"
        try:
            from src.core.particle_engine import ParticleEngine

            engine = ParticleEngine()
            if pid in ("default", ""):
                res = engine.get_status()
            else:
                res = engine.get_particle_status(pid)
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Particle status error: {exc}"}, indent=2)

    def _handle_particle_connect(
        self,
        particle_a: str = "",
        particle_b: str = "",
        trust_score: float = 50.0,
        **kwargs: Any,
    ) -> str:
        pa = _clean_str(particle_a)
        pb = _clean_str(particle_b)
        if not pa or not pb:
            return json.dumps({"ok": False, "error": "Both 'particle_a' and 'particle_b' are required."}, indent=2)

        try:
            from src.core.particle_engine import ParticleEngine

            engine = ParticleEngine()
            res = engine.connect_particles(
                particle_a=pa,
                particle_b=pb,
                trust_score=float(trust_score) if trust_score is not None else 50.0,
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Particle connect error: {exc}"}, indent=2)

    def _handle_particle_cell_run(
        self,
        role: str = "",
        prompt: str = "",
        particle_id: str = "default",
        auto_compliance: bool = False,
        **kwargs: Any,
    ) -> str:
        clean_role = _clean_str(role)
        clean_prompt = _clean_str(prompt)
        if not clean_role or not clean_prompt:
            return json.dumps({"ok": False, "error": "Both 'role' and 'prompt' are required."}, indent=2)

        try:
            from src.core.particle_engine import ParticleEngine

            engine = ParticleEngine()
            res = engine.run_cell(
                role=clean_role,
                prompt=clean_prompt,
                particle_id=_clean_str(particle_id) or "default",
                auto_compliance=bool(auto_compliance),
            )
            return json.dumps(res, indent=2)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Particle cell run error: {exc}"}, indent=2)

    _handle_mekong_particle_init = _handle_particle_init
    _handle_mekong_particle_status = _handle_particle_status
    _handle_mekong_particle_connect = _handle_particle_connect
    _handle_mekong_particle_cell_run = _handle_particle_cell_run

    def _handle_thue_tncn(
        self,
        monthly_income: float = 0.0,
        dependents: int = 0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.thue_engine import ThueEngine

            engine = ThueEngine()
            res = engine.calculate_tncn(monthly_income=float(monthly_income), dependents=int(dependents))
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tax TNCN error: {exc}"}, indent=2)

    def _handle_thue_tndn(
        self,
        annual_revenue: float = 0.0,
        profit: float = 0.0,
        is_sme: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.thue_engine import ThueEngine

            engine = ThueEngine()
            res = engine.calculate_tndn(
                annual_revenue=float(annual_revenue),
                profit=float(profit) if profit > 0 else None,
                is_sme=bool(is_sme),
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tax TNDN error: {exc}"}, indent=2)

    def _handle_thue_gtgt(
        self,
        amount: float = 0.0,
        rate: int = 10,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.thue_engine import ThueEngine

            engine = ThueEngine()
            res = engine.calculate_gtgt(amount=float(amount), rate=int(rate))
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tax GTGT error: {exc}"}, indent=2)

    def _handle_thue_status(self, **kwargs: Any) -> str:
        try:
            from src.core.thue_engine import ThueEngine

            engine = ThueEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tax status error: {exc}"}, indent=2)

    _handle_mekong_thue_tncn = _handle_thue_tncn
    _handle_mekong_thue_tndn = _handle_thue_tndn
    _handle_mekong_thue_gtgt = _handle_thue_gtgt
    _handle_mekong_thue_status = _handle_thue_status

    def _handle_ke_toan_create(
        self,
        amount: float = 0.0,
        buyer: str = "Khách Hàng",
        vat_rate: int = 10,
        seller: str = "Doanh Nghiệp",
        seller_tax_code: str = "0000000000",
        buyer_tax_code: str = "",
        description: str = "Hàng hóa/Dịch vụ",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ke_toan_engine import KeToanEngine

            engine = KeToanEngine()
            res = engine.create_invoice(
                amount=float(amount),
                buyer=str(buyer),
                vat_rate=int(vat_rate),
                seller=str(seller),
                seller_tax_code=str(seller_tax_code),
                buyer_tax_code=str(buyer_tax_code),
                description=str(description),
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Accounting create error: {exc}"}, indent=2)

    def _handle_ke_toan_xml(
        self,
        amount: float = 0.0,
        buyer: str = "Khách Hàng",
        vat_rate: int = 10,
        seller: str = "Doanh Nghiệp",
        seller_tax_code: str = "0000000000",
        description: str = "Hàng hóa/Dịch vụ",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ke_toan_engine import KeToanEngine

            engine = KeToanEngine()
            inv = engine.create_invoice(
                amount=float(amount),
                buyer=str(buyer),
                vat_rate=int(vat_rate),
                seller=str(seller),
                seller_tax_code=str(seller_tax_code),
                description=str(description),
                save=False,
            )
            return inv.get("xml_content", "")
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Accounting XML error: {exc}"}, indent=2)

    def _handle_ke_toan_journal(
        self,
        amount: float = 0.0,
        buyer: str = "Khách Hàng",
        vat_rate: int = 10,
        seller: str = "Doanh Nghiệp",
        seller_tax_code: str = "0000000000",
        description: str = "Hàng hóa/Dịch vụ",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ke_toan_engine import KeToanEngine

            engine = KeToanEngine()
            inv = engine.create_invoice(
                amount=float(amount),
                buyer=str(buyer),
                vat_rate=int(vat_rate),
                seller=str(seller),
                seller_tax_code=str(seller_tax_code),
                description=str(description),
                save=False,
            )
            res = engine.create_vas_journal(inv, save=True)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Accounting journal error: {exc}"}, indent=2)

    def _handle_ke_toan_status(self, **kwargs: Any) -> str:
        try:
            from src.core.ke_toan_engine import KeToanEngine

            engine = KeToanEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Accounting status error: {exc}"}, indent=2)

    _handle_mekong_ke_toan_create = _handle_ke_toan_create
    _handle_mekong_ke_toan_xml = _handle_ke_toan_xml
    _handle_mekong_ke_toan_journal = _handle_ke_toan_journal
    _handle_mekong_ke_toan_status = _handle_ke_toan_status

    def _handle_zalo_send(
        self,
        user_id: str = "",
        message: str = "",
        template: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.zalo_engine import ZaloEngine

            engine = ZaloEngine()
            res = engine.send_message(user_id=str(user_id), text=str(message), template=str(template))
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Zalo send error: {exc}"}, indent=2)

    def _handle_zalo_broadcast(
        self,
        message: str = "",
        title: str = "Thông báo Zalo OA",
        target_segment: str = "all",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.zalo_engine import ZaloEngine

            engine = ZaloEngine()
            res = engine.broadcast_campaign(title=str(title), text=str(message), target_segment=str(target_segment))
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Zalo broadcast error: {exc}"}, indent=2)

    def _handle_zalo_followers(
        self,
        segment: str = "all",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.zalo_engine import ZaloEngine

            engine = ZaloEngine()
            followers = engine.list_followers(segment=str(segment), limit=int(limit))
            return json.dumps({"total": len(followers), "followers": followers}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Zalo followers error: {exc}"}, indent=2)

    def _handle_zalo_caption(
        self,
        topic: str = "Sản phẩm",
        tone: str = "vui_ve",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.zalo_engine import ZaloEngine

            engine = ZaloEngine()
            res = engine.generate_caption(topic=str(topic), tone=str(tone))
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Zalo caption error: {exc}"}, indent=2)

    def _handle_zalo_status(self, **kwargs: Any) -> str:
        try:
            from src.core.zalo_engine import ZaloEngine

            engine = ZaloEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Zalo status error: {exc}"}, indent=2)

    _handle_mekong_zalo_send = _handle_zalo_send
    _handle_mekong_zalo_broadcast = _handle_zalo_broadcast
    _handle_mekong_zalo_followers = _handle_zalo_followers
    _handle_mekong_zalo_caption = _handle_zalo_caption
    _handle_mekong_zalo_status = _handle_zalo_status

    def _handle_bhxh_calc(
        self,
        salary: float = 0.0,
        region: int = 1,
        include_kpcd: bool = False,
        employee_id: str = "ADHOC",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.bhxh_engine import BhxhEngine

            engine = BhxhEngine()
            res = engine.calculate_contribution(
                salary=float(salary),
                region=int(region),
                include_kpcd=bool(include_kpcd),
                employee_id=str(employee_id),
                save=True,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"BHXH calculation error: {exc}"}, indent=2)

    def _handle_bhxh_employees(
        self,
        status: str = "all",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.bhxh_engine import BhxhEngine

            engine = BhxhEngine()
            emps = engine.list_employees(status=str(status))
            return json.dumps({"total": len(emps), "employees": emps}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"BHXH employees error: {exc}"}, indent=2)

    def _handle_bhxh_declaration(
        self,
        change_type: str = "dieu_chinh_luong",
        employee_id: str = "",
        effective_month: str = "",
        new_salary: float = 0.0,
        note: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.bhxh_engine import BhxhEngine

            engine = BhxhEngine()
            res = engine.create_declaration_d02lt(
                change_type=str(change_type),
                employee_id=str(employee_id),
                effective_month=str(effective_month),
                new_salary=float(new_salary),
                note=str(note),
                save=True,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"BHXH declaration error: {exc}"}, indent=2)

    def _handle_bhxh_status(self, **kwargs: Any) -> str:
        try:
            from src.core.bhxh_engine import BhxhEngine

            engine = BhxhEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"BHXH status error: {exc}"}, indent=2)

    _handle_mekong_bhxh_calc = _handle_bhxh_calc
    _handle_mekong_bhxh_employees = _handle_bhxh_employees
    _handle_mekong_bhxh_declaration = _handle_bhxh_declaration
    _handle_mekong_bhxh_status = _handle_bhxh_status

    def _handle_ocop_eval(
        self,
        product_name: str,
        part_a: float = 30.0,
        part_b: float = 22.0,
        part_c: float = 38.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ocop_engine import OcopEngine

            engine = OcopEngine()
            res = engine.evaluate_star_rating(
                product_name=product_name,
                part_a_community=part_a,
                part_b_marketing=part_b,
                part_c_quality=part_c,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"OCOP eval error: {exc}"}, indent=2)

    def _handle_ocop_products(
        self,
        min_stars: int = 1,
        province: str = "all",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ocop_engine import OcopEngine

            engine = OcopEngine()
            prods = engine.list_products(min_stars=min_stars, province=province)
            return json.dumps({"ok": True, "total": len(prods), "products": prods}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"OCOP products error: {exc}"}, indent=2)

    def _handle_ocop_listing(
        self,
        product_id: str,
        target_market: str = "EU",
        platform: str = "alibaba",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ocop_engine import OcopEngine

            engine = OcopEngine()
            res = engine.generate_b2b_listing(
                product_id=product_id,
                target_market=target_market,
                platform=platform,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"OCOP listing error: {exc}"}, indent=2)

    def _handle_ocop_compliance(
        self,
        market: str = "EU",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ocop_engine import OcopEngine

            engine = OcopEngine()
            res = engine.get_market_compliance(market)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"OCOP compliance error: {exc}"}, indent=2)

    def _handle_ocop_status(self, **kwargs: Any) -> str:
        try:
            from src.core.ocop_engine import OcopEngine

            engine = OcopEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"OCOP status error: {exc}"}, indent=2)

    _handle_mekong_ocop_eval = _handle_ocop_eval
    _handle_mekong_ocop_products = _handle_ocop_products
    _handle_mekong_ocop_listing = _handle_ocop_listing
    _handle_mekong_ocop_compliance = _handle_ocop_compliance
    _handle_mekong_ocop_status = _handle_ocop_status

    def _handle_vietqr_generate(
        self,
        amount: int = 0,
        memo: str = "",
        bank: str = "MB",
        account_number: str = "",
        account_name: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.vietqr_engine import VietQrEngine

            engine = VietQrEngine()
            res = engine.generate_qr(
                bank=bank,
                account_number=account_number,
                account_name=account_name,
                amount_vnd=amount,
                memo=memo,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"VietQR generate error: {exc}"}, indent=2)

    def _handle_vietqr_banks(self, **kwargs: Any) -> str:
        try:
            from src.core.vietqr_engine import VietQrEngine

            engine = VietQrEngine()
            banks = engine.list_banks()
            return json.dumps({"ok": True, "total": len(banks), "banks": banks}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"VietQR banks error: {exc}"}, indent=2)

    def _handle_vietqr_transactions(self, limit: int = 20, **kwargs: Any) -> str:
        try:
            from src.core.vietqr_engine import VietQrEngine

            engine = VietQrEngine()
            txs = engine.list_transactions(limit=limit)
            return json.dumps({"ok": True, "total": len(txs), "transactions": txs}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"VietQR transactions error: {exc}"}, indent=2)

    def _handle_vietqr_record(
        self,
        bank_tx_id: str,
        amount_vnd: int,
        memo: str = "",
        bin_code: str = "970422",
        matched_order_id: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.vietqr_engine import VietQrEngine

            engine = VietQrEngine()
            res = engine.record_transaction(
                bank_tx_id=bank_tx_id,
                amount_vnd=amount_vnd,
                memo=memo,
                bin_code=bin_code,
                matched_order_id=matched_order_id or None,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"VietQR record error: {exc}"}, indent=2)

    def _handle_vietqr_status(self, **kwargs: Any) -> str:
        try:
            from src.core.vietqr_engine import VietQrEngine

            engine = VietQrEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"VietQR status error: {exc}"}, indent=2)

    _handle_mekong_vietqr_generate = _handle_vietqr_generate
    _handle_mekong_vietqr_banks = _handle_vietqr_banks
    _handle_mekong_vietqr_transactions = _handle_vietqr_transactions
    _handle_mekong_vietqr_record = _handle_vietqr_record
    _handle_mekong_vietqr_status = _handle_vietqr_status

    def _handle_audit_run(self, framework: str = "all", **kwargs: Any) -> str:
        try:
            from src.core.sox_audit_engine import SoxAuditEngine

            engine = SoxAuditEngine()
            res = engine.run_audit(framework=framework)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Audit run error: {exc}"}, indent=2)

    def _handle_audit_controls(
        self, domain: str = "all", framework: str = "all", **kwargs: Any
    ) -> str:
        try:
            from src.core.sox_audit_engine import SoxAuditEngine

            engine = SoxAuditEngine()
            res = engine.list_controls(domain=domain, framework=framework)
            return json.dumps({"ok": True, "controls": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Audit controls error: {exc}"}, indent=2)

    def _handle_audit_findings(self, min_severity: str = "all", **kwargs: Any) -> str:
        try:
            from src.core.sox_audit_engine import SoxAuditEngine

            engine = SoxAuditEngine()
            res = engine.list_findings(min_severity=min_severity)
            return json.dumps({"ok": True, "findings": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Audit findings error: {exc}"}, indent=2)

    def _handle_audit_status(self, **kwargs: Any) -> str:
        try:
            from src.core.sox_audit_engine import SoxAuditEngine

            engine = SoxAuditEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Audit status error: {exc}"}, indent=2)

    _handle_mekong_audit_run = _handle_audit_run
    _handle_mekong_audit_controls = _handle_audit_controls
    _handle_mekong_audit_findings = _handle_audit_findings
    _handle_mekong_audit_status = _handle_audit_status

    def _handle_payroll_gross_to_net(
        self,
        gross: float,
        dependents: int = 0,
        region: int = 1,
        lunch_allowance: float = 730000.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.payroll_engine import PayrollEngine

            engine = PayrollEngine()
            res = engine.calculate_gross_to_net(
                gross=gross,
                dependents=dependents,
                region=region,
                lunch_allowance=lunch_allowance,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Payroll gross-to-net error: {exc}"}, indent=2)

    def _handle_payroll_net_to_gross(
        self,
        net: float,
        dependents: int = 0,
        region: int = 1,
        lunch_allowance: float = 730000.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.payroll_engine import PayrollEngine

            engine = PayrollEngine()
            res = engine.calculate_net_to_gross(
                net=net,
                dependents=dependents,
                region=region,
                lunch_allowance=lunch_allowance,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Payroll net-to-gross error: {exc}"}, indent=2)

    def _handle_payroll_payslip(
        self,
        employee_name: str,
        gross: float,
        employee_id: str = "",
        month: str = "",
        dependents: int = 0,
        region: int = 1,
        bonus: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.payroll_engine import PayrollEngine

            engine = PayrollEngine()
            res = engine.generate_payslip(
                employee_name=employee_name,
                gross=gross,
                employee_id=employee_id or None,
                month=month or None,
                dependents=dependents,
                region=region,
                bonus=bonus,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Payroll payslip error: {exc}"}, indent=2)

    def _handle_payroll_list(self, month: str = "", limit: int = 20, **kwargs: Any) -> str:
        try:
            from src.core.payroll_engine import PayrollEngine

            engine = PayrollEngine()
            res = engine.list_payslips(month=month, limit=limit)
            return json.dumps({"ok": True, "payslips": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Payroll list error: {exc}"}, indent=2)

    def _handle_payroll_status(self, **kwargs: Any) -> str:
        try:
            from src.core.payroll_engine import PayrollEngine

            engine = PayrollEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Payroll status error: {exc}"}, indent=2)

    _handle_mekong_payroll_gross_to_net = _handle_payroll_gross_to_net
    _handle_mekong_payroll_net_to_gross = _handle_payroll_net_to_gross
    _handle_mekong_payroll_payslip = _handle_payroll_payslip
    _handle_mekong_payroll_list = _handle_payroll_list
    _handle_mekong_payroll_status = _handle_payroll_status

    def _handle_corporate_charter(
        self,
        company_name: str,
        entity_type: str = "TNHH_1TV",
        charter_capital: int = 1000000000,
        legal_rep_name: str = "Nguyễn Văn A",
        address: str = "Hà Nội, Việt Nam",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.corporate_engine import CorporateEngine

            engine = CorporateEngine()
            res = engine.generate_charter(
                company_name=company_name,
                entity_type=entity_type,
                charter_capital=charter_capital,
                legal_rep_name=legal_rep_name,
                address=address,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Corporate charter error: {exc}"}, indent=2)

    def _handle_corporate_resolution(
        self,
        company_name: str,
        resolution_type: str = "APPOINTMENT",
        title: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.corporate_engine import CorporateEngine

            engine = CorporateEngine()
            res = engine.generate_resolution(
                company_name=company_name,
                resolution_type=resolution_type,
                title=title,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Corporate resolution error: {exc}"}, indent=2)

    def _handle_corporate_dossier(
        self,
        company_name: str,
        entity_type: str = "TNHH_1TV",
        charter_capital: int = 1000000000,
        legal_rep_name: str = "Nguyễn Văn A",
        address: str = "Hà Nội, Việt Nam",
        main_industry: str = "6201",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.corporate_engine import CorporateEngine

            engine = CorporateEngine()
            res = engine.create_filing_dossier(
                company_name=company_name,
                entity_type=entity_type,
                charter_capital=charter_capital,
                legal_rep_name=legal_rep_name,
                address=address,
                main_industry=main_industry,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Corporate dossier error: {exc}"}, indent=2)

    def _handle_corporate_list(self, limit: int = 20, **kwargs: Any) -> str:
        try:
            from src.core.corporate_engine import CorporateEngine

            engine = CorporateEngine()
            res = engine.list_filings(limit=limit)
            return json.dumps({"ok": True, "filings": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Corporate list error: {exc}"}, indent=2)

    def _handle_corporate_status(self, **kwargs: Any) -> str:
        try:
            from src.core.corporate_engine import CorporateEngine

            engine = CorporateEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Corporate status error: {exc}"}, indent=2)

    _handle_mekong_corporate_charter = _handle_corporate_charter
    _handle_mekong_corporate_resolution = _handle_corporate_resolution
    _handle_mekong_corporate_dossier = _handle_corporate_dossier
    _handle_mekong_corporate_list = _handle_corporate_list
    _handle_mekong_corporate_status = _handle_corporate_status

    def _handle_fdi_market_access(
        self,
        sector_code: str,
        investor_nationality: str = "US",
        ownership_pct: float = 100.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.fdi_engine import FDIEngine

            engine = FDIEngine()
            res = engine.evaluate_market_access(
                sector_code=sector_code,
                investor_nationality=investor_nationality,
                ownership_pct=ownership_pct,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"FDI market access error: {exc}"}, indent=2)

    def _handle_fdi_remittance(
        self,
        fiscal_year: int,
        audited_profit_vnd: float,
        tax_cleared: bool = True,
        retained_reserve_pct: float = 5.0,
        dica_verified: bool = True,
        losses_carried_forward_vnd: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.fdi_engine import FDIEngine

            engine = FDIEngine()
            res = engine.verify_profit_remittance(
                fiscal_year=fiscal_year,
                audited_profit_vnd=audited_profit_vnd,
                tax_cleared=tax_cleared,
                retained_reserve_pct=retained_reserve_pct,
                dica_verified=dica_verified,
                losses_carried_forward_vnd=losses_carried_forward_vnd,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"FDI remittance error: {exc}"}, indent=2)

    def _handle_fdi_foreign_loan(
        self,
        loan_amount: float,
        currency: str = "USD",
        tenure_months: int = 24,
        interest_rate_pct: float = 6.5,
        project_capital_gap: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.fdi_engine import FDIEngine

            engine = FDIEngine()
            res = engine.evaluate_foreign_loan(
                loan_amount=loan_amount,
                currency=currency,
                tenure_months=tenure_months,
                interest_rate_pct=interest_rate_pct,
                project_capital_gap=project_capital_gap,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"FDI foreign loan error: {exc}"}, indent=2)

    def _handle_fdi_irc(
        self,
        project_name: str,
        sector_code: str,
        total_investment_vnd: float,
        investor_name: str,
        investor_country: str = "US",
        project_location: str = "TP. Hồ Chí Minh",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.fdi_engine import FDIEngine

            engine = FDIEngine()
            res = engine.generate_irc_dossier(
                project_name=project_name,
                sector_code=sector_code,
                total_investment_vnd=total_investment_vnd,
                investor_name=investor_name,
                investor_country=investor_country,
                project_location=project_location,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"FDI IRC dossier error: {exc}"}, indent=2)

    def _handle_fdi_status(self, **kwargs: Any) -> str:
        try:
            from src.core.fdi_engine import FDIEngine

            engine = FDIEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"FDI status error: {exc}"}, indent=2)

    _handle_mekong_fdi_market_access = _handle_fdi_market_access
    _handle_mekong_fdi_remittance = _handle_fdi_remittance
    _handle_mekong_fdi_foreign_loan = _handle_fdi_foreign_loan
    _handle_mekong_fdi_irc = _handle_fdi_irc
    _handle_mekong_fdi_status = _handle_fdi_status

    def _handle_ip_trademark(
        self,
        mark_name: str,
        nice_class: str = "09",
        applicant_name: str = "Công Ty Công Nghệ Mekong",
        goods_services_spec: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ip_engine import IPEngine

            engine = IPEngine()
            res = engine.register_trademark(
                mark_name=mark_name,
                nice_class=nice_class,
                applicant_name=applicant_name,
                goods_services_spec=goods_services_spec,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"IP trademark error: {exc}"}, indent=2)

    def _handle_ip_search(
        self,
        mark_name: str,
        nice_class: str = "09",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ip_engine import IPEngine

            engine = IPEngine()
            res = engine.search_trademark_similarity(
                mark_name=mark_name,
                nice_class=nice_class,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"IP search error: {exc}"}, indent=2)

    def _handle_ip_patent(
        self,
        title: str,
        technical_field: str,
        applicant_name: str = "Tổ chức Nghiên cứu Mekong",
        independent_claims: int = 1,
        dependent_claims: int = 2,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ip_engine import IPEngine

            engine = IPEngine()
            res = engine.draft_patent_specification(
                title=title,
                technical_field=technical_field,
                applicant_name=applicant_name,
                independent_claims=independent_claims,
                dependent_claims=dependent_claims,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"IP patent error: {exc}"}, indent=2)

    def _handle_ip_copyright(
        self,
        software_name: str,
        author_name: str,
        version: str = "1.0.0",
        repository_url: str = "",
        lines_of_code: int = 10000,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ip_engine import IPEngine

            engine = IPEngine()
            res = engine.register_software_copyright(
                software_name=software_name,
                author_name=author_name,
                version=version,
                repository_url=repository_url,
                lines_of_code=lines_of_code,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"IP copyright error: {exc}"}, indent=2)

    def _handle_ip_fees(
        self,
        trademark_classes: int = 1,
        patent_claims: int = 1,
        software_copyrights: int = 1,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ip_engine import IPEngine

            engine = IPEngine()
            res = engine.calculate_statutory_fees(
                trademark_classes=trademark_classes,
                patent_claims=patent_claims,
                software_copyrights=software_copyrights,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"IP fees error: {exc}"}, indent=2)

    def _handle_ip_status(self, **kwargs: Any) -> str:
        try:
            from src.core.ip_engine import IPEngine

            engine = IPEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"IP status error: {exc}"}, indent=2)

    _handle_mekong_ip_trademark = _handle_ip_trademark
    _handle_mekong_ip_search = _handle_ip_search
    _handle_mekong_ip_patent = _handle_ip_patent
    _handle_mekong_ip_copyright = _handle_ip_copyright
    _handle_mekong_ip_fees = _handle_ip_fees
    _handle_mekong_ip_status = _handle_ip_status

    def _handle_customs_hs_lookup(
        self,
        hs_code: str,
        fta: str = "MFN",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.customs_engine import CustomsEngine

            engine = CustomsEngine()
            res = engine.lookup_hs_code(hs_code=hs_code, fta=fta)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Customs HS lookup error: {exc}"}, indent=2)

    def _handle_customs_duty_calc(
        self,
        invoice_value_usd: float,
        hs_code: str = "8471.30.20",
        freight_usd: float = 0.0,
        insurance_usd: float = 0.0,
        fta: str = "MFN",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.customs_engine import CustomsEngine

            engine = CustomsEngine()
            res = engine.calculate_customs_duties(
                invoice_value_usd=invoice_value_usd,
                hs_code=hs_code,
                freight_usd=freight_usd,
                insurance_usd=insurance_usd,
                fta=fta,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Customs duty calculation error: {exc}"}, indent=2)

    def _handle_customs_channel(
        self,
        enterprise_tax_id: str,
        hs_code: str,
        invoice_value_usd: float,
        origin_country: str = "US",
        compliance_tier: str = "TIER_2_NORMAL",
        has_valid_co: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.customs_engine import CustomsEngine

            engine = CustomsEngine()
            res = engine.evaluate_customs_channel(
                enterprise_tax_id=enterprise_tax_id,
                hs_code=hs_code,
                invoice_value_usd=invoice_value_usd,
                origin_country=origin_country,
                compliance_tier=compliance_tier,
                has_valid_co=has_valid_co,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Customs channel evaluation error: {exc}"}, indent=2)

    def _handle_customs_declare(
        self,
        enterprise_tax_id: str,
        hs_code: str,
        commodity_name: str,
        invoice_value_usd: float,
        origin_country: str = "US",
        declaration_type: str = "IMPORT_BUSINESS",
        compliance_tier: str = "TIER_2_NORMAL",
        has_valid_co: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.customs_engine import CustomsEngine

            engine = CustomsEngine()
            res = engine.create_declaration(
                enterprise_tax_id=enterprise_tax_id,
                hs_code=hs_code,
                commodity_name=commodity_name,
                invoice_value_usd=invoice_value_usd,
                origin_country=origin_country,
                declaration_type=declaration_type,
                compliance_tier=compliance_tier,
                has_valid_co=has_valid_co,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Customs declaration error: {exc}"}, indent=2)

    def _handle_customs_origin(
        self,
        form_type: str,
        hs_code: str,
        fob_value_usd: float,
        non_originating_value_usd: float,
        exporter_name: str = "Doanh Nghiệp Xuất Khẩu Việt Nam",
        importer_country: str = "DE",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.customs_engine import CustomsEngine

            engine = CustomsEngine()
            res = engine.verify_rules_of_origin(
                form_type=form_type,
                hs_code=hs_code,
                fob_value_usd=fob_value_usd,
                non_originating_value_usd=non_originating_value_usd,
                exporter_name=exporter_name,
                importer_country=importer_country,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Customs origin verification error: {exc}"}, indent=2)

    def _handle_customs_status(self, **kwargs: Any) -> str:
        try:
            from src.core.customs_engine import CustomsEngine

            engine = CustomsEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Customs status error: {exc}"}, indent=2)

    _handle_mekong_customs_hs_lookup = _handle_customs_hs_lookup
    _handle_mekong_customs_duty_calc = _handle_customs_duty_calc
    _handle_mekong_customs_channel = _handle_customs_channel
    _handle_mekong_customs_declare = _handle_customs_declare
    _handle_mekong_customs_origin = _handle_customs_origin
    _handle_mekong_customs_status = _handle_customs_status

    def _handle_contract_draft(
        self,
        template_type: str,
        party_a_name: str,
        party_b_name: str,
        contract_value_vnd: float = 0.0,
        party_a_tax_id: str = "0100000001",
        party_b_tax_id: str = "0300000002",
        scope_summary: str = "",
        penalty_rate_pct: float = 8.0,
        dispute_forum: str = "VIAC",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.contract_engine import ContractEngine

            engine = ContractEngine()
            res = engine.draft_contract(
                template_type=template_type,
                party_a_name=party_a_name,
                party_b_name=party_b_name,
                contract_value_vnd=contract_value_vnd,
                party_a_tax_id=party_a_tax_id,
                party_b_tax_id=party_b_tax_id,
                scope_summary=scope_summary,
                penalty_rate_pct=penalty_rate_pct,
                dispute_forum=dispute_forum,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Contract drafting error: {exc}"}, indent=2)

    def _handle_contract_risk_check(
        self,
        contract_text: str,
        penalty_pct: Any = None,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.contract_engine import ContractEngine

            engine = ContractEngine()
            p_val = float(penalty_pct) if penalty_pct is not None else None
            res = engine.assess_contract_risk(contract_text=contract_text, penalty_pct=p_val)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Contract risk assessment error: {exc}"}, indent=2)

    def _handle_contract_sign(
        self,
        contract_id: str,
        signer_name: str,
        signer_title: str = "Giám đốc điều hành",
        signer_tax_id: str = "0100000001",
        organization_name: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.contract_engine import ContractEngine

            engine = ContractEngine()
            res = engine.sign_contract(
                contract_id=contract_id,
                signer_name=signer_name,
                signer_title=signer_title,
                signer_tax_id=signer_tax_id,
                organization_name=organization_name,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Contract e-signing error: {exc}"}, indent=2)

    def _handle_contract_verify(
        self,
        signature_id: str,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.contract_engine import ContractEngine

            engine = ContractEngine()
            res = engine.verify_signature(signature_id=signature_id)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Contract signature verification error: {exc}"}, indent=2)

    def _handle_contract_list(
        self,
        status: str = "ALL",
        limit: int = 20,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.contract_engine import ContractEngine

            engine = ContractEngine()
            res = engine.list_contracts(status=status, limit=limit)
            return json.dumps({"ok": True, "contracts": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Contract list error: {exc}"}, indent=2)

    def _handle_contract_status(self, **kwargs: Any) -> str:
        try:
            from src.core.contract_engine import ContractEngine

            engine = ContractEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Contract status error: {exc}"}, indent=2)

    _handle_mekong_contract_draft = _handle_contract_draft
    _handle_mekong_contract_risk_check = _handle_contract_risk_check
    _handle_mekong_contract_sign = _handle_contract_sign
    _handle_mekong_contract_verify = _handle_contract_verify
    _handle_mekong_contract_list = _handle_contract_list
    _handle_mekong_contract_status = _handle_contract_status

    def _handle_tender_method(
        self,
        package_type: str,
        budget_vnd: float,
        urgent: bool = False,
        proprietary: bool = False,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.tender_engine import TenderEngine

            engine = TenderEngine()
            res = engine.evaluate_procurement_method(
                package_type=package_type,
                budget_vnd=budget_vnd,
                is_urgent=urgent,
                is_proprietary_tech=proprietary,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tender method evaluation error: {exc}"}, indent=2)

    def _handle_tender_create(
        self,
        package_name: str,
        procuring_entity: str,
        budget_vnd: float,
        package_type: str = "GOODS",
        procurement_method: str = "",
        submission_days: int = 15,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.tender_engine import TenderEngine

            engine = TenderEngine()
            p_method = procurement_method if procurement_method else None
            res = engine.create_tender(
                package_name=package_name,
                procuring_entity=procuring_entity,
                budget_vnd=budget_vnd,
                package_type=package_type,
                procurement_method=p_method,
                submission_days=submission_days,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tender creation error: {exc}"}, indent=2)

    def _handle_tender_eval(
        self,
        tender_id: str,
        bidder_name: str,
        bid_price_vnd: float,
        bidder_tax_id: str = "0101234567",
        revenue_3yr_avg_vnd: float = 0.0,
        similar_contract_val_vnd: float = 0.0,
        tech_score: float = 85.0,
        has_valid_security: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.tender_engine import TenderEngine

            engine = TenderEngine()
            res = engine.evaluate_bid(
                tender_id=tender_id,
                bidder_name=bidder_name,
                bid_price_vnd=bid_price_vnd,
                bidder_tax_id=bidder_tax_id,
                revenue_3yr_avg_vnd=revenue_3yr_avg_vnd,
                similar_contract_val_vnd=similar_contract_val_vnd,
                tech_score=tech_score,
                has_valid_security=has_valid_security,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Bid evaluation error: {exc}"}, indent=2)

    def _handle_tender_collusion_scan(
        self,
        tender_id: str,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.tender_engine import TenderEngine

            engine = TenderEngine()
            res = engine.detect_bid_collusion(tender_id=tender_id)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Bid collusion scan error: {exc}"}, indent=2)

    def _handle_tender_list(
        self,
        status: str = "ALL",
        limit: int = 20,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.tender_engine import TenderEngine

            engine = TenderEngine()
            res = engine.list_tenders(status=status, limit=limit)
            return json.dumps({"ok": True, "tenders": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tender list error: {exc}"}, indent=2)

    def _handle_tender_status(self, **kwargs: Any) -> str:
        try:
            from src.core.tender_engine import TenderEngine

            engine = TenderEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Tender status error: {exc}"}, indent=2)

    _handle_mekong_tender_method = _handle_tender_method
    _handle_mekong_tender_create = _handle_tender_create
    _handle_mekong_tender_eval = _handle_tender_eval
    _handle_mekong_tender_collusion_scan = _handle_tender_collusion_scan
    _handle_mekong_tender_list = _handle_tender_list
    _handle_mekong_tender_status = _handle_tender_status

    def _handle_realestate_finance(
        self,
        category: str,
        area_sqm: float,
        unit_rent_usd: float,
        lease_term_months: int = 36,
        maintenance_fee_usd: float = 0.5,
        deposit_months: int = 3,
        annual_escalation_pct: float = 3.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.realestate_engine import RealEstateEngine

            engine = RealEstateEngine()
            res = engine.calculate_lease_financials(
                category=category,
                area_sqm=area_sqm,
                unit_rent_usd=unit_rent_usd,
                lease_term_months=lease_term_months,
                maintenance_fee_usd=maintenance_fee_usd,
                deposit_months=deposit_months,
                annual_escalation_pct=annual_escalation_pct,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Real estate financial calculation error: {exc}"}, indent=2)

    def _handle_realestate_density(
        self,
        lot_area_sqm: float,
        building_footprint_sqm: float,
        green_space_sqm: float,
        building_height_tier: str = "UP_TO_20M",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.realestate_engine import RealEstateEngine

            engine = RealEstateEngine()
            res = engine.validate_construction_density(
                lot_area_sqm=lot_area_sqm,
                building_footprint_sqm=building_footprint_sqm,
                green_space_sqm=green_space_sqm,
                building_height_tier=building_height_tier,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Density validation error: {exc}"}, indent=2)

    def _handle_realestate_audit(
        self,
        project_name: str,
        category: str,
        land_area_sqm: float,
        has_land_cert: bool = True,
        has_construction_permit: bool = True,
        has_fire_safety_cert: bool = True,
        tenure_remaining_years: float = 35.0,
        payment_term: str = "ANNUAL_RENT",
        has_disputes: bool = False,
        is_mortgaged_to_bank: bool = False,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.realestate_engine import RealEstateEngine

            engine = RealEstateEngine()
            res = engine.perform_due_diligence(
                project_name=project_name,
                category=category,
                land_area_sqm=land_area_sqm,
                has_land_cert=has_land_cert,
                has_construction_permit=has_construction_permit,
                has_fire_safety_cert=has_fire_safety_cert,
                tenure_remaining_years=tenure_remaining_years,
                payment_term=payment_term,
                has_disputes=has_disputes,
                is_mortgaged_to_bank=is_mortgaged_to_bank,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Real estate due diligence error: {exc}"}, indent=2)

    def _handle_realestate_draft(
        self,
        property_id: str,
        lessor_name: str,
        lessee_name: str,
        leased_area_sqm: float,
        unit_rent_usd: float,
        lease_term_months: int = 36,
        maintenance_fee_usd: float = 0.5,
        deposit_months: int = 3,
        dispute_resolution: str = "VIAC",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.realestate_engine import RealEstateEngine

            engine = RealEstateEngine()
            res = engine.draft_lease_agreement(
                property_id=property_id,
                lessor_name=lessor_name,
                lessee_name=lessee_name,
                leased_area_sqm=leased_area_sqm,
                unit_rent_usd=unit_rent_usd,
                lease_term_months=lease_term_months,
                maintenance_fee_usd=maintenance_fee_usd,
                deposit_months=deposit_months,
                dispute_resolution=dispute_resolution,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Lease agreement drafting error: {exc}"}, indent=2)

    def _handle_realestate_list(
        self,
        category: str = "ALL",
        limit: int = 20,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.realestate_engine import RealEstateEngine

            engine = RealEstateEngine()
            res = engine.list_properties(category=category, limit=limit)
            return json.dumps({"ok": True, "properties": res, "total": len(res)}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Real estate list error: {exc}"}, indent=2)

    def _handle_realestate_status(self, **kwargs: Any) -> str:
        try:
            from src.core.realestate_engine import RealEstateEngine

            engine = RealEstateEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Real estate status error: {exc}"}, indent=2)

    _handle_mekong_realestate_finance = _handle_realestate_finance
    _handle_mekong_realestate_density = _handle_realestate_density
    _handle_mekong_realestate_audit = _handle_realestate_audit
    _handle_mekong_realestate_draft = _handle_realestate_draft
    _handle_mekong_realestate_list = _handle_realestate_list
    _handle_mekong_realestate_status = _handle_realestate_status

    def _handle_esg_ghg(
        self,
        enterprise_name: str,
        reporting_year: int,
        fuel_diesel_liters: float = 0.0,
        fuel_gasoline_liters: float = 0.0,
        coal_tons: float = 0.0,
        lpg_kg: float = 0.0,
        electricity_kwh: float = 0.0,
        scope3_logistics_tco2e: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.esg_engine import EsgEngine

            engine = EsgEngine()
            res = engine.calculate_ghg_inventory(
                enterprise_name=enterprise_name,
                reporting_year=int(reporting_year),
                fuel_diesel_liters=float(fuel_diesel_liters),
                fuel_gasoline_liters=float(fuel_gasoline_liters),
                coal_tons=float(coal_tons),
                lpg_kg=float(lpg_kg),
                electricity_kwh=float(electricity_kwh),
                scope3_logistics_tco2e=float(scope3_logistics_tco2e),
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"ESG GHG inventory error: {exc}"}, indent=2)

    def _handle_esg_cbam(
        self,
        product_type: str,
        export_volume_tons: float,
        direct_emissions_tco2: float,
        indirect_emissions_tco2: float = 0.0,
        cbam_carbon_price_eur_per_ton: float = 75.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.esg_engine import EsgEngine

            engine = EsgEngine()
            res = engine.evaluate_cbam_liability(
                product_type=product_type,
                export_volume_tons=float(export_volume_tons),
                direct_emissions_tco2=float(direct_emissions_tco2),
                indirect_emissions_tco2=float(indirect_emissions_tco2),
                cbam_carbon_price_eur_per_ton=float(cbam_carbon_price_eur_per_ton),
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"ESG CBAM liability error: {exc}"}, indent=2)

    def _handle_esg_audit(
        self,
        enterprise_name: str,
        has_iso_14001: bool = True,
        renewable_energy_ratio_pct: float = 20.0,
        has_waste_treatment_license: bool = True,
        full_social_insurance_compliance: bool = True,
        workplace_accident_rate: float = 0.0,
        female_leadership_ratio_pct: float = 30.0,
        independent_board_members_ratio_pct: float = 33.3,
        has_anti_corruption_policy: bool = True,
        has_audited_financial_report: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.esg_engine import EsgEngine

            engine = EsgEngine()
            res = engine.audit_esg_score(
                enterprise_name=enterprise_name,
                has_iso_14001=bool(has_iso_14001),
                renewable_energy_ratio_pct=float(renewable_energy_ratio_pct),
                has_waste_treatment_license=bool(has_waste_treatment_license),
                full_social_insurance_compliance=bool(full_social_insurance_compliance),
                workplace_accident_rate=float(workplace_accident_rate),
                female_leadership_ratio_pct=float(female_leadership_ratio_pct),
                independent_board_members_ratio_pct=float(independent_board_members_ratio_pct),
                has_anti_corruption_policy=bool(has_anti_corruption_policy),
                has_audited_financial_report=bool(has_audited_financial_report),
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"ESG audit error: {exc}"}, indent=2)

    def _handle_esg_carbon_trade(
        self,
        project_name: str,
        credit_type: str,
        quantity_tco2e: float,
        unit_price_usd: float,
        action: str = "BUY",
        counterparty: str = "Sàn giao dịch Carbon Quốc gia",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.esg_engine import EsgEngine

            engine = EsgEngine()
            res = engine.trade_carbon_credits(
                project_name=project_name,
                credit_type=credit_type,
                quantity_tco2e=float(quantity_tco2e),
                unit_price_usd=float(unit_price_usd),
                action=action,
                counterparty=counterparty,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"ESG carbon trade error: {exc}"}, indent=2)

    def _handle_esg_list(
        self,
        limit: int = 20,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.esg_engine import EsgEngine

            engine = EsgEngine()
            invs = engine.list_inventories(limit=limit)
            txs = engine.list_transactions(limit=limit)
            return json.dumps({"ok": True, "ghg_inventories": invs, "carbon_transactions": txs}, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"ESG list error: {exc}"}, indent=2)

    def _handle_esg_status(self, **kwargs: Any) -> str:
        try:
            from src.core.esg_engine import EsgEngine

            engine = EsgEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"ESG status error: {exc}"}, indent=2)

    _handle_mekong_esg_ghg = _handle_esg_ghg
    _handle_mekong_esg_cbam = _handle_esg_cbam
    _handle_mekong_esg_audit = _handle_esg_audit
    _handle_mekong_esg_carbon_trade = _handle_esg_carbon_trade
    _handle_mekong_esg_list = _handle_esg_list
    _handle_mekong_esg_status = _handle_esg_status

    def _handle_supplychain_plot(
        self,
        farmer_name: str,
        province: str,
        commodity: str,
        latitude: float,
        longitude: float,
        area_hectares: float,
        district: str = "Tây Nguyên",
        deforestation_free_post_2020: bool = True,
        legal_land_cert: str = "Sổ đỏ nông nghiệp / Giấy chứng nhận QSDĐ",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.supplychain_engine import SupplyChainEngine

            engine = SupplyChainEngine()
            res = engine.register_plot(
                farmer_name=farmer_name,
                province=province,
                commodity=commodity,
                latitude=float(latitude),
                longitude=float(longitude),
                area_hectares=float(area_hectares),
                district=district,
                deforestation_free_post_2020=bool(deforestation_free_post_2020),
                legal_land_cert=legal_land_cert,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Supply chain plot registration error: {exc}"}, indent=2)

    def _handle_supplychain_batch(
        self,
        batch_code: str,
        commodity: str,
        quantity_kg: float,
        processor_name: str,
        plot_ids: Optional[list[str]] = None,
        certifications: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.supplychain_engine import SupplyChainEngine

            engine = SupplyChainEngine()
            res = engine.create_batch(
                batch_code=batch_code,
                commodity=commodity,
                quantity_kg=float(quantity_kg),
                processor_name=processor_name,
                plot_ids=plot_ids,
                certifications=certifications,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Supply chain batch creation error: {exc}"}, indent=2)

    def _handle_supplychain_event(
        self,
        batch_code: str,
        event_type: str,
        location: str,
        actor_name: str,
        notes: str = "",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.supplychain_engine import SupplyChainEngine

            engine = SupplyChainEngine()
            res = engine.record_custody_event(
                batch_code=batch_code,
                event_type=event_type,
                location=location,
                actor_name=actor_name,
                notes=notes,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Supply chain custody event error: {exc}"}, indent=2)

    def _handle_supplychain_eudr(
        self,
        batch_code: str,
        exporter_name: str,
        importer_name: str,
        destination_country: str = "Germany",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.supplychain_engine import SupplyChainEngine

            engine = SupplyChainEngine()
            res = engine.generate_eudr_statement(
                batch_code=batch_code,
                exporter_name=exporter_name,
                importer_name=importer_name,
                destination_country=destination_country,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Supply chain EUDR statement error: {exc}"}, indent=2)

    def _handle_supplychain_trace(
        self,
        batch_code: str,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.supplychain_engine import SupplyChainEngine

            engine = SupplyChainEngine()
            res = engine.get_batch_trace(batch_code=batch_code)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Supply chain trace error: {exc}"}, indent=2)

    def _handle_supplychain_status(self, **kwargs: Any) -> str:
        try:
            from src.core.supplychain_engine import SupplyChainEngine

            engine = SupplyChainEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Supply chain status error: {exc}"}, indent=2)

    _handle_mekong_supplychain_plot = _handle_supplychain_plot
    _handle_mekong_supplychain_batch = _handle_supplychain_batch
    _handle_mekong_supplychain_event = _handle_supplychain_event
    _handle_mekong_supplychain_eudr = _handle_supplychain_eudr
    _handle_mekong_supplychain_trace = _handle_supplychain_trace
    _handle_mekong_supplychain_status = _handle_supplychain_status

    def _handle_labor_permit(
        self,
        worker_name: str,
        nationality: str,
        position: str,
        job_title: str,
        degree: str = "BACHELOR",
        exp: float = 3.0,
        capital: float = 0.0,
        wto: bool = False,
        married_vn: bool = False,
        passport: str = "PASS-DEFAULT",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.evaluate_work_permit_eligibility(
                worker_name=worker_name,
                nationality=nationality,
                position_category=position,
                job_title=job_title,
                education_degree=degree,
                experience_years=exp,
                capital_contribution_vnd=capital,
                is_wto_internal_transfer=wto,
                married_to_vietnamese=married_vn,
                passport_number=passport,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor permit error: {exc}"}, indent=2)

    def _handle_labor_overtime(
        self,
        hourly_rate: float,
        weekday_ot: float = 0.0,
        weekend_ot: float = 0.0,
        holiday_ot: float = 0.0,
        night_regular: float = 0.0,
        night_ot: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.calculate_overtime_pay(
                hourly_rate_vnd=hourly_rate,
                normal_day_ot_hours=weekday_ot,
                weekend_ot_hours=weekend_ot,
                holiday_ot_hours=holiday_ot,
                night_shift_regular_hours=night_regular,
                night_shift_ot_hours=night_ot,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor overtime error: {exc}"}, indent=2)

    def _handle_labor_caps(
        self,
        employee_id: str,
        employee_name: str,
        monthly_ot_hours: float,
        yearly_cumulative_hours: float,
        industry: str = "GENERAL",
        exceptional: bool = False,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.validate_overtime_caps(
                monthly_overtime_hours=monthly_ot_hours,
                yearly_cumulative_hours=yearly_cumulative_hours,
                is_extended_industry=exceptional,
            )
            res["employee_id"] = employee_id
            res["employee_name"] = employee_name
            res["industry"] = industry
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor caps error: {exc}"}, indent=2)

    def _handle_labor_severance(
        self,
        employee_name: str,
        average_salary: float,
        total_years: float,
        bhtn_years: float = 0.0,
        allowance_type: str = "SEVERANCE",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.calculate_termination_allowance(
                average_salary_vnd=average_salary,
                total_working_months=round(total_years * 12),
                bhtn_working_months=round(bhtn_years * 12),
                termination_type=allowance_type,
            )
            res["employee_name"] = employee_name
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor severance error: {exc}"}, indent=2)

    def _handle_labor_regulations(
        self,
        enterprise_name: str,
        total_employees: int,
        has_written_regulations: bool = True,
        is_registered: bool = True,
        dialogue: bool = True,
        safety_council: bool = True,
        docket: str = "NQLD-2026-DOLAB",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.audit_internal_regulations(
                enterprise_name=enterprise_name,
                total_employees=total_employees,
                has_written_regulations=has_written_regulations,
                is_registered_with_dolab=is_registered,
                has_dialogue_mechanism=dialogue,
                has_safety_council=safety_council,
                dolab_filing_number=docket,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor regulations error: {exc}"}, indent=2)

    def _handle_labor_list(
        self,
        category: str = "ALL",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.list_workers(position=category, limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor list error: {exc}"}, indent=2)

    def _handle_labor_status(self, **kwargs: Any) -> str:
        try:
            from src.core.labor_engine import LaborEngine

            engine = LaborEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Labor status error: {exc}"}, indent=2)

    _handle_mekong_labor_permit = _handle_labor_permit
    _handle_mekong_labor_overtime = _handle_labor_overtime
    _handle_mekong_labor_caps = _handle_labor_caps
    _handle_mekong_labor_severance = _handle_labor_severance
    _handle_mekong_labor_regulations = _handle_labor_regulations
    _handle_mekong_labor_list = _handle_labor_list
    _handle_mekong_labor_status = _handle_labor_status

    def _handle_maritime_vessel(
        self,
        name: str,
        imo: str,
        flag: str,
        dwt: float,
        grt: float,
        loa: float,
        draft: float,
        port_code: str,
        terminal: str,
        eta: str,
        etd: str,
        call_sign: str = "3XYZ",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.maritime_engine import MaritimeEngine

            engine = MaritimeEngine()
            res = engine.register_vessel_call(
                vessel_name=name,
                imo_number=imo,
                flag_state=flag,
                dwt=dwt,
                grt=grt,
                loa_meters=loa,
                draft_meters=draft,
                port_code=port_code,
                terminal_name=terminal,
                eta=eta,
                etd=etd,
                call_sign=call_sign,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Maritime vessel error: {exc}"}, indent=2)

    def _handle_maritime_container(
        self,
        container_no: str,
        container_type: str,
        gross_weight: float,
        seal: str,
        booking_or_bl: str,
        slot: str = "YARD-B01-R03-T2",
        tare: float = 2300.0,
        reefer: bool = False,
        dg: bool = False,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.maritime_engine import MaritimeEngine

            engine = MaritimeEngine()
            res = engine.register_container(
                container_no=container_no,
                container_type=container_type,
                gross_weight_kg=gross_weight,
                seal_number=seal,
                booking_or_bl=booking_or_bl,
                yard_slot=slot,
                tare_weight_kg=tare,
                is_reefer=reefer,
                is_dangerous=dg,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Maritime container error: {exc}"}, indent=2)

    def _handle_maritime_tariff(
        self,
        vessel_call: str,
        group: str,
        grt: float,
        berth_hours: float,
        distance: float = 18.0,
        f20: int = 0,
        f40: int = 0,
        e20: int = 0,
        e40: int = 0,
        reefer_hrs: float = 0.0,
        reefer_cnt: int = 0,
        terminal: str = "Tân Cảng Cát Lái",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.maritime_engine import MaritimeEngine

            engine = MaritimeEngine()
            res = engine.calculate_port_tariffs(
                vessel_call_id=vessel_call,
                port_group=group,
                grt=grt,
                berth_hours=berth_hours,
                pilotage_distance_nm=distance,
                full_20ft_count=f20,
                full_40ft_count=f40,
                empty_20ft_count=e20,
                empty_40ft_count=e40,
                reefer_power_hours=reefer_hrs,
                reefer_count=reefer_cnt,
                terminal_name=terminal,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Maritime tariff error: {exc}"}, indent=2)

    def _handle_maritime_manifest(
        self,
        vessel_call: str,
        bl: str,
        shipper: str,
        consignee: str,
        cargo: str,
        containers: int,
        gross_kg: float,
        decl_no: typing.Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.maritime_engine import MaritimeEngine

            engine = MaritimeEngine()
            res = engine.declare_customs_manifest(
                vessel_call_id=vessel_call,
                bill_of_lading=bl,
                shipper_name=shipper,
                consignee_name=consignee,
                cargo_description=cargo,
                container_count=containers,
                total_gross_kg=gross_kg,
                declaration_no=decl_no,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Maritime manifest error: {exc}"}, indent=2)

    def _handle_maritime_list(
        self,
        item_type: str = "vessels",
        yard: str = "ALL",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.maritime_engine import MaritimeEngine

            engine = MaritimeEngine()
            clean_type = item_type.lower().strip()
            if clean_type in ("containers", "container"):
                res = engine.list_containers(yard=yard, limit=limit)
            else:
                res = engine.list_vessel_calls(limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Maritime list error: {exc}"}, indent=2)

    def _handle_maritime_status(self, **kwargs: Any) -> str:
        try:
            from src.core.maritime_engine import MaritimeEngine

            engine = MaritimeEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Maritime status error: {exc}"}, indent=2)

    _handle_mekong_maritime_vessel = _handle_maritime_vessel
    _handle_mekong_maritime_container = _handle_maritime_container
    _handle_mekong_maritime_tariff = _handle_maritime_tariff
    _handle_mekong_maritime_manifest = _handle_maritime_manifest
    _handle_mekong_maritime_list = _handle_maritime_list
    _handle_mekong_maritime_status = _handle_maritime_status

    def _handle_energy_solar(
        self,
        project_id: str,
        capacity_kwp: float,
        location: str = "Binh Thuan",
        self_consumption_pct: float = 80.0,
        grid_connection: str = "connected",
        battery_storage_kwh: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.energy_engine import EnergyEngine

            engine = EnergyEngine()
            res = engine.evaluate_rooftop_solar(
                project_id=project_id,
                capacity_kwp=capacity_kwp,
                location=location,
                self_consumption_pct=self_consumption_pct,
                grid_connection=grid_connection,
                battery_storage_kwh=battery_storage_kwh,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Energy solar error: {exc}"}, indent=2)

    def _handle_energy_dppa(
        self,
        contract_id: str,
        buyer_id: str,
        seller_id: str,
        mechanism: str = "direct",
        contract_kwh_month: float = 500000.0,
        strike_price_vnd_kwh: float = 1800.0,
        spot_price_vnd_kwh: float = 1650.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.energy_engine import EnergyEngine

            engine = EnergyEngine()
            res = engine.evaluate_dppa_contract(
                contract_id=contract_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                mechanism=mechanism,
                contract_kwh_month=contract_kwh_month,
                strike_price_vnd_kwh=strike_price_vnd_kwh,
                spot_price_vnd_kwh=spot_price_vnd_kwh,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Energy DPPA error: {exc}"}, indent=2)

    def _handle_energy_ev(
        self,
        session_id: str,
        station_id: str,
        charger_type: str = "DC_120kW",
        energy_kwh: float = 45.0,
        tou_period: str = "normal",
        ev_model: str = "VF8",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.energy_engine import EnergyEngine

            engine = EnergyEngine()
            res = engine.simulate_ev_charging_session(
                session_id=session_id,
                station_id=station_id,
                charger_type=charger_type,
                energy_kwh=energy_kwh,
                tou_period=tou_period,
                ev_model=ev_model,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Energy EV error: {exc}"}, indent=2)

    def _handle_energy_list(
        self,
        item_type: str = "solar",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.energy_engine import EnergyEngine

            engine = EnergyEngine()
            if item_type.lower() in ("dppa", "contracts"):
                res = engine.list_dppa_contracts(limit=limit)
            elif item_type.lower() in ("ev", "sessions", "charging"):
                res = engine.list_ev_sessions(limit=limit)
            else:
                res = engine.list_solar_projects(limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Energy list error: {exc}"}, indent=2)

    def _handle_energy_status(self, **kwargs: Any) -> str:
        try:
            from src.core.energy_engine import EnergyEngine

            engine = EnergyEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Energy status error: {exc}"}, indent=2)

    _handle_mekong_energy_solar = _handle_energy_solar
    _handle_mekong_energy_dppa = _handle_energy_dppa
    _handle_mekong_energy_ev = _handle_energy_ev
    _handle_mekong_energy_list = _handle_energy_list
    _handle_mekong_energy_status = _handle_energy_status

    def _handle_privacy_audit(
        self,
        enterprise_name: str,
        controller_type: str = "CONTROLLER_AND_PROCESSOR",
        has_sensitive_data: bool = False,
        has_dpo: bool = False,
        has_cross_border: bool = False,
        has_dpia_dossier: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            res = engine.audit_enterprise_compliance(
                enterprise_name=enterprise_name,
                controller_type=controller_type,
                has_sensitive_data=has_sensitive_data,
                has_dpo=has_dpo,
                has_cross_border=has_cross_border,
                has_dpia_dossier=has_dpia_dossier,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy audit error: {exc}"}, indent=2)

    def _handle_privacy_dpia(
        self,
        activity_name: str,
        processing_purpose: str,
        data_categories: list[str],
        legal_basis: str = "CONSENT",
        security_measures: str = "AES-256 Encryption, RBAC, TLS 1.3",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            res = engine.create_dpia_assessment(
                activity_name=activity_name,
                processing_purpose=processing_purpose,
                data_categories=data_categories,
                legal_basis=legal_basis,
                security_measures=security_measures,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy DPIA error: {exc}"}, indent=2)

    def _handle_privacy_transfer(
        self,
        transfer_name: str,
        recipient_entity: str,
        destination_country: str,
        data_types: list[str],
        record_count: int = 1000,
        has_scc: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            res = engine.evaluate_cross_border_transfer(
                transfer_name=transfer_name,
                recipient_entity=recipient_entity,
                destination_country=destination_country,
                data_types=data_types,
                record_count=record_count,
                has_scc=has_scc,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy transfer error: {exc}"}, indent=2)

    def _handle_privacy_breach(
        self,
        incident_name: str,
        severity: str,
        affected_count: int,
        breach_type: str,
        hours_elapsed: float = 2.0,
        mitigation_plan: str = "Revoked compromised tokens, enabled network isolation, activated incident team",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            res = engine.report_data_breach(
                incident_name=incident_name,
                severity=severity,
                affected_count=affected_count,
                breach_type=breach_type,
                hours_elapsed=hours_elapsed,
                mitigation_plan=mitigation_plan,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy breach error: {exc}"}, indent=2)

    def _handle_privacy_dsar(
        self,
        request_type: str,
        subject_id: str,
        details: str = "Request under Article 9 PDPD",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            res = engine.handle_dsar_request(
                request_type=request_type,
                subject_id=subject_id,
                details=details,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy DSAR error: {exc}"}, indent=2)

    def _handle_privacy_list(
        self,
        item_type: str = "dpia",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            clean_type = item_type.lower().strip()
            if clean_type in ("transfer", "transfers", "cross_border"):
                res = engine.list_cross_border_transfers(limit=limit)
            elif clean_type in ("breach", "breaches", "incident", "incidents"):
                res = engine.list_breach_incidents(limit=limit)
            elif clean_type in ("dsar", "requests"):
                res = engine.list_dsar_requests(limit=limit)
            else:
                res = engine.list_dpia_assessments(limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy list error: {exc}"}, indent=2)

    def _handle_privacy_status(self, **kwargs: Any) -> str:
        try:
            from src.core.privacy_engine import PrivacyEngine

            engine = PrivacyEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Privacy status error: {exc}"}, indent=2)

    _handle_mekong_privacy_audit = _handle_privacy_audit
    _handle_mekong_privacy_dpia = _handle_privacy_dpia
    _handle_mekong_privacy_transfer = _handle_privacy_transfer
    _handle_mekong_privacy_breach = _handle_privacy_breach
    _handle_mekong_privacy_dsar = _handle_privacy_dsar
    _handle_mekong_privacy_list = _handle_privacy_list
    _handle_mekong_privacy_status = _handle_privacy_status

    # Aviation Handlers
    def _handle_aviation_flight(
        self,
        flight_no: str,
        aircraft_type: str,
        origin_airport: str,
        dest_airport: str,
        mtow_tons: float = 90.0,
        parking_hours: float = 2.0,
        is_international: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.aviation_engine import AviationEngine

            engine = AviationEngine()
            res = engine.register_flight_schedule(
                flight_no=flight_no,
                aircraft_type=aircraft_type,
                origin_airport=origin_airport,
                dest_airport=dest_airport,
                mtow_tons=mtow_tons,
                parking_hours=parking_hours,
                is_international=is_international,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Aviation flight error: {exc}"}, indent=2)

    def _handle_aviation_cargo(
        self,
        mawb_no: str,
        origin_airport: str,
        dest_airport: str,
        piece_count: int,
        gross_weight_kg: float,
        volume_cbm: float,
        cargo_type: str = "GENERAL",
        temperature_regime: str = "AMBIENT",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.aviation_engine import AviationEngine

            engine = AviationEngine()
            res = engine.calculate_air_cargo_chargeable_weight(
                mawb_no=mawb_no,
                origin_airport=origin_airport,
                dest_airport=dest_airport,
                piece_count=piece_count,
                gross_weight_kg=gross_weight_kg,
                volume_cbm=volume_cbm,
                cargo_type=cargo_type,
                temperature_regime=temperature_regime,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Aviation cargo error: {exc}"}, indent=2)

    def _handle_aviation_tariff(
        self,
        flight_no: str,
        airport_code: str,
        mtow_tons: float,
        parking_hours: float = 2.0,
        cargo_tons: float = 10.0,
        is_international: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.aviation_engine import AviationEngine

            engine = AviationEngine()
            res = engine.calculate_airport_tariffs(
                flight_no=flight_no,
                airport_code=airport_code,
                mtow_tons=mtow_tons,
                parking_hours=parking_hours,
                cargo_tons=cargo_tons,
                is_international=is_international,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Aviation tariff error: {exc}"}, indent=2)

    def _handle_aviation_dg(
        self,
        un_number: str,
        proper_shipping_name: str,
        hazard_class: str,
        packing_group: str = "II",
        quantity_kg: float = 10.0,
        aircraft_type: str = "PAX_AND_CARGO",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.aviation_engine import AviationEngine

            engine = AviationEngine()
            res = engine.evaluate_dangerous_goods_declaration(
                un_number=un_number,
                proper_shipping_name=proper_shipping_name,
                hazard_class=hazard_class,
                packing_group=packing_group,
                quantity_kg=quantity_kg,
                aircraft_type=aircraft_type,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Aviation DG error: {exc}"}, indent=2)

    def _handle_aviation_list(
        self,
        item_type: str = "flights",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.aviation_engine import AviationEngine

            engine = AviationEngine()
            clean_type = item_type.lower().strip()
            if clean_type in ("cargo", "shipment", "shipments", "awb"):
                res = engine.list_air_cargo_shipments(limit=limit)
            elif clean_type in ("dg", "dangerous_goods", "hazmat", "declarations"):
                res = engine.list_dangerous_goods(limit=limit)
            else:
                res = engine.list_flight_schedules(limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Aviation list error: {exc}"}, indent=2)

    def _handle_aviation_status(self, **kwargs: Any) -> str:
        try:
            from src.core.aviation_engine import AviationEngine

            engine = AviationEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Aviation status error: {exc}"}, indent=2)

    _handle_mekong_aviation_flight = _handle_aviation_flight
    _handle_mekong_aviation_cargo = _handle_aviation_cargo
    _handle_mekong_aviation_tariff = _handle_aviation_tariff
    _handle_mekong_aviation_dg = _handle_aviation_dg
    _handle_mekong_aviation_list = _handle_aviation_list
    _handle_mekong_aviation_status = _handle_aviation_status

    # E-Commerce Handlers
    def _handle_ecom_fct(
        self,
        foreign_supplier_name: str,
        supplier_etax_code: str,
        service_category: str,
        revenue_usd: float = 0.0,
        revenue_vnd: float = 0.0,
        quarter: str = "Q1-2026",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ecommerce_engine import EcommerceEngine

            engine = EcommerceEngine()
            res = engine.calculate_foreign_contractor_tax(
                foreign_supplier_name=foreign_supplier_name,
                supplier_etax_code=supplier_etax_code,
                service_category=service_category,
                revenue_usd=revenue_usd,
                revenue_vnd=revenue_vnd,
                quarter=quarter,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"E-Commerce FCT error: {exc}"}, indent=2)

    def _handle_ecom_audit(
        self,
        platform_name: str,
        domain_url: str,
        platform_type: str = "MARKETPLACE",
        enterprise_tax_id: str = "0109999999",
        has_operating_regulations: bool = True,
        has_dispute_mechanism: bool = True,
        has_seller_kyc: bool = True,
        has_data_retention_3yr: bool = True,
        has_tax_reporting_system: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ecommerce_engine import EcommerceEngine

            engine = EcommerceEngine()
            res = engine.audit_platform_compliance(
                platform_name=platform_name,
                domain_url=domain_url,
                platform_type=platform_type,
                enterprise_tax_id=enterprise_tax_id,
                has_operating_regulations=has_operating_regulations,
                has_dispute_mechanism=has_dispute_mechanism,
                has_seller_kyc=has_seller_kyc,
                has_data_retention_3yr=has_data_retention_3yr,
                has_tax_reporting_system=has_tax_reporting_system,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"E-Commerce audit error: {exc}"}, indent=2)

    def _handle_ecom_order(
        self,
        order_code: str,
        platform_id: str,
        seller_id: str,
        buyer_id: str,
        gmv_gross_vnd: float,
        platform_commission_pct: float = 6.0,
        payment_fee_pct: float = 2.5,
        shop_voucher_vnd: float = 0.0,
        platform_voucher_vnd: float = 0.0,
        shipping_fee_vnd: float = 30000.0,
        vat_rate_pct: int = 10,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ecommerce_engine import EcommerceEngine

            engine = EcommerceEngine()
            res = engine.process_marketplace_order_settlement(
                order_code=order_code,
                platform_id=platform_id,
                seller_id=seller_id,
                buyer_id=buyer_id,
                gmv_gross_vnd=gmv_gross_vnd,
                platform_commission_pct=platform_commission_pct,
                payment_fee_pct=payment_fee_pct,
                shop_voucher_vnd=shop_voucher_vnd,
                platform_voucher_vnd=platform_voucher_vnd,
                shipping_fee_vnd=shipping_fee_vnd,
                vat_rate_pct=vat_rate_pct,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"E-Commerce order settlement error: {exc}"}, indent=2)

    def _handle_ecom_parcel(
        self,
        tracking_no: str,
        shipper_country: str,
        consignee_name: str,
        item_description: str,
        customs_value_usd: float = 0.0,
        customs_value_vnd: float = 0.0,
        import_duty_pct: float = 10.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ecommerce_engine import EcommerceEngine

            engine = EcommerceEngine()
            res = engine.evaluate_cross_border_parcel(
                tracking_no=tracking_no,
                shipper_country=shipper_country,
                consignee_name=consignee_name,
                item_description=item_description,
                customs_value_usd=customs_value_usd,
                customs_value_vnd=customs_value_vnd,
                import_duty_pct=import_duty_pct,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"E-Commerce parcel error: {exc}"}, indent=2)

    def _handle_ecom_list(
        self,
        item_type: str = "platforms",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.ecommerce_engine import EcommerceEngine

            engine = EcommerceEngine()
            clean_type = item_type.lower().strip()
            if clean_type in ("fct", "tax", "declarations"):
                res = engine.list_fct_declarations(limit=limit)
            elif clean_type in ("order", "orders", "settlements"):
                res = engine.list_marketplace_orders(limit=limit)
            elif clean_type in ("parcel", "parcels", "express"):
                res = engine.list_cross_border_parcels(limit=limit)
            else:
                res = engine.list_platform_registrations(limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"E-Commerce list error: {exc}"}, indent=2)

    def _handle_ecom_status(self, **kwargs: Any) -> str:
        try:
            from src.core.ecommerce_engine import EcommerceEngine

            engine = EcommerceEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"E-Commerce status error: {exc}"}, indent=2)

    _handle_mekong_ecom_fct = _handle_ecom_fct
    _handle_mekong_ecom_audit = _handle_ecom_audit
    _handle_mekong_ecom_order = _handle_ecom_order
    _handle_mekong_ecom_parcel = _handle_ecom_parcel
    _handle_mekong_ecom_list = _handle_ecom_list
    _handle_mekong_ecom_status = _handle_ecom_status

    def _handle_telecom_spectrum(
        self,
        band_code: str,
        license_years: int = 15,
        deposit_pct: float = 10.0,
        custom_reserve_price_vnd: float = 0.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.telecom_engine import TelecomEngine

            engine = TelecomEngine()
            res = engine.calculate_spectrum_auction_valuation(
                band_code=band_code,
                license_years=license_years,
                deposit_pct=deposit_pct,
                custom_reserve_price_vnd=custom_reserve_price_vnd,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telecom spectrum error: {exc}"}, indent=2)

    def _handle_telecom_ott(
        self,
        service_name: str,
        provider_name: str,
        service_category: str = "OTT_MESSAGING_VOICE",
        registered_users: int = 1000000,
        has_kyc_verification: bool = True,
        has_encryption_e2ee: bool = True,
        has_local_data_storage: bool = True,
        has_vnta_notification: bool = True,
        has_consumer_dispute_system: bool = True,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.telecom_engine import TelecomEngine

            engine = TelecomEngine()
            res = engine.audit_ott_service_compliance(
                service_name=service_name,
                provider_name=provider_name,
                service_category=service_category,
                registered_users=registered_users,
                has_kyc_verification=has_kyc_verification,
                has_encryption_e2ee=has_encryption_e2ee,
                has_local_data_storage=has_local_data_storage,
                has_vnta_notification=has_vnta_notification,
                has_consumer_dispute_system=has_consumer_dispute_system,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telecom OTT error: {exc}"}, indent=2)

    def _handle_telecom_bts(
        self,
        station_id: str,
        location: str,
        antenna_height_m: float = 30.0,
        transmit_power_watts: float = 80.0,
        frequency_mhz: float = 2600.0,
        antenna_gain_dbi: float = 18.0,
        distance_residential_m: float = 25.0,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.telecom_engine import TelecomEngine

            engine = TelecomEngine()
            res = engine.evaluate_bts_emf_safety(
                station_id=station_id,
                location=location,
                antenna_height_m=antenna_height_m,
                transmit_power_watts=transmit_power_watts,
                frequency_mhz=frequency_mhz,
                antenna_gain_dbi=antenna_gain_dbi,
                distance_residential_m=distance_residential_m,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telecom BTS error: {exc}"}, indent=2)

    def _handle_telecom_number(
        self,
        number_prefix: str,
        assigned_operator: str,
        block_size: int = 10000,
        service_purpose: str = "MOBILE_SUBSCRIBER",
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.telecom_engine import TelecomEngine

            engine = TelecomEngine()
            res = engine.allocate_numbering_resource(
                number_prefix=number_prefix,
                assigned_operator=assigned_operator,
                block_size=block_size,
                service_purpose=service_purpose,
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telecom number error: {exc}"}, indent=2)

    def _handle_telecom_list(
        self,
        item_type: str = "spectrum",
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        try:
            from src.core.telecom_engine import TelecomEngine

            engine = TelecomEngine()
            clean_type = item_type.lower().strip()
            if clean_type in ("ott", "audits", "services"):
                res = engine.list_ott_audits(limit=limit)
            elif clean_type in ("bts", "stations", "emf"):
                res = engine.list_bts_evaluations(limit=limit)
            elif clean_type in ("number", "numbers", "resources"):
                res = engine.list_numbering_resources(limit=limit)
            else:
                res = engine.list_spectrum_auctions(limit=limit)
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telecom list error: {exc}"}, indent=2)

    def _handle_telecom_status(self, **kwargs: Any) -> str:
        try:
            from src.core.telecom_engine import TelecomEngine

            engine = TelecomEngine()
            res = engine.get_status()
            return json.dumps(res, indent=2, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": f"Telecom status error: {exc}"}, indent=2)

    _handle_mekong_telecom_spectrum = _handle_telecom_spectrum
    _handle_mekong_telecom_ott = _handle_telecom_ott
    _handle_mekong_telecom_bts = _handle_telecom_bts
    _handle_mekong_telecom_number = _handle_telecom_number
    _handle_mekong_telecom_list = _handle_telecom_list
    _handle_mekong_telecom_status = _handle_telecom_status








# ===================================================================
# Module-level helpers
# ===================================================================


def create_app(name: str = "mekong-ai-os") -> Any:
    """Shorthand to create a pre-configured FastMCP app.

    Returns:
        FastMCP instance with all 25 tools registered.

    """
    server = MekongMcpServer(name=name)
    return server.create_app()


# ===================================================================
# CLI entry point
# ===================================================================


def main() -> None:
    """Standalone entry point for the MCP server.

    Parses arguments and runs the server with the chosen transport.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Mekong AI OS — MCP Server",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)",
    )
    parser.add_argument(
        "--name",
        default="mekong-ai-os",
        help="MCP server name (default: mekong-ai-os)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "WARNING").upper(),
        format="%(levelname)s | %(name)s | %(message)s",
    )

    server = MekongMcpServer(name=args.name)

    if args.transport == "sse":
        os.environ["MCP_SSE_PORT"] = str(args.port)

    try:
        server.run(transport=args.transport)
    except RuntimeError as exc:
        logger.error("Failed to start MCP server: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
