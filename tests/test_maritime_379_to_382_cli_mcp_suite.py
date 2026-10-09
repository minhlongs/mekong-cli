"""Zero-mock tests for Central Facade, Typer CLI, and FastMCP tools (Phases 379-382).

Validates unified execution across Starting Air, Seachest Ingress, Draft & Tank Sounding,
and Port Pilotage ARPA engines under 200 lines.
"""

import asyncio
from typing import Any

from typer.testing import CliRunner

from scripts.mcp_server import (
    mekong_maritime_draft_sounding_evaluate,
    mekong_maritime_pilotage_arpa_evaluate,
    mekong_maritime_seachest_cooling_evaluate,
    mekong_maritime_starting_air_evaluate,
)
from src.cli.app_setup import build_app
from src.core.maritime_air_seachest_draft_pilot_engine import (
    DraftTankGaugingInput,
    EngineReversibility,
    MaritimeAirSeachestDraftPilotEngine,
    PilotageArpaInput,
    SeachestCoolingInput,
    SeachestSuctionType,
    StartingAirInput,
    TargetTrack,
)

runner = CliRunner()


def test_central_facade_run_all() -> None:
    air_in = StartingAirInput(
        vessel_id="IMO9923456",
        engine_type=EngineReversibility.REVERSIBLE,
        current_pressure_bar=30.0,
        compressor_charge_time_min=45.0,
        air_consumption_per_start_bar=1.2,
    )
    seachest_in = SeachestCoolingInput(
        vessel_id="IMO9923456",
        active_suction=SeachestSuctionType.LOW_SEACHEST,
        under_keel_clearance_m=8.0,
        strainer_inlet_pressure_bar=2.4,
        strainer_outlet_pressure_bar=2.2,
        seawater_flow_m3_h=800.0,
        mgps_anode_current_a=4.0,
    )
    draft_in = DraftTankGaugingInput(
        vessel_id="IMO9923456",
        draft_fore_m=10.0,
        draft_mid_port_m=10.0,
        draft_mid_starboard_m=10.0,
        draft_aft_m=10.0,
        tank_height_m=15.0,
        sounding_level_m=10.5,
    )
    pilot_in = PilotageArpaInput(
        vessel_id="IMO9923456",
        own_speed_knots=12.0,
        own_course_deg=90.0,
        targets=[
            TargetTrack(
                target_id="TGT01",
                relative_x_nm=5.0,
                relative_y_nm=5.0,
                target_speed_knots=10.0,
                target_course_deg=90.0,
            )
        ],
        ground_speed_knots=6.0,
        dwt_tonnes=40000.0,
        available_tug_bollard_pull_tonnes=60.0,
    )

    facade = MaritimeAirSeachestDraftPilotEngine()
    rep = facade.run_all(air_in, seachest_in, draft_in, pilot_in)

    assert rep.starting_air_report.vessel_id == "IMO9923456"
    assert rep.starting_air_report.is_solas_compliant is True
    assert rep.seachest_report.is_strainer_clogged is False
    assert rep.draft_sounding_report.quarter_mean_draft_m == 10.0
    assert rep.pilotage_arpa_report.is_pilot_speed_compliant is True
    assert rep.overall_status == "OPTIMAL_OPERATIONAL"
    assert len(rep.critical_alerts) == 0


def test_cli_sub_apps_execution() -> None:
    app = build_app()

    # English CLI commands
    res_air = runner.invoke(app, ["startingair", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_air.exit_code == 0
    assert "Starting Air System" in res_air.output

    res_sc = runner.invoke(app, ["seachest", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_sc.exit_code == 0
    assert "Seachest Cooling Evaluation" in res_sc.output

    res_ds = runner.invoke(app, ["draftsounding", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_ds.exit_code == 0
    assert "Draft & Tank Sounding" in res_ds.output

    res_pa = runner.invoke(app, ["pilotagearpa", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_pa.exit_code == 0
    assert "Port Pilotage & ARPA" in res_pa.output

    # Vietnamese aliases
    res_air_vn = runner.invoke(app, ["khinenkhoidong", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_air_vn.exit_code == 0
    assert "Starting Air System" in res_air_vn.output

    res_sc_vn = runner.invoke(app, ["vanthongbien", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_sc_vn.exit_code == 0
    assert "Seachest Cooling Evaluation" in res_sc_vn.output

    res_ds_vn = runner.invoke(app, ["mondatketluu", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_ds_vn.exit_code == 0
    assert "Draft & Tank Sounding" in res_ds_vn.output

    res_pa_vn = runner.invoke(app, ["hoatieuarpa", "evaluate", "--vessel-id", "IMO9923456"])
    assert res_pa_vn.exit_code == 0
    assert "Port Pilotage & ARPA" in res_pa_vn.output


def test_fastmcp_async_tools() -> None:
    async def run_mcp_checks() -> dict[str, Any]:
        air_res = await mekong_maritime_starting_air_evaluate(
            vessel_id="IMO-MCP-379",
            engine_type="REVERSIBLE",
            current_pressure_bar=30.0,
            compressor_charge_time_min=45.0,
            air_consumption_per_start_bar=1.2,
        )
        seachest_res = await mekong_maritime_seachest_cooling_evaluate(
            vessel_id="IMO-MCP-380",
            active_suction="LOW_SEACHEST",
            under_keel_clearance_m=7.0,
            strainer_inlet_pressure_bar=2.4,
            strainer_outlet_pressure_bar=2.2,
            seawater_flow_m3_h=800.0,
            mgps_anode_current_a=4.0,
        )
        draft_res = await mekong_maritime_draft_sounding_evaluate(
            vessel_id="IMO-MCP-381",
            draft_fore_m=10.0,
            draft_mid_port_m=10.0,
            draft_mid_starboard_m=10.0,
            draft_aft_m=10.0,
            tank_height_m=15.0,
            sounding_level_m=10.5,
        )
        pilot_res = await mekong_maritime_pilotage_arpa_evaluate(
            vessel_id="IMO-MCP-382",
            own_speed_knots=12.0,
            own_course_deg=90.0,
            ground_speed_knots=6.0,
            dwt_tonnes=45000.0,
            available_tug_bollard_pull_tonnes=60.0,
        )
        return {
            "air": air_res,
            "seachest": seachest_res,
            "draft": draft_res,
            "pilot": pilot_res,
        }

    results = asyncio.run(run_mcp_checks())
    assert results["air"]["vessel_id"] == "IMO-MCP-379"
    assert results["air"]["is_solas_compliant"] is True
    assert results["seachest"]["is_strainer_clogged"] is False
    assert results["draft"]["quarter_mean_draft_m"] == 10.0
    assert results["pilot"]["is_pilot_speed_compliant"] is True
