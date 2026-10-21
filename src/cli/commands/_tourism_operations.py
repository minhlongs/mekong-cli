# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tour guide, adventure safety, and tour booking subcommands for Tourism CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_tourism_operations(tourism_app: typer.Typer) -> None:
    """Register guide, adventure, and booking commands onto tourism_app."""
    tourism_app.command("guide")(guide_cmd)
    tourism_app.command("adventure")(adventure_cmd)
    tourism_app.command("booking")(booking_cmd)


def guide_cmd(
    name: str = typer.Argument(..., help="Họ và tên hướng dẫn viên du lịch"),
    card_type: str = typer.Option("INTERNATIONAL", "--type", "-t", help="Loại thẻ: DOMESTIC, INTERNATIONAL, ON_SITE"),
    language: str = typer.Option("Tiếng Anh (IELTS 7.5)", "--language", "-l", help="Ngoại ngữ thành thạo"),
    qualification: str = typer.Option("Cử nhân Hướng dẫn Du lịch", "--qualification", "-q", help="Văn bằng, chứng chỉ chuyên môn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Cấp thẻ hành nghề hướng dẫn viên du lịch nội địa, quốc tế hoặc tại điểm theo Luật Du lịch."""
    from src.core.tourism_engine import TourismEngine

    engine = TourismEngine()
    result = engine.issue_tour_guide_card(
        full_name=name,
        card_type=card_type,
        language=language,
        qualification=qualification,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["guide_profile"]
    table = Table(title=f"Thẻ Hành Nghề Hướng Dẫn Viên Du Lịch — {prof['full_name']}")
    table.add_column("Thông tin thẻ hướng dẫn viên", style="cyan")
    table.add_column("Chi tiết", justify="right", style="bold green")

    table.add_row("Số thẻ hành nghề", prof["card_number"])
    table.add_row("Họ và tên", prof["full_name"])
    table.add_row("Phân loại thẻ", prof["card_type_name_vi"])
    table.add_row("Phạm vi hành nghề", prof["scope"])
    table.add_row("Ngoại ngữ hành nghề", prof["language"])
    table.add_row("Trình độ đào tạo", prof["qualification"])
    table.add_row("Ngày cấp thẻ", prof["issued_date"])
    table.add_row("Ngày hết hạn thẻ", prof["expiry_date"])
    table.add_row("Hiệu lực pháp lý", "HỢP LỆ ĐANG HOẠT ĐỘNG")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


def adventure_cmd(
    tour: str = typer.Argument(..., help="Tên tour du lịch mạo hiểm (vd: 'Thám hiểm Hang Sơn Đoòng 4N3Đ')"),
    adv_type: str = typer.Option("CAVING_EXPEDITION", "--type", "-t", help="Loại hình: PARAGLIDING, SCUBA_DIVING, WHITE_WATER_RAFTING, ROCK_CLIMBING, CAVING_EXPEDITION, ZIPLINE_CANOPY"),
    location: str = typer.Option("Vườn Quốc gia Phong Nha - Kẻ Bàng, Quảng Bình", "--location", "-l", help="Địa điểm tổ chức hoạt động mạo hiểm"),
    instructor: bool = typer.Option(True, "--instructor/--no-instructor", help="Có hướng dẫn viên chuyên nghiệp có chứng chỉ"),
    gear: bool = typer.Option(True, "--gear/--no-gear", help="Trang bị đầy đủ đồ bảo hộ, định vị vệ tinh đạt chuẩn"),
    rescue: bool = typer.Option(True, "--rescue/--no-rescue", help="Có phương án cứu hộ, sơ cấp cứu khẩn cấp"),
    insurance: float = typer.Option(100_000_000.0, "--insurance", "-i", help="Mức trách nhiệm bảo hiểm tai nạn du lịch (VND/khách)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định an toàn các sản phẩm du lịch có nguy cơ ảnh hưởng tính mạng (du lịch mạo hiểm)."""
    from src.core.tourism_engine import TourismEngine

    engine = TourismEngine()
    result = engine.audit_adventure_safety(
        tour_name=tour,
        adventure_type=adv_type,
        location=location,
        has_certified_instructor=instructor,
        has_safety_gear=gear,
        has_rescue_plan=rescue,
        insurance_coverage_vnd=insurance,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["safety_profile"]
    status_color = "green" if prof["is_safety_cleared"] else "red"

    table = Table(title=f"Thẩm Định An Toàn Du Lịch Mạo Hiểm — {prof['tour_name']}")
    table.add_column("Hạng mục an toàn mạo hiểm", style="cyan")
    table.add_column("Kết quả thẩm định", justify="right", style="bold")

    table.add_row("Mã hồ sơ audit an toàn", prof["audit_id"])
    table.add_row("Tên tour du lịch", prof["tour_name"])
    table.add_row("Loại hình mạo hiểm", prof["adventure_type_desc"])
    table.add_row("Khu vực tổ chức", prof["location"])
    table.add_row("Huấn luyện viên chứng chỉ", "CÓ ĐẠT CHUẨN" if prof["has_certified_instructor"] else "THIẾU CHỨNG CHỈ")
    table.add_row("Trang thiết bị bảo hộ", "ĐẦY ĐỦ ĐẠT CHUẨN" if prof["has_safety_gear"] else "CHƯA ĐẠT CHUẨN")
    table.add_row("Phương án cứu nạn khẩn cấp", "ĐÃ PHÊ DUYỆT" if prof["has_rescue_plan"] else "CHƯA CÓ")
    table.add_row("Mức bảo hiểm tai nạn", f"{prof['insurance_coverage_vnd']:,.0f} VND / khách")
    table.add_row("Kết luận an toàn", prof["action_verdict"], style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Quy định an toàn: {result['statutory_reference']}[/dim]")


def booking_cmd(
    tourist: str = typer.Argument(..., help="Tên đại diện khách / đoàn du lịch"),
    nationality: str = typer.Option("Vietnam", "--nationality", "-n", help="Quốc tịch khách du lịch"),
    tour_type: str = typer.Option("DOMESTIC", "--type", "-t", help="Loại tour: INBOUND, OUTBOUND, DOMESTIC"),
    pax: int = typer.Option(4, "--pax", "-p", help="Số lượng khách trong đoàn"),
    price: float = typer.Option(6_500_000.0, "--price", help="Giá tour trọn gói trên mỗi khách (VND)"),
    start_date: str = typer.Option("2026-10-15", "--date", "-d", help="Ngày khởi hành tour (YYYY-MM-DD)"),
    duration: int = typer.Option(4, "--duration", help="Thời lượng tour (ngày)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Ghi nhận booking tour du lịch và tính toán doanh thu dịch vụ lữ hành."""
    from src.core.tourism_engine import TourismEngine

    engine = TourismEngine()
    result = engine.create_tour_booking(
        tourist_name=tourist,
        nationality=nationality,
        tour_type=tour_type,
        passengers_count=pax,
        price_per_pax_vnd=price,
        start_date=start_date,
        duration_days=duration,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["booking_profile"]
    table = Table(title=f"Xác Nhận Booking Tour Du Lịch — Mã {prof['booking_id']}")
    table.add_column("Thông tin đặt tour du lịch", style="cyan")
    table.add_column("Chi tiết hợp đồng", justify="right", style="bold")

    table.add_row("Mã booking tour", prof["booking_id"])
    table.add_row("Đại diện đoàn khách", prof["tourist_name"])
    table.add_row("Quốc tịch", prof["nationality"])
    table.add_row("Phân khúc tour", prof["tour_type"])
    table.add_row("Số lượng khách tham gia", f"{prof['passengers_count']} khách")
    table.add_row("Đơn giá tour trọn gói", f"{prof['price_per_pax_vnd']:,.0f} VND / khách")
    table.add_row("Tổng doanh thu booking", f"{prof['total_revenue_vnd']:,.0f} VND", style="bold green")
    table.add_row("Ngày khởi hành", prof["start_date"])
    table.add_row("Thời lượng hành trình", f"{prof['duration_days']} ngày")
    table.add_row("Trạng thái đặt chỗ", prof["status"], style="bold green")

    console.print(table)
