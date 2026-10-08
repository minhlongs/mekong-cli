"""Typer CLI Commands for Seaport Vessel Traffic Service (VTS), Cold Ironing Shore Power, Green Port GHG MRV & Marine Bunkering.

Phases 239-242:
- Phase 239: mekong vtsreporting check / speed / cpa / tariff
- Phase 240: mekong coldironing energy / emissions / cost
- Phase 241: mekong greenportghg cii / rating
- Phase 242: mekong marinebunkering bdn / safety / volume
"""

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_vts_coldironing_ghg_bunkering_engine import (
    VesselTrafficServiceEngine,
    ColdIroningEngine,
    GreenPortGhgCiiEngine,
    CiiShipType,
    CiiRatingGrade,
    MarineBunkeringSafetyEngine,
    BunkerGrade,
)

console = Console()

vtsreporting_app = typer.Typer(
    name="vtsreporting",
    help="Báo cáo VTS, kiểm soát tốc độ luồng hàng hải & cảnh báo va chạm CPA/TCPA (Phase 239).",
)
coldironing_app = typer.Typer(
    name="coldironing",
    help="Cấp điện bờ Onshore Power Supply (OPS/Cold Ironing), giảm phát thải & chi phí (Phase 240).",
)
greenportghg_app = typer.Typer(
    name="greenportghg",
    help="Đo lường phát thải Cảng xanh, xếp hạng IMO CII (A-E) & ưu đãi giá phí (Phase 241).",
)
marinebunkering_app = typer.Typer(
    name="marinebunkering",
    help="An toàn cấp dầu tàu biển, thẩm định phiếu BDN, giới hạn lưu huỳnh & chuẩn ASTM (Phase 242).",
)


# ==============================================================================
# PHASE 239: VESSEL TRAFFIC SERVICE (VTS) COMMANDS
# ==============================================================================

@vtsreporting_app.command(name="check")
def check_vts_reporting_cmd(
    hours: float = typer.Option(2.5, "--hours", "-h", help="Số giờ báo cáo trước khi đến trạm/điểm kiểm tra VTS"),
    checkpoint: str = typer.Option("Vung Tau Pilot Station Point 0", "--checkpoint", "-c", help="Tên điểm kiểm soát VTS"),
    required_hours: float = typer.Option(2.0, "--req-hours", help="Quy định số giờ phải báo cáo trước theo luật"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra tuân thủ thời hạn báo cáo VTS vào luồng theo Nghị định 58/2017/NĐ-CP."""
    res = VesselTrafficServiceEngine.check_vts_reporting(
        hours_before_checkpoint=hours,
        checkpoint_name=checkpoint,
        required_advance_hours=required_hours,
    )

    data = {
        "is_compliant": res.is_compliant,
        "status": res.status.value,
        "hours_before_checkpoint": res.hours_before_checkpoint,
        "required_advance_hours": res.required_advance_hours,
        "discrepancy_hours": res.discrepancy_hours,
        "notes": res.notes,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_compliant else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ THẨM ĐỊNH BÁO CÁO VTS HÀNG HẢI[/bold {color}]\n"
        f"• Điểm kiểm soát: [cyan]{checkpoint}[/cyan]\n"
        f"• Trạng thái: [bold]{res.status.value.upper()}[/bold]\n"
        f"• Hợp lệ: [bold]{'ĐẠT CHUẨN' if res.is_compliant else 'VI PHẠM'}[/bold]\n"
        f"• Báo trước: {res.hours_before_checkpoint:.1f}h (Yêu cầu: {res.required_advance_hours:.1f}h)\n"
        f"• Chênh lệch: {res.discrepancy_hours:.1f}h",
        title="VTS Reporting Check",
        border_style=color,
    ))


@vtsreporting_app.command(name="speed")
def check_fairway_speed_cmd(
    speed: float = typer.Option(11.5, "--speed", "-s", help="Tốc độ hành hải thực tế của tàu (knots)"),
    limit: float = typer.Option(12.0, "--limit", "-l", help="Giới hạn tốc độ luồng quy định (knots)"),
    zone: str = typer.Option("inner_channel", "--zone", "-z", help="Khu vực luồng: inner_channel, outer_channel, berth_approach"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra giới hạn tốc độ luồng hàng hải và nguy cơ sóng cuộn (wake wash)."""
    res = VesselTrafficServiceEngine.evaluate_fairway_speed(
        actual_speed_knots=speed,
        max_allowed_speed_knots=limit,
        fairway_zone=zone,
    )

    data = {
        "actual_speed_knots": res.actual_speed_knots,
        "max_allowed_speed_knots": res.max_allowed_speed_knots,
        "is_speeding": res.is_speeding,
        "speed_excess_knots": res.speed_excess_knots,
        "wake_wash_hazard": res.wake_wash_hazard,
        "reprimand_level": res.reprimand_level,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "red" if res.is_speeding else "green"
    console.print(Panel(
        f"[bold {color}]KIỂM TRA TỐC ĐỘ HÀNH HẢI TRONG LUỒNG VTS[/bold {color}]\n"
        f"• Tốc độ thực tế: [bold]{res.actual_speed_knots:.1f} kts[/bold] (Giới hạn: {res.max_allowed_speed_knots:.1f} kts)\n"
        f"• Vượt tốc: {'CÓ - ' + str(res.speed_excess_knots) + ' kts' if res.is_speeding else 'KHÔNG'}\n"
        f"• Cảnh báo sóng đập bến (Wake Wash): {'CẢNH BÁO NGUY HIỂM' if res.wake_wash_hazard else 'AN TOÀN'}\n"
        f"• Chế tài xử lý: [yellow]{res.reprimand_level}[/yellow]",
        title="Fairway Speed Check",
        border_style=color,
    ))


@vtsreporting_app.command(name="cpa")
def calculate_cpa_cmd(
    own_speed: float = typer.Option(12.0, "--own-speed", help="Tốc độ tàu ta (knots)"),
    own_course: float = typer.Option(90.0, "--own-course", help="Hướng đi tàu ta (độ)"),
    target_x: float = typer.Option(2.0, "--target-x", help="Khoảng cách tọa độ X mục tiêu (NM)"),
    target_y: float = typer.Option(3.0, "--target-y", help="Khoảng cách tọa độ Y mục tiêu (NM)"),
    target_speed: float = typer.Option(10.0, "--target-speed", help="Tốc độ tàu mục tiêu (knots)"),
    target_course: float = typer.Option(270.0, "--target-course", help="Hướng đi tàu mục tiêu (độ)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán khoảng cách tiếp cận gần nhất (CPA) và thời gian đến CPA (TCPA)."""
    res = VesselTrafficServiceEngine.calculate_cpa_tcpa(
        own_x=0.0,
        own_y=0.0,
        own_speed_knots=own_speed,
        own_course_deg=own_course,
        target_x=target_x,
        target_y=target_y,
        target_speed_knots=target_speed,
        target_course_deg=target_course,
    )

    data = {
        "cpa_nautical_miles": res.cpa_nautical_miles,
        "tcpa_minutes": res.tcpa_minutes,
        "risk_level": res.risk_level.value,
        "action_required": res.action_required,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "red" if res.risk_level.value == "critical" else ("yellow" if res.risk_level.value == "warning" else "green")
    console.print(Panel(
        f"[bold {color}]ĐÁNH GIÁ NGUY CƠ VA CHẠM HÀNG HẢI (CPA & TCPA)[/bold {color}]\n"
        f"• Khoảng cách tiếp cận CPA: [bold]{res.cpa_nautical_miles:.2f} NM[/bold]\n"
        f"• Thời gian đến CPA (TCPA): [bold]{res.tcpa_minutes:.1f} phút[/bold]\n"
        f"• Mức độ rủi ro: [bold {color}]{res.risk_level.value.upper()}[/bold {color}]\n"
        f"• Hành động khuyến nghị: [cyan]{res.action_required}[/cyan]",
        title="Collision Risk Assessment",
        border_style=color,
    ))


@vtsreporting_app.command(name="tariff")
def calculate_vts_tariff_cmd(
    gt: float = typer.Option(20000.0, "--gt", help="Tổng dung tích Gross Tonnage (GT)"),
    intl: bool = typer.Option(True, "--intl/--domestic", help="Tuyến vận chuyển quốc tế hay nội địa"),
    dist: float = typer.Option(18.0, "--dist", help="Khoảng cách dẫn đường trong vùng VTS (hải lý)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính giá dịch vụ giám sát và hỗ trợ điều động VTS theo Thông tư 39/2023/TT-BGTVT."""
    res = VesselTrafficServiceEngine.calculate_vts_tariff(
        gross_tonnage=gt,
        is_international=intl,
        transit_distance_nm=dist,
    )

    data = {
        "gross_tonnage": res.gross_tonnage,
        "base_rate": res.base_rate,
        "channel_transit_fee": res.channel_transit_fee,
        "surveillance_charge": res.surveillance_charge,
        "total_fee": res.total_fee,
        "currency": res.currency,
        "audit_hash": res.audit_hash,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Biểu Phí Dịch Vụ VTS Hàng Hải (Thông tư 39/2023/TT-BGTVT)")
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị", style="green")
    table.add_row("Tổng dung tích (GT)", f"{res.gross_tonnage:,.0f} GT")
    table.add_row("Đơn giá cơ sở", f"{res.base_rate} {res.currency}/GT")
    table.add_row("Phí qua luồng", f"{res.channel_transit_fee:,.2f} {res.currency}")
    table.add_row("Phí giám sát radar VTS", f"{res.surveillance_charge:,.2f} {res.currency}")
    table.add_row("TỔNG PHÍ DỊCH VỤ VTS", f"{res.total_fee:,.2f} {res.currency}")
    table.add_row("Mã xác thực Audit Hash", f"{res.audit_hash}")
    console.print(table)


# ==============================================================================
# PHASE 240: COLD IRONING (OPS) SHORE POWER COMMANDS
# ==============================================================================

@coldironing_app.command(name="energy")
def cold_ironing_energy_cmd(
    power_mw: float = typer.Option(2.5, "--power", "-p", help="Công suất phụ tải tàu tại bến (MW)"),
    hours: float = typer.Option(24.0, "--hours", "-h", help="Thời gian neo đậu cấp điện tại cầu cảng (giờ)"),
    grid_hz: int = typer.Option(50, "--grid-hz", help="Tần số lưới điện bờ (50 Hz tại VN)"),
    ship_hz: int = typer.Option(60, "--ship-hz", help="Tần số điện lưới trên tàu (60 Hz tiêu chuẩn)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán lượng điện năng cấp từ bờ và tổn hao chuyển đổi tần số Static Frequency Converter."""
    res = ColdIroningEngine.calculate_energy(
        hotel_power_mw=power_mw,
        berth_duration_hours=hours,
        grid_frequency_hz=grid_hz,
        ship_frequency_hz=ship_hz,
    )

    data = {
        "hotel_power_mw": res.hotel_power_mw,
        "berth_duration_hours": res.berth_duration_hours,
        "total_energy_mwh": res.total_energy_mwh,
        "grid_frequency_hz": res.grid_frequency_hz,
        "ship_frequency_hz": res.ship_frequency_hz,
        "converter_loss_mwh": res.converter_loss_mwh,
        "net_billed_mwh": res.net_billed_mwh,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Tính Toán Điện Năng Cấp Bờ (Cold Ironing / OPS)")
    table.add_column("Thông số", style="cyan")
    table.add_column("Kết quả", style="green")
    table.add_row("Công suất phụ tải tại bến", f"{res.hotel_power_mw} MW")
    table.add_row("Thời gian cấp điện", f"{res.berth_duration_hours} giờ")
    table.add_row("Tổng năng lượng tiêu thụ", f"{res.total_energy_mwh:.3f} MWh")
    table.add_row("Chuyển đổi tần số", f"{res.grid_frequency_hz} Hz → {res.ship_frequency_hz} Hz")
    table.add_row("Tổn hao bộ biến tần (SFC Loss)", f"{res.converter_loss_mwh:.3f} MWh")
    table.add_row("Điện năng thanh toán ghi nhận", f"{res.net_billed_mwh:.3f} MWh")
    console.print(table)


@coldironing_app.command(name="emissions")
def cold_ironing_emissions_cmd(
    mwh: float = typer.Option(60.0, "--mwh", help="Tổng năng lượng phụ tải tiêu thụ tại bến (MWh)"),
    billed_mwh: float = typer.Option(61.8, "--billed-mwh", help="Năng lượng thanh toán từ lưới điện (MWh)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán lượng khí thải cắt giảm (CO2, SOx, NOx, PM2.5) so với chạy máy phát diesel MGO."""
    res = ColdIroningEngine.calculate_emissions_avoided(
        total_energy_mwh=mwh,
        net_billed_mwh=billed_mwh,
    )

    data = {
        "baseline_mgo_tonnes": res.baseline_mgo_tonnes,
        "mgo_co2_tonnes": res.mgo_co2_tonnes,
        "grid_co2_tonnes": res.grid_co2_tonnes,
        "net_co2_avoided_tonnes": res.net_co2_avoided_tonnes,
        "sox_avoided_tonnes": res.sox_avoided_tonnes,
        "nox_avoided_tonnes": res.nox_avoided_tonnes,
        "pm25_avoided_tonnes": res.pm25_avoided_tonnes,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đo Lường Cắt Giảm Phát Thải Cảng Xanh (Cold Ironing)")
    table.add_column("Chỉ số phát thải", style="cyan")
    table.add_column("Giá trị cắt giảm", style="green")
    table.add_row("Dầu MGO tránh phải đốt", f"{res.baseline_mgo_tonnes:.4f} tấn")
    table.add_row("CO2 phát thải cơ sở từ MGO", f"{res.mgo_co2_tonnes:.3f} tấn CO2")
    table.add_row("CO2 phát thải từ điện lưới", f"{res.grid_co2_tonnes:.3f} tấn CO2")
    table.add_row("NET CO2 CẮT GIẢM RÒNG", f"{res.net_co2_avoided_tonnes:.3f} tấn CO2")
    table.add_row("SOx cắt giảm tránh được", f"{res.sox_avoided_tonnes:.4f} tấn SOx")
    table.add_row("NOx cắt giảm tránh được", f"{res.nox_avoided_tonnes:.4f} tấn NOx")
    table.add_row("Bụi mịn PM2.5 cắt giảm", f"{res.pm25_avoided_tonnes:.4f} tấn PM2.5")
    console.print(table)


@coldironing_app.command(name="cost")
def cold_ironing_cost_cmd(
    billed_mwh: float = typer.Option(40.0, "--billed-mwh", help="Năng lượng thanh toán từ lưới điện (MWh)"),
    mgo_tonnes: float = typer.Option(8.6, "--mgo-tonnes", help="Lượng dầu MGO cơ sở thay thế (tấn)"),
    elec_price: float = typer.Option(3200.0, "--elec-price", help="Giá điện bán lẻ cho cảng (VND/kWh)"),
    infra_fee: float = typer.Option(2000000.0, "--infra-fee", help="Phí hạ tầng cấp điện cầu cảng (VND)"),
    mgo_price: float = typer.Option(850.0, "--mgo-price", help="Giá dầu MGO quốc tế (USD/tấn)"),
    fx: float = typer.Option(25400.0, "--fx", help="Tỷ giá quy đổi USD/VND"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá hiệu quả kinh tế: so sánh chi phí cấp điện bờ và chi phí nhiên liệu diesel MGO."""
    res = ColdIroningEngine.evaluate_cost_savings(
        net_billed_mwh=billed_mwh,
        baseline_mgo_tonnes=mgo_tonnes,
        electricity_price_per_kwh_vnd=elec_price,
        green_infra_fee_vnd=infra_fee,
        mgo_price_per_tonne_usd=mgo_price,
        fx_usd_vnd=fx,
    )

    data = {
        "electricity_cost": res.electricity_cost,
        "green_berth_infrastructure_fee": res.green_berth_infrastructure_fee,
        "total_shore_power_cost": res.total_shore_power_cost,
        "mgo_fuel_saved_cost": res.mgo_fuel_saved_cost,
        "net_financial_savings": res.net_financial_savings,
        "currency": res.currency,
        "audit_hash": res.audit_hash,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đánh Giá Hiệu Quả Kinh Tế Điện Bờ (Cold Ironing)")
    table.add_column("Chỉ tiêu tài chính", style="cyan")
    table.add_column("Giá trị", style="green")
    table.add_row("Tiền điện tiêu thụ", f"{res.electricity_cost:,.2f} {res.currency}")
    table.add_row("Phí hạ tầng cầu cảng xanh", f"{res.green_berth_infrastructure_fee:,.2f} {res.currency}")
    table.add_row("Tổng chi phí cấp điện bờ", f"{res.total_shore_power_cost:,.2f} {res.currency}")
    table.add_row("Chi phí dầu MGO tiết kiệm", f"{res.mgo_fuel_saved_cost:,.2f} {res.currency}")
    table.add_row("TIẾT KIỆM TÀI CHÍNH RÒNG", f"{res.net_financial_savings:,.2f} {res.currency}")
    table.add_row("Mã xác thực Audit Hash", f"{res.audit_hash}")
    console.print(table)


# ==============================================================================
# PHASE 241: GREEN PORT GHG & IMO CII RATING COMMANDS
# ==============================================================================

@greenportghg_app.command(name="cii")
def evaluate_cii_cmd(
    ship_type: str = typer.Option("container", "--type", "-t", help="Loại tàu: container, bulk_carrier, tanker, general_cargo, gas_carrier"),
    dwt: float = typer.Option(50000.0, "--dwt", "-d", help="Trọng tải toàn phần Deadweight Tonnage (DWT)"),
    distance: float = typer.Option(60000.0, "--dist", help="Tổng hải lý hành trình trong năm (hải lý)"),
    fuel_hfo: float = typer.Option(0.0, "--hfo", help="Nhiên liệu HFO tiêu thụ (tấn)"),
    fuel_mgo: float = typer.Option(3200.0, "--mgo", help="Nhiên liệu MGO tiêu thụ (tấn)"),
    fuel_lng: float = typer.Option(0.0, "--lng", help="Nhiên liệu LNG tiêu thụ (tấn)"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm đánh giá (2023-2026)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán chỉ số phát thải carbon hoạt động hàng năm (CII) và xếp hạng A-E theo MARPOL."""
    type_map = {
        "bulk": CiiShipType.BULK_CARRIER,
        "container": CiiShipType.CONTAINER,
        "tanker": CiiShipType.TANKER,
        "general": CiiShipType.GENERAL_CARGO,
        "gas": CiiShipType.GAS_CARRIER,
    }
    ship_enum = CiiShipType.CONTAINER
    for k, v in type_map.items():
        if k in ship_type.lower():
            ship_enum = v
            break

    fuel_dict = {}
    if fuel_hfo > 0:
        fuel_dict["HFO"] = fuel_hfo
    if fuel_mgo > 0:
        fuel_dict["MGO"] = fuel_mgo
    if fuel_lng > 0:
        fuel_dict["LNG"] = fuel_lng
    if not fuel_dict:
        fuel_dict["MGO"] = 3000.0

    attained = GreenPortGhgCiiEngine.calculate_attained_cii(
        fuel_consumption_tonnes=fuel_dict,
        capacity_dwt=dwt,
        distance_travelled_nm=distance,
    )

    res = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=ship_enum,
        capacity_dwt=dwt,
        distance_travelled_nm=distance,
        attained_cii=attained,
        calendar_year=year,
    )

    data = {
        "ship_type": res.ship_type.value,
        "dwt": res.dwt,
        "distance_travelled_nm": res.distance_travelled_nm,
        "attained_cii": res.attained_cii,
        "required_cii": res.required_cii,
        "cii_ratio": res.cii_ratio,
        "rating_grade": res.rating_grade.value,
        "corrective_action_plan_required": res.corrective_action_plan_required,
        "port_tonnage_dues_discount_pct": res.port_tonnage_dues_discount_pct,
        "notes": res.notes,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.rating_grade in (CiiRatingGrade.A, CiiRatingGrade.B) else ("yellow" if res.rating_grade == CiiRatingGrade.C else "red")
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ XẾP HẠNG CƯỜNG ĐỘ CARBON HÀNG HẢI (IMO CII {year})[/bold {color}]\n"
        f"• Loại tàu: [cyan]{res.ship_type.value.upper()}[/cyan] ({res.dwt:,.0f} DWT)\n"
        f"• Chỉ số CII đạt được (Attained CII): [bold]{res.attained_cii} g CO2/(t·NM)[/bold]\n"
        f"• Chỉ số CII yêu cầu (Required CII): {res.required_cii} g CO2/(t·NM)\n"
        f"• Tỷ lệ đạt (CII Ratio): {res.cii_ratio:.4f}\n"
        f"• HẠNG XẾP HẠNG: [bold {color}]HẠNG {res.rating_grade.value}[/bold {color}]\n"
        f"• Yêu cầu Kế hoạch Khắc phục (SEEMP CAP): {'BẮT BUỘC (Rating E)' if res.corrective_action_plan_required else 'Không yêu cầu'}\n"
        f"• Mức giảm phí trọng tải cảng xanh: [bold green]{res.port_tonnage_dues_discount_pct:.0f}%[/bold green]",
        title="IMO CII Rating Evaluation",
        border_style=color,
    ))


@greenportghg_app.command(name="rating")
def direct_rating_cmd(
    ship_type: str = typer.Option("container", "--type", "-t", help="Loại tàu: container, bulk_carrier, tanker, general_cargo, gas_carrier"),
    dwt: float = typer.Option(50000.0, "--dwt", "-d", help="Trọng tải toàn phần DWT"),
    distance: float = typer.Option(60000.0, "--dist", help="Tổng hải lý hành trình"),
    attained_cii: float = typer.Option(3.5, "--cii", help="Chỉ số Attained CII đã tính (g CO2/t·NM)"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm đánh giá"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá trực tiếp cấp sao xếp hạng CII (A-E) từ chỉ số CII đạt được."""
    type_map = {
        "bulk": CiiShipType.BULK_CARRIER,
        "container": CiiShipType.CONTAINER,
        "tanker": CiiShipType.TANKER,
        "general": CiiShipType.GENERAL_CARGO,
        "gas": CiiShipType.GAS_CARRIER,
    }
    ship_enum = CiiShipType.CONTAINER
    for k, v in type_map.items():
        if k in ship_type.lower():
            ship_enum = v
            break

    res = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=ship_enum,
        capacity_dwt=dwt,
        distance_travelled_nm=distance,
        attained_cii=attained_cii,
        calendar_year=year,
    )

    data = {
        "ship_type": res.ship_type.value,
        "dwt": res.dwt,
        "distance_travelled_nm": res.distance_travelled_nm,
        "attained_cii": res.attained_cii,
        "required_cii": res.required_cii,
        "cii_ratio": res.cii_ratio,
        "rating_grade": res.rating_grade.value,
        "corrective_action_plan_required": res.corrective_action_plan_required,
        "port_tonnage_dues_discount_pct": res.port_tonnage_dues_discount_pct,
        "notes": res.notes,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.rating_grade in (CiiRatingGrade.A, CiiRatingGrade.B) else "yellow"
    console.print(Panel(
        f"[bold {color}]XẾP HẠNG IMO CII: HẠNG {res.rating_grade.value}[/bold {color}]\n"
        f"• Attained CII: {res.attained_cii} | Required CII: {res.required_cii}\n"
        f"• Giảm phí trọng tải cảng xanh: {res.port_tonnage_dues_discount_pct:.0f}%",
        title="Direct CII Rating Check",
        border_style=color,
    ))


# ==============================================================================
# PHASE 242: MARINE BUNKERING SAFETY & BDN COMMANDS
# ==============================================================================

@marinebunkering_app.command(name="bdn")
def verify_bdn_cmd(
    grade: str = typer.Option("vlsfo", "--grade", "-g", help="Chủng loại dầu: vlsfo, ulsfo, mgo, hsfo_scrubber"),
    sulphur: float = typer.Option(0.48, "--sulphur", "-s", help="Hàm lượng lưu huỳnh ghi trên phiếu BDN (% m/m)"),
    age: float = typer.Option(1.5, "--age", "-a", help="Thời gian lưu trữ hồ sơ phiếu BDN (năm)"),
    seal: str = typer.Option("SEAL-VN-2026-8889", "--seal", help="Mã niêm phong mẫu đại diện MARPOL"),
    eca: bool = typer.Option(False, "--eca", help="Tàu hoạt động trong khu vực kiểm soát khí thải ECA (giới hạn 0.10%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Thẩm định tính hợp lệ của Phiếu giao nhận nhiên liệu (Bunker Delivery Note - BDN)."""
    grade_map = {
        "vlsfo": BunkerGrade.VLSFO,
        "ulsfo": BunkerGrade.ULSFO,
        "mgo": BunkerGrade.MGO,
        "hsfo": BunkerGrade.HSFO_SCRUBBER,
    }
    b_grade = BunkerGrade.VLSFO
    for k, v in grade_map.items():
        if k in grade.lower():
            b_grade = v
            break

    res = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=b_grade,
        sulphur_content_pct=sulphur,
        bdn_record_age_years=age,
        sample_seal_number=seal,
        is_operating_in_eca=eca,
    )

    data = {
        "is_valid_bdn": res.is_valid_bdn,
        "is_sulphur_compliant": res.is_sulphur_compliant,
        "sulphur_content_pct": res.sulphur_content_pct,
        "statutory_cap_pct": res.statutory_cap_pct,
        "retention_period_years": res.retention_period_years,
        "is_retention_compliant": res.is_retention_compliant,
        "sample_seal_number": res.sample_seal_number,
        "rejection_reasons": res.rejection_reasons,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_valid_bdn else "red"
    console.print(Panel(
        f"[bold {color}]THẨM ĐỊNH PHIẾU GIAO NHẬN NHIÊN LIỆU (MARPOL BDN)[/bold {color}]\n"
        f"• Hợp lệ theo MARPOL Annex VI: [bold]{'HỢP CHUẨN' if res.is_valid_bdn else 'KHÔNG HỢP LỆ'}[/bold]\n"
        f"• Hàm lượng lưu huỳnh: [bold]{res.sulphur_content_pct:.2f}%[/bold] (Giới hạn luật định: {res.statutory_cap_pct:.2f}%)\n"
        f"• Tuân thủ thời hạn lưu trữ (3 năm): {'ĐẠT CHUẨN' if res.is_retention_compliant else 'QUÁ HẠN'}\n"
        f"• Mã niêm phong mẫu MARPOL: [cyan]{res.sample_seal_number}[/cyan]\n"
        f"• Lý do vi phạm: {', '.join(res.rejection_reasons) if res.rejection_reasons else 'Không có'}",
        title="Bunker Delivery Note Compliance",
        border_style=color,
    ))


@marinebunkering_app.command(name="volume")
def bunker_volume_correction_cmd(
    volume: float = typer.Option(500.0, "--volume", "-v", help="Thể tích dầu quan sát thực tế (m3)"),
    temp: float = typer.Option(32.0, "--temp", "-t", help="Nhiệt độ quan sát thực tế (độ C)"),
    density: float = typer.Option(985.0, "--density", "-d", help="Khối lượng riêng tiêu chuẩn tại 15°C (kg/m3)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Quy đổi thể tích và khối lượng dầu theo Tiêu chuẩn ASTM Table 54B (VCF) trong không khí."""
    res = MarineBunkeringSafetyEngine.calculate_volume_and_mass(
        observed_volume_m3=volume,
        observed_temp_c=temp,
        density_15c_kg_m3=density,
    )

    data = {
        "observed_volume_m3": res.observed_volume_m3,
        "observed_temp_c": res.observed_temp_c,
        "density_15c_kg_m3": res.density_15c_kg_m3,
        "vcf_factor": res.vcf_factor,
        "standard_volume_15c_m3": res.standard_volume_15c_m3,
        "metric_tonnes_in_air": res.metric_tonnes_in_air,
        "audit_hash": res.audit_hash,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Quy Đổi Khối Lượng Dầu Cấp Tàu (ASTM Table 54B)")
    table.add_column("Chỉ số đo đạc", style="cyan")
    table.add_column("Kết quả quy đổi", style="green")
    table.add_row("Thể tích quan sát thực tế", f"{res.observed_volume_m3:,.2f} m3 tại {res.observed_temp_c:.1f}°C")
    table.add_row("Khối lượng riêng tại 15°C", f"{res.density_15c_kg_m3:.1f} kg/m3")
    table.add_row("Hệ số hiệu chỉnh thể tích (VCF)", f"{res.vcf_factor:.5f}")
    table.add_row("Thể tích quy chuẩn tại 15°C", f"{res.standard_volume_15c_m3:,.3f} m3")
    table.add_row("Khối lượng thương mại trong không khí", f"{res.metric_tonnes_in_air:,.4f} tấn (MT)")
    table.add_row("Mã xác thực Audit Hash", f"{res.audit_hash}")
    console.print(table)


@marinebunkering_app.command(name="safety")
def bunkering_safety_cmd(
    rate: float = typer.Option(350.0, "--rate", "-r", help="Tốc độ bơm cấp dầu thực tế (m3/h)"),
    pressure: float = typer.Option(3.5, "--pressure", "-p", help="Áp suất tại bích họng nhận dầu (bar)"),
    esd_seconds: float = typer.Option(20.0, "--esd", help="Thời gian kích hoạt ngắt khẩn cấp ESD (giây)"),
    scuppers: bool = typer.Option(True, "--scuppers/--no-scuppers", help="Lỗ thoát nước boong đã bịt kín"),
    sopep: bool = typer.Option(True, "--sopep/--no-sopep", help="Trang thiết bị ứng cứu tràn dầu sẵn sàng"),
    bonding: bool = typer.Option(True, "--bonding/--no-bonding", help="Dây tiếp địa / bích cách điện hoàn tất"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra danh mục an toàn cấp dầu tàu biển (ISGOTT Checklist) & ngắt khẩn cấp ESD."""
    res = MarineBunkeringSafetyEngine.evaluate_bunkering_safety(
        pumping_rate_m3_h=rate,
        manifold_pressure_bar=pressure,
        esd_response_time_seconds=esd_seconds,
        scupper_plugs_secured=scuppers,
        sopep_spill_kit_ready=sopep,
        bonding_wire_secured=bonding,
    )

    data = {
        "is_cleared_for_bunkering": res.is_cleared_for_bunkering,
        "max_pumping_rate_m3_h": res.max_pumping_rate_m3_h,
        "max_manifold_pressure_bar": res.max_manifold_pressure_bar,
        "esd_response_time_seconds": res.esd_response_time_seconds,
        "is_esd_acceptable": res.is_esd_acceptable,
        "violations": res.violations,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_cleared_for_bunkering else "red"
    console.print(Panel(
        f"[bold {color}]KIỂM TRA AN TOÀN CẤP NHIÊN LIỆU (ISGOTT SAFETY CHECK)[/bold {color}]\n"
        f"• Cho phép bơm dầu: [bold]{'CHO PHÉP' if res.is_cleared_for_bunkering else 'ĐÌNH CHỈ / KHÔNG CHO PHÉP'}[/bold]\n"
        f"• Thời gian ngắt khẩn cấp ESD: {res.esd_response_time_seconds:.1f}s (Giới hạn: 30.0s) -> {'ĐẠT' if res.is_esd_acceptable else 'KHÔNG ĐẠT'}\n"
        f"• Vi phạm an toàn: {', '.join(res.violations) if res.violations else 'Không có vi phạm'}",
        title="Bunkering Safety Check",
        border_style=color,
    ))

