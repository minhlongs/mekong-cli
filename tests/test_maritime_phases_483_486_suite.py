"""Zero-mock Pytest Suite for Maritime Automation Phases 483-486.

Covers:
- Phase 483: STP Aeration Dissolved Oxygen & Air-Lift Sludge Return
- Phase 484: Main Engine Bearing Temperature & Optical Oil Mist Slowdown
- Phase 485: Exhaust Gas Boiler (EGB) Forced Circulation Pump & Dry-Run Interlock
- Phase 486: Emergency Diesel Generator (EDG) Blackout Auto-Start & Fuel Day Tank
- Master Coordinator: MaritimeSafetyAuxiliaryBatch6Engine
- CLI Commands via CliRunner
"""

from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch6_command import maritime_aux6_app


from src.core.maritime.phase_483_stp_aeration_sludge_return import (
    StpAerationSludgeReturnEngine,
    StpAerationStatus,
    StpAerationTelemetry,
)
from src.core.maritime.phase_484_bearing_mist_slowdown import (
    BearingMistSlowdownEngine,
    BearingMistStatus,
    BearingMistSlowdownTelemetry,
)
from src.core.maritime.phase_485_egb_circulation_dryrun import (
    EgbCirculationDryRunEngine,
    EgbCirculationStatus,
    EgbCirculationTelemetry,
)
from src.core.maritime.phase_486_emergency_gen_blackout import (
    EmergencyGenBlackoutEngine,
    EmergencyGenStatus,
    EmergencyGenTelemetry,
)
from src.core.maritime_safety_auxiliary_batch6_engine import (
    MaritimeAuxiliaryBatch6Telemetry,
    MaritimeSafetyAuxiliaryBatch6Engine,
)


def test_phase_483_stp_aeration_nominal_and_failure_modes():
    # Nominal
    telem_normal = StpAerationTelemetry(
        dissolved_oxygen_mg_l=3.2,
        aeration_pressure_bar=0.35,
        blower_running=True,
        standby_blower_ready=True,
        airlift_sludge_flow_l_min=22.0,
        blower_failover_elapsed_s=0.0,
    )
    res_normal = StpAerationSludgeReturnEngine.evaluate(telem_normal)
    assert res_normal.status == StpAerationStatus.NORMAL
    assert res_normal.aerobic_treatment_healthy is True
    assert res_normal.standby_blower_start_command is False

    # Blower pressure loss -> failover start commanded
    telem_blower_loss = StpAerationTelemetry(
        dissolved_oxygen_mg_l=2.1,
        aeration_pressure_bar=0.08,
        blower_running=True,
        standby_blower_ready=True,
        airlift_sludge_flow_l_min=20.0,
        blower_failover_elapsed_s=10.0,
    )
    res_blower_loss = StpAerationSludgeReturnEngine.evaluate(telem_blower_loss)
    assert res_blower_loss.status == StpAerationStatus.BLOWER_PRESSURE_LOST
    assert res_blower_loss.standby_blower_start_command is True
    assert res_blower_loss.aerobic_treatment_healthy is False

    # Septic critical DO (< 1.0 mg/L)
    telem_septic = StpAerationTelemetry(
        dissolved_oxygen_mg_l=0.7,
        aeration_pressure_bar=0.28,
        blower_running=True,
        standby_blower_ready=True,
        airlift_sludge_flow_l_min=18.0,
        blower_failover_elapsed_s=0.0,
    )
    res_septic = StpAerationSludgeReturnEngine.evaluate(telem_septic)
    assert res_septic.status == StpAerationStatus.SEPTIC_ALARM_STANDBY_START
    assert res_septic.standby_blower_start_command is True

    # Sludge recirculation failure (< 15 L/min)
    telem_sludge_fail = StpAerationTelemetry(
        dissolved_oxygen_mg_l=2.5,
        aeration_pressure_bar=0.30,
        blower_running=True,
        standby_blower_ready=True,
        airlift_sludge_flow_l_min=8.0,
        blower_failover_elapsed_s=0.0,
    )
    res_sludge = StpAerationSludgeReturnEngine.evaluate(telem_sludge_fail)
    assert res_sludge.status == StpAerationStatus.SLUDGE_RECIRC_FAILURE
    assert res_sludge.sludge_recirculation_ok is False


def test_phase_484_bearing_mist_slowdown_boundaries():
    # Nominal
    telem_normal = BearingMistSlowdownTelemetry(
        max_crosshead_temp_c=68.0,
        max_main_bearing_temp_c=64.0,
        bearing_delta_t_c=3.5,
        crankcase_oil_mist_pct_lel=0.6,
        lube_oil_inlet_p_bar=2.3,
        engine_load_pct=80.0,
    )
    res_normal = BearingMistSlowdownEngine.evaluate(telem_normal)
    assert res_normal.status == BearingMistStatus.NORMAL
    assert res_normal.slowdown_command is False
    assert res_normal.crankcase_explosion_risk is False

    # Oil mist emergency slowdown (>= 2.5% LEL)
    telem_mist = BearingMistSlowdownTelemetry(
        max_crosshead_temp_c=72.0,
        max_main_bearing_temp_c=68.0,
        bearing_delta_t_c=4.0,
        crankcase_oil_mist_pct_lel=2.8,
        lube_oil_inlet_p_bar=2.1,
        engine_load_pct=80.0,
    )
    res_mist = BearingMistSlowdownEngine.evaluate(telem_mist)
    assert res_mist.status == BearingMistStatus.EMERGENCY_SLOWDOWN_TRIP
    assert res_mist.slowdown_command is True
    assert res_mist.crankcase_explosion_risk is True

    # Bearing thermal runaway trip (crosshead >= 85 C)
    telem_thermal = BearingMistSlowdownTelemetry(
        max_crosshead_temp_c=86.5,
        max_main_bearing_temp_c=74.0,
        bearing_delta_t_c=14.0,
        crankcase_oil_mist_pct_lel=1.1,
        lube_oil_inlet_p_bar=2.0,
        engine_load_pct=75.0,
    )
    res_thermal = BearingMistSlowdownEngine.evaluate(telem_thermal)
    assert res_thermal.status == BearingMistStatus.EMERGENCY_SLOWDOWN_TRIP
    assert res_thermal.slowdown_command is True

    # Critical lube oil pressure drop (< 1.5 bar)
    telem_lo = BearingMistSlowdownTelemetry(
        max_crosshead_temp_c=70.0,
        max_main_bearing_temp_c=66.0,
        bearing_delta_t_c=3.0,
        crankcase_oil_mist_pct_lel=0.5,
        lube_oil_inlet_p_bar=1.3,
        engine_load_pct=60.0,
    )
    res_lo = BearingMistSlowdownEngine.evaluate(telem_lo)
    assert res_lo.status == BearingMistStatus.LUBE_OIL_PRESSURE_CRITICAL
    assert res_lo.slowdown_command is True
    assert res_lo.lube_oil_pressure_ok is False


def test_phase_485_egb_circulation_dryrun_protection():
    # Nominal
    telem_normal = EgbCirculationTelemetry(
        pump_diff_pressure_bar=1.6,
        water_flow_m3_h=24.0,
        standby_pump_available=True,
        loss_of_flow_duration_s=0.0,
        exhaust_gas_inlet_temp_c=315.0,
        economizer_inlet_temp_c=145.0,
        tsat_c=170.0,
    )
    res_normal = EgbCirculationDryRunEngine.evaluate(telem_normal)
    assert res_normal.status == EgbCirculationStatus.NORMAL
    assert res_normal.circulation_adequate is True
    assert res_normal.exhaust_diverter_bypass_trip is False

    # Standby pump cut-in on low dP (< 0.8 bar)
    telem_low_dp = EgbCirculationTelemetry(
        pump_diff_pressure_bar=0.6,
        water_flow_m3_h=10.0,
        standby_pump_available=True,
        loss_of_flow_duration_s=5.0,
        exhaust_gas_inlet_temp_c=320.0,
        economizer_inlet_temp_c=145.0,
        tsat_c=170.0,
    )
    res_low_dp = EgbCirculationDryRunEngine.evaluate(telem_low_dp)
    assert res_low_dp.status == EgbCirculationStatus.STANDBY_PUMP_CUT_IN
    assert res_low_dp.standby_pump_start_command is True
    assert res_low_dp.exhaust_diverter_bypass_trip is False

    # Dry-run trip: loss of flow > 15s -> bypass diverter damper tripped
    telem_dryrun = EgbCirculationTelemetry(
        pump_diff_pressure_bar=0.2,
        water_flow_m3_h=1.0,
        standby_pump_available=False,
        loss_of_flow_duration_s=18.0,
        exhaust_gas_inlet_temp_c=330.0,
        economizer_inlet_temp_c=150.0,
        tsat_c=170.0,
    )
    res_dryrun = EgbCirculationDryRunEngine.evaluate(telem_dryrun)
    assert res_dryrun.status == EgbCirculationStatus.DRY_RUN_DAMPER_BYPASS_TRIP
    assert res_dryrun.exhaust_diverter_bypass_trip is True
    assert res_dryrun.circulation_adequate is False


def test_phase_486_emergency_gen_blackout_behavior():
    # Cold standby when main bus is healthy
    telem_standby = EmergencyGenTelemetry(
        main_bus_voltage_pct=100.0,
        edg_frequency_hz=0.0,
        edg_voltage_v=0.0,
        blackout_elapsed_s=0.0,
        fuel_day_tank_hours=12.0,
        start_attempts_remaining=3,
        breaker_closed=False,
    )
    res_standby = EmergencyGenBlackoutEngine.evaluate(telem_standby)
    assert res_standby.status == EmergencyGenStatus.NORMAL
    assert res_standby.crank_start_command is False
    assert res_standby.fuel_endurance_ok is True

    # Blackout cranking active
    telem_crank = EmergencyGenTelemetry(
        main_bus_voltage_pct=0.0,
        edg_frequency_hz=45.0,
        edg_voltage_v=320.0,
        blackout_elapsed_s=12.0,
        fuel_day_tank_hours=10.0,
        start_attempts_remaining=2,
        breaker_closed=False,
    )
    res_crank = EmergencyGenBlackoutEngine.evaluate(telem_crank)
    assert res_crank.status == EmergencyGenStatus.BLACKOUT_CRANKING_ACTIVE
    assert res_crank.crank_start_command is True
    assert res_crank.breaker_close_permissive is False

    # Emergency power connected and energized
    telem_connected = EmergencyGenTelemetry(
        main_bus_voltage_pct=0.0,
        edg_frequency_hz=60.0,
        edg_voltage_v=440.0,
        blackout_elapsed_s=25.0,
        fuel_day_tank_hours=9.5,
        start_attempts_remaining=2,
        breaker_closed=True,
    )
    res_conn = EmergencyGenBlackoutEngine.evaluate(telem_connected)
    assert res_conn.status == EmergencyGenStatus.EMERGENCY_POWER_CONNECTED
    assert res_conn.emergency_power_restored is True
    assert res_conn.breaker_close_permissive is True

    # SOLAS limit exceeded (> 45s)
    telem_exceeded = EmergencyGenTelemetry(
        main_bus_voltage_pct=0.0,
        edg_frequency_hz=52.0,
        edg_voltage_v=390.0,
        blackout_elapsed_s=50.0,
        fuel_day_tank_hours=8.5,
        start_attempts_remaining=1,
        breaker_closed=False,
    )
    res_exceeded = EmergencyGenBlackoutEngine.evaluate(telem_exceeded)
    assert res_exceeded.status == EmergencyGenStatus.TAKEOVER_TIME_EXCEEDED

    # Pneumatic quick-closing valve trip interlock
    telem_qc = EmergencyGenTelemetry(
        main_bus_voltage_pct=0.0,
        edg_frequency_hz=0.0,
        edg_voltage_v=0.0,
        blackout_elapsed_s=5.0,
        fuel_day_tank_hours=10.0,
        start_attempts_remaining=3,
        breaker_closed=False,
        pneumatic_quick_closing_tripped=True,
    )
    res_qc = EmergencyGenBlackoutEngine.evaluate(telem_qc)
    assert res_qc.status == EmergencyGenStatus.PNEUMATIC_QC_TRIP
    assert res_qc.crank_start_command is False


def test_coordinator_batch6_engine_all_green_and_tripped():
    # All normal
    telem_ok = MaritimeAuxiliaryBatch6Telemetry(
        stp=StpAerationTelemetry(3.0, 0.35, True, True, 20.0, 0.0),
        bearing=BearingMistSlowdownTelemetry(65.0, 62.0, 3.0, 0.4, 2.2, 70.0),
        egb=EgbCirculationTelemetry(1.5, 22.0, True, 0.0, 300.0, 140.0, 170.0),
        edg=EmergencyGenTelemetry(100.0, 0.0, 0.0, 0.0, 10.0, 3, False),
    )
    res_ok = MaritimeSafetyAuxiliaryBatch6Engine.evaluate(telem_ok)
    assert res_ok.overall_safe is True
    assert res_ok.active_alarms_count == 0

    # With multiple alarms
    telem_alarmed = MaritimeAuxiliaryBatch6Telemetry(
        stp=StpAerationTelemetry(0.5, 0.35, True, True, 20.0, 0.0),  # Septic
        bearing=BearingMistSlowdownTelemetry(88.0, 62.0, 20.0, 0.4, 2.2, 70.0),  # Slowdown
        egb=EgbCirculationTelemetry(0.4, 8.0, True, 18.0, 300.0, 140.0, 170.0),  # Bypass trip
        edg=EmergencyGenTelemetry(0.0, 0.0, 0.0, 60.0, 1.0, 0, False),  # Over 45s / Lockout / Low fuel
    )
    res_alarmed = MaritimeSafetyAuxiliaryBatch6Engine.evaluate(telem_alarmed)
    assert res_alarmed.overall_safe is False
    assert res_alarmed.active_alarms_count >= 3


def test_cli_maritime_aux6_commands():
    runner = CliRunner()

    res1 = runner.invoke(maritime_aux6_app, ["stpaeration-check", "--do-mg-l", "2.5"])
    assert res1.exit_code == 0
    assert "normal" in res1.stdout

    res2 = runner.invoke(maritime_aux6_app, ["bearingmist-check", "--crosshead-c", "82.0"])
    assert res2.exit_code == 0
    assert "emergency_slowdown_trip" in res2.stdout

    res3 = runner.invoke(maritime_aux6_app, ["egbcirc-check", "--diff-p-bar", "1.5"])
    assert res3.exit_code == 0
    assert "normal" in res3.stdout

    res4 = runner.invoke(maritime_aux6_app, ["edgblackout-check", "--bus-pct", "0.0", "--elapsed-s", "10.0"])
    assert res4.exit_code == 0
    assert "blackout_cranking_active" in res4.stdout

