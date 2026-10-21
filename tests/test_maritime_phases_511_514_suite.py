"""Pytest test suite for Maritime Safety Automation Batch 13 (Phases 511-514).
Covers Scavenge Air Condensate, Medical Oxygen Manifold, Mooring Winch Brake, and Water-Mist.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_511_scavenge_air_condensate_drain import (
    ScavengeAirCondensateDrainEngine, ScavengeCondensateState, ScavengeCondensateTelemetry,
)
from src.core.maritime.phase_512_medical_oxygen_manifold_safety import (
    MedicalGasState, MedicalOxygenManifoldSafetyEngine, MedicalOxygenTelemetry,
)
from src.core.maritime.phase_513_mooring_winch_brake_render import (
    MooringBrakeStatus, MooringWinchBrakeRenderEngine, MooringWinchTelemetry,
)
from src.core.maritime.phase_514_water_mist_local_application import (
    WaterMistLocalApplicationEngine, WaterMistSystemState, WaterMistTelemetry,
)
from src.core.maritime_safety_auxiliary_batch13_engine import (
    MaritimeSafetyAuxiliaryBatch13Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch13_command import maritime_aux13_app

runner = CliRunner()


def test_phase_511_scavenge_air_condensate_drain() -> None:
    res_norm = ScavengeAirCondensateDrainEngine.evaluate(
        ScavengeCondensateTelemetry(scavenge_air_temp_c=44.0, compressed_dewpoint_c=36.0, drain_pot_level_pct=25.0)
    )
    assert res_norm.condensate_state == ScavengeCondensateState.OPTIMAL_DRY_SCAVENGE
    assert res_norm.cylinder_oil_feed_boost is False
    assert res_norm.alarm_active is False

    res_choked = ScavengeAirCondensateDrainEngine.evaluate(
        ScavengeCondensateTelemetry(scavenge_air_temp_c=42.0, compressed_dewpoint_c=36.0, drain_pot_level_pct=88.0)
    )
    assert res_choked.condensate_state == ScavengeCondensateState.DRAIN_TRAP_BLOCKED_HIGH_LEVEL
    assert res_choked.bypass_drain_valve_open is True
    assert res_choked.cylinder_oil_feed_boost is True

    res_cold = ScavengeAirCondensateDrainEngine.evaluate(
        ScavengeCondensateTelemetry(scavenge_air_temp_c=36.5, compressed_dewpoint_c=36.0, drain_pot_level_pct=30.0)
    )
    assert res_cold.condensate_state == ScavengeCondensateState.UNDERCOOLING_LINER_WASH_RISK
    assert res_cold.cylinder_oil_feed_boost is True


def test_phase_512_medical_oxygen_manifold_safety() -> None:
    res_norm = MedicalOxygenManifoldSafetyEngine.evaluate(
        MedicalOxygenTelemetry(duty_cylinder_bar=120.0, delivery_line_bar=4.5, locker_ambient_o2_pct=20.9)
    )
    assert res_norm.gas_state == MedicalGasState.DUTY_BANK_SUPPLYING
    assert res_norm.reserve_bank_engaged is False

    res_change = MedicalOxygenManifoldSafetyEngine.evaluate(
        MedicalOxygenTelemetry(duty_cylinder_bar=28.0, delivery_line_bar=4.3, locker_ambient_o2_pct=20.9)
    )
    assert res_change.gas_state == MedicalGasState.RESERVE_BANK_AUTO_CHANGEOVER
    assert res_change.reserve_bank_engaged is True

    res_leak = MedicalOxygenManifoldSafetyEngine.evaluate(
        MedicalOxygenTelemetry(duty_cylinder_bar=100.0, delivery_line_bar=4.2, locker_ambient_o2_pct=24.2)
    )
    assert res_leak.gas_state == MedicalGasState.LOCKER_O2_ENRICHMENT_SHUTOFF
    assert res_leak.manifold_isolation_tripped is True


def test_phase_513_mooring_winch_brake_render() -> None:
    res_norm = MooringWinchBrakeRenderEngine.evaluate(
        MooringWinchTelemetry(line_tension_pct_mbl=35.0, brake_setpoint_pct_mbl=60.0)
    )
    assert res_norm.brake_status == MooringBrakeStatus.SAFE_HOLDING_TENSION
    assert res_norm.meg4_compliant is True
    assert res_norm.drum_rendering_active is False

    res_render = MooringWinchBrakeRenderEngine.evaluate(
        MooringWinchTelemetry(line_tension_pct_mbl=62.5, brake_setpoint_pct_mbl=60.0)
    )
    assert res_render.brake_status == MooringBrakeStatus.BRAKE_RENDERING_PAYOUT
    assert res_render.drum_rendering_active is True

    res_meg4 = MooringWinchBrakeRenderEngine.evaluate(
        MooringWinchTelemetry(line_tension_pct_mbl=40.0, brake_setpoint_pct_mbl=85.0)
    )
    assert res_meg4.brake_status == MooringBrakeStatus.MEG4_OVER_HOLDING_CAP_VIOLATION
    assert res_meg4.meg4_compliant is False


def test_phase_514_water_mist_local_application() -> None:
    res_standby = WaterMistLocalApplicationEngine.evaluate(
        WaterMistTelemetry(flame_detector_active=False, smoke_heat_detector_active=False)
    )
    assert res_standby.system_state == WaterMistSystemState.STANDBY_MONITORING
    assert res_standby.section_valve_open is False

    res_single = WaterMistLocalApplicationEngine.evaluate(
        WaterMistTelemetry(flame_detector_active=True, smoke_heat_detector_active=False)
    )
    assert res_single.system_state == WaterMistSystemState.SINGLE_SENSOR_PRE_ALARM
    assert res_single.section_valve_open is False

    res_coinc = WaterMistLocalApplicationEngine.evaluate(
        WaterMistTelemetry(flame_detector_active=True, smoke_heat_detector_active=True, pump_discharge_bar=92.0)
    )
    assert res_coinc.system_state == WaterMistSystemState.LOCAL_SECTION_MIST_DISCHARGING
    assert res_coinc.section_valve_open is True
    assert res_coinc.high_pressure_pump_running is True


def test_maritime_auxiliary_batch13_coordinator() -> None:
    scav = ScavengeCondensateTelemetry(scavenge_air_temp_c=44.0, compressed_dewpoint_c=36.0, drain_pot_level_pct=20.0)
    med = MedicalOxygenTelemetry(duty_cylinder_bar=115.0, delivery_line_bar=4.5)
    mooring = MooringWinchTelemetry(line_tension_pct_mbl=30.0)
    mist = WaterMistTelemetry(flame_detector_active=False, smoke_heat_detector_active=False)

    res = MaritimeSafetyAuxiliaryBatch13Engine.evaluate_batch13(scav, med, mooring, mist)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch13_cli() -> None:
    res1 = runner.invoke(maritime_aux13_app, ["scavdrain-check", "--air-c", "44.0"])
    assert res1.exit_code == 0
    assert "OPTIMAL_DRY_SCAVENGE" in res1.stdout

    res2 = runner.invoke(maritime_aux13_app, ["medo2-check", "--duty-bar", "110.0"])
    assert res2.exit_code == 0
    assert "DUTY_BANK_SUPPLYING" in res2.stdout

    res3 = runner.invoke(maritime_aux13_app, ["mooring-check", "--tension-pct", "32.0"])
    assert res3.exit_code == 0
    assert "SAFE_HOLDING_TENSION" in res3.stdout

    res4 = runner.invoke(maritime_aux13_app, ["watermist-check"])
    assert res4.exit_code == 0
    assert "STANDBY_MONITORING" in res4.stdout
