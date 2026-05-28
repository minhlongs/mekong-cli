"""Mekong CLI — MCP Server for AI OS capabilities.

Provides 24 MCP tools wrapping Mekong AI OS core services.
Designed to run as a standalone MCP server (stdio or SSE) or be imported.

Usage:
    python -m src.core.mcp_server                           # stdio mode
    python -m src.core.mcp_server --transport sse --port 8000  # SSE mode
"""

from __future__ import annotations

import json
import logging
import os
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
_HAS_MCU = False
_HAS_COST = False
_HAS_ROUTER = False

try:
    from src.core.memory_client import get_memory_provider

    _HAS_MEMORY = True
except ImportError:
    pass

try:
    from src.core.memory import MemoryStore

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

try:
    from src.core.mcu_gate import MCUGate

    _HAS_MCU = True
except ImportError:
    pass

try:
    from src.core.cost_estimator import estimate_cost

    _HAS_COST = True
except ImportError:
    pass

try:
    from src.core.hybrid_router import hybrid_route, MissionResult

    _HAS_ROUTER = True
except ImportError:
    pass


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


# ---------------------------------------------------------------------------
# Lazy singletons (initialised on first use)
# ---------------------------------------------------------------------------
_memory: Any = None
_memory_store: Any = None
_agent_registry: Any = None
_plugin_registry: Any = None
_mcu_gate: Any = None


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


def _get_mcu_gate() -> Any:
    """Get or create the MCU gate singleton."""
    global _mcu_gate
    if _mcu_gate is None and _HAS_MCU:
        _mcu_gate = MCUGate()
    return _mcu_gate


# ===================================================================
# MekongMcpServer
# ===================================================================


class MekongMcpServer:
    """MCP server exposing Mekong AI OS capabilities as tools.

    Wraps 24 tool handlers that proxy to Mekong core modules with
    graceful degradation when modules are unavailable.

    Usage:
        server = MekongMcpServer()
        app = server.create_app()
        app.run(transport="stdio")
    """

    def __init__(self, name: str = "mekong-ai-os") -> None:
        self.name = name
        self._app: Any = None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    def create_app(self) -> Any:
        """Create the FastMCP application with all 24 tools registered.

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

        @app.tool(description="Create a new task in Mekong")
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

        @app.tool(description="Start Mekong multi-agent research lab on a topic")
        def cc_lab_start(topic: str) -> str:
            return self._handle_lab_start(topic)

        @app.tool(description="Check Mekong research lab status")
        def cc_lab_status() -> str:
            return self._handle_lab_status()

        # ── Trading ───────────────────────────────────────────────────

        @app.tool(description="Analyze a trading symbol with multi-agent debate")
        def cc_trading_analyze(symbol: str) -> str:
            return self._handle_trading_analyze(symbol)

        @app.tool(description="Get current price for a trading symbol")
        def cc_trading_price(symbol: str) -> str:
            return self._handle_trading_price(symbol)

        # ── Monitor ───────────────────────────────────────────────────

        @app.tool(description="Run Mekong AI monitor on a topic or all subscriptions")
        def cc_monitor_run(topic: str = "") -> str:
            return self._handle_monitor_run(topic)

        @app.tool(description="Check Mekong monitor scheduler status")
        def cc_monitor_status() -> str:
            return self._handle_monitor_status()

        # ── Plan Mode ─────────────────────────────────────────────────

        @app.tool(description="Enter Mekong plan mode (write-protect code)")
        def cc_plan_start(description: str) -> str:
            return self._handle_plan_start(description)

        @app.tool(description="Exit Mekong plan mode")
        def cc_plan_done() -> str:
            return self._handle_plan_done()

        # ── SSJ (Developer Power Menu) ────────────────────────────────

        @app.tool(description="Open Mekong SSJ Developer Mode power menu")
        def cc_ssj() -> str:
            return self._handle_ssj()

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
        """List tasks — currently a stub pending task system integration."""
        # Mekong CLI does not yet have a unified task API in core.
        # This stub returns a helpful message.
        return _ok({
            "tasks": [],
            "note": (
                "Task management is available via the Mekong CLI shell "
                "(`mekong task ...`). MCP task support coming in v6.1."
            ),
        })

    def _handle_tasks_create(self, subject: str) -> str:
        return _ok({
            "created": False,
            "note": (
                "Task creation is available via `mekong task create ...` "
                "in the Mekong CLI shell. MCP task support coming in v6.1."
            ),
        })

    def _handle_tasks_done(self, task_id: str) -> str:
        return _err("Task management not yet exposed via MCP — use `mekong task done <id>` in CLI")

    def _handle_tasks_start(self, task_id: str) -> str:
        return _err("Task management not yet exposed via MCP — use `mekong task start <id>` in CLI")

    def _handle_tasks_delete(self, task_id: str) -> str:
        return _err("Task management not yet exposed via MCP — use `mekong task delete <id>` in CLI")

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
            from src.core.agent_dispatcher import load_agent_prompt, build_message_chain

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
                for child in sorted(sdir.iterdir()):
                    if child.is_dir():
                        skills.append({
                            "name": child.name,
                            "source": str(sdir),
                        })

        return _ok({"skills": skills, "count": len(skills)})

    # ── MCP System ────────────────────────────────────────────────────

    def _handle_mcp_list(self) -> str:
        """List this MCP server's own tools and any discovered MCP servers."""
        tools: list[dict[str, str]] = []
        if self._app is not None:
            try:
                for tool in self._app._tool_manager.list_tools():
                    tools.append({
                        "name": tool.name,
                        "description": tool.description or "",
                    })
            except Exception:
                pass

        return _ok({
            "mcp_servers": [{"name": self.name, "tools_count": len(tools)}],
            "tools": tools,
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
            from src.core.llm_client import get_client as get_llm_client

            client = get_llm_client()
            prompt = (
                f"You are a multi-persona brainstorming facilitator. "
                f"Generate diverse perspectives on the topic: '{topic}'. "
                f"Include viewpoints from a CTO, CMO, COO, and a domain expert. "
                f"Provide structured insights with pros and cons for each perspective."
            )
            response = client.complete(prompt, max_tokens=2000)
            text = response if isinstance(response, str) else getattr(response, "content", str(response))
            return _ok({"topic": topic, "brainstorm": text[:4000]})
        except ImportError:
            return _missing("llm_client (brainstorm)")
        except Exception as exc:
            logger.warning("Brainstorm failed: %s", exc)
            return _err(f"Brainstorm error: {exc}")

    # ── Research Lab ──────────────────────────────────────────────────

    def _handle_lab_start(self, topic: str) -> str:
        """Start multi-agent research lab — placeholder."""
        return _ok({
            "lab_started": False,
            "topic": topic,
            "note": (
                "Multi-agent research lab is available via "
                "the Mekong CLI orchestrator (`mekong lab start <topic>`). "
                "MCP lab support coming in v6.1."
            ),
        })

    def _handle_lab_status(self) -> str:
        """Check research lab status — placeholder."""
        return _ok({
            "status": "idle",
            "active_labs": [],
            "note": "Lab status available via `mekong lab status` in CLI",
        })

    # ── Trading ───────────────────────────────────────────────────────

    def _handle_trading_analyze(self, symbol: str) -> str:
        """Analyze a trading symbol — placeholder."""
        return _ok({
            "symbol": symbol,
            "note": (
                f"Trading analysis for '{symbol}' is available via "
                f"the Mekong trading module (`mekong trading analyze {symbol}`). "
                "MCP trading support coming in v6.1."
            ),
        })

    def _handle_trading_price(self, symbol: str) -> str:
        """Get current price for a trading symbol — placeholder."""
        return _ok({
            "symbol": symbol,
            "note": (
                f"Price lookup for '{symbol}' is available via "
                f"`mekong trading price {symbol}` in the CLI."
            ),
        })

    # ── Monitor ───────────────────────────────────────────────────────

    def _handle_monitor_run(self, topic: str = "") -> str:
        """Run AI monitor — placeholder."""
        return _ok({
            "monitor_started": False,
            "topic": topic or "all subscriptions",
            "note": (
                "AI monitor is available via `mekong monitor run` in the CLI. "
                "MCP monitor support coming in v6.1."
            ),
        })

    def _handle_monitor_status(self) -> str:
        """Check monitor scheduler status — placeholder."""
        return _ok({
            "status": "idle",
            "note": "Monitor status available via `mekong monitor status` in CLI",
        })

    # ── Plan Mode ─────────────────────────────────────────────────────

    def _handle_plan_start(self, description: str) -> str:
        """Enter plan mode — decomposes goal into tasks via RecipePlanner."""
        try:
            from src.core.planner import RecipePlanner, PlanningContext

            planner = RecipePlanner()
            context = PlanningContext(goal=description)
            tasks = planner.decompose_goal(description, context)
            return _ok({
                "plan_started": True,
                "description": description,
                "tasks": tasks,
                "task_count": len(tasks),
            })
        except ImportError:
            return _ok({
                "plan_started": True,
                "description": description,
                "note": (
                    "Plan mode entered (simulated). Full RecipePlanner "
                    "module is not installed."
                ),
            })
        except Exception as exc:
            logger.warning("Plan start failed: %s", exc)
            return _err(f"Plan start error: {exc}")

    def _handle_plan_done(self) -> str:
        """Exit plan mode."""
        return _ok({
            "plan_done": True,
            "note": "Plan mode exited.",
        })

    # ── SSJ ───────────────────────────────────────────────────────────

    def _handle_ssj(self) -> str:
        """SSJ Developer Mode power menu — informational."""
        return _ok({
            "ssj_menu": [
                {"key": "1", "label": "Run diagnostics"},
                {"key": "2", "label": "Toggle verbose logging"},
                {"key": "3", "label": "Reload config"},
                {"key": "4", "label": "System health check"},
                {"key": "5", "label": "Memory stats"},
                {"key": "6", "label": "Plugin status"},
            ],
            "note": (
                "SSJ Developer Mode is a power-user menu available "
                "in the Mekong CLI. Use `mekong ssj` for the full menu."
            ),
        })


# ===================================================================
# Module-level helpers
# ===================================================================


def create_app(name: str = "mekong-ai-os") -> Any:
    """Shorthand to create a pre-configured FastMCP app.

    Returns:
        FastMCP instance with all 24 tools registered.

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
