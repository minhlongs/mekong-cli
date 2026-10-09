"""Deterministic zero-mock test suite for Maritime Phases 407-410.

Validates:
- Phase 407 Marine EGB Economizer & Soot Blow (SOLAS II-2 Reg 4 / DNV Pt.4)
- Phase 408 Marine Shaft Earthing & Hull Galvanic Potential (DNV-RP-B401 / ISO 15541)
- Phase 409 Bulk Cargo Hold Dew Point & Hold Ventilation (IMSBC Code / IMO MSC.268(85))
- Phase 410 Emergency Diesel Generator 45s Blackout Sequence (SOLAS II-1 Reg 42/43)
- Maritime Auxiliary Safety Unified Facade Engine
- CLI Typer command execution & FastMCP server tools
Strictly < 180 LOC, zero mocks.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_407_egb_economizer_soot_blow import (
    EgbEconomizerEngine,
    EgbEconomizerInput,
    EgbEconomizerStatus,
)
from src.core.maritime.phase_408_shaft_earthing_galvanic import (
    ShaftEarthingEngine,
    ShaftEarthingInput,
    ShaftEarthingStatus,
)
from src.core.maritime.phase_409_cargo_dewpoint_ventilation import (
    HoldPsychrometricInput,
    HoldVentilationEngine,
    HoldVentilationStatus,
)
from src.core.maritime.phase_410_emergency_generator_blackout import (
    EdgBlackoutEngine,
    EdgBlackoutInput,
    EdgBlackoutStatus,
)
from src.core.maritime_auxiliary_safety_engine import (
    MaritimeAuxiliarySafetyEngine,
)
from src.cli.commands.maritime_egb_shaft_hold_edg_command import (
    edgblackout_app,
    egb_app,
    holdvent_app,
    shaftearth_app,
)
from scripts.mcp_server import (
    mekong_maritime_auxiliary_safety_evaluate,
    mekong_maritime_cargo_hold_vent_evaluate,
    mekong_maritime_edg_blackout_evaluate,
    mekong_maritime_egb_economizer_evaluate,
    mekong_maritime_shaft_earthing_evaluate,
)

runner = CliRunner()


def test_phase_407_egb_economizer_evaluations():
    engine = EgbEconomizerEngine()
    nominal = engine.evaluate(EgbEconomizerInput())
    assert nominal.status == EgbEconomizerStatus.NORMAL_HEAT_RECOVERY
    assert nominal.soot_blow_permitted is True
    assert nominal.soot_fire_risk_detected is False

    # Fouling requiring soot blow
    fouled = engine.evaluate(EgbEconomizerInput(gas_differential_pressure_mmwc=52.0))
    assert fouled.status == EgbEconomizerStatus.SOOT_CLEANING_REQUIRED
    assert fouled.soot_blow_recommended is True

    # Critical soot fire trip
    fire = engine.evaluate(EgbEconomizerInput(flue_gas_outlet_temp_c=235.0))
    assert fire.status == EgbEconomizerStatus.SOOT_FIRE_HAZARD_TRIP
    assert fire.soot_fire_risk_detected is True


def test_phase_408_shaft_earthing_evaluations():
    engine = ShaftEarthingEngine()
    nominal = engine.evaluate(ShaftEarthingInput())
    assert nominal.status == ShaftEarthingStatus.OPTIMAL_PROTECTION
    assert nominal.bearing_spark_erosion_risk is False

    # Spark erosion critical trip (> 100 mV)
    spark = engine.evaluate(ShaftEarthingInput(shaft_voltage_mv=115.0))
    assert spark.status == ShaftEarthingStatus.SPARK_EROSION_CRITICAL
    assert spark.bearing_spark_erosion_risk is True

    # Hull underprotection
    under = engine.evaluate(ShaftEarthingInput(reference_electrode_mv=-720.0))
    assert under.status == ShaftEarthingStatus.HULL_UNDER_PROTECTED


def test_phase_409_cargo_dewpoint_ventilation():
    engine = HoldVentilationEngine()
    # Dew point calculation check
    dp = engine.calculate_dew_point(20.0, 50.0)
    assert 8.0 <= dp <= 10.5

    # Cargo sweat: Outside DP > Cargo temp -> Prohibited
    sweat = engine.evaluate(HoldPsychrometricInput(outside_temp_c=25.0, outside_relative_humidity_pct=90.0, cargo_surface_temp_c=18.0))
    assert sweat.status == HoldVentilationStatus.VENTILATION_PROHIBITED
    assert sweat.cargo_sweat_risk is True

    # Normal nominal
    nominal = engine.evaluate(HoldPsychrometricInput(hold_temp_c=20.0, hold_relative_humidity_pct=40.0, deckhead_hull_temp_c=18.0))
    assert nominal.cargo_sweat_risk is False


def test_phase_410_edg_blackout_sequence():
    engine = EdgBlackoutEngine()
    # Nominal dead ship restore within 18.5 seconds
    res = engine.evaluate(EdgBlackoutInput(msb_voltage_volts=0.0, blackout_elapsed_sec=18.5))
    assert res.status == EdgBlackoutStatus.EMERGENCY_BUS_CONNECTED
    assert res.solas_45s_compliant is True

    # SOLAS violation: 55 seconds elapsed without breaker closure
    over = engine.evaluate(EdgBlackoutInput(msb_voltage_volts=0.0, blackout_elapsed_sec=55.0, esb_breaker_closed=False))
    assert over.status == EdgBlackoutStatus.OVER_TIME_SOLAS_VIOLATION
    assert over.solas_45s_compliant is False

    # Low air/battery energy lockout
    low_e = engine.evaluate(EdgBlackoutInput(starting_air_pressure_bar=12.0, starter_battery_volts=20.5))
    assert low_e.status == EdgBlackoutStatus.LOW_STARTING_ENERGY_LOCKOUT


def test_unified_auxiliary_safety_facade():
    engine = MaritimeAuxiliarySafetyEngine()
    res = engine.evaluate(
        EgbEconomizerInput(),
        ShaftEarthingInput(),
        HoldPsychrometricInput(),
        EdgBlackoutInput(msb_voltage_volts=440.0),
    )
    assert res.all_systems_green is True
    assert res.overall_safety_status == "ALL_AUXILIARY_SAFETY_SYSTEMS_OPTIMAL"
    d = res.to_dict()
    assert d["all_systems_green"] is True
    assert "edg_blackout" in d


def test_maritime_407_to_410_typer_cli_commands():
    r_egb = runner.invoke(egb_app, ["--engine-load", "80.0"])
    assert r_egb.exit_code == 0
    assert "EGB Economizer & Soot Blow" in r_egb.stdout

    r_shaft = runner.invoke(shaftearth_app, ["--shaft-mv", "22.0"])
    assert r_shaft.exit_code == 0
    assert "Shaft Earthing" in r_shaft.stdout

    r_hold = runner.invoke(holdvent_app, ["--hold-temp", "24.0"])
    assert r_hold.exit_code == 0
    assert "Cargo Hold Dew Point Ventilation" in r_hold.stdout

    r_edg = runner.invoke(edgblackout_app, ["--msb-v", "0.0"])
    assert r_edg.exit_code == 0
    assert "EDG 45s Blackout Sequence" in r_edg.stdout


@pytest.mark.asyncio
async def test_maritime_407_to_410_fastmcp_tools():
    egb = await mekong_maritime_egb_economizer_evaluate()
    assert egb["status"] == "NORMAL_HEAT_RECOVERY"

    shaft = await mekong_maritime_shaft_earthing_evaluate()
    assert shaft["shaft_voltage_safe"] is True

    hold = await mekong_maritime_cargo_hold_vent_evaluate()
    assert "hold_dew_point_c" in hold

    edg = await mekong_maritime_edg_blackout_evaluate()
    assert edg["solas_45s_compliant"] is True

    facade = await mekong_maritime_auxiliary_safety_evaluate()
    assert "overall_status" in facade
