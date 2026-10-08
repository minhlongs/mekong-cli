"""Automated Test Suite for Maritime Bio-Security, Dangerous Goods, Oil Pollution & Cabotage (Phases 219-222).

Covers:
- Phase 219: Ballast Water Management (BWM 2004) Reg D-1 & D-2 standards & BWRB logs
- Phase 220: IMDG Code Stowage & Segregation Table 7.2.4 & Port entry permits
- Phase 221: CLC 1992 & IOPC Fund 1992 Oil Pollution Liability, Blue Card & Timebar
- Phase 222: Maritime Coastal Cabotage Reservation & Foreign Vessel Waiver Licensing
- CLI Commands & App Setup
- FastMCP tool handlers
- AST Zero-External-Dependency verification
"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_ballast_imdg_clc_cabotage_engine import (
    BallastWaterManagementEngine,
    BallastDischargeSample,
    BwmStandardApplied,
    ImdgCargoSegregationEngine,
    DangerousCargoEntry,
    ImdgClass,
    SegregationRequirement,
    ClcOilPollutionLiabilityEngine,
    OilPollutionClaimSummary,
    MaritimeCabotageLicensingEngine,
    CabotageCargoType,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_ballast_compliance_audit,
    handle_imdg_segregation_audit,
    handle_clc_oil_pollution_assess,
    handle_cabotage_licensing_evaluate,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================
def test_ast_zero_external_dependency_invariant():
    """Verify engine relies purely on Python standard library modules."""
    engine_path = "src/core/maritime_ballast_imdg_clc_cabotage_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    allowed_stdlib = {"dataclasses", "enum", "math", "typing", "json", "re", "hashlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Unauthorized external import: {base_pkg}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Unauthorized external importFrom: {base_pkg}"


# ===========================================================================
# 2. Phase 219: Ballast Water Management Tests
# ===========================================================================
def test_phase219_bwm_d1_compliant_exchange():
    """Test compliant Reg. D-1 ballast water exchange (>=200nm, >=200m depth, >=95% exchange)."""
    report = BallastWaterManagementEngine.audit_ballast_compliance(
        vessel_name="MV PACIFIC TRADER",
        imo_number="9123456",
        standard_applied=BwmStandardApplied.D1_BALLAST_EXCHANGE,
        exchange_distance_nm=220.0,
        exchange_depth_meters=450.0,
        volumetric_exchange_percent=96.5,
        bwrb_years_retained_onboard=2.5,
    )
    assert report.discharge_permitted is True
    assert report.bwrb_log_compliant is True
    assert len(report.sample_violations) == 0
    assert "DISCHARGE_PERMITTED" in report.verdict


def test_phase219_bwm_d1_violations():
    """Test non-compliant Reg. D-1 exchange with insufficient distance and depth."""
    report = BallastWaterManagementEngine.audit_ballast_compliance(
        vessel_name="MV INSHORE CARRIER",
        imo_number="9234567",
        standard_applied=BwmStandardApplied.D1_BALLAST_EXCHANGE,
        exchange_distance_nm=30.0,      # < 50nm
        exchange_depth_meters=100.0,    # < 200m
        volumetric_exchange_percent=88.0,  # < 95%
        bwrb_years_retained_onboard=1.0,   # < 2 years
    )
    assert report.discharge_permitted is False
    assert report.bwrb_log_compliant is False
    assert any("D1_LOCATION_VIOLATION" in v for v in report.sample_violations)
    assert any("D1_INSUFFICIENT_EXCHANGE" in v for v in report.sample_violations)
    assert any("BWRB_RETENTION_DEFICIT" in v for v in report.sample_violations)


def test_phase219_bwm_d2_compliant_treatment_sample():
    """Test compliant Reg. D-2 BWMS system with clean biological discharge."""
    sample = BallastDischargeSample(
        tank_identifier="FOREPEAK_TANK",
        organisms_50um_plus_per_m3=2.0,       # < 10
        organisms_10_to_50um_per_ml=3.5,      # < 10
        vibrio_cholerae_cfu_per_100ml=0.0,    # < 1
        escherichia_coli_cfu_per_100ml=85.0,  # < 250
        intestinal_enterococci_cfu_per_100ml=25.0,  # < 100
    )
    report = BallastWaterManagementEngine.audit_ballast_compliance(
        vessel_name="MV GREEN ARROW",
        imo_number="9345678",
        standard_applied=BwmStandardApplied.D2_TREATMENT_SYSTEM,
        bwms_type_approved=True,
        bwms_active_and_calibrated=True,
        bwrb_years_retained_onboard=3.0,
        sample=sample,
    )
    assert report.discharge_permitted is True
    assert len(report.sample_violations) == 0
    assert "DISCHARGE_PERMITTED" in report.verdict


def test_phase219_bwm_d2_biological_limits_exceeded():
    """Test Reg. D-2 bio-security violations for pathogenic bacteria and micro-organisms."""
    sample = BallastDischargeSample(
        tank_identifier="WING_TANK_2S",
        organisms_50um_plus_per_m3=18.0,      # > 10
        organisms_10_to_50um_per_ml=15.0,     # > 10
        vibrio_cholerae_cfu_per_100ml=3.0,    # > 1
        escherichia_coli_cfu_per_100ml=350.0, # > 250
        intestinal_enterococci_cfu_per_100ml=180.0, # > 100
    )
    report = BallastWaterManagementEngine.audit_ballast_compliance(
        vessel_name="MV BIO HAZARD",
        imo_number="9456789",
        standard_applied=BwmStandardApplied.D2_TREATMENT_SYSTEM,
        bwms_type_approved=True,
        bwms_active_and_calibrated=True,
        bwrb_years_retained_onboard=2.0,
        sample=sample,
    )
    assert report.discharge_permitted is False
    assert any("D2_VIABLE_ORGANISMS_50UM" in v for v in report.sample_violations)
    assert any("D2_VIABLE_ORGANISMS_10_50UM" in v for v in report.sample_violations)
    assert any("D2_VIBRIO_CHOLERAE" in v for v in report.sample_violations)
    assert any("D2_ESCHERICHIA_COLI" in v for v in report.sample_violations)
    assert any("D2_ENTEROCOCCI" in v for v in report.sample_violations)


# ===========================================================================
# 3. Phase 220: IMDG Code Dangerous Goods Tests
# ===========================================================================
def test_phase220_imdg_segregation_matrix_lookups():
    """Test IMDG Table 7.2.4 segregation matrix lookups across hazard classes."""
    # Class 1 (Explosives) vs Class 3 (Flammable Liquids) -> 4 (Separated longitudinally)
    req1 = ImdgCargoSegregationEngine.get_required_segregation(
        ImdgClass.CLASS_1_EXPLOSIVES, ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS
    )
    assert req1 == SegregationRequirement.SEPARATED_LONGITUDINALLY

    # Class 3 (Flammable Liquids) vs Class 5.1 (Oxidizing Substances) -> 2 (Separated from)
    req2 = ImdgCargoSegregationEngine.get_required_segregation(
        ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES
    )
    assert req2 == SegregationRequirement.SEPARATED_FROM

    # Class 3 (Flammable Liquids) vs Class 5.2 (Organic Peroxides) -> 3 (Separated by compartment)
    req3 = ImdgCargoSegregationEngine.get_required_segregation(
        ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_5_2_ORGANIC_PEROXIDES
    )
    assert req3 == SegregationRequirement.SEPARATED_BY_COMPARTMENT

    # Class 3 vs Class 8 (Corrosives) -> 1 (Away from)
    req4 = ImdgCargoSegregationEngine.get_required_segregation(
        ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_8_CORROSIVES
    )
    assert req4 == SegregationRequirement.AWAY_FROM

    # Identical class -> None
    req5 = ImdgCargoSegregationEngine.get_required_segregation(
        ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS, ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS
    )
    assert req5 == SegregationRequirement.NONE


def test_phase220_stowage_pair_compliant_physical_separation():
    """Test compliant stowage pair meeting 'Separated From' requirements."""
    c_a = DangerousCargoEntry(
        container_id="C-FLAM-01",
        un_number="UN1203",
        proper_shipping_name="GASOLINE",
        imdg_class=ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS,
        packing_group="II",
        bay_row_tier="01-02-82",
    )
    c_b = DangerousCargoEntry(
        container_id="C-OXID-02",
        un_number="UN1479",
        proper_shipping_name="OXIDIZING SOLID, N.O.S.",
        imdg_class=ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES,
        packing_group="II",
        bay_row_tier="05-02-82",
    )
    # Required: SEPARATED_FROM (min 6.0m or 1 bulkhead). Actual: 8.5m with 1 bulkhead.
    report = ImdgCargoSegregationEngine.audit_stowage_pair(
        cargo_a=c_a,
        cargo_b=c_b,
        physical_distance_meters=8.5,
        intervening_bulkheads_count=1,
        has_dangerous_goods_declaration=True,
        has_container_packing_certificate=True,
    )
    assert report.segregation_compliant is True
    assert len(report.deficiencies) == 0
    assert "STOWAGE_APPROVED" in report.verdict


def test_phase220_stowage_pair_insufficient_segregation_and_docs():
    """Test stowage failure due to distance violation and missing CPC."""
    c_a = DangerousCargoEntry(
        container_id="C-FLAM-01",
        un_number="UN1203",
        proper_shipping_name="GASOLINE",
        imdg_class=ImdgClass.CLASS_3_FLAMMABLE_LIQUIDS,
        packing_group="II",
        bay_row_tier="01-02-82",
    )
    c_b = DangerousCargoEntry(
        container_id="C-OXID-02",
        un_number="UN1479",
        proper_shipping_name="OXIDIZING SOLID, N.O.S.",
        imdg_class=ImdgClass.CLASS_5_1_OXIDIZING_SUBSTANCES,
        packing_group="II",
        bay_row_tier="01-04-82",
    )
    # Distance only 3.0m without bulkhead (< 6.0m) and missing CPC
    report = ImdgCargoSegregationEngine.audit_stowage_pair(
        cargo_a=c_a,
        cargo_b=c_b,
        physical_distance_meters=3.0,
        intervening_bulkheads_count=0,
        has_dangerous_goods_declaration=True,
        has_container_packing_certificate=False,
    )
    assert report.segregation_compliant is False
    assert any("SEGREGATION_FAIL_SEPARATED_FROM" in d for d in report.deficiencies)
    assert any("MISSING_CPC" in d for d in report.deficiencies)
    assert "STOWAGE_REJECTED" in report.verdict


# ===========================================================================
# 4. Phase 221: CLC 1992 & IOPC Fund Oil Pollution Tests
# ===========================================================================
def test_phase221_clc_liability_formula_brackets():
    """Verify CLC 1992 shipowner strict liability limits by gross tonnage."""
    # Small tanker (GT <= 5,000) -> Flat 4,510,000 SDR
    limit_small = ClcOilPollutionLiabilityEngine.calculate_clc_limit_sdr(3_000.0)
    assert limit_small == 4_510_000.0

    limit_boundary = ClcOilPollutionLiabilityEngine.calculate_clc_limit_sdr(5_000.0)
    assert limit_boundary == 4_510_000.0

    # Medium tanker (GT = 25,000): 4,510,000 + (20,000 * 631) = 4,510,000 + 12,620,000 = 17,130,000 SDR
    limit_med = ClcOilPollutionLiabilityEngine.calculate_clc_limit_sdr(25_000.0)
    assert limit_med == 17_130_000.0

    # VLCC Supertanker (GT = 160,000): Capped at statutory ceiling of 89,770,000 SDR
    limit_vlcc = ClcOilPollutionLiabilityEngine.calculate_clc_limit_sdr(160_000.0)
    assert limit_vlcc == 89_770_000.0


def test_phase221_clc_and_iopc_fund_tiered_payout():
    """Test tiered payout where shipowner pays up to CLC cap and IOPC Fund pays excess."""
    claims = OilPollutionClaimSummary(
        cleanup_and_preventive_costs_usd=20_000_000.0,
        fisheries_economic_loss_usd=15_000_000.0,
        property_damage_usd=5_000_000.0,
        environmental_reinstatement_usd=10_000_000.0,
    )
    # Total claims: $50,000,000 USD
    # Tanker: 25,000 GT -> CLC limit = 17,130,000 SDR * 1.33 = $22,782,900 USD
    # Remaining claims = $50,000,000 - $22,782,900 = $27,217,100 USD (absorbed by IOPC Fund)
    assessment = ClcOilPollutionLiabilityEngine.evaluate_oil_pollution_claims(
        incident_ref="INC-2026-VUNGTAU-01",
        tanker_name="MT MEKONG PIONEER",
        gross_tonnage=25_000.0,
        claims=claims,
        sdr_usd_rate=1.33,
        compulsory_blue_card_valid=True,
        years_since_incident=1.0,
        years_since_damage=1.0,
    )
    assert assessment.total_claims_usd == 50_000_000.0
    assert assessment.shipowner_liability_usd == pytest.approx(22_782_900.0, 1.0)
    assert assessment.iopc_fund_contribution_usd == pytest.approx(27_217_100.0, 1.0)
    assert assessment.uncompensated_shortfall_usd == 0.0
    assert assessment.timebar_prescribed is False
    assert assessment.direct_action_against_pi_insurer is True
    assert "TIERED_SETTLEMENT" in assessment.verdict


def test_phase221_mega_spill_exceeding_iopc_aggregate_ceiling():
    """Test catastrophic mega spill exceeding the 203M SDR aggregate cap."""
    # Total claims: $350,000,000 USD
    claims = OilPollutionClaimSummary(
        cleanup_and_preventive_costs_usd=150_000_000.0,
        fisheries_economic_loss_usd=100_000_000.0,
        property_damage_usd=50_000_000.0,
        environmental_reinstatement_usd=50_000_000.0,
    )
    # Max aggregate ceiling = 203,000,000 SDR * 1.33 = $269,990,000 USD
    # Shortfall = $350,000,000 - $269,990,000 = $80,010,000 USD
    assessment = ClcOilPollutionLiabilityEngine.evaluate_oil_pollution_claims(
        incident_ref="INC-2026-CATHO-02",
        tanker_name="MT GIANT CRUDE",
        gross_tonnage=150_000.0,
        claims=claims,
        sdr_usd_rate=1.33,
    )
    assert assessment.uncompensated_shortfall_usd > 0
    assert assessment.uncompensated_shortfall_usd == pytest.approx(80_010_000.0, 1.0)


def test_phase221_intentional_fault_breaks_limitation():
    """Test intentional/reckless fault breaking limitation under CLC Art. V(2)."""
    claims = OilPollutionClaimSummary(
        cleanup_and_preventive_costs_usd=30_000_000.0,
        fisheries_economic_loss_usd=10_000_000.0,
        property_damage_usd=5_000_000.0,
        environmental_reinstatement_usd=5_000_000.0,
    )
    assessment = ClcOilPollutionLiabilityEngine.evaluate_oil_pollution_claims(
        incident_ref="INC-2026-MALICE-01",
        tanker_name="MT ROGUE WAVE",
        gross_tonnage=20_000.0,
        claims=claims,
        shipowner_intentional_fault=True,
    )
    assert assessment.shipowner_liability_usd == 50_000_000.0
    assert assessment.iopc_fund_contribution_usd == 0.0
    assert "UNLIMITED_LIABILITY" in assessment.verdict


def test_phase221_statutory_timebar_prescription():
    """Test claims extinction under VMC Art. 296 after 3 years damage or 6 years incident."""
    claims = OilPollutionClaimSummary(
        cleanup_and_preventive_costs_usd=10_000_000.0,
        fisheries_economic_loss_usd=5_000_000.0,
        property_damage_usd=0.0,
        environmental_reinstatement_usd=0.0,
    )
    # Damage occurred 3.5 years ago (> 3.0 statutory limit)
    assessment = ClcOilPollutionLiabilityEngine.evaluate_oil_pollution_claims(
        incident_ref="INC-2020-OLD-01",
        tanker_name="MT ANCIENT TANKER",
        gross_tonnage=30_000.0,
        claims=claims,
        years_since_damage=3.5,
    )
    assert assessment.timebar_prescribed is True
    assert assessment.shipowner_liability_usd == 0.0
    assert assessment.iopc_fund_contribution_usd == 0.0
    assert "CLAIMS_TIMEBARRED" in assessment.verdict


# ===========================================================================
# 5. Phase 222: Maritime Coastal Cabotage Tests
# ===========================================================================
def test_phase222_vietnamese_flag_unrestricted_cabotage():
    """Test Vietnamese-flagged vessel has statutory right to coastal transport."""
    assessment = MaritimeCabotageLicensingEngine.evaluate_cabotage_licensing(
        application_ref="CAB-VN-001",
        vessel_name="MV VINASHIP STAR",
        flag_state="Vietnam",
        gross_tonnage=12_000.0,
        cargo_type=CabotageCargoType.CONTAINER_DOMESTIC_FEEDER,
        requested_duration_months=12,
    )
    assert assessment.license_granted is True
    assert assessment.permit_duration_months == 12
    assert assessment.statutory_cabotage_surcharge_usd == 0.0
    assert "NATIONAL_RIGHT" in assessment.verdict


def test_phase222_foreign_vessel_specialized_heavy_lift_waiver_granted():
    """Test foreign vessel granted temporary waiver for specialized heavy lift with domestic deficit."""
    assessment = MaritimeCabotageLicensingEngine.evaluate_cabotage_licensing(
        application_ref="CAB-FOR-002",
        vessel_name="MV BIGLIFT BARENTS",
        flag_state="Netherlands",
        gross_tonnage=22_000.0,
        cargo_type=CabotageCargoType.SPECIALIZED_HEAVY_LIFT_PROJECT,
        requested_duration_months=6,
        domestic_vietnamese_vessel_available=False,
        national_defense_clearance=True,
        vessel_age_years=8.0,
    )
    assert assessment.license_granted is True
    assert assessment.permit_duration_months == 6
    assert assessment.domestic_fleet_deficit_verified is True
    assert assessment.statutory_cabotage_surcharge_usd == 5_000.0 + (6 * 2_500.0)  # $20,000 USD
    assert "FOREIGN_CABOTAGE_PERMIT_GRANTED" in assessment.verdict


def test_phase222_foreign_vessel_refused_domestic_available():
    """Test foreign vessel rejected when Vietnamese domestic fleet capacity exists."""
    assessment = MaritimeCabotageLicensingEngine.evaluate_cabotage_licensing(
        application_ref="CAB-FOR-003",
        vessel_name="MV ASIAN FEEDER",
        flag_state="Panama",
        gross_tonnage=10_000.0,
        cargo_type=CabotageCargoType.CONTAINER_DOMESTIC_FEEDER,
        requested_duration_months=6,
        domestic_vietnamese_vessel_available=True,  # Domestic fleet available
    )
    assert assessment.license_granted is False
    assert any("DOMESTIC_FLEET_AVAILABLE" in r for r in assessment.disqualification_reasons)
    assert "CABOTAGE_PERMIT_REFUSED" in assessment.verdict


def test_phase222_foreign_vessel_refused_defense_objection_and_age_cap():
    """Test foreign vessel rejected due to defense objection and excessive vessel age."""
    assessment = MaritimeCabotageLicensingEngine.evaluate_cabotage_licensing(
        application_ref="CAB-FOR-004",
        vessel_name="MV RUSTY FERRY",
        flag_state="Liberia",
        gross_tonnage=5_000.0,
        cargo_type=CabotageCargoType.COASTAL_PASSENGER_FERRY,
        requested_duration_months=9,  # > 6m
        national_defense_clearance=False,  # Defense denied
        vessel_age_years=18.0,  # > 15y max for passenger
    )
    assert assessment.license_granted is False
    assert any("DEFENSE_SECURITY_OBJECTION" in r for r in assessment.disqualification_reasons)
    assert any("AGE_LIMIT_EXCEEDED" in r for r in assessment.disqualification_reasons)
    assert any("DURATION_EXCESS" in r for r in assessment.disqualification_reasons)


# ===========================================================================
# 6. CLI Command Integration Tests
# ===========================================================================
def test_cli_ballast_audit_command():
    """Test CLI mekong ballast audit invocation."""
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["ballast", "audit", "--vessel", "MV TEST SHIP", "--standard", "D2"])
    assert result.exit_code == 0
    assert "ĐÁNH GIÁ AN TOÀN SINH HỌC NƯỚC DẰN" in result.output


def test_cli_imdg_segregate_command():
    """Test CLI mekong imdg segregate invocation."""
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["imdg", "segregate", "--class-a-str", "3", "--class-b-str", "5.1"])
    assert result.exit_code == 0
    assert "KIỂM ĐỊNH PHÂN CÁCH IMDG CODE" in result.output


def test_cli_clc_assess_command():
    """Test CLI mekong clc assess invocation."""
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["clc", "assess", "--tanker", "MT TEST TANKER", "--gt", "40000"])
    assert result.exit_code == 0
    assert "ĐÁNH GIÁ TRÁCH NHIỆM DÂN SỰ Ô NHIỄM DẦU TRÀN" in result.output


def test_cli_cabotage_evaluate_command():
    """Test CLI mekong cabotage evaluate invocation."""
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["cabotage", "evaluate", "--vessel", "MV PROJECT CRANE", "--flag", "Vietnam"])
    assert result.exit_code == 0
    assert "THẨM ĐỊNH CẤP PHÉP VẬN TẢI BIỂN NỘI ĐỊA" in result.output


# ===========================================================================
# 7. FastMCP Tool Handler Tests
# ===========================================================================
def test_mcp_ballast_compliance_audit_handler():
    """Test FastMCP tool handler for ballast compliance audit."""
    res_str = handle_ballast_compliance_audit({
        "vessel_name": "MV MCP SHIP",
        "standard_applied": "D2",
        "organisms_50um_plus_per_m3": 4.0,
    })
    res = json.loads(res_str)
    assert res["ok"] is True
    assert res["discharge_permitted"] is True
    assert res["vessel_name"] == "MV MCP SHIP"


def test_mcp_imdg_segregation_audit_handler():
    """Test FastMCP tool handler for IMDG segregation audit."""
    res_str = handle_imdg_segregation_audit({
        "container_a": "CNTR-A",
        "class_a": "3",
        "container_b": "CNTR-B",
        "class_b": "8",
        "physical_distance_meters": 5.0,
    })
    res = json.loads(res_str)
    assert res["ok"] is True
    assert res["required_segregation"] == "1_AWAY_FROM"
    assert res["segregation_compliant"] is True


def test_mcp_clc_oil_pollution_assess_handler():
    """Test FastMCP tool handler for CLC oil pollution liability assessment."""
    res_str = handle_clc_oil_pollution_assess({
        "incident_ref": "INC-TEST-01",
        "tanker_name": "MT TANKER ALPHA",
        "gross_tonnage": 35000.0,
        "cleanup_usd": 15000000.0,
    })
    res = json.loads(res_str)
    assert res["ok"] is True
    assert res["clc_shipowner_limit_sdr"] > 0
    assert res["shipowner_liability_usd"] > 0


def test_mcp_cabotage_licensing_evaluate_handler():
    """Test FastMCP tool handler for coastal cabotage licensing."""
    res_str = handle_cabotage_licensing_evaluate({
        "application_ref": "CAB-TEST-01",
        "vessel_name": "MV VN HERO",
        "flag_state": "Vietnam",
    })
    res = json.loads(res_str)
    assert res["ok"] is True
    assert res["license_granted"] is True
    assert res["statutory_cabotage_surcharge_usd"] == 0.0
