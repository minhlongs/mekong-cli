# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List and status subcommands for Tourism CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_tourism_queries(tourism_app: typer.Typer) -> None:
    """Register list and status commands onto tourism_app."""
    tourism_app.command("list")(list_cmd)
    tourism_app.command("status")(status_cmd)


def list_cmd(
    resource: str = typer.Argument("licenses", help="Tài nguyên: 'licenses', 'accommodations', 'guides', 'adventure', 'bookings'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu dữ liệu giấy phép lữ hành, khách sạn sao, hướng dẫn viên, tour mạo hiểm, booking."""
    from src.core.tourism_engine import TourismEngine

    engine = TourismEngine()
    res_type = resource.lower().strip()

    if res_type in ("licenses", "license"):
        items = engine.list_licenses(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giấy Phép Kinh Doanh Dịch Vụ Lữ Hành")
        for col, kw in [("Số Giấy Phép", {"style": "cyan"}), ("Tên Doanh Nghiệp Lữ Hành", {"style": "bold"}), ("Mã Số Thuế", {}), ("Loại Hình", {}), ("Tiền Ký Quỹ", {"justify": "right"}), ("Ngân Hàng", {})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["license_number"], item["enterprise_name"], item["tax_id"], item["license_type"], f"{item['escrow_amount_vnd']:,.0f} VND", item["escrow_bank"])
        console.print(table)

    elif res_type in ("accommodations", "hotels", "resorts"):
        items = engine.list_accommodations(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Cơ Sở Lưu Trú & Xếp Hạng Sao (TCVN 4391)")
        for col, kw in [("Mã Cơ Sở", {"style": "cyan"}), ("Tên Khách Sạn / Resort", {"style": "bold"}), ("Loại Hình", {}), ("Tỉnh/Thành", {}), ("Số Phòng", {"justify": "right"}), ("Hạng Sao", {"justify": "center", "style": "bold yellow"}), ("Chuẩn Hóa", {"justify": "center", "style": "green"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["rating_id"], item["establishment_name"], item["accommodation_type"], item["province"], str(item["room_count"]), f"{item['star_count']}★ ({item['star_rating']})", "ĐẠT CHUẨN" if item["is_rating_compliant"] else "CHƯA ĐẠT")
        console.print(table)

    elif res_type in ("guides", "tour_guides"):
        items = engine.list_tour_guides(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hướng Dẫn Viên Du Lịch Được Cấp Thẻ")
        for col, kw in [("Số Thẻ", {"style": "cyan"}), ("Họ Và Tên", {"style": "bold"}), ("Loại Thẻ", {}), ("Ngoại Ngữ", {}), ("Trình Độ", {}), ("Hạn Thẻ", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["card_number"], item["full_name"], item["card_type"], item["language"], item["qualification"], item["expiry_date"])
        console.print(table)

    elif res_type in ("adventure", "adventure_audits"):
        items = engine.list_adventure_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Thẩm Định An Toàn Tour Mạo Hiểm")
        for col, kw in [("Mã Audit", {"style": "cyan"}), ("Tên Tour Mạo Hiểm", {"style": "bold"}), ("Loại Hình", {}), ("Địa Điểm", {}), ("Kết Luận", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            st_color = "green" if item["is_safety_cleared"] else "red"
            st_txt = "CHO PHÉP" if item["is_safety_cleared"] else "ĐÌNH CHỈ"
            table.add_row(item["audit_id"], item["tour_name"], item["adventure_type"], item["location"], f"[{st_color}]{st_txt}[/]")
        console.print(table)

    elif res_type in ("bookings", "booking"):
        items = engine.list_bookings(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Booking Tour & Đặt Chỗ Du Lịch")
        for col, kw in [("Mã Booking", {"style": "cyan"}), ("Khách Hàng", {"style": "bold"}), ("Quốc Tịch", {}), ("Phân Loại", {}), ("Số Khách", {"justify": "right"}), ("Doanh Thu", {"justify": "right", "style": "bold green"}), ("Khởi Hành", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["booking_id"], item["tourist_name"], item["nationality"], item["tour_type"], str(item["passengers_count"]), f"{item['total_revenue_vnd']:,.0f} VND", item["start_date"])
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'accommodations', 'guides', 'adventure', 'bookings'")


def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của ngành du lịch, lữ hành và khách sạn."""
    from src.core.tourism_engine import TourismEngine

    status_data = TourismEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Ngành Du Lịch & Lữ Hành Việt Nam")
    table.add_column("Chỉ số ngành du lịch & khách sạn", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")
    for k, v in [
        ("Giấy phép lữ hành đang hoạt động", str(m["active_travel_licenses"])),
        ("Tổng số cơ sở lưu trú thẩm định", str(m["total_rated_accommodations"])),
        ("Cơ sở lưu trú đạt chuẩn sao", str(m["certified_star_hotels"])),
        ("Hướng dẫn viên du lịch có thẻ", str(m["certified_tour_guides"])),
        ("Hồ sơ thẩm định an toàn mạo hiểm", str(m["adventure_safety_audits"])),
        ("Tour mạo hiểm đủ điều kiện an toàn", str(m["cleared_adventure_tours"])),
        ("Tổng số booking tour du lịch", str(m["total_tour_bookings"])),
        ("Tổng lượt khách phục vụ", f"{m['total_tourists_served']:,} khách"),
        ("Tổng doanh thu ngành du lịch", f"{m['total_tourism_revenue_vnd']:,.0f} VND"),
    ]:
        table.add_row(k, v)
    console.print(table)
