# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_pipeline.py — Verification Suite for Multi-Agent Sequential Pipeline.

Covers:
1. Pipeline orchestrator sequential execution (FilePicker -> Editor -> Reviewer).
2. Context propagation, stage dependencies, and custom stage composition.
3. Stage failure handling, stop_on_failure skipping, and error reporting.
4. Typer CLI surface (mekong pipeline) in console, --json, and --verbose modes.
5. Dual-engine MCP tools parity (FastMCP & JSON-RPC 2.0 fallback).
6. Strict AST core boundary invariants.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.pipeline_manager import (
    PipelineManager,
    PipelineResult,
    PipelineStage,
    PipelineStatus,
    get_pipeline_manager,
)


# ---------------------------------------------------------------------------
# Test Suite 1: Pipeline Orchestration & Multi-Agent Execution
# ---------------------------------------------------------------------------


class TestPipelineOrchestration:
    """Tests for core multi-agent sequential pipeline execution."""

    def test_singleton_get_pipeline_manager(self):
        pm1 = get_pipeline_manager()
        pm2 = get_pipeline_manager()
        assert pm1 is pm2
        assert isinstance(pm1, PipelineManager)

    def test_sequential_pipeline_execution(self, tmp_path: Path):
        pm = PipelineManager(stop_on_failure=True)
        # Point to tmp_path for fast file-picker scanning
        result = pm.run_multi_agent_pipeline(
            goal="implement user profile validation",
            root_dir=str(tmp_path),
        )

        assert result.status == PipelineStatus.COMPLETED
        assert result.total_stages == 3
        assert result.completed_stages == 3
        assert result.failed_stages == 0
        assert result.success_rate == 100.0
        assert result.total_duration_ms >= 0.0

        stage_names = [s.name for s in result.stages]
        assert stage_names == ["file-picker", "editor", "reviewer"]
        for s in result.stages:
            assert s.status == "completed"
            assert s.duration_ms >= 0.0
            assert s.output != ""

    def test_context_propagation_between_stages(self):
        captured_contexts: dict[str, dict[str, Any]] = {}

        def mock_executor(stage_name: str, goal: str, context: dict[str, Any]) -> str:
            captured_contexts[stage_name] = dict(context)
            if stage_name == "file-picker":
                return "auth.py, tokens.py"
            elif stage_name == "editor":
                return "Added JWT token validation"
            elif stage_name == "reviewer":
                return "All checks passed without regressions"
            return "ok"

        pm = PipelineManager(stop_on_failure=True)
        result = pm.run_multi_agent_pipeline(
            goal="add jwt authentication",
            executor_override=mock_executor,
        )

        assert result.status == PipelineStatus.COMPLETED
        assert "file-picker" in captured_contexts
        assert "editor" in captured_contexts
        assert "reviewer" in captured_contexts

        # Verify context was passed downstream
        assert captured_contexts["editor"]["file-picker"] == "auth.py, tokens.py"
        assert captured_contexts["reviewer"]["editor"] == "Added JWT token validation"

    def test_custom_stages_composition(self):
        pm = PipelineManager()
        result = pm.run_multi_agent_pipeline(
            goal="quick lint and review",
            stages=["file-picker", "reviewer"],
            executor_override=lambda stage, goal, ctx: f"{stage} done",
        )

        assert result.status == PipelineStatus.COMPLETED
        assert result.total_stages == 2
        assert [s.name for s in result.stages] == ["file-picker", "reviewer"]

    def test_stage_failure_stops_pipeline(self):
        def failing_executor(stage_name: str, goal: str, context: dict[str, Any]) -> str:
            if stage_name == "editor":
                raise RuntimeError("Syntax error in generated patch")
            return "stage output"

        pm = PipelineManager(stop_on_failure=True)
        result = pm.run_multi_agent_pipeline(
            goal="broken patch scenario",
            executor_override=failing_executor,
        )

        assert result.status == PipelineStatus.PARTIAL
        assert result.completed_stages == 1
        assert result.failed_stages == 1
        assert len(result.errors) == 1
        assert "Syntax error in generated patch" in result.errors[0]

        # Stage 1: completed, Stage 2: failed, Stage 3: skipped
        assert result.stages[0].status == "completed"
        assert result.stages[1].status == "failed"
        assert result.stages[2].status == "skipped"

    def test_invalid_stage_name_raises_value_error(self):
        pm = PipelineManager()
        with pytest.raises(ValueError, match="Unknown pipeline stage"):
            pm.run_multi_agent_pipeline(
                goal="invalid stage test",
                stages=["unknown_nonexistent_stage_xyz"],
            )

    def test_aggregate_results_includes_stage_outputs(self, tmp_path: Path):
        pm = PipelineManager()
        res = pm.run_multi_agent_pipeline(
            goal="test aggregation",
            stages=["file-picker", "reviewer"],
            root_dir=str(tmp_path),
        )
        agg = pm.aggregate_results(res.pipeline_id)

        assert agg["pipeline_id"] == res.pipeline_id
        assert agg["status"] == "completed"
        assert agg["total_stages"] == 2
        assert len(agg["stages"]) == 2
        assert agg["stages"][0]["name"] == "file-picker"
        assert agg["stages"][1]["name"] == "reviewer"
        assert "output" in agg["stages"][0]


# ---------------------------------------------------------------------------
# Test Suite 2: Typer CLI Commands Surface
# ---------------------------------------------------------------------------


class TestPipelineCliCommands:
    """Tests for mekong pipeline CLI commands."""

    def test_cli_pipeline_console_pass(self, tmp_path: Path):
        app = build_app()
        runner = CliRunner()

        res = runner.invoke(app, ["pipeline", "add error handling to auth.py"])
        assert res.exit_code == 0
        assert "Multi-Agent Sequential Pipeline" in res.output
        assert "Pipeline Execution Summary" in res.output
        assert "Verdict: PASS" in res.output
        assert "file-picker" in res.output
        assert "editor" in res.output
        assert "reviewer" in res.output

    def test_cli_pipeline_json_output(self):
        app = build_app()
        runner = CliRunner()

        res = runner.invoke(app, ["pipeline", "optimize database queries", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "completed"
        assert data["total_stages"] == 3
        assert data["completed"] == 3
        assert data["goal"] == "optimize database queries"
        assert len(data["stages"]) == 3

    def test_cli_pipeline_verbose_mode(self):
        app = build_app()
        runner = CliRunner()

        res = runner.invoke(app, ["pipeline", "update config", "--verbose"])
        assert res.exit_code == 0
        assert "Stage [1] file-picker (completed)" in res.output
        assert "Stage [2] editor (completed)" in res.output
        assert "Stage [3] reviewer (completed)" in res.output

    def test_cli_pipeline_custom_stages(self):
        app = build_app()
        runner = CliRunner()

        res = runner.invoke(
            app,
            ["pipeline", "code review only", "--stages", "file-picker,reviewer", "--json"],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["total_stages"] == 2
        stage_names = [s["name"] for s in data["stages"]]
        assert stage_names == ["file-picker", "reviewer"]

    def test_cli_pipeline_invalid_stage_failure(self):
        app = build_app()
        runner = CliRunner()

        res = runner.invoke(
            app,
            ["pipeline", "broken pipeline", "--stages", "invalid_stage_xyz", "--json"],
        )
        assert res.exit_code == 1
        data = json.loads(res.output)
        assert data["ok"] is False
        assert data["status"] == "failed"
        assert "Unknown pipeline stage" in data["error"]


# ---------------------------------------------------------------------------
# Test Suite 3: Native MCP Pipeline Tools Dual-Engine Parity
# ---------------------------------------------------------------------------


class TestMcpPipelineToolsParity:
    """Tests for native MCP pipeline tools dual-engine parity."""

    def test_mcp_pipeline_run_and_status_fallback(self):
        from scripts.mcp_server import handle_pipeline_run, handle_pipeline_status

        raw_run = handle_pipeline_run(
            {"goal": "add telemetry trace context", "stages": ["file-picker", "reviewer"]}
        )
        run_data = json.loads(raw_run)
        assert run_data["ok"] is True
        assert run_data["data"]["status"] == "completed"
        assert run_data["data"]["total_stages"] == 2
        pipeline_id = run_data["data"]["pipeline_id"]

        raw_stat = handle_pipeline_status({"pipeline_id": pipeline_id})
        stat_data = json.loads(raw_stat)
        assert stat_data["ok"] is True
        assert stat_data["data"]["pipeline_id"] == pipeline_id
        assert stat_data["data"]["status"] == "completed"

    def test_mcp_pipeline_status_list_all(self):
        from scripts.mcp_server import handle_pipeline_status

        raw_list = handle_pipeline_status({})
        list_data = json.loads(raw_list)
        assert list_data["ok"] is True
        assert "total_pipelines" in list_data["data"]
        assert isinstance(list_data["data"]["pipelines"], list)

    def test_mcp_pipeline_status_not_found(self):
        from scripts.mcp_server import handle_pipeline_status

        raw_stat = handle_pipeline_status({"pipeline_id": "nonexistent_pid_12345"})
        stat_data = json.loads(raw_stat)
        assert stat_data["ok"] is False
        assert "Pipeline not found" in stat_data["error"]

    def test_mcp_pipeline_run_missing_goal(self):
        from scripts.mcp_server import handle_pipeline_run

        raw_run = handle_pipeline_run({})
        run_data = json.loads(raw_run)
        assert run_data["ok"] is False
        assert "Missing required argument: goal" in run_data["error"]

    def test_core_mcp_server_pipeline_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_run = server._handle_pipeline_run(
            goal="test core mcp pipeline execution",
            stages=["file-picker", "reviewer"],
        )
        run_data = json.loads(res_run)
        assert run_data["ok"] is True
        assert run_data["data"]["status"] == "completed"

        pid = run_data["data"]["pipeline_id"]
        res_stat = server._handle_pipeline_status(pipeline_id=pid)
        stat_data = json.loads(res_stat)
        assert stat_data["ok"] is True
        assert stat_data["data"]["pipeline_id"] == pid


# ---------------------------------------------------------------------------
# Test Suite 4: AST Core Boundary Invariant
# ---------------------------------------------------------------------------


class TestAstCoreBoundary:
    """Verifies src/core/pipeline_manager.py contains strictly zero vendor SDK imports."""

    def test_pure_standard_library_imports(self):
        core_file = Path(__file__).resolve().parents[1] / "src" / "core" / "pipeline_manager.py"
        assert core_file.is_file(), f"Missing {core_file}"

        tree = ast.parse(core_file.read_text(encoding="utf-8"), filename=str(core_file))
        disallowed_modules = {
            "anthropic",
            "openai",
            "google.generativeai",
            "requests",
            "httpx",
            "aiohttp",
            "fastapi",
            "flask",
            "pydantic",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".")[0]
                    assert top_level not in disallowed_modules, (
                        f"Disallowed import '{alias.name}' at line {node.lineno} in {core_file}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level = node.module.split(".")[0]
                    assert top_level not in disallowed_modules, (
                        f"Disallowed import-from '{node.module}' at line {node.lineno} in {core_file}"
                    )
