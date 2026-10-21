"""Integration tests for Maritime Phases 359-362 Facade, CLI & FastMCP Tools.

Strictly kept under 200 lines, 0 mocks, verifying complete end-to-end flow.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime_autopilot_shaft_inert_waste_engine import (
    MaritimeAutopilotShaftInertWasteEngine,
    AdaptiveAutopilotInput,
    ShaftAlignmentVibrationInput,
    N2InertGasInput,
    SeaportWastewaterInput,
)
from scripts.mcp_server import (
    mekong_maritime_adaptive_autopilot_evaluate,
    mekong_maritime_shaft_vibration_evaluate,
    mekong_maritime_n2_inert_gas_evaluate,
    mekong_maritime_wastewater_recycling_evaluate,
)

runner = CliRunner()
app = build_app()


def test_facade_run_all_nominal_and_critical():
    auto_ok = AdaptiveAutopilotInput(
        vessel_id="V-TEST-01", target_heading_deg=100.0, actual_heading_deg=100.1, rate_of_turn_deg_s=0.01,
        actual_rudder_angle_deg=0.0, sea_state_douglas=2, speed_knots=15.0, command_latency_seconds=0.5,
    )
    shaft_ok = ShaftAlignmentVibrationInput(
        shaft_id="S-TEST-01", engine_rpm=80.0, propeller_blades_count=4, aft_bearing_reaction_kn=250.0,
        bearing_length_m=1.2, bearing_diameter_m=0.5, whirling_natural_frequency_hz=12.0, vibration_velocity_rms_mm_s=2.0,
    )
    inert_ok = N2InertGasInput(
        generator_id="G-TEST-01", target_tank_id="T-01", delivered_o2_percent_vol=0.6,
        measured_dew_point_celsius=-45.0, dryer_differential_pressure_bar=0.15, inert_gas_flow_rate_m3_h=1000.0,
    )
    waste_ok = SeaportWastewaterInput(
        facility_id="W-TEST-01", influent_flow_m3_day=100.0, recycled_permeate_m3_day=90.0,
        effluent_bod5_mg_l=10.0, effluent_turbidity_ntu=0.9, effluent_coliform_mpn_100ml=20.0, feed_tds_mg_l=800.0,
    )

    report_ok = MaritimeAutopilotShaftInertWasteEngine.run_all(auto_ok, shaft_ok, inert_ok, waste_ok)
    assert report_ok.overall_risk_level == "NOMINAL"
    assert len(report_ok.critical_alerts) == 0
    assert report_ok.summary_metrics["inert_cargo_supply_permitted"] is True

    # Induce critical failure in inert gas (high O2) & shaft (overload)
    inert_bad = N2InertGasInput(
        generator_id="G-BAD-01", target_tank_id="T-01", delivered_o2_percent_vol=3.0,
        measured_dew_point_celsius=-20.0, dryer_differential_pressure_bar=0.6, inert_gas_flow_rate_m3_h=1000.0,
    )
    report_crit = MaritimeAutopilotShaftInertWasteEngine.run_all(auto_ok, shaft_ok, inert_bad, waste_ok)
    assert report_crit.overall_risk_level == "CRITICAL"
    assert any("INERT GAS" in alert for alert in report_crit.critical_alerts)


def test_cli_bilingual_commands():
    # Phase 359: English & Vietnamese aliases
    res1 = runner.invoke(app, ["autopilot", "evaluate", "--vessel-id", "V-AUTO-CLI"])
    assert res1.exit_code == 0
    assert "Autopilot Evaluation:" in res1.output

    res2 = runner.invoke(app, ["laitudong", "evaluate", "--vessel-id", "V-AUTO-VN"])
    assert res2.exit_code == 0
    assert "Autopilot Evaluation:" in res2.output

    # Phase 360: English & Vietnamese aliases
    res3 = runner.invoke(app, ["shaftvib", "evaluate", "--shaft-id", "S-CLI-01"])
    assert res3.exit_code == 0
    assert "Shaft Vibration Evaluation:" in res3.output

    res4 = runner.invoke(app, ["rungdongtruc", "evaluate", "--shaft-id", "S-VN-01"])
    assert res4.exit_code == 0
    assert "Shaft Vibration Evaluation:" in res4.output

    # Phase 361: English & Vietnamese aliases
    res5 = runner.invoke(app, ["n2inert", "evaluate", "--gen-id", "G-CLI-01"])
    assert res5.exit_code == 0
    assert "N2 Inert Gas Evaluation:" in res5.output

    res6 = runner.invoke(app, ["khitron2", "evaluate", "--gen-id", "G-VN-01"])
    assert res6.exit_code == 0
    assert "N2 Inert Gas Evaluation:" in res6.output

    # Phase 362: English & Vietnamese aliases
    res7 = runner.invoke(app, ["portwaste", "evaluate", "--fac-id", "P-CLI-01"])
    assert res7.exit_code == 0
    assert "Wastewater Recycling Evaluation:" in res7.output

    res8 = runner.invoke(app, ["nuocthaicang", "evaluate", "--fac-id", "P-VN-01"])
    assert res8.exit_code == 0
    assert "Wastewater Recycling Evaluation:" in res8.output


@pytest.mark.asyncio
async def test_fastmcp_tools_evaluation():
    # 1. Autopilot MCP
    res_auto = await mekong_maritime_adaptive_autopilot_evaluate(
        vessel_id="V-MCP-01", target_heading_deg=180.0, actual_heading_deg=180.2, sea_state_douglas=2
    )
    assert res_auto["vessel_id"] == "V-MCP-01"
    assert res_auto["is_hunting_prevented"] is True

    # 2. Shaft Vibration MCP
    res_shaft = await mekong_maritime_shaft_vibration_evaluate(
        shaft_id="S-MCP-01", engine_rpm=95.0, propeller_blades_count=5, aft_bearing_reaction_kn=350.0
    )
    assert res_shaft["shaft_id"] == "S-MCP-01"
    assert res_shaft["blade_passing_frequency_hz"] == pytest.approx(7.92, abs=0.05)

    # 3. N2 Inert Gas MCP
    res_inert = await mekong_maritime_n2_inert_gas_evaluate(
        generator_id="G-MCP-01", target_tank_id="T-MCP-01", delivered_o2_percent_vol=0.7
    )
    assert res_inert["is_o2_compliant_igc"] is True
    assert res_inert["is_cargo_supply_permitted"] is True

    # 4. Wastewater Recycling MCP
    res_waste = await mekong_maritime_wastewater_recycling_evaluate(
        facility_id="W-MCP-01", influent_flow_m3_day=100.0, recycled_permeate_m3_day=90.0
    )
    assert res_waste["water_recovery_rate_percent"] == 90.0
    assert res_waste["is_zld_target_achieved"] is True
