"""Zero-mock unit tests for Maritime Phases 367 & 368.

Phase 367: Marine Fuel ISO 8217 & ASTM D4740 Compatibility
Phase 368: Marine Battery BESS & Thermal Runaway Safety
Strictly kept under 200 lines.
"""

from src.core.maritime_fuel_bess_esi_ahc_engine import (
    BessModuleInput,
    BessSafetyTripStage,
    FuelOilIso8217Engine,
    FuelSampleInput,
    MarineBatteryBessEngine,
    SpotTestRating,
)


def test_fuel_oil_iso8217_compliant() -> None:
    sample = FuelSampleInput(
        sample_id="VLSFO-TEST-01",
        fuel_grade="VLSFO",
        al_plus_si_mg_kg=18.0,
        flash_point_c=65.0,
        viscosity_at_50c_cst=180.0,
        total_sediment_potential_pct=0.04,
        sulfur_pct=0.48,
        spot_test_rating=SpotTestRating.GOOD,
    )
    rep = FuelOilIso8217Engine().evaluate(sample)
    assert rep.is_compliant is True
    assert rep.status == "COMPLIANT"
    assert rep.cat_fines_status == "OPTIMAL"
    assert rep.recommended_preheat_temp_c > 80.0
    assert len(rep.warnings) == 0


def test_fuel_oil_iso8217_cat_fines_and_flash_fail() -> None:
    sample = FuelSampleInput(
        sample_id="VLSFO-BAD-01",
        fuel_grade="VLSFO",
        al_plus_si_mg_kg=65.0,  # Exceeds statutory 60.0
        flash_point_c=58.0,  # Below SOLAS 60C limit
        viscosity_at_50c_cst=380.0,
        total_sediment_potential_pct=0.12,  # Exceeds 0.10%
        sulfur_pct=0.55,  # Exceeds 0.50%
        spot_test_rating=SpotTestRating.POOR,
    )
    rep = FuelOilIso8217Engine().evaluate(sample)
    assert rep.is_compliant is False
    assert rep.status == "OFF_SPEC"
    assert rep.cat_fines_status == "CRITICAL_OFF_SPEC"
    assert any("Flash point 58.0°C below SOLAS" in w for w in rep.warnings)
    assert any("TSP 0.12%" in w for w in rep.warnings)


def test_fuel_oil_cimac_cat_fines_alert() -> None:
    sample = FuelSampleInput(
        sample_id="VLSFO-CIMAC-01",
        fuel_grade="VLSFO",
        al_plus_si_mg_kg=35.0,  # 25 < Al+Si <= 60
        flash_point_c=62.0,
        viscosity_at_50c_cst=180.0,
        total_sediment_potential_pct=0.05,
        sulfur_pct=0.49,
        spot_test_rating=SpotTestRating.BORDERLINE,
    )
    rep = FuelOilIso8217Engine().evaluate(sample)
    assert rep.is_compliant is True
    assert rep.cat_fines_status == "HIGH_TREATMENT_NEEDED"
    assert any("multi-stage separator" in w for w in rep.warnings)


def test_marine_bess_normal_operation() -> None:
    module = BessModuleInput(
        pack_id="PACK-01",
        soc_pct=70.0,
        soh_pct=95.0,
        c_rate=0.8,
        cell_max_temp_c=32.0,
        cell_delta_temp_c=1.5,
        offgas_h2_ppm=0.0,
        offgas_co_ppm=0.0,
    )
    rep = MarineBatteryBessEngine().evaluate(module)
    assert rep.is_safe is True
    assert rep.trip_stage == BessSafetyTripStage.STAGE_0_NORMAL
    assert rep.allowable_c_rate == 1.0
    assert len(rep.actions_required) == 0


def test_marine_bess_stage_1_alarm_derate() -> None:
    module = BessModuleInput(
        pack_id="PACK-HOT",
        soc_pct=92.0,  # SoC > 90%
        soh_pct=78.0,  # SoH < 80%
        c_rate=1.2,  # Exceeds standard 1.0C
        cell_max_temp_c=48.0,  # > 45C
        cell_delta_temp_c=6.0,  # > 5C
        offgas_h2_ppm=5.0,
        offgas_co_ppm=2.0,
    )
    rep = MarineBatteryBessEngine().evaluate(module)
    assert rep.is_safe is True
    assert rep.trip_stage == BessSafetyTripStage.STAGE_1_ALARM_DERATE
    assert rep.allowable_c_rate == 0.5
    assert any("ALARM: De-rate" in a for a in rep.actions_required)
    assert any("SoC > 90%" in a for a in rep.actions_required)


def test_marine_bess_stage_2_electrical_trip() -> None:
    module = BessModuleInput(
        pack_id="PACK-GAS-LEAK",
        soc_pct=60.0,
        soh_pct=85.0,
        c_rate=0.5,
        cell_max_temp_c=58.0,  # >= 55C
        cell_delta_temp_c=4.0,
        offgas_h2_ppm=60.0,  # >= 50 ppm H2
        offgas_co_ppm=30.0,  # >= 25 ppm CO
    )
    rep = MarineBatteryBessEngine().evaluate(module)
    assert rep.is_safe is False
    assert rep.trip_stage == BessSafetyTripStage.STAGE_2_ELECTRICAL_TRIP
    assert rep.allowable_c_rate == 0.0
    assert any("TRIP: Open DC main contactors" in a for a in rep.actions_required)


def test_marine_bess_stage_3_fire_deluge() -> None:
    module = BessModuleInput(
        pack_id="PACK-CRITICAL",
        soc_pct=50.0,
        soh_pct=80.0,
        c_rate=0.0,
        cell_max_temp_c=80.0,  # >= 75C
        cell_delta_temp_c=12.0,
        offgas_h2_ppm=150.0,
        offgas_co_ppm=80.0,
    )
    rep = MarineBatteryBessEngine().evaluate(module)
    assert rep.is_safe is False
    assert rep.trip_stage == BessSafetyTripStage.STAGE_3_FIRE_DELUGE
    assert any("EMERGENCY: Activate high-pressure water mist deluge" in a for a in rep.actions_required)
