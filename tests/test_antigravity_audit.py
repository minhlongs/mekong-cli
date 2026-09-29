# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Enterprise SOX 404, ITGC & Internal Controls Audit Engine (Phase 45)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.sox_audit_engine import (
    CANONICAL_CONTROLS,
    SoxAuditEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestSoxAuditCoreBoundary:
    """Ensure SoxAuditEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/sox_audit_engine.py")
        assert source_path.exists(), "sox_audit_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestSoxAuditEngine:
    """Test SoxAuditEngine methods and business logic."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> SoxAuditEngine:
        db_file = tmp_path / "test_audit.db"
        return SoxAuditEngine(db_path=db_file)

    def test_canonical_controls_catalog(self, engine: SoxAuditEngine) -> None:
        assert len(CANONICAL_CONTROLS) >= 8
        domains = {c["domain"] for c in CANONICAL_CONTROLS}
        assert domains == {"AC", "CM", "CO", "SD"}

    def test_list_controls_filtering(self, engine: SoxAuditEngine) -> None:
        all_controls = engine.list_controls()
        assert len(all_controls) == len(CANONICAL_CONTROLS)

        ac_controls = engine.list_controls(domain="AC")
        assert len(ac_controls) >= 2
        assert all(c["domain"] == "AC" for c in ac_controls)

        sox_controls = engine.list_controls(framework="SOX")
        assert len(sox_controls) >= 4
        assert all(c["framework"] == "SOX" for c in sox_controls)

        cm_itgc = engine.list_controls(domain="CM", framework="ITGC")
        assert len(cm_itgc) >= 2
        assert all(c["domain"] == "CM" and c["framework"] == "ITGC" for c in cm_itgc)

    def test_run_audit_all_frameworks(self, engine: SoxAuditEngine) -> None:
        res = engine.run_audit(framework="all", save=True)
        assert res["ok"] is True
        assert res["total_controls_tested"] >= 8
        assert res["compliance_score"] >= 0.0
        assert "audit_id" in res
        assert "audit_opinion" in res
        assert len(res["test_results"]) == res["total_controls_tested"]

    def test_run_audit_sox_only(self, engine: SoxAuditEngine) -> None:
        res = engine.run_audit(framework="sox", save=True)
        assert res["ok"] is True
        assert res["framework"] == "SOX"
        assert res["total_controls_tested"] >= 4

    def test_run_audit_itgc_only(self, engine: SoxAuditEngine) -> None:
        res = engine.run_audit(framework="itgc", save=True)
        assert res["ok"] is True
        assert res["framework"] == "ITGC"
        assert res["total_controls_tested"] >= 4

    def test_list_findings_and_status(self, engine: SoxAuditEngine) -> None:
        # Run audit to populate database
        engine.run_audit(framework="all", save=True)

        findings = engine.list_findings()
        assert isinstance(findings, list)

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_audit_runs"] >= 1
        assert status["total_controls_in_catalog"] >= 8
        assert "latest_compliance_score" in status
        assert "latest_audit_opinion" in status


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestSoxAuditCLI:
    """Test Typer CLI commands for audit."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_audit_overview(self, app) -> None:
        result = runner.invoke(app, ["audit"])
        assert result.exit_code == 0
        assert "HỆ THỐNG KIỂM TOÁN NỘI BỘ SOX 404 & ITGC" in result.output

    def test_audit_overview_json(self, app) -> None:
        result = runner.invoke(app, ["audit", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "total_controls_in_catalog" in data

    def test_audit_run_cli(self, app) -> None:
        result = runner.invoke(app, ["audit", "run", "--framework", "all"])
        assert result.exit_code == 0
        assert "KẾT QUẢ KIỂM TOÁN NỘI BỘ" in result.output

    def test_audit_run_cli_json(self, app) -> None:
        result = runner.invoke(app, ["audit", "run", "--framework", "sox", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["framework"] == "SOX"

    def test_audit_controls_cli(self, app) -> None:
        result = runner.invoke(app, ["audit", "controls", "--domain", "AC"])
        assert result.exit_code == 0
        assert "Segregation of" in result.output

    def test_audit_controls_cli_json(self, app) -> None:
        result = runner.invoke(app, ["audit", "controls", "--domain", "CM", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "controls" in data
        assert any(c["control_id"] == "CTRL-CM-01" for c in data["controls"])

    def test_audit_findings_cli(self, app) -> None:
        result = runner.invoke(app, ["audit", "findings"])
        assert result.exit_code == 0

    def test_audit_findings_cli_json(self, app) -> None:
        result = runner.invoke(app, ["audit", "findings", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "findings" in data
        assert isinstance(data["findings"], list)

    def test_audit_status_cli(self, app) -> None:
        result = runner.invoke(app, ["audit", "status"])
        assert result.exit_code == 0
        assert "TRẠNG THÁI HỆ THỐNG KIỂM TOÁN NỘI BỘ" in result.output

    def test_audit_status_cli_json(self, app) -> None:
        result = runner.invoke(app, ["audit", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestSoxAuditMCPParity:
    """Test FastMCP and scripts/mcp_server.py parity for audit tools."""

    def test_scripts_mcp_handlers(self) -> None:
        import scripts.mcp_server as smcp

        run_res = json.loads(smcp.handle_audit_run({"framework": "sox"}))
        assert run_res["ok"] is True
        assert run_res["framework"] == "SOX"

        ctrl_res = json.loads(smcp.handle_audit_controls({"domain": "AC"}))
        assert ctrl_res["ok"] is True
        assert ctrl_res["total"] >= 2

        find_res = json.loads(smcp.handle_audit_findings({}))
        assert find_res["ok"] is True

        stat_res = json.loads(smcp.handle_audit_status({}))
        assert stat_res["status"] == "operational"

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        run_res = json.loads(server._handle_audit_run(framework="itgc"))
        assert run_res["ok"] is True
        assert run_res["framework"] == "ITGC"

        ctrl_res = json.loads(server._handle_audit_controls(domain="CM"))
        assert ctrl_res["ok"] is True
        assert ctrl_res["total"] >= 2

        find_res = json.loads(server._handle_audit_findings())
        assert find_res["ok"] is True

        stat_res = json.loads(server._handle_audit_status())
        assert stat_res["status"] == "operational"
