# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Telemetry Mesh, Prometheus Exporter & Distributed Tracing (Phase 17).

Covers:
1. Span & W3C Tracecontext: 00-{trace_id}-{span_id}-01 generation, header parsing, span lifecycles.
2. TelemetryRegistry: Prometheus exposition formatting (# HELP, # TYPE, counters, gauges, histograms).
3. TelemetryBridge: In-memory ring buffer, SQLite persistence, trace hierarchy querying.
4. CLI Commands: mekong telemetry metrics, mekong telemetry traces, mekong telemetry export.
5. Native MCP Tools: mekong_telemetry_metrics and mekong_trace_query dual-engine parity.
6. AST Core Boundary Compliance: strict standard library only in src/core/telemetry_bridge.py.
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.telemetry_bridge import (
    DEFAULT_HISTOGRAM_BUCKETS,
    Span,
    TelemetryBridge,
    TelemetryRegistry,
    get_telemetry_bridge,
    parse_traceparent,
)


@pytest.fixture
def temp_bridge(tmp_path: Path):
    """Create an isolated TelemetryBridge with a temporary SQLite database."""
    db_file = tmp_path / "telemetry_test.db"
    return TelemetryBridge(db_path=db_file, max_spans=10)


class TestSpanAndW3CTraceparent:
    """Tests for W3C distributed tracing spans and traceparent headers."""

    def test_span_creation_and_defaults(self):
        span = Span(
            span_id="0123456789abcdef",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            name="test_operation",
        )
        assert span.span_id == "0123456789abcdef"
        assert span.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert span.name == "test_operation"
        assert span.status == "unset"
        assert span.parent_id is None
        assert span.duration_ms == 0.0
        assert span.traceparent == "00-4bf92f3577b34da6a3ce929d0e0e4736-0123456789abcdef-01"

    def test_span_end_and_events(self):
        span = Span(
            span_id="1111222233334444",
            trace_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            name="work_task",
        )
        span.add_event("checkpoint_saved", {"snapshot_id": "snap-99"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "checkpoint_saved"
        assert span.events[0]["attributes"]["snapshot_id"] == "snap-99"

        time.sleep(0.01)
        span.end(status="ok")
        assert span.status == "ok"
        assert span.duration_ms > 0.0
        assert span.end_time is not None

        # Test error ending
        err_span = Span(
            span_id="5555666677778888",
            trace_id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            name="failing_task",
        )
        err_span.end(status="error", error="Database connection refused")
        assert err_span.status == "error"
        assert err_span.attributes["error"] == "Database connection refused"
        assert any(e["name"] == "exception" for e in err_span.events)

    def test_parse_traceparent_valid_and_invalid(self):
        valid = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        res = parse_traceparent(valid)
        assert res is not None
        trace_id, parent_id = res
        assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert parent_id == "00f067aa0ba902b7"

        # Invalid cases
        assert parse_traceparent("invalid") is None
        assert parse_traceparent("01-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01") is None
        assert parse_traceparent("00-short-00f067aa0ba902b7-01") is None
        assert parse_traceparent("00-4bf92f3577b34da6a3ce929d0e0e4736-short-01") is None
        assert parse_traceparent("00-4bf92f3577b34da6a3ce929d0e0e473g-00f067aa0ba902b7-01") is None


class TestTelemetryRegistry:
    """Tests for pure standard-library Prometheus exposition formatting."""

    def test_counter_and_gauge_operations(self):
        reg = TelemetryRegistry()
        reg.inc_counter("mekong_missions_total", 1.0, {"agent": "cto"}, "Total missions executed")
        reg.inc_counter("mekong_missions_total", 2.0, {"agent": "cto"})
        reg.inc_counter("mekong_missions_total", 1.0, {"agent": "sre"})

        reg.set_gauge("mekong_active_subagents", 4.0, help_text="Currently running subagents")
        reg.inc_gauge("mekong_active_subagents", 2.0)
        reg.dec_gauge("mekong_active_subagents", 1.0)

        data = reg.to_dict()
        assert "mekong_missions_total" in data["counters"]
        assert "mekong_active_subagents" in data["gauges"]
        assert data["gauges"]["mekong_active_subagents"][0]["value"] == 5.0

    def test_histogram_operations(self):
        reg = TelemetryRegistry()
        reg.observe_histogram("mekong_step_duration_seconds", 0.05, {"step": "plan"}, "Step latency")
        reg.observe_histogram("mekong_step_duration_seconds", 0.35, {"step": "plan"})
        reg.observe_histogram("mekong_step_duration_seconds", 1.5, {"step": "plan"})

        data = reg.to_dict()
        assert "mekong_step_duration_seconds" in data["histograms"]
        entry = data["histograms"]["mekong_step_duration_seconds"][0]
        assert entry["count"] == 3
        assert pytest.approx(entry["sum"], 0.001) == 1.9

    def test_prometheus_exposition_text(self):
        reg = TelemetryRegistry()
        reg.inc_counter("http_requests_total", 10.0, {"method": "GET", "status": "200"}, "Total HTTP requests")
        reg.set_gauge("system_memory_usage_ratio", 0.42, help_text="System memory ratio")
        reg.observe_histogram("http_request_duration_seconds", 0.12, {"handler": "metrics"}, "Request duration")

        text = reg.to_prometheus_text()
        assert "# HELP http_requests_total Total HTTP requests" in text
        assert "# TYPE http_requests_total counter" in text
        assert 'http_requests_total{method="GET",status="200"} 10.0' in text

        assert "# HELP system_memory_usage_ratio System memory ratio" in text
        assert "# TYPE system_memory_usage_ratio gauge" in text
        assert "system_memory_usage_ratio 0.42" in text

        assert "# HELP http_request_duration_seconds Request duration" in text
        assert "# TYPE http_request_duration_seconds histogram" in text
        assert 'http_request_duration_seconds_bucket{handler="metrics",le="0.25"} 1' in text
        assert 'http_request_duration_seconds_sum{handler="metrics"} 0.12' in text
        assert 'http_request_duration_seconds_count{handler="metrics"} 1' in text


class TestTelemetryBridge:
    """Tests for distributed tracing bridge, span query, and ring-buffer capping."""

    def test_span_lifecycle_and_db_persistence(self, temp_bridge: TelemetryBridge):
        span = temp_bridge.start_span("agent_execute", attributes={"role": "cto"})
        assert span.name == "agent_execute"
        assert len(span.trace_id) == 32
        assert len(span.span_id) == 16
        assert span.span_id in temp_bridge._active_spans

        temp_bridge.end_span(span, status="ok")
        assert span.span_id not in temp_bridge._active_spans
        assert len(temp_bridge._spans_buffer) == 1

        # Query back
        spans = temp_bridge.query_spans(trace_id=span.trace_id)
        assert len(spans) == 1
        assert spans[0].span_id == span.span_id
        assert spans[0].attributes["role"] == "cto"

    def test_span_propagation_from_w3c_header(self, temp_bridge: TelemetryBridge):
        trace_header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        child = temp_bridge.start_span("child_task", traceparent=trace_header)
        assert child.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert child.parent_id == "00f067aa0ba902b7"
        assert child.span_id != "00f067aa0ba902b7"

    def test_ring_buffer_capping(self, temp_bridge: TelemetryBridge):
        # max_spans is 10 for temp_bridge
        for i in range(15):
            s = temp_bridge.start_span(f"task_{i}")
            temp_bridge.end_span(s)

        assert len(temp_bridge._spans_buffer) == 10
        # All 15 should still exist in SQLite
        recent = temp_bridge.query_spans(limit=20)
        assert len(recent) == 15


class TestTelemetryCliCommands:
    """Tests for mekong telemetry CLI commands."""

    def test_cli_metrics_prometheus_and_json(self):
        app = build_app()
        runner = CliRunner()

        # Record a test metric first
        bridge = get_telemetry_bridge()
        bridge.metrics.inc_counter("mekong_cli_test_counter", 1.0)

        # 1. Prometheus format (default)
        res1 = runner.invoke(app, ["telemetry", "metrics"])
        assert res1.exit_code == 0
        assert "# TYPE" in res1.output

        # 2. JSON format
        res2 = runner.invoke(app, ["telemetry", "metrics", "--format", "json"])
        assert res2.exit_code == 0
        data = json.loads(res2.output)
        assert "counters" in data
        assert "gauges" in data

    def test_cli_traces_and_export(self, tmp_path: Path):
        app = build_app()
        runner = CliRunner()

        bridge = get_telemetry_bridge()
        s = bridge.start_span("cli_test_span", attributes={"env": "test"})
        bridge.end_span(s)

        # 1. Console traces
        res_traces = runner.invoke(app, ["telemetry", "traces"])
        assert res_traces.exit_code == 0
        assert "Distributed Traces Query" in res_traces.output or "cli_test_span" in res_traces.output

        # 2. JSON traces
        res_traces_json = runner.invoke(app, ["telemetry", "traces", "--json"])
        assert res_traces_json.exit_code == 0
        traces_list = json.loads(res_traces_json.output)
        assert isinstance(traces_list, list)
        assert any(t["name"] == "cli_test_span" for t in traces_list)

        # 3. Export
        export_dir = tmp_path / "telemetry_export"
        res_export = runner.invoke(app, ["telemetry", "export", "-o", str(export_dir), "--json"])
        assert res_export.exit_code == 0
        exp_summary = json.loads(res_export.output)
        assert exp_summary["ok"] is True
        assert Path(exp_summary["metrics_file"]).exists()
        assert Path(exp_summary["traces_file"]).exists()


class TestMcpTelemetryToolsParity:
    """Tests for native MCP telemetry tools dual-engine parity."""

    def test_mcp_telemetry_metrics_fallback(self):
        from scripts.mcp_server import handle_telemetry_metrics

        # Prometheus text mode
        raw_prom = handle_telemetry_metrics({"format_type": "prometheus"})
        assert isinstance(raw_prom, str)
        assert "# HELP" in raw_prom or "# TYPE" in raw_prom or raw_prom == ""

        # JSON mode
        raw_json = handle_telemetry_metrics({"format_type": "json"})
        data = json.loads(raw_json)
        assert data["ok"] is True
        assert "counters" in data["data"]

    def test_mcp_trace_query_fallback(self):
        from scripts.mcp_server import handle_trace_query

        bridge = get_telemetry_bridge()
        s = bridge.start_span("mcp_parity_span")
        bridge.end_span(s)

        raw = handle_trace_query({"limit": 5})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["data"]["total_spans"] >= 1
        assert "spans" in data["data"]

    def test_core_mcp_server_telemetry_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        metrics_raw = server._handle_telemetry_metrics(format_type="json")
        metrics_data = json.loads(metrics_raw)
        assert metrics_data["ok"] is True

        traces_raw = server._handle_trace_query(limit=5)
        traces_data = json.loads(traces_raw)
        assert traces_data["ok"] is True


class TestAstCoreBoundary:
    """Verify strict standard-library-only rule for telemetry_bridge.py."""

    FORBIDDEN_MODULES = {
        "anthropic",
        "openai",
        "requests",
        "httpx",
        "fastapi",
        "pydantic",
        "aiohttp",
        "numpy",
        "torch",
        "prometheus_client",
        "opentelemetry",
    }

    def test_pure_standard_library_imports(self):
        rel_path = "src/core/telemetry_bridge.py"
        full_path = Path(__file__).resolve().parents[1] / rel_path
        assert full_path.exists(), f"File {rel_path} does not exist"

        tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden import '{alias.name}' found in {rel_path} (line {node.lineno})"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden from-import '{node.module}' found in {rel_path} (line {node.lineno})"
                    )
