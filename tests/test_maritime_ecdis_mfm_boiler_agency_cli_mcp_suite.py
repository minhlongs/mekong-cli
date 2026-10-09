"""CLI & FastMCP Integration Tests for Maritime Phases 343-346.

Tests Typer CLI invocation and FastMCP tool calls for:
- ecdis / haidodientu
- mfmbunker / dodaucoriolis
- noihoint / hoanoihotau
- portagency / quyettoancangg
Strictly adheres to zero-mock and kept under 200 lines.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from scripts.mcp_server import (
    mekong_boiler_water_treatment_analyze,
    mekong_bunkering_mfm_verify,
    mekong_ecdis_passage_planning,
    mekong_port_agency_disbursements_reconcile,
)

runner = CliRunner()


@pytest.fixture(scope="module")
def cli_app():
    return build_app()


def test_cli_ecdis_passage_planning(cli_app):
    result = runner.invoke(
        cli_app,
        ["ecdis", "plan", "--leg", "TEST-LEG", "--speed", "12.0", "--depth", "14.0"],
    )
    assert result.exit_code == 0
    assert "TEST-LEG" in result.stdout
    assert "safety_depth_m" in result.stdout

    # Test Vietnamese alias
    alias_res = runner.invoke(cli_app, ["haidodientu", "plan", "--leg", "VN-LEG"])
    assert alias_res.exit_code == 0
    assert "VN-LEG" in alias_res.stdout


def test_cli_mfmbunker_verification(cli_app):
    result = runner.invoke(
        cli_app,
        ["mfmbunker", "verify", "--bunker-id", "BNK-CLI-01", "--mfm-mass", "400.0", "--sounding-mass", "399.0"],
    )
    assert result.exit_code == 0
    assert "BNK-CLI-01" in result.stdout
    assert "is_mpe_compliant" in result.stdout

    # Test Vietnamese alias
    alias_res = runner.invoke(cli_app, ["dodaucoriolis", "verify", "--bunker-id", "BNK-VN-01"])
    assert alias_res.exit_code == 0
    assert "BNK-VN-01" in alias_res.stdout


def test_cli_noihoint_analysis(cli_app):
    result = runner.invoke(
        cli_app,
        ["noihoint", "analyze", "--boiler-id", "BLR-CLI-01", "--ph", "10.1", "--cl", "110.0"],
    )
    assert result.exit_code == 0
    assert "BLR-CLI-01" in result.stdout
    assert "recommended_blowdown_pct" in result.stdout

    # Test Vietnamese alias
    alias_res = runner.invoke(cli_app, ["hoanoihotau", "analyze", "--boiler-id", "BLR-VN-01"])
    assert alias_res.exit_code == 0
    assert "BLR-VN-01" in alias_res.stdout


def test_cli_portagency_reconciliation(cli_app):
    result = runner.invoke(
        cli_app,
        ["portagency", "reconcile", "--call-id", "CALL-CLI-01", "--advance", "30000.0"],
    )
    assert result.exit_code == 0
    assert "CALL-CLI-01" in result.stdout
    assert "settlement_status" in result.stdout

    # Test Vietnamese alias
    alias_res = runner.invoke(cli_app, ["quyettoancangg", "reconcile", "--call-id", "CALL-VN-01"])
    assert alias_res.exit_code == 0
    assert "CALL-VN-01" in alias_res.stdout


@pytest.mark.asyncio
async def test_mcp_ecdis_passage_planning():
    res = await mekong_ecdis_passage_planning(
        leg_name="MCP-LEG",
        planned_speed_knots=10.0,
        channel_depth_charted_m=12.0,
    )
    assert res["leg_name"] == "MCP-LEG"
    assert "safety_contour_m" in res
    assert res["is_safe_transit"] is True


@pytest.mark.asyncio
async def test_mcp_bunkering_mfm_verify():
    res = await mekong_bunkering_mfm_verify(
        bunker_id="MCP-BNK",
        mfm_totalizer_mass_mt=500.0,
        vessel_sounding_mass_mt=498.0,
    )
    assert res["bunker_id"] == "MCP-BNK"
    assert res["is_mpe_compliant"] is True


@pytest.mark.asyncio
async def test_mcp_boiler_water_treatment_analyze():
    res = await mekong_boiler_water_treatment_analyze(
        boiler_id="MCP-BLR",
        water_ph=10.2,
        chloride_ppm=100.0,
    )
    assert res["boiler_id"] == "MCP-BLR"
    assert res["overall_status"] == "OPTIMAL"


@pytest.mark.asyncio
async def test_mcp_port_agency_disbursements_reconcile():
    res = await mekong_port_agency_disbursements_reconcile(
        call_id="MCP-CALL",
        advance_received_usd=35000.0,
    )
    assert res["call_id"] == "MCP-CALL"
    assert "settlement_status" in res
    assert "actual_port_costs_usd" in res
