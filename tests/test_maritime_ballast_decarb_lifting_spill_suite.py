"""Unit and Integration Tests for Maritime Ballast, Decarb, Lifting & Spill Response Suite.

Phases 327-330 100% Zero-Mock Deterministic Verification Suite.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime.phase_327_ballast_water_uscg import (
    BallastWaterComplianceEngine as ModularBwmEngine,
)
from src.core.maritime.phase_328_decarb_fueleu_fuels import (
    MaritimeDecarbFuelEngine as ModularDecarbEngine,
)
from src.core.maritime.phase_329_lifting_appliances import (
    PortLiftingComplianceEngine as ModularLiftingEngine,
)
from src.core.maritime.phase_330_oil_spill_oprc_neba import (
    MarineOilSpillResponseEngine as ModularSpillEngine,
)
from src.core.maritime_ballast_decarb_lifting_spill_engine import (
    BallastWaterComplianceEngine,
    BallastWaterQualityInput,
    BallastWaterQualityResult,
    DecarbEvaluationResult,
    DualFuelBunkeringInput,
    EuEtsFuelEuInput,
    LiftingApplianceInput,
    LiftingApplianceResult,
    MarineOilSpillResponseEngine,
    MaritimeDecarbFuelEngine,
    OilSpillIncidentInput,
    OilSpillResponseResult,
    PortLiftingComplianceEngine,
)

runner = CliRunner()
app = build_app()


# ==============================================================================
# Phase 327: IMO BWM D-2 vs USCG Type Approval (46 CFR 162.060) Tests
# ==============================================================================
def test_bwm_imo_d2_compliant():
    """Phase 327: Test IMO D-2 compliant discharge with UV system."""
    inp = BallastWaterQualityInput(
        vessel_name="MV-MEKONG-ALPHA",
        bwms_type="UV",
        standard_regime="IMO_D2",
        organisms_over_50um_per_m3=2.5,
        organisms_10_to_50um_per_ml=4.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        ecoli_cfu_per_100ml=45.0,
        enterococci_cfu_per_100ml=12.0,
        uv_transmittance_pct=65.0,
        sediment_stripping_ratio_pct=1.5,
    )
    res: BallastWaterQualityResult = BallastWaterComplianceEngine.evaluate(inp)
    assert res.compliant is True
    assert len(res.reasons) >= 1
    assert "complies" in res.reasons[0].lower()
    assert len(res.audit_trail_hash) == 64
    assert res.parameters["uv_transmittance_pct"] == 65.0


def test_bwm_uscg_microbe_violation():
    """Phase 327: Test USCG regime with viable organism and cholera violation."""
    inp = BallastWaterQualityInput(
        vessel_name="MV-MEKONG-BETA",
        bwms_type="UV",
        standard_regime="USCG_TYPE_APPROVAL",
        organisms_over_50um_per_m3=15.0,  # Exceeds 10.0
        organisms_10_to_50um_per_ml=2.0,
        vibrio_cholerae_cfu_per_100ml=2.5,  # Exceeds 1.0
        ecoli_cfu_per_100ml=10.0,
        enterococci_cfu_per_100ml=5.0,
        uv_transmittance_pct=70.0,
    )
    res = BallastWaterComplianceEngine.evaluate(inp)
    assert res.compliant is False
    assert any(">=50um (15.0/m3)" in r for r in res.reasons)
    assert any("Vibrio cholerae" in r for r in res.reasons)


def test_bwm_electrochlorination_tro_violation():
    """Phase 327: Test TRO discharge violation without neutralization."""
    inp = BallastWaterQualityInput(
        vessel_name="MV-MEKONG-GAMMA",
        bwms_type="ELECTROCHLORINATION",
        standard_regime="IMO_D2",
        organisms_over_50um_per_m3=1.0,
        organisms_10_to_50um_per_ml=1.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        ecoli_cfu_per_100ml=20.0,
        enterococci_cfu_per_100ml=5.0,
        tro_discharge_mg_per_l=0.35,  # Exceeds 0.1 mg/L
        tro_neutralizer_applied=False,
    )
    res = BallastWaterComplianceEngine.evaluate(inp)
    assert res.compliant is False
    assert any("Residual TRO 0.35 mg/L" in r for r in res.reasons)


def test_bwm_tro_neutralized_ok():
    """Phase 327: Test TRO neutralizer brings compliance."""
    inp = BallastWaterQualityInput(
        vessel_name="MV-MEKONG-DELTA",
        bwms_type="ELECTROCHLORINATION",
        standard_regime="IMO_D2",
        organisms_over_50um_per_m3=1.0,
        organisms_10_to_50um_per_ml=1.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        ecoli_cfu_per_100ml=20.0,
        enterococci_cfu_per_100ml=5.0,
        tro_discharge_mg_per_l=0.05,
        tro_neutralizer_applied=True,
    )
    res = BallastWaterComplianceEngine.evaluate(inp)
    assert res.compliant is True


def test_bwm_low_uvt_and_sediment_rejection():
    """Phase 327: Test UVT < 50% and sediment > 5% rejection."""
    inp = BallastWaterQualityInput(
        vessel_name="MV-MEKONG-EPSILON",
        bwms_type="UV",
        standard_regime="IMO_D2",
        organisms_over_50um_per_m3=3.0,
        organisms_10_to_50um_per_ml=3.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        ecoli_cfu_per_100ml=30.0,
        enterococci_cfu_per_100ml=10.0,
        uv_transmittance_pct=42.0,  # Below 50.0%
        sediment_stripping_ratio_pct=6.5,  # Exceeds 5.0%
    )
    res = BallastWaterComplianceEngine.evaluate(inp)
    assert res.compliant is False
    assert any("UV Transmittance 42.0%" in r for r in res.reasons)
    assert any("Sediment stripping ratio 6.5%" in r for r in res.reasons)


# ==============================================================================
# Phase 328: Decarbonization EU ETS MRV & FuelEU Green Fuels Tests
# ==============================================================================
def test_decarb_eu_ets_phase_in_2025():
    """Phase 328: Test EU ETS 2025 70% phase-in calculation."""
    ets_in = EuEtsFuelEuInput(
        ship_id="IMO-9912345",
        reporting_year=2025,
        gross_tonnage=35000.0,
        eu_intra_voyage_emissions_mt=2400.0,  # 100% scope = 2400 MT
        eu_extra_voyage_emissions_mt=1800.0,  # 50% scope = 900 MT
        ghg_intensity_actual_g_per_mj=88.5,
        fuel_energy_consumption_mj=1.5e8,
    )
    res: DecarbEvaluationResult = MaritimeDecarbFuelEngine.evaluate(ets_in=ets_in)
    # Total scope = 2400 + 900 = 3300 MT. Phase-in 2025 is 70% -> 2310 MT.
    assert res.eua_surrender_obligation_mt == 2310.0
    assert res.fueleu_target_ghg_intensity == pytest.approx(89.3368, 0.01)
    assert res.fueleu_compliance_balance_eur > 0  # Actual (88.5) < Target (89.34) -> Surplus


def test_decarb_eu_ets_small_vessel_exemption():
    """Phase 328: Test ships under 5,000 GT are exempt from EU ETS maritime."""
    ets_in = EuEtsFuelEuInput(
        ship_id="IMO-9100000",
        reporting_year=2025,
        gross_tonnage=4200.0,  # < 5000 GT
        eu_intra_voyage_emissions_mt=1000.0,
        eu_extra_voyage_emissions_mt=500.0,
        ghg_intensity_actual_g_per_mj=85.0,
        fuel_energy_consumption_mj=5.0e7,
    )
    res = MaritimeDecarbFuelEngine.evaluate(ets_in=ets_in)
    assert res.eua_surrender_obligation_mt == 0.0


def test_decarb_fueleu_deficit_penalty():
    """Phase 328: Test FuelEU deficit penalty balance when actual GHG exceeds target."""
    ets_in = EuEtsFuelEuInput(
        ship_id="IMO-9999999",
        reporting_year=2025,
        gross_tonnage=50000.0,
        eu_intra_voyage_emissions_mt=5000.0,
        eu_extra_voyage_emissions_mt=4000.0,
        ghg_intensity_actual_g_per_mj=92.5,  # > Target (89.34)
        fuel_energy_consumption_mj=2.0e8,
    )
    res = MaritimeDecarbFuelEngine.evaluate(ets_in=ets_in)
    assert res.fueleu_compliance_balance_eur < 0  # Deficit penalty
    assert any("Deficit balance" in r for r in res.reasons)


def test_decarb_dual_fuel_methanol_bunkering_safety():
    """Phase 328: Test Methanol bunkering safety verification."""
    bunker_in = DualFuelBunkeringInput(
        fuel_type="METHANOL",
        pipeline_nitrogen_purged=True,
        pipeline_o2_vol_pct=1.4,  # < 2.0%
        vapor_leak_ppm=50.0,  # < 200 ppm
        transfer_pressure_bar=6.0,
        observed_safety_radius_meters=10.0,  # > Required 5.0 + 0.5*6.0 = 8.0m
    )
    res = MaritimeDecarbFuelEngine.evaluate(bunker_in=bunker_in)
    assert res.bunkering_safe is True
    # Required safety radius: 5.0 + 0.5 * 6.0 = 8.0 meters
    assert res.parameters["required_safety_radius_m"] == 8.0


def test_decarb_ammonia_bunkering_leak_rejection():
    """Phase 328: Test Ammonia bunkering leak exceeding 25 ppm threshold."""
    bunker_in = DualFuelBunkeringInput(
        fuel_type="AMMONIA",
        pipeline_nitrogen_purged=True,
        pipeline_o2_vol_pct=1.2,
        vapor_leak_ppm=35.0,  # Exceeds 25 ppm
        transfer_pressure_bar=10.0,
        observed_safety_radius_meters=12.0,
    )
    res = MaritimeDecarbFuelEngine.evaluate(bunker_in=bunker_in)
    assert res.bunkering_safe is False
    assert any("AMMONIA leak 35.0 ppm" in r for r in res.reasons)


# ==============================================================================
# Phase 329: Port Lifting Appliances (ILO 152 & ISO 4309) Tests
# ==============================================================================
def test_lifting_proof_load_ranges():
    """Phase 329: Test statutory proof load ratios across SWL brackets."""
    # Bracket 1: SWL <= 20T -> 1.25 * SWL
    assert ModularLiftingEngine.calculate_proof_load(10.0) == 12.5
    assert ModularLiftingEngine.calculate_proof_load(20.0) == 25.0

    # Bracket 2: 20T < SWL <= 50T -> SWL + 5T
    assert ModularLiftingEngine.calculate_proof_load(30.0) == 35.0
    assert ModularLiftingEngine.calculate_proof_load(50.0) == 55.0

    # Bracket 3: SWL > 50T -> 1.10 * SWL
    assert ModularLiftingEngine.calculate_proof_load(60.0) == 66.0
    assert ModularLiftingEngine.calculate_proof_load(100.0) == 110.0


def test_lifting_appliance_full_pass():
    """Phase 329: Test lifting appliance passing all inspections and load tests."""
    inp = LiftingApplianceInput(
        equipment_id="CRANE-STS-01",
        swl_tonnes=40.0,
        tested_proof_load_tonnes=45.0,  # 40 + 5 = 45 required
        months_since_last_annual_inspection=8,  # <= 12
        months_since_last_quadrennial_survey=40,  # <= 60
        wire_rope_nominal_diameter_mm=36.0,
        wire_rope_measured_diameter_mm=35.0,  # Loss 2.78% < 7.0%
        visible_broken_wires_in_lay_length=1,
        max_allowed_broken_wires=4,
        corrosion_pitting_severe=False,
    )
    res: LiftingApplianceResult = PortLiftingComplianceEngine.evaluate(inp)
    assert res.certified_safe is True
    assert res.calculated_proof_load_required_tonnes == 45.0
    assert len(res.audit_trail_hash) == 64


def test_lifting_appliance_insufficient_proof_load():
    """Phase 329: Test failure when tested proof load < required proof load."""
    inp = LiftingApplianceInput(
        equipment_id="CRANE-RTG-02",
        swl_tonnes=40.0,
        tested_proof_load_tonnes=42.0,  # Required 45.0
        months_since_last_annual_inspection=6,
        months_since_last_quadrennial_survey=24,
        wire_rope_nominal_diameter_mm=30.0,
        wire_rope_measured_diameter_mm=29.5,
        visible_broken_wires_in_lay_length=0,
        max_allowed_broken_wires=3,
        corrosion_pitting_severe=False,
    )
    res = PortLiftingComplianceEngine.evaluate(inp)
    assert res.certified_safe is False
    assert any("Tested proof load (42.0T)" in r for r in res.reasons)


def test_lifting_survey_overdue_and_wire_rope_discard():
    """Phase 329: Test annual inspection overdue and wire rope diameter reduction >= 7%."""
    inp = LiftingApplianceInput(
        equipment_id="CRANE-WHARF-03",
        swl_tonnes=16.0,
        tested_proof_load_tonnes=20.0,
        months_since_last_annual_inspection=14,  # Overdue > 12
        months_since_last_quadrennial_survey=65,  # Overdue > 60
        wire_rope_nominal_diameter_mm=20.0,
        wire_rope_measured_diameter_mm=18.4,  # 8.0% loss >= 7.0%
        visible_broken_wires_in_lay_length=5,  # Exceeds max 3
        max_allowed_broken_wires=3,
        corrosion_pitting_severe=True,
    )
    res = PortLiftingComplianceEngine.evaluate(inp)
    assert res.certified_safe is False
    assert any("Annual thorough examination overdue" in r for r in res.reasons)
    assert any("5-Year thorough survey & load test overdue" in r for r in res.reasons)
    assert any("Diameter reduction 8.00%" in r for r in res.reasons)
    assert any("Severe corrosion pitting detected" in r for r in res.reasons)


# ==============================================================================
# Phase 330: Marine Oil Spill Response (OPRC 1990 & NEBA) Tests
# ==============================================================================
def test_oil_spill_tier_classification():
    """Phase 330: Test OPRC 1990 Tier classification boundaries."""
    assert ModularSpillEngine.classify_tier(5.0) == "TIER_1"
    assert ModularSpillEngine.classify_tier(20.0) == "TIER_1"
    assert ModularSpillEngine.classify_tier(20.1) == "TIER_2"
    assert ModularSpillEngine.classify_tier(500.0) == "TIER_2"
    assert ModularSpillEngine.classify_tier(500.1) == "TIER_3"
    assert ModularSpillEngine.classify_tier(2500.0) == "TIER_3"


def test_oil_spill_neba_dispersant_approved():
    """Phase 330: Test NEBA dispersant approval with sufficient depth, distance & low viscosity."""
    inp = OilSpillIncidentInput(
        incident_id="SPILL-2026-ALPHA",
        spill_volume_metric_tonnes=85.0,
        water_depth_meters=22.0,  # >= 10.0m
        distance_from_shore_nm=6.5,  # >= 3.0 NM
        oil_viscosity_cst=1800.0,  # < 10,000 cSt
        vessel_length_overall_meters=180.0,
        current_velocity_knots=1.5,
        skimmer_efficiency_factor=0.8,
        slick_thickness_mm=1.2,
    )
    res: OilSpillResponseResult = MarineOilSpillResponseEngine.evaluate(inp)
    assert res.tier_classification == "TIER_2"
    assert res.dispersant_permitted is True
    assert res.required_boom_length_meters == 540.0  # 3 * 180.0
    assert res.skimmer_recovery_rate_m3_per_hour > 0
    assert len(res.audit_trail_hash) == 64


def test_oil_spill_neba_dispersant_rejected_shallow_nearshore():
    """Phase 330: Test NEBA dispersant rejected due to shallow depth, nearshore, and high viscosity."""
    inp = OilSpillIncidentInput(
        incident_id="SPILL-2026-BETA",
        spill_volume_metric_tonnes=12.0,
        water_depth_meters=6.0,  # < 10.0m
        distance_from_shore_nm=1.8,  # < 3.0 NM
        oil_viscosity_cst=12500.0,  # >= 10,000 cSt
        vessel_length_overall_meters=90.0,
        current_velocity_knots=0.8,
    )
    res = MarineOilSpillResponseEngine.evaluate(inp)
    assert res.tier_classification == "TIER_1"
    assert res.dispersant_permitted is False
    assert any("Water depth 6.0m < 10.0m" in r for r in res.reasons)
    assert any("Distance 1.8 NM < 3.0 NM" in r for r in res.reasons)
    assert any("Oil viscosity 12500.0 cSt >= 10000.0 cSt" in r for r in res.reasons)


# ==============================================================================
# Facade and Modular Engine Consistency Tests
# ==============================================================================
def test_modular_and_facade_consistency():
    """Verify that facade re-exports call the exact same logic as modular engines."""
    assert BallastWaterComplianceEngine is ModularBwmEngine
    assert MaritimeDecarbFuelEngine is ModularDecarbEngine
    assert PortLiftingComplianceEngine is ModularLiftingEngine
    assert MarineOilSpillResponseEngine is ModularSpillEngine


# ==============================================================================
# CLI Commands End-to-End Execution Tests
# ==============================================================================
def test_cli_ballast_eval_json():
    """Test ballast CLI command output formatting via root app."""
    result = runner.invoke(app, ["ballast", "eval", "--vessel", "MV-TEST", "--json"])
    assert result.exit_code == 0
    assert '"compliant": true' in result.output


def test_cli_decarb_eval_json():
    """Test decarb CLI command output formatting via root app."""
    result = runner.invoke(app, ["decarb", "eval", "--ship-id", "IMO-9912345", "--year", "2025", "--json"])
    assert result.exit_code == 0
    assert '"eua_surrender_obligation_mt": 2310.0' in result.output


def test_cli_lifting_test_json():
    """Test lifting CLI command output formatting via root app."""
    result = runner.invoke(app, ["lifting", "test", "--eq-id", "CRANE-01", "--swl", "40", "--proof-load", "45", "--json"])
    assert result.exit_code == 0
    assert '"certified_safe": true' in result.output


def test_cli_spill_eval_json():
    """Test spill CLI command output formatting via root app."""
    result = runner.invoke(app, ["spill", "eval", "--inc-id", "INC-01", "--volume-mt", "50", "--json"])
    assert result.exit_code == 0
    assert '"tier_classification": "TIER_2"' in result.output


def test_cli_bilingual_vietnamese_aliases():
    """Test Vietnamese aliases for all 4 maritime modules."""
    res_nuocdan = runner.invoke(app, ["nuocdan", "eval", "--json"])
    assert res_nuocdan.exit_code == 0
    assert '"compliant": true' in res_nuocdan.output

    res_decarb = runner.invoke(app, ["giamphatthai", "eval", "--json"])
    assert res_decarb.exit_code == 0
    assert '"fueleu_compliance_balance_eur"' in res_decarb.output

    res_lifting = runner.invoke(app, ["thietbinang", "test", "--json"])
    assert res_lifting.exit_code == 0
    assert '"certified_safe"' in res_lifting.output

    res_spill = runner.invoke(app, ["trandau", "eval", "--json"])
    assert res_spill.exit_code == 0
    assert '"tier_classification"' in res_spill.output
