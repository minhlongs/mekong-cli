"""CLI & FastMCP Integration Tests for Maritime Phases 351-354.

Tests Typer CLI invocation and FastMCP tool calls for:
- loadingcomp / ondinhtau
- hnsdrift / toicathns
- centralcool / lammatbien
- ecert / chungchiso
Strictly adheres to zero-mock and kept under 200 lines.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from scripts.mcp_server import (
    mekong_bulk_loading_stability_evaluate,
    mekong_central_cooling_mgps_evaluate,
    mekong_hns_chemical_spill_drift_simulate,
    mekong_marine_ecert_verify,
)

runner = CliRunner()


@pytest.fixture(scope="module")
def cli_app():
    return build_app()


def test_cli_loadingcomp_evaluation(cli_app):
    result = runner.invoke(
        cli_app,
        ["loadingcomp", "evaluate", "--vessel", "BULK-TEST-01", "--displacement", "60000.0", "--km", "11.0", "--kg", "9.5"],
    )
    assert result.exit_code == 0
    assert "BULK-TEST-01" in result.stdout
    assert "gm_fluid_m" in result.stdout

    alias_res = runner.invoke(cli_app, ["ondinhtau", "evaluate", "--vessel", "BULK-VN-01"])
    assert alias_res.exit_code == 0
    assert "BULK-VN-01" in alias_res.stdout


def test_cli_hnsdrift_simulation(cli_app):
    result = runner.invoke(
        cli_app,
        ["hnsdrift", "simulate", "--un", "UN1203", "--name", "GASOLINE", "--group", "FE", "--tonnes", "25.0"],
    )
    assert result.exit_code == 0
    assert "UN1203" in result.stdout
    assert "drift_speed_knots" in result.stdout

    alias_res = runner.invoke(cli_app, ["toicathns", "simulate", "--un", "UN1267"])
    assert alias_res.exit_code == 0
    assert "UN1267" in alias_res.stdout


def test_cli_centralcool_evaluation(cli_app):
    result = runner.invoke(
        cli_app,
        ["centralcool", "evaluate", "--vessel", "COOL-TEST-01", "--heat-kw", "4000.0", "--speed", "16.0"],
    )
    assert result.exit_code == 0
    assert "COOL-TEST-01" in result.stdout
    assert "lmtd_celsius" in result.stdout

    alias_res = runner.invoke(cli_app, ["lammatbien", "evaluate", "--vessel", "COOL-VN-01"])
    assert alias_res.exit_code == 0
    assert "COOL-VN-01" in alias_res.stdout


def test_cli_ecert_verification(cli_app):
    result = runner.invoke(
        cli_app,
        ["ecert", "verify", "--cert-id", "UTN-TEST-001", "--imo", "IMO9999999", "--ro", "VR"],
    )
    assert result.exit_code == 0
    assert "UTN-TEST-001" in result.stdout
    assert "is_signature_valid" in result.stdout

    alias_res = runner.invoke(cli_app, ["chungchiso", "verify", "--cert-id", "UTN-ALIAS-001"])
    assert alias_res.exit_code == 0
    assert "UTN-ALIAS-001" in alias_res.stdout


@pytest.mark.asyncio
async def test_mcp_bulk_loading_evaluate():
    res = await mekong_bulk_loading_stability_evaluate(
        vessel_id="BULK-MCP",
        displacement_tonnes=55000.0,
        km_transverse_m=10.8,
        kg_solid_m=9.2,
    )
    assert res["vessel_id"] == "BULK-MCP"
    assert res["is_stability_compliant"] is True
    assert res["gm_fluid_m"] > 0.15


@pytest.mark.asyncio
async def test_mcp_hns_drift_simulate():
    res = await mekong_hns_chemical_spill_drift_simulate(
        chemical_un_number="UN1203",
        chemical_name="GASOLINE",
        behavior_group="E",
        spill_quantity_tonnes=50.0,
    )
    assert res["chemical_un_number"] == "UN1203"
    assert res["drift_speed_knots"] > 0.0
    assert res["hazard_isolation_radius_nm"] > 0.0


@pytest.mark.asyncio
async def test_mcp_central_cooling_evaluate():
    res = await mekong_central_cooling_mgps_evaluate(
        vessel_id="CONTAINER-MCP",
        heat_duty_kw=4200.0,
        vessel_speed_knots=15.0,
    )
    assert res["vessel_id"] == "CONTAINER-MCP"
    assert res["is_scoop_active"] is True
    assert res["cu_ion_concentration_ug_l"] > 0.0


@pytest.mark.asyncio
async def test_mcp_marine_ecert_verify():
    res = await mekong_marine_ecert_verify(
        certificate_id="UTN-DNV-MCP",
        certificate_type="CLASS",
        vessel_imo="IMO9876543",
        issuing_ro="DNV",
    )
    assert res["certificate_id"] == "UTN-DNV-MCP"
    assert res["is_signature_valid"] is True
    assert res["lifecycle_status"] == "VALID"
