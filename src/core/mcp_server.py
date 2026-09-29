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
