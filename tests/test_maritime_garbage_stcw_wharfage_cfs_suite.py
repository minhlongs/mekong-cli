"""Test suite for Phases 287-290 Maritime Garbage, STCW Rest, Port Wharfage & CFS Suite.

Zero-mock comprehensive test suite covering:
- Phase 287: MARPOL Annex V Garbage Discharge Limits & GRB Part I/II Engine (MEPC.295(71)).
- Phase 288: Seafarer Hours of Rest STCW Manila Table A-VIII/1 & MLC 2006 Standard A2.3 Engine.
- Phase 289: Seaport Wharfage & Terminal Berth Tariffs Engine (Circular 39/2023/TT-BGTVT).
- Phase 290: Customs CFS Deconsolidation 90-Day Caps & E-Seal Tracking Engine (Customs Law 2014 & Decree 08/2015).
- Typer CLI integration (8 bilingual aliases) & FastMCP tool handlers.
"""

import json
from typer.testing import CliRunner

from scripts.mcp_server import (
    handle_cfs_eseal_supervision_evaluate,
    handle_marpol_garbage_discharge_evaluate,
    handle_port_wharfage_tariff_calculate,
    handle_stcw_seafarer_rest_verify,
)
from src.cli.app_setup import build_app
from src.core.maritime_garbage_stcw_wharfage_cfs_engine import (
    BerthType,
    CfsCargoOperation,
    CfsCustomsStatus,
    CfsEsealEngine,
    CfsEsealSupervisionInput,
    GarbageCategory,
    GarbageDischargeEngine,
    GarbageDischargeInput,
    GarbageDischargeVerdict,
    PortWharfArea,
    PortWharfageEngine,
    RestComplianceStatus,
    RestPeriod,
    SeaAreaZone,
    SeafarerRestEngine,
    SeafarerRestInput,
    VesselTradeType,
    WharfageCalculationInput,
)

app = build_app()
runner = CliRunner()


# ==============================================================================
# Phase 287: MARPOL Annex V Garbage Discharge Engine Tests
# ==============================================================================

def test_garbage_plastics_strictly_prohibited():
    """Verify plastic waste is strictly prohibited everywhere."""
    sample = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.PLASTICS,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=25.0,
        vessel_speed_knots=12.0,
        estimated_volume_m3=0.5,
    )
    result = GarbageDischargeEngine.evaluate(sample)

    assert result.verdict == GarbageDischargeVerdict.PROHIBITED_MUST_RETAIN
    assert result.is_discharge_permitted is False
    assert result.required_min_distance_nm == 999.0
    assert result.grb_log_code == "GRB-HOLD-RETAIN"
    assert "strictly prohibits overboard discharge of PLASTICS" in result.remarks
    assert len(result.verification_token) == 24


def test_garbage_food_waste_comminuted_outside_special_area():
    """Verify comminuted food waste discharge outside special area (>= 3 NM en route)."""
    # Compliant: 4.5 NM and 11.2 kts
    sample = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.FOOD_WASTE_COMMINUTED,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=4.5,
        vessel_speed_knots=11.2,
        estimated_volume_m3=0.35,
    )
    res = GarbageDischargeEngine.evaluate(sample)
    assert res.verdict == GarbageDischargeVerdict.PERMITTED_OVERBOARD
    assert res.is_discharge_permitted is True
    assert res.required_min_distance_nm == 3.0

    # Non-compliant: distance < 3.0 NM
    sample_close = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.FOOD_WASTE_COMMINUTED,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=2.1,
        vessel_speed_knots=11.2,
        estimated_volume_m3=0.35,
    )
    res_close = GarbageDischargeEngine.evaluate(sample_close)
    assert res_close.verdict == GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT
    assert res_close.is_discharge_permitted is False

    # Non-compliant: vessel stopped (< 0.5 knots)
    sample_stopped = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.FOOD_WASTE_COMMINUTED,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=5.0,
        vessel_speed_knots=0.2,
        estimated_volume_m3=0.35,
    )
    res_stopped = GarbageDischargeEngine.evaluate(sample_stopped)
    assert res_stopped.verdict == GarbageDischargeVerdict.PROHIBITED_VESSEL_NOT_EN_ROUTE
    assert res_stopped.is_discharge_permitted is False


def test_garbage_food_waste_special_area():
    """Verify food waste regulations inside Special Areas (>= 12 NM for comminuted, uncomminuted prohibited)."""
    # Comminuted inside special area at 14 NM
    sample = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.FOOD_WASTE_COMMINUTED,
        zone=SeaAreaZone.SPECIAL_AREA,
        distance_from_land_nm=14.0,
        vessel_speed_knots=10.0,
        estimated_volume_m3=0.2,
    )
    res = GarbageDischargeEngine.evaluate(sample)
    assert res.verdict == GarbageDischargeVerdict.PERMITTED_OVERBOARD
    assert res.is_discharge_permitted is True
    assert res.required_min_distance_nm == 12.0

    # Uncomminuted inside special area is prohibited
    sample_uncomminuted = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.FOOD_WASTE_UNCOMMINUTED,
        zone=SeaAreaZone.SPECIAL_AREA,
        distance_from_land_nm=20.0,
        vessel_speed_knots=12.0,
        estimated_volume_m3=0.4,
    )
    res_uncomminuted = GarbageDischargeEngine.evaluate(sample_uncomminuted)
    assert res_uncomminuted.verdict == GarbageDischargeVerdict.PROHIBITED_SPECIAL_AREA
    assert res_uncomminuted.is_discharge_permitted is False


def test_garbage_animal_carcasses():
    """Verify animal carcasses discharge (>= 100 NM, water depth >= 100m outside special area)."""
    sample_ok = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.ANIMAL_CARCASSES,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=110.0,
        vessel_speed_knots=14.0,
        estimated_volume_m3=1.2,
        water_depth_meters=150.0,
    )
    res_ok = GarbageDischargeEngine.evaluate(sample_ok)
    assert res_ok.verdict == GarbageDischargeVerdict.PERMITTED_OVERBOARD
    assert res_ok.is_discharge_permitted is True

    # Too shallow water depth (< 100m)
    sample_shallow = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.ANIMAL_CARCASSES,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=110.0,
        vessel_speed_knots=14.0,
        estimated_volume_m3=1.2,
        water_depth_meters=60.0,
    )
    res_shallow = GarbageDischargeEngine.evaluate(sample_shallow)
    assert res_shallow.verdict == GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT
    assert res_shallow.is_discharge_permitted is False

    # Inside special area
    sample_special = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.ANIMAL_CARCASSES,
        zone=SeaAreaZone.SPECIAL_AREA,
        distance_from_land_nm=110.0,
        vessel_speed_knots=14.0,
        estimated_volume_m3=1.2,
        water_depth_meters=200.0,
    )
    res_special = GarbageDischargeEngine.evaluate(sample_special)
    assert res_special.verdict == GarbageDischargeVerdict.PROHIBITED_SPECIAL_AREA
    assert res_special.is_discharge_permitted is False


def test_garbage_cooking_oil_and_ashes_prohibited():
    """Verify cooking oil and incinerator ashes are strictly prohibited."""
    sample_oil = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.COOKING_OIL,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=50.0,
        vessel_speed_knots=15.0,
        estimated_volume_m3=0.1,
    )
    assert GarbageDischargeEngine.evaluate(sample_oil).is_discharge_permitted is False

    sample_ashes = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.INCINERATOR_ASHES,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=50.0,
        vessel_speed_knots=15.0,
        estimated_volume_m3=0.1,
    )
    assert GarbageDischargeEngine.evaluate(sample_ashes).is_discharge_permitted is False


def test_garbage_cargo_residues_hme_and_non_hme():
    """Verify cargo residues HME vs Non-HME rules."""
    # HME cargo residues are banned
    sample_hme = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.CARGO_RESIDUES_HME,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=30.0,
        vessel_speed_knots=12.0,
        estimated_volume_m3=2.0,
    )
    res_hme = GarbageDischargeEngine.evaluate(sample_hme)
    assert res_hme.is_discharge_permitted is False

    # Non-HME outside special area >= 12 NM
    sample_non_hme = GarbageDischargeInput(
        vessel_name="MV MEKONG HORIZON",
        imo_number="9845123",
        garbage_category=GarbageCategory.CARGO_RESIDUES_NON_HME,
        zone=SeaAreaZone.OUTSIDE_SPECIAL_AREA,
        distance_from_land_nm=15.0,
        vessel_speed_knots=12.0,
        estimated_volume_m3=1.0,
    )
    res_non_hme = GarbageDischargeEngine.evaluate(sample_non_hme)
    assert res_non_hme.is_discharge_permitted is True


# ==============================================================================
# Phase 288: STCW Manila & MLC 2006 Seafarer Rest Hours Engine Tests
# ==============================================================================

def test_seafarer_rest_fully_compliant():
    """Verify compliant seafarer rest hours schedule."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=4.0),
        RestPeriod(start_hour=13.0, duration_hours=7.0),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Nguyen Van A",
        rank="Chief Officer",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=72.0,
        interval_between_rests_hours=9.0,
        is_emergency_drill_or_sar=False,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is True
    assert result.compliance_status == RestComplianceStatus.FULLY_COMPLIANT
    assert result.total_rest_24h == 11.0
    assert result.total_rest_7d == 83.0
    assert result.longest_continuous_rest == 7.0
    assert result.period_count_24h == 2
    assert result.compensation_rest_due_hours == 0.0


def test_seafarer_rest_violation_total_24h():
    """Verify violation when total 24h rest is under 10.0 hours."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=3.0),
        RestPeriod(start_hour=14.0, duration_hours=5.0),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Tran Van B",
        rank="Second Engineer",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=70.0,
        interval_between_rests_hours=11.0,
        is_emergency_drill_or_sar=False,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is False
    assert result.compliance_status == RestComplianceStatus.VIOLATION_24H_TOTAL
    assert result.total_rest_24h == 8.0
    assert result.compensation_rest_due_hours == 2.0


def test_seafarer_rest_violation_longest_continuous():
    """Verify violation when longest continuous rest is under 6.0 hours."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=5.5),
        RestPeriod(start_hour=12.0, duration_hours=5.0),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Le Van C",
        rank="Able Seaman",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=70.0,
        interval_between_rests_hours=6.5,
        is_emergency_drill_or_sar=False,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is False
    assert result.compliance_status == RestComplianceStatus.VIOLATION_24H_CONTINUOUS
    assert result.longest_continuous_rest == 5.5
    assert result.compensation_rest_due_hours == 0.0


def test_seafarer_rest_violation_period_count():
    """Verify violation when rest is divided into more than 2 periods."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=4.0),
        RestPeriod(start_hour=8.0, duration_hours=2.0),
        RestPeriod(start_hour=16.0, duration_hours=6.0),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Pham Van D",
        rank="Bosun",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=70.0,
        interval_between_rests_hours=4.0,
        is_emergency_drill_or_sar=False,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is False
    assert result.compliance_status == RestComplianceStatus.VIOLATION_24H_PERIODS
    assert result.period_count_24h == 3


def test_seafarer_rest_violation_interval():
    """Verify violation when interval between rests exceeds 14.0 hours."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=6.0),
        RestPeriod(start_hour=21.0, duration_hours=5.0),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Hoang Van E",
        rank="Third Mate",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=70.0,
        interval_between_rests_hours=15.0,
        is_emergency_drill_or_sar=False,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is False
    assert result.compliance_status == RestComplianceStatus.VIOLATION_INTERVAL_EXCEEDED


def test_seafarer_rest_violation_7d_total():
    """Verify violation when 7-day rolling rest is under 77.0 hours."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=4.0),
        RestPeriod(start_hour=12.0, duration_hours=6.5),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Ngo Van F",
        rank="Oiler",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=65.0,  # 65 + 10.5 = 75.5 < 77.0
        interval_between_rests_hours=8.0,
        is_emergency_drill_or_sar=False,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is False
    assert result.compliance_status == RestComplianceStatus.VIOLATION_7D_TOTAL
    assert result.total_rest_7d == 75.5
    assert result.compensation_rest_due_hours == 1.5


def test_seafarer_rest_emergency_override():
    """Verify emergency override permits temporary deviation with compensatory rest."""
    periods = [
        RestPeriod(start_hour=0.0, duration_hours=4.0),
        RestPeriod(start_hour=14.0, duration_hours=3.0),
    ]
    sample = SeafarerRestInput(
        seafarer_name="Nguyen Van A",
        rank="Master",
        rest_periods_24h=periods,
        total_rest_hours_past_6d=60.0,
        interval_between_rests_hours=10.0,
        is_emergency_drill_or_sar=True,
    )
    result = SeafarerRestEngine.evaluate(sample)

    assert result.is_compliant is True
    assert result.compliance_status == RestComplianceStatus.EMERGENCY_OVERRIDE_COMPENSATED
    assert result.compensation_rest_due_hours == 3.0  # 10.0 - 7.0 = 3.0
    assert "Emergency/Drill exception invoked" in result.audit_remarks


# ==============================================================================
# Phase 289: Seaport Wharfage Tariffs (Circular 39/2023) Tests
# ==============================================================================

def test_port_wharfage_international_with_overstay():
    """Verify international container berth wharfage with overstay surcharge."""
    sample = WharfageCalculationInput(
        gross_tonnage=32000.0,
        trade_type=VesselTradeType.INTERNATIONAL,
        port_area=PortWharfArea.AREA_III_SOUTH,
        berth_type=BerthType.CONTAINER_BERTH,
        scheduled_hours=36.0,
        actual_hours=40.0,
        is_holiday=False,
        vnd_exchange_rate=25000.0,
    )
    result = PortWharfageEngine.calculate(sample)

    assert result.base_rate_per_gt_hour == 0.0035
    assert result.base_berthage_fee_usd == 4480.0
    assert result.overstay_hours == 4.0
    assert result.overstay_surcharge_usd == 224.0
    assert result.holiday_surcharge_usd == 0.0
    assert result.total_wharfage_fee_usd == 4704.0
    assert result.total_wharfage_fee_vnd == 117600000.0
    assert "CONTAINER_BERTH" in result.invoice_description


def test_port_wharfage_domestic_area_north_with_holiday():
    """Verify domestic general cargo berth in Area I North with holiday surcharge."""
    sample = WharfageCalculationInput(
        gross_tonnage=5000.0,
        trade_type=VesselTradeType.DOMESTIC,
        port_area=PortWharfArea.AREA_I_NORTH,
        berth_type=BerthType.GENERAL_CARGO_BERTH,
        scheduled_hours=24.0,
        actual_hours=24.0,
        is_holiday=True,
        vnd_exchange_rate=25000.0,
    )
    result = PortWharfageEngine.calculate(sample)

    assert round(result.base_rate_per_gt_hour, 6) == 0.000836
    assert result.base_berthage_fee_vnd == 2508000.0
    assert result.total_wharfage_fee_vnd == 3260400.0
    assert result.overstay_hours == 0.0


def test_port_wharfage_buoy_and_liquid_jetty():
    """Verify wharfage calculations for buoy anchorage and liquid jetty."""
    # Buoy Anchorage Area II Central (0.90x)
    sample_buoy = WharfageCalculationInput(
        gross_tonnage=10000.0,
        trade_type=VesselTradeType.INTERNATIONAL,
        port_area=PortWharfArea.AREA_II_CENTRAL,
        berth_type=BerthType.BUOY_ANCHORAGE,
        scheduled_hours=12.0,
        actual_hours=12.0,
    )
    res_buoy = PortWharfageEngine.calculate(sample_buoy)
    expected_rate = 0.00175 * 0.90
    assert round(res_buoy.base_rate_per_gt_hour, 6) == round(expected_rate, 6)

    # Liquid bulk jetty
    sample_liquid = WharfageCalculationInput(
        gross_tonnage=15000.0,
        trade_type=VesselTradeType.INTERNATIONAL,
        port_area=PortWharfArea.AREA_III_SOUTH,
        berth_type=BerthType.LIQUID_BULK_JETTY,
        scheduled_hours=18.0,
        actual_hours=18.0,
    )
    res_liquid = PortWharfageEngine.calculate(sample_liquid)
    assert res_liquid.base_rate_per_gt_hour == 0.0042


# ==============================================================================
# Phase 290: Customs CFS & E-Seal Tracking Engine Tests
# ==============================================================================

def test_cfs_normal_compliant_storage():
    """Verify normal compliant CFS storage within 90 days."""
    sample = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_DECONSOLIDATION,
        storage_days=45,
        is_extension_approved=False,
        is_cable_intact=True,
        is_tamper_detected=False,
        route_deviation_meters=0.0,
        gps_lost_minutes=0.0,
    )
    result = CfsEsealEngine.evaluate(sample)

    assert result.is_cleared_for_release is True
    assert result.customs_status == CfsCustomsStatus.COMPLIANT_ACTIVE
    assert result.max_permitted_storage_days == 90
    assert result.remaining_storage_days == 45
    assert len(result.supervision_token) == 24


def test_cfs_expiring_warning_and_extended_storage():
    """Verify expiration warning when remaining days <= 15 and extension logic."""
    # Expiring warning: 80 days of 90 days (10 days left)
    sample_warning = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_DECONSOLIDATION,
        storage_days=80,
        is_extension_approved=False,
    )
    res_warning = CfsEsealEngine.evaluate(sample_warning)
    assert res_warning.customs_status == CfsCustomsStatus.WARNING_EXPIRING_SOON
    assert res_warning.remaining_storage_days == 10
    assert res_warning.is_cleared_for_release is True

    # Extended storage: 120 days of 180 days (60 days left)
    sample_ext = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_CONSOLIDATION,
        storage_days=120,
        is_extension_approved=True,
    )
    res_ext = CfsEsealEngine.evaluate(sample_ext)
    assert res_ext.customs_status == CfsCustomsStatus.COMPLIANT_ACTIVE
    assert res_ext.max_permitted_storage_days == 180
    assert res_ext.remaining_storage_days == 60
    assert res_ext.is_cleared_for_release is True


def test_cfs_storage_overstay_expired():
    """Verify overstay expiry triggering administrative handling."""
    sample_expired = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_DECONSOLIDATION,
        storage_days=95,
        is_extension_approved=False,
    )
    res_expired = CfsEsealEngine.evaluate(sample_expired)
    assert res_expired.customs_status == CfsCustomsStatus.OVERDUE_ABANDONED_SUSPECT
    assert res_expired.remaining_storage_days == 0
    assert res_expired.is_cleared_for_release is False
    assert "exceeds statutory cap 90 days" in res_expired.status_summary


def test_cfs_eseal_tamper_and_telemetry_violation():
    """Verify E-Seal cable breach and telemetry deviation flagging."""
    # Cable cut
    sample_tamper = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_DECONSOLIDATION,
        storage_days=30,
        is_cable_intact=False,
    )
    res_tamper = CfsEsealEngine.evaluate(sample_tamper)
    assert res_tamper.customs_status == CfsCustomsStatus.TAMPER_ALERT_CABLE_CUT
    assert res_tamper.is_cleared_for_release is False
    assert "E-Seal wire severed" in res_tamper.status_summary

    # Route deviation > 500m
    sample_dev = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_DECONSOLIDATION,
        storage_days=30,
        route_deviation_meters=650.0,
    )
    res_dev = CfsEsealEngine.evaluate(sample_dev)
    assert res_dev.customs_status == CfsCustomsStatus.ROUTE_DEVIATION_ALERT
    assert res_dev.is_cleared_for_release is False

    # GPS lost > 30 minutes
    sample_gps = CfsEsealSupervisionInput(
        container_no="TCNU8923410",
        eseal_id="ESEAL-VN-2026-9921",
        operation=CfsCargoOperation.LCL_DECONSOLIDATION,
        storage_days=30,
        gps_lost_minutes=45.0,
    )
    res_gps = CfsEsealEngine.evaluate(sample_gps)
    assert res_gps.customs_status == CfsCustomsStatus.GPS_SIGNAL_LOST
    assert res_gps.is_cleared_for_release is False


# ==============================================================================
# CLI Commands Integration Tests (Bilingual Aliases)
# ==============================================================================

def test_cli_garbage_evaluate_bilingual():
    """Verify CLI 'garbage evaluate' and 'quanlyrac evaluate'."""
    res1 = runner.invoke(app, [
        "garbage", "evaluate",
        "--vessel", "MV MEKONG HORIZON",
        "--imo", "9845123",
        "--category", "FOOD_WASTE_COMMINUTED",
        "--zone", "OUTSIDE_SPECIAL_AREA",
        "--dist", "4.5",
        "--speed", "11.2",
    ])
    assert res1.exit_code == 0
    assert "QUẢN LÝ RÁC THẢI TÀU BIỂN" in res1.stdout
    assert "Được phép xả qua mạn: CÓ" in res1.stdout

    res2 = runner.invoke(app, [
        "quanlyrac", "evaluate",
        "--vessel", "MV MEKONG HORIZON",
        "--category", "PLASTICS",
        "--dist", "50.0",
    ])
    assert res2.exit_code == 0
    assert "KHÔNG (LƯU GIỮ TRÊN TÀU)" in res2.stdout


def test_cli_resthours_verify_bilingual():
    """Verify CLI 'resthours verify' and 'gionghithuyenvien verify'."""
    res1 = runner.invoke(app, [
        "resthours", "verify",
        "--name", "Nguyen Van A",
        "--rank", "Chief Officer",
        "--p1", "4.0",
        "--p2", "7.0",
        "--past-6d", "72.0",
        "--interval", "10.0",
    ])
    assert res1.exit_code == 0
    assert "KIỂM SOÁT THỜI GIAN NGHỈ NGƠI THUYỀN VIÊN" in res1.stdout
    assert "ĐẠT (COMPLIANT)" in res1.stdout

    res2 = runner.invoke(app, [
        "gionghithuyenvien", "verify",
        "--name", "Tran Van B",
        "--p1", "3.0",
        "--p2", "4.0",
        "--past-6d", "60.0",
    ])
    assert res2.exit_code == 0
    assert "VI PHẠM (NON-COMPLIANT)" in res2.stdout


def test_cli_wharfage_calculate_bilingual():
    """Verify CLI 'wharfage calculate' and 'cuoccauben calculate'."""
    res1 = runner.invoke(app, [
        "wharfage", "calculate",
        "--gt", "32000",
        "--trade", "INTERNATIONAL",
        "--area", "AREA_III_SOUTH",
        "--berth", "CONTAINER_BERTH",
        "--sched-h", "36",
        "--actual-h", "40",
    ])
    assert res1.exit_code == 0
    assert "TÍNH CƯỚC SỬ DỤNG CẦU BẾN CẢNG BIỂN" in res1.stdout
    assert "TỔNG CƯỚC CẦU BẾN PHẢI THU: $4,704.00 USD" in res1.stdout

    res2 = runner.invoke(app, [
        "cuoccauben", "calculate",
        "--gt", "5000",
        "--trade", "DOMESTIC",
        "--area", "AREA_I_NORTH",
        "--berth", "GENERAL_CARGO_BERTH",
        "--sched-h", "24",
        "--actual-h", "24",
        "--holiday",
    ])
    assert res2.exit_code == 0
    assert "3,260,400 VND" in res2.stdout


def test_cli_cfseseal_supervise_bilingual():
    """Verify CLI 'cfseseal supervise' and 'khohangcfs supervise'."""
    res1 = runner.invoke(app, [
        "cfseseal", "supervise",
        "--container", "TCNU8923410",
        "--eseal", "ESEAL-VN-2026-9921",
        "--op", "LCL_DECONSOLIDATION",
        "--days", "45",
    ])
    assert res1.exit_code == 0
    assert "GIÁM SÁT KHO HÀNG CFS & ĐỊNH VỊ NIÊM PHONG ĐIỆN TỬ" in res1.stdout
    assert "CÓ (CLEARED)" in res1.stdout

    res2 = runner.invoke(app, [
        "khohangcfs", "supervise",
        "--container", "TCNU8923410",
        "--tamper",
    ])
    assert res2.exit_code == 0
    assert "KHÔNG (GIỮ LẠI ĐIỀU TRA)" in res2.stdout


# ==============================================================================
# FastMCP Handlers Tests
# ==============================================================================

def test_fastmcp_handlers_execute_successfully():
    """Verify FastMCP handlers return proper structured JSON responses."""
    # Handler 1: MARPOL Garbage Discharge
    out1 = handle_marpol_garbage_discharge_evaluate({
        "vessel_name": "MV MEKONG HORIZON",
        "garbage_category": "FOOD_WASTE_COMMINUTED",
        "distance_from_land_nm": 4.5,
    })
    data1 = json.loads(out1)
    assert data1["ok"] is True
    assert data1["garbage_evaluation"]["is_discharge_permitted"] is True

    # Handler 2: STCW Seafarer Rest
    out2 = handle_stcw_seafarer_rest_verify({
        "seafarer_name": "Nguyen Van A",
        "period_1_hours": 4.0,
        "period_2_hours": 7.0,
        "total_rest_hours_past_6d": 72.0,
    })
    data2 = json.loads(out2)
    assert data2["ok"] is True
    assert data2["rest_verification"]["is_compliant"] is True

    # Handler 3: Port Wharfage Tariffs
    out3 = handle_port_wharfage_tariff_calculate({
        "gross_tonnage": 32000.0,
        "scheduled_hours": 36.0,
        "actual_hours": 40.0,
    })
    data3 = json.loads(out3)
    assert data3["ok"] is True
    assert data3["wharfage_calculation"]["total_wharfage_fee_usd"] == 4704.0

    # Handler 4: CFS E-Seal Supervision
    out4 = handle_cfs_eseal_supervision_evaluate({
        "container_no": "TCNU8923410",
        "storage_days": 45,
    })
    data4 = json.loads(out4)
    assert data4["ok"] is True
    assert data4["cfs_eseal_supervision"]["is_cleared_for_release"] is True
