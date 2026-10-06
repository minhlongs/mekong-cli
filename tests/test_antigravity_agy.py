# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for AGY (Agent Governance YAML & Antigravity CLI) Operations Suite.

Covers:
1. AST Core Boundary Compliance: standard library only, zero external SDKs.
2. AGYEngine Operations: status, list, show, plan, walk, new, bin, chat, sync.
3. CLI Command Surface: mekong agy subcommands (--json and rich text modes).
4. Native MCP Tools: parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.core.agy_engine import AGYEngine


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking Typer CLI commands."""
    return CliRunner()


class TestASTCoreBoundary:
    """Verify src/core/agy_engine.py adheres strictly to the standard library."""

    def test_no_external_vendor_or_http_imports_in_agy_engine(self):
        engine_file = Path("src/core/agy_engine.py")
        assert engine_file.exists()

        tree = ast.parse(engine_file.read_text(encoding="utf-8"), filename=str(engine_file))
        forbidden_modules = {
            "anthropic",
            "openai",
            "requests",
            "httpx",
            "pydantic",
            "fastapi",
            "typer",
            "rich",
            "watchdog",
            "google",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".")[0]
                    assert root_name not in forbidden_modules, f"Forbidden import found: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_name = node.module.split(".")[0]
                    assert root_name not in forbidden_modules, f"Forbidden import from found: {node.module}"


class TestAGYEngine:
    """Tests for pure AGYEngine business logic."""

    def test_get_status(self):
        engine = AGYEngine()
        status = engine.get_status()

        assert "status" in status
        assert status["status"] in ("HEALTHY", "DEGRADED")
        assert "binaries" in status
        assert "agy" in status["binaries"]
        assert "agym" in status["binaries"]
        assert "agy_task" in status["binaries"]
        assert "directories" in status
        assert "metrics" in status
        assert status["metrics"]["local_skills_count"] >= 0
        assert "governance" in status
        assert status["governance"]["framework"] == "AGY (Agent Governance YAML)"

    def test_list_workflows(self):
        engine = AGYEngine()
        all_wf = engine.list_workflows(limit=20)
        assert isinstance(all_wf, list)
        assert len(all_wf) <= 20

        if all_wf:
            first = all_wf[0]
            assert "name" in first
            assert "layer" in first
            assert "macro" in first
            assert first["macro"].startswith("/mekong-")
            assert "short_macro" in first
            assert first["short_macro"].startswith("/m-")
            assert "description" in first

    def test_list_workflows_filter_layer(self):
        engine = AGYEngine()
        eng_wf = engine.list_workflows(layer="engineering", limit=10)
        assert isinstance(eng_wf, list)
        for wf in eng_wf:
            assert "engineering" in wf["layer"].lower()

    def test_list_workflows_filter_category(self):
        engine = AGYEngine()
        cook_wf = engine.list_workflows(category="cook", limit=10)
        assert isinstance(cook_wf, list)
        for wf in cook_wf:
            assert "cook" in wf["name"].lower() or "cook" in wf["description"].lower()

    def test_show_workflow_found(self):
        engine = AGYEngine()
        # "cook" or "status" or "plan" skill is guaranteed to exist
        res = engine.show_workflow("cook")
        assert res["ok"] is True
        assert res["name"] == "cook"
        assert res["macro_binding"] == "/mekong-cook"
        assert "governance_gate" in res
        assert "content" in res

    def test_show_workflow_not_found(self):
        engine = AGYEngine()
        res = engine.show_workflow("non_existent_skill_xyz_999")
        assert res["ok"] is False
        assert "not found" in res["error"]

    def test_plan_workflow_build(self):
        engine = AGYEngine()
        plan = engine.plan_workflow("Build a high performance real-time streaming feature")
        assert plan["plan_id"].startswith("AGY-PLAN-")
        assert plan["tasks_count"] == 4
        assert len(plan["tasks"]) == 4
        assert plan["tasks"][0]["role"] == "Product Strategist"
        assert plan["tasks"][1]["role"] == "Senior Engineer"
        assert plan["tasks"][2]["role"] == "QA Engineer"
        assert plan["tasks"][3]["role"] == "DevOps Lead"
        assert plan["tasks"][3]["gate"] == "HIGH_RISK_REQUIRE_CEO"
        assert plan["estimated_total_tokens"] > 0
        assert "governance" in plan
        assert plan["governance"]["context_budget_cap"] == 40000

    def test_plan_workflow_fix(self):
        engine = AGYEngine()
        plan = engine.plan_workflow("Fix broken database connection pool timeout bug")
        assert plan["tasks_count"] == 3
        roles = [t["role"] for t in plan["tasks"]]
        assert "PM Agent" in roles
        assert "Lead Developer" in roles
        assert "QA Agent" in roles

    def test_plan_workflow_audit(self):
        engine = AGYEngine()
        plan = engine.plan_workflow("Audit compliance and security governance rules")
        assert plan["tasks_count"] == 2
        roles = [t["role"] for t in plan["tasks"]]
        assert "SRE & Auditor" in roles
        assert "Solo CEO" in roles

    def test_get_walkthrough(self):
        engine = AGYEngine()
        walk = engine.get_walkthrough()
        assert "title" in walk
        assert "components" in walk
        assert len(walk["components"]) >= 4
        assert "macro_patterns" in walk
        assert "slash_commands" in walk

    def test_scaffold_spec(self):
        engine = AGYEngine()
        scaffold = engine.scaffold_spec(name="my-custom-flow", layer="business", description="Custom Biz Flow")
        assert scaffold["name"] == "my-custom-flow"
        assert scaffold["layer"] == "business"
        assert scaffold["macro"] == "/mekong-my-custom-flow"
        assert "---" in scaffold["yaml_spec"]
        assert "name: my-custom-flow" in scaffold["yaml_spec"]
        assert "layer: business" in scaffold["yaml_spec"]

    def test_scaffold_spec_high_risk(self):
        engine = AGYEngine()
        scaffold = engine.scaffold_spec(name="deploy-production", layer="ops")
        assert "HIGH" in scaffold["yaml_spec"]
        assert "requires_approval: true" in scaffold["yaml_spec"]

    def test_get_binary_info(self):
        engine = AGYEngine()
        info = engine.get_binary_info()
        assert "binaries" in info
        assert "agy" in info["binaries"]
        assert "agym" in info["binaries"]
        assert "agy_task" in info["binaries"]
        assert "macro_wrapper_enabled" in info

    def test_execute_chat_simulated(self):
        engine = AGYEngine()
        # When binary is not mocked or found, returns simulated response
        with patch("shutil.which", return_value=None), patch.object(Path, "exists", return_value=False):
            res = engine.execute_chat("Hello Antigravity")
            assert res["ok"] is True
            assert res["mode"] == "simulated"
            assert "Hello Antigravity" in res["response"]

    def test_execute_chat_live_success(self):
        engine = AGYEngine()
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "AGY response from LLM"
        mock_proc.stderr = ""

        with patch("shutil.which", return_value="/mock/bin/agy"), \
             patch("os.access", return_value=True), \
             patch("subprocess.run", return_value=mock_proc):
            res = engine.execute_chat("Plan deployment", model="gemini-3-flash-preview")
            assert res["ok"] is True
            assert res["mode"] == "live"
            assert res["response"] == "AGY response from LLM"
            assert res["exit_code"] == 0

    def test_execute_chat_live_failure(self):
        engine = AGYEngine()
        with patch("shutil.which", return_value="/mock/bin/agy"), \
             patch("os.access", return_value=True), \
             patch("subprocess.run", side_effect=RuntimeError("Subprocess failed")):
            res = engine.execute_chat("Fail prompt")
            assert res["ok"] is False
            assert res["mode"] == "live_failed"
            assert "Subprocess failed" in res["error"]

    def test_sync_integration(self):
        engine = AGYEngine()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            mock_config_dir = tmp_path / "config"
            with patch("src.core.agy_engine.AGY_CONFIG_DIR", mock_config_dir), \
                 patch("src.core.agy_engine.ANTIGRAVITY_DIR", tmp_path / "antigravity"), \
                 patch("src.core.agy_engine.AGY_PLUGIN_DIR", tmp_path / "plugin"):
                res = engine.sync_integration()
                assert res["ok"] is True
                assert res["macros_registered"] >= 0
                assert (mock_config_dir / "macros.json").exists()


class TestAGYCLI:
    """Tests for Typer CLI commands in src/cli/commands/agy_command.py."""

    def test_cli_agy_default_status(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy"])
        assert result.exit_code == 0
        assert "AGY — AGENT GOVERNANCE YAML" in result.output

    def test_cli_agy_status_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "status" in data
        assert "binaries" in data
        assert "metrics" in data

    def test_cli_agy_list_text(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "list", "--limit", "5"])
        assert result.exit_code == 0
        assert "AGY Workflows & Macro Bindings" in result.output

    def test_cli_agy_list_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "list", "--limit", "5", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_cli_agy_show_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "show", "cook", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["name"] == "cook"

    def test_cli_agy_show_not_found(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "show", "non_existent_xyz"])
        assert result.exit_code != 0

    def test_cli_agy_plan_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "plan", "Build analytics dashboard", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "plan_id" in data
        assert data["tasks_count"] == 4

    def test_cli_agy_plan_text(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "plan", "Audit SOX compliance"])
        assert result.exit_code == 0
        assert "AGY Multi-Agent Plan" in result.output

    def test_cli_agy_walk(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "walk"])
        assert result.exit_code == 0
        assert "Architecture Walkthrough" in result.output

    def test_cli_agy_walk_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "walk", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "components" in data

    def test_cli_agy_new_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "new", "test-scaffold", "--layer", "engineering", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "test-scaffold"
        assert data["layer"] == "engineering"
        assert "yaml_spec" in data

    def test_cli_agy_bin(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "bin", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "binaries" in data

    def test_cli_agy_chat_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        with patch.object(
            AGYEngine,
            "execute_chat",
            return_value={"ok": True, "mode": "simulated", "prompt": "Test prompt", "response": "Mocked chat response"}
        ):
            result = runner.invoke(app, ["agy", "chat", "Test prompt", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True
            assert "response" in data

    def test_cli_agy_sync_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["agy", "sync", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "macros_registered" in data


class TestAGYMCP:
    """Tests for native MCP tools across scripts/mcp_server.py and src/core/mcp_server.py."""

    def test_scripts_mcp_handlers(self):
        from scripts.mcp_server import (
            handle_agy_list,
            handle_agy_plan,
            handle_agy_status,
            handle_agy_sync,
        )

        # Status
        raw_status = handle_agy_status({})
        status_data = json.loads(raw_status)
        assert "status" in status_data
        assert "binaries" in status_data

        # List
        raw_list = handle_agy_list({"limit": 5})
        list_data = json.loads(raw_list)
        assert isinstance(list_data, list)
        assert len(list_data) <= 5

        # Plan
        raw_plan = handle_agy_plan({"goal": "Build payment processing"})
        plan_data = json.loads(raw_plan)
        assert "plan_id" in plan_data
        assert plan_data["tasks_count"] == 4

        # Sync
        raw_sync = handle_agy_sync({})
        sync_data = json.loads(raw_sync)
        assert sync_data["ok"] is True

    def test_scripts_mcp_tool_handlers_registration(self):
        from scripts.mcp_server import CORE_HANDLERS

        assert "mekong_agy_status" in CORE_HANDLERS
        assert "mekong_agy_list" in CORE_HANDLERS
        assert "mekong_agy_plan" in CORE_HANDLERS
        assert "mekong_agy_sync" in CORE_HANDLERS
        assert "agy_status" in CORE_HANDLERS
        assert "agy_list" in CORE_HANDLERS
        assert "agy_plan" in CORE_HANDLERS
        assert "agy_sync" in CORE_HANDLERS

    def test_core_mcp_server_method_parity(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # _handle_agy_status
        raw_status = server._handle_agy_status()
        status_data = json.loads(raw_status)
        assert "status" in status_data

        # _handle_agy_list
        raw_list = server._handle_agy_list(limit=3)
        list_data = json.loads(raw_list)
        assert isinstance(list_data, list)
        assert len(list_data) <= 3

        # _handle_agy_plan
        raw_plan = server._handle_agy_plan(goal="Fix bug in auth")
        plan_data = json.loads(raw_plan)
        assert "plan_id" in plan_data
        assert plan_data["tasks_count"] == 3

        # _handle_agy_sync
        raw_sync = server._handle_agy_sync()
        sync_data = json.loads(raw_sync)
        assert sync_data["ok"] is True

        # Alias parity
        assert server._handle_mekong_agy_status == server._handle_agy_status
        assert server._handle_mekong_agy_sync == server._handle_agy_sync
        assert server._handle_mekong_agy_list == server._handle_agy_list
        assert server._handle_mekong_agy_plan == server._handle_agy_plan
