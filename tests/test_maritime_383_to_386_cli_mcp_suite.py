"""Integration tests for Maritime Phases 383-386 Facade, CLI & FastMCP tools.

Testing aggregated seaworthiness diagnosis, Typer commands, and FastMCP endpoints.
Zero mock dependencies.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_383_marine_fuel_purifier_clarifier import FuelPurifierInput
from src.core.maritime.phase_384_auxiliary_emergency_steering import SteeringGearInput
from src.core.maritime.phase_385_anti_heeling_ballast_pumping import AntiHeelingInput
from src.core.maritime.phase_386_tanker_pumproom_gas_sniffer import PumpRoomGasInput
from src.core.maritime_purifier_steering_heeling_sniffer_engine import (
    MaritimePurifierSteeringHeelingSnifferEngine,
)
from src.cli.commands.maritime_purifier_steering_heeling_sniffer_command import (
    purifier_app,
    steering_app,
    heeling_app,
    gas_app,
)
from scripts.mcp_server import (
    mekong_maritime_fuel_purifier_evaluate,
    mekong_maritime_emergency_steering_evaluate,
    mekong_maritime_anti_heeling_evaluate,
    mekong_maritime_pumproom_gas_evaluate,
)

runner = CliRunner()


def test_facade_fully_compliant():
    engine = MaritimePurifierSteeringHeelingSnifferEngine()
    res = engine.evaluate_all(
        FuelPurifierInput(vibration_velocity_rms_mm_s=2.5),
        SteeringGearInput(mode="MAIN", elapsed_time_s=24.0),
        AntiHeelingInput(current_heel_deg=0.1),
        PumpRoomGasInput(hydrocarbon_lel_pct=2.0, ventilation_ach=25.0),
    )
    assert res.overall_seaworthiness == "FULLY_COMPLIANT"
    assert len(res.all_warnings) == 0


def test_facade_non_compliant_due_to_gas_and_steering():
    engine = MaritimePurifierSteeringHeelingSnifferEngine()
    res = engine.evaluate_all(
        FuelPurifierInput(),
        SteeringGearInput(mode="MAIN", elapsed_time_s=35.0),
        AntiHeelingInput(),
        PumpRoomGasInput(hydrocarbon_lel_pct=25.0),
    )
    assert res.overall_seaworthiness == "NON_COMPLIANT"
    assert len(res.all_warnings) > 0


def test_cli_purifier_evaluate():
    result = runner.invoke(purifier_app, ["--flow", "3.0", "--rpm", "8500"])
    assert result.exit_code == 0
    assert "Centrifugal G-Force" in result.output
    assert "Purifier Status" in result.output


def test_cli_steering_evaluate():
    result = runner.invoke(steering_app, ["--mode", "MAIN", "--time", "22.5"])
    assert result.exit_code == 0
    assert "Travel Time Compliant" in result.output
    assert "Hydraulic Integrity" in result.output


def test_cli_anti_heeling_evaluate():
    result = runner.invoke(heeling_app, ["--heel", "1.2", "--disp", "85000"])
    assert result.exit_code == 0
    assert "Restoring Moment" in result.output
    assert "Target Pump Action" in result.output


def test_cli_pumproom_gas_evaluate():
    result = runner.invoke(gas_app, ["--lel", "3.0", "--h2s", "0.5"])
    assert result.exit_code == 0
    assert "Atmosphere Status" in result.output
    assert "Safe Entry Permitted" in result.output


@pytest.mark.asyncio
async def test_mcp_endpoints():
    p_res = await mekong_maritime_fuel_purifier_evaluate(flow_rate_m3_h=3.5)
    assert "g_force_factor" in p_res
    assert p_res["purifier_status"] == "OPTIMAL"

    s_res = await mekong_maritime_emergency_steering_evaluate(mode="MAIN", elapsed_time_s=24.0)
    assert s_res["travel_compliant"] is True

    h_res = await mekong_maritime_anti_heeling_evaluate(current_heel_deg=0.5)
    assert h_res["operational_status"] == "SAFE"

    g_res = await mekong_maritime_pumproom_gas_evaluate(hydrocarbon_lel_pct=3.0)
    assert g_res["entry_permitted"] is True
