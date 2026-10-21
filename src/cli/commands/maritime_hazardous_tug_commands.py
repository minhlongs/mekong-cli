# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 231 & 232 CLI subcommands: Dangerous Cargo Terminal & Tugboat Towage Escort."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel

from src.core.maritime_hazardous_tug_berth_clearance_engine import (
    DangerousCargoTerminalEngine,
    DangerousGoodsOperationType,
    IMDGClass,
    TugboatTowageEscortEngine,
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
        imdg_enum, op_enum = IMDGClass(imdg_class), DangerousGoodsOperationType(operation)
    except ValueError as e:
        console.print(f"[bold red]Lỗi tham số:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = DangerousCargoTerminalEngine.validate_cargo_handling(
        imdg_class=imdg_enum, un_number=un_number, operation_type=op_enum,
        dwell_hours=dwell_hours, buffer_distance_meters=buffer_meters, containment_capacity_liters=sump_liters,
    )
    if as_json:
        console.print(json.dumps({
            "is_compliant": res.is_compliant, "requires_direct_discharge": res.requires_direct_discharge,
            "is_yard_storage_allowed": res.is_yard_storage_allowed, "max_allowed_dwell_hours": res.max_allowed_dwell_hours,
            "actual_dwell_hours": res.actual_dwell_hours, "is_dwell_time_exceeded": res.is_dwell_time_exceeded,
            "penalty_surcharge_pct": res.penalty_surcharge_pct, "emergency_buffer_meters": res.emergency_buffer_meters,
            "containment_sump_liters": res.containment_sump_liters, "violations": res.violations, "statutory_citations": res.statutory_citations,
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
        a_enum, b_enum = IMDGClass(class_a), IMDGClass(class_b)
    except ValueError as e:
        console.print(f"[bold red]Lỗi nhóm IMDG:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = DangerousCargoTerminalEngine.check_yard_segregation(a_enum, b_enum, bay_gap, row_gap)
    if as_json:
        console.print(json.dumps({
            "is_compatible": res.is_compatible, "required_bay_separation": res.required_bay_separation,
            "required_row_separation": res.required_row_separation, "minimum_distance_meters": res.minimum_distance_meters,
            "separation_rule": res.separation_rule, "violations": res.violations,
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
        loa_meters=loa, gross_tonnage=gt, allocated_tugs_bp=bp_list, wind_speed_mps=wind_mps,
        current_speed_knots=current_knots, visibility_nm=vis_nm, is_channel_escort=channel_escort,
        is_night_operation=night, has_hazardous_cargo=hazardous, has_maritime_admin_override=admin_override,
    )
    if as_json:
        console.print(json.dumps({
            "is_safe_to_operate": res.is_safe_to_operate, "required_tug_count": res.required_tug_count,
            "allocated_tug_count": res.allocated_tug_count, "required_total_bp_tonnes": res.required_total_bp_tonnes,
            "allocated_total_bp_tonnes": res.allocated_total_bp_tonnes, "is_bp_sufficient": res.is_bp_sufficient,
            "wind_speed_mps": res.wind_speed_mps, "beaufort_scale": res.beaufort_scale,
            "current_speed_knots": res.current_speed_knots, "visibility_nm": res.visibility_nm,
            "weather_abort_triggered": res.weather_abort_triggered, "current_abort_triggered": res.current_abort_triggered,
            "visibility_abort_triggered": res.visibility_abort_triggered, "surcharge_pct_total": res.surcharge_pct_total,
            "surcharges_applied": res.surcharges_applied, "operational_warnings": res.operational_warnings,
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
