"""Comprehensive Test Suite for Maritime SAR, AtoN, Tiered Oil Spill & Dredging Suite (Phases 247-250).

Statutory & Standard References:
- Phase 247: IMO/ICAO IAMSAR Manual Vol. II, SAR Convention 1979, Decision 06/2014/QĐ-TTg & Circular 29/2020/TT-BGTVT (Distress Phases, Drift Error, Sweep Width, POD).
- Phase 248: IALA Buoyage System Region A, IALA Guideline G1078, Circular 47/2023/TT-BGTVT & Vietnam Maritime Code 2015 Arts. 113-120 (AtoN Categories 1-3, Allard's Law, Notice to Mariners).
- Phase 249: Decision 12/2021/QĐ-TTg, MARPOL Annex I, Decree 45/2022/NĐ-CP & Circular 33/2018/TT-BTNMT (Tier 1-3 Classification, Containment Boom, Chemical Dispersants).
- Phase 250: Decree 159/2018/NĐ-CP, Decree 08/2022/NĐ-CP, Circular 35/2019/TT-BGTVT, Law on Sea 2012 & QCVN 43:2017/BTNMT (Channel Infill Geometry, Heavy Metals Class A-C, Sea Dumping).
"""

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from scripts.mcp_server import CORE_HANDLERS
from src.cli.commands.maritime_sar_aton_spill_dredging_command import (
    aton_app,
    dredging_app,
    oilspill_app,
    sar_app,
)
from src.core.maritime_sar_aton_spill_dredging_engine import (
    AtonMaritimeEngine,
    AtonSpecification,
    ChannelDredgingEngine,
    DredgingProjectAssessment,
    IalaCategory,
    IalaMarkType,
    MaritimeSarEngine,
    OilProductClass,
    OilSpillResponsePlan,
    OilSpillTier,
    SarDistressPhase,
    SarOperationPlan,
    SarSearchPattern,
    SearchObjectType,
    SedimentClass,
    TieredOilSpillEngine,
)

runner = CliRunner()


def test_ast_zero_external_dependency_invariant() -> None:
    """Verify that the core maritime engine module maintains zero external dependencies."""
    engine_path = Path("src/core/maritime_sar_aton_spill_dredging_engine.py")
    assert engine_path.exists(), "Engine file must exist"

    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    allowed_standard_modules = {
        "__future__",
        "dataclasses",
        "enum",
        "math",
        "typing",
        "hashlib",
        "datetime",
        "json",
        "re",
        "sys",
        "os",
        "pathlib",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_standard_modules, f"Disallowed import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_standard_modules, f"Disallowed from-import: {node.module}"


# ==============================================================================
# Phase 247: Maritime SAR & IAMSAR Mission Planning
# ==============================================================================

def test_sar_distress_phase_classification() -> None:
    """Verify IAMSAR emergency distress phase transitions (INCERFA, ALERFA, DETRESFA)."""
    # Normal / initial tracking
    phase, notes = MaritimeSarEngine.evaluate_distress_phase(
        communications_lost_minutes=5,
        unreported_delay_minutes=10,
    )
    assert phase == SarDistressPhase.UNCERTAINTY
    assert "chưa đủ căn cứ" in notes

    # INCERFA: delay >= 30 min or comms lost >= 15 min
    phase, notes = MaritimeSarEngine.evaluate_distress_phase(
        communications_lost_minutes=20,
        unreported_delay_minutes=35,
    )
    assert phase == SarDistressPhase.UNCERTAINTY
    assert "INCERFA" in notes

    # ALERFA: delay >= 60 min or comms lost >= 60 min
    phase, notes = MaritimeSarEngine.evaluate_distress_phase(
        communications_lost_minutes=65,
        unreported_delay_minutes=45,
    )
    assert phase == SarDistressPhase.ALERT
    assert "ALERFA" in notes

    # DETRESFA: Mayday / EPIRB / Grave imminent danger
    phase, notes = MaritimeSarEngine.evaluate_distress_phase(
        communications_lost_minutes=10,
        unreported_delay_minutes=10,
        mayday_received=True,
    )
    assert phase == SarDistressPhase.DISTRESS
    assert "DETRESFA" in notes

    phase_epirb, _ = MaritimeSarEngine.evaluate_distress_phase(
        communications_lost_minutes=5,
        unreported_delay_minutes=5,
        epirb_active=True,
    )
    assert phase_epirb == SarDistressPhase.DISTRESS


def test_sar_search_parameters_calculation() -> None:
    """Verify total probable error, search radius, area, sweep width, and POD calculations."""
    plan: SarOperationPlan = MaritimeSarEngine.calculate_search_parameters(
        incident_id="SAR-TS-01",
        phase=SarDistressPhase.DISTRESS,
        target_type=SearchObjectType.LIFE_RAFT_15_25,
        datum_lat=10.50,
        datum_lon=107.20,
        position_error_nm=1.0,
        drift_error_nm=1.5,
        safety_factor=1.3,
        visibility_nm=10.0,
        available_speed_kts=12.0,
        number_of_search_units=1,
    )

    # Total probable error E = sqrt(1.0^2 + 1.5^2) = sqrt(3.25) ~ 1.80277
    # Search radius R = 1.80277 * 1.3 ~ 2.34 NM
    assert 2.30 <= plan.search_radius_nm <= 2.40
    # Search area A = 4 * R^2 = 4 * (2.34^2) ~ 21.90 NM^2
    assert 20.0 <= plan.search_area_sq_nm <= 24.0
    # Baseline sweep width for life raft 15-25 is 2.7 NM at 10 NM visibility
    assert plan.sweep_width_nm == 2.7
    # Coverage factor C = W / S
    assert plan.coverage_factor > 0
    # POD is calculated via exponential formula
    assert 50.0 <= plan.probability_of_detection_pct <= 99.0
    assert plan.required_search_hours > 0
    assert "SAR-TS-01" in plan.operational_summary


def test_sar_patterns_and_multi_unit_scaling() -> None:
    """Verify search pattern selection based on target type, search radius, and fleet size."""
    # Sector Search (VS) for small radius and PIW
    plan_piw = MaritimeSarEngine.calculate_search_parameters(
        incident_id="SAR-PIW",
        phase=SarDistressPhase.DISTRESS,
        target_type=SearchObjectType.PERSON_IN_WATER,
        datum_lat=9.15,
        datum_lon=106.40,
        position_error_nm=0.5,
        drift_error_nm=0.5,
        safety_factor=1.1,
    )
    assert plan_piw.recommended_pattern == SarSearchPattern.SECTOR_SEARCH

    # Parallel Track (PS) for multiple search craft
    plan_multi = MaritimeSarEngine.calculate_search_parameters(
        incident_id="SAR-MULTI",
        phase=SarDistressPhase.DISTRESS,
        target_type=SearchObjectType.VESSEL_OVER_20M,
        datum_lat=11.00,
        datum_lon=109.00,
        position_error_nm=5.0,
        drift_error_nm=6.0,
        number_of_search_units=3,
        available_speed_kts=15.0,
    )
    assert plan_multi.recommended_pattern == SarSearchPattern.PARALLEL_TRACK
    assert plan_multi.search_radius_nm > 10.0


# ==============================================================================
# Phase 248: Aids to Navigation (AtoN) & IALA Buoyage Region A
# ==============================================================================

def test_aton_allards_law_and_ranges() -> None:
    """Verify geographic range formula and Allard's Law luminous range."""
    # Elevation 25m, observer eye 5m
    # D_g = 2.08 * (sqrt(25) + sqrt(5)) = 2.08 * (5.0 + 2.236) = 2.08 * 7.236 ~ 15.05 NM
    geo_range, lum_range = AtonMaritimeEngine.calculate_ranges(
        elevation_m=25.0,
        intensity_candela=10000.0,
        observer_eye_height_m=5.0,
        atmospheric_transmissivity=0.74,
    )
    assert 14.8 <= geo_range <= 15.3
    assert lum_range > 15.0


def test_aton_iala_region_a_specs_and_marks() -> None:
    """Verify IALA Region A visual specifications for all buoyage types."""
    for mark_type in IalaMarkType:
        spec = AtonMaritimeEngine.evaluate_aton_status(
            aton_id=f"ATON-{mark_type.name}",
            name=f"Beacon {mark_type.value}",
            mark_type=mark_type,
            category=IalaCategory.CATEGORY_2,
            elevation_m=12.0,
            intensity_candela=1500.0,
            total_service_hours=8760.0,
            outage_hours=20.0,
        )
        assert spec.color != ""
        assert spec.topmark != ""
        assert spec.light_characteristic != ""

    # Port hand buoy in Region A must be Red
    port_spec = AtonMaritimeEngine.evaluate_aton_status(
        aton_id="PORT-01",
        name="Phao số 2",
        mark_type=IalaMarkType.PORT_HAND,
        category=IalaCategory.CATEGORY_1,
        elevation_m=8.0,
        intensity_candela=1000.0,
    )
    assert "Đỏ" in port_spec.color or "Red" in port_spec.color
    assert "Hình trụ" in port_spec.topmark or "can" in port_spec.topmark


def test_aton_operational_availability_benchmarks() -> None:
    """Verify operational availability target audits and Notice to Mariners triggers."""
    # Cat 1 target >= 99.8%. Outage 8h in 8760h -> 99.909% (Passes)
    spec_cat1_pass: AtonSpecification = AtonMaritimeEngine.evaluate_aton_status(
        aton_id="LH-VUNGTAU",
        name="Hải đăng Vũng Tàu",
        mark_type=IalaMarkType.SAFE_WATER,
        category=IalaCategory.CATEGORY_1,
        elevation_m=170.0,
        intensity_candela=50000.0,
        total_service_hours=8760.0,
        outage_hours=8.0,
    )
    assert spec_cat1_pass.operational_availability_pct >= 99.8
    assert spec_cat1_pass.meets_iala_standard is True

    # Cat 1 target >= 99.8%. Outage 30h in 8760h -> 99.658% (Fails standard -> Notice required)
    spec_cat1_fail: AtonSpecification = AtonMaritimeEngine.evaluate_aton_status(
        aton_id="LH-HONKHOAI",
        name="Hải đăng Hòn Khoai",
        mark_type=IalaMarkType.SAFE_WATER,
        category=IalaCategory.CATEGORY_1,
        elevation_m=318.0,
        intensity_candela=80000.0,
        total_service_hours=8760.0,
        outage_hours=30.0,
    )
    assert spec_cat1_fail.operational_availability_pct < 99.8
    assert spec_cat1_fail.meets_iala_standard is False
    assert spec_cat1_fail.notice_to_mariners_required is True
    assert "KHÔNG ĐẠT CHUẨN" in spec_cat1_fail.remarks


# ==============================================================================
# Phase 249: Tiered Oil Spill Response & Dispersant Compliance
# ==============================================================================

def test_oil_spill_tier_classification() -> None:
    """Verify statutory spill tier classification per Decision 12/2021/QĐ-TTg."""
    # Tier 1: < 20 tons
    tier1 = TieredOilSpillEngine.classify_spill_tier(15.0)
    assert tier1 == OilSpillTier.TIER_1

    # Tier 2: 20 - 100 tons
    tier2 = TieredOilSpillEngine.classify_spill_tier(65.0)
    assert tier2 == OilSpillTier.TIER_2

    # Facility capacity exceeded escalates to Tier 2 even if < 20t
    tier2_escalated = TieredOilSpillEngine.classify_spill_tier(12.0, facility_capacity_exceeded=True)
    assert tier2_escalated == OilSpillTier.TIER_2

    # Tier 3: > 100 tons or transboundary risk
    tier3 = TieredOilSpillEngine.classify_spill_tier(150.0)
    assert tier3 == OilSpillTier.TIER_3

    tier3_transboundary = TieredOilSpillEngine.classify_spill_tier(30.0, transboundary_risk=True)
    assert tier3_transboundary == OilSpillTier.TIER_3


def test_oil_spill_dispersant_chemical_safety_criteria() -> None:
    """Verify dispersant approval barriers: depth >= 20m, distance >= 3 NM, prohibited on light oils & MPAs."""
    # Light distillate -> Prohibited regardless of location
    approved, notes = TieredOilSpillEngine.evaluate_dispersant_application(
        water_depth_m=40.0,
        distance_from_shore_nm=10.0,
        near_marine_protected_area=False,
        near_aquaculture_zone=False,
        product_class=OilProductClass.LIGHT_DISTILLATE,
    )
    assert approved is False
    assert "CẤM SỬ DỤNG CHẤT PHÂN TÁN" in notes
    assert "Dầu nhẹ" in notes

    # Shallow water (< 20m) -> Prohibited
    approved_shallow, notes_shallow = TieredOilSpillEngine.evaluate_dispersant_application(
        water_depth_m=14.0,
        distance_from_shore_nm=5.0,
        near_marine_protected_area=False,
        near_aquaculture_zone=False,
        product_class=OilProductClass.HEAVY_RESIDUAL,
    )
    assert approved_shallow is False
    assert "Độ sâu khu vực" in notes_shallow

    # Close to shore (< 3 NM) -> Prohibited
    approved_near_shore, notes_near = TieredOilSpillEngine.evaluate_dispersant_application(
        water_depth_m=30.0,
        distance_from_shore_nm=2.0,
        near_marine_protected_area=False,
        near_aquaculture_zone=False,
        product_class=OilProductClass.HEAVY_RESIDUAL,
    )
    assert approved_near_shore is False
    assert "Khoảng cách tới bờ" in notes_near

    # Adjacent to MPA or Aquaculture -> Prohibited
    approved_mpa, notes_mpa = TieredOilSpillEngine.evaluate_dispersant_application(
        water_depth_m=35.0,
        distance_from_shore_nm=8.0,
        near_marine_protected_area=True,
        near_aquaculture_zone=False,
        product_class=OilProductClass.HEAVY_RESIDUAL,
    )
    assert approved_mpa is False
    assert "bảo tồn biển" in notes_mpa

    # Valid offshore conditions -> Approved conditionally
    approved_ok, notes_ok = TieredOilSpillEngine.evaluate_dispersant_application(
        water_depth_m=35.0,
        distance_from_shore_nm=8.0,
        near_marine_protected_area=False,
        near_aquaculture_zone=False,
        product_class=OilProductClass.HEAVY_RESIDUAL,
    )
    assert approved_ok is True
    assert "CHẤP THUẬN CÓ ĐIỀU KIỆN" in notes_ok


def test_oil_spill_boom_skimmer_and_sanction() -> None:
    """Verify boom containment length, skimmer recovery derating, and Decree 45 administrative fines."""
    # Vessel LOA 180m -> Boom length >= max(250m, 3 * 180 = 540m) = 540m
    plan: OilSpillResponsePlan = TieredOilSpillEngine.evaluate_spill_incident(
        incident_id="SPILL-VT-01",
        spill_volume_tons=75.0,
        product_class=OilProductClass.HEAVY_RESIDUAL,
        vessel_loa_m=180.0,
        water_depth_m=32.0,
        distance_from_shore_nm=6.0,
        delayed_reporting=True,
    )
    assert plan.tier == OilSpillTier.TIER_2
    assert plan.required_response_time_hours == 2.0
    assert plan.min_containment_boom_m == 540.0
    assert plan.min_skimmer_capacity_m3_h > 0
    assert plan.statutory_fine_vnd == 550_000_000.0  # 450M base + 100M delay
    assert len(plan.remedial_measures) >= 4


# ==============================================================================
# Phase 250: Navigation Channel Dredging & Sea Dumping Licensing
# ==============================================================================

def test_channel_dredging_volume_geometry() -> None:
    """Verify 3-component dredging volume calculations (infill, side slopes, overdepth)."""
    # L=3000m, W=100m, design=-12.0m CD, surveyed=-10.0m CD -> delta_h = 2.0m
    # side slope m=3, allowable overdepth = 0.5m
    assessment: DredgingProjectAssessment = ChannelDredgingEngine.calculate_dredging_volumes_and_licensing(
        project_id="DRG-01",
        channel_name="Luồng Định An - Cần Thơ",
        dredge_length_m=3000.0,
        design_bottom_width_m=100.0,
        design_depth_cd_m=-12.0,
        surveyed_depth_cd_m=-10.0,
        side_slope_ratio=3.0,
        allowable_overdepth_m=0.5,
    )

    assert assessment.siltation_depth_m == 2.0
    # Infill: 3000 * 100 * 2.0 = 600,000 m3
    assert assessment.infill_volume_m3 == 600_000.0
    # Slope: 3000 * 3.0 * (2.0^2) = 36,000 m3
    assert assessment.side_slope_volume_m3 == 36_000.0
    # Overdepth: overdepth_width = 100 + 2*3*2 = 112m -> 3000 * 112 * 0.5 = 168,000 m3
    assert assessment.allowable_overdepth_volume_m3 == 168_000.0
    # Total = 600,000 + 36,000 + 168,000 = 804,000 m3
    assert assessment.total_dredge_volume_m3 == 804_000.0
    assert assessment.estimated_dredging_cost_vnd == 804_000.0 * 115_000.0
    assert assessment.environmental_deposit_vnd == round(assessment.estimated_dredging_cost_vnd * 0.05, 0)


def test_qcvn43_marine_sediment_classification() -> None:
    """Verify sediment classification under QCVN 43:2017/BTNMT thresholds."""
    # Clean sediment (Class A)
    clean_metals = {
        "arsenic": 15.0,
        "cadmium": 1.0,
        "lead": 30.0,
        "mercury": 0.2,
        "copper": 40.0,
        "zinc": 80.0,
    }
    sed_class, notes = ChannelDredgingEngine.evaluate_sediment_quality(clean_metals)
    assert sed_class == SedimentClass.CLASS_A_CLEAN
    assert "Đủ điều kiện cấp phép" in notes

    # Marginal sediment (Class B: >= 85% limit)
    # Cadmium limit is 4.2 -> 3.8 is ~90%
    marginal_metals = {
        "arsenic": 15.0,
        "cadmium": 3.8,
        "lead": 30.0,
        "mercury": 0.2,
        "copper": 40.0,
        "zinc": 80.0,
    }
    sed_b, notes_b = ChannelDredgingEngine.evaluate_sediment_quality(marginal_metals)
    assert sed_b == SedimentClass.CLASS_B_RESTRICTED
    assert "tiệm cận ngưỡng" in notes_b

    # Contaminated sediment (Class C: exceeding limit)
    # Mercury limit is 0.70 -> 1.2 is exceeded
    toxic_metals = {
        "arsenic": 15.0,
        "cadmium": 1.0,
        "lead": 30.0,
        "mercury": 1.2,
        "copper": 40.0,
        "zinc": 80.0,
    }
    sed_c, notes_c = ChannelDredgingEngine.evaluate_sediment_quality(toxic_metals)
    assert sed_c == SedimentClass.CLASS_C_CONTAMINATED
    assert "CẤM NHẬN CHÌM Ở BIỂN" in notes_c


def test_sea_dumping_licensing_criteria_and_fees() -> None:
    """Verify Law on Sea dumping prerequisites and licensing eligibility."""
    # Ineligible because contaminated sediment
    toxic_metals = {"arsenic": 80.0}  # limit is 41.6
    assess_fail = ChannelDredgingEngine.calculate_dredging_volumes_and_licensing(
        project_id="DRG-FAIL",
        channel_name="Luồng Cửa Tiểu",
        dredge_length_m=1000.0,
        design_bottom_width_m=80.0,
        design_depth_cd_m=-8.0,
        surveyed_depth_cd_m=-7.0,
        heavy_metals_mg_kg=toxic_metals,
        dumping_distance_nm=10.0,
        dumping_depth_m=25.0,
        buffer_from_mpa_nm=10.0,
    )
    assert assess_fail.sea_dumping_eligible is False
    assert assess_fail.sediment_class == SedimentClass.CLASS_C_CONTAMINATED

    # Ineligible because too close to shore (< 6 NM)
    assess_near = ChannelDredgingEngine.calculate_dredging_volumes_and_licensing(
        project_id="DRG-NEAR",
        channel_name="Luồng Quy Nhơn",
        dredge_length_m=1000.0,
        design_bottom_width_m=80.0,
        design_depth_cd_m=-10.0,
        surveyed_depth_cd_m=-9.0,
        dumping_distance_nm=4.0,  # < 6.0 NM
        dumping_depth_m=25.0,
        buffer_from_mpa_nm=10.0,
    )
    assert assess_near.sea_dumping_eligible is False

    # Fully compliant
    assess_ok = ChannelDredgingEngine.calculate_dredging_volumes_and_licensing(
        project_id="DRG-PASS",
        channel_name="Luồng Vũng Tàu - Thị Vải",
        dredge_length_m=2000.0,
        design_bottom_width_m=150.0,
        design_depth_cd_m=-14.0,
        surveyed_depth_cd_m=-12.5,
        dumping_distance_nm=15.0,
        dumping_depth_m=30.0,
        buffer_from_mpa_nm=12.0,
    )
    assert assess_ok.sea_dumping_eligible is True
    assert assess_ok.sediment_class == SedimentClass.CLASS_A_CLEAN


# ==============================================================================
# CLI Commands Integration Tests
# ==============================================================================

def test_cli_sar_command() -> None:
    """Verify Typer CLI 'sar' command with JSON and table formats."""
    res_plan = runner.invoke(sar_app, [
        "--id", "SAR-CLI-01",
        "--phase", "alert",
        "--target", "craft_under_9m",
        "--lat", "10.2",
        "--lon", "107.1",
        "--json",
    ])
    assert res_plan.exit_code == 0
    data = json.loads(res_plan.output)
    assert data["incident_id"] == "SAR-CLI-01"
    assert data["search_radius_nm"] > 0
    assert data["recommended_pattern"] != ""

    # Test table output
    res_table = runner.invoke(sar_app, [
        "--id", "SAR-CLI-02",
        "--phase", "distress",
    ])
    assert res_table.exit_code == 0
    assert "Kế hoạch Tìm kiếm Cứu nạn IAMSAR" in res_table.output


def test_cli_aton_command() -> None:
    """Verify Typer CLI 'aton' command with JSON and table formats."""
    res_audit = runner.invoke(aton_app, [
        "--id", "ATON-CLI-01",
        "--name", "Phao so 0",
        "--cat", "1",
        "--elevation", "15.0",
        "--intensity", "2000.0",
        "--outage", "5.0",
        "--json",
    ])
    assert res_audit.exit_code == 0
    data = json.loads(res_audit.output)
    assert data["aton_id"] == "ATON-CLI-01"
    assert data["meets_iala_standard"] is True

    # Test table output
    res_table = runner.invoke(aton_app, [
        "--id", "ATON-CLI-02",
        "--name", "Phao so 2",
    ])
    assert res_table.exit_code == 0
    assert "Đánh giá Báo hiệu Hàng hải" in res_table.output


def test_cli_oilspill_command() -> None:
    """Verify Typer CLI 'oilspill' command with JSON and table formats."""
    res_plan = runner.invoke(oilspill_app, [
        "--id", "SPILL-CLI-01",
        "--volume", "85.0",
        "--product", "heavy_residual",
        "--loa", "160.0",
        "--json",
    ])
    assert res_plan.exit_code == 0
    data = json.loads(res_plan.output)
    assert data["tier"] == "tier_2"
    assert data["min_containment_boom_m"] == 480.0

    # Test table output
    res_table = runner.invoke(oilspill_app, [
        "--id", "SPILL-CLI-02",
        "--volume", "15.0",
    ])
    assert res_table.exit_code == 0
    assert "Kế hoạch Ứng phó Sự cố Tràn dầu" in res_table.output


def test_cli_channeldredge_command() -> None:
    """Verify Typer CLI 'dredging' command with JSON and table formats."""
    res_assess = runner.invoke(dredging_app, [
        "--id", "DRG-CLI-01",
        "--channel", "Soai Rap",
        "--length", "4000.0",
        "--width", "120.0",
        "--des-depth", "-12.0",
        "--surv-depth", "-10.0",
        "--json",
    ])
    assert res_assess.exit_code == 0
    data = json.loads(res_assess.output)
    assert data["project_id"] == "DRG-CLI-01"
    assert data["siltation_depth_m"] == 2.0
    assert data["total_dredge_volume_m3"] > 0

    # Test table output
    res_table = runner.invoke(dredging_app, [
        "--id", "DRG-CLI-02",
        "--channel", "Dinh An",
    ])
    assert res_table.exit_code == 0
    assert "Đánh giá Nạo vét Luồng" in res_table.output


# ==============================================================================
# FastMCP Handlers Integration Tests
# ==============================================================================

def test_mcp_handlers_sar_aton_spill_dredging() -> None:
    """Verify that all 4 MCP tool handlers produce conforming JSON responses."""
    # 1. SAR tool
    sar_handler = CORE_HANDLERS["mekong_maritime_sar_plan"]
    res_sar_raw = sar_handler({
        "incident_id": "SAR-MCP-01",
        "phase": "distress",
        "target_type": "life_raft_15_25",
        "datum_lat": 10.3,
        "datum_lon": 107.1,
    })
    res_sar = json.loads(res_sar_raw)
    assert res_sar["ok"] is True
    assert res_sar["sar_plan"]["incident_id"] == "SAR-MCP-01"

    # 2. AtoN tool
    aton_handler = CORE_HANDLERS["mekong_aton_status_audit"]
    res_aton_raw = aton_handler({
        "aton_id": "ATON-MCP-01",
        "name": "Beacon North",
        "mark_type": "cardinal_north",
        "category": 2,
    })
    res_aton = json.loads(res_aton_raw)
    assert res_aton["ok"] is True
    assert res_aton["aton_audit"]["aton_id"] == "ATON-MCP-01"

    # 3. Oil spill tool
    spill_handler = CORE_HANDLERS["mekong_oil_spill_response_plan"]
    res_spill_raw = spill_handler({
        "incident_id": "SPILL-MCP-01",
        "spill_volume_tons": 50.0,
        "product_class": "heavy_residual",
    })
    res_spill = json.loads(res_spill_raw)
    assert res_spill["ok"] is True
    assert res_spill["oil_spill_plan"]["tier"] == "tier_2"

    # 4. Dredging assessment tool
    dredge_handler = CORE_HANDLERS["mekong_channel_dredging_assessment"]
    res_drg_raw = dredge_handler({
        "project_id": "DRG-MCP-01",
        "channel_name": "Song Hau",
        "dredge_length_m": 2500.0,
    })
    res_drg = json.loads(res_drg_raw)
    assert res_drg["ok"] is True
    assert res_drg["dredging_assessment"]["total_dredge_volume_m3"] > 0
