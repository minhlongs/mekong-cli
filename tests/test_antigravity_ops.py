# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_ops.py — Comprehensive test suite for Autonomous Operations & Incident Response Suite.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.ops_engine import (
    DrPlanReport,
    HealthSweepReport,
    IncidentRecord,
    MorningCheckReport,
    OpsEngine,
    PostmortemReport,
)

runner = CliRunner()


@pytest.fixture
def temp_ops_engine(tmp_path: Path) -> Generator[OpsEngine, None, None]:
    """Provide an isolated OpsEngine instance with a temporary database and workspace."""
    db_file = tmp_path / "ops_test.db"
    engine = OpsEngine(db_path=db_file, project_root=tmp_path)
    yield engine


class TestOpsEngineCore:
    """Unit tests for OpsEngine core business logic."""

    def test_health_sweep_report(self, temp_ops_engine: OpsEngine, tmp_path: Path) -> None:
        rep_dir = tmp_path / "reports"
        report = temp_ops_engine.health_sweep(save_report=True, output_dir=rep_dir)

        assert isinstance(report, HealthSweepReport)
        assert 0 <= report.score <= 100
        assert report.overall_status in {"HEALTHY", "DEGRADED", "CRITICAL"}
        assert len(report.checks) >= 4
        assert report.report_file is not None
        assert Path(report.report_file).exists()

        content = Path(report.report_file).read_text(encoding="utf-8")
        assert "# Mekong System Health Sweep Report" in content
        assert "Overall Status" in content

    def test_incident_lifecycle(self, temp_ops_engine: OpsEngine) -> None:
        # Create
        inc = temp_ops_engine.create_incident(
            title="Redis cache memory pressure",
            severity="SEV2",
            service="cache",
            summary="Eviction count increased sharply",
        )
        assert isinstance(inc, IncidentRecord)
        assert inc.id.startswith("INC-")
        assert inc.severity == "SEV2"
        assert inc.status == "OPEN"
        assert inc.resolved_at is None

        # Get
        retrieved = temp_ops_engine.get_incident(inc.id)
        assert retrieved is not None
        assert retrieved.title == inc.title

        # List
        all_incidents = temp_ops_engine.list_incidents()
        assert len(all_incidents) == 1
        assert all_incidents[0].id == inc.id

        # Update / Resolve
        resolved = temp_ops_engine.update_incident(
            incident_id=inc.id,
            status="RESOLVED",
            mitigation="Scaled Redis cache cluster memory by 2x",
            root_cause="Uncapped key expiration policy in task queue",
        )
        assert resolved is not None
        assert resolved.status == "RESOLVED"
        assert resolved.resolved_at is not None
        assert "Scaled Redis" in resolved.mitigation

        # Filter by status
        open_list = temp_ops_engine.list_incidents(status="OPEN")
        assert len(open_list) == 0
        res_list = temp_ops_engine.list_incidents(status="RESOLVED")
        assert len(res_list) == 1

    def test_postmortem_generation(self, temp_ops_engine: OpsEngine, tmp_path: Path) -> None:
        inc = temp_ops_engine.create_incident(
            title="Gateway latency spike",
            severity="SEV1",
            service="gateway",
            summary="P99 response time exceeded 2.5s",
        )
        temp_ops_engine.update_incident(
            incident_id=inc.id,
            status="RESOLVED",
            mitigation="Traffic shed applied and upstream connections cycled",
            root_cause="Connection leak in event streaming handler",
        )

        pm_dir = tmp_path / "postmortems"
        pm = temp_ops_engine.generate_postmortem(incident_id=inc.id, save_to_file=True, output_dir=pm_dir)

        assert isinstance(pm, PostmortemReport)
        assert pm.incident_id == inc.id
        assert pm.severity == "SEV1"
        assert len(pm.timeline) >= 3
        assert len(pm.action_items) >= 2
        assert pm.report_file is not None
        assert Path(pm.report_file).exists()

        content = Path(pm.report_file).read_text(encoding="utf-8")
        assert f"# SRE Blameless Postmortem: {inc.id}" in content
        assert "Root Cause Analysis" in content
        assert "Action Items" in content

    def test_morning_check(self, temp_ops_engine: OpsEngine) -> None:
        morning = temp_ops_engine.morning_check()
        assert isinstance(morning, MorningCheckReport)
        assert morning.system_status in {"READY", "ATTENTION_REQUIRED", "CRITICAL_ALERT"}
        assert 0 <= morning.health_score <= 100
        assert morning.open_incidents_count >= 0
        assert morning.disk_free_gb > 0
        assert len(morning.items) >= 3

    def test_dr_audit(self, temp_ops_engine: OpsEngine) -> None:
        dr = temp_ops_engine.dr_audit()
        assert isinstance(dr, DrPlanReport)
        assert 0 <= dr.readiness_score <= 100
        assert dr.status in {"READY", "ACCEPTABLE", "UNPREPARED"}
        assert dr.rto_target_minutes == 15
        assert dr.rpo_target_minutes == 60
        assert len(dr.steps) >= 4
        assert len(dr.backups_found) >= 1

    def test_get_status(self, temp_ops_engine: OpsEngine) -> None:
        status = temp_ops_engine.get_status()
        assert isinstance(status, dict)
        assert "health_score" in status
        assert "overall_status" in status
        assert "open_incidents" in status
        assert "dr_status" in status


class TestOpsCliCommands:
    """Integration tests for Typer CLI commands."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_ops_overview_json(self) -> None:
        res = runner.invoke(self.app, ["ops", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "health_score" in data
        assert "overall_status" in data
        assert "dr_status" in data

    def test_cli_ops_overview_console(self) -> None:
        res = runner.invoke(self.app, ["ops"])
        assert res.exit_code == 0
        assert "OPERATIONS & SRE CONTROL PLANE" in res.output or "Ops Layer Dashboard" in res.output

    def test_cli_ops_sweep_json(self) -> None:
        res = runner.invoke(self.app, ["ops", "sweep", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "overall_status" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)

    def test_cli_ops_sweep_save(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "custom_sweep"
        res = runner.invoke(self.app, ["ops", "sweep", "--save", "--output-dir", str(out_dir)])
        assert res.exit_code == 0
        assert out_dir.exists()
        reports = list(out_dir.glob("health_sweep_*.md"))
        assert len(reports) == 1

    def test_cli_ops_morning_json(self) -> None:
        res = runner.invoke(self.app, ["ops", "morning", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "system_status" in data
        assert "checklist_passed" in data

    def test_cli_ops_incident_lifecycle(self) -> None:
        # 1. Create incident
        create_res = runner.invoke(
            self.app,
            [
                "ops",
                "incident",
                "create",
                "API Gateway 502 Bad Gateway",
                "--severity",
                "SEV2",
                "--service",
                "gateway",
                "--summary",
                "Upstream timeout to worker service",
                "--json",
            ],
        )
        assert create_res.exit_code == 0
        inc_data = json.loads(create_res.output)
        inc_id = inc_data["id"]
        assert inc_id.startswith("INC-")
        assert inc_data["status"] == "OPEN"

        # 2. List incidents
        list_res = runner.invoke(self.app, ["ops", "incident", "list", "--json"])
        assert list_res.exit_code == 0
        inc_list = json.loads(list_res.output)
        assert any(i["id"] == inc_id for i in inc_list)

        # 3. Resolve incident with postmortem flag
        resolve_res = runner.invoke(
            self.app,
            [
                "ops",
                "incident",
                "resolve",
                inc_id,
                "--mitigation",
                "Restarted stalled worker pool",
                "--root-cause",
                "Worker deadlocked on locked SQLite record",
                "--postmortem",
                "--json",
            ],
        )
        assert resolve_res.exit_code == 0
        res_data = json.loads(resolve_res.output)
        assert res_data["status"] == "RESOLVED"
        assert "postmortem" in res_data
        assert res_data["postmortem"]["incident_id"] == inc_id

        # 4. Standalone postmortem
        pm_res = runner.invoke(self.app, ["ops", "incident", "postmortem", inc_id, "--json"])
        assert pm_res.exit_code == 0
        pm_data = json.loads(pm_res.output)
        assert pm_data["incident_id"] == inc_id
        assert "markdown_report" in pm_data

    def test_cli_ops_dr_json(self) -> None:
        res = runner.invoke(self.app, ["ops", "dr", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "readiness_score" in data
        assert "backups_found" in data
        assert "steps" in data


class TestOpsMcpTools:
    """Test parity for native MCP tools across FastMCP and fallback stdio engine."""

    def test_scripts_mcp_ops_tools(self) -> None:
        import scripts.mcp_server as mcp_scripts

        # Test health sweep
        sweep_out = mcp_scripts.handle_ops_health_sweep({"save_report": False})
        sweep = json.loads(sweep_out)
        assert "overall_status" in sweep
        assert "score" in sweep

        # Test incident create
        inc_out = mcp_scripts.handle_ops_incident_create({
            "title": "MCP test incident",
            "severity": "SEV3",
            "service": "mcp",
            "summary": "Integration validation",
        })
        inc = json.loads(inc_out)
        assert inc["id"].startswith("INC-")

        # Test incident list
        list_out = mcp_scripts.handle_ops_incident_list({"status": "ALL"})
        inc_list = json.loads(list_out)
        assert isinstance(inc_list, list)
        assert any(i["id"] == inc["id"] for i in inc_list)

    def test_core_mcp_ops_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        sweep_out = server._handle_ops_health_sweep(save_report=False)
        sweep = json.loads(sweep_out)
        assert "overall_status" in sweep

        inc_out = server._handle_ops_incident_create(title="Core MCP incident", severity="SEV4", service="test")
        inc = json.loads(inc_out)
        assert inc["id"].startswith("INC-")

        list_out = server._handle_ops_incident_list(status="ALL")
        inc_list = json.loads(list_out)
        assert isinstance(inc_list, list)


class TestOpsBoundary:
    """Ensure src/core/ops_engine.py complies with zero vendor SDK import boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        engine_file = Path(__file__).resolve().parents[1] / "src" / "core" / "ops_engine.py"
        assert engine_file.exists(), f"Missing {engine_file}"

        tree = ast.parse(engine_file.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "aiohttp", "openai", "anthropic", "google", "boto3", "psutil"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed module import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import module: {pkg}"
