# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 74: Inland Waterway Resource Listing & Telemetry Status CLI commands."""

from __future__ import annotations

import json

import typer
from rich.table import Table

from src.cli.commands._waterway_infra_cmds import console, waterway_app


def _render_waterway_list(res_type: str, data: list) -> None:
    if res_type in ("channels", "channel"):
        table = Table(title="Danh Sách Tuyến Luồng Đường Thủy Nội Địa (TCVN 5664)")
        for col, kw in [("Mã Luồng", {"style": "cyan"}), ("Tên Tuyến Luồng", {"style": "bold"}), ("Cấp Luồng", {"justify": "center"}), ("Chiều Dài", {"justify": "right"}), ("Độ Sâu", {"justify": "right"}), ("Tĩnh Không Cầu", {"justify": "right"}), ("Lưu Vực", {})]:
            table.add_column(col, **kw)
        for item in data:
            table.add_row(item["channel_code"], item["channel_name"], item["technical_grade"], f"{item['length_km']:.1f} km", f"{item['depth_m']:.2f} m", f"{item['bridge_clearance_m']:.2f} m", item["river_basin"])
        console.print(table)
    elif res_type in ("ports", "port"):
        table = Table(title="Danh Sách Cảng & Bến Thủy Nội Địa (NĐ 08/2021)")
        for col, kw in [("Mã Cảng", {"style": "cyan"}), ("Tên Cảng Bến", {"style": "bold"}), ("Phân Loại", {}), ("Luồng", {}), ("Tỉnh/Thành", {}), ("Max DWT", {"justify": "right"}), ("Trạng Thái", {"justify": "center", "style": "green"})]:
            table.add_column(col, **kw)
        for item in data:
            table.add_row(item["port_code"], item["port_name"], item["port_type"], item["channel_code"], item["province"], f"{item['max_dwt']:,.0f} DWT", item["status"])
        console.print(table)
    elif res_type in ("vessels", "vessel"):
        table = Table(title="Danh Sách Phương Tiện Thủy Nội Địa (NĐ 111/2014)")
        for col, kw in [("Số VR", {"style": "cyan"}), ("Tên Tàu / Sà Lan", {"style": "bold"}), ("Loại Phương Tiện", {}), ("Năm Đóng", {"justify": "center"}), ("Tuổi Tàu", {"justify": "center"}), ("Trọng Tải", {"justify": "right"}), ("Niên Hạn", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in data:
            valid_txt = "[green]HỢP LỆ[/]" if item["is_lifespan_valid"] else "[red]HẾT HẠN[/]"
            table.add_row(item["vr_number"], item["vessel_name"], item["vessel_type"], str(item["year_built"]), f"{item['age_years']} năm", f"{item['dwt_or_passengers']:,.0f}", valid_txt)
        console.print(table)
    elif res_type in ("clearances", "clearance"):
        table = Table(title="Danh Sách Giấy Phép Rời Cảng Bến Thủy Nội Địa")
        for col in ["Mã Giấy Phép", "Số VR", "Cảng Bến", "Thuyền Trưởng", "Hàng Hóa", "Kết Quả", "Thời Gian Cấp"]:
            table.add_column(col)
        for item in data:
            st_color = "green" if item["is_cleared"] else "red"
            st_txt = "CHO PHÉP" if item["is_cleared"] else "TỪ CHỐI"
            table.add_row(
                item["clearance_id"],
                item["vr_number"],
                item["port_code"],
                item["captain_name"],
                item["cargo_type"],
                f"[{st_color}]{st_txt}[/]",
                item["cleared_at"][:19],
            )
        console.print(table)
    elif res_type in ("captains", "captain"):
        table = Table(title="Danh Sách Thuyền Trưởng Thủy Nội Địa")
        for col in ["Số Bằng", "Họ Và Tên", "Hạng Bằng", "Thâm Niên", "Sức Khỏe", "Hiệu Lực"]:
            table.add_column(col)
        for item in data:
            table.add_row(
                item["license_number"],
                item["full_name"],
                item["tier"],
                f"{item['experience_months']} tháng",
                f"Loại {item['health_class']}",
                "HỢP LỆ" if item["is_valid"] else "KHÔNG ĐẠT",
            )
        console.print(table)
    elif res_type in ("bills", "freight", "orders"):
        table = Table(title="Danh Sách Vận Đơn Vận Tải Sà Lan")
        for col in ["Mã Vận Đơn", "Chủ Hàng", "Loại Hàng", "Khối Lượng", "Cự Ly", "Tổng Cước"]:
            table.add_column(col)
        for item in data:
            table.add_row(
                item["bill_id"],
                item["shipper_name"],
                item["cargo_type"],
                f"{item['volume_tons_or_teu']:,.1f}",
                f"{item['distance_km']:.1f} km",
                f"{item['total_charge_vnd']:,.0f} VND",
            )
        console.print(table)


@waterway_app.command("list")
def list_cmd(
    resource: str = typer.Argument("channels", help="Tài nguyên: 'channels', 'ports', 'vessels', 'clearances', 'captains', 'bills'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu dữ liệu tuyến luồng, cảng bến, phương tiện, giấy phép rời cảng, bằng thuyền trưởng."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    res_type = resource.lower().strip()
    dispatch = {
        "channels": engine.list_channels,
        "channel": engine.list_channels,
        "ports": engine.list_ports,
        "port": engine.list_ports,
        "vessels": engine.list_vessels,
        "vessel": engine.list_vessels,
        "clearances": engine.list_clearances,
        "clearance": engine.list_clearances,
        "captains": engine.list_captains,
        "captain": engine.list_captains,
        "bills": engine.list_freight_bills,
        "freight": engine.list_freight_bills,
        "orders": engine.list_freight_bills,
    }
    if res_type not in dispatch:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'channels', 'ports', 'vessels', 'clearances', 'captains', 'bills'")
        return
    items = dispatch[res_type](limit=limit)
    if json_mode:
        typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
        return
    _render_waterway_list(res_type, items.data)


@waterway_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của mạng lưới vận tải đường thủy nội địa và cảng bến."""
    from src.core.waterway_engine import WaterwayEngine

    status_data = WaterwayEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Giao Thông Đường Thủy Nội Địa & Cảng Bến")
    table.add_column("Chỉ số vận hành thủy nội địa", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")
    for label, val in [
        ("Tuyến luồng kỹ thuật đăng ký", str(m["registered_waterway_channels"])),
        ("Tổng chiều dài mạng lưới luồng", f"{m['total_channel_length_km']:,.1f} km"),
        ("Cảng bến thủy đang hoạt động", str(m["active_river_ports"])),
        ("Phương tiện thủy đăng ký", str(m["registered_vessels"])),
        ("Phương tiện còn niên hạn lưu hành", str(m["valid_lifespan_vessels"])),
        ("Hồ sơ xin phép rời bến Cảng vụ", str(m["total_clearance_requests"])),
        ("Số lượt cấp phép rời cảng thành công", str(m["cleared_port_departures"])),
        ("Thuyền trưởng được công nhận bằng T1-T4", str(m["certified_captains"])),
        ("Số lượng vận đơn sà lan hàng hóa", str(m["barge_freight_bills"])),
        ("Tổng doanh thu cước vận tải sà lan", f"{m['total_barge_freight_revenue_vnd']:,.0f} VND"),
    ]:
        table.add_row(label, val)
    console.print(table)
