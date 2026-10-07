"""
CLI commands for Maritime Pilotage, Husbandry, Marine Insurance & Tokyo MOU PSC Suite (Phases 183-186).
"""

import dataclasses
import enum
import json
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.maritime_operations_engine import (
    PilotageTugboatTariffEngine,
    ShipAgencyCrewMLCEngine,
    MarineInsuranceRiskEngine,
    PortStateControlPSCEngine,
    PilotageArea,
    TugboatClass,
    SeafarerRank,
    DailyRestLog,
    PSCFlagStateStatus,
)

console = Console()


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    if dataclasses.is_dataclass(obj):
        data = dataclasses.asdict(obj)
    elif hasattr(obj, "__dict__"):
        data = obj.__dict__
    else:
        data = obj
    print(json.dumps(data, indent=2, default=_json_serial))

pilotage_app = typer.Typer(
    name="pilotage",
    help="Dịch vụ hoa tiêu & lai dắt tàu biển (TT 39/2023/TT-BGTVT)",
    no_args_is_help=True,
)

shipagency_app = typer.Typer(
    name="shipagency",
    help="Đại lý tàu biển & Thẩm định giờ nghỉ thuyền viên MLC 2006 (NĐ 160/2016)",
    no_args_is_help=True,
)

marineins_app = typer.Typer(
    name="marineins",
    help="Bảo hiểm hàng hải thân tàu ITC Hulls 83 & P&I Bunkers Convention 2001",
    no_args_is_help=True,
)

psc_app = typer.Typer(
    name="psc",
    help="Kiểm tra tàu biển Tokyo MOU Port State Control (NIR)",
    no_args_is_help=True,
)


# =====================================================================
# Pilotage Subcommands
# =====================================================================

@pilotage_app.command("tariff")
def pilotage_tariff_cmd(
    vessel_gt: float = typer.Argument(..., help="Tổng dung tích tàu biển (Gross Tonnage - GT)"),
    distance_nm: float = typer.Argument(..., help="Cự ly dẫn tàu hoa tiêu (Nautical Miles - NM)"),
    area: str = typer.Option("AREA_III", "--area", "-a", help="Khu vực hoa tiêu: AREA_I, AREA_II, AREA_III, OFFSHORE"),
    domestic: bool = typer.Option(False, "--domestic", "-d", help="Tuyến nội địa (VND) thay vì quốc tế (USD)"),
    night: bool = typer.Option(False, "--night", "-n", help="Ca đêm (18:00 - 06:00, +50%)"),
    hazardous: bool = typer.Option(False, "--hazardous", "-hz", help="Chở hàng nguy hiểm / IMO (+10%)"),
    dead_ship: bool = typer.Option(False, "--dead-ship", "-ds", help="Tàu mất chủ động (+150%)"),
    detention_hours: float = typer.Option(0.0, "--detention", "-dt", help="Thời gian chờ hoa tiêu (giờ)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Tính cước dẫn tàu hoa tiêu hàng hải theo Thông tư 39/2023/TT-BGTVT."""
    p_area = PilotageArea(area)
    res = PilotageTugboatTariffEngine.calculate_pilotage(
        vessel_gt=vessel_gt,
        distance_nm=distance_nm,
        area=p_area,
        is_international=not domestic,
        is_night_shift=night,
        is_hazardous_cargo=hazardous,
        is_dead_ship=dead_ship,
        detention_hours=detention_hours,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"BẢNG TÍNH CƯỚC HOA TIÊU HÀNG HẢI ({res.pilotage_area.value})", border_style="cyan")
    table.add_column("Chỉ số / Tiêu chí", style="bold")
    table.add_column("Giá trị áp dụng", style="green")

    table.add_row("Dung tích tàu thực tế (GT)", f"{res.vessel_gt:,.0f} GT")
    table.add_row("Dung tích tính cước tối thiểu", f"{res.billed_gt:,.0f} GT")
    table.add_row("Cự ly dẫn tàu", f"{res.distance_nm:.1f} NM")
    table.add_row("Hệ số phụ trội / Phụ phí", f"{res.surcharge_multiplier:.2f}x")
    table.add_row("Phí chờ hoa tiêu (Detention)", f"${res.detention_fee_usd:,.2f} USD")
    table.add_row("TỔNG CƯỚC HOA TIÊU (USD)", f"${res.total_pilotage_fee_usd:,.2f} USD")
    table.add_row("TỔNG CƯỚC HOA TIÊU (VND)", f"{res.total_pilotage_fee_vnd:,.0f} VND")

    console.print(table)


@pilotage_app.command("tugboat")
def tugboat_assistance_cmd(
    vessel_gt: float = typer.Argument(..., help="Gross Tonnage tàu"),
    loa: float = typer.Argument(..., help="Chiều dài lớn nhất của tàu (LOA meters)"),
    tug_class: str = typer.Option("CLASS_D", "--class", "-c", help="Cấp tàu lai: CLASS_A, CLASS_B, CLASS_C, CLASS_D, CLASS_E"),
    quantity: int = typer.Option(2, "--qty", "-q", help="Số lượng tàu lai dắt"),
    hours: float = typer.Option(2.0, "--hours", "-h", help="Thời gian lai dắt thực tế (tối thiểu 2h)"),
    holiday: bool = typer.Option(False, "--holiday", help="Phụ thu ngày nghỉ / ngày lễ (+30%)"),
    dead_ship: bool = typer.Option(False, "--dead-ship", help="Hộ tống tàu mất chủ động (+50%)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Tính cước dịch vụ tàu lai dắt hỗ trợ cập/rời cầu cảng."""
    tugs_req = [{"tug_class": tug_class, "quantity": quantity, "duration_hours": hours}]
    res = PilotageTugboatTariffEngine.calculate_tugboat_assistance(
        vessel_gt=vessel_gt,
        vessel_loa_meters=loa,
        tugs_request=tugs_req,
        is_holiday_or_weekend=holiday,
        is_dead_ship_escort=dead_ship,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"BẢNG CƯỚC TÀU LAI HỖ TRỢ CẢNG BIỂN ({res.vessel_gt:,.0f} GT)", border_style="blue")
    table.add_column("Cấp tàu lai", style="bold")
    table.add_column("Số lượng", justify="center")
    table.add_column("Thời lượng (h)", justify="center")
    table.add_column("Đơn giá/h (USD)", justify="right")
    table.add_column("Thành tiền (USD)", justify="right", style="green")

    for t in res.tugs:
        table.add_row(t.tug_class.value, str(t.quantity), f"{t.duration_hours:.1f}", f"${t.hourly_rate_usd:,.2f}", f"${t.line_total_usd:,.2f}")

    table.add_section()
    table.add_row("TỔNG CƯỚC LAI DẮT (USD)", "", "", "", f"${res.total_tugboat_fee_usd:,.2f} USD")
    table.add_row("TỔNG CƯỚC LAI DẮT (VND)", "", "", "", f"{res.total_tugboat_fee_vnd:,.0f} VND")

    console.print(table)


# =====================================================================
# Ship Agency Subcommands
# =====================================================================

@shipagency_app.command("disbursement")
def agency_disbursement_cmd(
    vessel_name: str = typer.Argument(..., help="Tên tàu biển"),
    vessel_gt: float = typer.Argument(..., help="Gross Tonnage tàu"),
    stay_days: int = typer.Option(2, "--days", "-d", help="Số ngày lưu cảng"),
    ctm: float = typer.Option(0.0, "--ctm", help="Giao tiền mặt cho thuyền trưởng Cash-to-Master (USD)"),
    crew_changes: int = typer.Option(0, "--crew", "-c", help="Số lượng thuyền viên thay thế (Crew changes)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Tính phí đại lý tàu biển & giải ngân ủy thác (Disbursement Account)."""
    res = ShipAgencyCrewMLCEngine.calculate_agency_disbursement(
        vessel_name=vessel_name,
        vessel_gt=vessel_gt,
        port_stay_days=stay_days,
        ctm_amount_usd=ctm,
        crew_changes_count=crew_changes,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"BẢNG PHÍ ĐẠI LÝ TÀU BIỂN — {res.vessel_name.upper()}", border_style="magenta")
    table.add_column("Khoản mục phí", style="bold")
    table.add_column("Chi tiết / Giá trị (USD)", style="green")

    table.add_row("Phí đại lý cơ bản (Agency Fee)", f"${res.base_agency_fee_usd:,.2f} USD")
    table.add_row("Phí quản lý lưu cảng kéo dài", f"${res.extra_day_husbandry_usd:,.2f} USD")
    table.add_row("Hoa hồng Cash-to-Master (1.5%)", f"${res.ctm_commission_usd:,.2f} USD")
    table.add_row("Phí thủ tục thay đổi thuyền viên", f"${res.crew_change_fee_usd:,.2f} USD")
    table.add_section()
    table.add_row("TỔNG CHI PHÍ ĐẠI LÝ (USD)", f"${res.total_agency_disbursement_usd:,.2f} USD")
    table.add_row("TỔNG CHI PHÍ ĐẠI LÝ (VND)", f"{res.total_agency_disbursement_vnd:,.0f} VND")

    console.print(table)


@shipagency_app.command("mlc-check")
def seafarer_mlc_check_cmd(
    seafarer_name: str = typer.Argument(..., help="Họ tên thuyền viên"),
    rank: str = typer.Option("CHIEF_ENGINEER", "--rank", "-r", help="Chức danh thuyền viên"),
    sea_days: int = typer.Option(200, "--sea-days", "-s", help="Tổng số ngày đi biển liên tục"),
    rest_24h: float = typer.Option(11.0, "--rest-24h", help="Số giờ nghỉ ngơi trong 24h gần nhất"),
    longest_block: float = typer.Option(7.0, "--block", help="Thời lượng đoạn nghỉ liên tục dài nhất (giờ)"),
    periods: int = typer.Option(2, "--periods", help="Số đoạn nghỉ trong ngày (tối đa 2)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Thẩm định tuân thủ Công ước Lao động Hàng hải MLC 2006 về thời giờ nghỉ ngơi & hồi hương."""
    s_rank = SeafarerRank(rank)
    sample_log = [DailyRestLog(log_date="TODAY", total_rest_hours_24h=rest_24h, longest_continuous_rest_hours=longest_block, rest_periods_count=periods)] * 7
    res = ShipAgencyCrewMLCEngine.assess_seafarer_mlc(
        seafarer_name=seafarer_name,
        rank=s_rank,
        consecutive_sea_days=sea_days,
        daily_rest_logs=sample_log,
    )

    if json_output:
        _dump_json(res)
        return

    status_style = "green" if res.status.value == "COMPLIANT" else "red"
    console.print(Panel(
        f"[bold]Thuyền viên:[/bold] {res.seafarer_name} ({res.rank.value})\n"
        f"[bold]Ngày đi biển liên tục:[/bold] {res.consecutive_sea_days} ngày (Tối đa 330 ngày)\n"
        f"[bold]Tổng giờ nghỉ 7 ngày:[/bold] {res.rolling_7d_rest_hours:.1f}h / 77h chuẩn\n"
        f"[bold]Trạng thái tuân thủ:[/bold] [{status_style}]{res.status.value}[/{status_style}]\n"
        f"[bold]Yêu cầu hồi hương:[/bold] {'CÓ - BẮT BUỘC' if res.is_repatriation_due else 'KHÔNG'}\n"
        f"[bold]Vi phạm ghi nhận:[/bold] {', '.join(res.violations) if res.violations else 'Không phát hiện vi phạm'}",
        title="THẨM ĐỊNH TUÂN THỦ MLC 2006",
        border_style=status_style,
    ))


# =====================================================================
# Marine Insurance Subcommands
# =====================================================================

@marineins_app.command("hull-claim")
def hull_claim_cmd(
    policy_id: str = typer.Argument(..., help="Mã đơn bảo hiểm thân tàu"),
    agreed_val: float = typer.Argument(..., help="Giá trị thỏa thuận thân tàu (Agreed Insured Value USD)"),
    repair_est: float = typer.Argument(..., help="Chi phí cứu hộ & sửa chữa ước tính (USD)"),
    deductible: float = typer.Option(50000.0, "--deductible", "-d", help="Mức khấu trừ bảo hiểm (Deductible USD)"),
    casualty_date: Optional[str] = typer.Option(None, "--casualty-date", help="Ngày xảy ra tai nạn (YYYY-MM-DD)"),
    assessment_date: Optional[str] = typer.Option(None, "--assess-date", help="Ngày giám định (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Tính bồi thường bảo hiểm thân tàu ITC Hulls 83 & Thẩm định Tổn thất toàn bộ ước tính (CTL)."""
    res = MarineInsuranceRiskEngine.assess_hull_claim(
        policy_id=policy_id,
        agreed_insured_value_usd=agreed_val,
        estimated_repair_and_salvage_usd=repair_est,
        policy_deductible_usd=deductible,
        casualty_date_iso=casualty_date,
        assessment_date_iso=assessment_date,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"KẾT QUẢ GIÁM ĐỊNH TỔN THẤT THÂN TÀU ({res.policy_id})", border_style="yellow")
    table.add_column("Thông số giám định", style="bold")
    table.add_column("Giá trị", style="green")

    table.add_row("Giá trị bảo hiểm thỏa thuận", f"${res.agreed_insured_value_usd:,.2f} USD")
    table.add_row("Chi phí sửa chữa & cứu hộ", f"${res.estimated_repair_and_salvage_usd:,.2f} USD")
    table.add_row("Tỷ lệ tổn thất (Loss Ratio)", f"{res.loss_ratio_percent:.2f}% (Ngưỡng CTL: 80%)")
    table.add_row("Loại hình tổn thất", res.claim_type.value)
    table.add_row("Yêu cầu thông báo từ bỏ tàu (NOA)", "BẮT BUỘC" if res.notice_of_abandonment_required else "KHÔNG")
    table.add_row("SỐ TIỀN BỒI THƯỜNG BẢO HIỂM", f"${res.net_payable_claim_usd:,.2f} USD")

    console.print(table)


@marineins_app.command("pi-pollution")
def pi_pollution_cmd(
    vessel_gt: float = typer.Argument(..., help="Gross Tonnage tàu biển"),
    sdr_rate: float = typer.Option(1.34, "--sdr-rate", help="Tỷ giá SDR/USD"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Tính hạn mức trách nhiệm dân sự bồi thường ô nhiễm dầu P&I (Bunkers Convention 2001)."""
    res = MarineInsuranceRiskEngine.calculate_pi_bunker_pollution_limit(
        vessel_gt=vessel_gt,
        sdr_usd_rate=sdr_rate,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"HẠN MỨC TRÁCH NHIỆM Ô NHIỄM DẦU P&I ({res.vessel_gt:,.0f} GT)", border_style="red")
    table.add_column("Quy chuẩn / Mức trách nhiệm", style="bold")
    table.add_column("Giá trị quy đổi", style="green")

    table.add_row("Hạn mức trách nhiệm (SDR)", f"{res.liability_limit_sdr:,.2f} SDR")
    table.add_row("Hạn mức trách nhiệm (USD)", f"${res.liability_limit_usd:,.2f} USD")
    table.add_row("Hạn mức trách nhiệm (VND)", f"{res.liability_limit_vnd:,.0f} VND")
    table.add_row("Chứng chỉ tài chính bắt buộc (CLC)", "CÓ (Bắt buộc với tàu >= 1,000 GT)" if res.is_compulsory_clc_cert_required else "KHÔNG")

    console.print(table)


# =====================================================================
# Port State Control (PSC) Subcommands
# =====================================================================

@psc_app.command("risk-profile")
def psc_risk_profile_cmd(
    imo: str = typer.Argument(..., help="Số hiệu IMO tàu biển"),
    vessel_type: str = typer.Argument(..., help="Loại tàu (CONTAINER, BULK_CARRIER, OIL_TANKER, CHEMICAL_TANKER, GENERAL_CARGO)"),
    age: int = typer.Argument(..., help="Tuổi tàu (năm)"),
    flag: str = typer.Option("WHITE_LIST", "--flag", "-f", help="Trạng thái Flag: WHITE_LIST, GREY_LIST, BLACK_LIST_MEDIUM, BLACK_LIST_HIGH, BLACK_LIST_VERY_HIGH"),
    ro_low: bool = typer.Option(False, "--ro-low", help="Tổ chức Đăng kiểm (RO) hiệu suất thấp (+2 điểm)"),
    company_low: bool = typer.Option(False, "--company-low", help="Công ty quản lý tàu ISM hiệu suất thấp (+2 điểm)"),
    detentions: int = typer.Option(0, "--detentions", "-d", help="Số lần bị lưu giữ (Detentions) trong 36 tháng qua"),
    deficiencies: int = typer.Option(0, "--deficiencies", help="Tổng số khiếm khuyết trong 36 tháng qua"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Tính điểm hồ sơ rủi ro tàu biển (Ship Risk Profile) theo Tokyo MOU NIR."""
    flag_st = PSCFlagStateStatus(flag)
    res = PortStateControlPSCEngine.evaluate_ship_risk_profile(
        vessel_imo=imo,
        vessel_type=vessel_type,
        vessel_age_years=age,
        flag_status=flag_st,
        ro_performance_low=ro_low,
        company_performance_low=company_low,
        detentions_last_36m=detentions,
        deficiencies_last_36m=deficiencies,
    )

    if json_output:
        _dump_json(res)
        return

    badge_color = "green" if res.risk_profile.value == "LOW_RISK_SHIP" else ("yellow" if res.risk_profile.value == "STANDARD_RISK_SHIP" else "red")
    table = Table(title=f"HỒ SƠ RỦI RO TOKYO MOU PSC — IMO {res.vessel_imo}", border_style=badge_color)
    table.add_column("Chỉ số đánh giá NIR", style="bold")
    table.add_column("Kết quả", style=badge_color)

    table.add_row("Điểm rủi ro chung (Generic Points)", str(res.generic_risk_points))
    table.add_row("Điểm rủi ro lịch sử (Historic Points)", str(res.historic_risk_points))
    table.add_row("TỔNG ĐIỂM RỦI RO (Total Points)", str(res.total_risk_points))
    table.add_row("PHÂN LOẠI RỦI RO (Ship Risk Profile)", res.risk_profile.value)
    table.add_row("Cửa sổ kiểm tra định kỳ (Inspection Window)", res.next_inspection_window_months)

    console.print(table)


@psc_app.command("deficiency")
def psc_deficiency_cmd(
    imo: str = typer.Argument(..., help="Số hiệu IMO tàu"),
    deficiency_codes: str = typer.Option("", "--codes", "-c", help="Danh sách mã khiếm khuyết (phân tách dấu phẩy)"),
    solas_fire: bool = typer.Option(False, "--solas-fire", help="Khiếm khuyết nghiêm trọng PCCC SOLAS Ch. II-2"),
    marpol_oil: bool = typer.Option(False, "--marpol-oil", help="Khiếm khuyết phân ly dầu nước MARPOL Annex I"),
    mlc_wage: bool = typer.Option(False, "--mlc-wage", help="Khiếm khuyết nợ lương / thiếu nước uống MLC 2006"),
    json_output: bool = typer.Option(False, "--json", help="Xuất định dạng JSON"),
):
    """Đánh giá khiếm khuyết PSC và cảnh báo nguy cơ Lưu giữ tàu (Detention Code 30)."""
    codes = [c.strip() for c in deficiency_codes.split(",") if c.strip()]
    res = PortStateControlPSCEngine.evaluate_deficiencies(
        vessel_imo=imo,
        deficiency_codes=codes,
        has_solas_fire_or_lifesaving_breach=solas_fire,
        has_marpol_annex_i_oily_water_breach=marpol_oil,
        has_mlc_wage_or_food_breach=mlc_wage,
    )

    if json_output:
        _dump_json(res)
        return

    style = "red" if res.is_code_30_detention else "green"
    console.print(Panel(
        f"[bold]Tàu IMO:[/bold] {res.vessel_imo}\n"
        f"[bold]Tổng số khiếm khuyết:[/bold] {len(res.deficiency_codes)}\n"
        f"[bold]Hành động khuyến nghị:[/bold] [{style}]{res.recommended_action.value}[/{style}]\n"
        f"[bold]Lưu giữ tàu (Code 30):[/bold] {'CÓ - NGUY CƠ RẤT CAO' if res.is_code_30_detention else 'KHÔNG'}\n"
        f"[bold]Ghi chú hành động:[/bold] {res.action_notes}",
        title="ĐÁNH GIÁ KHIẾM KHUYẾT PSC TOKYO MOU",
        border_style=style,
    ))
