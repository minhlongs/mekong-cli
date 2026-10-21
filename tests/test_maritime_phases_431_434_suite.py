"""Zero-mock unit test suite for Maritime Automation Phases 431-434.

Verifies:
- Phase 431: Stern Tube lube gravity DP & seal thermal boundary
- Phase 432: Diesel gen auto-sync window & reverse power relay trip
- Phase 433: EGCS scrubber washwater MEPC.340(77) compliance & holding divert
- Phase 434: Emergency bilge suction valve sizing & flooding trip
- Master Integration Facade: Multi-system telemetry orchestration
Strictly < 175 LOC, zero mocks.
"""

from src.core.maritime.phase_431_stern_tube_lube_gravity import (
    SternTubeLubeEngine,
    SternTubeLubeTelemetry,
)
from src.core.maritime.phase_432_diesel_gen_sync_loadshare import (
    DieselGenSyncEngine,
    GeneratorSyncTelemetry,
)
from src.core.maritime.phase_433_scrubber_washwater_monitoring import (
    ScrubberWashwaterEngine,
    ScrubberWashwaterTelemetry,
)
from src.core.maritime.phase_434_emergency_bilge_suction import (
    EmergencyBilgeSuctionEngine,
    EmergencyBilgeTelemetry,
)
from src.core.maritime_stern_sync_scrubber_bilge_engine import (
    MaritimeSternSyncScrubberBilgeEngine,
    MaritimePhases431to434Telemetry,
)


def test_phase_431_stern_tube_nominal_dp():
    engine = SternTubeLubeEngine()
    # 8.62m tank head, 5.0m seawater draft produces ~+0.25 bar differential
    telemetry = SternTubeLubeTelemetry(
        gravity_tank_height_m=8.62,
        ship_draft_m=5.0,
        fwd_seal_temp_c=52.0,
        aft_seal_temp_c=58.0,
        water_content_pct=0.3,
    )
    res = engine.evaluate(telemetry)
    assert res.dp_in_envelope is True
    assert res.seal_overheat is False
    assert res.status == "OPTIMAL_LUBRICATION"
    assert res.compliance_flags["DNV_DP_ENVELOPE"] is True
    assert res.compliance_flags["ISO_19973_COMPLIANT"] is True


def test_phase_431_stern_tube_seal_overheat_and_water():
    engine = SternTubeLubeEngine()
    telemetry = SternTubeLubeTelemetry(
        gravity_tank_height_m=3.0,
        ship_draft_m=8.2,
        fwd_seal_temp_c=78.0,
        aft_seal_temp_c=80.0,
        water_content_pct=1.8,
    )
    res = engine.evaluate(telemetry)
    assert res.dp_in_envelope is False
    assert res.seal_overheat is True
    assert res.status == "CRITICAL_SEAL_FAILURE_RISK"
    assert res.compliance_flags["WATER_PURITY_SAFE"] is False
    assert res.compliance_flags["SEAL_THERMAL_SAFE"] is False


def test_phase_432_generator_sync_ready_to_close():
    engine = DieselGenSyncEngine()
    telemetry = GeneratorSyncTelemetry(
        bus_frequency_hz=60.0,
        incoming_frequency_hz=60.08,
        bus_voltage_v=440.0,
        incoming_voltage_v=442.0,
        phase_angle_diff_deg=2.5,
        active_power_kw=450.0,
    )
    res = engine.evaluate(telemetry)
    assert res.sync_window_matched is True
    assert res.reverse_power_trip is False
    assert res.breaker_close_permitted is True
    assert res.status == "SYNCHRONIZED_READY_TO_CLOSE"


def test_phase_432_generator_reverse_power_trip():
    engine = DieselGenSyncEngine()
    telemetry = GeneratorSyncTelemetry(
        active_power_kw=-60.0,
        rated_power_kw=800.0,
        reverse_power_duration_sec=3.5,
    )
    res = engine.evaluate(telemetry)
    assert res.reverse_power_trip is True
    assert res.breaker_close_permitted is False
    assert res.status == "REVERSE_POWER_TRIP"
    assert res.compliance_flags["REVERSE_POWER_SAFE"] is False


def test_phase_433_scrubber_washwater_compliant():
    engine = ScrubberWashwaterEngine()
    telemetry = ScrubberWashwaterTelemetry(
        inlet_turbidity_fnu=3.0,
        discharge_turbidity_fnu=15.0,
        discharge_pah_ug_l=25.0,
        discharge_ph=6.8,
        nitrate_mg_l=30.0,
    )
    res = engine.evaluate(telemetry)
    assert res.turbidity_compliant is True
    assert res.pah_compliant is True
    assert res.ph_compliant is True
    assert res.overboard_discharge_allowed is True
    assert res.divert_to_holding_tank is False
    assert res.status == "MEPC_340_COMPLIANT_DISCHARGING"


def test_phase_433_scrubber_washwater_acidic_divert():
    engine = ScrubberWashwaterEngine()
    telemetry = ScrubberWashwaterTelemetry(
        discharge_ph=5.8,
        discharge_pah_ug_l=60.0,
    )
    res = engine.evaluate(telemetry)
    assert res.ph_compliant is False
    assert res.pah_compliant is False
    assert res.overboard_discharge_allowed is False
    assert res.divert_to_holding_tank is True
    assert res.status == "MARPOL_VIOLATION_DIVERTED"


def test_phase_434_emergency_bilge_nominal_standby():
    engine = EmergencyBilgeSuctionEngine()
    telemetry = EmergencyBilgeTelemetry(
        suction_pipe_diameter_mm=350.0,
        pump_suction_branch_diameter_mm=450.0,
        bilge_water_level_mm=120.0,
        cooling_pump_running=True,
    )
    res = engine.evaluate(telemetry)
    assert res.valve_sizing_compliant is True
    assert res.bilge_alarm_state == "NORMAL_LEVEL"
    assert res.status == "STANDBY_READY"
    assert res.compliance_flags["IACS_UR_M29_COMPLIANT"] is True


def test_phase_434_emergency_bilge_critical_flooding():
    engine = EmergencyBilgeSuctionEngine()
    telemetry = EmergencyBilgeTelemetry(
        bilge_water_level_mm=650.0,
        emergency_valve_open_pct=100.0,
        main_sea_chest_valve_open_pct=80.0,
    )
    res = engine.evaluate(telemetry)
    assert res.bilge_alarm_state == "CRITICAL_FLOODING_TRIP"
    assert res.emergency_suction_activated is True
    assert res.sea_chest_interlock_safe is False
    assert res.status == "EMERGENCY_DEWATERING_MANDATORY"


def test_master_integration_facade():
    engine = MaritimeSternSyncScrubberBilgeEngine()
    # Nominal case with balanced head
    telemetry_nominal = MaritimePhases431to434Telemetry(
        stern_tube=SternTubeLubeTelemetry(gravity_tank_height_m=8.62, ship_draft_m=5.0)
    )
    res_nominal = engine.evaluate(telemetry_nominal)
    assert res_nominal.overall_status == "ALL_SYSTEMS_NOMINAL"
    assert res_nominal.action_required is False
    assert "DNV_DP_ENVELOPE" in res_nominal.compliance_matrix

    # Critical case
    critical_telemetry = MaritimePhases431to434Telemetry(
        emergency_bilge=EmergencyBilgeTelemetry(bilge_water_level_mm=700.0)
    )
    res_critical = engine.evaluate(critical_telemetry)
    assert res_critical.overall_status == "CRITICAL_ACTION_REQUIRED"
    assert res_critical.action_required is True
