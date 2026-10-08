"""Typer CLI Commands for Dangerous Cargo Terminal Handling, Tugboat Escort, Berthage & Channel Clearance.

Phases 231-234:
- Phase 231: mekong dangerouscargo validate / segregation
- Phase 232: mekong tugescort evaluate / reqs
- Phase 233: mekong berthmooring berthage / mooring
- Phase 234: mekong channelclearance ukc / airdraft / refusal
"""

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

console = Console()

dangerouscargo_app = typer.Typer(
    name="dangerouscargo",
    help="Quản lý hàng nguy hiểm tại cảng biển, cách ly bãi & xuất thẳng xe theo NĐ 58/2017 & NĐ 34/2024 (Phase 231).",
)
tugescort_app = typer.Typer(
    name="tugescort",
    help="Quy định tàu lai dắt, định mức sức kéo Bollard Pull & ngưỡng an toàn khí tượng TT 39/2023 (Phase 232).",
)
berthmooring_app = typer.Typer(
    name="berthmooring",
    help="Tính phí cầu bến, phao neo & giá dịch vụ buộc/cởi dây tàu biển theo TT 39/2023 & TT 12/2024 (Phase 233).",
)
channelclearance_app = typer.Typer(
    name="channelclearance",
    help="Kiểm tra an toàn luồng, độ sâu dự trữ UKC động, tĩnh không cầu & từ chối cấp phép BLLHH Điều 101 (Phase 234).",
)


# ==============================================================================
# PHASE 231: DANGEROUS CARGO TERMINAL COMMANDS
# ==============================================================================

@dangerouscargo_app.command(name="validate")
def validate_dangerous_cargo(
    imdg_class: str = typer.Option("3", "--class", "-c", help="Cấp độ nguy hiểm IMDG (1, 2, 3, 4, 5.1, 5.2, 6.1, 7, 8, 9)"),
    un_number: str = typer.Option("1203", "--un", help="Mã số Liên hợp quốc UN Number"),
    operation: str = typer.Option("yard_storage_import", "--operation", "-o", help="Hình thức: direct_discharge_truck, direct_discharge_barge, yard_storage_import, yard_storage_transshipment"),
    dwell_hours: float = typer.Option(24.0, "--dwell-hours", "-d", help="Thời gian lưu bãi/cầu cảng (giờ)"),
    buffer_meters: float = typer.Option(60.0, "--buffer", help="Khoảng cách đệm an toàn tới cổng/kho CFS (mét)"),
    sump_liters: float = typer.Option(30000.0, "--sump", help="Dung tích bể thu gom tràn đổ (lít)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Thẩm định tuân thủ lưu trữ và bốc dỡ hàng nguy hiểm tại cảng biển."""
    try:
        imdg_enum = IMDGClass(imdg_class)
        op_enum = DangerousGoodsOperationType(operation)
    except ValueError as e:
        console.print(f"[bold red]Lỗi tham số:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=imdg_enum,
        un_number=un_number,
        operation_type=op_enum,
        dwell_hours=dwell_hours,
        buffer_distance_meters=buffer_meters,
        containment_capacity_liters=sump_liters,
    )

    if as_json:
        console.print(json.dumps({
            "is_compliant": res.is_compliant,
            "requires_direct_discharge": res.requires_direct_discharge,
            "is_yard_storage_allowed": res.is_yard_storage_allowed,
            "max_allowed_dwell_hours": res.max_allowed_dwell_hours,
            "actual_dwell_hours": res.actual_dwell_hours,
            "is_dwell_time_exceeded": res.is_dwell_time_exceeded,
            "penalty_surcharge_pct": res.penalty_surcharge_pct,
            "emergency_buffer_meters": res.emergency_buffer_meters,
            "containment_sump_liters": res.containment_sump_liters,
            "violations": res.violations,
            "statutory_citations": res.statutory_citations,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_compliant else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ THẨM ĐỊNH HÀNG NGUY HIỂM TẠI CẢNG (IMDG CLASS {imdg_class} - UN {un_number})[/bold {color}]\n"
        f"Trạng thái tuân thủ: {'[bold green]HỢP LỆ[/bold green]' if res.is_compliant else '[bold red]VI PHẠM QUY ĐỊNH AN TOÀN[/bold red]'}\n"
        f"Bắt buộc xuất thẳng (Direct Discharge): {'CÓ (Cấm hạ bãi)' if res.requires_direct_discharge else 'KHÔNG'}\n"
        f"Thời gian lưu tối đa cho phép: {res.max_allowed_dwell_hours:.1f} giờ | Thực tế: {res.actual_dwell_hours:.1f} giờ\n"
        f"Phụ phí phạt quá hạn lưu bãi: +{res.penalty_surcharge_pct:.1f}%\n"
        f"Khoảng cách đệm an toàn: {res.emergency_buffer_meters:.1f} m (Tối thiểu 50.0 m)\n"
        f"Dung tích bể sự cố: {res.containment_sump_liters:.0f} L (Tối thiểu 26,000 L)",
        title="Vietnam Maritime Safety - Port DG Inspection",
    ))

    if res.violations:
        console.print("[bold red]CÁC LỖI VI PHẠM PHÁP LÝ:[/bold red]")
        for v in res.violations:
            console.print(f" • [red]{v}[/red]")


@dangerouscargo_app.command(name="segregation")
def check_imdg_segregation(
    class_a: str = typer.Option("3", "--class-a", "-a", help="Nhóm IMDG thứ nhất"),
    class_b: str = typer.Option("5.1", "--class-b", "-b", help="Nhóm IMDG thứ hai"),
    bay_gap: int = typer.Option(1, "--bays", help="Khoảng cách số bay container theo chiều dọc (longitudinal)"),
    row_gap: int = typer.Option(1, "--rows", help="Khoảng cách số hàng container theo chiều ngang (transverse)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra ma trận cách ly container hàng nguy hiểm trên bãi theo Bộ luật IMDG."""
    try:
        a_enum = IMDGClass(class_a)
        b_enum = IMDGClass(class_b)
    except ValueError as e:
        console.print(f"[bold red]Lỗi nhóm IMDG:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = DangerousCargoTerminalEngine.check_yard_segregation(a_enum, b_enum, bay_gap, row_gap)

    if as_json:
        console.print(json.dumps({
            "is_compatible": res.is_compatible,
            "required_bay_separation": res.required_bay_separation,
            "required_row_separation": res.required_row_separation,
            "minimum_distance_meters": res.minimum_distance_meters,
            "separation_rule": res.separation_rule,
            "violations": res.violations,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_compatible else "red"
    console.print(Panel(
        f"[bold {color}]KIỂM TRA CÁCH LY BÃI CONTAINER (CLASS {class_a} & CLASS {class_b})[/bold {color}]\n"
        f"Quy tắc áp dụng: [cyan]{res.separation_rule}[/cyan]\n"
        f"Yêu cầu khoảng cách tối thiểu: {res.required_bay_separation} Bay(s) | {res.required_row_separation} Row(s)\n"
        f"Khoảng cách thực tế: {bay_gap} Bay(s) | {row_gap} Row(s)\n"
        f"Đánh giá tương thích: {'[bold green]ĐẠT TIÊU CHUẨN[/bold green]' if res.is_compatible else '[bold red]KHÔNG ĐẠT CÁCH LY AN TOÀN[/bold red]'}",
        title="IMDG Code Yard Segregation Check",
    ))


# ==============================================================================
# PHASE 232: TUGBOAT TOWAGE ESCORT COMMANDS
# ==============================================================================

@tugescort_app.command(name="evaluate")
def evaluate_tugboat_towage(
    loa: float = typer.Option(165.0, "--loa", help="Chiều dài lớn nhất của tàu (LOA tính bằng mét)"),
    gt: float = typer.Option(22000.0, "--gt", help="Dung tích toàn phần của tàu (Gross Tonnage)"),
    tugs_bp: str = typer.Option("35,40", "--tugs-bp", help="Danh sách sức kéo Bollard Pull từng tàu lai (tấn), phân tách bằng dấu phẩy"),
    wind_mps: float = typer.Option(7.5, "--wind", help="Tốc độ gió thực tế (m/s)"),
    current_knots: float = typer.Option(1.8, "--current", help="Vận tốc dòng chảy thủy triều (hải lý/giờ)"),
    vis_nm: float = typer.Option(4.0, "--visibility", help="Tầm nhìn xa hàng hải (Hải lý)"),
    channel_escort: bool = typer.Option(False, "--escort", help="Có thực hiện dẫn luồng chủ động (Channel Escort) không"),
    night: bool = typer.Option(False, "--night", help="Hoạt động vào ban đêm (18h-06h)"),
    hazardous: bool = typer.Option(False, "--hazardous", help="Tàu chở hàng nguy hiểm (IMDG 1, 2, 3)"),
    admin_override: bool = typer.Option(False, "--override", help="Lệnh ngoại lệ của Giám đốc Cảng vụ Hàng hải"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá an toàn và định mức tàu lai dắt theo Thông tư 39/2023/TT-BGTVT."""
    try:
        bp_list = [float(x.strip()) for x in tugs_bp.split(",") if x.strip()]
    except ValueError:
        console.print("[bold red]Lỗi danh sách sức kéo tàu lai.[/bold red]")
        raise typer.Exit(code=1)

    res = TugboatTowageEscortEngine.evaluate_towage_operation(
        loa_meters=loa,
        gross_tonnage=gt,
        allocated_tugs_bp=bp_list,
        wind_speed_mps=wind_mps,
        current_speed_knots=current_knots,
        visibility_nm=vis_nm,
        is_channel_escort=channel_escort,
        is_night_operation=night,
        has_hazardous_cargo=hazardous,
        has_maritime_admin_override=admin_override,
    )

    if as_json:
        console.print(json.dumps({
            "is_safe_to_operate": res.is_safe_to_operate,
            "required_tug_count": res.required_tug_count,
            "allocated_tug_count": res.allocated_tug_count,
            "required_total_bp_tonnes": res.required_total_bp_tonnes,
            "allocated_total_bp_tonnes": res.allocated_total_bp_tonnes,
            "is_bp_sufficient": res.is_bp_sufficient,
            "wind_speed_mps": res.wind_speed_mps,
            "beaufort_scale": res.beaufort_scale,
            "current_speed_knots": res.current_speed_knots,
            "visibility_nm": res.visibility_nm,
            "weather_abort_triggered": res.weather_abort_triggered,
            "current_abort_triggered": res.current_abort_triggered,
            "visibility_abort_triggered": res.visibility_abort_triggered,
            "surcharge_pct_total": res.surcharge_pct_total,
            "surcharges_applied": res.surcharges_applied,
            "operational_warnings": res.operational_warnings,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_safe_to_operate else "red"
    console.print(Panel(
        f"[bold {color}]ĐÁNH GIÁ ĐIỀU ĐỘNG TÀU LAI (LOA: {loa}m | GT: {gt:,})[/bold {color}]\n"
        f"Trạng thái an toàn: {'[bold green]CHO PHÉP HOẠT ĐỘNG[/bold green]' if res.is_safe_to_operate else '[bold red]ĐÌNH CHỈ / KHÔNG ĐỦ ĐIỀU KIỆN[/bold red]'}\n"
        f"Số lượng tàu lai: {res.allocated_tug_count} tàu (Yêu cầu tối thiểu: {res.required_tug_count} tàu)\n"
        f"Tổng sức kéo Bollard Pull: {res.allocated_total_bp_tonnes:.1f}T (Yêu cầu: {res.required_total_bp_tonnes:.1f}T)\n"
        f"Điều kiện thời tiết: Gió {res.wind_speed_mps:.1f} m/s (Cấp {res.beaufort_scale}) | Dòng chảy {res.current_speed_knots:.1f} kts | Tầm nhìn {res.visibility_nm:.1f} NM\n"
        f"Tổng phụ phí phát sinh: +{res.surcharge_pct_total:.1f}%",
        title="Vietnam Maritime Safety - Harbor Towage Evaluation",
    ))

    if res.operational_warnings:
        console.print("[bold yellow]CẢNH BÁO TÁC NGHIỆP:[/bold yellow]")
        for w in res.operational_warnings:
            console.print(f" • [yellow]{w}[/yellow]")


# ==============================================================================
# PHASE 233: BERTHAGE & MOORING TARIFF COMMANDS
# ==============================================================================

@berthmooring_app.command(name="berthage")
def calculate_berthage_fee(
    gt: float = typer.Option(25000.0, "--gt", help="Dung tích toàn phần của tàu (Gross Tonnage)"),
    hours: float = typer.Option(36.0, "--hours", "-h", help="Thời gian neo cập cầu bến (giờ)"),
    trade: str = typer.Option("international", "--trade", help="Loại tuyến: international hoặc domestic"),
    mode: str = typer.Option("cargo_operations", "--mode", "-m", help="Mục đích sử dụng: cargo_operations, waiting_or_repair, unauthorized_overstay"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán phí cầu bến theo Thông tư 39/2023/TT-BGTVT."""
    try:
        t_enum = VesselTradeType(trade)
        m_enum = BerthUsageMode(mode)
    except ValueError as e:
        console.print(f"[bold red]Lỗi tham số:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = BerthageAndMooringTariffEngine.calculate_berthage(gt, hours, t_enum, m_enum)

    if as_json:
        console.print(json.dumps({
            "vessel_gt": res.vessel_gt,
            "trade_type": res.trade_type.value,
            "usage_mode": res.usage_mode.value,
            "duration_hours": res.duration_hours,
            "gt_hours": res.gt_hours,
            "base_rate_per_gt_hour": res.base_rate_per_gt_hour,
            "currency": res.currency,
            "base_amount": res.base_amount,
            "overstay_penalty_amount": res.overstay_penalty_amount,
            "total_berthage_amount": res.total_berthage_amount,
        }, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Bảng Tính Phí Cầu Bến Cảng Biển (TT 39/2023 - GT: {gt:,})")
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị", style="white")
    table.add_row("Dung tích GT", f"{gt:,}")
    table.add_row("Thời gian neo đậu", f"{hours:.1f} giờ ({res.gt_hours:,.0f} GT-giờ)")
    table.add_row("Tuyến hành trình", trade.upper())
    table.add_row("Mục đích cập cầu", mode)
    table.add_row("Đơn giá", f"{res.base_rate_per_gt_hour} {res.currency}/GT-giờ")
    table.add_row("Phạt quá hạn (nếu có)", f"{res.overstay_penalty_amount:,.2f} {res.currency}")
    table.add_row("TỔNG TIỀN PHÍ CẦU BẾN", f"[bold green]{res.total_berthage_amount:,.2f} {res.currency}[/bold green]")

    console.print(table)


@berthmooring_app.command(name="mooring")
def calculate_mooring_service(
    gt: float = typer.Option(18000.0, "--gt", help="Dung tích toàn phần của tàu (Gross Tonnage)"),
    operations: int = typer.Option(2, "--ops", help="Số lượt tác nghiệp: 1 (chỉ buộc hoặc cởi), 2 (cả buộc và cởi dây)"),
    trade: str = typer.Option("international", "--trade", help="Loại tuyến: international hoặc domestic"),
    night: bool = typer.Option(False, "--night", help="Làm đêm (18h-06h, +40%)"),
    holiday: bool = typer.Option(False, "--holiday", help="Làm ngày lễ/tết (+100%)"),
    hazardous: bool = typer.Option(False, "--hazardous", help="Tàu chở hàng nguy hiểm (+25%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính giá dịch vụ buộc cởi dây tàu biển theo khung giá Thông tư 39/2023."""
    try:
        t_enum = VesselTradeType(trade)
    except ValueError as e:
        console.print(f"[bold red]Lỗi loại tuyến:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = BerthageAndMooringTariffEngine.calculate_mooring_service(
        gross_tonnage=gt,
        operations_count=operations,
        trade_type=t_enum,
        is_night=night,
        is_holiday=holiday,
        has_hazardous_cargo=hazardous,
    )

    if as_json:
        console.print(json.dumps({
            "vessel_gt": res.vessel_gt,
            "tier_name": res.tier_name,
            "operations_count": res.operations_count,
            "base_tariff_per_turn": res.base_tariff_per_turn,
            "currency": res.currency,
            "required_line_handlers": res.required_line_handlers,
            "requires_launch_boat": res.requires_launch_boat,
            "night_surcharge_amount": res.night_surcharge_amount,
            "holiday_surcharge_amount": res.holiday_surcharge_amount,
            "hazardous_surcharge_amount": res.hazardous_surcharge_amount,
            "total_mooring_amount": res.total_mooring_amount,
        }, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Dịch Vụ Buộc/Cởi Dây Tàu Biển (GT: {gt:,})")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Chi tiết", style="white")
    table.add_row("Khung phân hạng", res.tier_name)
    table.add_row("Số công nhân bắt buộc", f"{res.required_line_handlers} người")
    table.add_row("Cano đưa dây", "BẮT BUỘC" if res.requires_launch_boat else "Không yêu cầu")
    table.add_row("Đơn giá cơ sở / lượt", f"{res.base_tariff_per_turn:,.2f} {res.currency}")
    table.add_row("Phụ phí ban đêm (+40%)", f"{res.night_surcharge_amount:,.2f} {res.currency}")
    table.add_row("Phụ phí ngày Lễ (+100%)", f"{res.holiday_surcharge_amount:,.2f} {res.currency}")
    table.add_row("Phụ phí hàng độc hại (+25%)", f"{res.hazardous_surcharge_amount:,.2f} {res.currency}")
    table.add_row("TỔNG CHI PHÍ BUỘC/CỞI DÂY", f"[bold green]{res.total_mooring_amount:,.2f} {res.currency}[/bold green]")

    console.print(table)


# ==============================================================================
# PHASE 234: CHANNEL CLEARANCE & SAFETY INSPECTION COMMANDS
# ==============================================================================

@channelclearance_app.command(name="ukc")
def calculate_dynamic_ukc(
    chart_depth: float = typer.Option(12.5, "--chart-depth", "-cd", help="Độ sâu đáy luồng trên hải đồ (mét)"),
    tide: float = typer.Option(2.8, "--tide", "-t", help="Độ cao thủy triều tại thời điểm hành hải (mét)"),
    draft: float = typer.Option(11.8, "--draft", "-d", help="Mớn nước tĩnh của tàu (mét)"),
    speed: float = typer.Option(8.0, "--speed", "-v", help="Tốc độ hành hải qua luồng (Hải lý/giờ)"),
    block_coeff: float = typer.Option(0.75, "--block-coeff", help="Hệ số béo thân tàu Block Coefficient Cb"),
    density: float = typer.Option(1.015, "--density", help="Tỷ trọng nước luồng (g/cm3): 1.025 nước biển, 1.000 nước ngọt"),
    wave: float = typer.Option(0.4, "--wave", help="Dao động mớn nước do sóng/lắc dập (mét)"),
    channel: str = typer.Option("confined_river", "--channel", help="Loại luồng: confined_river hoặc open_estuary_sea"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính độ sâu dự trữ đáy tàu (Dynamic Under-Keel Clearance) theo chuẩn PIANC & NĐ 58/2017."""
    try:
        c_enum = ChannelType(channel)
    except ValueError as e:
        console.print(f"[bold red]Lỗi loại luồng:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = ChannelClearanceAndSafetyInspectionEngine.calculate_dynamic_ukc(
        chart_depth_meters=chart_depth,
        tide_height_meters=tide,
        static_draft_meters=draft,
        speed_knots=speed,
        block_coefficient=block_coeff,
        water_density_g_cm3=density,
        wave_heave_meters=wave,
        channel_type=c_enum,
    )

    if as_json:
        console.print(json.dumps({
            "is_safe": res.is_safe,
            "fairway_depth_meters": res.fairway_depth_meters,
            "static_draft_meters": res.static_draft_meters,
            "squat_sinkage_meters": res.squat_sinkage_meters,
            "wave_heave_allowance_meters": res.wave_heave_allowance_meters,
            "salinity_sinkage_meters": res.salinity_sinkage_meters,
            "dynamic_draft_meters": res.dynamic_draft_meters,
            "dynamic_ukc_meters": res.dynamic_ukc_meters,
            "minimum_required_ukc_meters": res.minimum_required_ukc_meters,
            "ukc_safety_margin_meters": res.ukc_safety_margin_meters,
            "violations": res.violations,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_safe else "red"
    console.print(Panel(
        f"[bold {color}]TÍNH TOÁN ĐỘ SÂU DỰ TRỮ ĐÁY TÀU ĐỘNG (DYNAMIC UKC)[/bold {color}]\n"
        f"Trạng thái hành hải: {'[bold green]ĐỦ ĐỘ SÂU AN TOÀN[/bold green]' if res.is_safe else '[bold red]NGUY CƠ MẮC CẠN - CẤM QUA LUỒNG[/bold red]'}\n"
        f"Độ sâu mặt nước luồng: {res.fairway_depth_meters:.2f} m\n"
        f"Mớn nước tĩnh: {res.static_draft_meters:.2f} m | Mớn nước động: [bold]{res.dynamic_draft_meters:.2f} m[/bold]\n"
        f" • Hiện tượng Squat: +{res.squat_sinkage_meters:.2f} m\n"
        f" • Chìm do tỷ trọng nước ngọt: +{res.salinity_sinkage_meters:.2f} m\n"
        f" • Dao động sóng: +{res.wave_heave_allowance_meters:.2f} m\n"
        f"Độ sâu dự trữ thực tế (Dynamic UKC): [bold {color}]{res.dynamic_ukc_meters:.2f} m[/bold {color}]\n"
        f"Yêu cầu tối thiểu luật định: {res.minimum_required_ukc_meters:.2f} m | Biên độ dư thừa: {res.ukc_safety_margin_meters:+.2f} m",
        title="Vietnam Maritime Safety - Dynamic UKC Assessment",
    ))


@channelclearance_app.command(name="air-draft")
def calculate_air_draft(
    structure_height: float = typer.Option(45.0, "--structure-height", "-sh", help="Tĩnh không công trình tại mực nước cao nhất HAT (mét)"),
    mast_height: float = typer.Option(52.0, "--mast-height", "-mh", help="Chiều cao từ đáy ky tới đỉnh cột buồm (mét)"),
    dynamic_draft: float = typer.Option(11.5, "--dynamic-draft", "-dd", help="Mớn nước động của tàu khi qua vị trí (mét)"),
    tide_above_hat: float = typer.Option(0.0, "--tide-hat", help="Độ cao triều vượt trên HAT nếu có (mét)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra tĩnh không tàu dưới cầu đường bộ và đường điện vượt sông."""
    res = ChannelClearanceAndSafetyInspectionEngine.calculate_air_draft_clearance(
        structure_height_hat_meters=structure_height,
        mast_height_above_keel_meters=mast_height,
        dynamic_draft_meters=dynamic_draft,
        tide_height_meters=tide_above_hat,
    )

    if as_json:
        console.print(json.dumps({
            "is_safe": res.is_safe,
            "structure_height_hat_meters": res.structure_height_hat_meters,
            "mast_height_above_keel_meters": res.mast_height_above_keel_meters,
            "dynamic_draft_meters": res.dynamic_draft_meters,
            "vessel_air_draft_meters": res.vessel_air_draft_meters,
            "actual_clearance_meters": res.actual_clearance_meters,
            "required_safety_buffer_meters": res.required_safety_buffer_meters,
            "violations": res.violations,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_safe else "red"
    console.print(Panel(
        f"[bold {color}]KIỂM TRA TĨNH KHÔNG CÔNG TRÌNH VƯỢT SÔNG[/bold {color}]\n"
        f"Kết luận: {'[bold green]ĐẢM BẢO AN TOÀN QUA TĨNH KHÔNG[/bold green]' if res.is_safe else '[bold red]NGUY CƠ VA CHẠM CẦU / ĐƯỜNG ĐIỆN[/bold red]'}\n"
        f"Tĩnh không công trình: {res.structure_height_hat_meters:.2f} m\n"
        f"Tĩnh không thực tế của tàu (Air Draft): {res.vessel_air_draft_meters:.2f} m\n"
        f"Khoảng cách an toàn thực tế: [bold {color}]{res.actual_clearance_meters:.2f} m[/bold {color}]\n"
        f"Đệm an toàn tối thiểu theo luật: {res.required_safety_buffer_meters:.1f} m",
        title="Air Draft Clearance Inspection",
    ))


@channelclearance_app.command(name="refusal")
def evaluate_clearance_refusal(
    vessel_name: str = typer.Option("MV PACIFIC VOYAGER", "--name", "-n", help="Tên tàu biển"),
    imo: str = typer.Option("9123456", "--imo", help="Số hiệu IMO"),
    unseaworthy: bool = typer.Option(False, "--unseaworthy", help="Tàu khiếm khuyết vỏ/máy đe dọa an toàn (Điều 101.1.a)"),
    missing_certs: bool = typer.Option(False, "--missing-certs", help="Thiếu hoặc hết hạn chứng chỉ luật định (Điều 101.1.b)"),
    unpaid_dues: bool = typer.Option(False, "--unpaid-dues", help="Chưa thanh toán phí cảng biển hoặc tiền phạt (Điều 101.1.c)"),
    pollution_threat: bool = typer.Option(False, "--pollution", help="Nguy cơ ô nhiễm môi trường biển (Điều 101.1.d)"),
    arrest_order: bool = typer.Option(False, "--arrest", help="Lệnh bắt giữ tàu của Tòa án (Điều 101.1.e)"),
    safety_defects: bool = typer.Option(False, "--safety-defects", help="Không khắc phục sai phạm kiểm tra an toàn (Điều 101.1.f)"),
    sar_order: bool = typer.Option(False, "--sar", help="Lệnh trưng dụng tìm kiếm cứu nạn (Điều 101.1.g)"),
    ukc_breach: bool = typer.Option(False, "--ukc-breach", help="Vi phạm mớn nước luồng hoặc tĩnh không (Điều 101.1.h)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Thẩm định căn cứ pháp lý từ chối cấp phép rời cảng / lưu giữ tàu theo Điều 101 Bộ luật Hàng hải VN 2015."""
    res = ChannelClearanceAndSafetyInspectionEngine.evaluate_clearance_refusal(
        vessel_name=vessel_name,
        imo_number=imo,
        has_unseaworthy_defects=unseaworthy,
        missing_statutory_certificates=missing_certs,
        unpaid_port_dues_or_fines=unpaid_dues,
        environmental_or_pollution_threat=pollution_threat,
        court_ship_arrest_order=arrest_order,
        safety_inspection_noncompliance=safety_defects,
        sar_mobilization_order=sar_order,
        ukc_or_air_draft_breach=ukc_breach,
    )

    if as_json:
        console.print(json.dumps({
            "clearance_granted": res.clearance_granted,
            "decision_summary": res.decision_summary,
            "triggered_grounds": res.triggered_grounds,
            "applicable_statutory_articles": res.applicable_statutory_articles,
            "detention_hash": res.detention_hash,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.clearance_granted else "red"
    console.print(Panel(
        f"[bold {color}]QUYẾT ĐỊNH CẤP PHÉP RỜI CẢNG - ĐIỀU 101 BLLHH 2015[/bold {color}]\n"
        f"Tàu biển: [cyan]{vessel_name}[/cyan] | IMO: [cyan]{imo}[/cyan]\n"
        f"Kết luận Cảng vụ Hàng hải: [bold {color}]{res.decision_summary}[/bold {color}]\n"
        f"Mã tra cứu lưu giữ (Token): {res.detention_hash if res.detention_hash else 'N/A'}",
        title="Vietnam Port Authority Clearance Determination",
    ))

    if res.triggered_grounds:
        console.print("[bold red]CÁC CĂN CỨ TỪ CHỐI RỜI CẢNG / GIỮ TÀU ĐANG ÁP DỤNG:[/bold red]")
        for g in res.triggered_grounds:
            console.print(f" • [red]{g}[/red]")
