"""Automated Test Suite for Maritime Bunker Oil Pollution, MLC Living Conditions, SOPEP & Environmental Sanctions (Phases 223-226).

Covers:
- Phase 223: Bunker Oil Pollution Civil Liability & Bunker Convention 2001 Suite
- Phase 224: MLC 2006 Seafarer Working & Living Conditions, Food & Catering, and Medical Care Suite
- Phase 225: MARPOL Reg. 37 Shipboard Oil Pollution Emergency Plan (SOPEP) & SMPEP Suite
- Phase 226: Maritime Environmental Administrative Penalties & Port Detention Sanctions Suite
- AST Zero-External-Dependency verification
- CLI Typer command execution
- FastMCP tool handler tests
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_bunker_mlc_sopep_sanctions_engine import (
    BunkerOilPollutionEngine,
    BunkerPollutionDefense,
    MlcLivingMedicalEngine,
    MlcMedicineChestCategory,
    SopepEmergencyPlanEngine,
    SopepPlanType,
    MaritimeEnvironmentalSanctionsEngine,
    EnvironmentalInfractionType,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_bunker_pollution_assess,
    handle_mlc_living_medical_audit,
    handle_sopep_compliance_verify,
    handle_maritime_environmental_sanction,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================
def test_ast_zero_external_dependency_invariant():
    """Verify engine relies purely on Python standard library modules."""
    engine_path = "src/core/maritime_bunker_mlc_sopep_sanctions_engine.py"
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
# 2. Phase 223: Bunker Oil Pollution & Bunker Convention 2001 Tests
# ===========================================================================
def test_phase223_llmc_limitation_brackets():
    """Verify LLMC 1996 limitation formulas across GT tiers."""
    # Base tier <= 2,000 GT
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(1500.0) == 1510000.0
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(2000.0) == 1510000.0

    # Tier 1: 2,001 - 30,000 GT (e.g., 10,000 GT: 1.51M + 8,000 * 604 = 1,510,000 + 4,832,000 = 6,342,000)
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(10000.0) == 6342000.0

    # At 30,000 GT: 1.51M + 28,000 * 604 = 1,510,000 + 16,912,000 = 18,422,000 SDR
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(30000.0) == 18422000.0

    # Tier 2: 30,001 - 70,000 GT (e.g., 50,000 GT: 18,422,000 + 20,000 * 453 = 18,422,000 + 9,060,000 = 27,482,000)
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(50000.0) == 27482000.0

    # At 70,000 GT: 18,422,000 + 40,000 * 453 = 18,422,000 + 18,120,000 = 36,542,000 SDR
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(70000.0) == 36542000.0

    # Tier 3: > 70,000 GT (e.g., 100,000 GT: 36,542,000 + 30,000 * 302 = 36,542,000 + 9,060,000 = 45,602,000)
    assert BunkerOilPollutionEngine.calculate_llmc_limitation_sdr(100000.0) == 45602000.0


def test_phase223_bunker_pollution_standard_claim_with_blue_card():
    """Verify bunker oil pollution claim with valid blue card and LLMC cap."""
    res = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel_name="MV MEKONG TRANSPORTER",
        gross_tonnage=25000.0,
        claim_clean_up_sdr=5000000.0,
        claim_property_damage_sdr=2000000.0,
        claim_economic_loss_sdr=1000000.0,
        claim_environmental_sdr=1000000.0,
        has_bunker_blue_card=True,
    )
    # Total claims: 9,000,000 SDR.
    # LLMC Limit for 25,000 GT: 1,510,000 + 23,000 * 604 = 15,402,000 SDR.
    # Total claims < LLMC limit, so payout is full claims.
    assert res.compulsory_insurance_required is True
    assert res.has_valid_bunker_blue_card is True
    assert res.direct_action_against_insurer_allowed is True
    assert res.limitation_of_liability_applies is True
    assert res.total_claim_amount_sdr == 9000000.0
    assert res.owner_statutory_payout_sdr == 9000000.0
    assert res.uncompensated_shortfall_sdr == 0.0
    assert res.defense_exoneration_granted is False
    assert res.claim_prescribed is False


def test_phase223_bunker_pollution_exceeds_llmc_cap():
    """Verify bunker pollution claims exceeding LLMC cap results in shortfall."""
    res = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel_name="MV COASTAL CARRIER",
        gross_tonnage=2000.0,
        claim_clean_up_sdr=2000000.0,
        claim_property_damage_sdr=500000.0,
        claim_economic_loss_sdr=0.0,
        claim_environmental_sdr=0.0,
        has_bunker_blue_card=True,
    )
    # Total: 2,500,000 SDR. LLMC cap: 1,510,000 SDR.
    assert res.applicable_llmc_limit_sdr == 1510000.0
    assert res.owner_statutory_payout_sdr == 1510000.0
    assert res.uncompensated_shortfall_sdr == 990000.0


def test_phase223_bunker_pollution_intentional_misconduct():
    """Verify intentional misconduct breaks limitation of liability (LLMC Art. 4)."""
    res = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel_name="MV ROGUE SHIP",
        gross_tonnage=2000.0,
        claim_clean_up_sdr=2500000.0,
        claim_property_damage_sdr=0.0,
        claim_economic_loss_sdr=0.0,
        claim_environmental_sdr=0.0,
        has_bunker_blue_card=True,
        is_intentional_misconduct=True,
    )
    assert res.limitation_of_liability_applies is False
    assert res.owner_statutory_payout_sdr == 2500000.0
    assert res.uncompensated_shortfall_sdr == 0.0
    assert any("MẤT QUYỀN GIỚI HẠN TRÁCH NHIỆM" in f for f in res.findings)


def test_phase223_bunker_pollution_defense_and_prescription():
    """Verify exoneration defense and prescription timebar (3y/6y)."""
    # Defense: War hostilities
    res_war = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel_name="MV SHIP",
        gross_tonnage=5000.0,
        claim_clean_up_sdr=100000.0,
        claim_property_damage_sdr=0.0,
        claim_economic_loss_sdr=0.0,
        claim_environmental_sdr=0.0,
        has_bunker_blue_card=True,
        defense=BunkerPollutionDefense.WAR_HOSTILITIES,
    )
    assert res_war.defense_exoneration_granted is True
    assert res_war.owner_statutory_payout_sdr == 0.0

    # Prescription: 4 years since damage (> 3 years)
    res_timebar = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel_name="MV SHIP",
        gross_tonnage=5000.0,
        claim_clean_up_sdr=100000.0,
        claim_property_damage_sdr=0.0,
        claim_economic_loss_sdr=0.0,
        claim_environmental_sdr=0.0,
        has_bunker_blue_card=True,
        years_since_damage=3.5,
    )
    assert res_timebar.claim_prescribed is True
    assert res_timebar.owner_statutory_payout_sdr == 0.0


# ===========================================================================
# 3. Phase 224: MLC 2006 Living & Medical Conditions Tests
# ===========================================================================
def test_phase224_mlc_fully_compliant_vessel():
    """Verify fully compliant ocean-going vessel under MLC 2006."""
    res = MlcLivingMedicalEngine.audit_living_and_medical(
        vessel_name="MV GLOBAL SEAFARER",
        crew_count=20,
        passenger_count=0,
        voyage_duration_days=15.0,
        potable_water_liters_per_person_day=5.0,
        has_certified_cook=True,
        has_dedicated_hospital_berth=True,
        has_qualified_doctor=False,  # Crew < 100, no doctor needed
        has_valid_medical_guide_and_chest=True,
        chest_category=MlcMedicineChestCategory.CATEGORY_A_OCEAN_GOING,
    )
    assert res.is_compliant is True
    assert len(res.deficiencies) == 0
    assert res.requires_qualified_doctor is False


def test_phase224_mlc_deficiencies_detected():
    """Verify deficiencies detected for low water, uncertified cook, missing hospital."""
    res = MlcLivingMedicalEngine.audit_living_and_medical(
        vessel_name="MV DEFICIENT TRADER",
        crew_count=18,
        passenger_count=0,
        voyage_duration_days=10.0,
        potable_water_liters_per_person_day=1.8,  # < 2.5L
        has_certified_cook=False,                 # Crew >= 10 requires cook
        has_dedicated_hospital_berth=False,       # Crew >= 15 & duration > 3d requires hospital
        has_qualified_doctor=False,
        has_valid_medical_guide_and_chest=False,  # Invalid chest
    )
    assert res.is_compliant is False
    assert len(res.deficiencies) == 4
    assert any("nước ngọt" in d.lower() for d in res.deficiencies)
    assert any("bếp trưởng" in d.lower() for d in res.deficiencies)
    assert any("bệnh xá" in d.lower() for d in res.deficiencies)
    assert any("tủ thuốc" in d.lower() for d in res.deficiencies)


def test_phase224_mlc_doctor_mandatory_for_large_complement():
    """Verify doctor required for >= 100 persons on > 3 days voyage."""
    res = MlcLivingMedicalEngine.audit_living_and_medical(
        vessel_name="MV CRUISE ISLAND",
        crew_count=40,
        passenger_count=80,  # Total 120 >= 100
        voyage_duration_days=5.0,
        potable_water_liters_per_person_day=6.0,
        has_certified_cook=True,
        has_dedicated_hospital_berth=True,
        has_qualified_doctor=False,  # Deficient
        has_valid_medical_guide_and_chest=True,
    )
    assert res.requires_qualified_doctor is True
    assert res.is_compliant is False
    assert any("bác sĩ y khoa" in d.lower() for d in res.deficiencies)


# ===========================================================================
# 4. Phase 225: MARPOL SOPEP / SMPEP Tests
# ===========================================================================
def test_phase225_sopep_oil_tanker_compliant():
    """Verify compliant SOPEP for oil tanker >= 150 GT."""
    res = SopepEmergencyPlanEngine.verify_sopep_compliance(
        vessel_name="MT MEKONG OIL",
        vessel_type="OIL_TANKER",
        gross_tonnage=20000.0,
        is_administration_approved=True,
        has_coastal_state_contacts=True,
        has_operational_spill_steps=True,
        has_casualty_mitigation_steps=True,
        has_national_local_liaison=True,
        months_since_last_oil_spill_drill=1.5,
    )
    assert res.plan_type == SopepPlanType.SOPEP_ANNEX_I
    assert res.is_mandatory is True
    assert res.drill_compliant is True
    assert res.overall_status == "COMPLIANT"
    assert len(res.deficiencies) == 0


def test_phase225_smpep_chemical_tanker_drills_overdue():
    """Verify SMPEP Annex II for chemical tanker with drill overdue (> 3 months)."""
    res = SopepEmergencyPlanEngine.verify_sopep_compliance(
        vessel_name="MT CHEMICAL GLORY",
        vessel_type="CHEMICAL_TANKER",
        gross_tonnage=8000.0,
        is_administration_approved=True,
        has_coastal_state_contacts=True,
        has_operational_spill_steps=True,
        has_casualty_mitigation_steps=True,
        has_national_local_liaison=True,
        months_since_last_oil_spill_drill=4.5,  # > 3 months
    )
    assert res.plan_type == SopepPlanType.SMPEP_ANNEX_II
    assert res.is_mandatory is True
    assert res.drill_compliant is False
    assert res.overall_status == "NON_COMPLIANT_DEFICIENCIES"
    assert any("thực tập" in d.lower() for d in res.deficiencies)


def test_phase225_sopep_exempt_small_cargo_vessel():
    """Verify general cargo vessel < 400 GT is exempt from mandatory SOPEP."""
    res = SopepEmergencyPlanEngine.verify_sopep_compliance(
        vessel_name="MV SMALL COASTER",
        vessel_type="GENERAL_CARGO",
        gross_tonnage=350.0,  # < 400 GT
        is_administration_approved=False,
        has_coastal_state_contacts=False,
        has_operational_spill_steps=False,
        has_casualty_mitigation_steps=False,
        has_national_local_liaison=False,
        months_since_last_oil_spill_drill=10.0,
    )
    assert res.is_mandatory is False
    assert res.overall_status == "EXEMPT"


# ===========================================================================
# 5. Phase 226: Maritime Environmental Sanctions Tests
# ===========================================================================
def test_phase226_oily_bilge_triggers_psc_detention():
    """Verify oily bilge discharge triggers statutory fine and mandatory PSC detention."""
    res = MaritimeEnvironmentalSanctionsEngine.calculate_sanctions(
        vessel_name="MV BILGE DISCHARGER",
        infraction=EnvironmentalInfractionType.OILY_BILGE_OVERBOARD_DISCHARGE,
        is_repeat_offense=False,
        caused_measurable_pollution=False,
        refused_cooperation=False,
    )
    assert res.base_fine_vnd == 75_000_000.0  # (50M + 100M) / 2
    assert res.aggravating_multiplier == 1.0
    assert res.total_statutory_fine_vnd == 75_000_000.0
    assert res.psc_detention_ordered is True
    assert res.mandatory_escrow_deposit_vnd == 150_000_000.0  # 2x fine
    assert "Bơm hút toàn bộ chất thải" in res.rectification_order


def test_phase226_repeat_offense_and_pollution_multiplier():
    """Verify repeat offense and measurable pollution compound aggravating multiplier."""
    res = MaritimeEnvironmentalSanctionsEngine.calculate_sanctions(
        vessel_name="MV POLLUTING VESSEL",
        infraction=EnvironmentalInfractionType.MARPOL_V_PLASTICS_GARBAGE_DUMP,
        is_repeat_offense=True,            # +0.5
        caused_measurable_pollution=True,  # +0.5 & detention
        refused_cooperation=False,
    )
    # Base: (20M + 50M) / 2 = 35,000,000 VND. Multiplier: 1.0 + 0.5 + 0.5 = 2.0
    assert res.base_fine_vnd == 35_000_000.0
    assert res.aggravating_multiplier == 2.0
    assert res.total_statutory_fine_vnd == 70_000_000.0
    assert res.psc_detention_ordered is True
    assert res.mandatory_escrow_deposit_vnd == 140_000_000.0


# ===========================================================================
# 6. CLI Command Integration Tests
# ===========================================================================
def test_cli_bunkerclaim_assess():
    """Test CLI mekong bunkerclaim assess."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["bunkerclaim", "assess", "--vessel", "MV CLI TEST", "--gt", "15000"])
    assert res.exit_code == 0
    assert "ĐÁNH GIÁ TRÁCH NHIỆM BỒI THƯỜNG DẦU BUNKER" in res.output


def test_cli_mlcliving_audit():
    """Test CLI mekong mlcliving audit."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["mlcliving", "audit", "--vessel", "MV MLC TEST", "--crew", "25", "--days", "10"])
    assert res.exit_code == 0
    assert "KIỂM TOÁN ĐIỀU KIỆN SINH HOẠT & Y TẾ MLC 2006" in res.output


def test_cli_sopep_verify():
    """Test CLI mekong sopep verify."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["sopep", "verify", "--vessel", "MT TANKER TEST", "--type", "OIL_TANKER", "--gt", "30000"])
    assert res.exit_code == 0
    assert "THẨM ĐỊNH KẾ HOẠCH ỨNG CỨU Ô NHIỄM DẦU SOPEP / SMPEP" in res.output


def test_cli_maritimesanction_penalize():
    """Test CLI mekong maritimesanction penalize."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["maritimesanction", "penalize", "--vessel", "MV SANCTION TEST", "--infraction", "OILY_BILGE_OVERBOARD_DISCHARGE"])
    assert res.exit_code == 0
    assert "QUYẾT ĐỊNH XỬ PHẠT VI PHẠM MÔI TRƯỜNG BIỂN" in res.output


# ===========================================================================
# 7. FastMCP Tool Handler Tests
# ===========================================================================
def test_mcp_bunker_pollution_assess_handler():
    """Test FastMCP tool handler for bunker pollution assessment."""
    out = handle_bunker_pollution_assess({
        "vessel_name": "MV FAST MCP",
        "gross_tonnage": 20000.0,
        "has_bunker_blue_card": True,
    })
    data = json.loads(out)
    assert data["ok"] is True
    assert data["compulsory_insurance_required"] is True
    assert data["owner_statutory_payout_sdr"] > 0


def test_mcp_mlc_living_medical_audit_handler():
    """Test FastMCP tool handler for MLC living & medical audit."""
    out = handle_mlc_living_medical_audit({
        "vessel_name": "MV FAST MLC",
        "crew_count": 22,
        "potable_water_liters_per_person_day": 3.5,
    })
    data = json.loads(out)
    assert data["ok"] is True
    assert data["is_compliant"] is True


def test_mcp_sopep_compliance_verify_handler():
    """Test FastMCP tool handler for SOPEP verification."""
    out = handle_sopep_compliance_verify({
        "vessel_name": "MT FAST SOPEP",
        "vessel_type": "OIL_TANKER",
        "gross_tonnage": 5000.0,
    })
    data = json.loads(out)
    assert data["ok"] is True
    assert data["overall_status"] == "COMPLIANT"


def test_mcp_maritime_environmental_sanction_handler():
    """Test FastMCP tool handler for maritime environmental sanctions."""
    out = handle_maritime_environmental_sanction({
        "vessel_name": "MV FAST SANCTION",
        "infraction": "OILY_BILGE_OVERBOARD_DISCHARGE",
    })
    data = json.loads(out)
    assert data["ok"] is True
    assert data["psc_detention_ordered"] is True
    assert data["total_statutory_fine_vnd"] == 75_000_000.0
