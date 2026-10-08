# -*- coding: utf-8 -*-
"""Comprehensive Test Suite for Phases 263-266.

Phases Covered:
- Phase 263: Letter of Indemnity (LOI) & Switch B/L Risk Evaluation Under VMC 2015 & IG P&I
- Phase 264: General Average (GA) Adjustment Under York-Antwerp Rules 2016 & VMC 2015
- Phase 265: Bunker Delivery Note (BDN) & MARPOL Annex VI Fuel Sulfur Compliance
- Phase 266: Seaport Container Demurrage & Detention (D&D) Progressive Tariffs Under Circular 39/2023
"""

import ast
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.maritime_loi_ga_bunker_demurrage_engine import (
    LOIType,
    BankGuaranteeStatus,
    LOIEvaluationInput,
    LOIRiskEngine,
    GASacrificeExpenditure,
    ContributoryValues,
    GeneralAverageEngine,
    FuelGrade,
    EmissionControlArea,
    BunkerDeliveryData,
    BunkerMARPOLComplianceEngine,
    ContainerType,
    FreeTimePolicy,
    DemurrageDetentionEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_loi_risk_evaluate,
    handle_general_average_adjust,
    handle_bunker_sulfur_compliance_check,
    handle_demurrage_detention_calculate,
)


# ==============================================================================
# 1. ZERO-DEPENDENCY AST ARCHITECTURAL INVARIANT TEST
# ==============================================================================

def test_core_engine_zero_dependencies():
    """Verify that core engine imports only Python standard library modules."""
    engine_path = Path("/Users/macbook/mekong-cli/src/core/maritime_loi_ga_bunker_demurrage_engine.py")
    assert engine_path.exists(), "Engine file must exist"

    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])

    stdlib_modules = {
        "__future__",
        "dataclasses",
        "enum",
        "math",
        "typing",
        "json",
        "datetime",
        "sys",
        "os",
    }
    invalid_imports = imported_modules - stdlib_modules
    assert not invalid_imports, f"Core engine has external dependencies: {invalid_imports}"


# ==============================================================================
# 2. PHASE 263: LETTER OF INDEMNITY (LOI) & SWITCH B/L TESTS
# ==============================================================================

def test_loi_delivery_without_bl_first_class_bank():
    """Verify standard delivery without B/L with first class bank co-guarantee."""
    inp = LOIEvaluationInput(
        vessel_name="MV_PACIFIC_VOYAGER",
        voyage_number="VOY-2026-01",
        loi_type=LOIType.DELIVERY_WITHOUT_ORIGINAL_BL,
        cargo_cif_value_usd=1000000.0,
        requested_indemnity_multiplier=2.0,
        bank_status=BankGuaranteeStatus.FIRST_CLASS_INTERNATIONAL_BANK,
        charterer_name="GLOBAL_COMMODITIES_LTD",
    )
    res = LOIRiskEngine.evaluate_loi(inp)

    assert res.cargo_cif_value_usd == 1000000.0
    assert res.recommended_guarantee_amount_usd == 2000000.0
    assert res.provided_guarantee_amount_usd == 2000000.0
    assert res.guarantee_adequacy_ratio == 1.0
    assert res.is_pi_club_cover_prejudiced is True
    assert res.risk_level == "MEDIUM_ACCEPTABLE"
    assert "HIỆU LỰC CÓ ĐIỀU KIỆN KÈM BẢO LÃNH NGÂN HÀNG" in res.enforceability_status
    assert "6 năm" in res.validity_period_assessment
    assert res.to_dict()["vessel_name"] == "MV_PACIFIC_VOYAGER"


def test_loi_unsecured_corporate_only():
    """Verify high risk when LOI is backed by unsecured charterer signature only."""
    inp = LOIEvaluationInput(
        vessel_name="MV_MEKONG_STAR",
        voyage_number="VOY-2026-02",
        loi_type=LOIType.DELIVERY_WITHOUT_ORIGINAL_BL,
        cargo_cif_value_usd=1500000.0,
        requested_indemnity_multiplier=1.2,
        bank_status=BankGuaranteeStatus.UNSECURED_CORPORATE_ONLY,
        charterer_name="SHADOW_TRADER_CO",
    )
    res = LOIRiskEngine.evaluate_loi(inp)

    assert res.recommended_guarantee_amount_usd == 1800000.0
    assert res.guarantee_adequacy_ratio == 0.4
    assert res.risk_level == "HIGH_UNSECURED"
    assert "RỦI RO CAO" in res.enforceability_status


def test_loi_clean_bl_against_defects_fraud_unenforceable():
    """Verify clean B/L against defects is classified as CRITICAL_FRAUDULENT and VOID."""
    inp = LOIEvaluationInput(
        vessel_name="MV_HAIPHONG_EXPRESS",
        voyage_number="VOY-2026-03",
        loi_type=LOIType.CLEAN_BL_AGAINST_DEFECTS,
        cargo_cif_value_usd=800000.0,
        requested_indemnity_multiplier=2.0,
        bank_status=BankGuaranteeStatus.FIRST_CLASS_INTERNATIONAL_BANK,
        charterer_name="EXPORT_AGRI_VN",
    )
    res = LOIRiskEngine.evaluate_loi(inp)

    assert res.risk_level == "CRITICAL_FRAUDULENT"
    assert "VÔ HIỆU DO GIAN LẬN THƯƠNG MẠI" in res.enforceability_status
    assert any("The Brown Jenkinson" in rec for rec in res.recommendations)


def test_loi_change_of_discharge_port():
    """Verify change of discharge port LOI risk assessment."""
    inp = LOIEvaluationInput(
        vessel_name="MV_SAIGON_QUEEN",
        voyage_number="VOY-2026-04",
        loi_type=LOIType.CHANGE_OF_DISCHARGE_PORT,
        cargo_cif_value_usd=2000000.0,
        requested_indemnity_multiplier=2.0,
        bank_status=BankGuaranteeStatus.LOCAL_COMMERCIAL_BANK,
        charterer_name="IMPORT_CORP_VN",
    )
    res = LOIRiskEngine.evaluate_loi(inp)

    assert res.risk_level == "MEDIUM_ACCEPTABLE"
    assert res.cargo_cif_value_usd == 2000000.0
    assert res.recommended_guarantee_amount_usd == 4000000.0


# ==============================================================================
# 3. PHASE 264: GENERAL AVERAGE (GA) ADJUSTMENT TESTS
# ==============================================================================

def test_ga_standard_adjustment_calculation():
    """Verify full York-Antwerp Rules 2016 GA calculation."""
    exp = GASacrificeExpenditure(
        ship_damage_sacrifice_usd=250000.0,
        cargo_jettison_sacrifice_usd=400000.0,
        salvage_award_allowable_usd=180000.0,
        port_of_refuge_expenses_usd=120000.0,
        adjuster_fee_and_legal_usd=50000.0,
    )
    cont = ContributoryValues(
        ship_sound_value_usd=8000000.0,
        ship_deductions_usd=150000.0,
        cargo_cif_value_usd=12000000.0,
        cargo_deductions_usd=300000.0,
        freight_at_risk_gross_usd=600000.0,
    )

    res = GeneralAverageEngine.calculate_adjustment(exp, cont)

    # Base expenditure: 250k + 400k + 180k + 120k + 50k = 1,000,000
    # Rule XX (2% on base: 1,000,000 * 0.02 = 20,000)
    # Total before interest = 1,020,000
    # Rule XXI Interest (7% p.a. for 1 yr on 1,020,000 = 71,400)
    # Total GA allowances = 1,091,400
    assert res.total_ga_allowances_usd == 1091400.0

    # Net contributory:
    # Ship: 8,000,000 - 150,000 + 250,000 = 8,100,000
    # Cargo: 12,000,000 - 300,000 + 400,000 = 12,100,000
    # Freight: 600,000 - 0 = 600,000
    # Total contributory = 20,800,000
    assert res.total_contributory_value_usd == 20800000.0

    expected_rate = (1091400.0 / 20800000.0) * 100.0
    assert abs(res.ga_contribution_rate_percentage - expected_rate) < 1e-4

    # Cargo net balance: Cargo sacrifice 400k - Cargo contribution (~634.9k) = negative (must pay)
    assert res.cargo_net_balance_usd < 0.0
    # Recommended cash deposit includes 20% contingency
    assert res.recommended_cash_deposit_pct > res.ga_contribution_rate_percentage
    assert "Điều 290-302" in res.legal_statute_reference
    assert res.to_dict()["total_ga_allowances_usd"] == 1091400.0


def test_ga_zero_contributory_value_raises():
    """Verify ValueError is raised if total contributory value is non-positive."""
    exp = GASacrificeExpenditure()
    cont = ContributoryValues(
        ship_sound_value_usd=0.0,
        cargo_cif_value_usd=0.0,
        freight_at_risk_gross_usd=0.0,
    )
    with pytest.raises(ValueError, match="phải lớn hơn 0"):
        GeneralAverageEngine.calculate_adjustment(exp, cont)


def test_ga_positive_net_balance_for_sacrificing_party():
    """Verify party whose sacrifice exceeds contribution is in net credit."""
    exp = GASacrificeExpenditure(
        ship_damage_sacrifice_usd=1500000.0,  # Huge ship sacrifice
        cargo_jettison_sacrifice_usd=0.0,
        salvage_award_allowable_usd=0.0,
        port_of_refuge_expenses_usd=0.0,
        adjuster_fee_and_legal_usd=0.0,
    )
    cont = ContributoryValues(
        ship_sound_value_usd=5000000.0,
        ship_deductions_usd=0.0,
        cargo_cif_value_usd=15000000.0,
        cargo_deductions_usd=0.0,
        freight_at_risk_gross_usd=0.0,
    )
    res = GeneralAverageEngine.calculate_adjustment(exp, cont, include_rule_xx_commission=False, interest_rate_p_a=0.0)

    # Ship allowance = 1.5M, Total contributory = (5M + 1.5M) + 15M = 21.5M
    # Ship contribution = ~453.4k. Net balance = 1.5M - 453.4k > 0 (Ship receives money)
    assert res.ship_net_balance_usd > 0.0
    assert res.cargo_net_balance_usd < 0.0


# ==============================================================================
# 4. PHASE 265: BUNKER DELIVERY NOTE (BDN) & SULFUR TESTS
# ==============================================================================

def test_bunker_vlsfo_compliant_open_sea():
    """Verify standard VLSFO <= 0.50% complies in open sea."""
    bunker = BunkerDeliveryData(
        bdn_number="BDN-2026-9001",
        bunkering_date="2026-10-08",
        port_name="VUNG_TAU_OFFSHORE",
        fuel_grade=FuelGrade.VLSFO,
        supplied_quantity_mt=400.0,
        density_at_15c_kg_m3=985.0,
        viscosity_cst=380.0,
        flash_point_celsius=65.0,
        tested_sulfur_content_pct=0.48,
        has_scrubber_installed=False,
    )
    res = BunkerMARPOLComplianceEngine.evaluate_bunker_sample(bunker, EmissionControlArea.GLOBAL_OPEN_SEA)

    assert res.is_sulfur_compliant is True
    assert res.is_flash_point_safe is True
    assert res.is_bdn_legally_valid is True
    assert "AN TOÀN" in res.statutory_sanction_risk
    assert res.estimated_debunkering_cost_usd == 0.0
    assert res.marpol_record_retention_years == 3
    assert res.sample_retention_months == 12


def test_bunker_vlsfo_non_compliant_in_eca_zone():
    """Verify VLSFO 0.48% violates 0.10% sulfur limit in ECA zone."""
    bunker = BunkerDeliveryData(
        bdn_number="BDN-2026-9002",
        bunkering_date="2026-10-08",
        port_name="ROTTERDAM",
        fuel_grade=FuelGrade.VLSFO,
        supplied_quantity_mt=300.0,
        density_at_15c_kg_m3=985.0,
        viscosity_cst=380.0,
        flash_point_celsius=66.0,
        tested_sulfur_content_pct=0.45,
        has_scrubber_installed=False,
    )
    res = BunkerMARPOLComplianceEngine.evaluate_bunker_sample(bunker, EmissionControlArea.IMO_ECA_ZONE)

    assert res.is_sulfur_compliant is False
    assert res.applicable_sulfur_limit_pct == 0.10
    assert "NGHIÊM TRỌNG" in res.statutory_sanction_risk
    assert res.estimated_debunkering_cost_usd > 0.0


def test_bunker_hsfo_compliant_with_scrubber():
    """Verify HSFO > 0.50% complies when EGCS scrubber SO2/CO2 ratio <= 21.7."""
    bunker = BunkerDeliveryData(
        bdn_number="BDN-2026-9003",
        bunkering_date="2026-10-08",
        port_name="SINGAPORE",
        fuel_grade=FuelGrade.HSFO,
        supplied_quantity_mt=800.0,
        density_at_15c_kg_m3=991.0,
        viscosity_cst=380.0,
        flash_point_celsius=72.0,
        tested_sulfur_content_pct=2.85,
        has_scrubber_installed=True,
        scrubber_so2_co2_ratio=18.5,  # <= 21.7 compliant
    )
    res = BunkerMARPOLComplianceEngine.evaluate_bunker_sample(bunker, EmissionControlArea.GLOBAL_OPEN_SEA)

    assert res.is_sulfur_compliant is True
    assert res.scrubber_equivalence_accepted is True
    assert "ĐẠT" in res.compliance_summary


def test_bunker_solas_flash_point_hazard():
    """Verify flash point < 60°C violates SOLAS Chapter II-2 fire safety."""
    bunker = BunkerDeliveryData(
        bdn_number="BDN-2026-9004",
        bunkering_date="2026-10-08",
        port_name="HAI_PHONG",
        fuel_grade=FuelGrade.MGO,
        supplied_quantity_mt=150.0,
        density_at_15c_kg_m3=850.0,
        viscosity_cst=4.5,
        flash_point_celsius=54.0,  # Below 60°C
        tested_sulfur_content_pct=0.08,
        has_scrubber_installed=False,
    )
    res = BunkerMARPOLComplianceEngine.evaluate_bunker_sample(bunker, EmissionControlArea.IMO_ECA_ZONE)

    assert res.is_flash_point_safe is False
    assert "NGUY CƠ HỎA HOẠN" in res.statutory_sanction_risk
    assert res.estimated_debunkering_cost_usd > 0.0


# ==============================================================================
# 5. PHASE 266: SEAPORT DEMURRAGE & DETENTION (D&D) TESTS
# ==============================================================================

def test_demurrage_within_free_time():
    """Verify zero fees when dwell time is strictly within free periods."""
    res = DemurrageDetentionEngine.calculate_charges(
        container_id="CMAU-1029384",
        container_type=ContainerType.DRY_20FT,
        total_dwell_days=4,
        policy=FreeTimePolicy(terminal_free_days=5, carrier_equipment_free_days=7),
    )

    assert res.terminal_demurrage_days == 0
    assert res.terminal_demurrage_fee_vnd == 0.0
    assert res.carrier_detention_days == 0
    assert res.carrier_detention_fee_vnd == 0.0
    assert res.total_dd_charges_vnd == 0.0
    assert res.is_maritime_lien_warning is False


def test_demurrage_progressive_brackets_dry_20ft():
    """Verify tiered progressive demurrage and detention charges for Dry 20ft."""
    # total_dwell = 14 days
    # terminal_free = 5 days -> overdue = 9 days (Tier 1: 5 days @ 45k = 225k; Tier 2: 4 days @ 75k = 300k -> Demurrage = 525,000 VND)
    # equipment_free = 7 days -> overdue = 7 days (Tier 1: 5 days @ 250k = 1.25M; Tier 2: 2 days @ 380k = 760k -> Detention = 2,010,000 VND)
    # Total = 2,535,000 VND
    res = DemurrageDetentionEngine.calculate_charges(
        container_id="TEMU-8821941",
        container_type=ContainerType.DRY_20FT,
        total_dwell_days=14,
        policy=FreeTimePolicy(terminal_free_days=5, carrier_equipment_free_days=7),
    )

    assert res.terminal_demurrage_days == 9
    assert res.terminal_demurrage_fee_vnd == 525000.0
    assert res.carrier_detention_days == 7
    assert res.carrier_detention_fee_vnd == 2010000.0
    assert res.total_dd_charges_vnd == 2535000.0
    assert res.is_maritime_lien_warning is False


def test_demurrage_maritime_lien_trigger_on_high_ratio():
    """Verify maritime lien alert when D&D exceeds 70% of cargo value."""
    # Cargo value low: 3,000,000 VND
    res = DemurrageDetentionEngine.calculate_charges(
        container_id="MSCU-9988776",
        container_type=ContainerType.REEFER_40FT,
        total_dwell_days=25,
        policy=FreeTimePolicy(terminal_free_days=3, carrier_equipment_free_days=5),
        cargo_value_vnd=3000000.0,
    )

    assert res.total_dd_charges_vnd > (0.70 * 3000000.0)
    assert res.is_maritime_lien_warning is True
    assert "Vượt bãi" in res.cost_status_summary


# ==============================================================================
# 6. CLI COMMAND TESTS (TYPER CLI RUNNER)
# ==============================================================================

def test_cli_loi_evaluate_runner():
    """Test 'loi evaluate' CLI subcommand in text and JSON mode."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["loi", "evaluate", "--vessel", "MV_ALPHA", "--cif", "1000000"])
    assert result.exit_code == 0
    assert "THẨM ĐỊNH RỦI RO THƯ CAM KẾT BỒI THƯỜNG" in result.output
    assert "MV_ALPHA" in result.output

    json_result = runner.invoke(app, ["loi", "evaluate", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert "loi_type" in data
    assert "recommended_guarantee_amount_usd" in data


def test_cli_ga_adjust_runner():
    """Test 'ga adjust' CLI subcommand in text and JSON mode."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["ga", "adjust", "--ship-sacrifice", "200000", "--cargo-sacrifice", "300000"])
    assert result.exit_code == 0
    assert "BẢN PHÂN BỔ TỔN THẤT CHUNG" in result.output

    json_result = runner.invoke(app, ["ga", "adjust", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert "ga_contribution_rate_percentage" in data


def test_cli_bunker_check_runner():
    """Test 'bunker check' CLI subcommand in text and JSON mode."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["bunker", "check", "--bdn-no", "BDN-TEST-123", "--sulfur", "0.45"])
    assert result.exit_code == 0
    assert "KIỂM ĐỊNH HỢP CHUẨN NHIÊN LIỆU MARPOL ANNEX VI" in result.output

    json_result = runner.invoke(app, ["bunker", "check", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert "is_sulfur_compliant" in data


def test_cli_demurrage_calculate_runner():
    """Test 'demurrage calculate' CLI subcommand in text and JSON mode."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["demurrage", "calculate", "--container-id", "MSCU-1234", "--dwell-days", "10"])
    assert result.exit_code == 0
    assert "QUYẾT TOÁN CƯỚC LƯU BÃI & LƯU VỎ CONTAINER" in result.output

    json_result = runner.invoke(app, ["demurrage", "calculate", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert "total_dd_charges_vnd" in data


# ==============================================================================
# 7. MCP SERVER HANDLER TESTS
# ==============================================================================

def test_mcp_loi_handler():
    """Verify handle_loi_risk_evaluate MCP handler."""
    raw = handle_loi_risk_evaluate({
        "vessel_name": "MV_MCP_TEST",
        "cargo_cif_value_usd": 2000000.0,
        "requested_indemnity_multiplier": 2.0,
        "bank_status": "first_class_international_bank",
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["loi_assessment"]["vessel_name"] == "MV_MCP_TEST"


def test_mcp_ga_handler():
    """Verify handle_general_average_adjust MCP handler."""
    raw = handle_general_average_adjust({
        "ship_sound_value_usd": 10000000.0,
        "cargo_cif_value_usd": 15000000.0,
        "ship_damage_sacrifice_usd": 300000.0,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert "ga_contribution_rate_percentage" in data["general_average_adjustment"]


def test_mcp_bunker_handler():
    """Verify handle_bunker_sulfur_compliance_check MCP handler."""
    raw = handle_bunker_sulfur_compliance_check({
        "bdn_number": "BDN-MCP-TEST",
        "fuel_grade": "vlsfo",
        "tested_sulfur_content_pct": 0.49,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["bunker_compliance"]["is_sulfur_compliant"] is True


def test_mcp_demurrage_handler():
    """Verify handle_demurrage_detention_calculate MCP handler."""
    raw = handle_demurrage_detention_calculate({
        "container_id": "TGHU-7766554",
        "container_type": "reefer_40ft",
        "total_dwell_days": 16,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert "total_dd_charges_vnd" in data["demurrage_detention"]
