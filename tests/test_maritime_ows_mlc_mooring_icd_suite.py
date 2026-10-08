"""Test suite for Phases 283-286 Maritime OWS, MLC Wages, Mooring & ICD Suite.

Zero-mock comprehensive test suite covering:
- Phase 283: Oil Water Separator (OWS) 15 ppm & Electronic ORB Part I Engine (MARPOL Annex I & MEPC.107(49)).
- Phase 284: Seafarers Wages, ILO Minimums & Repatriation Escrow Engine (MLC 2006 Standards A2.2 & A2.5).
- Phase 285: Port Mooring Tariffs (Circular 39/2023/TT-BGTVT) & OCIMF MEG4 Mooring Safety Engine.
- Phase 286: Inland Clearance Depot (ICD) Bonded Transit & Customs OLA Declaration Engine (Customs Law 2014 & Decree 08/2015).
- Typer CLI integration (8 bilingual aliases) & FastMCP tool handlers.
"""

import json
from typer.testing import CliRunner

from scripts.mcp_server import (
    handle_icd_bonded_transit_supervise,
    handle_mlc_seafarer_wages_calculate,
    handle_ows_15ppm_discharge_evaluate,
    handle_port_mooring_tariff_calculate,
)
from src.cli.app_setup import build_app
from src.core.maritime_ows_mlc_mooring_icd_engine import (
    IcdBondedTransitEngine,
    IcdTransitInput,
    IcdTransitStatus,
    MlcSeafarerWagesEngine,
    MooringOperationType,
    MooringTariffInput,
    OwsComplianceStatus,
    OwsDischargeEngine,
    OwsDischargeInput,
    PortMooringTariffEngine,
    SeafarerContractInput,
)

app = build_app()
runner = CliRunner()


# ==============================================================================
# Phase 283: OWS 15 ppm & Oil Record Book (MARPOL Annex I) Tests
# ==============================================================================

def test_ows_discharge_normal_compliant():
    """Verify compliant oily bilge discharge meeting MARPOL Annex I & MEPC.107(49)."""
    sample = OwsDischargeInput(
        vessel_name="MV MEKONG ODYSSEY",
        imo_number="9918234",
        oil_content_ppm=8.5,
        vessel_speed_knots=12.0,
        distance_from_land_nm=25.0,
        is_special_area=False,
        flow_rate_m3_h=2.5,
        discharge_duration_minutes=60.0,
        fail_safe_valve_operational=True,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    assert result.compliance_status == OwsComplianceStatus.COMPLIANT_DISCHARGE
    assert result.valve_position == "OVERBOARD"
    assert result.total_discharged_m3 == 2.5
    assert result.orb_code == "Code D (Item 15.2)"
    assert "OWS MEPC.107(49)" in result.orb_entry
    assert len(result.verification_token) == 24


def test_ows_discharge_oil_content_exceeded():
    """Verify automatic 3-way fail-safe valve redirection when oil content >= 15.0 ppm."""
    sample = OwsDischargeInput(
        vessel_name="MV MEKONG ODYSSEY",
        imo_number="9918234",
        oil_content_ppm=18.4,
        vessel_speed_knots=11.5,
        distance_from_land_nm=20.0,
        is_special_area=False,
        flow_rate_m3_h=2.5,
        discharge_duration_minutes=45.0,
        fail_safe_valve_operational=True,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    assert result.compliance_status == OwsComplianceStatus.VALVE_AUTO_RECIRCULATE
    assert result.valve_position == "RECIRCULATE_TO_HOLDING_TANK"
    assert result.total_discharged_m3 == 0.0
    assert "hồi lưu" in result.action_required


def test_ows_discharge_special_area_prohibition():
    """Verify MARPOL Special Area prohibition triggers holding tank recirculation."""
    sample = OwsDischargeInput(
        vessel_name="MV MEKONG ODYSSEY",
        imo_number="9918234",
        oil_content_ppm=6.2,
        vessel_speed_knots=10.0,
        distance_from_land_nm=30.0,
        is_special_area=True,  # In Special Area
        flow_rate_m3_h=2.0,
        discharge_duration_minutes=30.0,
        fail_safe_valve_operational=True,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    assert result.compliance_status == OwsComplianceStatus.PROHIBITED_LOCATION
    assert result.valve_position == "RECIRCULATE_TO_HOLDING_TANK"
    assert result.total_discharged_m3 == 0.0
    assert "vùng biển đặc biệt" in result.action_required


def test_ows_discharge_distance_violation():
    """Verify discharge within 12 NM territorial baseline is prohibited."""
    sample = OwsDischargeInput(
        vessel_name="MV MEKONG ODYSSEY",
        imo_number="9918234",
        oil_content_ppm=5.5,
        vessel_speed_knots=12.0,
        distance_from_land_nm=9.4,  # Under 12 NM
        is_special_area=False,
        flow_rate_m3_h=2.0,
        discharge_duration_minutes=60.0,
        fail_safe_valve_operational=True,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    assert result.compliance_status == OwsComplianceStatus.PROHIBITED_LOCATION
    assert result.valve_position == "RECIRCULATE_TO_HOLDING_TANK"
    assert result.total_discharged_m3 == 0.0
    assert "Cự ly bờ < 12 NM" in result.action_required


def test_ows_discharge_vessel_stopped_violation():
    """Verify en-route requirement (< 0.5 knots considered stopped/anchored)."""
    sample = OwsDischargeInput(
        vessel_name="MV MEKONG ODYSSEY",
        imo_number="9918234",
        oil_content_ppm=4.0,
        vessel_speed_knots=0.2,  # Stopped
        distance_from_land_nm=25.0,
        is_special_area=False,
        flow_rate_m3_h=2.0,
        discharge_duration_minutes=60.0,
        fail_safe_valve_operational=True,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    assert result.compliance_status == OwsComplianceStatus.VESSEL_NOT_EN_ROUTE
    assert result.valve_position == "RECIRCULATE_TO_HOLDING_TANK"
    assert result.total_discharged_m3 == 0.0
    assert "không đang hành trình" in result.action_required


def test_ows_discharge_equipment_fault():
    """Verify equipment/alarm failure fails closed to holding tank."""
    sample = OwsDischargeInput(
        vessel_name="MV MEKONG ODYSSEY",
        imo_number="9918234",
        oil_content_ppm=5.0,
        vessel_speed_knots=10.0,
        distance_from_land_nm=25.0,
        is_special_area=False,
        flow_rate_m3_h=2.0,
        discharge_duration_minutes=60.0,
        fail_safe_valve_operational=False,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    assert result.compliance_status == OwsComplianceStatus.EQUIPMENT_FAULT
    assert result.valve_position == "RECIRCULATE_TO_HOLDING_TANK"
    assert result.total_discharged_m3 == 0.0


# ==============================================================================
# Phase 284: MLC 2006 Seafarer Wages & Repatriation Escrow Tests
# ==============================================================================

def test_mlc_wages_standard_calculation():
    """Verify full salary calculation, hourly rates, 1.25x overtime and leave pay."""
    contract = SeafarerContractInput(
        seafarer_name="NGUYEN VAN A",
        rank="Able Seaman (AB)",
        basic_monthly_wage_usd=750.0,
        contract_months=9,
        actual_monthly_overtime_hours=65.0,
        guaranteed_overtime_hours=48.0,
        responsibility_allowance_usd=100.0,
        subsistence_allowance_usd=50.0,
        pni_repatriation_bond_amount_usd=12000.0,
    )
    result = MlcSeafarerWagesEngine.calculate_wages_and_escrow(contract)

    # 750 / 208 = 3.605769 -> 3.61
    assert result.hourly_basic_rate_usd == round(750.0 / 208.0, 2)
    # Overtime rate = 3.61 * 1.25 = 4.51
    assert result.overtime_hourly_rate_usd == round(result.hourly_basic_rate_usd * 1.25, 2)
    # Payable OT = max(65.0, 48.0) = 65.0
    assert result.payable_overtime_hours == 65.0
    assert result.overtime_pay_usd == round(65.0 * result.overtime_hourly_rate_usd, 2)
    # Annual leave = 2.5 * (750 / 30) = 62.50
    assert result.paid_annual_leave_pay_usd == 62.50
    assert result.gross_monthly_wage_usd > 750.0
    assert result.gross_monthly_wage_vnd == round(result.gross_monthly_wage_usd * 25000.0, 0)
    assert result.mlc_wage_compliant is True
    assert result.repatriation_bond_adequate is True
    assert len(result.sea_auth_token) == 24


def test_mlc_wages_guaranteed_overtime_applied():
    """Verify guaranteed OT applied when actual worked OT is lower than contractual minimum."""
    contract = SeafarerContractInput(
        seafarer_name="TRAN VAN B",
        rank="Able Seaman (AB)",
        basic_monthly_wage_usd=700.0,
        contract_months=6,
        actual_monthly_overtime_hours=30.0,  # Below guaranteed 48.0
        guaranteed_overtime_hours=48.0,
        responsibility_allowance_usd=0.0,
        subsistence_allowance_usd=0.0,
        pni_repatriation_bond_amount_usd=10000.0,
    )
    result = MlcSeafarerWagesEngine.calculate_wages_and_escrow(contract)

    assert result.payable_overtime_hours == 48.0
    assert result.overtime_pay_usd == round(48.0 * result.overtime_hourly_rate_usd, 2)


def test_mlc_wages_ilo_minimum_wage_fail():
    """Verify non-compliance flag when basic wage for AB falls below ILO benchmark ($658)."""
    contract = SeafarerContractInput(
        seafarer_name="LE VAN C",
        rank="Able Seaman (AB)",
        basic_monthly_wage_usd=600.0,  # Below ILO $658
        contract_months=6,
        actual_monthly_overtime_hours=40.0,
        guaranteed_overtime_hours=40.0,
        responsibility_allowance_usd=0.0,
        subsistence_allowance_usd=0.0,
        pni_repatriation_bond_amount_usd=8000.0,
    )
    result = MlcSeafarerWagesEngine.calculate_wages_and_escrow(contract)

    assert result.mlc_wage_compliant is False


def test_mlc_repatriation_escrow_deficiency():
    """Verify inadequate P&I bond when bond is less than 4 months basic wage + $3000."""
    # 4 * 1000 + 3000 = $7000 required reserve
    contract = SeafarerContractInput(
        seafarer_name="HOANG VAN D",
        rank="Chief Officer",
        basic_monthly_wage_usd=1000.0,
        contract_months=6,
        actual_monthly_overtime_hours=20.0,
        guaranteed_overtime_hours=20.0,
        responsibility_allowance_usd=200.0,
        subsistence_allowance_usd=100.0,
        pni_repatriation_bond_amount_usd=5000.0,  # Below 7000.0
    )
    result = MlcSeafarerWagesEngine.calculate_wages_and_escrow(contract)

    assert result.abandonment_reserve_4m_usd == 4000.0
    assert result.repatriation_bond_adequate is False


# ==============================================================================
# Phase 285: Port Mooring Tariffs & MEG4 Engine Tests
# ==============================================================================

def test_mooring_tariff_base_tiers():
    """Verify gross tonnage tier pricing under Circular 39/2023/TT-BGTVT."""
    test_cases = [
        (1500.0, 25.0),
        (3500.0, 45.0),
        (7500.0, 75.0),
        (15000.0, 120.0),
        (35000.0, 200.0),
        (75000.0, 260.0),  # 200 + 3 * 20 = 260
    ]
    for gt, expected_base in test_cases:
        input_data = MooringTariffInput(
            vessel_name="TEST VESSEL",
            gross_tonnage=gt,
            operation_type=MooringOperationType.MOORING,
            is_night_operation=False,
            is_holiday=False,
            standby_hours=0.0,
            mooring_line_swl_tons=50.0,
            mooring_line_mbl_tons=100.0,
        )
        res = PortMooringTariffEngine.calculate_mooring_dues(input_data)
        assert res.base_charge_usd == expected_base


def test_mooring_tariff_operation_multipliers():
    """Verify operation type multipliers: Mooring (1.0x), Unmooring (0.85x), Shifting (1.25x)."""
    gt = 10000.0  # Base charge = 120.0
    # Unmooring
    unmoor_res = PortMooringTariffEngine.calculate_mooring_dues(
        MooringTariffInput(
            vessel_name="MV SHIP",
            gross_tonnage=gt,
            operation_type=MooringOperationType.UNMOORING,
        )
    )
    assert unmoor_res.base_charge_usd == 120.0 * 0.85

    # Shifting
    shift_res = PortMooringTariffEngine.calculate_mooring_dues(
        MooringTariffInput(
            vessel_name="MV SHIP",
            gross_tonnage=gt,
            operation_type=MooringOperationType.SHIFTING,
        )
    )
    assert shift_res.base_charge_usd == 120.0 * 1.25


def test_mooring_tariff_surcharges_and_standby():
    """Verify night surcharge (+40%), holiday surcharge (+50%), and standby charge ($25/h)."""
    input_data = MooringTariffInput(
        vessel_name="MV TANKER",
        gross_tonnage=20000.0,  # Base = 200.0
        operation_type=MooringOperationType.MOORING,
        is_night_operation=True,
        is_holiday=True,
        standby_hours=2.5,  # 2.5 - 0.5 grace = 2.0 billable hours -> 2.0 * 25 = 50.0
        mooring_line_swl_tons=40.0,
        mooring_line_mbl_tons=80.0,
    )
    res = PortMooringTariffEngine.calculate_mooring_dues(input_data)

    assert res.base_charge_usd == 200.0
    assert res.night_surcharge_usd == 80.0    # 200 * 0.40
    assert res.holiday_surcharge_usd == 100.0  # 200 * 0.50
    assert res.standby_charge_usd == 50.0      # 2.0 * 25.0
    assert res.total_charge_usd == 430.0
    assert res.total_charge_vnd == 430.0 * 25000.0


def test_mooring_meg4_safety_check_pass():
    """Verify MEG4 safety validation passes when SWL/MBL <= 60%."""
    input_data = MooringTariffInput(
        vessel_name="MV SAFETY",
        gross_tonnage=5000.0,
        operation_type=MooringOperationType.MOORING,
        mooring_line_swl_tons=45.0,
        mooring_line_mbl_tons=100.0,  # 45% <= 60%
    )
    res = PortMooringTariffEngine.calculate_mooring_dues(input_data)

    assert res.meg4_safe is True
    assert res.meg4_line_tension_ratio == 0.45
    assert "Đảm bảo an toàn" in res.meg4_notes


def test_mooring_meg4_safety_check_hazard():
    """Verify MEG4 safety validation fails when SWL/MBL > 60%."""
    input_data = MooringTariffInput(
        vessel_name="MV HAZARD",
        gross_tonnage=5000.0,
        operation_type=MooringOperationType.MOORING,
        mooring_line_swl_tons=65.0,
        mooring_line_mbl_tons=100.0,  # 65% > 60%
    )
    res = PortMooringTariffEngine.calculate_mooring_dues(input_data)

    assert res.meg4_safe is False
    assert res.meg4_line_tension_ratio == 0.65
    assert "CẢNH BÁO" in res.meg4_notes


# ==============================================================================
# Phase 286: ICD Bonded Transit & Customs OLA Declaration Tests
# ==============================================================================

def test_icd_transit_compliant_on_time():
    """Verify successful ICD bonded transport clearance under Customs Law 2014."""
    data = IcdTransitInput(
        declaration_no="OLA-2026-001",
        container_no="TEMU1234567",
        origin_seaport_code="VNCME",
        dest_icd_code="VNSTH",
        distance_km=70.0,
        max_transit_hours=12.0,
        departure_time_iso="2026-10-08T06:00:00",
        arrival_time_iso="2026-10-08T10:00:00",  # 4.0 hours
        customs_seal_intact=True,
        bank_guarantee_amount_vnd=500_000_000.0,
        declared_tax_liability_vnd=400_000_000.0,  # 1.25 coverage
    )
    res = IcdBondedTransitEngine.supervise_icd_transit(data)

    assert res.transit_status == IcdTransitStatus.ON_TIME_SECURE
    assert res.customs_clearance_granted is True
    assert res.actual_transit_hours == 4.0
    assert res.duty_coverage_ratio == 1.25
    assert "ĐỦ ĐIỀU KIỆN THÔNG QUAN" in res.action_directive
    assert len(res.tracking_token) == 24


def test_icd_transit_minor_delay():
    """Verify minor delay (<= 6.0 hours over limit) yields TRANSIT_DELAY_WARNING."""
    data = IcdTransitInput(
        declaration_no="OLA-2026-002",
        container_no="TEMU1234568",
        origin_seaport_code="VNCME",
        dest_icd_code="VNSTH",
        distance_km=70.0,
        max_transit_hours=8.0,
        departure_time_iso="2026-10-08T06:00:00",
        arrival_time_iso="2026-10-08T16:30:00",  # 10.5 hours (delay 2.5h)
        customs_seal_intact=True,
        bank_guarantee_amount_vnd=500_000_000.0,
        declared_tax_liability_vnd=500_000_000.0,
    )
    res = IcdBondedTransitEngine.supervise_icd_transit(data)

    assert res.transit_status == IcdTransitStatus.TRANSIT_DELAY_WARNING
    assert res.customs_clearance_granted is True
    assert "CHẬM HÀNH TRÌNH" in res.action_directive


def test_icd_transit_critical_delay():
    """Verify critical delay (> 6.0 hours over limit) halts automated clearance."""
    data = IcdTransitInput(
        declaration_no="OLA-2026-003",
        container_no="TEMU1234569",
        origin_seaport_code="VNCME",
        dest_icd_code="VNSTH",
        distance_km=70.0,
        max_transit_hours=8.0,
        departure_time_iso="2026-10-08T06:00:00",
        arrival_time_iso="2026-10-08T22:00:00",  # 16.0 hours (delay 8.0h > 6h)
        customs_seal_intact=True,
        bank_guarantee_amount_vnd=500_000_000.0,
        declared_tax_liability_vnd=500_000_000.0,
    )
    res = IcdBondedTransitEngine.supervise_icd_transit(data)

    assert res.transit_status == IcdTransitStatus.TRANSIT_OVERDUE_CRITICAL
    assert res.customs_clearance_granted is False
    assert "QUÁ HẠN NGHIÊM TRỌNG" in res.action_directive


def test_icd_transit_seal_tampered():
    """Verify damaged or unsealed container triggers immediate quarantine inspection."""
    data = IcdTransitInput(
        declaration_no="OLA-2026-004",
        container_no="TEMU1234570",
        origin_seaport_code="VNCME",
        dest_icd_code="VNSTH",
        distance_km=70.0,
        max_transit_hours=12.0,
        departure_time_iso="2026-10-08T06:00:00",
        arrival_time_iso="2026-10-08T10:00:00",
        customs_seal_intact=False,  # Broken seal
        bank_guarantee_amount_vnd=500_000_000.0,
        declared_tax_liability_vnd=400_000_000.0,
    )
    res = IcdBondedTransitEngine.supervise_icd_transit(data)

    assert res.transit_status == IcdTransitStatus.SEAL_TAMPERED
    assert res.customs_clearance_granted is False
    assert "CẢNH BÁO NIÊM PHONG" in res.action_directive


def test_icd_transit_insufficient_guarantee():
    """Verify guarantee shortfall (< 1.0 coverage ratio) blocks clearance."""
    data = IcdTransitInput(
        declaration_no="OLA-2026-005",
        container_no="TEMU1234571",
        origin_seaport_code="VNCME",
        dest_icd_code="VNSTH",
        distance_km=70.0,
        max_transit_hours=12.0,
        departure_time_iso="2026-10-08T06:00:00",
        arrival_time_iso="2026-10-08T10:00:00",
        customs_seal_intact=True,
        bank_guarantee_amount_vnd=300_000_000.0,
        declared_tax_liability_vnd=400_000_000.0,  # Ratio = 0.75 < 1.0
    )
    res = IcdBondedTransitEngine.supervise_icd_transit(data)

    assert res.transit_status == IcdTransitStatus.DUTY_GUARANTEE_DEFICIT
    assert res.customs_clearance_granted is False
    assert "THIẾU HỤT BẢO LÃNH" in res.action_directive


def test_icd_transit_invalid_timestamp_grace():
    """Verify parser gracefully falls back to 0.0h when timestamps are invalid."""
    data = IcdTransitInput(
        declaration_no="OLA-2026-006",
        container_no="TEMU1234572",
        origin_seaport_code="VNCME",
        dest_icd_code="VNSTH",
        distance_km=70.0,
        max_transit_hours=12.0,
        departure_time_iso="invalid-dep",
        arrival_time_iso="invalid-arr",
        customs_seal_intact=True,
        bank_guarantee_amount_vnd=500_000_000.0,
        declared_tax_liability_vnd=400_000_000.0,
    )
    res = IcdBondedTransitEngine.supervise_icd_transit(data)

    assert res.actual_transit_hours == 0.0
    assert res.transit_status == IcdTransitStatus.ON_TIME_SECURE


# ==============================================================================
# Typer CLI Integration Tests (8 Command Aliases)
# ==============================================================================

def test_cli_ows_evaluate_primary_and_alias():
    """Verify CLI `ows evaluate` and bilingual alias `tachdaula evaluate`."""
    res1 = runner.invoke(app, ["ows", "evaluate", "--vessel", "MV PACIFIC", "--ppm", "7.5"])
    assert res1.exit_code == 0
    assert "THIẾT BỊ PHÂN LY DẦU NƯỚC (OWS) 15 PPM" in res1.stdout
    assert "MV PACIFIC" in res1.stdout

    res2 = runner.invoke(app, ["tachdaula", "evaluate", "--vessel", "MV PACIFIC", "--ppm", "16.0"])
    assert res2.exit_code == 0
    assert "RECIRCULATE_TO_HOLDING_TANK" in res2.stdout


def test_cli_mlcwages_calculate_primary_and_alias():
    """Verify CLI `mlcwages calculate` and bilingual alias `luongthuyenvien calculate`."""
    res1 = runner.invoke(app, ["mlcwages", "calculate", "--name", "PHAM VAN T", "--basic", "800"])
    assert res1.exit_code == 0
    assert "TÍNH LƯƠNG THUYỀN VIÊN & BẢO LÃNH HỒI HƯƠNG" in res1.stdout
    assert "PHAM VAN T" in res1.stdout

    res2 = runner.invoke(app, ["luongthuyenvien", "calculate", "--name", "PHAM VAN T", "--basic", "800"])
    assert res2.exit_code == 0
    assert "PHAM VAN T" in res2.stdout


def test_cli_mooring_calculate_primary_and_alias():
    """Verify CLI `mooring calculate` and bilingual alias `buocdaytau calculate`."""
    res1 = runner.invoke(app, ["mooring", "calculate", "--gt", "25000", "--op", "MOORING"])
    assert res1.exit_code == 0
    assert "CƯỚC BUỘC CỞI DÂY TÀU BIỂN" in res1.stdout

    res2 = runner.invoke(app, ["buocdaytau", "calculate", "--gt", "25000", "--op", "UNMOORING"])
    assert res2.exit_code == 0
    assert "UNMOORING" in res2.stdout


def test_cli_icdtransit_supervise_primary_and_alias():
    """Verify CLI `icdtransit supervise` and bilingual alias `cangcanicd supervise`."""
    res1 = runner.invoke(app, ["icdtransit", "supervise", "--declaration", "OLA-999", "--dist", "50"])
    assert res1.exit_code == 0
    assert "GIÁM SÁT VẬN CHUYỂN ĐỘC LẬP OLA" in res1.stdout
    assert "OLA-999" in res1.stdout

    res2 = runner.invoke(app, ["cangcanicd", "supervise", "--declaration", "OLA-999", "--dist", "50"])
    assert res2.exit_code == 0
    assert "OLA-999" in res2.stdout


# ==============================================================================
# FastMCP Handlers Integration Tests
# ==============================================================================

def test_mcp_ows_discharge_evaluate_handler():
    """Verify FastMCP tool `handle_ows_15ppm_discharge_evaluate` returns structured JSON."""
    raw = handle_ows_15ppm_discharge_evaluate({
        "vessel_name": "MV FAST TANKER",
        "imo_number": "9123456",
        "oil_content_ppm": 9.2,
        "vessel_speed_knots": 14.0,
        "distance_from_land_nm": 22.0,
        "is_special_area": False,
        "flow_rate_m3_h": 2.0,
        "discharge_duration_minutes": 30.0,
        "fail_safe_valve_operational": True,
    })
    payload = json.loads(raw)
    assert payload["ok"] is True
    data = payload["ows_evaluation"]
    assert data["vessel_name"] == "MV FAST TANKER"
    assert data["compliance_status"] == "COMPLIANT_DISCHARGE"
    assert data["valve_position"] == "OVERBOARD"
    assert data["total_discharged_m3"] == 1.0


def test_mcp_mlc_wages_calculate_handler():
    """Verify FastMCP tool `handle_mlc_seafarer_wages_calculate` returns structured JSON."""
    raw = handle_mlc_seafarer_wages_calculate({
        "seafarer_name": "NGUYEN SEAMAN",
        "rank": "AB",
        "basic_monthly_wage_usd": 750.0,
        "contract_months": 8,
        "actual_monthly_overtime_hours": 50.0,
        "guaranteed_overtime_hours": 48.0,
        "responsibility_allowance_usd": 50.0,
        "subsistence_allowance_usd": 50.0,
        "pni_repatriation_bond_amount_usd": 10000.0,
    })
    payload = json.loads(raw)
    assert payload["ok"] is True
    data = payload["mlc_wages"]
    assert data["seafarer_name"] == "NGUYEN SEAMAN"
    assert data["mlc_wage_compliant"] is True
    assert data["repatriation_bond_adequate"] is True


def test_mcp_port_mooring_tariff_calculate_handler():
    """Verify FastMCP tool `handle_port_mooring_tariff_calculate` returns structured JSON."""
    raw = handle_port_mooring_tariff_calculate({
        "vessel_name": "MV PACIFIC EXPRESS",
        "gross_tonnage": 32000.0,
        "operation_type": "MOORING",
        "is_night_operation": True,
        "is_holiday": False,
        "standby_hours": 0.0,
        "mooring_line_swl_tons": 45.0,
        "mooring_line_mbl_tons": 90.0,
    })
    payload = json.loads(raw)
    assert payload["ok"] is True
    data = payload["mooring_tariff"]
    assert data["vessel_name"] == "MV PACIFIC EXPRESS"
    assert data["base_charge_usd"] == 200.0
    assert data["night_surcharge_usd"] == 80.0
    assert data["total_charge_usd"] == 280.0
    assert data["meg4_safe"] is True


def test_mcp_icd_bonded_transit_supervise_handler():
    """Verify FastMCP tool `handle_icd_bonded_transit_supervise` returns structured JSON."""
    raw = handle_icd_bonded_transit_supervise({
        "declaration_no": "OLA-TEST-999",
        "container_no": "CONT8819231",
        "origin_seaport_code": "VNCME",
        "dest_icd_code": "VNSTH",
        "distance_km": 65.0,
        "max_transit_hours": 15.0,
        "departure_time_iso": "2026-10-08T07:00:00",
        "arrival_time_iso": "2026-10-08T11:00:00",
        "customs_seal_intact": True,
        "bank_guarantee_amount_vnd": 600000000.0,
        "declared_tax_liability_vnd": 500000000.0,
    })
    payload = json.loads(raw)
    assert payload["ok"] is True
    data = payload["icd_transit"]
    assert data["declaration_no"] == "OLA-TEST-999"
    assert data["transit_status"] == "ON_TIME_SECURE"
    assert data["customs_clearance_granted"] is True
