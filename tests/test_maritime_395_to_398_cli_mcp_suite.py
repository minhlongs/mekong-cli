"""Integration tests for Maritime Phases 395-398 Facade, Typer CLI & FastMCP tools.

Strictly < 200 LOC, zero mocks.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_395_emergency_fire_pump_sea_suction import EmergencyFirePumpInput
from src.core.maritime.phase_396_steering_gear_dual_hydraulic import SteeringGearInput
from src.core.maritime.phase_397_quick_closing_valve_emergency_shutoff import QuickClosingValveInput
from src.core.maritime.phase_398_scavenge_air_fire_detection import ScavengeFireInput
from src.core.maritime_firepump_steering_qcvalve_scavenge_engine import (
    MaritimeSafetyPropulsionControlEngine,
)
from src.cli.commands.maritime_firepump_steering_qcvalve_scavenge_command import (
    firepump_app,
    steering_app,
    qcvalve_app,
    scavenge_app,
)
from scripts.mcp_server import (
    mekong_maritime_emergency_fire_pump_evaluate,
    mekong_maritime_quick_closing_valves_evaluate,
    mekong_maritime_scavenge_air_fire_evaluate,
    mekong_maritime_steering_gear_dual_evaluate,
)

runner = CliRunner()


def test_facade_nominal_optimal():
    engine = MaritimeSafetyPropulsionControlEngine()
    res = engine.evaluate(
        EmergencyFirePumpInput(),
        SteeringGearInput(),
        QuickClosingValveInput(),
        ScavengeFireInput(),
    )
    assert res.overall_maritime_safety_status == "SEAWORTHY_NOMINAL_OPTIMAL"
    d = res.to_dict()
    assert d["overall_status"] == "SEAWORTHY_NOMINAL_OPTIMAL"
    assert d["emergency_fire_pump"]["flow_compliant"] is True
    assert d["steering_gear"]["redundancy_active"] is True
    assert d["quick_closing_valves"]["completeness_pct"] == 100.0
    assert d["scavenge_air_fire"]["hazard_status"] == "NORMAL_CLEAR"


def test_facade_critical_hazard():
    engine = MaritimeSafetyPropulsionControlEngine()
    res = engine.evaluate(
        EmergencyFirePumpInput(discharge_pressure_bar=1.5),
        SteeringGearInput(pump_1_operational=False, pump_2_operational=False),
        QuickClosingValveInput(valves_tripped_count=2, valves_total_count=6),
        ScavengeFireInput(max_under_piston_temp_c=210.0),
    )
    assert res.overall_maritime_safety_status == "CRITICAL_MARITIME_HAZARD"
    assert len(res.aggregated_warnings) >= 4


def test_cli_fire_pump():
    result = runner.invoke(firepump_app, ["--flow-m3-h", "40.0", "--pressure-bar", "3.5"])
    assert result.exit_code == 0
    assert "Discharge Capacity OK" in result.output
    assert "Hose Jets Supported" in result.output


def test_cli_steering_gear():
    result = runner.invoke(steering_app, ["--transit-sec", "21.0"])
    assert result.exit_code == 0
    assert "Main Gear Speed (<=28s)" in result.output
    assert "Dual Redundancy Active" in result.output


def test_cli_quick_closing_valves():
    result = runner.invoke(qcvalve_app, ["--air-bar", "6.8"])
    assert result.exit_code == 0
    assert "Control Air OK" in result.output
    assert "Completeness" in result.output


def test_cli_scavenge_fire():
    result = runner.invoke(scavenge_app, ["--piston-temp-c", "88.0"])
    assert result.exit_code == 0
    assert "Hazard Status" in result.output
    assert "Under-Piston Temp OK" in result.output


@pytest.mark.asyncio
async def test_mcp_endpoints_phases_395_398():
    mcp_pump = await mekong_maritime_emergency_fire_pump_evaluate(flow_m3_h=32.0)
    assert mcp_pump["discharge_capacity_compliant"] is True

    mcp_steer = await mekong_maritime_steering_gear_dual_evaluate(transit_sec=24.0)
    assert mcp_steer["main_gear_speed_compliant"] is True

    mcp_qc = await mekong_maritime_quick_closing_valves_evaluate(tripped=6, total=6)
    assert mcp_qc["closure_completeness_pct"] == 100.0

    mcp_scav = await mekong_maritime_scavenge_air_fire_evaluate(piston_temp_c=78.0)
    assert mcp_scav["fire_hazard_status"] == "NORMAL_CLEAR"
