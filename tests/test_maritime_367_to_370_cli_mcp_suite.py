"""CLI & MCP Integration test suite for Maritime Phases 367-370.

Tests Typer sub-apps, Central Facade run_all, and FastMCP endpoints.
Strictly kept under 200 lines.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime_fuel_bess_esi_ahc_engine import (
    BessModuleInput,
    EsiShipInput,
    FuelSampleInput,
    MaritimeFuelBessEsiAhcEngine,
    WinchSensorInput,
)

runner = CliRunner()


def test_central_facade_run_all_optimal() -> None:
    fuel = FuelSampleInput(sample_id="F1", fuel_grade="VLSFO", al_plus_si_mg_kg=15.0, flash_point_c=65.0)
    bess = BessModuleInput(pack_id="B1", soc_pct=60.0, soh_pct=95.0, c_rate=0.5, cell_max_temp_c=30.0)
    esi = EsiShipInput(vessel_imo="IMO1", vessel_name="V1", nox_reduction_pct=50.0, fuel_sulfur_pct=0.1, co2_improvement_pct=20.0)
    winch = WinchSensorInput(winch_id="W1", measured_tension_kn=200.0, mbl_kn=1000.0, target_tension_pct_mbl=20.0, ship_heave_amplitude_m=0.4, load_displacement_rms_m=0.02)

    res = MaritimeFuelBessEsiAhcEngine.run_all(fuel, bess, esi, winch)
    assert res.overall_status == "OPTIMAL"
    assert len(res.critical_alerts) == 0
    assert "esi_total_score" in res.summary_metrics


def test_central_facade_critical_alerts() -> None:
    fuel_bad = FuelSampleInput(sample_id="F-BAD", fuel_grade="VLSFO", al_plus_si_mg_kg=70.0, flash_point_c=55.0)
    bess_bad = BessModuleInput(pack_id="B-BAD", soc_pct=50.0, cell_max_temp_c=60.0, offgas_h2_ppm=60.0)
    esi = EsiShipInput(vessel_imo="IMO1", vessel_name="V1", nox_reduction_pct=20.0, fuel_sulfur_pct=0.4, co2_improvement_pct=5.0)
    winch_bad = WinchSensorInput(winch_id="W-BAD", measured_tension_kn=600.0, mbl_kn=1000.0)

    res = MaritimeFuelBessEsiAhcEngine.run_all(fuel_bad, bess_bad, esi, winch_bad)
    assert res.overall_status == "CRITICAL"
    assert len(res.critical_alerts) == 3


def test_cli_commands() -> None:
    app = build_app()

    # English commands
    res1 = runner.invoke(app, ["fuelquality", "evaluate", "--sample-id", "S-101", "--al-si", "20.0"])
    assert res1.exit_code == 0
    assert "ISO 8217 Fuel Evaluation" in res1.stdout

    res2 = runner.invoke(app, ["marinebess", "evaluate", "--pack-id", "B-101", "--temp", "32.0"])
    assert res2.exit_code == 0
    assert "Marine BESS Safety Evaluation" in res2.stdout

    res3 = runner.invoke(app, ["portesi", "evaluate", "--imo", "IMO1234567", "--nox-red", "40.0"])
    assert res3.exit_code == 0
    assert "Port ESI & Green Dues" in res3.stdout

    res4 = runner.invoke(app, ["mooringahc", "evaluate", "--winch-id", "W-101", "--tension", "200.0"])
    assert res4.exit_code == 0
    assert "Auto-Tension & AHC Winch" in res4.stdout

    # Vietnamese aliases
    res1_vn = runner.invoke(app, ["chatluongdau", "evaluate", "--sample-id", "S-VN", "--al-si", "15.0"])
    assert res1_vn.exit_code == 0
    assert "ISO 8217 Fuel Evaluation" in res1_vn.stdout

    res2_vn = runner.invoke(app, ["pinbesshanghai", "evaluate", "--pack-id", "B-VN"])
    assert res2_vn.exit_code == 0
    assert "Marine BESS Safety Evaluation" in res2_vn.stdout

    res3_vn = runner.invoke(app, ["chisotauxanh", "evaluate", "--imo", "IMO-VN"])
    assert res3_vn.exit_code == 0
    assert "Port ESI & Green Dues" in res3_vn.stdout

    res4_vn = runner.invoke(app, ["toicangdaysong", "evaluate", "--winch-id", "W-VN"])
    assert res4_vn.exit_code == 0
    assert "Auto-Tension & AHC Winch" in res4_vn.stdout


@pytest.mark.asyncio
async def test_mcp_server_endpoints() -> None:
    from scripts.mcp_server import (
        mekong_maritime_bess_safety_evaluate,
        mekong_maritime_fuel_quality_evaluate,
        mekong_maritime_mooring_ahc_evaluate,
        mekong_maritime_port_esi_evaluate,
    )

    r_fuel = await mekong_maritime_fuel_quality_evaluate(sample_id="M-FUEL", al_si=15.0, flash=65.0)
    assert r_fuel["status"] == "COMPLIANT"

    r_bess = await mekong_maritime_bess_safety_evaluate(pack_id="M-BESS", temp=30.0)
    assert r_bess["is_safe"] is True

    r_esi = await mekong_maritime_port_esi_evaluate(vessel_imo="IMO999", nox_red=45.0, sulfur=0.1)
    assert r_esi["esi_total_score"] > 0

    r_mooring = await mekong_maritime_mooring_ahc_evaluate(winch_id="M-WINCH", tension=200.0, mbl=1000.0)
    assert r_mooring["action_state"] == "HOLD"
