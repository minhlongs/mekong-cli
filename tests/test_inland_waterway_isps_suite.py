"""Comprehensive test suite for Phases 187-190:
- Phase 187: Vietnam Inland Waterway Navigation & Bridge Clearance (Luật ĐTNĐ 2004/2014 & TT 46/2016/TT-BGTVT)
- Phase 188: Container Feeder Barging & Mekong Transit Freight (TT 39/2023/TT-BGTVT & TT 248/2016/TT-BTC)
- Phase 189: Maritime Search & Rescue (SAR) & Wreck Removal (NĐ 05/2017/NĐ-CP & IAMSAR Manual)
- Phase 190: Port Facility & Ship Security (ISPS Code & NĐ 159/2018/NĐ-CP)

Verifies:
1. Pure Python standard library AST zero-external-dependency invariants.
2. Inland Waterway bridge air clearance and Under Keel Clearance (UKC) evaluation.
3. Feeder barging tariffs, DG cargo surcharges, and TT 248 port dues.
4. IAMSAR sea surface drift vectors, search box area, and Decree 05 wreck removal statutory limits.
5. ISPS Code security levels, effective tier determination, and Declaration of Security (DoS) rules.
6. Typer CLI commands execution and --json outputs.
7. FastMCP tool handlers execution and json response contracts.
"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.inland_waterway_isps_engine import (
    WaterwayClass,
    FeederBargeRoute,
    SARRegion,
    ISPSLevel,
    InlandWaterwayNavEngine,
    FeederBargingFreightEngine,
    MaritimeSARWreckEngine,
    PortFacilitySecurityISPSEngine,
)
from src.cli.commands.inland_waterway_isps_command import (
    waterway_app,
    barge_app,
    sar_app,
    isps_app,
)
from scripts.mcp_server import (
    handle_inland_waterway_clearance,
    handle_barge_freight,
    handle_sar_datum,
    handle_sar_wreck,
    handle_isps_compliance,
)

runner = CliRunner()


# ===========================================================================
# 1. Zero External Dependency & AST Invariant Tests
# ===========================================================================


def test_core_engine_zero_external_dependencies():
    """Verify that src/core/inland_waterway_isps_engine.py only imports from the Python standard library."""
    with open("src/core/inland_waterway_isps_engine.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    allowed_stdlib = {"dataclasses", "datetime", "enum", "math", "typing", "json"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_stdlib, f"Unauthorized external import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_stdlib, f"Unauthorized external from-import: {node.module}"


# ===========================================================================
# 2. Phase 187: Inland Waterway Navigation Engine Tests
# ===========================================================================


def test_waterway_clearance_safe_transit():
    """Test safe waterway clearance where air draft and UKC meet all statutory buffers."""
    res = InlandWaterwayNavEngine.evaluate_clearance(
        vessel_name="Barge SG-9988",
        waterway_class=WaterwayClass.CLASS_I,
        bridge_name="Binh Loi Bridge",
        bridge_air_draft_m=11.0,
        vessel_air_draft_m=8.5,
        channel_depth_m=4.5,
        vessel_draft_m=3.0,
    )

    assert res.vessel_name == "Barge SG-9988"
    assert res.waterway_class == WaterwayClass.CLASS_I
    assert res.net_air_clearance_m == 2.50
    assert res.is_air_draft_safe is True
    assert res.under_keel_clearance_m == 1.50
    assert res.is_ukc_safe is True
    assert res.can_transit is True
    assert any("Clearance verified safe" in note for note in res.restriction_notes)


def test_waterway_clearance_air_draft_breach():
    """Test unsafe air draft (air clearance < 0.50m margin) causing transit prohibition."""
    res = InlandWaterwayNavEngine.evaluate_clearance(
        vessel_name="Barge SG-7721",
        waterway_class=WaterwayClass.CLASS_II,
        bridge_name="Dong Nai Bridge",
        bridge_air_draft_m=7.0,
        vessel_air_draft_m=6.8,  # Net margin 0.20m < 0.50m
        channel_depth_m=3.5,
        vessel_draft_m=2.5,
    )

    assert res.net_air_clearance_m == 0.20
    assert res.is_air_draft_safe is False
    assert res.is_ukc_safe is True
    assert res.can_transit is False
    assert any("Air clearance 0.2m is below safety margin" in note for note in res.restriction_notes)


def test_waterway_clearance_ukc_grounding_risk():
    """Test insufficient Under Keel Clearance (< 0.30m) triggering grounding risk."""
    res = InlandWaterwayNavEngine.evaluate_clearance(
        vessel_name="Barge CT-1029",
        waterway_class=WaterwayClass.CLASS_III,
        bridge_name="Can Tho Waterway Span",
        bridge_air_draft_m=12.0,
        vessel_air_draft_m=6.0,
        channel_depth_m=2.2,
        vessel_draft_m=2.0,  # UKC 0.20m < 0.30m
    )

    assert res.under_keel_clearance_m == 0.20
    assert res.is_air_draft_safe is True
    assert res.is_ukc_safe is False
    assert res.can_transit is False
    assert any("Under Keel Clearance 0.2m is below minimum required UKC" in note for note in res.restriction_notes)


# ===========================================================================
# 3. Phase 188: Container Feeder Barging Freight Engine Tests
# ===========================================================================


def test_feeder_barge_freight_standard_hcm_cai_mep():
    """Test standard feeder barging from HCM to Cai Mep without DG cargo."""
    res = FeederBargingFreightEngine.calculate_freight(
        route=FeederBargeRoute.HCM_CAI_MEP,
        teu_count=50,
        feu_count=10,
        dg_containers_count=0,
        barge_dwt_tonnage=2000.0,
    )

    # Base freight: 50 * 1,800,000 + 10 * 3,200,000 = 90,000,000 + 32,000,000 = 122,000,000 VND
    assert res.base_freight_vnd == 122_000_000.0
    assert res.dg_surcharge_vnd == 0.0
    # Port dues: (2000 * 150) + 50,000 = 350,000 VND
    assert res.waterway_port_dues_vnd == 350_000.0
    assert res.cross_border_mekong_fee_vnd == 0.0
    assert res.total_barging_cost_vnd == 122_350_000.0
    assert res.total_barging_cost_usd == 4894.00
    assert res.transit_hours_estimated == 4.5


def test_feeder_barge_freight_with_dg_cargo():
    """Test feeder barging with DG containers receiving +10% surcharge."""
    res = FeederBargingFreightEngine.calculate_freight(
        route=FeederBargeRoute.MEKONG_DELTA_CAI_MEP,
        teu_count=20,
        feu_count=10,
        dg_containers_count=6,
        barge_dwt_tonnage=1500.0,
    )

    # Base: (20 * 3,500,000) + (10 * 6,200,000) = 70,000,000 + 62,000,000 = 132,000,000 VND
    assert res.base_freight_vnd == 132_000_000.0
    # Avg per box: 132M / 30 = 4,400,000 VND
    # DG Surcharge: 6 * 4,400,000 * 10% = 2,640,000 VND
    assert res.dg_surcharge_vnd == 2_640_000.0
    # Port dues: (1500 * 150) + 50,000 = 275,000 VND
    assert res.waterway_port_dues_vnd == 275_000.0
    assert res.total_barging_cost_vnd == 134_915_000.0


def test_feeder_barge_cross_border_mekong_treaty():
    """Test cross-border HCM - Phnom Penh barge route including 2.5M VND treaty fee."""
    res = FeederBargingFreightEngine.calculate_freight(
        route=FeederBargeRoute.HCM_PHNOM_PENH,
        teu_count=10,
        feu_count=5,
        dg_containers_count=0,
        barge_dwt_tonnage=1000.0,
    )

    assert res.cross_border_mekong_fee_vnd == 2_500_000.0
    assert res.transit_hours_estimated == 32.0
    # Base: 10 * 8.5M + 5 * 15M = 85M + 75M = 160M VND
    assert res.base_freight_vnd == 160_000_000.0
    # Dues: 1000 * 150 + 50,000 = 200,000 VND
    assert res.total_barging_cost_vnd == 162_700_000.0


# ===========================================================================
# 4. Phase 189: Maritime SAR & Wreck Removal Engine Tests
# ===========================================================================


def test_maritime_sar_datum_drift_calculation():
    """Test IAMSAR datum drift position and rectangular search area box."""
    res = MaritimeSARWreckEngine.calculate_sar_datum(
        incident_id="SAR-2026-VT01",
        sar_region=SARRegion.REGION_III,
        initial_lat=10.25,
        initial_lon=107.05,
        drift_hours=4.0,
        water_current_speed_knots=1.5,
        water_current_direction_deg=210.0,
        wind_speed_knots=15.0,
        wind_direction_deg=45.0,
    )

    assert res.incident_id == "SAR-2026-VT01"
    assert res.sar_region == SARRegion.REGION_III
    assert res.primary_sar_base == "Vung Tau SAR Base (SAR 413 / SAR 272)"
    assert res.search_radius_nm > 5.0
    assert res.search_box_area_sq_nm == round((2 * res.search_radius_nm) ** 2, 2)
    assert 9.5 < res.datum_lat < 10.5
    assert 106.5 < res.datum_lon < 107.5


def test_wreck_removal_within_statutory_window():
    """Test wreck removal within 30-day statutory window (Decree 05/2017/NĐ-CP)."""
    res = MaritimeSARWreckEngine.assess_wreck_removal(
        vessel_name="MV THAI HUNG 28",
        sinking_date_iso="2026-10-01",
        assessment_date_iso="2026-10-10",
    )

    assert res.days_elapsed == 9
    assert res.statutory_plan_deadline_days == 30
    assert res.days_remaining_for_plan == 21
    assert res.is_deadline_breached is False
    assert res.port_authority_forced_removal is False
    assert res.maritime_lien_enforceable is False
    assert res.action_order == "SHIPOWNER_SUBMIT_SALVAGE_PLAN"


def test_wreck_removal_deadline_breached():
    """Test wreck removal when 30-day statutory deadline is breached."""
    res = MaritimeSARWreckEngine.assess_wreck_removal(
        vessel_name="MV PHU MY 09",
        sinking_date_iso="2026-08-01",
        assessment_date_iso="2026-09-15",
    )

    assert res.days_elapsed == 45
    assert res.days_remaining_for_plan == 0
    assert res.is_deadline_breached is True
    assert res.port_authority_forced_removal is True
    assert res.maritime_lien_enforceable is True
    assert res.action_order == "PORT_AUTHORITY_MANDATORY_FORCED_REMOVAL"


# ===========================================================================
# 5. Phase 190: ISPS Port & Ship Security Engine Tests
# ===========================================================================


def test_isps_security_level_1_both_normal():
    """Test ISPS evaluation where both port facility and ship are Level 1."""
    res = PortFacilitySecurityISPSEngine.evaluate_security_compliance(
        facility_name="Cai Mep International Terminal",
        port_isps_level=ISPSLevel.LEVEL_1,
        vessel_name="MV MAERSK HANOI",
        ship_isps_level=ISPSLevel.LEVEL_1,
    )

    assert res.effective_operational_level == ISPSLevel.LEVEL_1
    assert res.is_declaration_of_security_required is False
    assert "Standard ID check" in res.access_control_rule


def test_isps_security_level_difference_triggers_mandatory_dos():
    """Test that level mismatch (e.g. Port L1 vs Ship L2) triggers mandatory DoS."""
    res = PortFacilitySecurityISPSEngine.evaluate_security_compliance(
        facility_name="Tan Cang Cat Lai",
        port_isps_level=ISPSLevel.LEVEL_1,
        vessel_name="MV COSCO SAIGON",
        ship_isps_level=ISPSLevel.LEVEL_2,
    )

    # Effective operational level is max(L1, L2) = L2
    assert res.effective_operational_level == ISPSLevel.LEVEL_2
    assert res.is_declaration_of_security_required is True
    assert "100% photo ID inspection" in res.access_control_rule


def test_isps_security_level_3_crisis():
    """Test ISPS Level 3 exceptional risk emergency response."""
    res = PortFacilitySecurityISPSEngine.evaluate_security_compliance(
        facility_name="Lach Huyen Deepsea Terminal",
        port_isps_level=ISPSLevel.LEVEL_3,
        vessel_name="MV EVERGREEN BLUE",
        ship_isps_level=ISPSLevel.LEVEL_2,
    )

    assert res.effective_operational_level == ISPSLevel.LEVEL_3
    assert res.is_declaration_of_security_required is True
    assert "SUSPENDED" in res.cargo_handling_supervision
    assert any("National Security / Coast Guard" in m for m in res.mandatory_security_measures)


# ===========================================================================
# 6. Typer CLI Commands Execution Tests
# ===========================================================================


def test_cli_waterway_clearance():
    """Test waterway clearance CLI command with text and JSON output."""
    result = runner.invoke(waterway_app, ["clearance", "Barge-VN01", "--bridge-air", "12.0", "--vessel-air", "9.0"])
    assert result.exit_code == 0
    assert "Inland Waterway Clearance Assessment" in result.output
    assert "PERMITTED" in result.output

    # JSON test
    json_result = runner.invoke(waterway_app, ["clearance", "Barge-VN01", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert data["vessel_name"] == "Barge-VN01"
    assert "can_transit" in data


def test_cli_barge_freight():
    """Test container feeder barging freight CLI command."""
    result = runner.invoke(barge_app, ["freight", "HCM_CAI_MEP", "--teu", "40", "--feu", "10", "--dg", "2"])
    assert result.exit_code == 0
    assert "Container Feeder Barging Freight" in result.output
    assert "VND" in result.output

    # JSON test
    json_result = runner.invoke(barge_app, ["freight", "HCM_CAI_MEP", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert data["route"] == "HCM_CAI_MEP"
    assert data["total_barging_cost_vnd"] > 0


def test_cli_sar_datum_and_wreck():
    """Test SAR datum box calculation and wreck removal CLI commands."""
    res_datum = runner.invoke(sar_app, ["datum", "SAR-999", "--region", "REGION_III"])
    assert res_datum.exit_code == 0
    assert "Maritime SAR Datum & Search Box" in res_datum.output

    res_wreck = runner.invoke(sar_app, ["wreck", "MV SUNKEN 01", "--sinking-date", "2026-10-01", "--assess-date", "2026-10-05"])
    assert res_wreck.exit_code == 0
    assert "Wreck Removal Statutory Assessment" in res_wreck.output
    assert "VALID" in res_wreck.output


def test_cli_waterway_standards_and_barge_routes():
    """Test secondary utility commands for standards, routes, and security levels."""
    res_std = runner.invoke(waterway_app, ["standards"])
    assert res_std.exit_code == 0
    assert "Inland Waterway Classification Standards" in res_std.output

    res_routes = runner.invoke(barge_app, ["routes"])
    assert res_routes.exit_code == 0
    assert "Feeder Barging Routes & Benchmark Tariffs" in res_routes.output
    assert "HCM_CAI_MEP" in res_routes.output

    res_levels = runner.invoke(isps_app, ["levels"])
    assert res_levels.exit_code == 0
    assert "ISPS Code Security Levels" in res_levels.output


def test_cli_isps_compliance():
    """Test ISPS port facility & ship security compliance CLI command."""
    result = runner.invoke(isps_app, ["compliance", "Cai Mep Terminal", "--vessel", "MV PACIFIC", "--ship-level", "LEVEL_2"])
    assert result.exit_code == 0
    assert "ISPS Port Facility & Ship Security Evaluation" in result.output
    assert "MANDATORY REQUIRED" in result.output


# ===========================================================================
# 7. FastMCP Tool Handlers Tests
# ===========================================================================


def test_mcp_inland_waterway_clearance_handler():
    """Test FastMCP tool handler for inland waterway clearance."""
    payload = {
        "vessel_name": "Barge SG-100",
        "waterway_class": "CLASS_I",
        "bridge_name": "Binh Loi Bridge",
        "bridge_air_draft_m": 10.0,
        "vessel_air_draft_m": 8.0,
        "channel_depth_m": 4.5,
        "vessel_draft_m": 3.0,
    }
    raw = handle_inland_waterway_clearance(payload)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["can_transit"] is True
    assert res["net_air_clearance_m"] == 2.0


def test_mcp_barge_freight_handler():
    """Test FastMCP tool handler for barge freight."""
    payload = {
        "route": "HCM_CAI_MEP",
        "teu_count": 50,
        "feu_count": 10,
        "dg_containers_count": 2,
        "barge_dwt_tonnage": 2000.0,
    }
    raw = handle_barge_freight(payload)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["total_barging_cost_vnd"] > 0
    assert res["dg_surcharge_vnd"] > 0


def test_mcp_sar_datum_and_wreck_handlers():
    """Test FastMCP tool handlers for SAR datum and wreck removal."""
    raw_datum = handle_sar_datum({
        "incident_id": "SAR-MCP-01",
        "sar_region": "REGION_II",
        "initial_lat": 16.05,
        "initial_lon": 108.25,
    })
    res_datum = json.loads(raw_datum)
    assert res_datum["ok"] is True
    assert "Da Nang" in res_datum["primary_sar_base"]

    raw_wreck = handle_sar_wreck({
        "vessel_name": "MV WRECK 02",
        "sinking_date_iso": "2026-08-01",
        "assessment_date_iso": "2026-09-10",
    })
    res_wreck = json.loads(raw_wreck)
    assert res_wreck["ok"] is True
    assert res_wreck["is_deadline_breached"] is True


def test_mcp_isps_compliance_handler():
    """Test FastMCP tool handler for ISPS security compliance."""
    raw = handle_isps_compliance({
        "facility_name": "Hai Phong Port",
        "port_isps_level": "LEVEL_1",
        "vessel_name": "MV PACIFIC VOYAGER",
        "ship_isps_level": "LEVEL_1",
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["effective_operational_level"] == "LEVEL_1"
    assert res["is_declaration_of_security_required"] is False
