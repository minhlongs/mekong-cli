"""
Unit & Integration Test Suite for Phases 267-270 Maritime Compliance & Operations Suite.
Covers:
- Phase 267: Time Charterparty Speed & Consumption Warranty Assessment (NYPE 93/2015, The Didymi, The Gas Enterprise)
- Phase 268: Electronic Delivery Order (e-D/O) & Container Deposit Settlement
- Phase 269: Seaport Tonnage Dues, Maritime Safety & Anchorage Tariffs (Circular 39/2023/TT-BGTVT)
- Phase 270: IMDG Dangerous Goods Seaport Handling, Segregation Matrix (Table 7.2.4) & Safety Rules
"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_charterparty_edo_tonnage_imdg_engine import (
    CharterpartyPerformanceEngine,
    WarrantedTerms,
    PassageLegData,
    LiabilityParty,
    ElectronicDeliveryOrderEngine,
    ContainerDepositParams,
    ContainerCategory,
    EDOStatus,
    SeaportTonnageTariffEngine,
    VesselPortCallData,
    VoyageType,
    PortMaritimeZone,
    IMDGSafetyHandlingEngine,
    IMDGClass,
    SegregationRequirement,
    PortHandlingMode,
)
from src.cli.app_setup import build_app
import scripts.mcp_server as mcp_server


# ============================================================================
# 1. Zero External Dependencies Verification (AST Analysis)
# ============================================================================

def test_core_engine_zero_dependencies():
    """Verify core engine imports only Python standard library."""
    engine_path = "src/core/maritime_charterparty_edo_tonnage_imdg_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    std_lib_modules = {
        "dataclasses", "datetime", "enum", "math", "typing", "json", "sys", "os"
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                assert root_module in std_lib_modules, f"Non-standard import found: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                assert root_module in std_lib_modules, f"Non-standard import-from found: {node.module}"


# ============================================================================
# 2. Phase 267: Charterparty Speed & Consumption Warranty Engine Tests
# ============================================================================

def test_charterparty_underperformance_owners_liable():
    """Test vessel failing speed warranty with financial claim against Owner."""
    warranties = WarrantedTerms(
        warranted_speed_knots=14.0,       # Effective: 14.0 - 0.5 = 13.5 kts
        warranted_fuel_tonnes_day=30.0,   # Effective: 30.0 * 1.05 = 31.5 t/day
        daily_hire_rate_usd=20000.0,
        vlsfo_price_per_tonne_usd=600.0,
    )
    passage = PassageLegData(
        leg_name="Leg 1 Singapore to Hai Phong",
        total_distance_nm=3240.0,
        steaming_hours_total=270.0,       # Actual speed ~12.0 kts
        good_weather_hours=100.0,
        good_weather_distance_nm=1200.0,  # GW speed 12.0 kts < 13.5 kts (underperforming)
        actual_fuel_consumed_tonnes=360.0,
        current_factor_knots=0.0,
    )

    result = CharterpartyPerformanceEngine.evaluate_passage(warranties, passage)

    assert result.is_underperforming_in_good_weather is True
    assert result.warranted_net_speed_knots == 13.5
    assert result.allowed_steaming_hours == 240.0  # 3240 / 13.5
    assert result.net_time_lost_hours == 30.0     # 270 - 240
    assert result.net_time_lost_days == 1.25
    assert result.time_loss_financial_claim_usd == 25000.0  # 1.25 * 20000
    assert result.liability_determination == LiabilityParty.OWNERS_LIABLE
    assert result.net_total_claim_usd > 0


def test_charterparty_bunker_saving_offsets_time_loss():
    """Test The Gas Enterprise doctrine where fuel saving offsets time lost."""
    warranties = WarrantedTerms(
        warranted_speed_knots=14.0,
        warranted_fuel_tonnes_day=40.0,
        daily_hire_rate_usd=10000.0,
        vlsfo_price_per_tonne_usd=800.0,
    )
    passage = PassageLegData(
        leg_name="Leg 2",
        total_distance_nm=1350.0,
        steaming_hours_total=105.0,  # Slightly slow
        good_weather_hours=50.0,
        good_weather_distance_nm=650.0,  # 13.0 kts < 13.5 kts
        actual_fuel_consumed_tonnes=100.0, # Large fuel savings compared to allowed ~175t
    )

    result = CharterpartyPerformanceEngine.evaluate_passage(warranties, passage)

    assert result.is_underperforming_in_good_weather is True
    assert result.fuel_variance_tonnes < 0.0  # Bunker saving
    assert result.liability_determination == LiabilityParty.CHARTERERS_OFFSET


def test_charterparty_zero_hours_raises_value_error():
    """Test validation rejecting zero or negative steaming hours."""
    warranties = WarrantedTerms(warranted_speed_knots=13.0, warranted_fuel_tonnes_day=25.0)
    passage = PassageLegData(
        leg_name="Invalid",
        total_distance_nm=1000.0,
        steaming_hours_total=0.0,
        good_weather_hours=0.0,
        good_weather_distance_nm=0.0,
        actual_fuel_consumed_tonnes=50.0,
    )
    with pytest.raises(ValueError):
        CharterpartyPerformanceEngine.evaluate_passage(warranties, passage)


# ============================================================================
# 3. Phase 268: Electronic Delivery Order (e-D/O) & Container Deposit Tests
# ============================================================================

def test_edo_deposit_settlement_on_time_full_refund():
    """Test returning container within free time yields full refund."""
    params = ContainerDepositParams(
        category=ContainerCategory.DRY_20FT,
        unit_count=3,
        deposit_per_unit_vnd=2000000.0,
        free_days_allowed=7,
        actual_days_to_return=5,  # within free time
        daily_detention_rate_vnd=200000.0,
        iicl_damage_repair_vnd=0.0,
        container_cleaning_fee_vnd=0.0,
    )

    result = ElectronicDeliveryOrderEngine.calculate_deposit_settlement("BL123", "EDO-001", params)

    assert result.total_deposit_held_vnd == 6000000.0
    assert result.overdue_days == 0
    assert result.total_deductions_vnd == 0.0
    assert result.net_refund_payable_vnd == 6000000.0
    assert result.additional_balance_due_vnd == 0.0
    assert result.status == EDOStatus.DEPOSIT_REFUNDED


def test_edo_deposit_settlement_with_detention_and_repair():
    """Test partial refund after deductions for detention and IICL repairs."""
    params = ContainerDepositParams(
        category=ContainerCategory.DRY_40FT,
        unit_count=1,
        deposit_per_unit_vnd=4000000.0,
        free_days_allowed=5,
        actual_days_to_return=8,  # 3 days overdue
        daily_detention_rate_vnd=300000.0,
        iicl_damage_repair_vnd=800000.0,
        container_cleaning_fee_vnd=300000.0,
    )

    result = ElectronicDeliveryOrderEngine.calculate_deposit_settlement("BL456", "EDO-002", params)

    assert result.overdue_days == 3
    assert result.detention_charge_total_vnd == 900000.0  # 3 * 300,000
    assert result.repair_deduction_total_vnd == 800000.0
    assert result.cleaning_deduction_total_vnd == 300000.0
    assert result.total_deductions_vnd == 2000000.0
    assert result.net_refund_payable_vnd == 2000000.0     # 4,000,000 - 2,000,000
    assert result.additional_balance_due_vnd == 0.0


def test_edo_deposit_depleted_additional_charge_due():
    """Test heavy damage and long detention exceeding deposit."""
    params = ContainerDepositParams(
        category=ContainerCategory.REEFER_40FT,
        unit_count=1,
        deposit_per_unit_vnd=5000000.0,
        free_days_allowed=3,
        actual_days_to_return=13,  # 10 days overdue
        daily_detention_rate_vnd=800000.0,
        iicl_damage_repair_vnd=2500000.0,
    )

    result = ElectronicDeliveryOrderEngine.calculate_deposit_settlement("BL789", "EDO-003", params)

    assert result.detention_charge_total_vnd == 8000000.0
    assert result.total_deductions_vnd == 10500000.0
    assert result.net_refund_payable_vnd == 0.0
    assert result.additional_balance_due_vnd == 5500000.0
    assert result.status == EDOStatus.DISPUTED_OVERDUE


# ============================================================================
# 4. Phase 269: Seaport Tonnage Dues & Maritime Safety Tariffs Tests
# ============================================================================

def test_seaport_tonnage_dues_international_voyage():
    """Test statutory international port charges under Circular 39/2023."""
    call_data = VesselPortCallData(
        vessel_gross_tonnage_gt=30000.0,
        voyage_type=VoyageType.INTERNATIONAL,
        port_zone=PortMaritimeZone.ZONE_III_SOUTH,
        number_of_port_calls=1,
        anchorage_hours=20.0,
        has_green_award_certificate=False,
    )

    result = SeaportTonnageTariffEngine.calculate_dues(call_data)

    assert result.currency == "USD"
    # Tonnage: 30000 * 0.034 * 2 = 2040.0
    assert result.tonnage_dues_entry_exit_total == 2040.0
    # Safety: 30000 * 0.076 * 2 = 4560.0
    assert result.maritime_safety_dues_total == 4560.0
    # Anchorage: 30000 * 0.0005 * 20 = 300.0
    assert result.anchorage_fairway_dues_total == 300.0
    assert result.grand_total_port_dues == 6900.0


def test_seaport_tonnage_dues_green_award_discount():
    """Test 10% discount applied to tonnage and safety dues for green vessel."""
    call_data = VesselPortCallData(
        vessel_gross_tonnage_gt=20000.0,
        voyage_type=VoyageType.INTERNATIONAL,
        port_zone=PortMaritimeZone.ZONE_I_NORTH,
        number_of_port_calls=1,
        anchorage_hours=0.0,
        has_green_award_certificate=True,
    )

    result = SeaportTonnageTariffEngine.calculate_dues(call_data)

    base_tonnage_safety = (20000.0 * 0.034 * 2) + (20000.0 * 0.076 * 2) # 1360 + 3040 = 4400.0
    expected_discount = base_tonnage_safety * 0.10                       # 440.0
    assert result.green_discount_amount == expected_discount
    assert result.grand_total_port_dues == 4400.0 - 440.0


def test_seaport_tonnage_dues_domestic_voyage():
    """Test domestic voyage calculations in VND."""
    call_data = VesselPortCallData(
        vessel_gross_tonnage_gt=5000.0,
        voyage_type=VoyageType.DOMESTIC,
        port_zone=PortMaritimeZone.ZONE_II_CENTRAL,
        number_of_port_calls=1,
        anchorage_hours=12.0,
    )

    result = SeaportTonnageTariffEngine.calculate_dues(call_data)

    assert result.currency == "VND"
    # Tonnage: 5000 * 350 * 2 = 3,500,000 VND
    assert result.tonnage_dues_entry_exit_total == 3500000.0
    # Safety: 5000 * 1000 * 2 = 10,000,000 VND
    assert result.maritime_safety_dues_total == 10000000.0
    # Anchorage: 5000 * 20 * 12 = 1,200,000 VND
    assert result.anchorage_fairway_dues_total == 1200000.0
    assert result.grand_total_port_dues == 14700000.0


# ============================================================================
# 5. Phase 270: IMDG Dangerous Goods Handling & Segregation Tests
# ============================================================================

def test_imdg_class_1_mandatory_direct_delivery():
    """Test Class 1 Explosives strictly mandate direct delivery with 2h dock dwell."""
    result = IMDGSafetyHandlingEngine.evaluate_cargo_handling(
        primary_class=IMDGClass.CLASS_1_EXPLOSIVES,
    )

    assert result.port_handling_mode == PortHandlingMode.DIRECT_DELIVERY_MANDATORY
    assert result.max_dockside_dwell_hours == 2.0
    assert result.port_handling_surcharge_percent == 200.0


def test_imdg_table_segregation_class_1_and_class_3():
    """Test Table 7.2.4 segregation code 4 (longitudinal) between Class 1 & 3."""
    result = IMDGSafetyHandlingEngine.evaluate_cargo_handling(
        primary_class=IMDGClass.CLASS_1_EXPLOSIVES,
        secondary_class=IMDGClass.CLASS_3_FLAMMABLE_LIQUID,
    )

    assert result.segregation_code == 4
    assert result.segregation_requirement == SegregationRequirement.SEPARATED_LONGITUDINALLY
    assert result.minimum_buffer_distance_meters == 24.0


def test_imdg_class_3_flammable_liquids_hazmat_yard():
    """Test Class 3 requires dedicated hazmat yard with buffer."""
    result = IMDGSafetyHandlingEngine.evaluate_cargo_handling(
        primary_class=IMDGClass.CLASS_3_FLAMMABLE_LIQUID,
        secondary_class=IMDGClass.CLASS_8_CORROSIVE,
    )

    assert result.port_handling_mode == PortHandlingMode.DEDICATED_HAZMAT_YARD
    assert result.segregation_code == 1
    assert result.segregation_requirement == SegregationRequirement.AWAY_FROM
    assert result.minimum_buffer_distance_meters == 3.0
    assert result.port_handling_surcharge_percent == 100.0


# ============================================================================
# 6. Typer CLI Runner Verification
# ============================================================================

def test_cli_charterparty_evaluate():
    """Test CLI command 'charterpartyspeed evaluate'."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["charterpartyspeed", "evaluate", "--speed", "14.0", "--hours", "260.0"])
    assert res.exit_code == 0
    assert "BÁO CÁO ĐÁNH GIÁ THỰC HIỆN HỢP ĐỒNG THUÊ TÀU ĐỊNH HẠN" in res.stdout


def test_cli_edorelease_settle():
    """Test CLI command 'edorelease settle'."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["edorelease", "settle", "--units", "2", "--deposit", "2000000"])
    assert res.exit_code == 0
    assert "QUYẾT TOÁN CƯỢC VỎ CONTAINER" in res.stdout


def test_cli_tonnagedues_calculate():
    """Test CLI command 'tonnagedues calculate'."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["tonnagedues", "calculate", "--gt", "10000", "--voyage", "INTERNATIONAL"])
    assert res.exit_code == 0
    assert "BIỂU PHÍ TRỌNG TẢI & BẢO ĐẢM HÀNG HẢI CẢNG BIỂN" in res.stdout


def test_cli_imdgport_evaluate():
    """Test CLI command 'imdgport evaluate'."""
    runner = CliRunner()
    app = build_app()
    res = runner.invoke(app, ["imdgport", "evaluate", "--class", "CLASS_3_FLAMMABLE_LIQUID"])
    assert res.exit_code == 0
    assert "ĐÁNH GIÁ AN TOÀN & CÁCH LY HÀNG NGUY HIỂM IMDG" in res.stdout


# ============================================================================
# 7. FastMCP Handlers Integration Verification
# ============================================================================

def test_mcp_charterparty_speed_handler():
    """Verify MCP handler handle_charterparty_speed_consumption_evaluate."""
    raw = mcp_server.handle_charterparty_speed_consumption_evaluate({
        "warranted_speed_knots": 13.5,
        "warranted_fuel_tonnes_day": 28.0,
        "total_distance_nm": 3200.0,
        "steaming_hours_total": 250.0,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert "charterparty_claim" in data


def test_mcp_edo_deposit_settlement_handler():
    """Verify MCP handler handle_edo_deposit_settlement_calculate."""
    raw = mcp_server.handle_edo_deposit_settlement_calculate({
        "bl_number": "TESTBL123",
        "edo_reference": "EDO-001",
        "unit_count": 2,
        "deposit_per_unit_vnd": 2000000.0,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["deposit_settlement"]["net_refund_payable_vnd"] > 0


def test_mcp_seaport_tonnage_safety_dues_handler():
    """Verify MCP handler handle_seaport_tonnage_safety_dues_calculate."""
    raw = mcp_server.handle_seaport_tonnage_safety_dues_calculate({
        "vessel_gross_tonnage_gt": 15000.0,
        "voyage_type": "INTERNATIONAL",
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["port_dues"]["grand_total_port_dues"] > 0


def test_mcp_imdg_port_safety_handling_handler():
    """Verify MCP handler handle_imdg_port_safety_handling_evaluate."""
    raw = mcp_server.handle_imdg_port_safety_handling_evaluate({
        "primary_class": "CLASS_1_EXPLOSIVES",
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["imdg_handling"]["port_handling_mode"] == "DIRECT_DELIVERY_MANDATORY"
