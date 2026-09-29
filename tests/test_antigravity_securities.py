# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Securities, Stock Exchanges & Capital Markets Suite (Phase 79)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.securities_engine import (
    EXCHANGE_LISTING_RULES,
    FIRM_SAFETY_RATIO_THRESHOLDS,
    MARGIN_RISK_THRESHOLDS,
    OFFERING_TYPES,
    PRACTITIONER_CERT_TYPES,
    SecuritiesEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestSecuritiesCoreBoundary:
    """Ensure SecuritiesEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/securities_engine.py")
        assert source_path.exists(), "securities_engine.py must exist"

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


class TestSecuritiesEngine:
    """Test SecuritiesEngine offering, listing, margin, firm safety, and licensing."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> SecuritiesEngine:
        db_file = tmp_path / "test_securities.db"
        return SecuritiesEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Exchanges
        assert "HOSE" in EXCHANGE_LISTING_RULES
        assert EXCHANGE_LISTING_RULES["HOSE"]["min_charter_capital_vnd"] == 120_000_000_000.0
        assert EXCHANGE_LISTING_RULES["HOSE"]["min_non_major_shareholders"] == 300
        assert "HNX" in EXCHANGE_LISTING_RULES
        assert EXCHANGE_LISTING_RULES["HNX"]["min_charter_capital_vnd"] == 30_000_000_000.0
        assert EXCHANGE_LISTING_RULES["HNX"]["min_non_major_shareholders"] == 100
        assert "UPCOM" in EXCHANGE_LISTING_RULES

        # Offerings
        assert "IPO" in OFFERING_TYPES
        assert OFFERING_TYPES["IPO"]["min_capital_vnd"] == 30_000_000_000.0
        assert OFFERING_TYPES["IPO"]["require_two_profitable_years"] is True
        assert "PUBLIC_OFFERING" in OFFERING_TYPES
        assert "RIGHTS_ISSUE" in OFFERING_TYPES
        assert "PRIVATE_PLACEMENT" in OFFERING_TYPES

        # Margin Thresholds
        assert MARGIN_RISK_THRESHOLDS["INITIAL_MARGIN_RATIO_MIN"] == 50.0
        assert MARGIN_RISK_THRESHOLDS["MAINTENANCE_MARGIN_RATIO_MIN"] == 30.0
        assert MARGIN_RISK_THRESHOLDS["FORCE_SELL_THRESHOLD"] == 25.0
        assert MARGIN_RISK_THRESHOLDS["SAFE_TARGET_RATIO"] == 35.0

        # Firm CAR
        assert "HEALTHY" in FIRM_SAFETY_RATIO_THRESHOLDS
        assert FIRM_SAFETY_RATIO_THRESHOLDS["HEALTHY"]["min_ratio"] == 220.0
        assert "COMPLIANT" in FIRM_SAFETY_RATIO_THRESHOLDS
        assert FIRM_SAFETY_RATIO_THRESHOLDS["COMPLIANT"]["min_ratio"] == 180.0
        assert "EARLY_WARNING" in FIRM_SAFETY_RATIO_THRESHOLDS
        assert "SPECIAL_CONTROL" in FIRM_SAFETY_RATIO_THRESHOLDS

        # Practitioner types
        assert "BROKERAGE" in PRACTITIONER_CERT_TYPES
        assert "FINANCIAL_ANALYSIS" in PRACTITIONER_CERT_TYPES
        assert "FUND_MANAGEMENT" in PRACTITIONER_CERT_TYPES
        assert "INVESTMENT_BANKING" in PRACTITIONER_CERT_TYPES

    def test_audit_public_offering_ipo_eligible(self, engine: SecuritiesEngine) -> None:
        res = engine.audit_public_offering(
            enterprise_name="Công ty Cổ phần Công nghệ Mekong",
            ticker_symbol="MKT",
            tax_id="0108877665",
            offering_type="IPO",
            charter_capital_vnd=60_000_000_000.0,
            shares_offered=6_000_000,
            offering_price_vnd=25_000.0,
            roe_prior_year_pct=14.5,
            two_years_profitable=True,
            has_accumulated_losses=False,
            non_major_shareholder_count=200,
            non_major_ratio_pct=22.0,
        )
        assert res["audit_verdict"] == "ELIGIBLE"
        assert res["is_approved"] is True
        assert res["ticker_symbol"] == "MKT"
        assert res["total_offering_value_vnd"] == 150_000_000_000.0
        assert len(res["rejection_reasons"]) == 0
        assert "GCN-UBCK" in res["ssc_registration_number"]

    def test_audit_public_offering_ipo_ineligible(self, engine: SecuritiesEngine) -> None:
        res = engine.audit_public_offering(
            enterprise_name="Công ty Cổ phần Startup Yếu",
            ticker_symbol="YEU",
            tax_id="0109999888",
            offering_type="IPO",
            charter_capital_vnd=20_000_000_000.0,  # < 30B
            shares_offered=2_000_000,
            offering_price_vnd=10_000.0,
            roe_prior_year_pct=3.5,  # < 5%
            two_years_profitable=False,  # not profitable
            has_accumulated_losses=True,  # has losses
            non_major_shareholder_count=40,  # < 100
            non_major_ratio_pct=10.0,  # < 20%
        )
        assert res["audit_verdict"] == "INELIGIBLE"
        assert res["is_approved"] is False
        assert len(res["rejection_reasons"]) >= 4

    def test_audit_public_offering_invalid_type(self, engine: SecuritiesEngine) -> None:
        with pytest.raises(ValueError, match="Loại hình chào bán không hợp lệ"):
            engine.audit_public_offering(
                enterprise_name="Công ty Test",
                ticker_symbol="TST",
                tax_id="0101111222",
                offering_type="INVALID_TYPE",
            )

    def test_verify_listing_hose_approved(self, engine: SecuritiesEngine) -> None:
        res = engine.verify_listing_qualification(
            ticker_symbol="MKT",
            company_name="Công ty Cổ phần Công nghệ Mekong",
            exchange="HOSE",
            listed_shares=50_000_000,
            par_value_vnd=10_000.0,
            current_market_price_vnd=40_000.0,
            charter_capital_vnd=500_000_000_000.0,
            roe_pct=15.0,
            operating_years=5,
            shareholder_count_non_major=500,
            has_accumulated_losses=False,
            has_overdue_debt_1yr=False,
        )
        assert res["audit_verdict"] == "APPROVED"
        assert res["is_approved"] is True
        assert res["exchange"] == "HOSE"
        assert res["market_cap_vnd"] == 2_000_000_000_000.0
        assert len(res["rejections"]) == 0
        assert "QĐ-NY-HOSE" in res["listing_decision_number"]

    def test_verify_listing_hose_rejected(self, engine: SecuritiesEngine) -> None:
        res = engine.verify_listing_qualification(
            ticker_symbol="MKT",
            company_name="Công ty Cổ phần Chưa Đạt Chuẩn",
            exchange="HOSE",
            listed_shares=10_000_000,
            par_value_vnd=10_000.0,
            current_market_price_vnd=20_000.0,
            charter_capital_vnd=80_000_000_000.0,  # < 120B
            roe_pct=3.0,  # < 5%
            operating_years=1,  # < 2 years
            shareholder_count_non_major=150,  # < 300
            has_accumulated_losses=True,
            has_overdue_debt_1yr=True,
        )
        assert res["audit_verdict"] == "REJECTED"
        assert res["is_approved"] is False
        assert len(res["rejections"]) >= 4

    def test_verify_listing_hnx_upcom(self, engine: SecuritiesEngine) -> None:
        # HNX
        res_hnx = engine.verify_listing_qualification(
            ticker_symbol="HNX_CO",
            company_name="Công ty Sàn Hà Nội",
            exchange="HNX",
            listed_shares=5_000_000,
            charter_capital_vnd=40_000_000_000.0,
            roe_pct=8.0,
            operating_years=2,
            shareholder_count_non_major=120,
        )
        assert res_hnx["audit_verdict"] == "APPROVED"

        # UPCoM
        res_upcom = engine.verify_listing_qualification(
            ticker_symbol="UPC_CO",
            company_name="Công ty Sàn UPCoM",
            exchange="UPCOM",
            charter_capital_vnd=35_000_000_000.0,
        )
        assert res_upcom["audit_verdict"] == "APPROVED"

    def test_verify_listing_invalid_exchange(self, engine: SecuritiesEngine) -> None:
        with pytest.raises(ValueError, match="Sàn giao dịch không hợp lệ"):
            engine.verify_listing_qualification(
                ticker_symbol="BAD",
                company_name="Công ty Bad",
                exchange="NASDAQ",
            )

    def test_audit_margin_account_normal(self, engine: SecuritiesEngine) -> None:
        res = engine.audit_margin_account(
            investor_name="Nguyễn Văn An",
            investor_id="026C112233",
            brokerage_firm="Chứng khoán Mekong",
            total_asset_value_vnd=1_000_000_000.0,
            loan_balance_vnd=400_000_000.0,
            collateral_value_vnd=1_000_000_000.0,
        )
        assert res["status"] == "NORMAL"
        assert res["margin_ratio_pct"] == 60.0
        assert res["call_margin_trigger"] is False
        assert res["force_sell_trigger"] is False
        assert res["deficit_amount_vnd"] == 0.0

    def test_audit_margin_account_margin_call(self, engine: SecuritiesEngine) -> None:
        res = engine.audit_margin_account(
            investor_name="Trần Thị Bình",
            investor_id="026C223344",
            brokerage_firm="Chứng khoán Mekong",
            total_asset_value_vnd=1_000_000_000.0,
            loan_balance_vnd=720_000_000.0,  # equity = 280M (28% < 30%)
            collateral_value_vnd=1_000_000_000.0,
        )
        assert res["status"] == "MARGIN_CALL"
        assert res["margin_ratio_pct"] == 28.0
        assert res["call_margin_trigger"] is True
        assert res["force_sell_trigger"] is False
        assert res["deficit_amount_vnd"] == 20_000_000.0  # need 20M to reach 300M (30%)

    def test_audit_margin_account_force_sell(self, engine: SecuritiesEngine) -> None:
        res = engine.audit_margin_account(
            investor_name="Lê Hoàng Cường",
            investor_id="026C334455",
            brokerage_firm="Chứng khoán Mekong",
            total_asset_value_vnd=1_000_000_000.0,
            loan_balance_vnd=780_000_000.0,  # equity = 220M (22% <= 25%)
            collateral_value_vnd=1_000_000_000.0,
        )
        assert res["status"] == "FORCE_SELL"
        assert res["margin_ratio_pct"] == 22.0
        assert res["call_margin_trigger"] is True
        assert res["force_sell_trigger"] is True
        # safe target is 35% (350M), equity is 220M => deficit is 130M
        assert res["deficit_amount_vnd"] == 130_000_000.0

    def test_audit_margin_account_invalid_asset(self, engine: SecuritiesEngine) -> None:
        with pytest.raises(ValueError, match="Tổng giá trị tài sản trong tài khoản ký quỹ phải lớn hơn 0"):
            engine.audit_margin_account(
                investor_name="Bad Asset",
                investor_id="026C000000",
                brokerage_firm="Chứng khoán Mekong",
                total_asset_value_vnd=0.0,
                loan_balance_vnd=0.0,
                collateral_value_vnd=0.0,
            )

    def test_audit_firm_financial_safety_tiers(self, engine: SecuritiesEngine) -> None:
        # HEALTHY (CAR >= 220%)
        res_healthy = engine.audit_firm_financial_safety(
            firm_name="CTCP Chứng khoán Mekong A",
            tax_id="0108877001",
            liquid_capital_vnd=2_500_000_000_000.0,
            market_risk_vnd=500_000_000_000.0,
            settlement_risk_vnd=200_000_000_000.0,
            operational_risk_vnd=300_000_000_000.0,  # Total risk = 1,000B, CAR = 250%
        )
        assert res_healthy["safety_status"] == "HEALTHY"
        assert res_healthy["capital_adequacy_ratio_pct"] == 250.0
        assert res_healthy["is_compliant"] is True

        # COMPLIANT (180% <= CAR < 220%)
        res_comp = engine.audit_firm_financial_safety(
            firm_name="CTCP Chứng khoán Mekong B",
            tax_id="0108877002",
            liquid_capital_vnd=1_900_000_000_000.0,
            market_risk_vnd=500_000_000_000.0,
            settlement_risk_vnd=200_000_000_000.0,
            operational_risk_vnd=300_000_000_000.0,  # CAR = 190%
        )
        assert res_comp["safety_status"] == "COMPLIANT"
        assert res_comp["capital_adequacy_ratio_pct"] == 190.0
        assert res_comp["is_compliant"] is True

        # EARLY_WARNING (150% <= CAR < 180%)
        res_warn = engine.audit_firm_financial_safety(
            firm_name="CTCP Chứng khoán Mekong C",
            tax_id="0108877003",
            liquid_capital_vnd=1_600_000_000_000.0,
            market_risk_vnd=500_000_000_000.0,
            settlement_risk_vnd=200_000_000_000.0,
            operational_risk_vnd=300_000_000_000.0,  # CAR = 160%
        )
        assert res_warn["safety_status"] == "EARLY_WARNING"
        assert res_warn["is_compliant"] is False

        # SPECIAL_CONTROL (CAR < 150%)
        res_ctrl = engine.audit_firm_financial_safety(
            firm_name="CTCP Chứng khoán Mekong D",
            tax_id="0108877004",
            liquid_capital_vnd=1_200_000_000_000.0,
            market_risk_vnd=500_000_000_000.0,
            settlement_risk_vnd=200_000_000_000.0,
            operational_risk_vnd=300_000_000_000.0,  # CAR = 120%
        )
        assert res_ctrl["safety_status"] == "SPECIAL_CONTROL"
        assert res_ctrl["is_compliant"] is False

    def test_audit_firm_financial_safety_invalid_risk(self, engine: SecuritiesEngine) -> None:
        with pytest.raises(ValueError, match="Tổng giá trị rủi ro"):
            engine.audit_firm_financial_safety(
                firm_name="CTCP Zero Risk",
                tax_id="0108877005",
                liquid_capital_vnd=1_000_000_000.0,
                market_risk_vnd=0.0,
                settlement_risk_vnd=0.0,
                operational_risk_vnd=0.0,
            )

    def test_issue_practitioner_license_success(self, engine: SecuritiesEngine) -> None:
        res = engine.issue_practitioner_license(
            practitioner_name="Võ Tấn Phát",
            id_card_or_passport="079090011223",
            license_type="BROKERAGE",
            firm_affiliation="Công ty Cổ phần Chứng khoán Mekong",
        )
        assert res["compliance_status"] == "ACTIVE"
        assert res["license_type"] == "BROKERAGE"
        assert "CCHN-UBCK-BROK" in res["ssc_license_number"]
        assert res["practitioner_name"] == "Võ Tấn Phát"

    def test_issue_practitioner_license_invalid_type(self, engine: SecuritiesEngine) -> None:
        with pytest.raises(ValueError, match="Loại chứng chỉ hành nghề không hợp lệ"):
            engine.issue_practitioner_license(
                practitioner_name="Test",
                id_card_or_passport="012345",
                license_type="INVALID_CERT",
            )

    def test_listing_and_status(self, engine: SecuritiesEngine) -> None:
        # Populate records
        engine.audit_public_offering(
            enterprise_name="DN Test",
            ticker_symbol="DNT",
            tax_id="0101112223",
        )
        engine.verify_listing_qualification(
            ticker_symbol="DNT",
            company_name="DN Test",
            exchange="HOSE",
        )
        engine.audit_margin_account(
            investor_name="Investor Test",
            investor_id="026C999888",
            brokerage_firm="Chứng khoán Mekong",
            total_asset_value_vnd=500_000_000.0,
            loan_balance_vnd=200_000_000.0,
            collateral_value_vnd=500_000_000.0,
        )
        engine.audit_firm_financial_safety(
            firm_name="CTCP Mekong Test",
            tax_id="0109998881",
            liquid_capital_vnd=2_000_000_000_000.0,
            market_risk_vnd=500_000_000_000.0,
            settlement_risk_vnd=200_000_000_000.0,
            operational_risk_vnd=300_000_000_000.0,
        )
        engine.issue_practitioner_license(
            practitioner_name="Nguyen Van Test",
            id_card_or_passport="001122334455",
            license_type="FINANCIAL_ANALYSIS",
        )

        offerings = engine.list_offerings()
        assert len(offerings) == 1

        listings = engine.list_listings()
        assert len(listings) == 1

        margins = engine.list_margin_accounts()
        assert len(margins) == 1

        safeties = engine.list_firm_safeties()
        assert len(safeties) == 1

        practitioners = engine.list_practitioners()
        assert len(practitioners) == 1

        status = engine.get_status()
        assert status["offerings"]["total"] == 1
        assert status["listings"]["total_listed"] == 1
        assert status["margin_risk"]["monitored_accounts"] == 1
        assert status["brokerage_safety_car"]["total_firm_audits"] == 1
        assert status["practitioners"]["total_licensed"] == 1
        assert status["engine"] == "SecuritiesEngine"


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestSecuritiesCli:
    """Test CLI commands for mekong securities."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_status(self) -> None:
        res = runner.invoke(self.app, ["securities"])
        assert res.exit_code == 0
        assert "THỊ TRƯỜNG CHỨNG KHOÁN" in res.output or "Securities" in res.output

    def test_cli_status_json(self) -> None:
        res = runner.invoke(self.app, ["securities", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["engine"] == "SecuritiesEngine"

    def test_cli_offering_command(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "securities",
                "offering",
                "Công ty CP Công nghệ AI Mekong",
                "AIM",
                "0109988771",
                "--type",
                "IPO",
                "--capital",
                "100000000000",
                "--shares",
                "10000000",
                "--price",
                "30000",
                "--roe",
                "16.5",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["audit_verdict"] == "ELIGIBLE"
        assert data["ticker_symbol"] == "AIM"

    def test_cli_listing_command(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "securities",
                "listing",
                "AIM",
                "Công ty CP Công nghệ AI Mekong",
                "--exchange",
                "HOSE",
                "--shares",
                "50000000",
                "--price",
                "35000",
                "--capital",
                "500000000000",
                "--roe",
                "18.0",
                "--years",
                "5",
                "--shareholders",
                "450",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["audit_verdict"] == "APPROVED"
        assert data["exchange"] == "HOSE"

    def test_cli_margin_command(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "securities",
                "margin",
                "Phan Văn Đạt",
                "026C556677",
                "--firm",
                "Chứng khoán Mekong",
                "--assets",
                "1000000000",
                "--loan",
                "750000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] in ("MARGIN_CALL", "FORCE_SELL")
        assert data["margin_ratio_pct"] == 25.0

    def test_cli_safety_command(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "securities",
                "safety",
                "Công ty CP Chứng khoán Alpha",
                "0108889990",
                "--liquid",
                "2000000000000",
                "--market-risk",
                "400000000000",
                "--settle-risk",
                "200000000000",
                "--op-risk",
                "200000000000",
                "--quarter",
                "Q3/2026",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["safety_status"] == "HEALTHY"
        assert data["capital_adequacy_ratio_pct"] == 250.0

    def test_cli_license_command(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "securities",
                "license",
                "Lý Thường Kiệt",
                "001099112233",
                "--type",
                "BROKERAGE",
                "--firm",
                "Chứng khoán Mekong",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["compliance_status"] == "ACTIVE"
        assert "CCHN-UBCK-BROK" in data["ssc_license_number"]

    def test_cli_list_commands(self) -> None:
        for resource in ["offerings", "listings", "margin", "safety", "practitioners"]:
            res = runner.invoke(self.app, ["securities", "list", "--type", resource, "--json"])
            assert res.exit_code == 0
            data = json.loads(res.output)
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# MCP Tool Server Parity Tests
# ---------------------------------------------------------------------------


class TestSecuritiesMcp:
    """Test MCP handlers in scripts/mcp_server.py and src/core/mcp_server.py."""

    def test_scripts_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_securities_license,
            handle_securities_list,
            handle_securities_listing,
            handle_securities_margin,
            handle_securities_offering,
            handle_securities_safety,
            handle_securities_status,
        )

        # 1. Offering
        res_off = json.loads(
            handle_securities_offering({
                "enterprise_name": "Công ty CP Tập đoàn Mekong",
                "ticker_symbol": "MKG",
                "tax_id": "0108881234",
                "offering_type": "IPO",
                "charter_capital_vnd": 80_000_000_000.0,
                "shares_offered": 8_000_000,
                "offering_price_vnd": 25_000.0,
                "roe_prior_year_pct": 15.0,
                "two_years_profitable": True,
                "has_accumulated_losses": False,
                "non_major_shareholder_count": 250,
                "non_major_ratio_pct": 20.0,
            })
        )
        assert res_off["audit_verdict"] == "ELIGIBLE"
        assert res_off["ticker_symbol"] == "MKG"

        # 2. Listing
        res_list = json.loads(
            handle_securities_listing({
                "ticker_symbol": "MKG",
                "company_name": "Công ty CP Tập đoàn Mekong",
                "exchange": "HOSE",
                "listed_shares": 50_000_000,
                "par_value_vnd": 10_000.0,
                "current_market_price_vnd": 35_000.0,
                "charter_capital_vnd": 500_000_000_000.0,
                "roe_pct": 14.0,
                "operating_years": 4,
                "shareholder_count_non_major": 400,
            })
        )
        assert res_list["audit_verdict"] == "APPROVED"

        # 3. Margin
        res_mar = json.loads(
            handle_securities_margin({
                "investor_name": "Đặng Thị Hoa",
                "investor_id": "026C889900",
                "brokerage_firm": "Chứng khoán Mekong",
                "total_asset_value_vnd": 800_000_000.0,
                "loan_balance_vnd": 300_000_000.0,
                "collateral_value_vnd": 800_000_000.0,
            })
        )
        assert res_mar["status"] == "NORMAL"

        # 4. Safety
        res_saf = json.loads(
            handle_securities_safety({
                "firm_name": "CTCP Chứng khoán Thủ Đô",
                "tax_id": "0109991122",
                "liquid_capital_vnd": 1_800_000_000_000.0,
                "market_risk_vnd": 400_000_000_000.0,
                "settlement_risk_vnd": 200_000_000_000.0,
                "operational_risk_vnd": 200_000_000_000.0,
            })
        )
        assert res_saf["safety_status"] == "HEALTHY"

        # 5. License
        res_lic = json.loads(
            handle_securities_license({
                "practitioner_name": "Phan Bội Châu",
                "id_card_or_passport": "001099554433",
                "license_type": "FUND_MANAGEMENT",
            })
        )
        assert res_lic["compliance_status"] == "ACTIVE"

        # 6. List
        res_all = json.loads(handle_securities_list({"resource": "offerings", "limit": 10}))
        assert isinstance(res_all, list)
        assert len(res_all) >= 1

        # 7. Status
        res_stat = json.loads(handle_securities_status({}))
        assert res_stat["engine"] == "SecuritiesEngine"

    def test_core_mcp_server_methods(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_securities_offering")
        assert hasattr(server, "_handle_securities_listing")
        assert hasattr(server, "_handle_securities_margin")
        assert hasattr(server, "_handle_securities_safety")
        assert hasattr(server, "_handle_securities_license")
        assert hasattr(server, "_handle_securities_list")
        assert hasattr(server, "_handle_securities_status")

        # Test call
        res_stat = json.loads(server._handle_securities_status())
        assert res_stat["engine"] == "SecuritiesEngine"
