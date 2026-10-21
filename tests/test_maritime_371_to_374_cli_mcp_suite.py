"""CLI & MCP Integration test suite for Maritime Phases 371-374.

Tests Typer sub-apps, Central Facade run_all, and FastMCP endpoints.
Strictly kept under 200 lines.
"""

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime_pto_berth_biofoul_waste_engine import (
    BerthRequest,
    BiofoulingInspection,
    MaritimePtoBerthBiofoulWasteEngine,
    ShaftGeneratorInput,
    ShaftHybridMode,
    WasteOilBatch,
)

runner = CliRunner()


def test_central_facade_run_all_optimal() -> None:
    pto = ShaftGeneratorInput(
        vessel_id="V-PTO-01",
        main_engine_mcr_kw=10000.0,
        main_engine_speed_rpm=80.0,
        main_engine_rated_rpm=95.0,
        current_me_load_kw=6500.0,
        shaft_gen_capacity_kw=1500.0,
        shaft_power_kw=1000.0,
        hotel_load_kw=800.0,
        requested_mode=ShaftHybridMode.PTO,
    )
    berth = BerthRequest(
        vessel_name="V-BERTH-01",
        loa_m=300.0,
        draft_m=12.0,
        container_moves=1000,
        assigned_berth_length_m=350.0,
        berth_chart_depth_m=14.0,
        tide_height_m=1.0,
        assigned_cranes=3,
        crane_spacing_m=45.0,
    )
    biofoul = BiofoulingInspection(
        vessel_id="V-BIO-01",
        level_of_fouling=1,
        hull_surface_area_m2=12000.0,
        baseline_propulsion_power_kw=14000.0,
        rov_capture_efficiency_pct=0.0,
        filtration_mesh_micron=50.0,
    )
    waste = WasteOilBatch(
        batch_id="W-01",
        volume_m3=100.0,
        flash_point_c=66.0,
        water_content_pct=30.0,
        effluent_oil_ppm=10.0,
        rfo_lhv_mj_kg=40.0,
    )

    res = MaritimePtoBerthBiofoulWasteEngine.run_all(pto, berth, biofoul, waste)
    assert res.overall_status == "OPTIMAL_OPERATIONAL"
    assert len(res.critical_alerts) == 0
    assert "pto_savings_kg_per_h" in res.summary_metrics


def test_central_facade_critical_alerts() -> None:
    pto = ShaftGeneratorInput(
        vessel_id="V-PTO-BAD",
        main_engine_mcr_kw=10000.0,
        main_engine_speed_rpm=50.0,
        main_engine_rated_rpm=100.0,  # Speed < 65% -> PTO inhibited
        current_me_load_kw=4000.0,
        shaft_gen_capacity_kw=1500.0,
        shaft_power_kw=1000.0,
        hotel_load_kw=800.0,
        requested_mode=ShaftHybridMode.PTO,
    )
    berth = BerthRequest(
        vessel_name="V-BERTH-BAD",
        loa_m=300.0,
        draft_m=12.0,
        container_moves=1000,
        assigned_berth_length_m=350.0,
        berth_chart_depth_m=14.0,
        tide_height_m=1.0,
        assigned_cranes=2,
        crane_spacing_m=20.0,  # Crane spacing violation
    )
    biofoul = BiofoulingInspection(
        vessel_id="V-BIO-BAD",
        level_of_fouling=4,  # Drydock mandatory
        hull_surface_area_m2=12000.0,
        baseline_propulsion_power_kw=14000.0,
        rov_capture_efficiency_pct=99.0,
        filtration_mesh_micron=5.0,
    )
    waste = WasteOilBatch(
        batch_id="W-BAD",
        volume_m3=100.0,
        flash_point_c=50.0,  # Low flash point reject
    )

    res = MaritimePtoBerthBiofoulWasteEngine.run_all(pto, berth, biofoul, waste)
    assert res.overall_status == "CRITICAL_ACTION_REQUIRED"
    assert len(res.critical_alerts) >= 3


def test_cli_commands() -> None:
    app = build_app()

    # English commands
    res1 = runner.invoke(app, ["shaftpto", "evaluate", "--vessel-id", "V-101", "--power-kw", "1000.0"])
    assert res1.exit_code == 0
    assert "Shaft PTO/PTI Hybrid Evaluation" in res1.stdout

    res2 = runner.invoke(app, ["berthalloc", "evaluate", "--vessel", "Cai Mep Max", "--moves", "800"])
    assert res2.exit_code == 0
    assert "Berth & Crane Allocation" in res2.stdout

    res3 = runner.invoke(app, ["biofoul", "evaluate", "--vessel-id", "V-103", "--lof", "2"])
    assert res3.exit_code == 0
    assert "Biofouling & In-Water Cleaning Report" in res3.stdout

    res4 = runner.invoke(app, ["wasteoil", "evaluate", "--batch-id", "B-104", "--flash", "65.0"])
    assert res4.exit_code == 0
    assert "Circular Waste Oil Co-Processing" in res4.stdout

    # Vietnamese aliases
    res1_vn = runner.invoke(app, ["mayphattruc", "evaluate", "--vessel-id", "V-VN1"])
    assert res1_vn.exit_code == 0
    assert "Shaft PTO/PTI Hybrid Evaluation" in res1_vn.stdout

    res2_vn = runner.invoke(app, ["dieudocauport", "evaluate", "--vessel", "V-VN2"])
    assert res2_vn.exit_code == 0
    assert "Berth & Crane Allocation" in res2_vn.stdout

    res3_vn = runner.invoke(app, ["sambanhabien", "evaluate", "--vessel-id", "V-VN3"])
    assert res3_vn.exit_code == 0
    assert "Biofouling & In-Water Cleaning Report" in res3_vn.stdout

    res4_vn = runner.invoke(app, ["dauthaicang", "evaluate", "--batch-id", "B-VN4"])
    assert res4_vn.exit_code == 0
    assert "Circular Waste Oil Co-Processing" in res4_vn.stdout


@pytest.mark.asyncio
async def test_mcp_server_endpoints() -> None:
    from scripts.mcp_server import (
        mekong_maritime_berth_crane_evaluate,
        mekong_maritime_biofouling_evaluate,
        mekong_maritime_shaft_pto_evaluate,
        mekong_maritime_waste_oil_evaluate,
    )

    r_pto = await mekong_maritime_shaft_pto_evaluate(vessel_id="M-PTO", power_kw=1000.0)
    assert r_pto["active_mode"] == "PTO"
    assert r_pto["is_pto_permitted"] is True

    r_berth = await mekong_maritime_berth_crane_evaluate(vessel_name="M-BERTH", container_moves=600)
    assert r_berth["status"] == "APPROVED"

    r_bio = await mekong_maritime_biofouling_evaluate(vessel_id="M-BIO", lof=1)
    assert r_bio["permission"] == "GROOMING_ALLOWED"

    r_waste = await mekong_maritime_waste_oil_evaluate(batch_id="M-WASTE", flash_point_c=65.0)
    assert r_waste["is_safe_to_receive"] is True
