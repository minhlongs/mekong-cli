"""Zero-mock Pytest Suite for Maritime Automation Phases 487-490 (Batch 7).

Covers:
- Phase 487: Main Engine Jacket Cooling Water Temperature & Flow Protection
- Phase 488: Inert Gas System (IGS) Deck Water Seal Level & Non-Return Protection
- Phase 489: Central Cooling System 3-Way Mixing Valve & SW Head
- Phase 490: Starting Air Compressor Unloader & Receiver Pressure Safety
- Coordinator: MaritimeSafetyAuxiliaryBatch7Engine
- CLI Commands via Typer CliRunner: maritime_aux7_app
"""

from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch7_command import maritime_aux7_app
from src.core.maritime.phase_487_jacket_cooling_temp_flow import (
    JacketCoolingStatus,
    JacketCoolingTelemetry,
    JacketCoolingTempFlowEngine,
)
from src.core.maritime.phase_488_deck_water_seal_level import (
    DeckWaterSealLevelEngine,
    DeckWaterSealStatus,
    DeckWaterSealTelemetry,
)
from src.core.maritime.phase_489_central_cooling_3way_valve import (
    CentralCooling3WayValveEngine,
    CentralCoolingStatus,
    CentralCoolingTelemetry,
)
from src.core.maritime.phase_490_starting_air_compressor_unloader import (
    StartingAirCompressorUnloaderEngine,
    StartingAirStatus,
    StartingAirTelemetry,
)
from src.core.maritime_safety_auxiliary_batch7_engine import (
    MaritimeAuxiliaryBatch7Telemetry,
    MaritimeSafetyAuxiliaryBatch7Engine,
)


def test_phase_487_jacket_cooling_temp_flow_boundaries():
    # Nominal
    telem_normal = JacketCoolingTelemetry(
        outlet_temp_c=84.0,
        inlet_temp_c=74.0,
        engine_block_diff_pressure_bar=1.1,
        expansion_tank_level_pct=60.0,
        preheater_pump_available=True,
    )
    res_normal = JacketCoolingTempFlowEngine.evaluate(telem_normal)
    assert res_normal.status == JacketCoolingStatus.NORMAL
    assert res_normal.cooling_adequate is True
    assert res_normal.slowdown_trip_command is False

    # Overheat slowdown trip (outlet >= 92 C)
    telem_overheat = JacketCoolingTelemetry(
        outlet_temp_c=93.5,
        inlet_temp_c=78.0,
        engine_block_diff_pressure_bar=1.0,
        expansion_tank_level_pct=55.0,
        preheater_pump_available=True,
    )
    res_overheat = JacketCoolingTempFlowEngine.evaluate(telem_overheat)
    assert res_overheat.status == JacketCoolingStatus.HIGH_TEMP_SLOWDOWN_TRIP
    assert res_overheat.slowdown_trip_command is True

    # Low flow dP trip (< 0.6 bar)
    telem_low_flow = JacketCoolingTelemetry(
        outlet_temp_c=86.0,
        inlet_temp_c=74.0,
        engine_block_diff_pressure_bar=0.45,
        expansion_tank_level_pct=55.0,
        preheater_pump_available=True,
    )
    res_flow = JacketCoolingTempFlowEngine.evaluate(telem_low_flow)
    assert res_flow.status == JacketCoolingStatus.LOW_FLOW_DP_TRIP
    assert res_flow.slowdown_trip_command is True

    # Expansion tank low-low trip (< 15%)
    telem_tank = JacketCoolingTelemetry(
        outlet_temp_c=82.0,
        inlet_temp_c=70.0,
        engine_block_diff_pressure_bar=1.0,
        expansion_tank_level_pct=12.0,
        preheater_pump_available=True,
    )
    res_tank = JacketCoolingTempFlowEngine.evaluate(telem_tank)
    assert res_tank.status == JacketCoolingStatus.EXPANSION_TANK_LOW_LOW_TRIP
    assert res_tank.slowdown_trip_command is True


def test_phase_488_deck_water_seal_safety_matrix():
    # Nominal
    telem_normal = DeckWaterSealTelemetry(
        water_column_height_mm=520.0,
        ambient_temp_c=18.0,
        downstream_pressure_mbar=15.0,
        inlet_supply_pressure_mbar=22.0,
        refill_valve_currently_open=False,
    )
    res_normal = DeckWaterSealLevelEngine.evaluate(telem_normal)
    assert res_normal.status == DeckWaterSealStatus.NORMAL
    assert res_normal.seal_integrity_safe is True
    assert res_normal.supply_valve_locked is False

    # Gas backflow trip (downstream > inlet and height < 300 mm)
    telem_backflow = DeckWaterSealTelemetry(
        water_column_height_mm=250.0,
        ambient_temp_c=15.0,
        downstream_pressure_mbar=30.0,
        inlet_supply_pressure_mbar=10.0,
        refill_valve_currently_open=False,
    )
    res_back = DeckWaterSealLevelEngine.evaluate(telem_backflow)
    assert res_back.status == DeckWaterSealStatus.GAS_BACKFLOW_TRIP
    assert res_back.gas_backflow_trip is True
    assert res_back.supply_valve_locked is True

    # Low level valve lock (< 450 mm)
    telem_low = DeckWaterSealTelemetry(
        water_column_height_mm=420.0,
        ambient_temp_c=15.0,
        downstream_pressure_mbar=15.0,
        inlet_supply_pressure_mbar=20.0,
        refill_valve_currently_open=False,
    )
    res_low = DeckWaterSealLevelEngine.evaluate(telem_low)
    assert res_low.status == DeckWaterSealStatus.LOW_LEVEL_VALVE_LOCK
    assert res_low.low_level_alarm is True

    # Trace heating active (< 5 C)
    telem_freeze = DeckWaterSealTelemetry(
        water_column_height_mm=510.0,
        ambient_temp_c=2.0,
        downstream_pressure_mbar=15.0,
        inlet_supply_pressure_mbar=20.0,
        refill_valve_currently_open=False,
    )
    res_freeze = DeckWaterSealLevelEngine.evaluate(telem_freeze)
    assert res_freeze.status == DeckWaterSealStatus.TRACE_HEATING_ACTIVE
    assert res_freeze.trace_heating_active is True


def test_phase_489_central_cooling_3way_valve():
    # Nominal
    telem_normal = CentralCoolingTelemetry(
        lt_freshwater_temp_c=36.0,
        ht_jacket_water_temp_c=85.0,
        seawater_pump_diff_pressure_bar=1.6,
        standby_sw_pump_available=True,
        ht_target_setpoint_c=85.0,
    )
    res_normal = CentralCooling3WayValveEngine.evaluate(telem_normal)
    assert res_normal.status == CentralCoolingStatus.NORMAL
    assert res_normal.cooling_loop_balanced is True
    assert res_normal.ht_bypass_valve_pct == 50.0

    # Standby SW pump cut-in (< 1.0 bar)
    telem_sw_cutin = CentralCoolingTelemetry(
        lt_freshwater_temp_c=36.0,
        ht_jacket_water_temp_c=85.0,
        seawater_pump_diff_pressure_bar=0.8,
        standby_sw_pump_available=True,
        ht_target_setpoint_c=85.0,
    )
    res_cutin = CentralCooling3WayValveEngine.evaluate(telem_sw_cutin)
    assert res_cutin.status == CentralCoolingStatus.STANDBY_SW_PUMP_CUT_IN
    assert res_cutin.standby_sw_pump_command is True

    # LT temp deviation > 1.5 C
    telem_lt_dev = CentralCoolingTelemetry(
        lt_freshwater_temp_c=39.0,
        ht_jacket_water_temp_c=85.0,
        seawater_pump_diff_pressure_bar=1.5,
        standby_sw_pump_available=True,
        ht_target_setpoint_c=85.0,
    )
    res_lt = CentralCooling3WayValveEngine.evaluate(telem_lt_dev)
    assert res_lt.status == CentralCoolingStatus.LT_TEMP_OUT_OF_SPEC
    assert res_lt.cooling_loop_balanced is False


def test_phase_490_starting_air_compressor():
    # Normal compression charging
    telem_charge = StartingAirTelemetry(
        receiver_pressure_bar=24.0,
        high_stage_discharge_temp_c=120.0,
        compressor_running=True,
        unloader_purge_elapsed_s=8.0,
    )
    res_charge = StartingAirCompressorUnloaderEngine.evaluate(telem_charge)
    assert res_charge.status == StartingAirStatus.COMPRESSION_CHARGING
    assert res_charge.motor_start_command is True

    # Purge unloader starting
    telem_purge = StartingAirTelemetry(
        receiver_pressure_bar=23.0,
        high_stage_discharge_temp_c=90.0,
        compressor_running=True,
        unloader_purge_elapsed_s=2.0,
    )
    res_purge = StartingAirCompressorUnloaderEngine.evaluate(telem_purge)
    assert res_purge.status == StartingAirStatus.PURGE_UNLOADER_RUNNING
    assert res_purge.unloader_purge_solenoid_open is True

    # High discharge temp trip (> 160 C)
    telem_temp = StartingAirTelemetry(
        receiver_pressure_bar=26.0,
        high_stage_discharge_temp_c=168.0,
        compressor_running=True,
        unloader_purge_elapsed_s=10.0,
    )
    res_temp = StartingAirCompressorUnloaderEngine.evaluate(telem_temp)
    assert res_temp.status == StartingAirStatus.HIGH_DISCHARGE_TEMP_TRIP
    assert res_temp.trip_lockout is True

    # Safety relief valve lift (>= 31.5 bar)
    telem_relief = StartingAirTelemetry(
        receiver_pressure_bar=32.0,
        high_stage_discharge_temp_c=130.0,
        compressor_running=True,
        unloader_purge_elapsed_s=10.0,
    )
    res_relief = StartingAirCompressorUnloaderEngine.evaluate(telem_relief)
    assert res_relief.status == StartingAirStatus.SAFETY_VALVE_LIFT_TRIP
    assert res_relief.safety_relief_lifted is True


def test_coordinator_batch7_engine_overall():
    telem_ok = MaritimeAuxiliaryBatch7Telemetry(
        jacket=JacketCoolingTelemetry(84.0, 72.0, 1.2, 65.0, True),
        deck_seal=DeckWaterSealTelemetry(500.0, 18.0, 15.0, 20.0, False),
        central_cooling=CentralCoolingTelemetry(36.0, 85.0, 1.6, True, 85.0),
        starting_air=StartingAirTelemetry(30.0, 110.0, False, 10.0, False),
    )
    res_ok = MaritimeSafetyAuxiliaryBatch7Engine.evaluate(telem_ok)
    assert res_ok.overall_safe is True
    assert res_ok.active_alarms_count == 0

    telem_alarmed = MaritimeAuxiliaryBatch7Telemetry(
        jacket=JacketCoolingTelemetry(94.0, 72.0, 0.4, 10.0, True),
        deck_seal=DeckWaterSealTelemetry(200.0, 1.0, 35.0, 10.0, False),
        central_cooling=CentralCoolingTelemetry(40.0, 85.0, 0.6, True, 85.0),
        starting_air=StartingAirTelemetry(32.5, 175.0, True, 10.0, False),
    )
    res_alarmed = MaritimeSafetyAuxiliaryBatch7Engine.evaluate(telem_alarmed)
    assert res_alarmed.overall_safe is False
    assert res_alarmed.active_alarms_count >= 3


def test_cli_maritime_aux7_commands():
    runner = CliRunner()

    res1 = runner.invoke(maritime_aux7_app, ["jacketcooling-check", "--outlet-c", "84.0"])
    assert res1.exit_code == 0
    assert "normal" in res1.stdout

    res2 = runner.invoke(maritime_aux7_app, ["deckseal-check", "--height-mm", "520.0"])
    assert res2.exit_code == 0
    assert "normal" in res2.stdout

    res3 = runner.invoke(maritime_aux7_app, ["centralcooling-check", "--lt-temp-c", "36.0"])
    assert res3.exit_code == 0
    assert "normal" in res3.stdout

    res4 = runner.invoke(maritime_aux7_app, ["startingair-check", "--p-bar", "24.0", "--purge-s", "8.0"])
    assert res4.exit_code == 0
    assert "compression_charging" in res4.stdout
