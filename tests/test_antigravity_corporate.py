# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Corporate Governance & Incorporation Engine (Phase 47)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.corporate_engine import (
    CANONICAL_VSIC,
    ENTITY_TYPE_NAMES,
    CorporateEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestCorporateCoreBoundary:
    """Ensure CorporateEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/corporate_engine.py")
        assert source_path.exists(), "corporate_engine.py must exist"

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


class TestCorporateEngine:
    """Test CorporateEngine document synthesis and database operations."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> CorporateEngine:
        db_file = tmp_path / "test_corporate.db"
        return CorporateEngine(db_path=db_file)

    def test_canonical_vsic_and_entities(self) -> None:
        assert "6201" in CANONICAL_VSIC
        assert "6202" in CANONICAL_VSIC
        assert "TNHH_1TV" in ENTITY_TYPE_NAMES
        assert "JSC" in ENTITY_TYPE_NAMES

    def test_generate_charter(self, engine: CorporateEngine) -> None:
        res = engine.generate_charter(
            company_name="Công Ty TNHH AI Mekong",
            entity_type="TNHH_1TV",
            charter_capital=2_000_000_000,
            legal_rep_name="Trần Văn B",
            address="123 Phố Huế, Hai Bà Trưng, Hà Nội",
        )
        assert res["ok"] is True
        assert res["chapters_count"] == 10
        assert res["articles_count"] == 18
        assert "CHƯƠNG I: QUY ĐỊNH CHUNG" in res["content_markdown"]
        assert "CHƯƠNG VI: NGƯỜI ĐẠI DIỆN THEO PHÁP LUẬT" in res["content_markdown"]
        assert res["charter_capital"] == 2_000_000_000

    def test_generate_resolution(self, engine: CorporateEngine) -> None:
        res = engine.generate_resolution(
            company_name="Công Ty Cổ Phần Công Nghệ Mekong",
            resolution_type="APPOINTMENT",
            title="Nghị Quyết Bổ Nhiệm Tổng Giám Đốc",
        )
        assert res["ok"] is True
        assert res["resolution_type"] == "APPOINTMENT"
        assert res["decisions_count"] >= 3
        assert "QUYẾT NGHỊ:" in res["content_markdown"]

    def test_create_filing_dossier_and_status(self, engine: CorporateEngine) -> None:
        dossier = engine.create_filing_dossier(
            company_name="Công Ty TNHH Giải Pháp Số Mekong",
            entity_type="TNHH_2TV",
            charter_capital=5_000_000_000,
            legal_rep_name="Lê Thị C",
            address="Quận 1, TP. Hồ Chí Minh",
            main_industry="6201",
        )
        assert dossier["ok"] is True
        assert len(dossier["documents"]) >= 4
        assert dossier["filing_portal"] == "https://dangkykinhdoanh.gov.vn"

        filings = engine.list_filings()
        assert len(filings) >= 2  # Charter + Resolution

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["metrics"]["registered_entities"] >= 1
        assert status["metrics"]["total_charter_capital_vnd"] >= 5_000_000_000


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestCorporateCLI:
    """Test Typer CLI commands for corporate governance."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_corporate_overview(self, app) -> None:
        result = runner.invoke(app, ["corporate"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN TRỊ DOANH NGHIỆP" in result.output

    def test_corporate_overview_json(self, app) -> None:
        result = runner.invoke(app, ["corporate", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "governance_framework" in data

    def test_corporate_charter_cli(self, app) -> None:
        result = runner.invoke(app, ["corporate", "charter", "Công Ty TNHH Test", "--type", "TNHH_1TV"])
        assert result.exit_code == 0
        assert "ĐIỀU LỆ HOẠT ĐỘNG DOANH NGHIỆP" in result.output

    def test_corporate_charter_cli_json(self, app) -> None:
        result = runner.invoke(app, ["corporate", "charter", "Công Ty TNHH Test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "charter_id" in data
        assert data["chapters_count"] == 10

    def test_corporate_resolution_cli(self, app) -> None:
        result = runner.invoke(app, ["corporate", "resolution", "Công Ty Test", "--type", "APPOINTMENT"])
        assert result.exit_code == 0
        assert "NGHỊ QUYẾT PHÁP LÝ" in result.output

    def test_corporate_resolution_cli_json(self, app) -> None:
        result = runner.invoke(app, ["corporate", "resolution", "Công Ty Test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "resolution_id" in data

    def test_corporate_dossier_cli(self, app) -> None:
        result = runner.invoke(app, ["corporate", "dossier", "Công Ty TNHH Startup Mekong"])
        assert result.exit_code == 0
        assert "BỘ HỒ SƠ ĐĂNG KÝ DOANH NGHIỆP" in result.output

    def test_corporate_dossier_cli_json(self, app) -> None:
        result = runner.invoke(app, ["corporate", "dossier", "Công Ty TNHH Startup Mekong", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "dossier_id" in data
        assert len(data["documents"]) >= 4

    def test_corporate_list_cli(self, app) -> None:
        result = runner.invoke(app, ["corporate", "list"])
        assert result.exit_code == 0

    def test_corporate_list_cli_json(self, app) -> None:
        result = runner.invoke(app, ["corporate", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "filings" in data

    def test_corporate_status_cli(self, app) -> None:
        result = runner.invoke(app, ["corporate", "status"])
        assert result.exit_code == 0
        assert "TRẠNG THÁI CƠ SỞ PHÁP LÝ DOANH NGHIỆP" in result.output

    def test_corporate_status_cli_json(self, app) -> None:
        result = runner.invoke(app, ["corporate", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestCorporateMCPParity:
    """Test FastMCP and scripts/mcp_server.py parity for corporate tools."""

    def test_scripts_mcp_handlers(self) -> None:
        import scripts.mcp_server as smcp

        ch = json.loads(smcp.handle_corporate_charter({"company_name": "Công Ty A"}))
        assert ch["ok"] is True
        assert ch["chapters_count"] == 10

        res = json.loads(smcp.handle_corporate_resolution({"company_name": "Công Ty A"}))
        assert res["ok"] is True

        dos = json.loads(smcp.handle_corporate_dossier({"company_name": "Công Ty B"}))
        assert dos["ok"] is True

        flist = json.loads(smcp.handle_corporate_list({}))
        assert flist["ok"] is True

        cstat = json.loads(smcp.handle_corporate_status({}))
        assert cstat["status"] == "operational"

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        ch = json.loads(server._handle_corporate_charter(company_name="Công Ty C"))
        assert ch["ok"] is True
        assert ch["chapters_count"] == 10

        res = json.loads(server._handle_corporate_resolution(company_name="Công Ty C"))
        assert res["ok"] is True

        dos = json.loads(server._handle_corporate_dossier(company_name="Công Ty D"))
        assert dos["ok"] is True

        flist = json.loads(server._handle_corporate_list())
        assert flist["ok"] is True

        cstat = json.loads(server._handle_corporate_status())
        assert cstat["status"] == "operational"
