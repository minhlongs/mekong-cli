# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Comprehensive Tests for Mekong FTA Concessions, EPE, AEO & Duty Exemption Suite (Phases 171 - 174).

Covers:
1. AST Boundary & Zero-Dependency Purity (Pure Python Stdlib in src/core/fta_duty_engine.py)
2. Phase 171: FTA Preferential Tariffs & Rules of Origin Engine
3. Phase 172: Export Processing Enterprises (EPE / DNCX) Customs Engine
4. Phase 173: Authorized Economic Operator (AEO) & Risk Channeling Engine
5. Phase 174: Duty Exemption, Refund & Raw Materials Reconciliation (BCQT 15) Engine
6. CLI Commands & Dual-Group Wiring (mekong fta & mekong dncx)
7. FastMCP & JSON-RPC Server Tool Handlers
"""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.fta_duty_engine import (
    FTATariffOriginEngine,
    FTAAgreement,
    OriginCriterion,
    EPECustomsEngine,
    AEOComplianceEngine,
    EnterpriseType,
    DutyExemptionRefundEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_fta_tariff_savings,
    handle_fta_origin_criterion,
    handle_epe_conditions_check,
    handle_aeo_eligibility_eval,
    handle_duty_reconciliation_bcqt15,
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
)

runner = CliRunner()


# ============================================================================
# 1. AST Boundary & Zero-Dependency Purity Tests
# ============================================================================


class TestFTADutyBoundary:
    """Verify fta_duty_engine is 100% Python Standard Library."""

    def test_pure_standard_library_imports(self) -> None:
        file_rel_path = "src/core/fta_duty_engine.py"
        source_path = pathlib.Path(file_rel_path)
        assert source_path.exists(), f"{file_rel_path} must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        allowed_stdlib = {
            "__future__",
            "datetime",
            "typing",
            "dataclasses",
            "enum",
            "math",
            "json",
        }

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        disallowed = imported_modules - allowed_stdlib
        assert not disallowed, f"Disallowed external dependencies in {file_rel_path}: {disallowed}"


# ============================================================================
# 2. Phase 171: FTA Preferential Tariffs & Rules of Origin Engine
# ============================================================================


class TestFTATariffOriginEngine:
    """Tests for FTATariffOriginEngine under EVFTA, CPTPP, RCEP, etc."""

    def test_calculate_tariff_savings_positive(self) -> None:
        res = FTATariffOriginEngine.calculate_tariff_savings(
            customs_value_vnd=1_000_000_000.0,
            mfn_rate_pct=15.0,
            fta_rate_pct=0.0,
            agreement="EVFTA",
        )
        assert res.customs_value_vnd == 1_000_000_000.0
        assert res.mfn_duty_vnd == 150_000_000.0
        assert res.fta_duty_vnd == 0.0
        assert res.duty_savings_vnd == 150_000_000.0
        assert res.savings_pct == 100.0
        assert res.effective_agreement == FTAAgreement.EVFTA.value
        assert "115/2022/NĐ-CP" in res.advice_vn

    def test_calculate_tariff_savings_partial_reduction(self) -> None:
        res = FTATariffOriginEngine.calculate_tariff_savings(
            customs_value_vnd=500_000_000.0,
            mfn_rate_pct=20.0,
            fta_rate_pct=5.0,
            agreement="CPTPP",
        )
        assert res.mfn_duty_vnd == 100_000_000.0
        assert res.fta_duty_vnd == 25_000_000.0
        assert res.duty_savings_vnd == 75_000_000.0
        assert res.savings_pct == 75.0
        assert res.effective_agreement == FTAAgreement.CPTPP.value

    def test_calculate_tariff_savings_no_advantage(self) -> None:
        res = FTATariffOriginEngine.calculate_tariff_savings(
            customs_value_vnd=200_000_000.0,
            mfn_rate_pct=5.0,
            fta_rate_pct=5.0,
            agreement="RCEP",
        )
        assert res.duty_savings_vnd == 0.0
        assert res.savings_pct == 0.0
        assert "không mang lại chênh lệch" in res.advice_vn

    def test_calculate_tariff_savings_validation_error(self) -> None:
        with pytest.raises(ValueError, match="Trị giá hải quan phải là số dương"):
            FTATariffOriginEngine.calculate_tariff_savings(customs_value_vnd=-100.0, mfn_rate_pct=10.0, fta_rate_pct=0.0)

        with pytest.raises(ValueError, match="Thuế suất không được là số âm"):
            FTATariffOriginEngine.calculate_tariff_savings(customs_value_vnd=100.0, mfn_rate_pct=-5.0, fta_rate_pct=0.0)

    def test_evaluate_origin_criterion_wo(self) -> None:
        res = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="0901.11",
            criterion="wo",
            agreement="EVFTA",
        )
        assert res.is_qualified is True
        assert res.criterion == OriginCriterion.WO.value
        assert "thuần túy" in res.details_vn

    def test_evaluate_origin_criterion_ctc_pass(self) -> None:
        # Product in Chapter 62, raw material in Chapter 52 -> Chapter Change (CC) passes
        res = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="6203.42",
            criterion="cc",
            non_originating_materials_hs=["5208.11", "5209.21"],
            agreement="EVFTA",
        )
        assert res.is_qualified is True
        assert "Chuyển đổi Chương" in res.details_vn

    def test_evaluate_origin_criterion_cth_fail_same_heading(self) -> None:
        # Product 6203.42 and material 6203.11 are same heading 6203 -> CTH fails
        res = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="6203.42",
            criterion="cth",
            non_originating_materials_hs=["6203.11"],
            agreement="CPTPP",
        )
        assert res.is_qualified is False
        assert "Không đạt CTH" in res.details_vn

    def test_evaluate_origin_criterion_rvc_pass_and_fail(self) -> None:
        # Passing case >= 40%
        res_pass = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="8708.29",
            criterion="rvc",
            rvc_actual_pct=42.5,
            rvc_threshold_pct=40.0,
            agreement="ATIGA",
        )
        assert res_pass.is_qualified is True
        assert "Đạt tiêu chí hàm lượng RVC" in res_pass.details_vn

        # Failing case < 40%
        res_fail = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="8708.29",
            criterion="rvc",
            rvc_actual_pct=36.0,
            rvc_threshold_pct=40.0,
            agreement="ATIGA",
        )
        assert res_fail.is_qualified is False
        assert "Không đạt tiêu chí RVC" in res_fail.details_vn

    def test_evaluate_origin_criterion_de_minimis(self) -> None:
        # Non-originating ratio 8.5% <= 10.0% -> Passes
        res_pass = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="6203.42",
            criterion="de_minimis",
            non_originating_value_fob_pct=8.5,
            agreement="CPTPP",
        )
        assert res_pass.is_qualified is True
        assert "Đạt quy tắc De Minimis" in res_pass.details_vn

        # Non-originating ratio 12.0% > 10.0% -> Fails
        res_fail = FTATariffOriginEngine.evaluate_origin_criterion(
            product_hs="6203.42",
            criterion="de_minimis",
            non_originating_value_fob_pct=12.0,
            agreement="CPTPP",
        )
        assert res_fail.is_qualified is False
        assert "Không đạt quy tắc De Minimis" in res_fail.details_vn

    def test_determine_proof_of_origin(self) -> None:
        # EVFTA under 6000 EUR
        proof_evfta_small = FTATariffOriginEngine.determine_proof_of_origin(
            agreement="EVFTA",
            consignment_value_eur=4500.0,
        )
        assert "REX" in proof_evfta_small["required_proof_form"]

        # EVFTA over 6000 EUR without approved exporter
        proof_evfta_large = FTATariffOriginEngine.determine_proof_of_origin(
            agreement="EVFTA",
            consignment_value_eur=15000.0,
            is_approved_exporter=False,
        )
        assert "EUR.1" in proof_evfta_large["required_proof_form"]

        # CPTPP
        proof_cptpp = FTATariffOriginEngine.determine_proof_of_origin(agreement="CPTPP")
        assert "CPTPP" in proof_cptpp["required_proof_form"]

        # ATIGA
        proof_atiga = FTATariffOriginEngine.determine_proof_of_origin(agreement="ATIGA")
        assert "Mẫu D" in proof_atiga["required_proof_form"]


# ============================================================================
# 3. Phase 172: Export Processing Enterprises (EPE / DNCX) Customs Engine
# ============================================================================


class TestEPECustomsEngine:
    """Tests for EPE Customs Engine under Decree 35/2022/ND-CP & Circular 38/2015."""

    def test_verify_supervision_conditions_fully_compliant(self) -> None:
        res = EPECustomsEngine.verify_supervision_conditions(
            has_physical_fence=True,
            has_24_7_camera_streaming=True,
            has_separate_gate=True,
            has_erp_connected=True,
        )
        assert res.is_compliant is True
        assert len(res.missing_conditions) == 0
        assert "ĐỦ ĐIỀU KIỆN" in res.recommendations_vn

    def test_verify_supervision_conditions_missing_items(self) -> None:
        res = EPECustomsEngine.verify_supervision_conditions(
            has_physical_fence=True,
            has_24_7_camera_streaming=False,
            has_separate_gate=True,
            has_erp_connected=False,
        )
        assert res.is_compliant is False
        assert len(res.missing_conditions) == 2
        assert "camera" in res.missing_conditions[0].lower()
        assert "erp" in res.missing_conditions[1].lower()
        assert "CHƯA ĐỦ ĐIỀU KIỆN" in res.recommendations_vn

    def test_enforce_on_spot_deadline_within_term(self) -> None:
        res = EPECustomsEngine.enforce_on_spot_deadline(
            export_declaration_date_str="2026-03-01",
            reference_date_str="2026-03-10",
        )
        assert res.days_elapsed == 9
        assert res.is_overdue is False
        assert res.remaining_days == 6
        assert "HỢP LỆ" in res.compliance_status

    def test_enforce_on_spot_deadline_overdue(self) -> None:
        res = EPECustomsEngine.enforce_on_spot_deadline(
            export_declaration_date_str="2026-03-01",
            reference_date_str="2026-03-25",
        )
        assert res.days_elapsed == 24
        assert res.is_overdue is True
        assert res.remaining_days == -9
        assert "QUÁ HẠN" in res.compliance_status

    def test_enforce_on_spot_deadline_invalid_date(self) -> None:
        with pytest.raises(ValueError, match="Định dạng ngày khai báo không hợp lệ"):
            EPECustomsEngine.enforce_on_spot_deadline("invalid-date")

    def test_calculate_scrap_domestic_sale(self) -> None:
        res = EPECustomsEngine.calculate_scrap_domestic_sale(
            scrap_value_vnd=100_000_000.0,
            scrap_hs_code="7204.49",
            import_duty_rate_pct=5.0,
            vat_rate_pct=10.0,
        )
        assert res.scrap_value_vnd == 100_000_000.0
        assert res.import_duty_vnd == 5_000_000.0
        # VAT = (100M + 5M) * 10% = 10,500,000 VND
        assert res.vat_vnd == 10_500_000.0
        assert res.total_tax_payable_vnd == 15_500_000.0
        assert res.declaration_type == "A42"


# ============================================================================
# 4. Phase 173: Authorized Economic Operator (AEO) & Risk Channeling Engine
# ============================================================================


class TestAEOComplianceEngine:
    """Tests for AEO Compliance and Customs Risk Channeling Engine."""

    def test_evaluate_aeo_eligibility_general_trader_qualified(self) -> None:
        res = AEOComplianceEngine.evaluate_aeo_eligibility(
            enterprise_type="GENERAL_TRADER",
            annual_turnover_usd=120_000_000.0,
            compliance_years=2,
            had_major_customs_tax_violations=False,
            has_unqualified_audit=False,
        )
        assert res.is_eligible is True
        assert res.turnover_threshold_usd == 100_000_000.0
        assert len(res.reasons_unqualified) == 0
        assert len(res.statutory_benefits_vn) >= 5
        assert "ĐỦ ĐIỀU KIỆN" in res.summary_vn

    def test_evaluate_aeo_eligibility_agri_sector(self) -> None:
        res = AEOComplianceEngine.evaluate_aeo_eligibility(
            enterprise_type=EnterpriseType.AGRI_AQUA_TEXTILE.value,
            annual_turnover_usd=45_000_000.0,
        )
        assert res.turnover_threshold_usd == 40_000_000.0
        assert res.turnover_qualified is True
        assert res.is_eligible is True

    def test_evaluate_aeo_eligibility_customs_broker(self) -> None:
        # Broker requires 20,000 declarations
        res_pass = AEOComplianceEngine.evaluate_aeo_eligibility(
            enterprise_type=EnterpriseType.CUSTOMS_BROKER.value,
            annual_turnover_usd=0.0,
            customs_broker_declarations=22_000,
        )
        assert res_pass.turnover_qualified is True
        assert res_pass.is_eligible is True

        res_fail = AEOComplianceEngine.evaluate_aeo_eligibility(
            enterprise_type=EnterpriseType.CUSTOMS_BROKER.value,
            annual_turnover_usd=0.0,
            customs_broker_declarations=15_000,
        )
        assert res_fail.turnover_qualified is False
        assert res_fail.is_eligible is False

    def test_evaluate_aeo_eligibility_disqualifications(self) -> None:
        # Fails turnover, compliance years, and has tax violation
        res = AEOComplianceEngine.evaluate_aeo_eligibility(
            enterprise_type="GENERAL_TRADER",
            annual_turnover_usd=80_000_000.0,
            compliance_years=1,
            had_major_customs_tax_violations=True,
            has_unqualified_audit=True,
        )
        assert res.is_eligible is False
        assert len(res.reasons_unqualified) == 4

    def test_assess_customs_risk_channel_aeo(self) -> None:
        res = AEOComplianceEngine.assess_customs_risk_channel(
            is_aeo=True,
            enterprise_risk_score=60.0,  # High risk score ignored for AEO unless targeted alert
            has_intelligence_alert=False,
        )
        assert res.channel == "GREEN"
        assert res.inspection_ratio_pct == 0.0
        assert "Ưu tiên luồng Xanh" in res.rationale_vn

    def test_assess_customs_risk_channel_red_on_alert(self) -> None:
        res = AEOComplianceEngine.assess_customs_risk_channel(
            is_aeo=True,
            has_intelligence_alert=True,
        )
        assert res.channel == "RED"
        assert res.inspection_ratio_pct == 100.0
        assert "Cảnh báo nghiệp vụ trọng điểm" in res.rationale_vn

    def test_assess_customs_risk_channel_yellow_and_red_score(self) -> None:
        # Yellow channel (risk score 30)
        res_yellow = AEOComplianceEngine.assess_customs_risk_channel(
            is_aeo=False,
            enterprise_risk_score=30.0,
        )
        assert res_yellow.channel == "YELLOW"

        # Red channel (risk score 75)
        res_red = AEOComplianceEngine.assess_customs_risk_channel(
            is_aeo=False,
            enterprise_risk_score=75.0,
        )
        assert res_red.channel == "RED"


# ============================================================================
# 5. Phase 174: Duty Exemption, Refund & Raw Materials Reconciliation (BCQT 15)
# ============================================================================


class TestDutyExemptionRefundEngine:
    """Tests for Duty Refund and Form 15/BCQT-NVL/GSQL Material Reconciliation."""

    def test_calculate_sxxk_duty_refund_full(self) -> None:
        res = DutyExemptionRefundEngine.calculate_sxxk_duty_refund(
            total_duty_paid_vnd=200_000_000.0,
            raw_material_imported_qty=10_000.0,
            raw_material_exported_qty=10_000.0,
        )
        assert res.refund_duty_amount_vnd == 200_000_000.0
        assert res.refund_ratio_pct == 100.0
        assert "Điều 36 Nghị định 134/2016/NĐ-CP" in res.advice_vn

    def test_calculate_sxxk_duty_refund_partial(self) -> None:
        res = DutyExemptionRefundEngine.calculate_sxxk_duty_refund(
            total_duty_paid_vnd=200_000_000.0,
            raw_material_imported_qty=10_000.0,
            raw_material_exported_qty=6_000.0,
        )
        assert res.refund_duty_amount_vnd == 120_000_000.0
        assert res.refund_ratio_pct == 60.0

    def test_calculate_reexport_refund(self) -> None:
        # Qualified re-export
        res_pass = DutyExemptionRefundEngine.calculate_reexport_refund(
            total_duty_paid_vnd=50_000_000.0,
            is_goods_unused_in_vietnam=True,
        )
        assert res_pass.refund_duty_amount_vnd == 50_000_000.0
        assert "ĐỦ ĐIỀU KIỆN" in res_pass.advice_vn

        # Disqualified (used/processed in VN)
        res_fail = DutyExemptionRefundEngine.calculate_reexport_refund(
            total_duty_paid_vnd=50_000_000.0,
            is_goods_unused_in_vietnam=False,
        )
        assert res_fail.refund_duty_amount_vnd == 0.0
        assert "KHÔNG ĐỦ ĐIỀU KIỆN" in res_fail.advice_vn

    def test_reconcile_raw_materials_bcqt15_balanced(self) -> None:
        # Opening 1000 + Imported 5000 - Consumed (2000 * 2.0 = 4000) - Scrap 100 = 1900
        res = DutyExemptionRefundEngine.reconcile_raw_materials_bcqt15(
            opening_balance=1000.0,
            imported_in_period=5000.0,
            exported_finished_goods_qty=2000.0,
            bom_consumption_norm=2.0,
            approved_scrap_qty=100.0,
            actual_physical_inventory=1900.0,
        )
        assert res.theoretical_closing_balance == 1900.0
        assert res.actual_physical_inventory == 1900.0
        assert res.variance_qty == 0.0
        assert res.is_balanced is True
        assert res.potential_unpaid_duty_vnd == 0.0

    def test_reconcile_raw_materials_bcqt15_deficit_with_arrears(self) -> None:
        # Theoretical 1900, Actual 1700 -> Deficit 200 units
        res = DutyExemptionRefundEngine.reconcile_raw_materials_bcqt15(
            opening_balance=1000.0,
            imported_in_period=5000.0,
            exported_finished_goods_qty=2000.0,
            bom_consumption_norm=2.0,
            approved_scrap_qty=100.0,
            actual_physical_inventory=1700.0,
            raw_material_unit_duty_vnd=25_000.0,
        )
        assert res.variance_qty == -200.0
        assert res.is_balanced is False
        assert res.is_deficit_risk is True
        assert res.potential_unpaid_duty_vnd == 5_000_000.0
        # 5,000,000 * 0.0003 = 1,500 VND/day
        assert res.late_payment_interest_per_day_vnd == 1500.0
        assert "THIẾU HỤT" in res.audit_warning_vn

    def test_reconcile_raw_materials_bcqt15_surplus(self) -> None:
        # Theoretical 1900, Actual 2050 -> Surplus 150 units
        res = DutyExemptionRefundEngine.reconcile_raw_materials_bcqt15(
            opening_balance=1000.0,
            imported_in_period=5000.0,
            exported_finished_goods_qty=2000.0,
            bom_consumption_norm=2.0,
            approved_scrap_qty=100.0,
            actual_physical_inventory=2050.0,
        )
        assert res.variance_qty == 150.0
        assert res.is_deficit_risk is False
        assert "DƯ THỪA" in res.audit_warning_vn


# ============================================================================
# 6. CLI Commands & Dual-Group Wiring Tests
# ============================================================================


class TestFTACLICommands:
    """Verify Typer CLI commands under mekong fta and alias mekong dncx."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_savings_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "savings", "1000000000", "--mfn", "15.0", "--fta", "0.0", "--agreement", "EVFTA"],
        )
        assert result.exit_code == 0
        assert "EVFTA" in result.stdout
        assert "150,000,000" in result.stdout

    def test_cli_savings_json_mode(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "savings", "1000000000", "--mfn", "15.0", "--fta", "0.0", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["duty_savings_vnd"] == 150_000_000.0
        assert data["savings_pct"] == 100.0

    def test_cli_origin_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["dncx", "origin", "6203.42", "--criterion", "cth", "--non-orig-hs", "5208.11", "--agreement", "CPTPP"],
        )
        assert result.exit_code == 0
        assert "6203.42" in result.stdout

    def test_cli_proof_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "proof", "--agreement", "EVFTA", "--value-eur", "5000"],
        )
        assert result.exit_code == 0
        assert "EVFTA" in result.stdout

    def test_cli_epe_check_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "epe-check", "--barrier", "--camera", "--gate", "--erp"],
        )
        assert result.exit_code == 0
        assert "ĐỦ ĐIỀU KIỆN" in result.stdout

    def test_cli_on_spot_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["dncx", "on-spot", "2026-03-01", "--import-date", "2026-03-10"],
        )
        assert result.exit_code == 0
        assert "HỢP LỆ" in result.stdout

    def test_cli_scrap_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "scrap", "50000000", "--hs", "7204.49", "--duty", "5.0"],
        )
        assert result.exit_code == 0
        assert "A42" in result.stdout

    def test_cli_aeo_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "aeo", "--enterprise-type", "GENERAL_TRADER", "--turnover-usd", "150000000"],
        )
        assert result.exit_code == 0
        assert "ĐỦ ĐIỀU KIỆN" in result.stdout

    def test_cli_channel_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "channel", "--aeo"],
        )
        assert result.exit_code == 0
        assert "LUỒNG XANH" in result.stdout

    def test_cli_refund_sxxk_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["fta", "refund-sxxk", "100000000", "5000", "3000"],
        )
        assert result.exit_code == 0
        assert "60,000,000" in result.stdout

    def test_cli_bcqt_command(self) -> None:
        result = runner.invoke(
            self.app,
            ["dncx", "bcqt", "1000", "5000", "2000", "--bom", "2.0", "--actual", "1900"],
        )
        assert result.exit_code == 0
        assert "CÂN BẰNG" in result.stdout


# ============================================================================
# 7. FastMCP & JSON-RPC Server Tool Handlers Tests
# ============================================================================


class TestFTAMCPHandlers:
    """Verify JSON-RPC tool handlers and CORE_TOOLS_SPEC mappings."""

    def test_mcp_core_handlers_registration(self) -> None:
        expected_tools = [
            "mekong_fta_tariff_savings",
            "fta_tariff_savings",
            "mekong_fta_origin_criterion",
            "fta_origin_criterion",
            "mekong_epe_conditions_check",
            "epe_conditions_check",
            "mekong_aeo_eligibility_eval",
            "aeo_eligibility_eval",
            "mekong_duty_reconciliation_bcqt15",
            "duty_reconciliation_bcqt15",
        ]
        for tool_name in expected_tools:
            assert tool_name in CORE_HANDLERS, f"{tool_name} must be in CORE_HANDLERS"

    def test_mcp_core_tools_spec_presence(self) -> None:
        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        assert "mekong_fta_tariff_savings" in tool_names
        assert "mekong_fta_origin_criterion" in tool_names
        assert "mekong_epe_conditions_check" in tool_names
        assert "mekong_aeo_eligibility_eval" in tool_names
        assert "mekong_duty_reconciliation_bcqt15" in tool_names

    def test_handle_fta_tariff_savings(self) -> None:
        payload = {
            "customs_value_vnd": 500_000_000.0,
            "mfn_rate_pct": 10.0,
            "fta_rate_pct": 0.0,
            "agreement": "EVFTA",
        }
        res_raw = handle_fta_tariff_savings(payload)
        data = json.loads(res_raw)
        assert data["ok"] is True
        assert data["duty_savings_vnd"] == 50_000_000.0
        assert data["effective_agreement"] == "EVFTA"

    def test_handle_fta_origin_criterion(self) -> None:
        payload = {
            "product_hs": "6203.42",
            "criterion": "cc",
            "non_originating_materials_hs": ["5208.11"],
            "agreement": "EVFTA",
        }
        res_raw = handle_fta_origin_criterion(payload)
        data = json.loads(res_raw)
        assert data["ok"] is True
        assert data["is_qualified"] is True

    def test_handle_epe_conditions_check(self) -> None:
        payload = {
            "barrier_fenced": True,
            "camera_online_streaming": True,
            "separate_gate": True,
            "erp_inventory_connected": True,
        }
        res_raw = handle_epe_conditions_check(payload)
        data = json.loads(res_raw)
        assert data["ok"] is True
        assert data["is_compliant"] is True

    def test_handle_aeo_eligibility_eval(self) -> None:
        payload = {
            "enterprise_type": "GENERAL_TRADER",
            "annual_turnover_usd": 150_000_000.0,
            "compliance_years": 2,
        }
        res_raw = handle_aeo_eligibility_eval(payload)
        data = json.loads(res_raw)
        assert data["ok"] is True
        assert data["is_eligible"] is True

    def test_handle_duty_reconciliation_bcqt15(self) -> None:
        payload = {
            "opening_inventory_qty": 1000.0,
            "imported_qty": 5000.0,
            "exported_qty": 2000.0,
            "standard_bom": 2.0,
            "scrap_qty": 100.0,
            "actual_physical_inventory_qty": 1900.0,
        }
        res_raw = handle_duty_reconciliation_bcqt15(payload)
        data = json.loads(res_raw)
        assert data["ok"] is True
        assert data["is_balanced"] is True
