"""Pytest test suite for Maritime Safety Automation Batch 10 (Phases 499-502).
Covers Turbocharger Surge, Fresh Water Generator, CO2 Flooding Interlock, and Fuel Viscometer.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_499_turbocharger_overspeed_surge import (
    TurbochargerOverspeedSurgeEngine, TurbochargerStatus, TurbochargerTelemetry,
)
from src.core.maritime.phase_500_fresh_water_generator_salinity import (
    FreshWaterGeneratorSalinityEngine, FwgDistributionState, FwgTelemetry,
)
from src.core.maritime.phase_501_co2_total_flooding_interlock import (
    Co2FloodingTelemetry, Co2ReleaseStatus, Co2TotalFloodingInterlockEngine,
)
from src.core.maritime.phase_502_fuel_oil_viscometer_heater import (
    FuelOilViscometerHeaterEngine, FuelViscometerTelemetry, ViscometerControlState,
)
from src.core.maritime_safety_auxiliary_batch10_engine import (
    MaritimeSafetyAuxiliaryBatch10Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch10_command import maritime_aux10_app

runner = CliRunner()


def test_phase_499_turbocharger_overspeed_surge() -> None:
    res_norm = TurbochargerOverspeedSurgeEngine.evaluate(
        TurbochargerTelemetry(rotor_rpm=15500.0, lube_oil_inlet_bar=1.6, exhaust_inlet_temp_c=450.0, surge_pulses_per_min=0)
    )
    assert res_norm.status == TurbochargerStatus.NORMAL_OPERATION
    assert res_norm.slowdown_requested is False
    assert res_norm.alarm_active is False

    res_trip = TurbochargerOverspeedSurgeEngine.evaluate(
        TurbochargerTelemetry(rotor_rpm=19800.0, lube_oil_inlet_bar=1.5, exhaust_inlet_temp_c=500.0)
    )
    assert res_trip.status == TurbochargerStatus.EMERGENCY_SLOWDOWN_TRIP
    assert res_trip.slowdown_requested is True
    assert res_trip.wastegate_bypass_open is True

    res_surge = TurbochargerOverspeedSurgeEngine.evaluate(
        TurbochargerTelemetry(rotor_rpm=16000.0, lube_oil_inlet_bar=1.5, exhaust_inlet_temp_c=480.0, surge_pulses_per_min=4)
    )
    assert res_surge.status == TurbochargerStatus.COMPRESSOR_SURGE_BYPASS
    assert res_surge.wastegate_bypass_open is True


def test_phase_500_fresh_water_generator_salinity() -> None:
    res_norm = FreshWaterGeneratorSalinityEngine.evaluate(
        FwgTelemetry(shell_vacuum_bar=-0.90, ejector_water_pressure_bar=2.8, distillate_salinity_ppm=1.8)
    )
    assert res_norm.distribution_state == FwgDistributionState.POTABLE_TANK_FILLING
    assert res_norm.potable_water_compliant is True
    assert res_norm.dump_valve_diverted_to_bilge is False

    res_saline = FreshWaterGeneratorSalinityEngine.evaluate(
        FwgTelemetry(shell_vacuum_bar=-0.88, ejector_water_pressure_bar=2.7, distillate_salinity_ppm=14.5)
    )
    assert res_saline.distribution_state == FwgDistributionState.BILGE_DUMP_HIGH_SALINITY
    assert res_saline.dump_valve_diverted_to_bilge is True
    assert res_saline.potable_water_compliant is False

    res_ejector = FreshWaterGeneratorSalinityEngine.evaluate(
        FwgTelemetry(shell_vacuum_bar=-0.85, ejector_water_pressure_bar=1.8, distillate_salinity_ppm=2.0)
    )
    assert res_ejector.distribution_state == FwgDistributionState.EJECTOR_FAULT_SHUTDOWN


def test_phase_501_co2_total_flooding_interlock() -> None:
    res_standby = Co2TotalFloodingInterlockEngine.evaluate(
        Co2FloodingTelemetry(cabinet_door_opened=False, pre_discharge_delay_sec=0.0, ventilation_fans_tripped=False, fire_dampers_closed=False)
    )
    assert res_standby.release_status == Co2ReleaseStatus.STANDBY_ARMED
    assert res_standby.main_manifold_valve_open is False

    res_blocked = Co2TotalFloodingInterlockEngine.evaluate(
        Co2FloodingTelemetry(cabinet_door_opened=True, pre_discharge_delay_sec=25.0, ventilation_fans_tripped=True, fire_dampers_closed=False)
    )
    assert res_blocked.release_status == Co2ReleaseStatus.INTERLOCK_BLOCKED
    assert res_blocked.main_manifold_valve_open is False

    res_delay = Co2TotalFloodingInterlockEngine.evaluate(
        Co2FloodingTelemetry(cabinet_door_opened=True, pre_discharge_delay_sec=12.0, ventilation_fans_tripped=True, fire_dampers_closed=True)
    )
    assert res_delay.release_status == Co2ReleaseStatus.PRE_DISCHARGE_ALARM_DELAY
    assert res_delay.main_manifold_valve_open is False

    res_rel = Co2TotalFloodingInterlockEngine.evaluate(
        Co2FloodingTelemetry(cabinet_door_opened=True, pre_discharge_delay_sec=22.0, ventilation_fans_tripped=True, fire_dampers_closed=True)
    )
    assert res_rel.release_status == Co2ReleaseStatus.MASTER_FLOODING_RELEASED
    assert res_rel.main_manifold_valve_open is True


def test_phase_502_fuel_oil_viscometer_heater() -> None:
    res_norm = FuelOilViscometerHeaterEngine.evaluate(
        FuelViscometerTelemetry(viscosity_cst=13.5, fuel_temp_c=130.0, temp_ramp_c_per_min=0.5, steam_valve_opening_pct=50.0)
    )
    assert res_norm.control_state == ViscometerControlState.OPTIMAL_INJECTION_VISCOSITY
    assert res_norm.plunger_seizure_risk is False

    res_ramp = FuelOilViscometerHeaterEngine.evaluate(
        FuelViscometerTelemetry(viscosity_cst=14.0, fuel_temp_c=110.0, temp_ramp_c_per_min=3.2, steam_valve_opening_pct=60.0)
    )
    assert res_ramp.control_state == ViscometerControlState.THERMAL_RAMP_RATE_EXCEEDED
    assert res_ramp.plunger_seizure_risk is True

    res_high = FuelOilViscometerHeaterEngine.evaluate(
        FuelViscometerTelemetry(viscosity_cst=21.0, fuel_temp_c=115.0, temp_ramp_c_per_min=1.0, steam_valve_opening_pct=45.0)
    )
    assert res_high.control_state == ViscometerControlState.HIGH_VISCOSITY_BOOST_STEAM
    assert res_high.recommended_steam_valve_pct == 70.0


def test_maritime_auxiliary_batch10_coordinator() -> None:
    tc = TurbochargerTelemetry(rotor_rpm=15000.0, lube_oil_inlet_bar=1.6, exhaust_inlet_temp_c=440.0)
    fwg = FwgTelemetry(shell_vacuum_bar=-0.90, ejector_water_pressure_bar=2.8, distillate_salinity_ppm=1.5)
    co2 = Co2FloodingTelemetry(cabinet_door_opened=False, pre_discharge_delay_sec=0.0, ventilation_fans_tripped=False, fire_dampers_closed=False)
    visc = FuelViscometerTelemetry(viscosity_cst=13.2, fuel_temp_c=126.0, temp_ramp_c_per_min=0.4)

    res = MaritimeSafetyAuxiliaryBatch10Engine.evaluate_batch10(tc, fwg, co2, visc)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch10_cli() -> None:
    res1 = runner.invoke(maritime_aux10_app, ["tc-check", "--rpm", "15200.0"])
    assert res1.exit_code == 0
    assert "NORMAL_OPERATION" in res1.stdout

    res2 = runner.invoke(maritime_aux10_app, ["fwg-check", "--salinity-ppm", "1.4"])
    assert res2.exit_code == 0
    assert "POTABLE_TANK_FILLING" in res2.stdout

    res3 = runner.invoke(maritime_aux10_app, ["co2-check"])
    assert res3.exit_code == 0
    assert "STANDBY_ARMED" in res3.stdout

    res4 = runner.invoke(maritime_aux10_app, ["visc-check", "--viscosity-cst", "13.5"])
    assert res4.exit_code == 0
    assert "OPTIMAL_INJECTION_VISCOSITY" in res4.stdout
