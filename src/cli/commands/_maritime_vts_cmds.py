# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 239: Seaport Vessel Traffic Service (VTS) CLI commands."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_vts_coldironing_ghg_bunkering_engine import (
    VesselTrafficServiceEngine,
)

console = Console()

vtsreporting_app = typer.Typer(
    name="vtsreporting",
    help="Báo cáo VTS, kiểm soát tốc độ luồng hàng hải & cảnh báo va chạm CPA/TCPA (Phase 239).",
)


@vtsreporting_app.command(name="check")
def check_vts_reporting_cmd(
    hours: float = typer.Option(2.5, "--hours", "-h", help="Số giờ báo cáo trước khi đến trạm/điểm kiểm tra VTS"),
    checkpoint: str = typer.Option("Vung Tau Pilot Station Point 0", "--checkpoint", "-c", help="Tên điểm kiểm soát VTS"),
    required_hours: float = typer.Option(2.0, "--req-hours", help="Quy định số giờ phải báo cáo trước theo luật"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Kiểm tra tuân thủ thời hạn báo cáo VTS vào luồng theo Nghị định 58/2017/NĐ-CP."""
    res = VesselTrafficServiceEngine.check_vts_reporting(
        hours_before_checkpoint=hours, checkpoint_name=checkpoint, required_advance_hours=required_hours,
    )
    if as_json:
        print(json.dumps({
            "is_compliant": res.is_compliant, "status": res.status.value,
            "hours_before_checkpoint": res.hours_before_checkpoint,
            "required_advance_hours": res.required_advance_hours,
            "discrepancy_hours": res.discrepancy_hours, "notes": res.notes,
        }, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_compliant else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ THẨM ĐỊNH BÁO CÁO VTS HÀNG HẢI[/bold {color}]\n"
        f"• Điểm kiểm soát: [cyan]{checkpoint}[/cyan]\n"
        f"• Trạng thái: [bold]{res.status.value.upper()}[/bold]\n"
        f"• Hợp lệ: [bold]{'ĐẠT CHUẨN' if res.is_compliant else 'VI PHẠM'}[/bold]\n"
        f"• Báo trước: {res.hours_before_checkpoint:.1f}h (Yêu cầu: {res.required_advance_hours:.1f}h)\n"
        f"• Chênh lệch: {res.discrepancy_hours:.1f}h",
        title="VTS Reporting Check", border_style=color,
    ))


@vtsreporting_app.command(name="speed")
def check_fairway_speed_cmd(
    speed: float = typer.Option(11.5, "--speed", "-s", help="Tốc độ hành hải thực tế của tàu (knots)"),
    limit: float = typer.Option(12.0, "--limit", "-l", help="Giới hạn tốc độ luồng quy định (knots)"),
    zone: str = typer.Option("inner_channel", "--zone", "-z", help="Khu vực luồng: inner_channel, outer_channel, berth_approach"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Kiểm tra giới hạn tốc độ luồng hàng hải và nguy cơ sóng cuộn (wake wash)."""
    res = VesselTrafficServiceEngine.evaluate_fairway_speed(
        actual_speed_knots=speed, max_allowed_speed_knots=limit, fairway_zone=zone,
    )
    if as_json:
        print(json.dumps({
            "actual_speed_knots": res.actual_speed_knots, "max_allowed_speed_knots": res.max_allowed_speed_knots,
            "is_speeding": res.is_speeding, "speed_excess_knots": res.speed_excess_knots,
            "wake_wash_hazard": res.wake_wash_hazard, "reprimand_level": res.reprimand_level,
        }, indent=2, ensure_ascii=False))
        return

    color = "red" if res.is_speeding else "green"
    console.print(Panel(
        f"[bold {color}]KIỂM TRA TỐC ĐỘ HÀNH HẢI TRONG LUỒNG VTS[/bold {color}]\n"
        f"• Tốc độ thực tế: [bold]{res.actual_speed_knots:.1f} kts[/bold] (Giới hạn: {res.max_allowed_speed_knots:.1f} kts)\n"
        f"• Vượt tốc: {'CÓ - ' + str(res.speed_excess_knots) + ' kts' if res.is_speeding else 'KHÔNG'}\n"
        f"• Cảnh báo sóng đập bến (Wake Wash): {'CẢNH BÁO NGUY HIỂM' if res.wake_wash_hazard else 'AN TOÀN'}\n"
        f"• Chế tài xử lý: [yellow]{res.reprimand_level}[/yellow]",
        title="Fairway Speed Check", border_style=color,
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
) -> None:
    """Tính toán khoảng cách tiếp cận gần nhất (CPA) và thời gian đến CPA (TCPA)."""
    res = VesselTrafficServiceEngine.calculate_cpa_tcpa(
        own_x=0.0, own_y=0.0, own_speed_knots=own_speed, own_course_deg=own_course,
        target_x=target_x, target_y=target_y, target_speed_knots=target_speed, target_course_deg=target_course,
    )
    if as_json:
        print(json.dumps({
            "cpa_nautical_miles": res.cpa_nautical_miles, "tcpa_minutes": res.tcpa_minutes,
            "risk_level": res.risk_level.value, "action_required": res.action_required,
        }, indent=2, ensure_ascii=False))
        return

    color = "red" if res.risk_level.value == "critical" else ("yellow" if res.risk_level.value == "warning" else "green")
    console.print(Panel(
        f"[bold {color}]ĐÁNH GIÁ NGUY CƠ VA CHẠM HÀNG HẢI (CPA & TCPA)[/bold {color}]\n"
        f"• Khoảng cách tiếp cận CPA: [bold]{res.cpa_nautical_miles:.2f} NM[/bold]\n"
        f"• Thời gian đến CPA (TCPA): [bold]{res.tcpa_minutes:.1f} phút[/bold]\n"
        f"• Mức độ rủi ro: [bold {color}]{res.risk_level.value.upper()}[/bold {color}]\n"
        f"• Hành động khuyến nghị: [cyan]{res.action_required}[/cyan]",
        title="Collision Risk Assessment", border_style=color,
    ))


@vtsreporting_app.command(name="tariff")
def calculate_vts_tariff_cmd(
    gt: float = typer.Option(20000.0, "--gt", help="Tổng dung tích Gross Tonnage (GT)"),
    intl: bool = typer.Option(True, "--intl/--domestic", help="Tuyến vận chuyển quốc tế hay nội địa"),
    dist: float = typer.Option(18.0, "--dist", help="Khoảng cách dẫn đường trong vùng VTS (hải lý)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Tính giá dịch vụ giám sát và hỗ trợ điều động VTS theo Thông tư 39/2023/TT-BGTVT."""
    res = VesselTrafficServiceEngine.calculate_vts_tariff(gross_tonnage=gt, is_international=intl, transit_distance_nm=dist)
    if as_json:
        print(json.dumps({
            "gross_tonnage": res.gross_tonnage, "base_rate": res.base_rate,
            "channel_transit_fee": res.channel_transit_fee, "surveillance_charge": res.surveillance_charge,
            "total_fee": res.total_fee, "currency": res.currency, "audit_hash": res.audit_hash,
        }, indent=2, ensure_ascii=False))
        return

    table = Table(title="Biểu Phí Dịch Vụ VTS Hàng Hải (Thông tư 39/2023/TT-BGTVT)")
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị", style="green")
    for k, v in [
        ("Tổng dung tích (GT)", f"{res.gross_tonnage:,.0f} GT"),
        ("Đơn giá cơ sở", f"{res.base_rate} {res.currency}/GT"),
        ("Phí qua luồng", f"{res.channel_transit_fee:,.2f} {res.currency}"),
        ("Phí giám sát radar VTS", f"{res.surveillance_charge:,.2f} {res.currency}"),
        ("TỔNG PHÍ DỊCH VỤ VTS", f"{res.total_fee:,.2f} {res.currency}"),
        ("Mã xác thực Audit Hash", f"{res.audit_hash}"),
    ]:
        table.add_row(k, v)
    console.print(table)
