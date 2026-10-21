"""Unit tests for Maritime Phase 387 & Phase 388.

Testing Chilled Water HVAC Cargo Hold Climate & Food Waste Pulper Bio-Digestion.
Strictly zero mock dependencies, exact physical calculations.
"""

from src.core.maritime.phase_387_chilled_water_hvac_control import (
    ChilledWaterHvacEngine,
    ChilledWaterHvacInput,
)
from src.core.maritime.phase_388_food_waste_pulper_biodigestion import (
    FoodWastePulperEngine,
    FoodWastePulperInput,
)


def test_hvac_nominal_optimal_cooling():
    engine = ChilledWaterHvacEngine()
    inp = ChilledWaterHvacInput(
        chw_flow_rate_m3_h=65.0,
        chw_temp_supply_c=7.0,
        chw_temp_return_c=12.0,
        compressor_power_kw=85.0,
        ambient_temp_c=30.0,
        ambient_relative_humidity_pct=60.0,
        cargo_hold_temp_c=22.0,
        cargo_surface_temp_c=25.0,
        cargo_hold_rh_pct=50.0,
        refrigerant_concentration_ppm=5.0,
    )
    res = engine.evaluate(inp)
    assert res.chiller_status == "OPTIMAL"
    assert res.compressor_trip is False
    assert res.cooling_capacity_kw > 350.0
    assert res.cop_actual > 4.0
    assert res.sweat_hazard == "SAFE"
    assert res.ventilation_action == "VENTILATE"
    assert len(res.warnings) == 0


def test_hvac_cargo_sweat_and_suboptimal_cop():
    engine = ChilledWaterHvacEngine()
    # High ambient humidity, cold cargo surface -> cargo sweat hazard
    inp = ChilledWaterHvacInput(
        chw_flow_rate_m3_h=40.0,
        chw_temp_supply_c=8.0,
        chw_temp_return_c=11.0,
        compressor_power_kw=70.0,
        ambient_temp_c=32.0,
        ambient_relative_humidity_pct=85.0,
        cargo_hold_temp_c=20.0,
        cargo_surface_temp_c=18.0,
        cargo_hold_rh_pct=60.0,
    )
    res = engine.evaluate(inp)
    assert res.chiller_status == "SUB_OPTIMAL"
    assert res.cop_actual < 2.5
    assert res.sweat_hazard == "CARGO_SWEAT_RISK"
    assert res.ventilation_action == "RECIRCULATE"
    assert any("CARGO SWEAT RISK" in w for w in res.warnings)


def test_hvac_refrigerant_critical_trip():
    engine = ChilledWaterHvacEngine()
    inp = ChilledWaterHvacInput(
        refrigerant_concentration_ppm=120.0,
    )
    res = engine.evaluate(inp)
    assert res.compressor_trip is True
    assert res.chiller_status == "CRITICAL_TRIP"
    assert any("CRITICAL REFRIGERANT LEAK" in w for w in res.warnings)


def test_food_waste_compliant_outside_special_area():
    engine = FoodWastePulperEngine()
    inp = FoodWastePulperInput(
        particle_size_mm=15.0,
        distance_to_nearest_land_nm=4.5,
        in_special_area=False,
        ship_speed_knots=10.0,
        vfa_to_tic_ratio=0.25,
        grease_trap_oil_ppm=10.0,
        daily_waste_mass_kg=150.0,
    )
    res = engine.evaluate(inp)
    assert res.comminution_compliant is True
    assert res.discharge_permitted is True
    assert res.digester_status == "STABLE"
    assert res.grease_trap_compliant is True
    assert res.biogas_yield_estimate_m3 > 20.0
    assert res.regulatory_classification == "DISCHARGE_PERMITTED"
    assert len(res.warnings) == 0


def test_food_waste_special_area_violation():
    engine = FoodWastePulperEngine()
    # Inside Special Area, 8 NM (< 12 NM required)
    inp = FoodWastePulperInput(
        particle_size_mm=20.0,
        distance_to_nearest_land_nm=8.0,
        in_special_area=True,
        ship_speed_knots=12.0,
    )
    res = engine.evaluate(inp)
    assert res.comminution_compliant is True
    assert res.discharge_permitted is False
    assert res.regulatory_classification == "RETENTION_MANDATORY"
    assert any("SPECIAL AREA DISTANCE VIOLATION" in w for w in res.warnings)


def test_food_waste_unscreened_particle_and_sour_digester():
    engine = FoodWastePulperEngine()
    # Large particle size > 25mm, souring VFA/TIC > 0.40, greasy water > 15 ppm
    inp = FoodWastePulperInput(
        particle_size_mm=32.0,
        distance_to_nearest_land_nm=2.0,
        ship_speed_knots=0.2,
        vfa_to_tic_ratio=0.45,
        grease_trap_oil_ppm=22.0,
    )
    res = engine.evaluate(inp)
    assert res.comminution_compliant is False
    assert res.discharge_permitted is False
    assert res.digester_status == "UPSET"
    assert res.grease_trap_compliant is False
    assert any("COMMINUTION NON-COMPLIANT" in w for w in res.warnings)
    assert any("CRITICAL DIGESTER UPSET" in w for w in res.warnings)
