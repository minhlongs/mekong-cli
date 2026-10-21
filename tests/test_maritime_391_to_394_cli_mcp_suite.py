"""Integration tests for Maritime Phases 391-394 Facade, CLI & FastMCP tools.

Testing aggregated seaworthiness diagnosis, Typer commands, and FastMCP endpoints.
Strictly < 200 LOC, zero mock dependencies.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_391_oily_water_separator_ceramic import OilyWaterSeparatorInput
from src.core.maritime.phase_392_iccp_cathodic_protection_shaft import IccpCathodicProtectionInput
from src.core.maritime.phase_393_central_titanium_phe_ultrasonic import CentralTitaniumPheInput
from src.core.maritime.phase_394_chemical_cofferdam_vapor_inerting import ChemicalCofferdamInput
from src.core.maritime_ows_iccp_phe_cofferdam_engine import MaritimeOwsIccpPheCofferdamEngine
from src.cli.commands.maritime_ows_iccp_phe_cofferdam_command import (
    cofferdam_app,
    iccp_app,
    ows_app,
    phe_app,
)
from scripts.mcp_server import (
    mekong_maritime_central_phe_evaluate,
    mekong_maritime_chemical_cofferdam_evaluate,
    mekong_maritime_iccp_cathodic_protection_evaluate,
    mekong_maritime_ows_separator_evaluate,
)

runner = CliRunner()


def test_facade_nominal_optimal():
    engine = MaritimeOwsIccpPheCofferdamEngine()
    res = engine.evaluate(
        OilyWaterSeparatorInput(),
        IccpCathodicProtectionInput(),
        CentralTitaniumPheInput(),
        ChemicalCofferdamInput(),
    )
    assert res.overall_maritime_status == "NOMINAL_OPTIMAL"
    d = res.to_dict()
    assert d["overall_status"] == "NOMINAL_OPTIMAL"
    assert "oil_content_ppm" in d["ows_bilge"]
    assert "hull_potential_mv" in d["iccp_protection"]
    assert "heat_duty_kw" in d["central_phe"]
    assert "safety_status" in d["chemical_cofferdam"]


def test_facade_critical_hazard():
    engine = MaritimeOwsIccpPheCofferdamEngine()
    res = engine.evaluate(
        OilyWaterSeparatorInput(bilge_oil_content_ppm=25.0),
        IccpCathodicProtectionInput(),
        CentralTitaniumPheInput(),
        ChemicalCofferdamInput(voc_hydrocarbon_lel_pct=25.0),
    )
    assert res.overall_maritime_status == "CRITICAL_HAZARD"
    assert res.ows_result.alarm_status == "ALARM_15PPM_EXCEEDED"
    assert res.cofferdam_result.cofferdam_safety_status == "CRITICAL_CHEMICAL_BREACH"


def test_cli_ows_evaluate():
    result = runner.invoke(ows_app, ["--oil-ppm", "6.5", "--flow-m3-h", "2.0"])
    assert result.exit_code == 0
    assert "Oil Content (ppm)" in result.output
    assert "Three-Way Valve Command" in result.output


def test_cli_iccp_evaluate():
    result = runner.invoke(iccp_app, ["--potential-mv", "-890.0"])
    assert result.exit_code == 0
    assert "Hull Potential" in result.output
    assert "Shaft Grounding Status" in result.output


def test_cli_phe_evaluate():
    result = runner.invoke(phe_app, ["--fw-in-c", "46.0", "--fw-out-c", "36.0"])
    assert result.exit_code == 0
    assert "Heat Duty (kW)" in result.output
    assert "LMTD" in result.output


def test_cli_cofferdam_evaluate():
    result = runner.invoke(cofferdam_app, ["--lel-pct", "1.5"])
    assert result.exit_code == 0
    assert "Cofferdam Safety Status" in result.output
    assert "Inerting Compliant" in result.output


@pytest.mark.asyncio
async def test_fastmcp_endpoints_evaluation():
    ows_res = await mekong_maritime_ows_separator_evaluate(oil_ppm=7.0)
    assert ows_res["alarm_status"] == "NOMINAL_SAFE"
    assert ows_res["discharge_permitted"] is True

    iccp_res = await mekong_maritime_iccp_cathodic_protection_evaluate(potential_mv=-900.0)
    assert iccp_res["protection_status"] == "OPTIMAL_PROTECTION"
    assert iccp_res["corrosion_activity_risk"] is False

    phe_res = await mekong_maritime_central_phe_evaluate(fw_in_c=48.0, fw_out_c=36.0)
    assert phe_res["thermal_performance"] == "OPTIMAL_HEAT_TRANSFER"
    assert phe_res["heat_duty_kw"] > 0.0

    cofferdam_res = await mekong_maritime_chemical_cofferdam_evaluate(lel_pct=1.5)
    assert cofferdam_res["cofferdam_safety_status"] == "SAFE_INERTED"
    assert cofferdam_res["positive_pressure_intact"] is True
