# -*- coding: utf-8 -*-
"""Comprehensive Test Suite for Phases 259-262.

Phases Covered:
- Phase 259: Bareboat Charter Registry & Temporary Flag Suspension Under VMC 2015 & Decree 171/2016
- Phase 260: Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015 & Brussels 1910
- Phase 261: Tokyo MOU PSC Ship Risk Profile (SRP) & CIC Inspection Engine
- Phase 262: Seaport Reefer Container Power Tariff & Temperature Monitoring Under Circular 39/2023
"""

import ast
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.maritime_flag_collision_psc_reefer_engine import (
    BareboatRegistryType,
    BareboatRegistrationApplication,
    BareboatRegistrationEngine,
    CollisionDamageProfile,
    CollisionLiabilityBothToBlameEngine,
    FlagPerformanceTier,
    ROPerformanceTier,
    CompanyPerformanceTier,
    PSCHistoryData,
    TokyoMOUPSCInspectionEngine,
    CargoThermalClass,
    PortReeferMonitoringEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_bareboat_registration_evaluate,
    handle_collision_settlement_evaluate,
    handle_tokyo_mou_psc_evaluate,
    handle_port_reefer_monitoring_evaluate,
)


# ==============================================================================
# 1. ZERO-DEPENDENCY AST ARCHITECTURAL INVARIANT TEST
# ==============================================================================

def test_core_engine_zero_dependencies():
    """Verify that core engine imports only Python standard library modules."""
    engine_path = Path("/Users/macbook/mekong-cli/src/core/maritime_flag_collision_psc_reefer_engine.py")
    assert engine_path.exists(), "Engine file must exist"

    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])

    stdlib_modules = {
        "__future__",
        "dataclasses",
        "enum",
        "math",
        "typing",
        "json",
        "datetime",
        "sys",
        "os",
    }
    invalid_imports = imported_modules - stdlib_modules
    assert not invalid_imports, f"Core engine has external dependencies: {invalid_imports}"


# ==============================================================================
# 2. PHASE 259: BAREBOAT CHARTER REGISTRY TESTS
# ==============================================================================

def test_bareboat_in_eligible_standard():
    """Verify standard eligible bareboat-in application."""
    app = BareboatRegistrationApplication(
        vessel_name="MV_PACIFIC_CHARTERER",
        imo_number="9283741",
        registry_type=BareboatRegistryType.BAREBOAT_IN,
        charter_start_date="2026-01-01",
        charter_end_date="2028-12-31",
        charterer_entity_name="VINASHIP CORP",
        disponent_owner_country="PANAMA",
        original_flag_state="PANAMA",
        has_temporary_flag_suspension_cert=True,
        total_crew_members=20,
        vietnamese_officers_count=8,
        vietnamese_ratings_count=10,
        gross_tonnage=28000.0,
        built_year=2015,
    )
    rep = BareboatRegistrationEngine.evaluate_registration(app, reference_year=2026)
    assert rep.eligible_for_registry is True
    assert rep.vietnamese_crew_ratio_pct == 90.0  # (8+10)/20 = 90%
    assert rep.vietnamese_officers_ratio_pct == 80.0  # 8 / (20 // 2) = 80%
    assert rep.max_registration_duration_days == 1095  # 3 years
    assert "HỢP LỆ" in rep.statutory_compliance_status
    assert rep.registration_fee_vnd == 8000000.0  # 10,000-30,000 GT tier


def test_bareboat_in_ineligible_no_suspension():
    """Verify rejection when flag suspension certificate is missing (prohibits dual flag)."""
    app = BareboatRegistrationApplication(
        vessel_name="MV_ILLEGAL_FLAG",
        imo_number="9112233",
        registry_type=BareboatRegistryType.BAREBOAT_IN,
        charter_start_date="2026-01-01",
        charter_end_date="2027-01-01",
        charterer_entity_name="TEST SHIP",
        disponent_owner_country="LIBERIA",
        original_flag_state="LIBERIA",
        has_temporary_flag_suspension_cert=False,
        total_crew_members=20,
        vietnamese_officers_count=6,
        vietnamese_ratings_count=10,
        gross_tonnage=15000.0,
        built_year=2018,
    )
    rep = BareboatRegistrationEngine.evaluate_registration(app, reference_year=2026)
    assert rep.eligible_for_registry is False
    assert "THIẾU Giấy chứng nhận tạm đình chỉ" in rep.remarks


def test_bareboat_in_ineligible_overage():
    """Verify rejection when vessel age exceeds 30 years."""
    app = BareboatRegistrationApplication(
        vessel_name="MV_OLD_VESSEL",
        imo_number="8123456",
        registry_type=BareboatRegistryType.BAREBOAT_IN,
        charter_start_date="2026-01-01",
        charter_end_date="2027-01-01",
        charterer_entity_name="TEST SHIP",
        disponent_owner_country="PANAMA",
        original_flag_state="PANAMA",
        has_temporary_flag_suspension_cert=True,
        total_crew_members=20,
        vietnamese_officers_count=8,
        vietnamese_ratings_count=10,
        gross_tonnage=10000.0,
        built_year=1990,  # 36 years in 2026
    )
    rep = BareboatRegistrationEngine.evaluate_registration(app, reference_year=2026)
    assert rep.eligible_for_registry is False
    assert "vượt quá khung cho phép" in rep.remarks


def test_bareboat_in_crew_quota_failure():
    """Verify rejection when Vietnamese crew is under 50%."""
    app = BareboatRegistrationApplication(
        vessel_name="MV_FOREIGN_CREW",
        imo_number="9556677",
        registry_type=BareboatRegistryType.BAREBOAT_IN,
        charter_start_date="2026-01-01",
        charter_end_date="2027-01-01",
        charterer_entity_name="TEST SHIP",
        disponent_owner_country="PANAMA",
        original_flag_state="PANAMA",
        has_temporary_flag_suspension_cert=True,
        total_crew_members=20,
        vietnamese_officers_count=2,
        vietnamese_ratings_count=3,  # 5/20 = 25% < 50%
        gross_tonnage=8000.0,
        built_year=2020,
    )
    rep = BareboatRegistrationEngine.evaluate_registration(app, reference_year=2026)
    assert rep.eligible_for_registry is False
    assert "Tỷ lệ thuyền viên Việt Nam" in rep.remarks


def test_bareboat_out_suspension_certificate():
    """Verify bareboat-out approval issuing flag suspension certificate."""
    app = BareboatRegistrationApplication(
        vessel_name="MV_VIETNAM_PRIDE",
        imo_number="9667788",
        registry_type=BareboatRegistryType.BAREBOAT_OUT,
        charter_start_date="2026-03-01",
        charter_end_date="2028-02-29",
        charterer_entity_name="SINGAPORE CHARTERING PTE",
        disponent_owner_country="VIETNAM",
        original_flag_state="VIETNAM",
        has_temporary_flag_suspension_cert=False,
        total_crew_members=18,
        vietnamese_officers_count=0,
        vietnamese_ratings_count=0,
        gross_tonnage=3500.0,
        built_year=2019,
    )
    rep = BareboatRegistrationEngine.evaluate_registration(app, reference_year=2026)
    assert rep.eligible_for_registry is True
    assert rep.registration_fee_vnd == 5000000.0  # < 10,000 GT tier
    assert "Chấp thuận tạm đình chỉ cờ Việt Nam" in rep.remarks


# ==============================================================================
# 3. PHASE 260: COLLISION CROSS-LIABILITIES & BOTH-TO-BLAME TESTS
# ==============================================================================

def test_collision_settlement_both_to_blame_calculation():
    """Verify single liability netting and Both-to-Blame recovery."""
    dmg_a = CollisionDamageProfile(
        hull_repair_damage_usd=1200000.0,
        loss_of_hire_demurrage_usd=300000.0,
        cargo_loss_onboard_usd=800000.0,
    )
    dmg_b = CollisionDamageProfile(
        hull_repair_damage_usd=600000.0,
        loss_of_hire_demurrage_usd=150000.0,
        cargo_loss_onboard_usd=0.0,
    )

    res = CollisionLiabilityBothToBlameEngine.calculate_collision_settlement(
        vessel_a_name="MV_VIET_SUN",
        vessel_b_name="MV_OCEAN_PRIDE",
        fault_percentage_a=60.0,
        damage_a=dmg_a,
        damage_b=dmg_b,
    )

    assert res.vessel_a_fault_ratio == 0.60
    assert res.vessel_b_fault_ratio == 0.40
    assert res.vessel_a_total_direct_loss_usd == 1500000.0
    assert res.vessel_b_total_direct_loss_usd == 750000.0

    # Liability A to B: 60% of 750k = 450k
    assert res.vessel_a_liability_to_vessel_b_usd == 450000.0
    # Liability B to A: 40% of 1500k = 600k
    assert res.vessel_b_liability_to_vessel_a_usd == 600000.0

    # Netting: B pays A 600k - 450k = 150k
    assert res.single_liability_net_balance_usd == 150000.0
    assert res.paying_vessel == "MV_OCEAN_PRIDE"

    # Cargo on A ($800k) recovers 40% from B ($320k)
    assert res.cargo_claims_against_other_vessel_usd == 320000.0

    # Under Both-to-Blame: B passes 60% of $320k ($192k) to A; A recovers $192k from Cargo A
    assert res.both_to_blame_indemnity_recovery_usd == 192000.0


def test_collision_sole_fault():
    """Verify 100% sole fault collision settlement."""
    dmg_a = CollisionDamageProfile(hull_repair_damage_usd=500000.0)
    dmg_b = CollisionDamageProfile(hull_repair_damage_usd=200000.0)

    res = CollisionLiabilityBothToBlameEngine.calculate_collision_settlement(
        vessel_a_name="SHIP_1",
        vessel_b_name="SHIP_2",
        fault_percentage_a=100.0,
        damage_a=dmg_a,
        damage_b=dmg_b,
    )
    assert res.vessel_a_liability_to_vessel_b_usd == 200000.0
    assert res.vessel_b_liability_to_vessel_a_usd == 0.0
    assert res.single_liability_net_balance_usd == 200000.0
    assert res.paying_vessel == "SHIP_1"
    assert res.both_to_blame_indemnity_recovery_usd == 0.0


# ==============================================================================
# 4. PHASE 261: TOKYO MOU PSC SHIP RISK PROFILE TESTS
# ==============================================================================

def test_tokyo_mou_low_risk_ship():
    """Verify Low Risk Ship (LRS) determination with white flag, high RO, high company."""
    psc_hist = PSCHistoryData(
        inspections_last_36_months=6,
        deficiencies_last_36_months=6,  # 1.0 def/insp < 5.0
        detentions_last_36_months=0,
    )
    res = TokyoMOUPSCInspectionEngine.calculate_ship_risk_profile(
        vessel_name="MV_SAFE_STAR",
        imo_number="9888888",
        ship_type="container",
        vessel_age=5,
        flag_status=FlagPerformanceTier.WHITE_LIST,
        ro_performance=ROPerformanceTier.HIGH,
        company_performance=CompanyPerformanceTier.HIGH,
        psc_history=psc_hist,
    )
    assert res.risk_profile_grade.value == "LRS"
    assert res.total_risk_weighting_points <= 0
    assert "9 - 18 tháng" in res.inspection_priority_window_months
    assert res.is_subject_to_expanded_inspection is False


def test_tokyo_mou_high_risk_ship():
    """Verify High Risk Ship (HRS) triggers for black flag, detentions, and old age."""
    psc_hist = PSCHistoryData(
        inspections_last_36_months=4,
        deficiencies_last_36_months=28,  # 7.0 def/insp >= 5.0 (+2 points)
        detentions_last_36_months=2,     # 2 * 3 = +6 points
    )
    res = TokyoMOUPSCInspectionEngine.calculate_ship_risk_profile(
        vessel_name="MV_RUSTY_BUCKET",
        imo_number="8999999",
        ship_type="oil_tanker",          # High risk type (+2 points)
        vessel_age=22,                   # Age > 20 (+2 points)
        flag_status=FlagPerformanceTier.BLACK_LIST,    # Black list (+4 points)
        ro_performance=ROPerformanceTier.LOW,          # Low RO (+2 points)
        company_performance=CompanyPerformanceTier.LOW, # Low company (+2 points)
        psc_history=psc_hist,
    )
    assert res.risk_profile_grade.value == "HRS"
    assert res.total_risk_weighting_points >= 6
    assert "2 - 4 tháng" in res.inspection_priority_window_months
    assert res.is_subject_to_expanded_inspection is True
    assert "RẤT CAO" in res.cic_target_risk_level


# ==============================================================================
# 5. PHASE 262: SEAPORT REEFER MONITORING & ENERGY TARIFF TESTS
# ==============================================================================

def test_reefer_monitoring_frozen_normal():
    """Verify standard frozen container monitoring and energy consumption calculation."""
    res = PortReeferMonitoringEngine.calculate_reefer_service(
        container_id="SEGU-8492014",
        thermal_class=CargoThermalClass.FROZEN,
        setpoint_celsius=-20.0,
        actual_avg_temp_celsius=-19.2,
        plugged_hours=48.0,
        ambient_temp_celsius=34.5,
        electricity_tariff_vnd_kwh=3850.0,
    )
    assert res.temperature_deviation_celsius == pytest.approx(0.8, abs=1e-2)
    assert "AN TOÀN" in res.temperature_excursion_risk
    assert res.cargo_quality_retention_index_pct == 99.5
    assert res.total_power_consumed_kwh > 0.0
    assert res.plug_unplug_service_fee_vnd == 450000.0
    assert res.monitoring_and_log_fee_vnd == (48.0 / 4.0) * 50000.0
    assert res.total_reefer_charges_vnd > res.power_electricity_cost_vnd


def test_reefer_monitoring_temperature_excursion_alarm():
    """Verify high deviation alert and quality index penalty."""
    res = PortReeferMonitoringEngine.calculate_reefer_service(
        container_id="MSCU-1234567",
        thermal_class=CargoThermalClass.CHILLED,
        setpoint_celsius=3.0,
        actual_avg_temp_celsius=7.5,  # Deviation 4.5C > 3.0C
        plugged_hours=24.0,
        ambient_temp_celsius=35.0,
    )
    assert res.temperature_deviation_celsius == pytest.approx(4.5, abs=1e-2)
    assert "NGHIÊM TRỌNG" in res.temperature_excursion_risk
    assert res.cargo_quality_retention_index_pct <= 50.0
    assert "Cần giám định kỹ thuật" in res.remarks


# ==============================================================================
# 6. TYPER CLI SUBCOMMAND INTEGRATION TESTS
# ==============================================================================

def test_cli_bareboat_evaluate():
    """Test 'bareboat evaluate' CLI command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "bareboat", "evaluate",
        "--vessel", "MV_TEST_CLI",
        "--imo", "9912345",
        "--reg-type", "bareboat_in",
        "--gt", "25000",
        "--total-crew", "20",
        "--vn-officers", "8",
        "--vn-ratings", "10",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["vessel_name"] == "MV_TEST_CLI"
    assert data["eligible_for_registry"] is True


def test_cli_collision_settle():
    """Test 'collision settle' CLI command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "collision", "settle",
        "--vessel-a", "SHIP_A",
        "--vessel-b", "SHIP_B",
        "--fault-a", "70",
        "--hull-a", "1000000",
        "--hull-b", "500000",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["vessel_a_fault_ratio"] == 0.70
    assert data["paying_vessel"] in ["SHIP_A", "SHIP_B"]


def test_cli_tokyomou_profile():
    """Test 'tokyomou profile' CLI command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "tokyomou", "profile",
        "--vessel", "MV_PSC_TEST",
        "--imo", "9554433",
        "--type", "bulk_carrier",
        "--age", "10",
        "--flag", "white_list",
        "--ro", "high",
        "--company", "high",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["risk_profile_grade"] in ["LRS", "SRS", "HRS"]


def test_cli_reeferport_monitor():
    """Test 'reeferport monitor' CLI command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "reeferport", "monitor",
        "--container-id", "TCLU-9988776",
        "--thermal", "frozen",
        "--setpoint", "-20.0",
        "--actual-temp", "-19.5",
        "--hours", "36",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["container_id"] == "TCLU-9988776"
    assert data["total_reefer_charges_vnd"] > 0


# ==============================================================================
# 7. MCP SERVER HANDLERS INTEGRATION TESTS
# ==============================================================================

def test_mcp_bareboat_handler():
    """Test MCP handler for bareboat registration."""
    res_str = handle_bareboat_registration_evaluate({
        "vessel_name": "MV_MCP_CHARTER",
        "imo_number": "9332211",
        "registry_type": "bareboat_in",
        "gross_tonnage": 18000.0,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["bareboat_evaluation"]["vessel_name"] == "MV_MCP_CHARTER"


def test_mcp_collision_handler():
    """Test MCP handler for collision settlement."""
    res_str = handle_collision_settlement_evaluate({
        "vessel_a_name": "CARRIER_1",
        "vessel_b_name": "CARRIER_2",
        "fault_percentage_a": 50.0,
        "hull_repair_damage_usd_a": 800000.0,
        "hull_repair_damage_usd_b": 400000.0,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["collision_settlement"]["vessel_a_fault_ratio"] == 0.50


def test_mcp_tokyomou_handler():
    """Test MCP handler for Tokyo MOU PSC evaluation."""
    res_str = handle_tokyo_mou_psc_evaluate({
        "vessel_name": "MV_MOU_VESSEL",
        "imo_number": "9118822",
        "ship_type": "general_cargo",
        "vessel_age": 12,
        "flag_status": "white_list",
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["tokyo_mou_assessment"]["vessel_name"] == "MV_MOU_VESSEL"


def test_mcp_reeferport_handler():
    """Test MCP handler for seaport reefer monitoring."""
    res_str = handle_port_reefer_monitoring_evaluate({
        "container_id": "SEGU-7766554",
        "thermal_class": "frozen",
        "setpoint_celsius": -18.0,
        "actual_avg_temp_celsius": -17.5,
        "plugged_hours": 24.0,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["port_reefer_monitoring"]["container_id"] == "SEGU-7766554"
