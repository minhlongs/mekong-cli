# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Foreign Direct Investment (FDI) & SBV Capital Compliance Engine (Phase 48)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.fdi_engine import (
    MARKET_ACCESS_REGIME,
    TREATIES,
    FDIEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestFDICoreBoundary:
    """Ensure FDIEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/fdi_engine.py")
        assert source_path.exists(), "fdi_engine.py must exist"

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


class TestFDIEngine:
    """Test FDIEngine business logic and database persistence."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> FDIEngine:
        db_file = tmp_path / "test_fdi.db"
        return FDIEngine(db_path=db_file)

    def test_market_access_regimes_and_treaties(self) -> None:
        assert "6201" in MARKET_ACCESS_REGIME
        assert "8411" in MARKET_ACCESS_REGIME
        assert "WTO" in TREATIES
        assert "CPTPP" in TREATIES
        assert "EVFTA" in TREATIES

    def test_evaluate_market_access_permitted(self, engine: FDIEngine) -> None:
        res = engine.evaluate_market_access(sector_code="6201", investor_nationality="US", ownership_pct=100.0)
        assert res["ok"] is True
        assert res["is_compliant"] is True
        assert res["regime"] == "PERMITTED"
        assert res["foreign_ownership_cap_pct"] == 100.0
        assert len(res["applicable_treaties"]) >= 3

    def test_evaluate_market_access_conditional_and_over_cap(self, engine: FDIEngine) -> None:
        res = engine.evaluate_market_access(sector_code="6810", investor_nationality="SG", ownership_pct=75.0)
        assert res["ok"] is True
        assert res["regime"] == "CONDITIONAL"
        assert res["foreign_ownership_cap_pct"] == 50.0
        assert res["is_compliant"] is False
        assert any("exceeds statutory cap" in w for w in res["warnings"])

    def test_evaluate_market_access_prohibited(self, engine: FDIEngine) -> None:
        res = engine.evaluate_market_access(sector_code="8411", investor_nationality="DE", ownership_pct=10.0)
        assert res["ok"] is True
        assert res["regime"] == "PROHIBITED"
        assert res["is_compliant"] is False

    def test_verify_profit_remittance_eligible(self, engine: FDIEngine) -> None:
        res = engine.verify_profit_remittance(
            fiscal_year=2025,
            audited_profit_vnd=1_000_000_000,
            tax_cleared=True,
            retained_reserve_pct=5.0,
            dica_verified=True,
            losses_carried_forward_vnd=0,
        )
        assert res["ok"] is True
        assert res["is_eligible"] is True
        assert res["legal_reserve_vnd"] == 50_000_000
        assert res["net_distributable_profit_vnd"] == 950_000_000
        assert res["eligible_remittance_vnd"] == 950_000_000

    def test_verify_profit_remittance_ineligible_tax_and_dica(self, engine: FDIEngine) -> None:
        res = engine.verify_profit_remittance(
            fiscal_year=2025,
            audited_profit_vnd=2_000_000_000,
            tax_cleared=False,
            dica_verified=False,
            losses_carried_forward_vnd=500_000_000,
        )
        assert res["ok"] is True
        assert res["is_eligible"] is False
        assert len(res["rejection_reasons"]) >= 3
        assert res["eligible_remittance_vnd"] == 0.0

    def test_evaluate_foreign_loan_short_term(self, engine: FDIEngine) -> None:
        res = engine.evaluate_foreign_loan(
            loan_amount=200_000,
            currency="USD",
            tenure_months=6,
            interest_rate_pct=5.0,
            project_capital_gap=300_000,
        )
        assert res["ok"] is True
        assert res["loan_category"] == "SHORT_TERM"
        assert res["sbv_registration_required"] is False
        assert res["is_compliant"] is True

    def test_evaluate_foreign_loan_medium_long_term(self, engine: FDIEngine) -> None:
        res = engine.evaluate_foreign_loan(
            loan_amount=500_000,
            currency="USD",
            tenure_months=36,
            interest_rate_pct=6.5,
            project_capital_gap=600_000,
        )
        assert res["ok"] is True
        assert res["loan_category"] == "MEDIUM_LONG_TERM"
        assert res["sbv_registration_required"] is True
        assert res["is_compliant"] is True
        assert "Circular 12/2022/TT-NHNN" in res["registration_timeline"]

    def test_evaluate_foreign_loan_exceeding_gap(self, engine: FDIEngine) -> None:
        res = engine.evaluate_foreign_loan(
            loan_amount=1_000_000,
            currency="USD",
            tenure_months=24,
            interest_rate_pct=7.0,
            project_capital_gap=800_000,
        )
        assert res["ok"] is True
        assert res["is_compliant"] is False
        assert any("exceeds permitted project investment gap" in c for c in res["conditions"])

    def test_generate_irc_dossier_and_status(self, engine: FDIEngine) -> None:
        dossier = engine.generate_irc_dossier(
            project_name="Trung Tâm Nghiên Cứu AI Quốc Tế",
            sector_code="6201",
            total_investment_vnd=5_000_000_000,
            investor_name="Silicon Horizon Corp",
            investor_country="US",
            project_location="Khu Công Nghệ Cao TP.HCM",
        )
        assert dossier["ok"] is True
        assert dossier["total_investment_vnd"] == 5_000_000_000
        assert dossier["sector_code"] == "6201"
        assert dossier["required_documents_count"] == 6
        assert len(dossier["documents"]) == 6

        # Check list
        filings = engine.list_irc_dossiers()
        assert len(filings) >= 1
        assert filings[0]["project_name"] == "Trung Tâm Nghiên Cứu AI Quốc Tế"

        # Check status
        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "FDIEngine"
        assert status["total_irc_dossiers"] >= 1
        assert "Law on Investment 2020" in status["legal_framework"]["investment_law"]


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestFDICLI:
    """Test CLI commands for mekong fdi."""

    def test_fdi_overview(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ ĐẦU TƯ TRỰC TIẾP NƯỚC NGOÀI" in result.output

    def test_fdi_overview_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_fdi_market_access_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "market-access", "6201"])
        assert result.exit_code == 0
        assert "ĐIỀU KIỆN TIẾP CẬN THỊ TRƯỜNG FDI" in result.output

    def test_fdi_market_access_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "market-access", "6201", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["sector_code"] == "6201"
        assert data["access_status"] == "PERMITTED"

    def test_fdi_remittance_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "remittance", "100000", "2025", "--audited", "--tax-cleared"])
        assert result.exit_code == 0
        assert "THẨM ĐỊNH HỒ SƠ CHUYỂN LỢI NHUẬN" in result.output

    def test_fdi_remittance_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "remittance", "100000", "2025", "--audited", "--tax-cleared", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_eligible"] is True
        assert data["amount_usd"] == 100000.0

    def test_fdi_foreign_loan_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "foreign-loan", "500000", "24", "6.5"])
        assert result.exit_code == 0
        assert "THẨM ĐỊNH KHOẢN VAY NƯỚC NGOÀI" in result.output

    def test_fdi_foreign_loan_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "foreign-loan", "500000", "24", "6.5", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["sbv_registration_required"] is True
        assert data["is_compliant"] is True

    def test_fdi_irc_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "irc", "Mekong AI Lab", "100000", "--sector", "6201"])
        assert result.exit_code == 0
        assert "HỒ SƠ XIN CẤP GIẤY CHỨNG NHẬN ĐẦU TƯ" in result.output

    def test_fdi_irc_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "irc", "Mekong AI Lab", "100000", "--sector", "6201", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["project_name"] == "Mekong AI Lab"
        assert data["required_documents_count"] == 6

    def test_fdi_status_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "status"])
        assert result.exit_code == 0
        assert "THÔNG SỐ QUẢN TRỊ DÒNG VỐN ĐẦU TƯ FDI" in result.output

    def test_fdi_status_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["fdi", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["engine"] == "FDIEngine"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestFDIMCPParity:
    """Test MCP tool parity on FastMCP and standard JSON-RPC handlers."""

    def test_core_mcp_server_fdi_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        srv = MekongMcpServer()
        res_access = json.loads(srv._handle_fdi_market_access(sector_code="6201"))
        assert res_access["ok"] is True
        assert res_access["regime"] == "PERMITTED"

        res_remit = json.loads(srv._handle_fdi_remittance(fiscal_year=2025, audited_profit_vnd=500_000_000))
        assert res_remit["ok"] is True
        assert res_remit["eligible_remittance_vnd"] == 475_000_000

        res_loan = json.loads(srv._handle_fdi_foreign_loan(loan_amount=100_000, tenure_months=12))
        assert res_loan["ok"] is True

        res_irc = json.loads(
            srv._handle_fdi_irc(
                project_name="AI Hub",
                sector_code="6201",
                total_investment_vnd=1_000_000_000,
                investor_name="InvestCo",
            )
        )
        assert res_irc["ok"] is True

        res_status = json.loads(srv._handle_fdi_status())
        assert res_status["ok"] is True
        assert res_status["engine"] == "FDIEngine"

    def test_scripts_mcp_server_fdi_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_fdi_foreign_loan,
            handle_fdi_irc,
            handle_fdi_market_access,
            handle_fdi_remittance,
            handle_fdi_status,
        )

        res_access = json.loads(handle_fdi_market_access({"sector_code": "6201"}))
        assert res_access["ok"] is True

        res_remit = json.loads(handle_fdi_remittance({"fiscal_year": 2025, "audited_profit_vnd": 800_000_000}))
        assert res_remit["ok"] is True

        res_loan = json.loads(handle_fdi_foreign_loan({"loan_amount": 300_000, "tenure_months": 24}))
        assert res_loan["ok"] is True
        assert res_loan["sbv_registration_required"] is True

        res_irc = json.loads(
            handle_fdi_irc(
                {
                    "project_name": "Cloud Infra",
                    "sector_code": "6311",
                    "total_investment_vnd": 10_000_000_000,
                    "investor_name": "Cloud Corp",
                }
            )
        )
        assert res_irc["ok"] is True

        res_status = json.loads(handle_fdi_status({}))
        assert res_status["ok"] is True
        assert res_status["engine"] == "FDIEngine"
