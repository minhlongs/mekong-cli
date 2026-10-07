# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Comprehensive Tests for Mekong Customs, Foreign Exchange & Bonded Logistics Suite (Phases 167 - 170).

Covers:
1. AST Boundary & Zero-Dependency Purity (Pure Python Stdlib)
2. Phase 167: Vietnam Customs Valuation & Rules of Origin (ROO) Engine
3. Phase 168: Foreign Exchange Control & SBV Offshore Loan Engine
4. Phase 169: Technology Transfer & IP Licensing Royalty Engine
5. Phase 170: Bonded Warehouse & CFS Logistics Operation Engine
6. CLI Commands & Dual-Group Wiring (mekong customs & mekong haiquan)
7. FastMCP & JSON-RPC Server Tool Handlers
"""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.customs_fx_engine import (
    CustomsValuationOriginEngine,
    CustomsValuationMethod,
    ForeignExchangeControlEngine,
    LoanTenorCategory,
    TechnologyTransferEngine,
    BondedLogisticsEngine,
    StorageFacilityType,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_customs_valuation,
    handle_customs_rvc,
    handle_fx_loan,
    handle_tech_transfer_royalty,
    handle_bonded_storage,
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
)

runner = CliRunner()


# ============================================================================
# 1. AST Boundary & Zero-Dependency Purity Tests
# ============================================================================


class TestCustomsFxBoundary:
    """Verify customs_fx_engine is 100% Python Standard Library."""

    def test_pure_standard_library_imports(self) -> None:
        file_rel_path = "src/core/customs_fx_engine.py"
        source_path = pathlib.Path(file_rel_path)
        assert source_path.exists(), f"{file_rel_path} must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer", "rich"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed external import '{pkg}' in {file_rel_path}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed external from-import '{pkg}' in {file_rel_path}"


# ============================================================================
# 2. Phase 167: Customs Valuation & ROO Engine Tests
# ============================================================================


class TestCustomsValuationOriginEngine:
    """Unit tests for Customs Valuation, Rules of Origin & Post-Clearance Audits."""

    def test_calculate_transaction_value_full(self) -> None:
        res = CustomsValuationOriginEngine.calculate_transaction_value(
            invoice_price_vnd=500_000_000,
            freight_international_vnd=35_000_000,
            insurance_international_vnd=5_000_000,
            royalties_license_fees_vnd=10_000_000,
            assists_value_vnd=5_000_000,
            post_import_construction_install_vnd=3_000_000,
            post_import_inland_freight_vnd=2_000_000,
            duties_taxes_in_vietnam_vnd=1_000_000,
        )
        assert res.method == CustomsValuationMethod.METHOD_1_TRANSACTION_VALUE
        assert res.invoice_price_vnd == 500_000_000
        assert res.total_additions_vnd == 55_000_000
        assert res.total_deductions_vnd == 6_000_000
        assert res.assessable_customs_value_vnd == 549_000_000
        assert "add_international_freight" in res.breakdown
        assert "deduct_post_import_inland_freight" in res.breakdown
        assert "39/2015/TT-BTC" in res.legal_basis

    def test_calculate_transaction_value_zero_adjustments(self) -> None:
        res = CustomsValuationOriginEngine.calculate_transaction_value(
            invoice_price_vnd=100_000_000,
        )
        assert res.invoice_price_vnd == 100_000_000
        assert res.total_additions_vnd == 0.0
        assert res.total_deductions_vnd == 0.0
        assert res.assessable_customs_value_vnd == 100_000_000

    def test_calculate_rvc_build_down_qualifies(self) -> None:
        res = CustomsValuationOriginEngine.calculate_regional_value_content(
            fob_price_vnd=100_000_000,
            non_originating_value_vnd=40_000_000,
            formula="build_down",
            threshold_percentage=40.0,
            agreement_code="ATIGA",
        )
        # RVC = ((100M - 40M) / 100M) * 100% = 60.0%
        assert res.rvc_percentage == 60.0
        assert res.is_originating is True
        assert res.threshold_percentage == 40.0
        assert "Build-down" in res.calculation_formula
        assert res.agreement_code == "ATIGA"
        assert "ĐẠT TIÊU CHÍ XUẤT XỨ" in res.advice_vn

    def test_calculate_rvc_build_down_fails(self) -> None:
        res = CustomsValuationOriginEngine.calculate_regional_value_content(
            fob_price_vnd=100_000_000,
            non_originating_value_vnd=75_000_000,
            formula="build_down",
            threshold_percentage=40.0,
        )
        # RVC = ((100M - 75M) / 100M) * 100% = 25.0%
        assert res.rvc_percentage == 25.0
        assert res.is_originating is False
        assert "KHÔNG ĐẠT TIÊU CHÍ" in res.advice_vn

    def test_calculate_rvc_build_up(self) -> None:
        res = CustomsValuationOriginEngine.calculate_regional_value_content(
            fob_price_vnd=200_000_000,
            originating_value_vnd=100_000_000,
            formula="build_up",
            threshold_percentage=45.0,
            agreement_code="CPTPP",
        )
        # RVC = (100M / 200M) * 100% = 50.0%
        assert res.rvc_percentage == 50.0
        assert res.is_originating is True
        assert "Build-up" in res.calculation_formula

    def test_calculate_rvc_invalid_fob(self) -> None:
        with pytest.raises(ValueError, match="FOB price must be positive"):
            CustomsValuationOriginEngine.calculate_regional_value_content(fob_price_vnd=0.0)

    def test_calculate_rvc_unknown_formula(self) -> None:
        with pytest.raises(ValueError, match="Unknown formula"):
            CustomsValuationOriginEngine.calculate_regional_value_content(
                fob_price_vnd=100_000,
                formula="unknown_xyz",
            )

    def test_check_post_clearance_audit_within_window(self) -> None:
        status = CustomsValuationOriginEngine.check_post_clearance_audit(
            declaration_date_str="2024-01-01",
            audit_date_str="2026-01-01",
        )
        assert status.is_within_5_year_audit_window is True
        assert status.days_passed == 731
        assert status.remaining_days == 1825 - 731
        assert "CÒN TRONG THỜI HIỆU" in status.advice_vn

    def test_check_post_clearance_audit_expired(self) -> None:
        status = CustomsValuationOriginEngine.check_post_clearance_audit(
            declaration_date_str="2018-01-01",
            audit_date_str="2026-01-01",
        )
        assert status.is_within_5_year_audit_window is False
        assert status.days_passed > 1825
        assert status.remaining_days == 0
        assert "ĐÃ HẾT THỜI HIỆU" in status.advice_vn


# ============================================================================
# 3. Phase 168: Foreign Exchange & SBV Loan Engine Tests
# ============================================================================


class TestForeignExchangeControlEngine:
    """Unit tests for SBV Foreign Loan Registration & FDI Profit Remittance."""

    def test_evaluate_sbv_loan_short_term_exempt(self) -> None:
        res = ForeignExchangeControlEngine.evaluate_sbv_loan_registration(
            principal_amount=500_000,
            currency="USD",
            tenor_months=6,
            is_extended_short_term=False,
        )
        assert res.tenor_category == LoanTenorCategory.SHORT_TERM
        assert res.requires_sbv_registration is False
        assert res.registration_deadline_days == 0
        assert "KHÔNG PHẢI ĐĂNG KÝ" in res.advice_vn

    def test_evaluate_sbv_loan_medium_long_term_mandatory(self) -> None:
        res = ForeignExchangeControlEngine.evaluate_sbv_loan_registration(
            principal_amount=2_000_000,
            currency="USD",
            tenor_months=36,
        )
        assert res.tenor_category == LoanTenorCategory.MEDIUM_LONG_TERM
        assert res.requires_sbv_registration is True
        assert res.registration_deadline_days == 30
        assert "DICA" in res.account_type_required
        assert "BẮT BUỘC PHẢI ĐĂNG KÝ" in res.advice_vn

    def test_evaluate_sbv_loan_extended_short_term(self) -> None:
        res = ForeignExchangeControlEngine.evaluate_sbv_loan_registration(
            principal_amount=300_000,
            currency="EUR",
            tenor_months=12,
            is_extended_short_term=True,
        )
        assert res.requires_sbv_registration is True
        assert res.tenor_category == LoanTenorCategory.MEDIUM_LONG_TERM

    def test_evaluate_sbv_loan_invalid_inputs(self) -> None:
        with pytest.raises(ValueError, match="principal must be positive"):
            ForeignExchangeControlEngine.evaluate_sbv_loan_registration(-100, "USD", 12)

        with pytest.raises(ValueError, match="Tenor must be at least 1 month"):
            ForeignExchangeControlEngine.evaluate_sbv_loan_registration(100, "USD", 0)

    def test_check_fdi_profit_remittance_eligible(self) -> None:
        res = ForeignExchangeControlEngine.check_fdi_profit_remittance(
            enterprise_name="Vietnam High-Tech Manufacturing Ltd",
            current_year_net_profit_vnd=5_000_000_000,
            accumulated_losses_vnd=0,
            has_audited_financial_statements=True,
            tax_obligations_completed=True,
        )
        assert res.is_eligible_for_remittance is True
        assert res.maximum_remittance_amount_vnd == 5_000_000_000
        assert "ĐỦ ĐIỀU KIỆN CHUYỂN LỢI NHUẬN" in res.advice_vn

    def test_check_fdi_profit_remittance_ineligible_losses(self) -> None:
        res = ForeignExchangeControlEngine.check_fdi_profit_remittance(
            enterprise_name="Vietnam Solar SPV Ltd",
            current_year_net_profit_vnd=3_000_000_000,
            accumulated_losses_vnd=1_000_000_000,
            has_audited_financial_statements=True,
            tax_obligations_completed=True,
        )
        assert res.is_eligible_for_remittance is False
        assert res.maximum_remittance_amount_vnd == 0.0
        assert "lỗ lũy kế" in res.advice_vn

    def test_check_fdi_profit_remittance_ineligible_unaudited(self) -> None:
        res = ForeignExchangeControlEngine.check_fdi_profit_remittance(
            enterprise_name="Test Corp",
            current_year_net_profit_vnd=1_000_000_000,
            accumulated_losses_vnd=0,
            has_audited_financial_statements=False,
            tax_obligations_completed=True,
        )
        assert res.is_eligible_for_remittance is False


# ============================================================================
# 4. Phase 169: Technology Transfer & IP Licensing Royalty Engine Tests
# ============================================================================


class TestTechnologyTransferEngine:
    """Unit tests for Tech Transfer Contract Registration & Royalty Valuations."""

    def test_evaluate_contract_registration_cross_border(self) -> None:
        res = TechnologyTransferEngine.evaluate_contract_registration(
            transfer_type="Semiconductor IP transfer from Germany",
            is_cross_border=True,
            involves_state_capital=False,
        )
        assert res.requires_mandatory_registration is True
        assert res.registration_deadline_days == 90
        assert "BKHCN" in res.registration_authority
        assert "BẮT BUỘC ĐĂNG KÝ" in res.advice_vn

    def test_evaluate_contract_registration_domestic_private(self) -> None:
        res = TechnologyTransferEngine.evaluate_contract_registration(
            transfer_type="Domestic software license",
            is_cross_border=False,
            involves_state_capital=False,
        )
        assert res.requires_mandatory_registration is False
        assert res.registration_deadline_days == 0
        assert "Tự nguyện" in res.registration_authority

    def test_calculate_running_royalty_standard(self) -> None:
        res = TechnologyTransferEngine.calculate_running_royalty(
            gross_revenue_vnd=100_000_000_000,
            discounts_returns_vnd=2_000_000_000,
            packing_shipping_vnd=1_000_000_000,
            duties_taxes_vnd=1_000_000_000,
            royalty_rate_pct=3.5,
            projected_operating_profit_vnd=20_000_000_000,
        )
        assert res.gross_revenue_vnd == 100_000_000_000
        assert res.deductions_vnd == 4_000_000_000
        assert res.net_sales_vnd == 96_000_000_000
        # Royalty = 96B * 3.5% = 3,360,000,000 VND
        assert res.royalty_payable_vnd == 3_360_000_000
        assert res.is_within_market_standard is True
        # Profit split benchmark = 20B * 25% = 5,000,000,000 VND
        assert res.profit_split_benchmark_vnd == 5_000_000_000
        assert "25% Profit Split" in res.advice_vn

    def test_calculate_running_royalty_abnormal_rate(self) -> None:
        res = TechnologyTransferEngine.calculate_running_royalty(
            gross_revenue_vnd=10_000_000_000,
            royalty_rate_pct=12.0,  # > 8.0%
        )
        assert res.is_within_market_standard is False
        assert "CẢNH BÁO" in res.advice_vn


# ============================================================================
# 5. Phase 170: Bonded Warehouse & CFS Logistics Operation Engine Tests
# ============================================================================


class TestBondedLogisticsEngine:
    """Unit tests for Bonded Warehouse & CFS time limits and operations."""

    def test_evaluate_bonded_warehouse_within_initial(self) -> None:
        status = BondedLogisticsEngine.evaluate_storage_period(
            facility_type="bonded_warehouse",
            entry_date_str="2025-06-01",
            check_date_str="2026-01-01",
            already_extended=False,
        )
        assert status.facility_type == StorageFacilityType.BONDED_WAREHOUSE
        assert status.statutory_max_initial_days == 365
        assert status.maximum_possible_days_with_extension == 730
        assert status.is_within_initial_term is True
        assert status.is_expired is False
        assert status.can_request_extension is True
        assert status.days_stored == 214
        assert len(status.allowed_operations) >= 4

    def test_evaluate_bonded_warehouse_expired_initial(self) -> None:
        status = BondedLogisticsEngine.evaluate_storage_period(
            facility_type="bonded",
            entry_date_str="2024-01-01",
            check_date_str="2025-06-01",
            already_extended=False,
        )
        assert status.is_within_initial_term is False
        assert status.is_expired is True
        assert status.can_request_extension is False
        assert "ĐÃ HẾT HẠN LƯU KHO" in status.advice_vn

    def test_evaluate_bonded_warehouse_extended_ok(self) -> None:
        status = BondedLogisticsEngine.evaluate_storage_period(
            facility_type="bonded_warehouse",
            entry_date_str="2024-06-01",
            check_date_str="2025-06-01",
            already_extended=True,
        )
        assert status.is_expired is False
        assert status.can_request_extension is False
        assert "giai đoạn gia hạn" in status.advice_vn

    def test_evaluate_cfs_station_within_limit(self) -> None:
        status = BondedLogisticsEngine.evaluate_storage_period(
            facility_type="cfs_station",
            entry_date_str="2026-01-01",
            check_date_str="2026-02-15",
        )
        assert status.facility_type == StorageFacilityType.CFS_STATION
        assert status.statutory_max_initial_days == 90
        assert status.is_expired is False
        assert status.can_request_extension is False

    def test_evaluate_cfs_station_expired(self) -> None:
        status = BondedLogisticsEngine.evaluate_storage_period(
            facility_type="cfs",
            entry_date_str="2025-10-01",
            check_date_str="2026-02-15",
        )
        assert status.is_expired is True
        assert "QUÁ THỜI HẠN 90 NGÀY" in status.advice_vn


# ============================================================================
# 6. CLI Commands & Dual-Group Integration Tests
# ============================================================================


class TestCustomsCLICommands:
    """Test Typer CLI commands under 'customs' and 'haiquan' groups."""

    @pytest.fixture(scope="class")
    def app(self):
        return build_app()

    def test_customs_default_rich_and_json(self, app) -> None:
        # Default rich table
        res_rich = runner.invoke(app, ["customs"])
        assert res_rich.exit_code == 0
        assert "MEKONG CUSTOMS" in res_rich.output

        # JSON mode
        res_json = runner.invoke(app, ["customs", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert 167 in data["phases"]
        assert "valuation" in data["subcommands"]

    def test_haiquan_alias_default(self, app) -> None:
        res = runner.invoke(app, ["haiquan", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["phases"] == [167, 168, 169, 170]

    def test_cli_valuation(self, app) -> None:
        res = runner.invoke(app, [
            "customs", "valuation", "500000000",
            "--freight", "35000000",
            "--insurance", "5000000",
            "--royalties", "10000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["assessable_customs_value_vnd"] == 550_000_000

    def test_cli_valuation_rich(self, app) -> None:
        res = runner.invoke(app, [
            "haiquan", "valuation", "200000000",
            "--freight", "15000000",
        ])
        assert res.exit_code == 0
        assert "Method 1" in res.output

    def test_cli_rvc(self, app) -> None:
        res = runner.invoke(app, [
            "customs", "rvc", "1000000",
            "--vnm", "400000",
            "--threshold", "40.0",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["rvc_percentage"] == 60.0
        assert data["is_originating"] is True

    def test_cli_rvc_rich(self, app) -> None:
        res = runner.invoke(app, [
            "haiquan", "rvc", "1000000",
            "--vnm", "800000",
            "--threshold", "40.0",
        ])
        assert res.exit_code == 0
        assert "KHÔNG ĐẠT TIÊU CHÍ" in res.output

    def test_cli_audit_check(self, app) -> None:
        res = runner.invoke(app, [
            "customs", "audit-check", "2023-01-01",
            "--audit-date", "2026-01-01",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_within_5_year_audit_window"] is True

    def test_cli_sbv_loan(self, app) -> None:
        res = runner.invoke(app, [
            "customs", "sbv-loan", "2000000",
            "--currency", "USD",
            "--tenor", "36",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["requires_sbv_registration"] is True
        assert data["registration_deadline_days"] == 30

    def test_cli_profit_remit(self, app) -> None:
        res = runner.invoke(app, [
            "customs", "profit-remit", "FDI Corp", "1000000000",
            "--losses", "0",
            "--audited",
            "--tax-clean",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_eligible_for_remittance"] is True

    def test_cli_tech_registration(self, app) -> None:
        res = runner.invoke(app, [
            "haiquan", "tech-registration", "Cross border patent",
            "--cross-border",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["requires_mandatory_registration"] is True

    def test_cli_royalty(self, app) -> None:
        res = runner.invoke(app, [
            "customs", "royalty", "10000000000",
            "--rate", "4.0",
            "--profit", "2000000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["royalty_payable_vnd"] == 400_000_000
        assert data["profit_split_benchmark_vnd"] == 500_000_000

    def test_cli_storage_check(self, app) -> None:
        res = runner.invoke(app, [
            "haiquan", "storage-check", "cfs", "2026-01-01",
            "--check-date", "2026-02-01",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["facility_type"] == "cfs_station"
        assert data["is_expired"] is False


# ============================================================================
# 7. FastMCP & JSON-RPC Tool Handlers Tests
# ============================================================================


class TestCustomsMCPHandlers:
    """Test FastMCP & JSON-RPC server tool handlers for Customs & FX."""

    def test_mcp_customs_valuation_handler(self) -> None:
        raw = handle_customs_valuation({
            "invoice_price_vnd": 500_000_000,
            "freight_international_vnd": 35_000_000,
            "insurance_international_vnd": 5_000_000,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["assessable_customs_value_vnd"] == 540_000_000

    def test_mcp_customs_rvc_handler(self) -> None:
        raw = handle_customs_rvc({
            "fob_price_vnd": 1000,
            "non_originating_value_vnd": 400,
            "threshold_percentage": 40.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["rvc_percentage"] == 60.0
        assert data["is_originating"] is True

    def test_mcp_fx_loan_handler(self) -> None:
        raw = handle_fx_loan({
            "principal_amount": 1_000_000,
            "currency": "USD",
            "tenor_months": 24,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["requires_sbv_registration"] is True

    def test_mcp_tech_transfer_royalty_handler(self) -> None:
        raw = handle_tech_transfer_royalty({
            "gross_revenue_vnd": 1_000_000_000,
            "royalty_rate_pct": 3.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["royalty_payable_vnd"] == 30_000_000

    def test_mcp_bonded_storage_handler(self) -> None:
        raw = handle_bonded_storage({
            "facility_type": "bonded_warehouse",
            "entry_date_str": "2025-06-01",
            "check_date_str": "2026-01-01",
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["can_request_extension"] is True

    def test_core_handlers_and_spec_registered(self) -> None:
        tools = [
            "mekong_customs_valuation", "customs_valuation",
            "mekong_customs_rvc", "customs_rvc",
            "mekong_fx_loan_registration", "fx_loan_registration",
            "mekong_tech_transfer_royalty", "tech_transfer_royalty",
            "mekong_bonded_storage_period", "bonded_storage_period",
        ]
        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for tool in tools:
            assert tool in CORE_HANDLERS, f"{tool} must be registered in CORE_HANDLERS"
            assert tool in spec_names, f"{tool} must be declared in CORE_TOOLS_SPEC"
