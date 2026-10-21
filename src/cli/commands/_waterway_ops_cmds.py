# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 74: Captain Licensing & Barge Freight Calculation CLI commands."""

from __future__ import annotations

import json

import typer
from rich.table import Table

from src.cli.commands._waterway_infra_cmds import console, waterway_app


@waterway_app.command("captain")
def captain_cmd(
    name: str = typer.Argument(..., help="Họ và tên thuyền trưởng"),
    tier: str = typer.Option("T1", "--tier", "-t", help="Hạng bằng: T1, T2, T3, T4"),
    exp: int = typer.Option(48, "--exp", "-e", help="Số tháng kinh nghiệm thực tế"),
    health: int = typer.Option(1, "--health", "-h", help="Phân loại sức khỏe (1 hoặc 2)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra sát hạch bằng thuyền trưởng thủy nội địa theo Thông tư 40/2020/TT-BGTVT."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.verify_captain_license(
        full_name=name,
        tier=tier,
        experience_months=exp,
        health_class=health,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    status_color = "green" if prof["is_valid"] else "red"
    status_text = "ĐỦ ĐIỀU KIỆN CẤP / CÔNG NHẬN BẰNG" if prof["is_valid"] else "CHƯA ĐỦ ĐIỀU KIỆN"

    table = Table(title=f"Thẩm Định Bằng Thuyền Trưởng — {prof['full_name']}")
    table.add_column("Tiêu chuẩn sát hạch", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold")

    table.add_row("Số giấy chứng nhận", prof["license_number"])
    table.add_row("Họ và tên thuyền trưởng", prof["full_name"])
    table.add_row("Hạng bằng thẩm tra", f"{prof['tier_name_vi']} ({prof['tier']})")
    table.add_row("Phạm vi điều khiển", prof["max_capacity_desc"])
    table.add_row("Thâm niên kinh nghiệm thực tế", f"{prof['experience_months']} tháng (Yêu cầu min: {prof['min_required_experience_months']} tháng)")
    table.add_row("Phân loại sức khỏe ngành GTVT", f"Loại {prof['health_class']}")
    table.add_row("Kết luận thẩm định", status_text, style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@waterway_app.command("freight")
def freight_cmd(
    shipper: str = typer.Argument(..., help="Tên chủ hàng / doanh nghiệp gửi hàng"),
    cargo: str = typer.Option("CONTAINER_TEU", "--cargo", "-c", help="Loại hàng: CONTAINER_TEU, BULK_AGRICULTURE, CONSTRUCTION_MATERIAL, PETROLEUM_LIQUID"),
    volume: float = typer.Option(40.0, "--volume", "-v", help="Khối lượng hàng (tấn) hoặc số container (TEU)"),
    distance: float = typer.Option(150.0, "--distance", "-d", help="Cự ly vận chuyển đường thủy (km)"),
    grade: str = typer.Option("GRADE_I", "--grade", "-g", help="Cấp kỹ thuật tuyến luồng di chuyển"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính cước vận tải hàng hóa đường thủy nội địa bằng sà lan theo tấn-km / TEU-km."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.calculate_barge_freight(
        shipper_name=shipper,
        cargo_type=cargo,
        volume=volume,
        distance_km=distance,
        channel_grade=grade,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    bill = result["freight_bill"]
    table = Table(title=f"Vận Đơn Vận Tải Sà Lan Đường Thủy — Mã {bill['bill_id']}")
    table.add_column("Cấu phần chi phí vận chuyển", style="cyan")
    table.add_column("Giá trị tính cước", justify="right", style="bold")

    table.add_row("Mã vận đơn", bill["bill_id"])
    table.add_row("Chủ hàng gửi", bill["shipper_name"])
    table.add_row("Loại hàng hóa", bill["cargo_type"])
    table.add_row("Khối lượng vận chuyển", f"{bill['volume_tons_or_teu']:,.1f}")
    table.add_row("Cự ly tuyến luồng", f"{bill['distance_km']:.1f} km")
    table.add_row("Cấp kỹ thuật luồng", bill["channel_grade"])
    table.add_row("Đơn giá cước cơ sở", f"{bill['base_rate_vnd']:,.0f} VND / đơn vị-km")
    table.add_row("Phụ phí bốc dỡ tại cảng bến", f"{bill['handling_fee_vnd']:,.0f} VND")
    table.add_row("Tổng cước vận tải sà lan", f"{bill['total_charge_vnd']:,.0f} VND", style="bold green")

    console.print(table)
