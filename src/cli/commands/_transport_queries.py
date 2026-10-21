# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List and status subcommands for Transport CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_transport_queries(transport_app: typer.Typer) -> None:
    """Register list and status commands onto transport_app."""
    transport_app.command("list")(list_cmd)
    transport_app.command("status")(status_cmd)


def list_cmd(
    resource: str = typer.Argument("licenses", help="Tài nguyên cần liệt kê: 'licenses', 'badges', 'etc', 'weights'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục giấy phép KDVT, phù hiệu xe, giao dịch ETC hoặc biên bản cân tải trọng."""
    from src.core.transport_engine import TransportEngine

    engine = TransportEngine()
    res_type = resource.lower()

    if res_type == "licenses":
        items = engine.list_licenses(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giấy Phép Kinh Doanh Vận Tải Ô Tô (NĐ 10/2020)")
        table.add_column("Số Giấy Phép", style="cyan")
        table.add_column("Tên Doanh Nghiệp / HTX", style="bold")
        table.add_column("Mã Số Thuế")
        table.add_column("Loại Hình")
        table.add_column("Quy Mô", justify="right")
        table.add_column("Hết Hạn")
        table.add_column("Trạng Thái", justify="center", style="green")
        for item in items.data:
            table.add_row(
                item["license_number"],
                item["enterprise_name"],
                item["tax_id"],
                item["business_type"],
                f"{item['authorized_fleet_size']} xe",
                item["expiry_date"],
                item["status"],
            )
        console.print(table)

    elif res_type == "badges":
        items = engine.list_badges(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Phù Hiệu Phương Tiện Kinh Doanh Vận Tải")
        table.add_column("Biển Số", style="cyan")
        table.add_column("Loại Phù Hiệu", style="bold")
        table.add_column("Năm SX", justify="center")
        table.add_column("Tuổi Xe", justify="center")
        table.add_column("GSHT / Camera", justify="center")
        table.add_column("Kết Quả", justify="center")
        table.add_column("Hết Hạn", justify="center")
        for item in items.data:
            status_text = "[green]ĐẠT[/]" if item["is_badge_granted"] else "[red]TỪ CHỐI[/]"
            equip = f"{'GPS' if item['has_gps'] else 'NO-GPS'} | {'CAM' if item['has_camera'] else 'NO-CAM'}"
            table.add_row(
                item["plate_number"],
                item["badge_type"],
                str(item["year_built"]),
                f"{item['vehicle_age_years']} năm",
                equip,
                status_text,
                item["badge_expiry_date"],
            )
        console.print(table)

    elif res_type == "etc":
        items = engine.list_etc_transactions(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giao Dịch Thu Phí Điện Tử Không Dừng ETC")
        table.add_column("Mã Giao Dịch", style="cyan")
        table.add_column("Biển Số Xe", style="bold")
        table.add_column("Trạm BOT")
        table.add_column("Phân Loại")
        table.add_column("Cước Phí", justify="right", style="yellow")
        table.add_column("Số Dư Sau Trừ", justify="right", style="green")
        table.add_column("Trạng Thái", justify="center")
        for item in items.data:
            st_color = "green" if item["status"] == "SUCCESS" else "red"
            table.add_row(
                item["transaction_id"],
                item["plate_number"],
                item["bot_station_name"],
                item["vehicle_class"],
                f"{item['toll_fee_vnd']:,.0f} VND",
                f"{item['remaining_balance_vnd']:,.0f} VND",
                f"[{st_color}]{item['status']}[/]",
            )
        console.print(table)

    elif res_type in ("weights", "weight"):
        items = engine.list_weight_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Biên Bản Cân Kiểm Tra Tải Trọng Xe")
        table.add_column("Mã Biên Bản", style="cyan")
        table.add_column("Biển Số Xe", style="bold")
        table.add_column("Cấu Hình Trục")
        table.add_column("Cân Thực Tế", justify="right")
        table.add_column("Cho Phép", justify="right")
        table.add_column("% Quá Tải", justify="right")
        table.add_column("Tổng Tiền Phạt", justify="right", style="bold red")
        for item in items.data:
            pct_style = "red" if item["overload_percentage"] >= 10.0 else ("yellow" if item["overload_percentage"] > 0 else "green")
            total_fine = item["fine_driver_vnd"] + item["fine_owner_vnd"]
            table.add_row(
                item["audit_id"],
                item["plate_number"],
                item["vehicle_configuration"],
                f"{item['gross_weight_tonnes']:.2f} t",
                f"{item['permitted_weight_tonnes']:.2f} t",
                f"[{pct_style}]{item['overload_percentage']:.1f}%[/]",
                f"{total_fine:,.0f} VND" if total_fine > 0 else "0 VND",
            )
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'badges', 'etc', 'weights'")


def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của mạng lưới vận tải đường bộ và trạm thu phí ETC."""
    from src.core.transport_engine import TransportEngine

    engine = TransportEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Vận Tải Đường Bộ & Thu Phí Không Dừng ETC")
    table.add_column("Chỉ số vận hành", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Giấy phép KDVT đang hoạt động", str(m["active_transport_licenses"]))
    table.add_row("Phù hiệu xe hợp chuẩn đã cấp", str(m["granted_vehicle_badges"]))
    table.add_row("Phù hiệu xe bị từ chối / quá hạn", str(m["rejected_vehicle_badges"]))
    table.add_row("Số lượt giao dịch thu phí ETC thành công", str(m["etc_toll_transactions"]))
    table.add_row("Tổng doanh thu cước BOT qua ETC", f"{m['total_etc_toll_revenue_vnd']:,.0f} VND")
    table.add_row("Hành trình tuân thủ giờ lái xe (TT 12/2020)", str(m["compliant_journey_logs"]))
    table.add_row("Hành trình vi phạm quá 4h/10h lái xe", str(m["violation_journey_logs"]))
    table.add_row("Số vụ vi phạm quá tải trọng trục", str(m["overload_violations_detected"]))
    table.add_row("Tổng tiền phạt quá tải trọng (NĐ 100/123)", f"{m['total_overload_fines_vnd']:,.0f} VND")

    console.print(table)
