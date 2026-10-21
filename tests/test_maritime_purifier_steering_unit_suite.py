"""Unit tests for Maritime Phase 383 & Phase 384.

Testing Marine Fuel Purifier & Auxiliary Emergency Steering systems.
Zero mock dependencies, strict real calculation checks.
"""


from src.core.maritime.phase_383_marine_fuel_purifier_clarifier import (
    FuelPurifierInput,
    MarineFuelPurifierEngine,
)
from src.core.maritime.phase_384_auxiliary_emergency_steering import (
    AuxiliaryEmergencySteeringEngine,
    SteeringGearInput,
)


def test_purifier_optimal_hfo_operation():
    engine = MarineFuelPurifierEngine()
    inp = FuelPurifierInput(
        fuel_type="HFO",
        flow_rate_m3_h=3.5,
        bowl_speed_rpm=8500.0,
        bowl_radius_m=0.22,
        inlet_temp_c=98.0,
        cat_fines_inlet_ppm=40.0,
        water_content_inlet_pct=1.2,
        vibration_velocity_rms_mm_s=3.2,
        operating_water_pressure_bar=3.0,
        hours_since_last_discharge=1.0,
    )
    res = engine.evaluate(inp)
    assert res.purifier_status == "OPTIMAL"
    assert res.feed_valve_open is True
    assert res.g_force_factor > 17000.0
    assert res.separation_efficiency_pct >= 85.0
    assert res.cat_fines_outlet_ppm <= 15.0
    assert res.vibration_status == "NORMAL"
    assert res.desludge_required is False
    assert len(res.warnings) == 0


def test_purifier_critical_vibration_trip():
    engine = MarineFuelPurifierEngine()
    inp = FuelPurifierInput(
        fuel_type="VLSFO",
        flow_rate_m3_h=4.0,
        bowl_speed_rpm=8500.0,
        inlet_temp_c=85.0,
        cat_fines_inlet_ppm=50.0,
        vibration_velocity_rms_mm_s=7.5,
    )
    res = engine.evaluate(inp)
    assert res.purifier_status == "CRITICAL_TRIP"
    assert res.feed_valve_open is False
    assert res.vibration_status == "UNACCEPTABLE"
    assert any("VIBRATION TRIP" in w for w in res.warnings)


def test_purifier_low_operating_water_and_desludge():
    engine = MarineFuelPurifierEngine()
    inp = FuelPurifierInput(
        operating_water_pressure_bar=2.0,
        hours_since_last_discharge=2.5,
        inlet_temp_c=80.0,
    )
    res = engine.evaluate(inp)
    assert res.purifier_status == "WARNING"
    assert res.desludge_required is True
    assert any("OPERATING WATER LOW" in w for w in res.warnings)
    assert any("AL+SI EXCEEDANCE" in w for w in res.warnings)


def test_steering_main_compliant():
    engine = AuxiliaryEmergencySteeringEngine()
    inp = SteeringGearInput(
        mode="MAIN",
        current_angle_deg=-35.0,
        target_angle_deg=30.0,
        elapsed_time_s=25.0,
        hydraulic_pressure_bar=190.0,
        oil_tank_level_pct=75.0,
    )
    res = engine.evaluate(inp)
    assert res.mode == "MAIN"
    assert res.travel_compliant is True
    assert res.steering_status == "OPERATIONAL"
    assert res.hydraulic_integrity == "NORMAL"
    assert len(res.warnings) == 0


def test_steering_main_time_exceeded():
    engine = AuxiliaryEmergencySteeringEngine()
    inp = SteeringGearInput(
        mode="MAIN",
        elapsed_time_s=32.0,
    )
    res = engine.evaluate(inp)
    assert res.travel_compliant is False
    assert res.steering_status == "ALARM"
    assert any("SOLAS II-1 R29 VIOLATION" in w for w in res.warnings)


def test_steering_auxiliary_compliant_and_non_compliant():
    engine = AuxiliaryEmergencySteeringEngine()
    # Compliant aux
    inp_ok = SteeringGearInput(
        mode="AUXILIARY_EMERGENCY",
        elapsed_time_s=55.0,
    )
    res_ok = engine.evaluate(inp_ok)
    assert res_ok.mode == "AUXILIARY_EMERGENCY"
    assert res_ok.travel_compliant is True

    # Non-compliant aux (> 60s)
    inp_slow = SteeringGearInput(
        mode="AUXILIARY_EMERGENCY",
        elapsed_time_s=65.0,
    )
    res_slow = engine.evaluate(inp_slow)
    assert res_slow.travel_compliant is False
    assert any("SOLAS II-1 R29 VIOLATION" in w for w in res_slow.warnings)


def test_steering_hydraulic_overpressure_and_hunting():
    engine = AuxiliaryEmergencySteeringEngine()
    inp = SteeringGearInput(
        hydraulic_pressure_bar=260.0,
        oil_tank_level_pct=35.0,
        rudder_demand_diff_deg=5.0,
        rudder_demand_diff_duration_s=3.5,
        main_power_available=False,
        emergency_power_active=True,
    )
    res = engine.evaluate(inp)
    assert res.hydraulic_integrity == "LOW_LEVEL"
    assert res.failover_ready is True
    assert any("HYDRAULIC OIL LOW" in w for w in res.warnings)
    assert any("STEERING LAG ALARM" in w for w in res.warnings)
