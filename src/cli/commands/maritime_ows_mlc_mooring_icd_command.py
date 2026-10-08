"""CLI Commands for OWS 15 ppm, MLC Seafarer Wages, Mooring Tariffs & ICD Transit Suite.

Phases 283-286 Maritime Operations, Secured Finance & Customs Logistics Suite.
"""

import typer

from src.core.maritime_ows_mlc_mooring_icd_engine import (
    IcdBondedTransitEngine,
    IcdTransitInput,
    MlcSeafarerWagesEngine,
    MooringOperationType,
    MooringTariffInput,
    OwsDischargeEngine,
    OwsDischargeInput,
    PortMooringTariffEngine,
    SeafarerContractInput,
)

# Typer Command Groups
ows_app = typer.Typer(help="Oil Water Separator (OWS) 15 ppm & Oil Record Book Engine (Phase 283)")
mlcwages_app = typer.Typer(help="Seafarer Wages MLC 2006 & Repatriation Escrow Engine (Phase 284)")
mooring_app = typer.Typer(help="Port Mooring Tariffs & MEG4 Mooring Safety Engine (Phase 285)")
icdtransit_app = typer.Typer(help="ICD Bonded Transit & Customs OLA Declaration Engine (Phase 286)")


# ------------------------------------------------------------------------------
# Phase 283: OWS 15 ppm & ORB Discharge Command
# ------------------------------------------------------------------------------

@ows_app.command("evaluate")
def evaluate_ows_discharge(
    vessel: str = typer.Option("MV MEKONG ODYSSEY", "--vessel", "-v", help="Vessel name"),
    imo: str = typer.Option("9918234", "--imo", help="IMO number"),
    ppm: float = typer.Option(8.4, "--ppm", help="Oil content in ppm from 15 ppm Bilge Alarm"),
    speed: float = typer.Option(12.5, "--speed", help="Vessel speed in knots"),
    dist: float = typer.Option(25.4, "--dist", help="Distance from nearest land in nautical miles"),
    special_area: bool = typer.Option(False, "--special-area", help="Is vessel located in MARPOL Special Area"),
    flow: float = typer.Option(2.5, "--flow", help="Discharge flow rate in m3/h"),
    duration: float = typer.Option(60.0, "--duration", help="Discharge duration in minutes"),
    valve_ok: bool = typer.Option(True, "--valve-ok", help="Is 3-way fail-safe valve operational"),
):
    """
    Evaluate Bilge Water Discharge compliance under MARPOL Annex I & MEPC.107(49).
    """
    sample = OwsDischargeInput(
        vessel_name=vessel,
        imo_number=imo,
        oil_content_ppm=ppm,
        vessel_speed_knots=speed,
        distance_from_land_nm=dist,
        is_special_area=special_area,
        flow_rate_m3_h=flow,
        discharge_duration_minutes=duration,
        fail_safe_valve_operational=valve_ok,
    )
    result = OwsDischargeEngine.evaluate_discharge(sample)

    typer.echo("================================================================================")
    typer.echo("THIẾT BỊ PHÂN LY DẦU NƯỚC (OWS) 15 PPM & NHẬT KÝ DẦU (MARPOL ANNEX I)")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {result.vessel_name} | IMO: {result.imo_number}")
    typer.echo(f"Hàm lượng dầu đo được: {result.oil_content_ppm:.1f} ppm (Giới hạn tối đa: 15.0 ppm)")
    typer.echo(f"Trạng thái tuân thủ: {result.compliance_status.value}")
    typer.echo(f"Vị trí van xả 3 ngả: {result.valve_position}")
    typer.echo(f"Khối lượng xả qua mạn: {result.total_discharged_m3:.3f} m3")
    typer.echo(f"Mã nhật ký dầu ORB: {result.orb_code}")
    typer.echo(f"Ghi chép mẫu ORB: {result.orb_entry}")
    typer.echo(f"Chỉ thị hành động: {result.action_required}")
    typer.echo(f"Mã xác thực điện tử: {result.verification_token}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 284: MLC 2006 Wages & Repatriation Escrow Command
# ------------------------------------------------------------------------------

@mlcwages_app.command("calculate")
def calculate_mlc_wages(
    name: str = typer.Option("NGUYEN VAN A", "--name", "-n", help="Seafarer full name"),
    rank: str = typer.Option("Able Seaman (AB)", "--rank", "-r", help="Seafarer rank"),
    basic: float = typer.Option(750.0, "--basic", help="Basic monthly wage in USD"),
    contract_months: int = typer.Option(9, "--months", help="Contract duration in months"),
    ot_hours: float = typer.Option(65.0, "--ot-hours", help="Actual overtime hours performed"),
    guaranteed_ot: float = typer.Option(48.0, "--guaranteed-ot", help="Guaranteed overtime hours in SEA"),
    resp_allowance: float = typer.Option(100.0, "--resp", help="Responsibility allowance in USD"),
    sub_allowance: float = typer.Option(50.0, "--sub", help="Subsistence allowance in USD"),
    pni_bond: float = typer.Option(12000.0, "--pni-bond", help="P&I repatriation financial security bond in USD"),
):
    """
    Calculate Seafarer Wages Statement and Abandonment Escrow per MLC 2006 Standard A2.2/A2.5.
    """
    contract = SeafarerContractInput(
        seafarer_name=name,
        rank=rank,
        basic_monthly_wage_usd=basic,
        contract_months=contract_months,
        actual_monthly_overtime_hours=ot_hours,
        guaranteed_overtime_hours=guaranteed_ot,
        responsibility_allowance_usd=resp_allowance,
        subsistence_allowance_usd=sub_allowance,
        pni_repatriation_bond_amount_usd=pni_bond,
    )
    result = MlcSeafarerWagesEngine.calculate_wages_and_escrow(contract)

    typer.echo("================================================================================")
    typer.echo("TÍNH LƯƠNG THUYỀN VIÊN & BẢO LÃNH HỒI HƯƠNG (MLC 2006 STANDARD A2.2 & A2.5)")
    typer.echo("================================================================================")
    typer.echo(f"Thuyền viên: {result.seafarer_name} | Chức danh: {result.rank}")
    typer.echo(f"Lương cơ bản tháng: ${result.basic_monthly_wage_usd:,.2f} USD")
    typer.echo(f"Lương giờ cơ bản: ${result.hourly_basic_rate_usd:,.2f}/h | Đơn giá làm thêm (1.25x): ${result.overtime_hourly_rate_usd:,.2f}/h")
    typer.echo(f"Số giờ làm thêm tính trả: {result.payable_overtime_hours:.1f}h | Tiền làm thêm: ${result.overtime_pay_usd:,.2f} USD")
    typer.echo(f"Tiền nghỉ phép tích lũy (2.5 ngày/tháng): ${result.paid_annual_leave_pay_usd:,.2f} USD")
    typer.echo(f"Tổng phụ cấp: ${result.allowances_total_usd:,.2f} USD")
    typer.echo(f"TỔNG LƯƠNG THỰC LĨNH: ${result.gross_monthly_wage_usd:,.2f} USD ({result.gross_monthly_wage_vnd:,.0f} VND)")
    typer.echo(f"Dự phòng hồi hương 4 tháng (Standard A2.5.2): ${result.abandonment_reserve_4m_usd:,.2f} USD")
    typer.echo(f"Bảo lãnh P&I đủ điều kiện: {'CÓ' if result.repatriation_bond_adequate else 'KHÔNG (THIẾU HỤT)'}")
    typer.echo(f"Tuân thủ mức lương tối thiểu ILO: {'ĐẠT CHUẨN' if result.mlc_wage_compliant else 'DƯỚI CHUẨN'}")
    typer.echo(f"Mã chứng thực SEA: {result.sea_auth_token}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 285: Port Mooring Tariffs & MEG4 Command
# ------------------------------------------------------------------------------

@mooring_app.command("calculate")
def calculate_mooring_dues(
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", "-v", help="Vessel name"),
    gt: float = typer.Option(35000.0, "--gt", help="Gross Tonnage (GT) of vessel"),
    op: str = typer.Option("MOORING", "--op", help="Operation type: MOORING, UNMOORING, SHIFTING"),
    night: bool = typer.Option(False, "--night", help="Is operation during night hours (18:00 - 06:00)"),
    holiday: bool = typer.Option(False, "--holiday", help="Is operation during national holidays"),
    standby: float = typer.Option(0.0, "--standby", help="Standby/waiting hours caused by vessel"),
    swl: float = typer.Option(50.0, "--swl", help="Mooring line Safe Working Load (SWL) in tons"),
    mbl: float = typer.Option(90.0, "--mbl", help="Mooring line Minimum Breaking Load (MBL) in tons"),
):
    """
    Calculate Port Mooring / Unmooring Tariffs under Circular 39/2023 & OCIMF MEG4 Safety.
    """
    op_type = MooringOperationType(op.upper())
    input_data = MooringTariffInput(
        vessel_name=vessel,
        gross_tonnage=gt,
        operation_type=op_type,
        is_night_operation=night,
        is_holiday=holiday,
        standby_hours=standby,
        mooring_line_swl_tons=swl,
        mooring_line_mbl_tons=mbl,
    )
    result = PortMooringTariffEngine.calculate_mooring_dues(input_data)

    typer.echo("================================================================================")
    typer.echo("CƯỚC BUỘC CỞI DÂY TÀU BIỂN & AN TOÀN DÂY MEG4 (THÔNG TƯ 39/2023/TT-BGTVT)")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {result.vessel_name} | Dung tích: {result.gross_tonnage:,.0f} GT | Thao tác: {result.operation_type.value}")
    typer.echo(f"Cước cơ bản: ${result.base_charge_usd:,.2f} USD")
    typer.echo(f"Phụ thu ban đêm (+40%): ${result.night_surcharge_usd:,.2f} USD")
    typer.echo(f"Phụ thu ngày lễ (+50%): ${result.holiday_surcharge_usd:,.2f} USD")
    typer.echo(f"Phí chờ đợi cầu bến: ${result.standby_charge_usd:,.2f} USD")
    typer.echo(f"TỔNG CƯỚC DỊCH VỤ: ${result.total_charge_usd:,.2f} USD ({result.total_charge_vnd:,.0f} VND)")
    typer.echo("Kiểm tra an toàn dây neo (OCIMF MEG4):")
    typer.echo(f"- Tỷ lệ tải SWL/MBL: {result.meg4_line_tension_ratio*100:.1f}%")
    typer.echo(f"- Đạt chuẩn an toàn (<= 60%): {'AN TOÀN' if result.meg4_safe else 'NGUY HIỂM'}")
    typer.echo(f"- Ghi chú an toàn: {result.meg4_notes}")
    typer.echo(f"Mã biên lai thu cước: {result.receipt_code}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 286: ICD Bonded Transit & OLA Command
# ------------------------------------------------------------------------------

@icdtransit_app.command("supervise")
def supervise_icd_transit(
    declaration: str = typer.Option("OLA-2026-TC89102", "--declaration", "-d", help="Customs OLA declaration no"),
    container: str = typer.Option("TEMU9918231", "--container", "-c", help="Container number"),
    origin: str = typer.Option("VNCME", "--origin", help="Origin seaport code"),
    dest: str = typer.Option("VNSTH", "--dest", help="Destination ICD code"),
    dist: float = typer.Option(68.5, "--dist", help="Transit distance in km"),
    max_hours: float = typer.Option(18.0, "--max-hours", help="Permissible transit duration in hours"),
    dep: str = typer.Option("2026-10-08T06:00:00", "--dep", help="Departure timestamp ISO"),
    arr: str = typer.Option("2026-10-08T10:30:00", "--arr", help="Arrival timestamp ISO"),
    seal_ok: bool = typer.Option(True, "--seal-ok", help="Is customs seal intact and undamaged"),
    guarantee_vnd: float = typer.Option(500_000_000.0, "--guarantee", help="Bank guarantee amount in VND"),
    tax_vnd: float = typer.Option(450_000_000.0, "--tax", help="Declared tax liability in VND"),
):
    """
    Supervise ICD Road Transit & OLA Declaration under Customs Law 2014 & Decree 08/2015.
    """
    data = IcdTransitInput(
        declaration_no=declaration,
        container_no=container,
        origin_seaport_code=origin,
        dest_icd_code=dest,
        distance_km=dist,
        max_transit_hours=max_hours,
        departure_time_iso=dep,
        arrival_time_iso=arr,
        customs_seal_intact=seal_ok,
        bank_guarantee_amount_vnd=guarantee_vnd,
        declared_tax_liability_vnd=tax_vnd,
    )
    result = IcdBondedTransitEngine.supervise_icd_transit(data)

    typer.echo("================================================================================")
    typer.echo("GIÁM SÁT VẬN CHUYỂN ĐỘC LẬP OLA & CẢNG CẠN ICD (LUẬT HẢI QUAN 2014)")
    typer.echo("================================================================================")
    typer.echo(f"Tờ khai OLA: {result.declaration_no} | Container: {result.container_no}")
    typer.echo(f"Thời gian vận chuyển thực tế: {result.actual_transit_hours:.2f}h / Quy định: {result.max_transit_hours:.2f}h")
    typer.echo(f"Tỷ lệ bảo lãnh thuế: {result.duty_coverage_ratio*100:.1f}%")
    typer.echo(f"Trạng thái hành trình: {result.transit_status.value}")
    typer.echo(f"Cấp phép thông quan đến đích: {'CHO PHÉP' if result.customs_clearance_granted else 'TỪ CHỐI / CẢNH BÁO'}")
    typer.echo(f"Chỉ thị giám sát: {result.action_directive}")
    typer.echo(f"Mã tra cứu VNACCS: {result.tracking_token}")
    typer.echo("================================================================================")
