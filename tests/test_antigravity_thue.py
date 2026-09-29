# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Vietnamese Tax Calculation, Progressive Deductions & Filing Simulation Engine (Phase 39)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_TOOLS_SPEC,
    handle_thue_gtgt,
    handle_thue_status,
    handle_thue_tncn,
    handle_thue_tndn,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
from src.core.thue_engine import (
    CANONICAL_TAX_PROFILES,
    PERSONAL_DEDUCTION,
    DEPENDENT_DEDUCTION,
    TNDN_SME_THRESHOLD,
    ThueEngine,
    format_vnd,
)

runner = CliRunner()


class TestThueEngine:
    """Unit test battery for ThueEngine core logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> ThueEngine:
        db_file = tmp_path / "test_thue.db"
        return ThueEngine(db_path=db_file)

    def test_engine_init_and_default_profiles(self, engine: ThueEngine) -> None:
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_profiles"] == len(CANONICAL_TAX_PROFILES)
        assert status["total_calculations"] == 0
        assert status["total_tax_simulated"] == 0.0

    def test_format_vnd(self) -> None:
        formatted = format_vnd(15000000)
        assert "15.000.000 đ" in formatted

    def test_calculate_tncn_zero_taxable(self, engine: ThueEngine) -> None:
        # Income <= 11M (personal deduction)
        res = engine.calculate_tncn(monthly_income=10000000, dependents=0)
        assert res["tax_type"] == "tncn"
        assert res["gross_income"] == 10000000.0
        assert res["personal_deduction"] == float(PERSONAL_DEDUCTION)
        assert res["total_deductions"] == float(PERSONAL_DEDUCTION)
        assert res["taxable_income"] == 0.0
        assert res["tax_amount"] == 0.0
        assert res["net_income"] == 10000000.0
        assert res["effective_rate_pct"] == 0.0
        assert len(res["breakdown"]) == 0

    def test_calculate_tncn_progressive_tiers(self, engine: ThueEngine) -> None:
        # Income: 20M, 0 dependents
        # Taxable = 20M - 11M = 9M
        # Bracket 1 (0 - 5M): 5M * 5% = 250,000 đ
        # Bracket 2 (5M - 10M): 4M * 10% = 400,000 đ
        # Total tax = 650,000 đ
        res = engine.calculate_tncn(monthly_income=20000000, dependents=0)
        assert res["taxable_income"] == 9000000.0
        assert res["tax_amount"] == 650000.0
        assert res["net_income"] == 19350000.0
        assert res["effective_rate_pct"] == 3.25
        assert len(res["breakdown"]) == 2
        assert res["breakdown"][0]["tax"] == 250000.0
        assert res["breakdown"][1]["tax"] == 400000.0

    def test_calculate_tncn_with_dependents(self, engine: ThueEngine) -> None:
        # Income: 30M, 2 dependents
        # Total deduction = 11M + 2 * 4.4M = 19.8M
        # Taxable = 30M - 19.8M = 10.2M
        # Bracket 1 (5M): 5M * 5% = 250,000 đ
        # Bracket 2 (5M): 5M * 10% = 500,000 đ
        # Bracket 3 (0.2M): 200,000 * 15% = 30,000 đ
        # Total tax = 780,000 đ
        res = engine.calculate_tncn(monthly_income=30000000, dependents=2)
        assert res["dependent_deduction"] == float(2 * DEPENDENT_DEDUCTION)
        assert res["total_deductions"] == 19800000.0
        assert res["taxable_income"] == 10200000.0
        assert res["tax_amount"] == 780000.0
        assert len(res["breakdown"]) == 3

    def test_calculate_tndn_sme_rate(self, engine: ThueEngine) -> None:
        # Revenue 2B VND (<= 3B threshold), profit = 200M VND, SME incentive = 17%
        res = engine.calculate_tndn(annual_revenue=2000000000, profit=200000000, is_sme=True)
        assert res["tax_type"] == "tndn"
        assert res["is_sme_incentive"] is True
        assert res["applied_rate_pct"] == 17.0
        assert res["taxable_profit"] == 200000000.0
        assert res["tax_amount"] == 34000000.0
        assert res["net_profit"] == 166000000.0

    def test_calculate_tndn_standard_rate(self, engine: ThueEngine) -> None:
        # Revenue 10B VND (> 3B threshold), profit = 1B VND, standard rate = 20%
        res = engine.calculate_tndn(annual_revenue=10000000000, profit=1000000000, is_sme=True)
        assert res["is_sme_incentive"] is False
        assert res["applied_rate_pct"] == 20.0
        assert res["tax_amount"] == 200000000.0
        assert res["net_profit"] == 800000000.0

    def test_calculate_tndn_default_profit_estimation(self, engine: ThueEngine) -> None:
        # If profit is None, estimated at 15% of revenue
        res = engine.calculate_tndn(annual_revenue=1000000000, profit=None, is_sme=True)
        assert res["taxable_profit"] == 150000000.0
        assert res["tax_amount"] == 25500000.0

    def test_calculate_gtgt_various_rates(self, engine: ThueEngine) -> None:
        # 10% standard rate
        res_10 = engine.calculate_gtgt(amount=100000000, rate=10)
        assert res_10["tax_type"] == "gtgt"
        assert res_10["subtotal"] == 100000000.0
        assert res_10["vat_rate_pct"] == 10
        assert res_10["vat_amount"] == 10000000.0
        assert res_10["total_inclusive"] == 110000000.0

        # 8% preferential rate
        res_8 = engine.calculate_gtgt(amount=50000000, rate=8)
        assert res_8["vat_rate_pct"] == 8
        assert res_8["vat_amount"] == 4000000.0
        assert res_8["total_inclusive"] == 54000000.0

        # 0% export rate
        res_0 = engine.calculate_gtgt(amount=200000000, rate=0)
        assert res_0["vat_rate_pct"] == 0
        assert res_0["vat_amount"] == 0.0
        assert res_0["total_inclusive"] == 200000000.0

    def test_list_and_status_telemetry(self, engine: ThueEngine) -> None:
        engine.calculate_tncn(monthly_income=25000000, dependents=1)
        engine.calculate_tndn(annual_revenue=1500000000, profit=150000000)
        engine.calculate_gtgt(amount=80000000, rate=10)

        all_calcs = engine.list_calculations(tax_type="all")
        assert len(all_calcs) == 3

        tncn_only = engine.list_calculations(tax_type="tncn")
        assert len(tncn_only) == 1
        assert tncn_only[0]["tax_type"] == "tncn"

        status = engine.get_status()
        assert status["total_calculations"] == 3
        assert status["total_tax_simulated"] > 0
        assert "tncn" in status["type_breakdown"]
        assert "tndn" in status["type_breakdown"]
        assert "gtgt" in status["type_breakdown"]


class TestThueCli:
    """CLI test battery for mekong thue commands."""

    @pytest.fixture
    def app(self) -> typing.Any:
        return build_app()

    def test_thue_overview_plain(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue"])
        assert res.exit_code == 0
        assert "VIETNAMESE TAX SIMULATION & COMPLIANCE ENGINE" in res.output or "Thuế" in res.output

    def test_thue_overview_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "status" in data
        assert "statutory_regulations" in data
        assert data["status"] == "operational"

    def test_thue_status_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "total_calculations" in data
        assert "total_profiles" in data

    def test_thue_tncn_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "tncn", "35000000", "--dependents", "1", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["tax_type"] == "tncn"
        assert data["gross_income"] == 35000000.0
        assert "tax_amount" in data
        assert "net_income" in data

    def test_thue_tncn_console(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "tncn", "25000000", "--dependents", "0"])
        assert res.exit_code == 0
        assert "TÍNH THUẾ TNCN" in res.output

    def test_thue_tndn_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "tndn", "1500000000", "--profit", "250000000", "--sme", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["tax_type"] == "tndn"
        assert data["is_sme_incentive"] is True
        assert data["applied_rate_pct"] == 17.0

    def test_thue_tndn_console(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "tndn", "4000000000", "--profit", "600000000"])
        assert res.exit_code == 0
        assert "TÍNH THUẾ TNDN" in res.output

    def test_thue_gtgt_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "gtgt", "100000000", "--rate", "8", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["tax_type"] == "gtgt"
        assert data["vat_rate_pct"] == 8
        assert data["vat_amount"] == 8000000.0

    def test_thue_gtgt_console(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "gtgt", "50000000", "--rate", "10"])
        assert res.exit_code == 0
        assert "Thuế GTGT" in res.output

    def test_thue_list_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "list", "--type", "all", "--limit", "10", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestThueMcpParity:
    """Parity tests for FastMCP and JSON-RPC fallback handlers."""

    def test_scripts_mcp_tools_spec_registered(self) -> None:
        tool_names = [tool["name"] for tool in CORE_TOOLS_SPEC]
        assert "mekong_thue_tncn" in tool_names
        assert "mekong_thue_tndn" in tool_names
        assert "mekong_thue_gtgt" in tool_names
        assert "mekong_thue_status" in tool_names

    def test_scripts_mcp_handlers(self) -> None:
        # TNCN
        res_raw = handle_thue_tncn({"monthly_income": 25000000, "dependents": 1})
        res_tncn = json.loads(res_raw)
        assert res_tncn["tax_type"] == "tncn"
        assert res_tncn["gross_income"] == 25000000.0

        # TNDN
        res_raw = handle_thue_tndn({"annual_revenue": 2000000000, "profit": 200000000, "is_sme": True})
        res_tndn = json.loads(res_raw)
        assert res_tndn["tax_type"] == "tndn"
        assert res_tndn["is_sme_incentive"] is True

        # GTGT
        res_raw = handle_thue_gtgt({"amount": 100000000, "rate": 10})
        res_gtgt = json.loads(res_raw)
        assert res_gtgt["tax_type"] == "gtgt"
        assert res_gtgt["vat_amount"] == 10000000.0

        # Status
        res_raw = handle_thue_status({})
        res_status = json.loads(res_raw)
        assert res_status["status"] == "operational"
        assert "total_calculations" in res_status

    def test_core_mcp_server_handlers(self) -> None:
        server = MekongMcpServer()
        res_raw = server._handle_thue_tncn(monthly_income=30000000, dependents=0)
        res_tncn = json.loads(res_raw)
        assert res_tncn["tax_type"] == "tncn"

        res_raw = server._handle_thue_tndn(annual_revenue=5000000000, profit=500000000)
        res_tndn = json.loads(res_raw)
        assert res_tndn["tax_type"] == "tndn"

        res_raw = server._handle_thue_gtgt(amount=50000000, rate=8)
        res_gtgt = json.loads(res_raw)
        assert res_gtgt["tax_type"] == "gtgt"

        res_raw = server._handle_thue_status()
        res_status = json.loads(res_raw)
        assert res_status["status"] == "operational"


class TestThueCoreBoundary:
    """Enforce strict standard-library-only core boundary on thue_engine.py."""

    def test_thue_engine_standard_library_only(self) -> None:
        target_path = Path("src/core/thue_engine.py")
        assert target_path.exists()

        tree = ast.parse(target_path.read_text(encoding="utf-8"))
        allowed_modules = {
            "__future__",
            "datetime",
            "decimal",
            "json",
            "pathlib",
            "sqlite3",
            "typing",
            "uuid",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg in allowed_modules, f"Disallowed import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg in allowed_modules, f"Disallowed from-import: {node.module}"
