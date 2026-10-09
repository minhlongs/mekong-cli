"""CLI & FastMCP Integration Tests for Maritime Phases 347-350.

Tests Typer CLI invocation and FastMCP tool calls for:
- iccp / chongannmon
- scrnox / khixatier3
- anchorwindlass / neocang
- eblmletr / vandonso
Strictly adheres to zero-mock and kept under 200 lines.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from scripts.mcp_server import (
    mekong_anchorage_windlass_holding_evaluate,
    mekong_ebl_mletr_transfer_verify,
    mekong_engine_scr_nox_evaluate,
    mekong_iccp_cathodic_protection_evaluate,
)

runner = CliRunner()


@pytest.fixture(scope="module")
def cli_app():
    return build_app()


def test_cli_iccp_evaluation(cli_app):
    result = runner.invoke(
        cli_app,
        ["iccp", "evaluate", "--vessel", "VN-TEST-01", "--lbp", "150.0", "--beam", "25.0"],
    )
    assert result.exit_code == 0
    assert "VN-TEST-01" in result.stdout
    assert "wetted_surface_area_m2" in result.stdout

    alias_res = runner.invoke(cli_app, ["chongannmon", "evaluate", "--vessel", "VN-ALIAS-01"])
    assert alias_res.exit_code == 0
    assert "VN-ALIAS-01" in alias_res.stdout


def test_cli_scr_nox_evaluation(cli_app):
    result = runner.invoke(
        cli_app,
        ["scrnox", "evaluate", "--engine", "MAN-TEST-01", "--rpm", "110.0", "--power", "7000.0"],
    )
    assert result.exit_code == 0
    assert "MAN-TEST-01" in result.stdout
    assert "tier_limit_g_kwh" in result.stdout

    alias_res = runner.invoke(cli_app, ["khixatier3", "evaluate", "--engine", "MAN-ALIAS-01"])
    assert alias_res.exit_code == 0
    assert "MAN-ALIAS-01" in alias_res.stdout


def test_cli_anchorage_holding_evaluation(cli_app):
    result = runner.invoke(
        cli_app,
        ["anchorwindlass", "evaluate", "--vessel", "MV-TEST-01", "--displacement", "30000.0"],
    )
    assert result.exit_code == 0
    assert "MV-TEST-01" in result.stdout
    assert "scope_ratio" in result.stdout

    alias_res = runner.invoke(cli_app, ["neocang", "evaluate", "--vessel", "MV-ALIAS-01"])
    assert alias_res.exit_code == 0
    assert "MV-ALIAS-01" in alias_res.stdout


def test_cli_ebl_mletr_verification(cli_app):
    result = runner.invoke(
        cli_app,
        ["eblmletr", "verify", "--bl", "EBL-TEST-001", "--carrier", "TEST LINE"],
    )
    assert result.exit_code == 0
    assert "EBL-TEST-001" in result.stdout
    assert "cryptographic_lineage_hash" in result.stdout

    alias_res = runner.invoke(cli_app, ["vandonso", "verify", "--bl", "EBL-ALIAS-001"])
    assert alias_res.exit_code == 0
    assert "EBL-ALIAS-001" in alias_res.stdout


@pytest.mark.asyncio
async def test_mcp_iccp_cathodic_protection_evaluate():
    res = await mekong_iccp_cathodic_protection_evaluate(
        vessel_id="MCP-HULL-01",
        length_bp_m=175.0,
        breadth_m=28.0,
        draft_m=9.5,
    )
    assert res["vessel_id"] == "MCP-HULL-01"
    assert "wetted_surface_area_m2" in res
    assert res["protection_status"] == "OPTIMAL"


@pytest.mark.asyncio
async def test_mcp_engine_scr_nox_evaluate():
    res = await mekong_engine_scr_nox_evaluate(
        engine_id="MCP-ENG-01",
        rated_speed_rpm=105.0,
        engine_power_kw=9000.0,
        raw_nox_g_kwh=11.8,
        exhaust_temp_celsius=330.0,
        is_neca_zone=True,
    )
    assert res["engine_id"] == "MCP-ENG-01"
    assert res["is_compliant"] is True
    assert res["engine_status"] == "COMPLIANT"


@pytest.mark.asyncio
async def test_mcp_anchorage_windlass_holding_evaluate():
    res = await mekong_anchorage_windlass_holding_evaluate(
        vessel_id="MCP-ANCHOR-01",
        displacement_tonnes=35000.0,
        water_depth_m=18.0,
        shackles_paid_out=5.0,
    )
    assert res["vessel_id"] == "MCP-ANCHOR-01"
    assert res["is_holding_secure"] is True
    assert res["dragging_risk"] == "LOW"


@pytest.mark.asyncio
async def test_mcp_ebl_mletr_transfer_verify():
    res = await mekong_ebl_mletr_transfer_verify(
        bl_number="MCP-EBL-01",
        carrier_name="MEKONG LINE",
        shipper_name="PETROVIETNAM",
        consignee_name="TO ORDER",
        events_json='[{"event_type": "ISSUE", "from_party": "PETROVIETNAM", "to_party": "BANK A", "timestamp_iso": "2026-10-09T00:00:00Z"}, {"event_type": "SURRENDER", "from_party": "BANK A", "to_party": "MEKONG LINE", "timestamp_iso": "2026-10-09T01:00:00Z"}]',
        requested_release_party="RECEIVER",
    )
    assert res["bl_number"] == "MCP-EBL-01"
    assert res["lifecycle_status"] == "SURRENDERED"
    assert res["is_release_authorized"] is True
