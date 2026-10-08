"""Automated Test Suite for Maritime Dangerous Cargo, Tugboat Escort, Berthage & Channel Clearance Suite (Phases 231-234).

Covers:
- Phase 231: Dangerous Cargo Terminal Handling & Yard Segregation (Decree 58/2017, Decree 34/2024, IMDG Amdt 41-22)
- Phase 232: Seaport Tugboat Towage Escort & Minimum Bollard Pull Allocation (Circular 39/2023/TT-BGTVT)
- Phase 233: Port Berthage / Anchorage Tariffs & Mooring Services (Circular 39/2023, Circular 12/2024)
- Phase 234: Maritime Safety Inspection, Under-Keel Clearance & Fairway Clearance (VMC 2015 Arts. 88-102, PIANC WG 121)
- AST Zero-External-Dependency Verification
- CLI Typer command execution & JSON outputs
- FastMCP tool handler tests
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_hazardous_tug_berth_clearance_engine import (
    DangerousCargoTerminalEngine,
    IMDGClass,
    DangerousGoodsOperationType,
    TugboatTowageEscortEngine,
    BerthageAndMooringTariffEngine,
    VesselTradeType,
    BerthUsageMode,
    ChannelClearanceAndSafetyInspectionEngine,
    ChannelType,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_dangerous_cargo_validate,
    handle_tugboat_towage_evaluate,
    handle_berthage_mooring_calculate,
    handle_channel_clearance_evaluate,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================
def test_ast_zero_external_dependency_invariant():
    """Verify engine relies purely on Python standard library modules."""
    engine_path = "src/core/maritime_hazardous_tug_berth_clearance_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    allowed_stdlib = {"dataclasses", "enum", "math", "typing", "json", "re", "hashlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Unauthorized external import: {base_pkg}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Unauthorized external importFrom: {base_pkg}"


# ===========================================================================
# 2. Phase 231: Dangerous Cargo Terminal Handling & Segregation Tests
# ===========================================================================
def test_phase231_direct_discharge_class1_within_limit():
    """Class 1 explosives direct discharge under 2 hours is approved."""
    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=IMDGClass.CLASS_1_EXPLOSIVES,
        un_number="UN0004",
        operation_type=DangerousGoodsOperationType.DIRECT_DISCHARGE_TRUCK,
        dwell_hours=1.5,
        buffer_distance_meters=60.0,
        containment_capacity_liters=30000.0,
    )
    assert res.is_compliant is True
    assert res.requires_direct_discharge is True
    assert res.is_yard_storage_allowed is False
    assert len(res.violations) == 0


def test_phase231_direct_discharge_class1_exceeded_hours():
    """Class 1 explosives direct discharge exceeding 2.0 hours is rejected."""
    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=IMDGClass.CLASS_1_EXPLOSIVES,
        un_number="UN0004",
        operation_type=DangerousGoodsOperationType.DIRECT_DISCHARGE_TRUCK,
        dwell_hours=2.5,
        buffer_distance_meters=60.0,
        containment_capacity_liters=30000.0,
    )
    assert res.is_compliant is False
    assert any("2.0h" in v for v in res.violations)


def test_phase231_prohibited_yard_storage_explosives():
    """Attempting yard storage for Class 1 explosives triggers critical violation."""
    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=IMDGClass.CLASS_1_EXPLOSIVES,
        un_number="UN0004",
        operation_type=DangerousGoodsOperationType.YARD_STORAGE_IMPORT,
        dwell_hours=5.0,
    )
    assert res.is_compliant is False
    assert res.is_yard_storage_allowed is False
    assert any("strictly barred from terminal container yards" in v for v in res.violations)


def test_phase231_yard_storage_general_dwell_exceeded():
    """Import cargo dwelling > 48h exceeds Decree 34/2024 limits."""
    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=IMDGClass.CLASS_3_FLAMMABLE_LIQUIDS,
        un_number="UN1203",
        operation_type=DangerousGoodsOperationType.YARD_STORAGE_IMPORT,
        dwell_hours=50.0,
        buffer_distance_meters=55.0,
        containment_capacity_liters=30000.0,
    )
    assert res.is_compliant is False
    assert any("48.0h" in v for v in res.violations)


def test_phase231_buffer_and_containment_breach():
    """Buffer distance < 50m and sump capacity < 26,000L fail statutory rules."""
    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=IMDGClass.CLASS_3_FLAMMABLE_LIQUIDS,
        un_number="UN1203",
        operation_type=DangerousGoodsOperationType.YARD_STORAGE_IMPORT,
        dwell_hours=24.0,
        buffer_distance_meters=40.0,
        containment_capacity_liters=20000.0,
    )
    assert res.is_compliant is False
    assert any("50.0m" in v for v in res.violations)
    assert any("26000L" in v for v in res.violations)


def test_phase231_imdg_segregation_separated_from():
    """Class 3 (Flammable) vs Class 5.1 (Oxidizing) requires 'Separated from' (2 bays / 2 rows)."""
    # Compliant spacing: 2 bays, 2 rows
    res_pass = DangerousCargoTerminalEngine.check_yard_segregation(
        class_a=IMDGClass.CLASS_3_FLAMMABLE_LIQUIDS,
        class_b=IMDGClass.CLASS_5_1_OXIDIZERS,
        actual_bay_gap=2,
        actual_row_gap=2,
    )
    assert res_pass.is_compatible is True
    assert res_pass.required_bay_separation == 2
    assert res_pass.required_row_separation == 2

    # Non-compliant: 1 bay, 1 row
    res_fail = DangerousCargoTerminalEngine.check_yard_segregation(
        class_a=IMDGClass.CLASS_3_FLAMMABLE_LIQUIDS,
        class_b=IMDGClass.CLASS_5_1_OXIDIZERS,
        actual_bay_gap=1,
        actual_row_gap=1,
    )
    assert res_fail.is_compatible is False


# ===========================================================================
# 3. Phase 232: Seaport Tugboat Towage Escort Tests
# ===========================================================================
def test_phase232_tugboat_allocation_tiers():
    """Verify statutory allocation lookup for various LOA and GT brackets."""
    # Tier 0: Small (< 80m or < 2,000 GT)
    t0 = TugboatTowageEscortEngine.get_statutory_allocation(75.0, 1800.0)
    assert t0.min_tug_count == 0
    assert t0.min_total_bollard_pull_tonnes == 0.0

    # Tier 2: 115m - 150m
    t2 = TugboatTowageEscortEngine.get_statutory_allocation(140.0, 12000.0)
    assert t2.min_tug_count == 1
    assert t2.min_total_bollard_pull_tonnes == 40.0
    assert t2.min_bollard_pull_per_tug_tonnes == 30.0

    # Tier 6: Ultra-large (> 250m)
    t6 = TugboatTowageEscortEngine.get_statutory_allocation(366.0, 140000.0)
    assert t6.min_tug_count == 3
    assert t6.recommended_tug_count == 4
    assert t6.min_total_bollard_pull_tonnes == 200.0
    assert t6.min_bollard_pull_per_tug_tonnes == 60.0


def test_phase232_tugboat_safety_evaluation_pass():
    """Tug allocation meeting BP and calm weather passes."""
    res = TugboatTowageEscortEngine.evaluate_towage_operation(
        loa_meters=185.0,
        gross_tonnage=28000.0,
        allocated_tugs_bp=[45.0, 45.0],
        wind_speed_mps=7.0,
        current_speed_knots=1.5,
        visibility_nm=2.0,
        is_channel_escort=True,
        is_night_operation=True,
    )
    assert res.is_safe_to_operate is True
    assert res.allocated_tug_count == 2
    assert res.allocated_total_bp_tonnes == 90.0
    assert res.weather_abort_triggered is False
    assert res.surcharge_pct_total == 70.0  # +40% escort + 30% night


def test_phase232_tugboat_insufficient_bp():
    """Tug allocation below minimum bollard pull fails."""
    res = TugboatTowageEscortEngine.evaluate_towage_operation(
        loa_meters=185.0,
        gross_tonnage=28000.0,
        allocated_tugs_bp=[30.0, 30.0],  # 60T total, required is 90T for LOA 185m
        wind_speed_mps=8.0,
        current_speed_knots=1.5,
        visibility_nm=2.0,
    )
    assert res.is_safe_to_operate is False
    assert res.is_bp_sufficient is False
    assert any("Bollard Pull" in r for r in res.operational_warnings)


def test_phase232_tugboat_weather_cutoff():
    """Weather exceeding wind speed 12 m/s aborts towage without override."""
    res = TugboatTowageEscortEngine.evaluate_towage_operation(
        loa_meters=185.0,
        gross_tonnage=28000.0,
        allocated_tugs_bp=[45.0, 45.0],
        wind_speed_mps=14.0,  # Limit is 12 m/s
        current_speed_knots=1.5,
        visibility_nm=2.0,
    )
    assert res.is_safe_to_operate is False
    assert res.weather_abort_triggered is True
    assert any("Wind speed" in r for r in res.operational_warnings)


# ===========================================================================
# 4. Phase 233: Port Berthage / Anchorage & Mooring Tariff Tests
# ===========================================================================
def test_phase233_international_cargo_berthage():
    """Calculate international cargo berthage: 25,000 GT * 24h * 0.0033 USD."""
    res = BerthageAndMooringTariffEngine.calculate_berthage(
        gross_tonnage=25000.0,
        duration_hours=24.0,
        trade_type=VesselTradeType.INTERNATIONAL,
        usage_mode=BerthUsageMode.CARGO_OPERATIONS,
    )
    assert res.base_amount == 1980.0
    assert res.overstay_penalty_amount == 0.0
    assert res.total_berthage_amount == 1980.0
    assert res.currency == "USD"


def test_phase233_berthage_overstay_penalty():
    """Unauthorized overstay incurs 200% penalty tariff."""
    res = BerthageAndMooringTariffEngine.calculate_berthage(
        gross_tonnage=10000.0,
        duration_hours=10.0,
        trade_type=VesselTradeType.DOMESTIC,
        usage_mode=BerthUsageMode.UNAUTHORIZED_OVERSTAY,
    )
    # Rate = 25 * 3 = 75 VND
    # Base amount = 10h * 10,000 GT * 75 = 7,500,000 VND
    # Overstay penalty = 10h * 10,000 GT * 50 = 5,000,000 VND
    assert res.base_amount == 7500000.0
    assert res.overstay_penalty_amount == 5000000.0
    assert res.total_berthage_amount == 7500000.0
    assert res.currency == "VND"


def test_phase233_mooring_service_night_and_holiday():
    """Mooring service for 15,000 GT international vessel with night (+40%) and holiday (+100%)."""
    # Tier: 10,000 - 20,000 GT -> 80.0 USD
    # Operations: 2 -> Base 160.0 USD
    # Surcharges: +40% (64 USD) + 100% (160 USD) = 224 USD
    # Total: 160.0 + 224.0 = 384.0 USD
    res = BerthageAndMooringTariffEngine.calculate_mooring_service(
        gross_tonnage=15000.0,
        operations_count=2,
        trade_type=VesselTradeType.INTERNATIONAL,
        is_night=True,
        is_holiday=True,
    )
    assert res.base_tariff_per_turn == 80.0
    assert res.night_surcharge_amount == 64.0
    assert res.holiday_surcharge_amount == 160.0
    assert res.total_mooring_amount == 384.0


# ===========================================================================
# 5. Phase 234: Maritime Safety Inspection, UKC & Clearance Refusal Tests
# ===========================================================================
def test_phase234_dynamic_ukc_calculation():
    """Verify hydrodynamic squat and dynamic UKC equation in confined fairway."""
    # Chart depth: 14.0m, Tide: 2.0m, Sounding err: 0.1m -> Fairway depth: 15.9m
    # Static draft: 12.0m, Speed: 8.0 kts, Cb: 0.8, Salinity: 1.015, Wave: 0.3m
    # Squat = 2.0 * 0.8 * (64 / 100) = 1.024m
    # Salinity sinkage = 12.0 * (1.025 - 1.015) / 1.025 = 0.117m
    # Total dynamic draft = 12.0 + 1.024 + 0.117 + 0.3 = 13.441m
    # Net UKC = 15.9 - 13.441 = 2.459m
    # Required min UKC = max(10% of 12.0 = 1.2m, 0.5m) = 1.2m
    res = ChannelClearanceAndSafetyInspectionEngine.calculate_dynamic_ukc(
        chart_depth_meters=14.0,
        tide_height_meters=2.0,
        static_draft_meters=12.0,
        speed_knots=8.0,
        block_coefficient=0.8,
        water_density_g_cm3=1.015,
        wave_heave_meters=0.3,
        channel_type=ChannelType.CONFINED_RIVER,
        sounding_error_meters=0.1,
    )
    assert res.squat_sinkage_meters == 1.024
    assert res.is_safe is True
    assert res.dynamic_ukc_meters > res.minimum_required_ukc_meters


def test_phase234_air_draft_clearance():
    """Air draft clearance with safe margin and unsafe margin."""
    # Safe: Structure 50m, Mast above keel 40m, dynamic draft 10m -> Air draft 30m. Clearance 20m >= 2.0m
    res_safe = ChannelClearanceAndSafetyInspectionEngine.calculate_air_draft_clearance(
        structure_height_hat_meters=50.0,
        mast_height_above_keel_meters=40.0,
        dynamic_draft_meters=10.0,
        tide_height_meters=0.0,
    )
    assert res_safe.is_safe is True
    assert res_safe.actual_clearance_meters >= 2.0

    # Unsafe: Structure 30m, Mast above keel 40m, dynamic draft 12m -> Air draft 28m. Clearance 2m - 1m tide = 1m (< 2.0m)
    res_unsafe = ChannelClearanceAndSafetyInspectionEngine.calculate_air_draft_clearance(
        structure_height_hat_meters=30.0,
        mast_height_above_keel_meters=40.0,
        dynamic_draft_meters=12.0,
        tide_height_meters=1.0,
    )
    assert res_unsafe.is_safe is False
    assert len(res_unsafe.violations) > 0


def test_phase234_port_clearance_refusal_grounds():
    """VMC Art. 101 refusal grounds trigger detention order."""
    res_clean = ChannelClearanceAndSafetyInspectionEngine.evaluate_clearance_refusal(
        vessel_name="MV MEKONG PRIDE",
        imo_number="IMO9876543",
    )
    assert res_clean.clearance_granted is True
    assert len(res_clean.triggered_grounds) == 0

    res_detained = ChannelClearanceAndSafetyInspectionEngine.evaluate_clearance_refusal(
        vessel_name="MV RISK RUNNER",
        imo_number="IMO9123456",
        court_ship_arrest_order=True,
        unpaid_port_dues_or_fines=True,
    )
    assert res_detained.clearance_granted is False
    assert len(res_detained.triggered_grounds) == 2
    assert res_detained.detention_hash != ""


# ===========================================================================
# 6. CLI Typer Execution Tests
# ===========================================================================
def test_cli_dangerous_cargo_validate():
    """Test CLI dangerouscargo validate command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "dangerouscargo", "validate",
        "-c", "1",
        "--un", "UN0004",
        "-o", "direct_discharge_truck",
        "-d", "1.5",
        "--json",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["is_compliant"] is True
    assert payload["requires_direct_discharge"] is True


def test_cli_tugboat_escort_evaluate():
    """Test CLI tugescort evaluate command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "tugescort", "evaluate",
        "--loa", "185.0",
        "--gt", "28000.0",
        "--tugs-bp", "45,45",
        "--wind", "7.0",
        "--json",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["is_safe_to_operate"] is True
    assert payload["allocated_tug_count"] == 2


def test_cli_berth_mooring_calculate():
    """Test CLI berthmooring berthage command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "berthmooring", "berthage",
        "--gt", "25000.0",
        "-h", "24.0",
        "--trade", "international",
        "--json",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["base_amount"] == 1980.0


def test_cli_channel_clearance_ukc():
    """Test CLI channelclearance ukc command."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "channelclearance", "ukc",
        "-cd", "14.0",
        "-t", "2.0",
        "-d", "12.0",
        "-v", "8.0",
        "--json",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["is_safe"] is True


# ===========================================================================
# 7. FastMCP Tool Handler Tests
# ===========================================================================
def test_mcp_handler_dangerous_cargo():
    """Test FastMCP handler for dangerous cargo."""
    resp_raw = handle_dangerous_cargo_validate({
        "imdg_class": "1",
        "un_number": "UN0004",
        "operation_type": "direct_discharge_truck",
        "dwell_hours": 1.0,
    })
    resp = json.loads(resp_raw)
    assert resp["ok"] is True
    assert resp["is_compliant"] is True


def test_mcp_handler_tugboat_towage():
    """Test FastMCP handler for tugboat towage."""
    resp_raw = handle_tugboat_towage_evaluate({
        "loa_meters": 185.0,
        "gross_tonnage": 28000.0,
        "allocated_tugs_bp": [45.0, 45.0],
        "wind_speed_mps": 7.0,
    })
    resp = json.loads(resp_raw)
    assert resp["ok"] is True
    assert resp["is_safe_to_operate"] is True


def test_mcp_handler_berthage_mooring():
    """Test FastMCP handler for berthage & mooring."""
    resp_raw = handle_berthage_mooring_calculate({
        "gross_tonnage": 25000.0,
        "duration_hours": 24.0,
        "trade_type": "international",
    })
    resp = json.loads(resp_raw)
    assert resp["ok"] is True
    assert resp["berthage"]["base_amount"] == 1980.0


def test_mcp_handler_channel_clearance():
    """Test FastMCP handler for channel clearance."""
    resp_raw = handle_channel_clearance_evaluate({
        "vessel_name": "MV PACIFIC VOYAGER",
        "imo_number": "IMO9988776",
        "chart_depth_meters": 14.0,
        "tide_height_meters": 2.0,
        "static_draft_meters": 12.0,
        "speed_knots": 8.0,
    })
    resp = json.loads(resp_raw)
    assert resp["ok"] is True
    assert resp["dynamic_ukc"]["is_safe"] is True
    assert resp["clearance_decision"]["clearance_granted"] is True
