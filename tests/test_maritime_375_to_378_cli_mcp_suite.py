"""Zero-mock tests for Central Facade, Typer CLI, and FastMCP tools (Phases 375-378).

Validates unified execution across Voyage Weather CII, VOC Recovery, Yard Stacking,
and HVAC Greywater engines under 200 lines.
"""

import asyncio
from typing import Any

from typer.testing import CliRunner

from scripts.mcp_server import (
    mekong_maritime_greywater_reuse_evaluate,
    mekong_maritime_voc_recovery_evaluate,
    mekong_maritime_weather_cii_evaluate,
    mekong_maritime_yard_rtg_dispatch_evaluate,
)
from src.cli.app_setup import build_app
from src.core.maritime_voyage_voc_yard_greywater_engine import (
    ContainerItem,
    MaritimeVoyageVocYardGreywaterEngine,
    VocRecoveryInput,
    VoyageRoutingInput,
    WaterReclamationInput,
    YardBlockInput,
)

runner = CliRunner()


def test_central_facade_run_all() -> None:
    voyage_in = VoyageRoutingInput(
        vessel_id="IMO9991111",
        dwt_tonnes=60000.0,
        distance_nm=2500.0,
        planned_speed_knots=14.0,
        calm_sea_power_kw=7000.0,
        beaufort_scale=4,
        significant_wave_height_m=2.0,
        fuel_consumption_tonnes=50.0,
    )
    voc_in = VocRecoveryInput(
        tanker_id="MT Mekong Star",
        loading_rate_m3_h=2500.0,
        vapor_return_capacity_m3_h=3500.0,
        tank_pressure_kpa=7.0,
        oxygen_content_pct=4.8,
        voc_concentration_g_m3=750.0,
    )
    yard_in = YardBlockInput(
        block_id="BLK-Z99",
        containers=[
            ContainerItem("CTR-01", bay=1, row=1, tier=1, departure_order=2),
            ContainerItem("CTR-02", bay=1, row=1, tier=2, departure_order=1),
        ],
        available_rtg_cranes=2,
        active_quay_cranes=2,
    )
    water_in = WaterReclamationInput(
        vessel_id="IMO9991111",
        air_flow_rate_m3_h=12000.0,
        humidity_in_g_kg=19.0,
        humidity_out_g_kg=9.0,
        condensate_tds_ppm=18.0,
        greywater_daily_inflow_m3=14.0,
        treated_bod5_mg_l=14.0,
        treated_tss_mg_l=7.0,
        treated_turbidity_ntu=1.1,
        treated_coliform_mpn_100ml=40.0,
        uv_c_dose_mj_cm2=44.0,
    )

    facade = MaritimeVoyageVocYardGreywaterEngine()
    rep = facade.run_all(voyage_in, voc_in, yard_in, water_in)

    assert rep.weather_cii_report.vessel_id == "IMO9991111"
    assert rep.weather_cii_report.cii_rating.value in ["A", "B", "C"]
    assert rep.voc_recovery_report.is_safe_to_load is True
    assert rep.yard_rtg_report.is_crane_capacity_sufficient is True
    assert rep.greywater_report.is_qcvn14_compliant is True
    assert rep.overall_status == "OPTIMAL"
    assert len(rep.critical_alerts) == 0


def test_cli_sub_apps_execution() -> None:
    app = build_app()

    # English CLI commands
    res_cii = runner.invoke(app, ["weathercii", "evaluate", "--vessel-id", "IMO1234567"])
    assert res_cii.exit_code == 0
    assert "Voyage Weather & CII Evaluation" in res_cii.output

    res_voc = runner.invoke(app, ["vocvapor", "evaluate", "--tanker-id", "MT Saigon River"])
    assert res_voc.exit_code == 0
    assert "VOC Recovery & Vapor Balancing" in res_voc.output

    res_yard = runner.invoke(app, ["yardstack", "evaluate", "--block-id", "BLK-TEST"])
    assert res_yard.exit_code == 0
    assert "Yard Block Stacking & RTG Dispatch" in res_yard.output

    res_gw = runner.invoke(app, ["greywater", "evaluate", "--vessel-id", "IMO7654321"])
    assert res_gw.exit_code == 0
    assert "HVAC Condensate & Greywater Reclamation" in res_gw.output

    # Vietnamese aliases
    res_cii_vn = runner.invoke(app, ["dinhhuongcii", "evaluate", "--vessel-id", "IMO1234567"])
    assert res_cii_vn.exit_code == 0
    assert "Voyage Weather & CII Evaluation" in res_cii_vn.output

    res_voc_vn = runner.invoke(app, ["thuhoikhivoc", "evaluate", "--tanker-id", "MT Saigon River"])
    assert res_voc_vn.exit_code == 0
    assert "VOC Recovery & Vapor Balancing" in res_voc_vn.output


def test_fastmcp_async_tools() -> None:
    async def run_mcp_checks() -> dict[str, Any]:
        cii_res = await mekong_maritime_weather_cii_evaluate(
            vessel_id="IMO-MCP-1",
            dwt_tonnes=50000.0,
            distance_nm=2000.0,
            speed_knots=14.0,
            power_kw=7000.0,
            beaufort_scale=3,
            wave_hs_m=1.5,
            fuel_tonnes=45.0,
        )
        voc_res = await mekong_maritime_voc_recovery_evaluate(
            tanker_id="MT-MCP-TANKER",
            loading_rate_m3_h=2000.0,
            vapor_capacity_m3_h=2800.0,
            tank_pressure_kpa=8.0,
            o2_pct=5.0,
            voc_conc_g_m3=700.0,
        )
        yard_res = await mekong_maritime_yard_rtg_dispatch_evaluate(
            block_id="BLK-MCP",
            rtg_cranes=2,
            qc_cranes=2,
            gantry_dist_m=80.0,
        )
        gw_res = await mekong_maritime_greywater_reuse_evaluate(
            vessel_id="IMO-MCP-1",
            air_flow_m3_h=10000.0,
            hum_in_g_kg=20.0,
            hum_out_g_kg=10.0,
            tds_ppm=20.0,
            greywater_m3=15.0,
            bod5_mg_l=15.0,
            tss_mg_l=8.0,
            turbidity_ntu=1.2,
            coliform_mpn=50.0,
            uv_dose_mj_cm2=42.0,
        )
        return {
            "cii": cii_res,
            "voc": voc_res,
            "yard": yard_res,
            "gw": gw_res,
        }

    results = asyncio.run(run_mcp_checks())
    assert results["cii"]["vessel_id"] == "IMO-MCP-1"
    assert results["voc"]["is_safe_to_load"] is True
    assert results["yard"]["is_crane_capacity_sufficient"] is True
    assert results["gw"]["is_qcvn14_compliant"] is True
