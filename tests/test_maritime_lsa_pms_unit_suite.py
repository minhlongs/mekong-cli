"""Unit tests for Maritime Phases 363 & 364 (LSA Lifeboat HRU & Marine Generator PMS).

Strictly kept under 200 lines, 0 mocks, testing real engineering dynamics.
"""

from src.core.maritime.phase_363_lsa_lifeboat_hru_release import (
    LifeboatHruInput,
    LifeboatHruReleaseEngine,
)
from src.core.maritime.phase_364_marine_generator_pms_blackout import (
    MarineGeneratorPmsEngine,
    MarineGeneratorUnit,
    PmsEvaluationInput,
)


def test_lifeboat_nominal_freefall_launch():
    inp = LifeboatHruInput(
        boat_id="LB-SAFE-01",
        drop_height_m=18.0,
        ramp_angle_deg=33.0,
        entry_angle_deg=56.0,
        peak_acceleration_g=9.2,
        hru_water_depth_m=2.5,
        is_manual_interlock_released=True,
    )
    res = LifeboatHruReleaseEngine.evaluate(inp)
    assert res.boat_id == "LB-SAFE-01"
    assert res.impact_velocity_m_s > 18.0
    assert res.is_entry_angle_compliant is True
    assert res.is_acceleration_tolerable is True
    assert res.is_hru_depth_compliant is True
    assert res.is_safe_to_launch_or_float is True
    assert res.safety_status == "READY_FOR_DEPLOYMENT"
    assert len(res.advisories) == 0


def test_lifeboat_shallow_and_excessive_entry_angle():
    shallow_inp = LifeboatHruInput(
        boat_id="LB-SHALLOW",
        drop_height_m=16.0,
        ramp_angle_deg=30.0,
        entry_angle_deg=44.0,  # < 50 deg
        peak_acceleration_g=8.0,
        hru_water_depth_m=2.0,
    )
    shallow_res = LifeboatHruReleaseEngine.evaluate(shallow_inp)
    assert shallow_res.is_entry_angle_compliant is False
    assert shallow_res.safety_status == "WARNING_RESTRICTED"

    steep_inp = LifeboatHruInput(
        boat_id="LB-STEEP",
        drop_height_m=22.0,
        ramp_angle_deg=35.0,
        entry_angle_deg=69.0,  # > 65 deg
        peak_acceleration_g=10.5,
        hru_water_depth_m=2.2,
    )
    steep_res = LifeboatHruReleaseEngine.evaluate(steep_inp)
    assert steep_res.is_entry_angle_compliant is False


def test_lifeboat_extreme_g_force_and_hru_overdue():
    danger_inp = LifeboatHruInput(
        boat_id="LB-DANGER",
        drop_height_m=28.0,
        ramp_angle_deg=35.0,
        entry_angle_deg=58.0,
        peak_acceleration_g=16.8,  # > 15.0 g
        hru_water_depth_m=4.8,      # > 4.0 m
    )
    danger_res = LifeboatHruReleaseEngine.evaluate(danger_inp)
    assert danger_res.is_acceleration_tolerable is False
    assert danger_res.is_hru_depth_compliant is False
    assert danger_res.safety_status == "CRITICAL_FAILURE"


def test_pms_nominal_load_sharing():
    inp = PmsEvaluationInput(
        generators=[
            MarineGeneratorUnit("DG-01", rated_kw=1000.0, current_kw=350.0, frequency_hz=60.0, voltage_pct=100.0),
            MarineGeneratorUnit("DG-02", rated_kw=1000.0, current_kw=360.0, frequency_hz=60.0, voltage_pct=100.0),
        ]
    )
    res = MarineGeneratorPmsEngine.evaluate(inp)
    assert res.total_running_kw == 710.0
    assert res.total_capacity_kw == 2000.0
    assert res.total_load_pct == 35.5
    assert res.is_load_sharing_balanced is True
    assert res.is_auto_start_required is False
    assert res.shedding_stage == 0
    assert res.blackout_risk_status == "NORMAL_STABLE"


def test_pms_standby_auto_start_and_imbalance():
    inp = PmsEvaluationInput(
        generators=[
            MarineGeneratorUnit("DG-01", rated_kw=1000.0, current_kw=920.0, frequency_hz=59.8, voltage_pct=98.0),
            MarineGeneratorUnit("DG-02", rated_kw=1000.0, current_kw=790.0, frequency_hz=59.8, voltage_pct=98.0),
        ]
    )
    res = MarineGeneratorPmsEngine.evaluate(inp)
    assert res.total_load_pct == 85.5  # >= 85%
    assert res.is_auto_start_required is True
    assert res.is_load_sharing_balanced is False  # 92% - 79% = 13% > 10%
    assert res.blackout_risk_status == "HIGH_LOAD_STANDBY_START"


def test_pms_preferential_shedding_and_blackout_trip():
    # Stage 2 shedding test
    shed_inp = PmsEvaluationInput(
        generators=[
            MarineGeneratorUnit("DG-01", rated_kw=1000.0, current_kw=960.0, frequency_hz=58.5, voltage_pct=92.0),
        ]
    )
    shed_res = MarineGeneratorPmsEngine.evaluate(shed_inp)
    assert shed_res.total_load_pct == 96.0
    assert shed_res.shedding_stage == 2
    assert shed_res.blackout_risk_status == "LOAD_SHEDDING_ACTIVE"

    # Emergency blackout trip test: freq <= 57.0 Hz sustained >= 0.5s
    trip_inp = PmsEvaluationInput(
        generators=[
            MarineGeneratorUnit("DG-01", rated_kw=1000.0, current_kw=1050.0, frequency_hz=56.4, voltage_pct=81.0),
        ],
        sustained_overload_seconds=0.7,
    )
    trip_res = MarineGeneratorPmsEngine.evaluate(trip_inp)
    assert trip_res.blackout_risk_status == "EMERGENCY_BLACKOUT_TRIP"
