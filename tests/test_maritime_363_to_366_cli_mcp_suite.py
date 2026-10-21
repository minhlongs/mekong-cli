"""Integration tests for Maritime Phases 363-366 Facade, CLI & FastMCP Tools.

Strictly kept under 200 lines, 0 mocks, verifying complete end-to-end flow.
"""

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    mekong_maritime_generator_pms_evaluate,
    mekong_maritime_lifeboat_hru_evaluate,
    mekong_maritime_ovid_tug_vetting_evaluate,
    mekong_maritime_sediment_beneficiation_evaluate,
)
from src.cli.app_setup import build_app
from src.core.maritime_lsa_pms_dredge_tug_engine import (
    DredgedSedimentInput,
    LifeboatHruInput,
    MarineGeneratorUnit,
    MaritimeLsaPmsDredgeTugEngine,
    PmsEvaluationInput,
    TugVettingInput,
)

runner = CliRunner()
app = build_app()


def test_facade_run_all_compliant_and_critical():
    lb_ok = LifeboatHruInput("LB-01", drop_height_m=18.0, ramp_angle_deg=33.0, entry_angle_deg=55.0, peak_acceleration_g=9.0, hru_water_depth_m=2.5)
    pms_ok = PmsEvaluationInput(generators=[MarineGeneratorUnit("DG-01", 1000.0, 400.0, 60.0, 100.0)])
    sed_ok = DredgedSedimentInput("SED-01", tbt_mg_kg=0.0003, total_pah_mg_kg=2.0, heavy_metals={"as": 10.0}, solids_content_pct=65.0, stabilized_ucs_kpa=70.0)
    tug_ok = TugVettingInput("TUG-01", certified_bollard_pull_t=65.0, towline_mbl_t=150.0, winch_brake_hold_t=130.0, quick_release_time_s=1.8)

    report_ok = MaritimeLsaPmsDredgeTugEngine.run_all(lb_ok, pms_ok, sed_ok, tug_ok)
    assert report_ok.overall_risk_level == "COMPLIANT"
    assert len(report_ok.critical_alerts) == 0

    # Induce critical failure in lifeboat g-force (>15g) and sediment TBT (>0.001 mg/kg)
    lb_bad = LifeboatHruInput("LB-BAD", drop_height_m=30.0, ramp_angle_deg=33.0, entry_angle_deg=55.0, peak_acceleration_g=18.0, hru_water_depth_m=5.0)
    sed_bad = DredgedSedimentInput("SED-BAD", tbt_mg_kg=0.005, total_pah_mg_kg=2.0, heavy_metals={}, solids_content_pct=65.0, stabilized_ucs_kpa=70.0)
    report_crit = MaritimeLsaPmsDredgeTugEngine.run_all(lb_bad, pms_ok, sed_bad, tug_ok)
    assert report_crit.overall_risk_level == "CRITICAL"
    assert len(report_crit.critical_alerts) >= 2


def test_cli_bilingual_commands():
    # Phase 363 Lifeboat
    r1 = runner.invoke(app, ["lifeboat", "evaluate", "--boat-id", "LB-CLI"])
    assert r1.exit_code == 0
    assert "Lifeboat & HRU Evaluation:" in r1.output

    r1_vn = runner.invoke(app, ["cuusinhhru", "evaluate", "--boat-id", "LB-VN"])
    assert r1_vn.exit_code == 0
    assert "Lifeboat & HRU Evaluation:" in r1_vn.output

    # Phase 364 Marine PMS
    r2 = runner.invoke(app, ["marinepms", "evaluate", "--dg1-kw", "500", "--dg2-kw", "500"])
    assert r2.exit_code == 0
    assert "Marine Generator PMS:" in r2.output

    r2_vn = runner.invoke(app, ["dienmaritime", "evaluate", "--dg1-kw", "500", "--dg2-kw", "500"])
    assert r2_vn.exit_code == 0
    assert "Marine Generator PMS:" in r2_vn.output

    # Phase 365 Dredge Spoil
    r3 = runner.invoke(app, ["dredgespoil", "evaluate", "--batch-id", "SED-CLI"])
    assert r3.exit_code == 0
    assert "Sediment Beneficiation:" in r3.output

    r3_vn = runner.invoke(app, ["bunnaovet", "evaluate", "--batch-id", "SED-VN"])
    assert r3_vn.exit_code == 0
    assert "Sediment Beneficiation:" in r3_vn.output

    # Phase 366 Tug Vetting
    r4 = runner.invoke(app, ["tugvetting", "evaluate", "--tug-id", "TUG-CLI"])
    assert r4.exit_code == 0
    assert "OCIMF OVID Tug Vetting:" in r4.output

    r4_vn = runner.invoke(app, ["kiemdinhtau", "evaluate", "--tug-id", "TUG-VN"])
    assert r4_vn.exit_code == 0
    assert "OCIMF OVID Tug Vetting:" in r4_vn.output


@pytest.mark.asyncio
async def test_fastmcp_tools():
    # FastMCP Lifeboat
    mcp_lb = await mekong_maritime_lifeboat_hru_evaluate(boat_id="LB-MCP", peak_acceleration_g=9.5)
    assert mcp_lb["boat_id"] == "LB-MCP"
    assert mcp_lb["is_acceleration_tolerable"] is True

    # FastMCP Marine PMS
    mcp_pms = await mekong_maritime_generator_pms_evaluate(dg1_kw=800.0, dg2_kw=900.0, rated_kw=1000.0)
    assert mcp_pms["total_load_pct"] == 85.0
    assert mcp_pms["is_auto_start_required"] is True

    # FastMCP Sediment
    mcp_sed = await mekong_maritime_sediment_beneficiation_evaluate(batch_id="SED-MCP", tbt_mg_kg=0.0003)
    assert mcp_sed["is_open_sea_dump_permitted"] is True
    assert mcp_sed["is_beneficial_reuse_approved"] is True

    # FastMCP Tug Vetting
    mcp_tug = await mekong_maritime_ovid_tug_vetting_evaluate(tug_id="TUG-MCP", winch_brake_hold_t=130.0, towline_mbl_t=150.0)
    assert mcp_tug["brake_hold_ratio_pct"] == 86.7
    assert mcp_tug["is_winch_brake_compliant"] is True
