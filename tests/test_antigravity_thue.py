# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Vietnamese Tax Calculation, Progressive Deductions & Filing Simulation Engine (Phase 39)."""

from __future__ import annotations

import ast
import json
import typing
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
        # Tax period 2025: personal relief 11M (Nghị quyết 954/2020/UBTVQH14)
        res = engine.calculate_tncn(monthly_income=10000000, dependents=0, as_of="2025-10-01")
        assert res["tax_type"] == "tncn"
        assert res["gross_income"] == 10000000.0
        assert res["personal_deduction"] == float(PERSONAL_DEDUCTION)
        assert res["total_deductions"] == float(PERSONAL_DEDUCTION)
        assert res["taxable_income"] == 0.0
        assert res["tax_amount"] == 0.0
        assert res["net_income"] == 10000000.0
        assert res["effective_rate_pct"] == 0.0
        assert len(res["breakdown"]) == 0

    def test_calculate_tncn_deductions_follow_the_tax_period(self, engine: ThueEngine) -> None:
        """14M/month is taxable in 2025 and tax-free from tax year 2026.

        Luật 109/2025/QH15 + Nghị quyết 110/2025/UBTVQH15 raise the personal
        relief to 15.5M and the dependent relief to 6.2M per person.
        """
        before = engine.calculate_tncn(monthly_income=14000000, dependents=0, as_of="2025-10-01")
        assert before["personal_deduction"] == 11000000.0
        assert before["taxable_income"] == 3000000.0
        assert before["tax_amount"] == 150000.0
        assert before["rule_version"] == "2020.07-2025.12"

        after = engine.calculate_tncn(monthly_income=14000000, dependents=0, as_of="2026-10-01")
        assert after["personal_deduction"] == 15500000.0
        assert after["taxable_income"] == 0.0
        assert after["tax_amount"] == 0.0
        assert after["rule_version"] == "2026.01-luat-109/2025/QH15"

    def test_calculate_tncn_progressive_tiers(self, engine: ThueEngine) -> None:
        # Tax period 2025 — 7-bracket schedule (Điều 22 Luật Thuế TNCN 2007)
        # Income: 20M, 0 dependents
        # Taxable = 20M - 11M = 9M
        # Bracket 1 (0 - 5M): 5M * 5% = 250,000 đ
        # Bracket 2 (5M - 10M): 4M * 10% = 400,000 đ
        # Total tax = 650,000 đ
        res = engine.calculate_tncn(monthly_income=20000000, dependents=0, as_of="2025-10-01")
        assert res["taxable_income"] == 9000000.0
        assert res["tax_amount"] == 650000.0
        assert res["net_income"] == 19350000.0
        assert res["effective_rate_pct"] == 3.25
        assert len(res["breakdown"]) == 2
        assert res["breakdown"][0]["tax"] == 250000.0
        assert res["breakdown"][1]["tax"] == 400000.0

    def test_calculate_tncn_uses_the_five_bracket_schedule_from_2026(self, engine: ThueEngine) -> None:
        # Tax year 2026 — Luật 109/2025/QH15 Điều 9: 5 brackets, first up to 10M @5%
        # Income 20M, 0 dependents -> taxable = 20M - 15.5M = 4.5M -> 4.5M * 5%
        res = engine.calculate_tncn(monthly_income=20000000, dependents=0, as_of="2026-10-01")
        assert res["rule_version"] == "2026.01-luat-109/2025/QH15"
        assert res["taxable_income"] == 4500000.0
        assert res["tax_amount"] == 225000.0
        assert len(res["breakdown"]) == 1
        assert res["net_income"] == 19775000.0

    def test_calculate_tncn_with_dependents(self, engine: ThueEngine) -> None:
        # Tax period 2025
        # Income: 30M, 2 dependents
        # Total deduction = 11M + 2 * 4.4M = 19.8M
        # Taxable = 30M - 19.8M = 10.2M
        # Bracket 1 (5M): 5M * 5% = 250,000 đ
        # Bracket 2 (5M): 5M * 10% = 500,000 đ
        # Bracket 3 (0.2M): 200,000 * 15% = 30,000 đ
        # Total tax = 780,000 đ
        res = engine.calculate_tncn(monthly_income=30000000, dependents=2, as_of="2025-10-01")
        assert res["dependent_deduction"] == float(2 * DEPENDENT_DEDUCTION)
        assert res["total_deductions"] == 19800000.0
        assert res["taxable_income"] == 10200000.0
        assert res["tax_amount"] == 780000.0
        assert len(res["breakdown"]) == 3

        # Tax year 2026: relief becomes 15.5M + 2 * 6.2M = 27.9M
        # Taxable = 30M - 27.9M = 2.1M -> 2.1M * 5% = 105,000 đ
        res_2026 = engine.calculate_tncn(monthly_income=30000000, dependents=2, as_of="2026-10-01")
        assert res_2026["dependent_deduction"] == 12400000.0
        assert res_2026["total_deductions"] == 27900000.0
        assert res_2026["taxable_income"] == 2100000.0
        assert res_2026["tax_amount"] == 105000.0
        assert len(res_2026["breakdown"]) == 1

    def test_calculate_tndn_sme_rate(self, engine: ThueEngine) -> None:
        """Điều 10 Luật 67/2025/QH15 (từ 01/10/2025): doanh thu <= 3 tỷ -> 15%.

        The 17% figure this test used to assert was never the small-enterprise
        rate: 17% belongs to the 3B < revenue <= 50B band, and neither band
        existed in the CIT law before 01/10/2025.
        """
        res = engine.calculate_tndn(annual_revenue=2000000000, profit=200000000,
                                    is_sme=True, as_of="2026-06-01")
        assert res["tax_type"] == "tndn"
        assert res["is_sme_incentive"] is True
        assert res["rate_tier"] == "SME_SMALL_15"
        assert res["applied_rate_pct"] == 15.0
        assert res["taxable_profit"] == 200000000.0
        assert res["tax_amount"] == 30000000.0
        assert res["net_profit"] == 170000000.0
        assert res["rule_version"] == "luat-67/2025/QH15"

        # The legacy 3B constant is the small-enterprise revenue ceiling of the
        # rule version in force — the engine resolves the band from the table.
        from decimal import Decimal

        from src.core.vn_statutory_rules import cit_rule

        params = cit_rule("2026-06-01").params
        assert params["sme_small_max_revenue"] == TNDN_SME_THRESHOLD == Decimal(3_000_000_000)
        assert params["sme_medium_max_revenue"] == Decimal(50_000_000_000)

    def test_calculate_tndn_sme_tiers_are_not_retroactive(self, engine: ThueEngine) -> None:
        """Before 01/10/2025 only the 20% standard rate applied."""
        res = engine.calculate_tndn(annual_revenue=2000000000, profit=200000000,
                                    is_sme=True, as_of="2025-06-01")
        assert res["is_sme_incentive"] is False
        assert res["rate_tier"] == "STANDARD_20"
        assert res["applied_rate_pct"] == 20.0
        assert res["tax_amount"] == 40000000.0
        assert res["rule_version"] == "2016-2025.09"

    def test_calculate_tndn_medium_revenue_tier(self, engine: ThueEngine) -> None:
        # 3B < revenue <= 50B -> 17% (Điều 10 khoản 2 Luật 67/2025/QH15)
        res = engine.calculate_tndn(annual_revenue=10000000000, profit=1000000000,
                                    is_sme=True, as_of="2026-06-01")
        assert res["rate_tier"] == "SME_MEDIUM_17"
        assert res["applied_rate_pct"] == 17.0
        assert res["tax_amount"] == 170000000.0
        assert res["net_profit"] == 830000000.0

    def test_calculate_tndn_standard_rate(self, engine: ThueEngine) -> None:
        # Revenue above 50B (or --no-sme) -> standard rate 20%
        res = engine.calculate_tndn(annual_revenue=60000000000, profit=1000000000,
                                    is_sme=True, as_of="2026-06-01")
        assert res["is_sme_incentive"] is False
        assert res["rate_tier"] == "STANDARD_20"
        assert res["applied_rate_pct"] == 20.0
        assert res["tax_amount"] == 200000000.0
        assert res["net_profit"] == 800000000.0

        opted_out = engine.calculate_tndn(annual_revenue=10000000000, profit=1000000000,
                                          is_sme=False, as_of="2026-06-01")
        assert opted_out["rate_tier"] == "STANDARD_20"
        assert opted_out["tax_amount"] == 200000000.0

    def test_calculate_tndn_default_profit_estimation(self, engine: ThueEngine) -> None:
        # If profit is None, estimated at 15% of revenue, then taxed at the
        # rate in force for the period.
        res = engine.calculate_tndn(annual_revenue=1000000000, profit=None,
                                    is_sme=True, as_of="2026-06-01")
        assert res["taxable_profit"] == 150000000.0
        assert res["tax_amount"] == 22500000.0  # 15% band (revenue <= 3B)

        res_2025 = engine.calculate_tndn(annual_revenue=1000000000, profit=None,
                                         is_sme=True, as_of="2025-06-01")
        assert res_2025["taxable_profit"] == 150000000.0
        assert res_2025["tax_amount"] == 30000000.0  # 20% only, before 01/10/2025

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
        # --ky-thue states the tax year, so the CLI answer does not drift with
        # the calendar (1.5B revenue <= 3B -> 15% from 01/10/2025).
        res = runner.invoke(app, ["thue", "tndn", "1500000000", "--profit", "250000000",
                                  "--sme", "--ky-thue", "2026-06-01", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["tax_type"] == "tndn"
        assert data["is_sme_incentive"] is True
        assert data["rate_tier"] == "SME_SMALL_15"
        assert data["applied_rate_pct"] == 15.0
        assert data["tax_amount"] == 37500000.0

        # The same command for a tax year before the 2025 law answers 20%.
        old_period = runner.invoke(app, ["thue", "tndn", "1500000000", "--profit", "250000000",
                                         "--sme", "--ky-thue", "2025-06-01", "--json"])
        assert old_period.exit_code == 0
        assert json.loads(old_period.output)["applied_rate_pct"] == 20.0

    def test_thue_tncn_cli_states_its_tax_period(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["thue", "tncn", "35000000", "--dependents", "1",
                                  "--ky-thue", "2026-10-01", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["tax_period"] == "2026-10-01"
        assert data["taxable_income"] == 13300000.0
        assert data["tax_amount"] == 830000.0

    def test_thue_gtgt_cli_rejects_an_excluded_sector(self, app: typing.Any) -> None:
        """8% is not available for viễn thông (NQ 204/2025/QH15 Điều 1 khoản 1)."""
        rejected = runner.invoke(app, ["thue", "gtgt", "100000000", "--rate", "8",
                                       "--nganh", "viễn thông", "--ky-thue", "2026-06-01"])
        assert rejected.exit_code == 2
        assert "excluded" in (rejected.stderr or rejected.output)

        illegal_rate = runner.invoke(app, ["thue", "gtgt", "100000000", "--rate", "7"])
        assert illegal_rate.exit_code == 2
        assert "not statutory" in (illegal_rate.stderr or illegal_rate.output)

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
        # The statutory rule table is part of the core boundary itself: it is
        # stdlib-only (asserted below) and holds no provider or network client,
        # so importing it keeps thue_engine.py offline and deterministic.
        allowed_core_modules = {"src.core.vn_statutory_rules"}
        # The rule table additionally uses dataclasses/re/unicodedata — all
        # standard library, all offline.
        rules_allowlist = allowed_modules | {"dataclasses", "re", "unicodedata"}

        def assert_stdlib_only(path: Path, allow: set[str] | None = None) -> None:
            permitted = allow if allow is not None else allowed_modules
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] in permitted, \
                            f"Disallowed import in {path.name}: {alias.name}"
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".")[0]
                    assert root in permitted or node.module in allowed_core_modules, \
                        f"Disallowed from-import in {path.name}: {node.module}"

        assert_stdlib_only(target_path)
        assert_stdlib_only(Path("src/core/vn_statutory_rules.py"), rules_allowlist)
