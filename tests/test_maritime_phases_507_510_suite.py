"""Pytest test suite for Maritime Safety Automation Batch 12 (Phases 507-510).
Covers Shaft Grounding, Emergency Bilge Suction, Watertight Doors, and Helideck Foam.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_507_shaft_grounding_slip_ring import (
    ShaftGroundingSlipRingEngine, ShaftGroundingState, ShaftGroundingTelemetry,
)
from src.core.maritime.phase_508_emergency_bilge_direct_suction import (
    BilgeFloodState, EmergencyBilgeDirectSuctionEngine, EmergencyBilgeTelemetry,
)
from src.core.maritime.phase_509_watertight_sliding_door_safety import (
    WatertightDoorStatus, WatertightDoorTelemetry, WatertightSlidingDoorSafetyEngine,
)
from src.core.maritime.phase_510_helideck_foam_monitor_system import (
    HelideckFoamMonitorSystemEngine, HelideckFoamStatus, HelideckFoamTelemetry,
)
from src.core.maritime_safety_auxiliary_batch12_engine import (
    MaritimeSafetyAuxiliaryBatch12Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch12_command import maritime_aux12_app

runner = CliRunner()


def test_phase_507_shaft_grounding_slip_ring() -> None:
    res_norm = ShaftGroundingSlipRingEngine.evaluate(
        ShaftGroundingTelemetry(shaft_potential_mv=25.0, grounding_current_ma=40.0, brush_wear_pct=20.0)
    )
    assert res_norm.grounding_state == ShaftGroundingState.OPTIMAL_EARTHING
    assert res_norm.bearing_pitting_risk is False
    assert res_norm.alarm_active is False

    res_spark = ShaftGroundingSlipRingEngine.evaluate(
        ShaftGroundingTelemetry(shaft_potential_mv=115.0, grounding_current_ma=12.0, brush_wear_pct=50.0)
    )
    assert res_spark.grounding_state == ShaftGroundingState.SPARK_EROSION_CRITICAL_ALARM
    assert res_spark.bearing_pitting_risk is True
    assert res_spark.alarm_active is True

    res_open = ShaftGroundingSlipRingEngine.evaluate(
        ShaftGroundingTelemetry(shaft_potential_mv=85.0, grounding_current_ma=0.0, brush_wear_pct=90.0)
    )
    assert res_open.grounding_state == ShaftGroundingState.OPEN_CIRCUIT_BRUSH_LIFTED


def test_phase_508_emergency_bilge_direct_suction() -> None:
    res_dry = EmergencyBilgeDirectSuctionEngine.evaluate(
        EmergencyBilgeTelemetry(well_water_level_mm=50.0)
    )
    assert res_dry.flood_state == BilgeFloodState.DRY_WELL_STANDBY
    assert res_dry.bilge_pump_start_cmd is False

    res_high = EmergencyBilgeDirectSuctionEngine.evaluate(
        EmergencyBilgeTelemetry(well_water_level_mm=420.0)
    )
    assert res_high.flood_state == BilgeFloodState.HIGH_LEVEL_FLOODING_ALARM
    assert res_high.bilge_pump_start_cmd is True
    assert res_high.emergency_direct_suction_open is False

    res_emerg = EmergencyBilgeDirectSuctionEngine.evaluate(
        EmergencyBilgeTelemetry(well_water_level_mm=680.0, main_sw_pump_running=True)
    )
    assert res_emerg.flood_state == BilgeFloodState.EMERGENCY_DIRECT_SUCTION_ACTIVE
    assert res_emerg.emergency_direct_suction_open is True


def test_phase_509_watertight_sliding_door_safety() -> None:
    res_closed = WatertightSlidingDoorSafetyEngine.evaluate(
        WatertightDoorTelemetry(bridge_master_close_cmd=True, door_fully_closed=True, accumulator_pressure_bar=175.0, closing_duration_sec=28.0)
    )
    assert res_closed.door_status == WatertightDoorStatus.CLOSED_AND_DOG_LOCKED
    assert res_closed.solas_3_closures_ready is True
    assert res_closed.alarm_active is False

    res_pinch = WatertightSlidingDoorSafetyEngine.evaluate(
        WatertightDoorTelemetry(bridge_master_close_cmd=True, door_fully_closed=False, accumulator_pressure_bar=170.0, pinch_strip_obstructed=True)
    )
    assert res_pinch.door_status == WatertightDoorStatus.OBSTRUCTION_REOPEN_PAUSE
    assert res_pinch.alarm_active is True

    res_speed = WatertightSlidingDoorSafetyEngine.evaluate(
        WatertightDoorTelemetry(bridge_master_close_cmd=True, door_fully_closed=True, accumulator_pressure_bar=165.0, closing_duration_sec=14.0)
    )
    assert res_speed.door_status == WatertightDoorStatus.CLOSING_SPEED_OUT_OF_SPEC


def test_phase_510_helideck_foam_monitor_system() -> None:
    res_standby = HelideckFoamMonitorSystemEngine.evaluate(
        HelideckFoamTelemetry(release_activated=False, nozzle_manifold_bar=0.0, afff_induction_ratio_pct=3.0, foam_tank_level_pct=96.0)
    )
    assert res_standby.foam_status == HelideckFoamStatus.STANDBY_READY
    assert res_standby.cap437_compliant is True

    res_disch = HelideckFoamMonitorSystemEngine.evaluate(
        HelideckFoamTelemetry(release_activated=True, nozzle_manifold_bar=8.5, afff_induction_ratio_pct=3.1, foam_tank_level_pct=92.0)
    )
    assert res_disch.foam_status == HelideckFoamStatus.DISCHARGING_COMPLIANT_FOAM
    assert res_disch.pop_up_nozzles_deployed is True
    assert res_disch.cap437_compliant is True

    res_ratio = HelideckFoamMonitorSystemEngine.evaluate(
        HelideckFoamTelemetry(release_activated=True, nozzle_manifold_bar=8.0, afff_induction_ratio_pct=1.8, foam_tank_level_pct=90.0)
    )
    assert res_ratio.foam_status == HelideckFoamStatus.PROPORTIONER_RATIO_FAULT
    assert res_ratio.cap437_compliant is False


def test_maritime_auxiliary_batch12_coordinator() -> None:
    shaft = ShaftGroundingTelemetry(shaft_potential_mv=20.0, grounding_current_ma=35.0)
    bilge = EmergencyBilgeTelemetry(well_water_level_mm=60.0)
    door = WatertightDoorTelemetry(bridge_master_close_cmd=True, door_fully_closed=True, accumulator_pressure_bar=175.0)
    heli = HelideckFoamTelemetry(release_activated=False, nozzle_manifold_bar=0.0, afff_induction_ratio_pct=3.0)

    res = MaritimeSafetyAuxiliaryBatch12Engine.evaluate_batch12(shaft, bilge, door, heli)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch12_cli() -> None:
    res1 = runner.invoke(maritime_aux12_app, ["shaft-check", "--potential-mv", "20.0"])
    assert res1.exit_code == 0
    assert "OPTIMAL_EARTHING" in res1.stdout

    res2 = runner.invoke(maritime_aux12_app, ["bilge-check", "--level-mm", "60.0"])
    assert res2.exit_code == 0
    assert "DRY_WELL_STANDBY" in res2.stdout

    res3 = runner.invoke(maritime_aux12_app, ["wtd-check", "--acc-bar", "175.0"])
    assert res3.exit_code == 0
    assert "CLOSED_AND_DOG_LOCKED" in res3.stdout

    res4 = runner.invoke(maritime_aux12_app, ["helideck-check", "--tank-pct", "95.0"])
    assert res4.exit_code == 0
    assert "STANDBY_READY" in res4.stdout
