"""Tests for Maritime Automation Safety Phases 479-482 Suite.

Covers:
- Phase 479: Cargo Hold Bilge Eductor & Flooding Detection Interlock (SOLAS XII/9, IACS UR S24)
- Phase 480: Turbocharger Auxiliary Blower & Surge Protection (IACS UR M9)
- Phase 481: Boiler Feedwater Deaerator & Condensate Salinity Engine (IACS UR M14)
- Phase 482: Steering Gear Phase Failure & Hydraulic Auto-Isolation (SOLAS II-1/29)
- Master MaritimeSafetyAuxiliaryBatch5Engine Coordinator
- CLI commands via CliRunner: cargoholdbilge-check, auxblower-check, boilerfeed-check, steeringgear-check

Zero mocks, strictly deterministic rules.
"""

from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch5_command import maritime_aux5_app
from src.core.maritime.phase_479_cargo_hold_bilge_eductor import (
    CargoHoldBilgeEductorEngine,
    CargoHoldBilgeStatus,
    CargoHoldBilgeTelemetry,
)
from src.core.maritime.phase_480_turbocharger_aux_blower import (
    AuxBlowerStatus,
    AuxBlowerTelemetry,
    TurbochargerAuxBlowerEngine,
)
from src.core.maritime.phase_481_boiler_feedwater_deaerator import (
    BoilerFeedwaterDeaeratorEngine,
    BoilerFeedwaterStatus,
    BoilerFeedwaterTelemetry,
)
from src.core.maritime.phase_482_steering_gear_phase_failure import (
    SteeringGearSafetyEngine,
    SteeringGearStatus,
    SteeringGearTelemetry,
)
from src.core.maritime_safety_auxiliary_batch5_engine import (
    MaritimePhases479to482Telemetry,
    MaritimeSafetyAuxiliaryBatch5Engine,
)


def test_phase_479_cargo_hold_bilge_eductor():
    # Nominal condition
    t_nom = CargoHoldBilgeTelemetry(water_level_m=0.2, driving_pressure_bar=5.0, backpressure_bar=1.0, backflow_check_ok=True)
    res_nom = CargoHoldBilgeEductorEngine.evaluate(t_nom)
    assert res_nom.status == CargoHoldBilgeStatus.NORMAL
    assert res_nom.eductor_permissive is True
    assert not res_nom.flooding_alarm_active
    assert not res_nom.pre_alarm_active

    # Pre-alarm condition (0.5m <= level < 2.0m)
    t_pre = CargoHoldBilgeTelemetry(water_level_m=0.8, driving_pressure_bar=5.0, backpressure_bar=1.0, backflow_check_ok=True)
    res_pre = CargoHoldBilgeEductorEngine.evaluate(t_pre)
    assert res_pre.status == CargoHoldBilgeStatus.PRE_ALARM
    assert res_pre.pre_alarm_active is True
    assert not res_pre.flooding_alarm_active
    assert res_pre.eductor_permissive is True

    # Flooding alarm condition (level >= 2.0m)
    t_flood = CargoHoldBilgeTelemetry(water_level_m=2.4, driving_pressure_bar=5.0, backpressure_bar=1.0, backflow_check_ok=True)
    res_flood = CargoHoldBilgeEductorEngine.evaluate(t_flood)
    assert res_flood.status == CargoHoldBilgeStatus.FLOODING_ALARM
    assert res_flood.flooding_alarm_active is True
    assert res_flood.pre_alarm_active is True

    # Backflow check failed
    t_backflow = CargoHoldBilgeTelemetry(water_level_m=0.3, driving_pressure_bar=5.0, backpressure_bar=1.0, backflow_check_ok=False)
    res_backflow = CargoHoldBilgeEductorEngine.evaluate(t_backflow)
    assert res_backflow.status == CargoHoldBilgeStatus.BACKFLOW_RISK_INHIBIT
    assert res_backflow.eductor_permissive is False

    # Low driving pressure (< 4.5 bar)
    t_low_p = CargoHoldBilgeTelemetry(water_level_m=0.3, driving_pressure_bar=4.0, backpressure_bar=1.0, backflow_check_ok=True)
    res_low_p = CargoHoldBilgeEductorEngine.evaluate(t_low_p)
    assert res_low_p.status == CargoHoldBilgeStatus.INSUFFICIENT_DRIVING_PRESSURE
    assert res_low_p.eductor_permissive is False

    # Low differential pressure (< 0.8 bar)
    t_low_dp = CargoHoldBilgeTelemetry(water_level_m=0.3, driving_pressure_bar=4.8, backpressure_bar=4.3, backflow_check_ok=True)
    res_low_dp = CargoHoldBilgeEductorEngine.evaluate(t_low_dp)
    assert res_low_dp.status == CargoHoldBilgeStatus.INSUFFICIENT_DRIVING_PRESSURE
    assert res_low_dp.eductor_permissive is False


def test_phase_480_turbocharger_aux_blower():
    # Engine stopped
    t_stop = AuxBlowerTelemetry(scavenge_pressure_bar=0.0, dp_dt_bar_s=0.0, blower_running=False, engine_running=False)
    res_stop = TurbochargerAuxBlowerEngine.evaluate(t_stop)
    assert res_stop.status == AuxBlowerStatus.ENGINE_STOPPED
    assert not res_stop.blower_start_command

    # TC Surge detected (dp/dt <= -0.25 bar/s)
    t_surge = AuxBlowerTelemetry(scavenge_pressure_bar=0.90, dp_dt_bar_s=-0.30, blower_running=False, engine_running=True)
    res_surge = TurbochargerAuxBlowerEngine.evaluate(t_surge)
    assert res_surge.status == AuxBlowerStatus.TC_SURGE_RELIEF_ACTIVE
    assert res_surge.surge_relief_bypass_open is True
    assert res_surge.blower_start_command is True

    # Low scavenge cut-in demand (< 0.85 bar)
    t_cutin = AuxBlowerTelemetry(scavenge_pressure_bar=0.75, dp_dt_bar_s=0.0, blower_running=False, engine_running=True)
    res_cutin = TurbochargerAuxBlowerEngine.evaluate(t_cutin)
    assert res_cutin.status == AuxBlowerStatus.AUX_BLOWER_CUT_IN_DEMAND
    assert res_cutin.blower_start_command is True
    assert not res_cutin.surge_relief_bypass_open

    # Scavenge cut-out (>= 1.15 bar)
    t_cutout = AuxBlowerTelemetry(scavenge_pressure_bar=1.20, dp_dt_bar_s=0.05, blower_running=True, engine_running=True)
    res_cutout = TurbochargerAuxBlowerEngine.evaluate(t_cutout)
    assert res_cutout.status == AuxBlowerStatus.NORMAL_TC_ONLY
    assert res_cutout.blower_stop_command is True

    # Intermediate band [0.85, 1.15)
    t_mid = AuxBlowerTelemetry(scavenge_pressure_bar=1.0, dp_dt_bar_s=0.0, blower_running=True, engine_running=True)
    res_mid = TurbochargerAuxBlowerEngine.evaluate(t_mid)
    assert res_mid.status == AuxBlowerStatus.AUX_BLOWER_RUNNING
    assert res_mid.blower_start_command is True


def test_phase_481_boiler_feedwater_deaerator():
    # Nominal
    t_nom = BoilerFeedwaterTelemetry(condensate_conductivity_us_cm=3.0, deaerator_pressure_bar=0.30, tsat_c=107.0, tactual_c=106.0)
    res_nom = BoilerFeedwaterDeaeratorEngine.evaluate(t_nom)
    assert res_nom.status == BoilerFeedwaterStatus.NORMAL
    assert not res_nom.condensate_dump_valve_open
    assert not res_nom.salinity_alarm
    assert res_nom.deaerator_pressure_normal
    assert res_nom.deaeration_saturation_ok

    # Salinity alarm (5.0 < conductivity <= 10.0)
    t_sal = BoilerFeedwaterTelemetry(condensate_conductivity_us_cm=7.5, deaerator_pressure_bar=0.30, tsat_c=107.0, tactual_c=106.0)
    res_sal = BoilerFeedwaterDeaeratorEngine.evaluate(t_sal)
    assert res_sal.status == BoilerFeedwaterStatus.SALINITY_HIGH_ALARM
    assert res_sal.salinity_alarm is True
    assert not res_sal.condensate_dump_valve_open

    # Salinity dump to bilge (conductivity > 10.0)
    t_dump = BoilerFeedwaterTelemetry(condensate_conductivity_us_cm=14.2, deaerator_pressure_bar=0.30, tsat_c=107.0, tactual_c=106.0)
    res_dump = BoilerFeedwaterDeaeratorEngine.evaluate(t_dump)
    assert res_dump.status == BoilerFeedwaterStatus.CONDENSATE_DUMP_TO_BILGE
    assert res_dump.condensate_dump_valve_open is True
    assert res_dump.salinity_alarm is True

    # Deaerator pressure out of range (< 0.20 or > 0.45)
    t_p_low = BoilerFeedwaterTelemetry(condensate_conductivity_us_cm=2.0, deaerator_pressure_bar=0.15, tsat_c=107.0, tactual_c=106.0)
    res_p_low = BoilerFeedwaterDeaeratorEngine.evaluate(t_p_low)
    assert res_p_low.status == BoilerFeedwaterStatus.DEAERATOR_PRESSURE_OUT_OF_RANGE
    assert not res_p_low.deaerator_pressure_normal

    # Incomplete deaeration margin (> 1.5 C)
    t_incomp = BoilerFeedwaterTelemetry(condensate_conductivity_us_cm=2.0, deaerator_pressure_bar=0.35, tsat_c=107.0, tactual_c=104.5)
    res_incomp = BoilerFeedwaterDeaeratorEngine.evaluate(t_incomp)
    assert res_incomp.status == BoilerFeedwaterStatus.INSUFFICIENT_DEAERATION_MARGIN
    assert not res_incomp.deaeration_saturation_ok


def test_phase_482_steering_gear_phase_failure():
    # Nominal
    t_nom = SteeringGearTelemetry(reservoir_level_pct=80.0, phase_imbalance_pct=3.0, phase_loss=False, standby_pressure_bar=0.0, standby_elapsed_s=0.0)
    res_nom = SteeringGearSafetyEngine.evaluate(t_nom)
    assert res_nom.status == SteeringGearStatus.NORMAL
    assert not res_nom.auto_isolate_unit
    assert not res_nom.phase_failure_alarm
    assert res_nom.steering_capable is True

    # Low reservoir auto-isolate (< 35%)
    t_res = SteeringGearTelemetry(reservoir_level_pct=28.0, phase_imbalance_pct=2.0, phase_loss=False, standby_pressure_bar=0.0, standby_elapsed_s=5.0)
    res_res = SteeringGearSafetyEngine.evaluate(t_res)
    assert res_res.status == SteeringGearStatus.RESERVOIR_LOW_AUTO_ISOLATE
    assert res_res.auto_isolate_unit is True
    assert res_res.standby_auto_start_command is True

    # Phase failure (imbalance > 10% or phase loss) auto-start standby
    t_pf = SteeringGearTelemetry(reservoir_level_pct=80.0, phase_imbalance_pct=15.0, phase_loss=False, standby_pressure_bar=40.0, standby_elapsed_s=10.0)
    res_pf = SteeringGearSafetyEngine.evaluate(t_pf)
    assert res_pf.status == SteeringGearStatus.PHASE_FAILURE_STANDBY_START
    assert res_pf.phase_failure_alarm is True
    assert res_pf.standby_auto_start_command is True

    # Standby reached pressure (>= 160 bar)
    t_standby_ok = SteeringGearTelemetry(reservoir_level_pct=80.0, phase_imbalance_pct=15.0, phase_loss=False, standby_pressure_bar=165.0, standby_elapsed_s=25.0)
    res_standby_ok = SteeringGearSafetyEngine.evaluate(t_standby_ok)
    assert res_standby_ok.status == SteeringGearStatus.STANDBY_PRESSURE_REACHED
    assert res_standby_ok.steering_capable is True

    # Standby failed to pressurize (> 45s and < 160 bar)
    t_standby_fail = SteeringGearTelemetry(reservoir_level_pct=80.0, phase_imbalance_pct=15.0, phase_loss=False, standby_pressure_bar=110.0, standby_elapsed_s=48.0)
    res_standby_fail = SteeringGearSafetyEngine.evaluate(t_standby_fail)
    assert res_standby_fail.status == SteeringGearStatus.STANDBY_FAILED_TO_PRESSURIZE
    assert res_standby_fail.steering_capable is False


def test_maritime_safety_auxiliary_batch5_coordinator():
    telemetry = MaritimePhases479to482Telemetry(
        cargo_hold_bilge=CargoHoldBilgeTelemetry(0.2, 5.0, 1.0, True),
        aux_blower=AuxBlowerTelemetry(1.25, 0.0, False, True),
        boiler_feedwater=BoilerFeedwaterTelemetry(2.5, 0.30, 107.0, 106.0),
        steering_gear=SteeringGearTelemetry(85.0, 2.0, False, 0.0, 0.0),
    )
    res = MaritimeSafetyAuxiliaryBatch5Engine.evaluate(telemetry)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0

    # Test with alarms
    telemetry_alarm = MaritimePhases479to482Telemetry(
        cargo_hold_bilge=CargoHoldBilgeTelemetry(2.5, 5.0, 1.0, True),  # Flooding alarm
        aux_blower=AuxBlowerTelemetry(0.9, -0.3, False, True),          # Surge active
        boiler_feedwater=BoilerFeedwaterTelemetry(12.0, 0.30, 107.0, 106.0),  # Dump to bilge
        steering_gear=SteeringGearTelemetry(20.0, 2.0, False, 0.0, 50.0),    # Auto-isolate & unpressurized
    )
    res_alarm = MaritimeSafetyAuxiliaryBatch5Engine.evaluate(telemetry_alarm)
    assert res_alarm.overall_safe is False
    assert res_alarm.active_alarms_count == 4


def test_batch5_cli_commands():
    runner = CliRunner()

    res1 = runner.invoke(maritime_aux5_app, ["cargoholdbilge-check", "--water-level-m", "0.2"])
    assert res1.exit_code == 0
    assert "NORMAL" in res1.output

    res2 = runner.invoke(maritime_aux5_app, ["auxblower-check", "--scavenge-p-bar", "1.25"])
    assert res2.exit_code == 0
    assert "NORMAL_TC_ONLY" in res2.output

    res3 = runner.invoke(maritime_aux5_app, ["boilerfeed-check", "--conductivity-us-cm", "2.0"])
    assert res3.exit_code == 0
    assert "NORMAL" in res3.output

    res4 = runner.invoke(maritime_aux5_app, ["steeringgear-check", "--reservoir-pct", "80.0"])
    assert res4.exit_code == 0
    assert "NORMAL" in res4.output
