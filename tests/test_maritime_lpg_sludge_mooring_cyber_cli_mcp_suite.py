"""CLI and FastMCP integration test suite for Maritime Phases 355-358.

Strictly kept under 200 lines. Tests Typer CLI commands, Vietnamese aliases, and MCP tools.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime_lpg_sludge_mooring_cyber_engine import (
    MaritimeLpgSludgeMooringCyberFacade,
    LpgReliquefactionInput,
    SludgeIncineratorInput,
    SmartMooringInput,
    MaritimeCyberInput,
)

runner = CliRunner()
app = build_app()


def test_cli_lpg_commands_en_and_vi():
    # English command
    res_en = runner.invoke(app, ["lpgreliq", "evaluate", "--cargo", "PROPANE", "--heat-leak", "180.0"])
    assert res_en.exit_code == 0
    assert "LPG Reliquefaction Result" in res_en.stdout
    assert "BOG Rate" in res_en.stdout

    # Vietnamese alias
    res_vi = runner.invoke(app, ["hoalonglpg", "evaluate", "--cargo", "BUTANE", "--heat-leak", "200.0"])
    assert res_vi.exit_code == 0
    assert "LPG Reliquefaction Result" in res_vi.stdout


def test_cli_sludge_commands_en_and_vi():
    # English command
    res_en = runner.invoke(app, ["sludgeburn", "evaluate", "--hfo-m3", "40.0", "--prim-temp", "880.0"])
    assert res_en.exit_code == 0
    assert "Sludge & Incinerator Result" in res_en.stdout
    assert "Est Daily Sludge" in res_en.stdout

    # Vietnamese alias
    res_vi = runner.invoke(app, ["xulydaucan", "evaluate", "--hfo-m3", "25.0", "--oil-ppm", "10.0"])
    assert res_vi.exit_code == 0
    assert "Sludge & Incinerator Result" in res_vi.stdout


def test_cli_mooring_commands_en_and_vi():
    # English command
    res_en = runner.invoke(app, ["mooringtension", "evaluate", "--mbl", "90.0", "--tension", "35.0"])
    assert res_en.exit_code == 0
    assert "Smart Mooring Surge Result" in res_en.stdout
    assert "WLL" in res_en.stdout

    # Vietnamese alias
    res_vi = runner.invoke(app, ["cangdaybuoc", "evaluate", "--mbl", "80.0", "--pass-speed", "9.0"])
    assert res_vi.exit_code == 0
    assert "Smart Mooring Surge Result" in res_vi.stdout


def test_cli_cyber_commands_en_and_vi():
    # English command
    res_en = runner.invoke(app, ["maritimecyber", "evaluate", "--nav-iso", "--prop-iso", "--crew-iso"])
    assert res_en.exit_code == 0
    assert "Maritime Cyber Result" in res_en.stdout
    assert "Threat: NORMAL" in res_en.stdout

    # Vietnamese alias
    res_vi = runner.invoke(app, ["anninhmangtau", "evaluate", "--unauth-usb"])
    assert res_vi.exit_code == 0
    assert "Maritime Cyber Result" in res_vi.stdout
    assert "PHYSICAL_SECURITY_BREACH" in res_vi.stdout


def test_facade_run_all_unified():
    lpg_in = LpgReliquefactionInput(vessel_id="V-1", cargo_type="PROPANE")
    sludge_in = SludgeIncineratorInput(vessel_id="V-2")
    mooring_in = SmartMooringInput(berth_id="B-1", vessel_id="V-3")
    cyber_in = MaritimeCyberInput(vessel_id="V-4")

    res = MaritimeLpgSludgeMooringCyberFacade.run_all(
        lpg_input=lpg_in,
        sludge_input=sludge_in,
        mooring_input=mooring_in,
        cyber_input=cyber_in,
    )
    assert res.lpg is not None
    assert res.sludge is not None
    assert res.mooring is not None
    assert res.cyber is not None
    assert res.summary_status == "ALL_SYSTEMS_OPTIMAL"


@pytest.mark.asyncio
async def test_fastmcp_tools_maritime_355_to_358():
    from scripts.mcp_server import (
        mekong_maritime_lpg_reliquefaction_evaluate,
        mekong_maritime_sludge_incinerator_evaluate,
        mekong_maritime_mooring_surge_evaluate,
        mekong_maritime_cyber_resilience_evaluate,
    )

    r_lpg = await mekong_maritime_lpg_reliquefaction_evaluate(vessel_id="V-MCP-01", cargo_type="PROPANE")
    assert r_lpg["vessel_id"] == "V-MCP-01"
    assert "bog_rate_kg_h" in r_lpg

    r_sludge = await mekong_maritime_sludge_incinerator_evaluate(vessel_id="V-MCP-02", daily_hfo_consumed_m3=30.0)
    assert r_sludge["vessel_id"] == "V-MCP-02"
    assert "estimated_daily_sludge_m3" in r_sludge

    r_mooring = await mekong_maritime_mooring_surge_evaluate(berth_id="B-MCP-01", ship_design_mbl_tonnes=100.0)
    assert r_mooring["berth_id"] == "B-MCP-01"
    assert "hydrodynamic_surge_force_kn" in r_mooring

    r_cyber = await mekong_maritime_cyber_resilience_evaluate(vessel_id="V-MCP-04", active_satellite_link="STARLINK_LEO")
    assert r_cyber["vessel_id"] == "V-MCP-04"
    assert "segmentation_score_percent" in r_cyber
