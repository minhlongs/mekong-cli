"""Integration tests for Maritime Phases 387-390 Facade, CLI & FastMCP tools.

Testing aggregated seaworthiness diagnosis, Typer commands, and FastMCP endpoints.
Strictly zero mock dependencies.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_387_chilled_water_hvac_control import ChilledWaterHvacInput
from src.core.maritime.phase_388_food_waste_pulper_biodigestion import FoodWastePulperInput
from src.core.maritime.phase_389_cpp_pitch_hydraulic_load import CppPitchControlInput
from src.core.maritime.phase_390_cryogenic_tank_leak_insulation import CryogenicTankLeakInput
from src.core.maritime_chw_food_cpp_cryo_engine import MaritimeChwFoodCppCryoEngine
from src.cli.commands.maritime_chw_food_cpp_cryo_command import (
    hvac_app,
    food_app,
    cpp_app,
    cryo_app,
)
from scripts.mcp_server import (
    mekong_maritime_chilled_water_hvac_evaluate,
    mekong_maritime_food_waste_pulper_evaluate,
    mekong_maritime_cpp_pitch_control_evaluate,
    mekong_maritime_cryogenic_leak_sniff_evaluate,
)

runner = CliRunner()


def test_facade_nominal_optimal():
    engine = MaritimeChwFoodCppCryoEngine()
    res = engine.evaluate(
        ChilledWaterHvacInput(),
        FoodWastePulperInput(),
        CppPitchControlInput(),
        CryogenicTankLeakInput(),
    )
    assert res.overall_maritime_status == "NOMINAL_OPTIMAL"
    d = res.to_dict()
    assert d["overall_status"] == "NOMINAL_OPTIMAL"
    assert "cooling_capacity_kw" in d["hvac"]
    assert "comminution_compliant" in d["food_waste"]
    assert "hydraulic_status" in d["cpp_propeller"]
    assert "barrier_integrity" in d["cryogenic_tank"]


def test_facade_critical_hazard():
    engine = MaritimeChwFoodCppCryoEngine()
    res = engine.evaluate(
        ChilledWaterHvacInput(refrigerant_concentration_ppm=150.0),
        FoodWastePulperInput(),
        CppPitchControlInput(hydraulic_pressure_bar=20.0),
        CryogenicTankLeakInput(methane_concentration_vol_pct=3.0),
    )
    assert res.overall_maritime_status == "CRITICAL_HAZARD"
    assert res.hvac_result.compressor_trip is True
    assert res.cryo_leak_result.cargo_tank_safety_status == "CRITICAL_EMERGENCY"


def test_cli_hvac_evaluate():
    result = runner.invoke(hvac_app, ["--flow-m3-h", "70.0", "--t-supply", "6.5"])
    assert result.exit_code == 0
    assert "Cooling Capacity" in result.output
    assert "Sweat Hazard" in result.output


def test_cli_food_waste_evaluate():
    result = runner.invoke(food_app, ["--particle-mm", "15.0"])
    assert result.exit_code == 0
    assert "Comminution Compliant" in result.output
    assert "MARPOL Annex" in result.output


def test_cli_cpp_evaluate():
    result = runner.invoke(cpp_app, ["--commanded-pitch", "22.0"])
    assert result.exit_code == 0
    assert "Hydraulic Servo Status" in result.output
    assert "DNV-RU-SHIP" in result.output


def test_cli_cryo_evaluate():
    result = runner.invoke(cryo_app, ["--ch4-vol-pct", "0.08"])
    assert result.exit_code == 0
    assert "Barrier Integrity" in result.output
    assert "IMO IGC Code" in result.output


@pytest.mark.asyncio
async def test_fastmcp_endpoints_evaluation():
    hvac_res = await mekong_maritime_chilled_water_hvac_evaluate(flow_m3_h=65.0)
    assert hvac_res["chiller_status"] == "OPTIMAL"
    assert hvac_res["cop_actual"] > 3.0

    food_res = await mekong_maritime_food_waste_pulper_evaluate(particle_mm=16.0)
    assert food_res["comminution_compliant"] is True
    assert food_res["discharge_permitted"] is True

    cpp_res = await mekong_maritime_cpp_pitch_control_evaluate(commanded_pitch=20.0)
    assert cpp_res["hydraulic_status"] == "NORMAL"
    assert cpp_res["seal_barrier_intact"] is True

    cryo_res = await mekong_maritime_cryogenic_leak_sniff_evaluate(ch4_vol_pct=0.05)
    assert cryo_res["barrier_integrity"] == "INTACT"
    assert cryo_res["cargo_tank_safety_status"] == "SAFE"
