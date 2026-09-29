# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_benchmark.py — Comprehensive Test Suite for Phase 11.

Verifies:
1. Benchmark data models: percentiles, pass rates, and serializations.
2. BenchmarkBridge suites: PEV, Checkpoints, Subagents, and Chaos scenarios.
3. Chaos fault injection: verified self-healing recovery and error detection.
4. CLI command (mekong benchmark): Rich terminal output and machine-readable --json.
5. Dual-engine MCP tools: mekong_benchmark_run and mekong_chaos_simulate parity.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.benchmark_bridge import (
    BenchmarkBridge,
    BenchmarkMetric,
    BenchmarkReport,
    ChaosFaultType,
    ChaosResult,
)
from src.core.mcp_server import MekongMcpServer
from scripts.mcp_server import (
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
    handle_benchmark_run,
    handle_chaos_simulate,
)

runner = CliRunner()


class TestBenchmarkDataModels:
    """Test BenchmarkMetric, ChaosResult, and BenchmarkReport data structures."""

    def test_benchmark_metric_percentiles_and_pass_rate(self) -> None:
        metric = BenchmarkMetric(
            name="test_metric",
            suite="test_suite",
            iterations=10,
            passed_count=9,
            failed_count=1,
            duration_ms_total=150.0,
            durations_ms=[10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 18.0, 20.0, 21.0],
        )
        metric.calculate_percentiles()
        assert metric.pass_rate == 90.0
        assert metric.p50_ms == 15.0
        assert metric.p90_ms == 21.0
        assert metric.p99_ms == 21.0

        d = metric.to_dict()
        assert d["name"] == "test_metric"
        assert d["pass_rate_pct"] == 90.0
        assert d["passed_count"] == 9
        assert d["failed_count"] == 1

    def test_benchmark_metric_empty_durations(self) -> None:
        metric = BenchmarkMetric(
            name="empty_metric",
            suite="test_suite",
            iterations=0,
            passed_count=0,
            failed_count=0,
            duration_ms_total=0.0,
            durations_ms=[],
        )
        metric.calculate_percentiles()
        assert metric.pass_rate == 0.0
        assert metric.p50_ms == 0.0

    def test_chaos_result_serialization(self) -> None:
        res = ChaosResult(
            scenario="simulated_crash",
            fault_injected="SIGKILL",
            detected=True,
            self_healed=True,
            recovery_time_ms=12.345,
            details={"retry_count": 1},
        )
        d = res.to_dict()
        assert d["scenario"] == "simulated_crash"
        assert d["detected"] is True
        assert d["self_healed"] is True
        assert d["recovery_time_ms"] == 12.35
        assert d["details"]["retry_count"] == 1


class TestBenchmarkBridgeSuites:
    """Test deterministic execution of all benchmark suites."""

    @pytest.fixture
    def bridge(self) -> BenchmarkBridge:
        return BenchmarkBridge()

    def test_pev_benchmark_suite(self, bridge: BenchmarkBridge) -> None:
        report = bridge.run_benchmark(suite="pev", iterations=2, chaos_level="none")
        assert report.run_id.startswith("bench_")
        assert "pev" in report.suites_run
        assert report.total_tests == 4  # 2 iterations * 2 tests
        assert report.total_passed == 4
        assert report.total_failed == 0
        assert report.resilience_score > 90.0
        assert len(report.metrics) == 2
        metric_names = [m.name for m in report.metrics]
        assert "pev_plan_generation" in metric_names
        assert "pev_task_sequencing" in metric_names

    def test_checkpoints_benchmark_suite(self, bridge: BenchmarkBridge) -> None:
        report = bridge.run_benchmark(suite="checkpoints", iterations=2, chaos_level="none")
        assert "checkpoints" in report.suites_run
        assert report.total_tests == 4  # 2 iterations * 2 tests
        assert report.total_passed == 4
        assert report.total_failed == 0
        metric_names = [m.name for m in report.metrics]
        assert "checkpoint_snapshot_creation" in metric_names
        assert "checkpoint_atomic_rollback" in metric_names

    def test_subagents_benchmark_suite(self, bridge: BenchmarkBridge) -> None:
        report = bridge.run_benchmark(suite="subagents", iterations=2, chaos_level="none")
        assert "subagents" in report.suites_run
        assert report.total_tests == 4
        assert report.total_passed == 4
        assert report.total_failed == 0
        metric_names = [m.name for m in report.metrics]
        assert "subagent_registry_lookup" in metric_names
        assert "subagent_context_budget_audit" in metric_names

    def test_chaos_benchmark_suite(self, bridge: BenchmarkBridge) -> None:
        report = bridge.run_benchmark(suite="chaos", iterations=1, chaos_level="high")
        assert "chaos" in report.suites_run
        assert len(report.chaos_results) >= 4  # 3 standard + 1 high severity
        for c in report.chaos_results:
            assert c.detected is True
            assert c.self_healed is True
            assert c.recovery_time_ms >= 0.0

    def test_full_benchmark_all_suites(self, bridge: BenchmarkBridge) -> None:
        report = bridge.run_benchmark(suite="all", iterations=1, chaos_level="low")
        assert len(report.suites_run) == 4
        assert report.total_tests >= 9
        assert report.total_passed == report.total_tests
        assert report.total_failed == 0
        assert report.resilience_score >= 95.0

    def test_telemetry_persisted_to_evals_db(self, bridge: BenchmarkBridge) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp_db = Path(td) / "test_evals.db"
            with patch("src.core.evals_bridge.get_evals_db_path", return_value=temp_db):
                report = bridge.run_benchmark(suite="pev", iterations=1)
                conn = sqlite3.connect(str(temp_db))
                row = conn.execute("SELECT * FROM mission_evals WHERE mission_id = ?", (report.run_id,)).fetchone()
                assert row is not None
                conn.close()


class TestChaosSimulations:
    """Test individual chaos fault injection and self-healing recovery."""

    @pytest.fixture
    def bridge(self) -> BenchmarkBridge:
        return BenchmarkBridge()

    def test_simulate_chaos_checkpoint_corruption(self, bridge: BenchmarkBridge) -> None:
        result = bridge.simulate_chaos(target="checkpoint", error_type="corrupt_file")
        assert result.scenario == "corrupted_checkpoint_recovery"
        assert result.detected is True
        assert result.self_healed is True
        assert result.recovery_time_ms > 0

    def test_simulate_chaos_tool_timeout(self, bridge: BenchmarkBridge) -> None:
        result = bridge.simulate_chaos(target="timeout", error_type="tool_hang")
        assert result.scenario == "tool_timeout_resilience"
        assert result.detected is True
        assert result.self_healed is True

    def test_simulate_chaos_corrupt_payload(self, bridge: BenchmarkBridge) -> None:
        result = bridge.simulate_chaos(target="payload", error_type="invalid_json")
        assert result.scenario == "corrupt_payload_validation"
        assert result.detected is True
        assert result.self_healed is True

    def test_simulate_chaos_multi_file(self, bridge: BenchmarkBridge) -> None:
        result = bridge._chaos_multi_file_corruption()
        assert result.scenario == "multi_file_simultaneous_corruption"
        assert result.detected is True
        assert result.self_healed is True


class TestBenchmarkCLI:
    """Test Typer CLI surface for mekong benchmark."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_benchmark_cli_help(self, app) -> None:
        res = runner.invoke(app, ["benchmark", "--help"])
        assert res.exit_code == 0
        assert "⚡ Autonomous Benchmark" in res.stdout
        assert "--suite" in res.stdout
        assert "--iterations" in res.stdout
        assert "--chaos-level" in res.stdout
        assert "--json" in res.stdout

    def test_benchmark_cli_json_mode(self, app) -> None:
        res = runner.invoke(app, ["benchmark", "--json", "--suite", "pev", "--iterations", "1"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["suites_run"] == ["pev"]
        assert data["total_tests"] == 2
        assert data["total_passed"] == 2
        assert data["total_failed"] == 0
        assert data["resilience_score"] > 90.0

    def test_benchmark_cli_interactive_table(self, app) -> None:
        res = runner.invoke(app, ["benchmark", "--suite", "checkpoints", "--iterations", "1"])
        assert res.exit_code == 0
        assert "Antigravity Resilience Engine" in res.stdout
        assert "CHECKPOINTS" in res.stdout
        assert "Composite Resilience Index" in res.stdout


class TestBenchmarkMCPParity:
    """Test FastMCP and JSON-RPC fallback parity for benchmark and chaos tools."""

    def test_scripts_mcp_server_benchmark_run(self) -> None:
        raw_res = handle_benchmark_run({"suite": "pev", "iterations": 1, "chaos_level": "none"})
        data = json.loads(raw_res)
        assert data.get("ok") is True
        assert "run_id" in data
        assert data.get("total_passed") == 2
        assert data.get("total_failed") == 0

    def test_scripts_mcp_server_chaos_simulate(self) -> None:
        raw_res = handle_chaos_simulate({"target": "checkpoint", "error_type": "corrupt_file"})
        data = json.loads(raw_res)
        assert data.get("ok") is True
        assert data.get("detected") is True
        assert data.get("self_healed") is True

    def test_core_handlers_and_spec_registration(self) -> None:
        assert "mekong_benchmark_run" in CORE_HANDLERS
        assert "mekong_chaos_simulate" in CORE_HANDLERS

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_benchmark_run" in tool_names
        assert "mekong_chaos_simulate" in tool_names

    def test_src_core_mcp_server_parity(self) -> None:
        server = MekongMcpServer()
        bench_res = json.loads(server._handle_benchmark_run(suite="pev", iterations=1))
        assert bench_res.get("ok") is True
        assert bench_res.get("total_passed") == 2

        chaos_res = json.loads(server._handle_chaos_simulate(target="checkpoint"))
        assert chaos_res.get("ok") is True
        assert chaos_res.get("self_healed") is True

        # Test aliases
        assert server._handle_mekong_benchmark_run == server._handle_benchmark_run
        assert server._handle_mekong_chaos_simulate == server._handle_chaos_simulate
