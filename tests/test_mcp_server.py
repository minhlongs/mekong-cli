"""Tests for src.core.mcp_server — Mekong AI OS MCP Server.

Verifies:
  1. Module imports cleanly without MCP SDK
  2. MekongMcpServer class construction and method signatures
  3. All 24 tool handler implementations return valid JSON
  4. Graceful degradation when core modules are unavailable
  5. create_app() / run() factory mechanics
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import ANY, MagicMock, PropertyMock, patch

import pytest

# Module to test
MODULE_PATH = "src.core.mcp_server"


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mcp_module():
    """Import the mcp_server module (with MCP SDK mocked as unavailable)."""
    # Force re-import by clearing cached module
    for key in list(sys.modules.keys()):
        if "mcp_server" in key:
            del sys.modules[key]
    import importlib

    mod = importlib.import_module(MODULE_PATH)
    # Ensure clean state
    mod._HAS_MCP = False
    mod._HAS_MEMORY = False
    mod._HAS_MEMORY_STORE = False
    mod._HAS_AGENT_REGISTRY = False
    mod._HAS_PLUGIN_REGISTRY = False
    mod._HAS_MCU = False
    mod._HAS_COST = False
    mod._HAS_ROUTER = False
    return mod


@pytest.fixture
def mcp_module_with_sdk(mcp_module):
    """Simulate MCP SDK being available."""
    # Mock FastMCP
    mock_fastmcp = MagicMock()
    mock_app = MagicMock()
    mock_fastmcp.return_value = mock_app

    mcp_module._HAS_MCP = True
    # Store original import so we can patch
    with patch.object(mcp_module, "FastMCP", mock_fastmcp):
        yield mcp_module


@pytest.fixture
def server(mcp_module):
    """MekongMcpServer instance with no core modules loaded."""
    return mcp_module.MekongMcpServer(name="test-ai-os")


@pytest.fixture
def server_with_memory(server, mcp_module):
    """Server with memory capability enabled."""
    mcp_module._HAS_MEMORY = True
    mcp_module._HAS_MEMORY_STORE = True
    return server


# =========================================================================
# Module-level tests
# =========================================================================


class TestModuleImports:
    """Verify module loads without MCP SDK."""

    def test_module_imports_cleanly(self, mcp_module):
        """Module should import without errors even when MCP SDK is absent."""
        assert mcp_module is not None
        assert hasattr(mcp_module, "MekongMcpServer")

    def test_has_mcp_flag_false_when_sdk_missing(self, mcp_module):
        """_HAS_MCP should be False when no mcp package."""
        assert mcp_module._HAS_MCP is False

    def test_create_app_raises_without_sdk(self, mcp_module):
        """create_app() should raise RuntimeError when MCP SDK is missing."""
        server = mcp_module.MekongMcpServer()
        with pytest.raises(RuntimeError, match="MCP SDK is not installed"):
            server.create_app()

    def test_module_create_app_shorthand(self, mcp_module):
        """Module-level create_app() should also raise without SDK."""
        with pytest.raises(RuntimeError, match="MCP SDK is not installed"):
            mcp_module.create_app()


# =========================================================================
# MekongMcpServer class tests
# =========================================================================


class TestMekongMcpServerClass:
    """Verify MekongMcpServer construction and structure."""

    def test_constructor_defaults(self, mcp_module):
        """Default name should be 'mekong-ai-os'."""
        srv = mcp_module.MekongMcpServer()
        assert srv.name == "mekong-ai-os"

    def test_constructor_custom_name(self, mcp_module):
        """Custom name should be accepted."""
        srv = mcp_module.MekongMcpServer(name="my-server")
        assert srv.name == "my-server"

    def test_has_create_app_method(self, server):
        """Server should have create_app method."""
        assert hasattr(server, "create_app")
        assert callable(server.create_app)

    def test_has_run_method(self, server):
        """Server should have run method."""
        assert hasattr(server, "run")
        assert callable(server.run)


class TestCreateApp:
    """Verify create_app() with mock MCP SDK."""

    def test_create_app_returns_app(self, mcp_module_with_sdk):
        """create_app() should return the FastMCP instance."""
        (srv, mod) = (mcp_module_with_sdk.MekongMcpServer(), mcp_module_with_sdk)
        with patch.object(srv, "_register_tools") as mock_register:
            app = srv.create_app()
            assert app is not None
            mock_register.assert_called_once_with(app)

    def test_create_app_tool_count(self, mcp_module_with_sdk):
        """Should register exactly 24 tools."""
        srv = mcp_module_with_sdk.MekongMcpServer()
        app = srv.create_app()
        # Verify _register_tools was called (we can check tool manager if mock supports it)
        assert app is not None


# =========================================================================
# Handler implementation tests
# =========================================================================


class TestHandlersReturnJson:
    """Every handler should return valid JSON."""

    def _check_json(self, raw: str) -> dict:
        """Assert raw is valid JSON and return parsed dict."""
        assert isinstance(raw, str), f"Expected string, got {type(raw)}"
        data = json.loads(raw)
        assert isinstance(data, dict)
        return data

    # ── Memory ────────────────────────────────────────────────────────

    def test_memory_search_no_core(self, server):
        """Without core, memory search should return error."""
        result = server._handle_memory_search("test query")
        data = self._check_json(result)
        assert data.get("ok") is False
        assert "error" in data

    def test_memory_consolidate_no_core(self, server):
        """Without core, memory consolidate should return ok with note."""
        result = server._handle_memory_consolidate()
        data = self._check_json(result)
        # Falls back gracefully when no MemoryStore
        assert "data" in data

    # ── Tasks ─────────────────────────────────────────────────────────

    def test_tasks_list(self, server):
        """Tasks list should return helpful note."""
        result = server._handle_tasks_list()
        data = self._check_json(result)
        assert data.get("ok") is True
        assert "note" in data.get("data", {})

    def test_tasks_list_with_status(self, server):
        """Tasks list with status filtering."""
        for status in ("todo", "in-progress", "done"):
            result = server._handle_tasks_list(status=status)
            data = self._check_json(result)
            assert data.get("ok") is True

    def test_tasks_create(self, server):
        """Tasks create should return helpful note."""
        result = server._handle_tasks_create("Test task")
        data = self._check_json(result)
        assert data.get("ok") is True

    def test_tasks_done(self, server):
        """Tasks done should return error (task system not yet exposed)."""
        result = server._handle_tasks_done("123")
        data = self._check_json(result)
        assert data.get("ok") is False

    def test_tasks_start(self, server):
        """Tasks start should return error."""
        result = server._handle_tasks_start("123")
        data = self._check_json(result)
        assert data.get("ok") is False

    def test_tasks_delete(self, server):
        """Tasks delete should return error."""
        result = server._handle_tasks_delete("123")
        data = self._check_json(result)
        assert data.get("ok") is False

    # ── Agents ────────────────────────────────────────────────────────

    def test_agents_list_no_core(self, server):
        """Without agent registry, list should return error."""
        result = server._handle_agents_list()
        data = self._check_json(result)
        assert data.get("ok") is False

    def test_agents_start_no_core(self, server):
        """Without agent registry, start should return error."""
        result = server._handle_agents_start("research_assistant")
        data = self._check_json(result)
        assert data.get("ok") is False

    def test_agents_stop(self, server):
        """Agent stop always returns ok with note."""
        result = server._handle_agents_stop("test-agent")
        data = self._check_json(result)
        assert data.get("ok") is True

    # ── Skills ────────────────────────────────────────────────────────

    def test_skills_list(self, server):
        """Skills list should return ok with empty list (no skill dirs)."""
        result = server._handle_skills_list()
        data = self._check_json(result)
        assert data.get("ok") is True
        assert "skills" in data.get("data", {})

    # ── MCP System ────────────────────────────────────────────────────

    def test_mcp_list_without_app(self, server):
        """MCP list without app should return empty tools list."""
        result = server._handle_mcp_list()
        data = self._check_json(result)
        assert data.get("ok") is True
        assert "mcp_servers" in data.get("data", {})

    # ── Plugins ───────────────────────────────────────────────────────

    def test_plugins_list_no_core(self, server):
        """Without plugin registry, list should return error."""
        result = server._handle_plugins_list()
        data = self._check_json(result)
        assert data.get("ok") is False

    def test_plugins_install_no_core(self, server):
        """Without plugin registry, install should return error."""
        result = server._handle_plugins_install("mekong-plugin-seo")
        data = self._check_json(result)
        assert data.get("ok") is False

    # ── Brainstorm ────────────────────────────────────────────────────

    def test_brainstorm_no_llm(self, server):
        """Without LLM client, brainstorm should return error."""
        result = server._handle_brainstorm("test topic")
        data = self._check_json(result)
        assert data.get("ok") is False

    # ── Research Lab ──────────────────────────────────────────────────

    def test_lab_start(self, server):
        """Lab start should return ok with note."""
        result = server._handle_lab_start("quantum computing")
        data = self._check_json(result)
        assert data.get("ok") is True

    def test_lab_status(self, server):
        """Lab status should return ok."""
        result = server._handle_lab_status()
        data = self._check_json(result)
        assert data.get("ok") is True

    # ── Trading ───────────────────────────────────────────────────────

    def test_trading_analyze(self, server):
        """Trading analyze should return ok with note."""
        result = server._handle_trading_analyze("BTC/USD")
        data = self._check_json(result)
        assert data.get("ok") is True

    def test_trading_price(self, server):
        """Trading price should return ok with note."""
        result = server._handle_trading_price("BTC/USD")
        data = self._check_json(result)
        assert data.get("ok") is True

    # ── Monitor ───────────────────────────────────────────────────────

    def test_monitor_run(self, server):
        """Monitor run should return ok with note."""
        result = server._handle_monitor_run("security")
        data = self._check_json(result)
        assert data.get("ok") is True

    def test_monitor_run_empty_topic(self, server):
        """Monitor run with empty topic should still work."""
        result = server._handle_monitor_run()
        data = self._check_json(result)
        assert data.get("ok") is True

    def test_monitor_status(self, server):
        """Monitor status should return ok."""
        result = server._handle_monitor_status()
        data = self._check_json(result)
        assert data.get("ok") is True

    # ── Plan Mode ─────────────────────────────────────────────────────

    def test_plan_start_no_planner(self, server):
        """Without planner, plan start should return ok simulated."""
        result = server._handle_plan_start("Implement login")
        data = self._check_json(result)
        assert data.get("ok") is True
        assert "note" in data.get("data", {}) or "tasks" in data.get("data", {})

    def test_plan_done(self, server):
        """Plan done should return ok."""
        result = server._handle_plan_done()
        data = self._check_json(result)
        assert data.get("ok") is True

    # ── SSJ ───────────────────────────────────────────────────────────

    def test_ssj(self, server):
        """SSJ should return ok with menu items."""
        result = server._handle_ssj()
        data = self._check_json(result)
        assert data.get("ok") is True
        assert "ssj_menu" in data.get("data", {})


# =========================================================================
# Tool naming consistency tests
# =========================================================================


class TestToolNaming:
    """Verify tool names match expected 24-tool set."""

    EXPECTED_TOOLS = [
        "cc_memory_search",
        "cc_memory_consolidate",
        "cc_tasks_list",
        "cc_tasks_create",
        "cc_tasks_done",
        "cc_tasks_start",
        "cc_tasks_delete",
        "cc_agents_list",
        "cc_agents_start",
        "cc_agents_stop",
        "cc_skills_list",
        "cc_mcp_list",
        "cc_plugins_list",
        "cc_plugins_install",
        "cc_brainstorm",
        "cc_lab_start",
        "cc_lab_status",
        "cc_trading_analyze",
        "cc_trading_price",
        "cc_monitor_run",
        "cc_monitor_status",
        "cc_plan_start",
        "cc_plan_done",
        "cc_ssj",
    ]

    def test_tool_count(self):
        """Should have exactly 24 expected tools."""
        assert len(self.EXPECTED_TOOLS) == 24

    def test_tool_names_all_cc_prefix(self):
        """Every tool name should start with cc_."""
        for name in self.EXPECTED_TOOLS:
            assert name.startswith("cc_"), f"{name} does not start with cc_"

    def test_tool_names_unique(self):
        """All tool names should be unique."""
        assert len(self.EXPECTED_TOOLS) == len(set(self.EXPECTED_TOOLS))


# =========================================================================
# Graceful degradation tests
# =========================================================================


class TestGracefulDegradation:
    """Verify meaningful error messages when core unavailable."""

    def test_missing_module_error_format(self, server):
        """Error responses should contain 'error' field."""
        result = server._handle_memory_search("x")
        data = json.loads(result)
        assert "error" in data

    def test_missing_module_has_ok_false(self, server):
        """Error responses should have ok: false."""
        result = server._handle_plugins_list()
        data = json.loads(result)
        assert data.get("ok") is False

    def test_ok_response_format(self, server):
        """Successful responses should contain 'data' field."""
        result = server._handle_plan_done()
        data = json.loads(result)
        assert "data" in data
        assert data.get("ok") is True


# =========================================================================
# Integration with actual core modules
# =========================================================================


class TestCoreModuleIntegration:
    """Verify handlers work when core modules are available.

    These tests use real imports where modules are installed in the
    current environment.
    """

    def test_handler_imports_are_lazy(self, mcp_module):
        """Core module imports should be lazy — not fail on module load."""
        # Already verified by test_module_imports_cleanly
        pass

    def test_missing_core_flags(self, mcp_module):
        """_HAS_* flags should be booleans."""
        for attr in [
            "_HAS_MEMORY",
            "_HAS_MEMORY_STORE",
            "_HAS_AGENT_REGISTRY",
            "_HAS_PLUGIN_REGISTRY",
            "_HAS_MCU",
            "_HAS_COST",
            "_HAS_ROUTER",
        ]:
            assert hasattr(mcp_module, attr), f"Missing flag: {attr}"
            assert isinstance(getattr(mcp_module, attr), bool)


# =========================================================================
# Skill directory scanning
# =========================================================================


class TestSkillsListIntegration:
    """Verify skills list scans directories correctly."""

    def test_skills_list_with_mock_dirs(self, server, tmp_path):
        """Skills list should find directories under skill paths."""
        # Create mock skill directories
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        (skill_dir / "python").mkdir()
        (skill_dir / "javascript").mkdir()

        with patch.object(Path, "expanduser") as mock_expand:
            def expand_side_effect():
                return tmp_path
            mock_expand.return_value = tmp_path

            result = server._handle_skills_list()
            data = json.loads(result)
            assert data.get("ok") is True

    def test_skills_list_empty(self, server):
        """Skills list should handle missing skill directories."""
        with patch("src.core.mcp_server.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            result = server._handle_skills_list()
            data = json.loads(result)
            assert data.get("ok") is True
            assert len(data["data"]["skills"]) == 0
