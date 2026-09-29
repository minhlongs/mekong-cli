# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Commercial Banking, Credit Institutions & Basel II Suite (Phase 80)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.banking_engine import (
    BASEL_II_CAR_THRESHOLDS,
    CREDIT_LIMIT_CONSTRAINTS,
    DEBT_GROUPS_CIC,
    GENERAL_PROVISION_RATE_PCT,
    INSTITUTION_TYPES,
    LIQUIDITY_LIMITS,
    BankingEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestBankingCoreBoundary:
    """Ensure BankingEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/banking_engine.py")
        assert source_path.exists(), "banking_engine.py must exist"

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


class TestBankingEngine:
    """Test BankingEngine licensing, credit underwriting, Basel II CAR, CIC debt & liquidity."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> BankingEngine:
        db_file = tmp_path / "test_banking.db"
        return BankingEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Institution types & legal capital
        assert "COMMERCIAL_BANK" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["COMMERCIAL_BANK"]["min_charter_capital_vnd"] == 3_000_000_000_000.0
        assert "POLICY_BANK" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["POLICY_BANK"]["min_charter_capital_vnd"] == 5_000_000_000_000.0
        assert "FINANCE_COMPANY" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["FINANCE_COMPANY"]["min_charter_capital_vnd"] == 500_000_000_000.0
        assert "FINANCIAL_LEASING" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["FINANCIAL_LEASING"]["min_charter_capital_vnd"] == 150_000_000_000.0
        assert "FOREIGN_BANK_BRANCH" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["FOREIGN_BANK_BRANCH"]["min_charter_capital_vnd"] == 375_000_000_000.0

        # Credit concentration limits
        assert CREDIT_LIMIT_CONSTRAINTS["SINGLE_CUSTOMER_EQUITY_RATIO_MAX"] == 14.0
        assert CREDIT_LIMIT_CONSTRAINTS["RELATED_GROUP_EQUITY_RATIO_MAX"] == 23.0

        # Basel II CAR thresholds
        assert BASEL_II_CAR_THRESHOLDS["STRONG"]["min_car_pct"] == 12.0
        assert BASEL_II_CAR_THRESHOLDS["COMPLIANT"]["min_car_pct"] == 8.0
        assert BASEL_II_CAR_THRESHOLDS["EARLY_INTERVENTION"]["min_car_pct"] == 6.0
        assert BASEL_II_CAR_THRESHOLDS["SPECIAL_CONTROL"]["min_car_pct"] == 0.0

        # CIC Debt Groups
        assert len(DEBT_GROUPS_CIC) == 5
        assert DEBT_GROUPS_CIC[1]["provision_rate_pct"] == 0.0
        assert DEBT_GROUPS_CIC[1]["is_npl"] is False
        assert DEBT_GROUPS_CIC[2]["provision_rate_pct"] == 5.0
        assert DEBT_GROUPS_CIC[2]["is_npl"] is False
        assert DEBT_GROUPS_CIC[3]["provision_rate_pct"] == 20.0
        assert DEBT_GROUPS_CIC[3]["is_npl"] is True
        assert DEBT_GROUPS_CIC[4]["provision_rate_pct"] == 50.0
        assert DEBT_GROUPS_CIC[4]["is_npl"] is True
        assert DEBT_GROUPS_CIC[5]["provision_rate_pct"] == 100.0
        assert DEBT_GROUPS_CIC[5]["is_npl"] is True

        assert GENERAL_PROVISION_RATE_PCT == 0.75

        # Liquidity Limits
        assert LIQUIDITY_LIMITS["LDR"]["max_limit_pct"] == 85.0
        assert LIQUIDITY_LIMITS["SHORT_FOR_MID_LONG"]["max_limit_pct"] == 30.0

    def test_license_institution_success(self, engine: BankingEngine) -> None:
        res = engine.license_institution(
            institution_name="Ngân hàng TMCP Mekong Sài Gòn",
            institution_type="COMMERCIAL_BANK",
            tax_id="0300123456",
            charter_capital_vnd=5_000_000_000_000.0,
            headquarters_address="Quận 1, TP. Hồ Chí Minh",
        )
        assert res["status"] == "ACTIVE"
        assert res["institution_type"] == "COMMERCIAL_BANK"
        assert res["charter_capital_vnd"] == 5_000_000_000_000.0
        assert res["statutory_min_capital_vnd"] == 3_000_000_000_000.0
        assert res["sbv_license_number"].startswith("GP-NHNN-")

        licenses = engine.list_licenses()
        assert len(licenses) == 1
        assert licenses[0]["institution_name"] == "Ngân hàng TMCP Mekong Sài Gòn"

    def test_license_institution_insufficient_capital(self, engine: BankingEngine) -> None:
        with pytest.raises(ValueError, match="chưa đạt mức vốn pháp định tối thiểu"):
            engine.license_institution(
                institution_name="Ngân hàng Thiếu Vốn",
                institution_type="COMMERCIAL_BANK",
                tax_id="0109999999",
                charter_capital_vnd=2_000_000_000_000.0,  # Below 3,000B
            )

    def test_license_institution_invalid_type(self, engine: BankingEngine) -> None:
        with pytest.raises(ValueError, match="Loại hình tổ chức tín dụng không hợp lệ"):
            engine.license_institution(
                institution_name="Quỹ Tín Dụng Lạ",
                institution_type="UNKNOWN_TYPE",
                tax_id="0108888888",
            )

    def test_underwrite_credit_approved(self, engine: BankingEngine) -> None:
        # Bank equity = 20,000B VND. Loan = 1,000B VND (5% < 14% cap). Collateral = 1,500B (LTV 66.7% <= 80%)
        res = engine.underwrite_credit(
            borrower_name="Tập đoàn Thủy sản Mekong",
            borrower_id="0309998888",
            loan_amount_vnd=1_000_000_000_000.0,
            interest_rate_pct=7.5,
            term_months=12,
            purpose="Tài trợ lưu động chuỗi cung ứng tôm",
            collateral_type="REAL_ESTATE",
            collateral_value_vnd=1_500_000_000_000.0,
            bank_equity_vnd=20_000_000_000_000.0,
            is_corporate=True,
        )
        assert res["underwriting_verdict"] == "APPROVED"
        assert res["is_approved"] is True
        assert res["exposure_ratio_pct"] == 5.0
        assert res["ltv_pct"] == 66.67
        assert len(res["rejection_reasons"]) == 0
        assert res["contract_number"].startswith("HDTD-")

        loans = engine.list_credit_facilities()
        assert len(loans) == 1
        assert loans[0]["underwriting_verdict"] == "APPROVED"

    def test_underwrite_credit_rejected_concentration_and_ltv(self, engine: BankingEngine) -> None:
        # Bank equity = 10,000B VND. Loan = 2,000B VND (20% > 14% cap). Collateral = 2,100B (LTV 95.2% > 80%)
        res = engine.underwrite_credit(
            borrower_name="Công ty Bất động sản Rủi ro Cao",
            borrower_id="0107776666",
            loan_amount_vnd=2_000_000_000_000.0,
            bank_equity_vnd=10_000_000_000_000.0,
            collateral_value_vnd=2_100_000_000_000.0,
        )
        assert res["underwriting_verdict"] == "REJECTED"
        assert res["is_approved"] is False
        assert res["exposure_ratio_pct"] == 20.0
        assert len(res["rejection_reasons"]) == 2

    def test_underwrite_credit_invalid_inputs(self, engine: BankingEngine) -> None:
        with pytest.raises(ValueError, match="Số tiền cấp tín dụng phải lớn hơn 0"):
            engine.underwrite_credit(
                borrower_name="Khách Vay",
                borrower_id="010111",
                loan_amount_vnd=-100.0,
            )

        with pytest.raises(ValueError, match="Vốn tự có của ngân hàng cấp tín dụng phải lớn hơn 0"):
            engine.underwrite_credit(
                borrower_name="Khách Vay",
                borrower_id="010111",
                loan_amount_vnd=1_000_000_000.0,
                bank_equity_vnd=0.0,
            )

    def test_audit_capital_adequacy_strong(self, engine: BankingEngine) -> None:
        # Tier 1 = 15,000B, Tier 2 = 5,000B -> Total Own Capital = 20,000B
        # Total RWA = 80,000B + 10,000B + 10,000B = 100,000B -> CAR = 20.0% (STRONG)
        res = engine.audit_capital_adequacy(
            institution_name="Ngân hàng TMCP An Toàn",
            tier1_capital_vnd=15_000_000_000_000.0,
            tier2_capital_vnd=5_000_000_000_000.0,
            credit_rwa_vnd=80_000_000_000_000.0,
            market_rwa_vnd=10_000_000_000_000.0,
            operational_rwa_vnd=10_000_000_000_000.0,
        )
        assert res["car_ratio_pct"] == 20.0
        assert res["car_status"] == "STRONG"
        assert res["is_compliant"] is True
        assert res["total_own_capital_vnd"] == 20_000_000_000_000.0

    def test_audit_capital_adequacy_tier2_cap_and_early_intervention(self, engine: BankingEngine) -> None:
        # Tier 1 = 4,000B, Tier 2 = 6,000B -> Eligible Tier 2 capped at 4,000B -> Total Own Capital = 8,000B
        # Total RWA = 110,000B + 5,000B + 5,000B = 120,000B -> CAR = 8,000 / 120,000 = 6.67% (EARLY_INTERVENTION, < 8.0%)
        res = engine.audit_capital_adequacy(
            institution_name="Ngân hàng Cần Can Thiệp",
            tier1_capital_vnd=4_000_000_000_000.0,
            tier2_capital_vnd=6_000_000_000_000.0,
            credit_rwa_vnd=110_000_000_000_000.0,
            market_rwa_vnd=5_000_000_000_000.0,
            operational_rwa_vnd=5_000_000_000_000.0,
        )
        assert res["tier2_capital_vnd"] == 4_000_000_000_000.0  # Capped at Tier 1
        assert res["total_own_capital_vnd"] == 8_000_000_000_000.0
        assert res["car_ratio_pct"] == 6.67
        assert res["car_status"] == "EARLY_INTERVENTION"
        assert res["is_compliant"] is False

    def test_classify_credit_debt_standard_group1(self, engine: BankingEngine) -> None:
        # Overdue 0 days -> Group 1: 0% specific, 0.75% general provision, not NPL
        res = engine.classify_credit_debt(
            contract_number="HDTD-2026-001",
            borrower_name="Công ty TNHH Mekong Agri",
            outstanding_balance_vnd=10_000_000_000.0,
            overdue_days=0,
            deductible_collateral_vnd=8_000_000_000.0,
        )
        assert res["debt_group"] == 1
        assert res["is_npl"] is False
        assert res["specific_provision_rate_pct"] == 0.0
        assert res["specific_provision_vnd"] == 0.0
        assert res["general_provision_vnd"] == 75_000_000.0  # 0.75% of 10B
        assert res["total_provision_vnd"] == 75_000_000.0

    def test_classify_credit_debt_npl_groups(self, engine: BankingEngine) -> None:
        # Group 3 (100 days overdue -> 91-180 days): 20% specific, 0.75% general
        # Balance = 10B, Collateral = 6B -> Net exposure = 4B -> Specific = 4B * 20% = 800M
        # General = 10B * 0.75% = 75M -> Total = 875M
        res3 = engine.classify_credit_debt(
            contract_number="HDTD-2026-003",
            borrower_name="Công ty Chậm Trả",
            outstanding_balance_vnd=10_000_000_000.0,
            overdue_days=100,
            deductible_collateral_vnd=6_000_000_000.0,
        )
        assert res3["debt_group"] == 3
        assert res3["is_npl"] is True
        assert res3["specific_provision_vnd"] == 800_000_000.0
        assert res3["general_provision_vnd"] == 75_000_000.0
        assert res3["total_provision_vnd"] == 875_000_000.0

        # Group 5 (> 360 days overdue): 100% specific, 0% general provision
        # Balance = 5B, Collateral = 2B -> Net exposure = 3B -> Specific = 3B * 100% = 3B
        res5 = engine.classify_credit_debt(
            contract_number="HDTD-2026-005",
            borrower_name="Khách Vay Mất Vốn",
            outstanding_balance_vnd=5_000_000_000.0,
            overdue_days=400,
            deductible_collateral_vnd=2_000_000_000.0,
        )
        assert res5["debt_group"] == 5
        assert res5["is_npl"] is True
        assert res5["specific_provision_vnd"] == 3_000_000_000.0
        assert res5["general_provision_vnd"] == 0.0  # Excluded for Group 5
        assert res5["total_provision_vnd"] == 3_000_000_000.0

    def test_audit_liquidity_ratios(self, engine: BankingEngine) -> None:
        # Compliant: LDR = 80,000 / 100,000 = 80% (<= 85%), Short-to-mid/long = 15,000 / 60,000 = 25% (<= 30%)
        res = engine.audit_liquidity_ratios(
            institution_name="Ngân hàng TMCP Chuẩn",
            total_loans_vnd=80_000_000_000_000.0,
            total_deposits_vnd=100_000_000_000_000.0,
            short_term_funds_vnd=60_000_000_000_000.0,
            mid_long_loans_vnd=15_000_000_000_000.0,
        )
        assert res["ldr_ratio_pct"] == 80.0
        assert res["ldr_compliant"] is True
        assert res["short_for_mid_long_ratio_pct"] == 25.0
        assert res["short_for_mid_long_compliant"] is True
        assert res["overall_status"] == "COMPLIANT"

        # Violation: LDR = 90% (> 85%)
        res_violation = engine.audit_liquidity_ratios(
            institution_name="Ngân hàng Căng Thanh Khoản",
            total_loans_vnd=90_000_000_000_000.0,
            total_deposits_vnd=100_000_000_000_000.0,
            short_term_funds_vnd=50_000_000_000_000.0,
            mid_long_loans_vnd=18_000_000_000_000.0,  # 36% > 30%
        )
        assert res_violation["ldr_compliant"] is False
        assert res_violation["short_for_mid_long_compliant"] is False
        assert res_violation["overall_status"] == "VIOLATION"

    def test_get_status_telemetry(self, engine: BankingEngine) -> None:
        # Seed 1 institution, 1 approved loan, 1 CAR audit, 2 debt classifications
        engine.license_institution("Ngân hàng Test", charter_capital_vnd=4_000_000_000_000.0)
        engine.underwrite_credit(
            borrower_name="Khách A",
            borrower_id="111",
            loan_amount_vnd=500_000_000_000.0,
            collateral_value_vnd=1_000_000_000_000.0,
        )
        engine.audit_capital_adequacy(
            institution_name="Ngân hàng Test",
            tier1_capital_vnd=10_000_000_000_000.0,
            tier2_capital_vnd=2_000_000_000_000.0,
            credit_rwa_vnd=80_000_000_000_000.0,
            market_rwa_vnd=5_000_000_000_000.0,
            operational_rwa_vnd=5_000_000_000_000.0,
        )
        engine.classify_credit_debt("HD-1", "Khách A", 10_000_000_000.0, overdue_days=0)
        engine.classify_credit_debt("HD-2", "Khách B", 5_000_000_000.0, overdue_days=120)  # NPL Group 3

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["engine"] == "BankingEngine"
        assert status["institutions"]["total_licensed"] == 1
        assert status["institutions"]["commercial_banks"] == 1
        assert status["credit_underwriting"]["total_facilities"] == 1
        assert status["credit_underwriting"]["approved_facilities"] == 1
        assert status["credit_underwriting"]["total_approved_balance_vnd"] == 500_000_000_000.0
        assert status["basel_ii_car"]["total_audits"] == 1
        assert status["basel_ii_car"]["compliant_audits_ratio_gte_8pct"] == 1
        assert status["asset_quality_cic"]["classified_loans_count"] == 2
        assert status["asset_quality_cic"]["npl_loans_count"] == 1
        assert status["asset_quality_cic"]["npl_ratio_pct"] == 33.33  # 5B / 15B = 33.33%


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestBankingCli:
    """Test CLI commands for mekong banking."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_banking_root_json(self) -> None:
        result = runner.invoke(self.app, ["banking", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["engine"] == "BankingEngine"
        assert data["status"] == "HEALTHY"

    def test_banking_root_panel(self) -> None:
        result = runner.invoke(self.app, ["banking"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ NGÂN HÀNG" in result.output

    def test_banking_license_cli(self) -> None:
        # Success with JSON
        import uuid
        unique_tax_id = f"03{uuid.uuid4().hex[:8]}"
        res = runner.invoke(
            self.app,
            [
                "banking",
                "license",
                "Ngân hàng TMCP Phương Nam",
                "--type",
                "COMMERCIAL_BANK",
                "--tax-id",
                unique_tax_id,
                "--capital",
                "4000000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "ACTIVE"
        assert data["institution_name"] == "Ngân hàng TMCP Phương Nam"

        # Failure: capital below 3,000B
        res_fail = runner.invoke(
            self.app,
            [
                "banking",
                "license",
                "Ngân hàng Vốn Yếu",
                "--capital",
                "1000000000000",
            ],
        )
        assert res_fail.exit_code == 1

    def test_banking_credit_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "banking",
                "credit",
                "Công ty CP Thép X",
                "0105554443",
                "500000000000",
                "--value",
                "800000000000",
                "--bank-equity",
                "15000000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["underwriting_verdict"] == "APPROVED"
        assert data["exposure_ratio_pct"] == 3.33

    def test_banking_car_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "banking",
                "car",
                "Ngân hàng Mekong",
                "12000000000000",
                "4000000000000",
                "90000000000000",
                "5000000000000",
                "5000000000000",
                "--quarter",
                "Q3/2026",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["car_ratio_pct"] == 16.0
        assert data["car_status"] == "STRONG"
        assert data["is_compliant"] is True

    def test_banking_debt_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "banking",
                "debt",
                "HDTD-2026-999",
                "Công ty ABC",
                "20000000000",
                "--overdue",
                "45",
                "--collateral",
                "5000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["debt_group"] == 2
        assert data["is_npl"] is False
        assert data["specific_provision_rate_pct"] == 5.0

    def test_banking_liquidity_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "banking",
                "liquidity",
                "Ngân hàng TMCP Phương Đông",
                "75000000000000",
                "100000000000000",
                "60000000000000",
                "15000000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ldr_ratio_pct"] == 75.0
        assert data["short_for_mid_long_ratio_pct"] == 25.0
        assert data["overall_status"] == "COMPLIANT"

    def test_banking_list_and_status_cli(self) -> None:
        res_list = runner.invoke(self.app, ["banking", "list", "--type", "licenses", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.output)
        assert isinstance(data_list, list)

        res_status = runner.invoke(self.app, ["banking", "status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.output)
        assert data_status["engine"] == "BankingEngine"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestBankingMcp:
    """Test MCP tool registration and handlers for both scripts/mcp_server.py and src/core/mcp_server.py."""

    def test_scripts_mcp_banking_tools(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        expected_tools = [
            "mekong_banking_license",
            "mekong_banking_credit",
            "mekong_banking_car",
            "mekong_banking_debt",
            "mekong_banking_liquidity",
            "mekong_banking_list",
            "mekong_banking_status",
        ]

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} must be in scripts CORE_TOOLS_SPEC"
            assert tool_name in CORE_HANDLERS, f"Tool {tool_name} must be in scripts CORE_HANDLERS"

        # Test execution through handler
        status_res = json.loads(CORE_HANDLERS["mekong_banking_status"]({}))
        assert status_res["status"] == "HEALTHY"
        assert status_res["engine"] == "BankingEngine"

    def test_core_mcp_banking_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_banking_license")
        assert hasattr(server, "_handle_banking_credit")
        assert hasattr(server, "_handle_banking_car")
        assert hasattr(server, "_handle_banking_debt")
        assert hasattr(server, "_handle_banking_liquidity")
        assert hasattr(server, "_handle_banking_list")
        assert hasattr(server, "_handle_banking_status")

        # Test dispatch
        res_stat = json.loads(server._handle_banking_status())
        assert res_stat["engine"] == "BankingEngine"
        assert res_stat["status"] == "HEALTHY"
