"""Unit tests for Maritime Phases 395-398 Core Engines.

Strictly < 200 LOC, zero mocks.
"""

from src.core.maritime.phase_395_emergency_fire_pump_sea_suction import (
    EmergencyFirePumpEngine,
    EmergencyFirePumpInput,
)
from src.core.maritime.phase_396_steering_gear_dual_hydraulic import (
    SteeringGearEngine,
    SteeringGearInput,
)
from src.core.maritime.phase_397_quick_closing_valve_emergency_shutoff import (
    QuickClosingValveEngine,
    QuickClosingValveInput,
)
from src.core.maritime.phase_398_scavenge_air_fire_detection import (
    ScavengeFireEngine,
    ScavengeFireInput,
)


def test_fire_pump_nominal_seaworthy():
    engine = EmergencyFirePumpEngine()
    res = engine.evaluate(EmergencyFirePumpInput())
    assert res.pump_operational_status == "SEAWORTHY_OPTIMAL"
    assert res.discharge_capacity_compliant is True
    assert res.discharge_pressure_compliant is True
    assert res.suction_priming_compliant is True
    assert res.endurance_compliant is True
    assert res.fire_hose_jets_supported >= 2
    assert len(res.warnings) == 0


def test_fire_pump_critical_defects():
    engine = EmergencyFirePumpEngine()
    # Flow too low, excessive suction lift, delayed priming
    res = engine.evaluate(
        EmergencyFirePumpInput(
            discharge_flow_rate_m3_h=18.0,
            suction_lift_head_m=5.2,
            priming_duration_seconds=210.0,
        )
    )
    assert res.pump_operational_status == "CRITICAL_DEFECT_NOT_SEAWORTHY"
    assert res.discharge_capacity_compliant is False
    assert res.suction_priming_compliant is False


def test_steering_gear_nominal_redundant():
    engine = SteeringGearEngine()
    res = engine.evaluate(SteeringGearInput())
    assert res.steering_readiness_status == "SEAWORTHY_REDUNDANT_OPTIMAL"
    assert res.main_gear_speed_compliant is True
    assert res.auxiliary_gear_speed_compliant is True
    assert res.redundancy_active is True
    assert res.hydraulic_pressure_status == "NORMAL_OPTIMAL"


def test_steering_gear_critical_failure():
    engine = SteeringGearEngine()
    # Both pumps dead, low oil level
    res = engine.evaluate(
        SteeringGearInput(
            pump_1_operational=False,
            pump_2_operational=False,
            oil_reservoir_level_pct=15.0,
        )
    )
    assert res.steering_readiness_status == "CRITICAL_STEERING_FAILURE"
    assert res.reservoir_level_ok is False
    assert res.redundancy_active is False


def test_quick_closing_valves_nominal():
    engine = QuickClosingValveEngine()
    res = engine.evaluate(QuickClosingValveInput())
    assert res.valve_system_status == "SEAWORTHY_FIRE_ISOLATION_READY"
    assert res.control_air_pressure_ok is True
    assert res.closure_speed_compliant is True
    assert res.closure_completeness_pct == 100.0


def test_quick_closing_valves_partial_closure_failure():
    engine = QuickClosingValveEngine()
    res = engine.evaluate(
        QuickClosingValveInput(
            valves_tripped_count=4,
            valves_total_count=6,
            closure_response_time_sec=4.2,
        )
    )
    assert res.valve_system_status == "CRITICAL_ISOLATION_FAILURE"
    assert res.closure_speed_compliant is False
    assert res.closure_completeness_pct < 100.0


def test_scavenge_fire_nominal_clear():
    engine = ScavengeFireEngine()
    res = engine.evaluate(ScavengeFireInput())
    assert res.fire_hazard_status == "NORMAL_CLEAR"
    assert res.under_piston_temp_ok is True
    assert res.engine_slowdown_demanded is False
    assert res.temperature_margin_c > 50.0


def test_scavenge_fire_active_emergency():
    engine = ScavengeFireEngine()
    # High under-piston temp > 180°C
    res = engine.evaluate(
        ScavengeFireInput(
            max_under_piston_temp_c=195.0,
            cylinder_oil_drain_rate_l_h=4.5,
            soot_density_mg_m3=75.0,
        )
    )
    assert res.fire_hazard_status == "SCAVENGE_FIRE_ACTIVE"
    assert res.under_piston_temp_ok is False
    assert res.engine_slowdown_demanded is True
    assert res.unburnt_oil_fouling_level == "HIGH_COMBUSTIBLE_RESIDUE"
