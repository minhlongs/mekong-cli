"""Pytest test suite for Maritime Safety Automation Batch 9 (Phases 495-498).
Covers OWS 15ppm, Crankcase OMD, Boiler Water Level, and Emergency Fire Pump.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_495_ows_15ppm_bilge_alarm import (
    Ows15PpmBilgeAlarmEngine, OwsTelemetry, ValveRouting,
)
from src.core.maritime.phase_496_crankcase_oil_mist_detector import (
    CrankcaseOilMistDetectorEngine, EngineSafeties, OilMistTelemetry,
)
from src.core.maritime.phase_497_boiler_water_level_fuel_cutoff import (
    BoilerWaterLevelFuelCutoffEngine, BoilerWaterTelemetry, BurnerState,
)
from src.core.maritime.phase_498_emergency_fire_pump_priming import (
    EmergencyFirePumpPrimingEngine, FirePumpStatus, FirePumpTelemetry,
)
from src.core.maritime_safety_auxiliary_batch9_engine import (
    MaritimeSafetyAuxiliaryBatch9Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch9_command import maritime_aux9_app

runner = CliRunner()

def test_phase_495_ows_15ppm_bilge_alarm():
    # Normal compliant overboard discharge
    res_norm = Ows15PpmBilgeAlarmEngine.evaluate(
        OwsTelemetry(oil_content_ppm=8.5, sample_flow_l_per_min=1.2)
    )
    assert res_norm.valve_routing == ValveRouting.OVERBOARD
    assert res_norm.overboard_allowed is True
    assert res_norm.alarm_active is False

    # High oil content > 15 ppm
    res_high = Ows15PpmBilgeAlarmEngine.evaluate(
        OwsTelemetry(oil_content_ppm=18.0, sample_flow_l_per_min=1.2)
    )
    assert res_high.valve_routing == ValveRouting.RECIRC_TO_BILGE_TANK
    assert res_high.overboard_allowed is False
    assert res_high.alarm_active is True

    # Sample flow loss
    res_loss = Ows15PpmBilgeAlarmEngine.evaluate(
        OwsTelemetry(oil_content_ppm=5.0, sample_flow_l_per_min=0.2)
    )
    assert res_loss.valve_routing == ValveRouting.RECIRC_TO_BILGE_TANK
    assert res_loss.alarm_active is True

def test_phase_496_crankcase_oil_mist_detector():
    # Normal opacity
    res_norm = CrankcaseOilMistDetectorEngine.evaluate(
        OilMistTelemetry(mist_opacity_pct=0.4, fan_differential_pa=180.0)
    )
    assert res_norm.engine_command == EngineSafeties.NORMAL
    assert res_norm.alarm_active is False

    # Slowdown threshold >= 2.0%
    res_slow = CrankcaseOilMistDetectorEngine.evaluate(
        OilMistTelemetry(mist_opacity_pct=2.4, fan_differential_pa=180.0)
    )
    assert res_slow.engine_command == EngineSafeties.SLOWDOWN_REQUESTED
    assert res_slow.explosion_risk_critical is True

    # Flame arrester ruptured
    res_flame = CrankcaseOilMistDetectorEngine.evaluate(
        OilMistTelemetry(mist_opacity_pct=0.5, fan_differential_pa=180.0, flame_arrester_intact=False)
    )
    assert res_flame.engine_command == EngineSafeties.EMERGENCY_STOP_REQUESTED

def test_phase_497_boiler_water_level_fuel_cutoff():
    # Normal operating level
    res_norm = BoilerWaterLevelFuelCutoffEngine.evaluate(
        BoilerWaterTelemetry(water_level_mm=10.0)
    )
    assert res_norm.burner_state == BurnerState.FIRING_ALLOWED
    assert res_norm.alarm_active is False

    # Low level alarm
    res_low = BoilerWaterLevelFuelCutoffEngine.evaluate(
        BoilerWaterTelemetry(water_level_mm=-80.0)
    )
    assert res_low.burner_state == BurnerState.FIRING_ALLOWED
    assert res_low.alarm_active is True
    assert res_low.feedwater_boost_required is True

    # Critical low-low water level trip
    res_trip = BoilerWaterLevelFuelCutoffEngine.evaluate(
        BoilerWaterTelemetry(water_level_mm=-130.0)
    )
    assert res_trip.burner_state == BurnerState.SAFETY_SHUTOFF_TRIPPED
    assert res_trip.alarm_active is True

def test_phase_498_emergency_fire_pump_priming():
    # Fully pressurized main
    res_norm = EmergencyFirePumpPrimingEngine.evaluate(
        FirePumpTelemetry(suction_valve_open=True, suction_vacuum_bar=-0.45, discharge_pressure_bar=3.2, priming_elapsed_sec=12.0)
    )
    assert res_norm.pump_status == FirePumpStatus.DELIVERING_PRESSURE
    assert res_norm.fire_main_pressurized is True

    # Priming timeout exceeded
    res_timeout = EmergencyFirePumpPrimingEngine.evaluate(
        FirePumpTelemetry(suction_valve_open=True, suction_vacuum_bar=-0.20, discharge_pressure_bar=0.5, priming_elapsed_sec=35.0)
    )
    assert res_timeout.pump_status == FirePumpStatus.PRIMING_FAILURE_TRIP
    assert res_timeout.standby_ejector_command is True

def test_maritime_auxiliary_batch9_coordinator():
    ows = OwsTelemetry(oil_content_ppm=5.0, sample_flow_l_per_min=1.0)
    omd = OilMistTelemetry(mist_opacity_pct=0.5, fan_differential_pa=150.0)
    boiler = BoilerWaterTelemetry(water_level_mm=0.0)
    fire = FirePumpTelemetry(suction_valve_open=True, suction_vacuum_bar=-0.45, discharge_pressure_bar=3.0, priming_elapsed_sec=8.0)

    res = MaritimeSafetyAuxiliaryBatch9Engine.evaluate_batch9(ows, omd, boiler, fire)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0

def test_maritime_auxiliary_batch9_cli():
    res1 = runner.invoke(maritime_aux9_app, ["ows-check", "--ppm", "10.0"])
    assert res1.exit_code == 0
    assert "OVERBOARD" in res1.stdout

    res2 = runner.invoke(maritime_aux9_app, ["omd-check", "--opacity", "0.2"])
    assert res2.exit_code == 0
    assert "NORMAL" in res2.stdout

    res3 = runner.invoke(maritime_aux9_app, ["boiler-check", "--level-mm", "5.0"])
    assert res3.exit_code == 0
    assert "FIRING_ALLOWED" in res3.stdout

    res4 = runner.invoke(maritime_aux9_app, ["firepump-check", "--discharge-bar", "3.0"])
    assert res4.exit_code == 0
    assert "DELIVERING_PRESSURE" in res4.stdout
