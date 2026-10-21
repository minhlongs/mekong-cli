# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Road Transport, Logistics, Highway Tolling & ETC (Phase 73)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._transport_operations import (
    etc_cmd,
    gps_cmd,
    register_transport_operations,
    weight_cmd,
)
from src.cli.commands._transport_queries import (
    list_cmd,
    register_transport_queries,
    status_cmd,
)

console = Console()
transport_app = typer.Typer(
    name="transport",
    help="Transport — Vietnamese Road Transport, Logistics, Highway Tolling & ETC Regulation",
    add_completion=False,
)


@transport_app.callback(invoke_without_command=True)
def transport_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Vận tải Đường bộ, Phù hiệu Xe, Thu phí Tự động ETC & Giám sát Tải trọng."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.transport_engine import TransportEngine

    engine = TransportEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ VẬN TẢI ĐƯỜNG BỘ, ETC & TẢI TRỌNG (LUẬT GTĐB & NĐ 10/2020)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Giấy phép KDVT:      [bold cyan]{m['active_transport_licenses']} giấy phép đang hoạt động[/]\n"
            f"  Phù hiệu xe đã cấp:  [bold green]{m['granted_vehicle_badges']} phương tiện đạt chuẩn[/] (Từ chối/quá niên hạn: [bold red]{m['rejected_vehicle_badges']}[/])\n"
            f"  Giao dịch thu phí:   [bold cyan]{m['etc_toll_transactions']} lượt qua trạm ETC[/] (Doanh thu cước BOT: [bold green]{m['total_etc_toll_revenue_vnd']:,.0f} VND[/])\n"
            f"  Giám sát hành trình: [bold green]{m['compliant_journey_logs']} hành trình đúng giờ lái[/] (Vi phạm quá 4h/10h: [bold red]{m['violation_journey_logs']}[/])\n"
            f"  Kiểm soát tải trọng: [bold]{m['overload_violations_detected']} vụ quá tải bị phạt[/] (Tổng tiền xử phạt: [bold red]{m['total_overload_fines_vnd']:,.0f} VND[/])",
            title="[bold blue]Vietnam Road Transport & Highway Tolling Telemetry[/]",
            border_style="green",
        )
    )


@transport_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp / hợp tác xã vận tải (vd: 'Công ty Vận tải Phương Trang')"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp (vd: '0303888999')"),
    business_type: str = typer.Option("PASSENGER_COACH_FIXED", "--type", "-t", help="Loại hình kinh doanh: PASSENGER_COACH_FIXED, PASSENGER_CONTRACT, PASSENGER_TAXI, PASSENGER_BUS, CARGO_TRUCK, CARGO_CONTAINER, CARGO_SUPER_HEAVY"),
    fleet: int = typer.Option(20, "--fleet", "-f", help="Quy mô số lượng phương tiện xin cấp phép"),
    authority: str = typer.Option("Sở Giao thông Vận tải", "--authority", "-a", help="Cơ quan cấp giấy phép KDVT"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Cấp Giấy phép kinh doanh vận tải bằng xe ô tô theo Nghị định 10/2020/NĐ-CP & 41/2024/NĐ-CP."""
    from src.core.transport_engine import TransportEngine

    result = TransportEngine().issue_business_license(
        enterprise_name=name, tax_id=tax_id, business_type=business_type,
        authorized_fleet_size=fleet, issuing_authority=authority,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Hồ Sơ Giấy Phép Kinh Doanh Vận Tải — {prof['license_number']}")
    table.add_column("Hạng mục cấp phép", style="cyan")
    table.add_column("Thông tin chi tiết", justify="right", style="bold green")
    for k, v in [
        ("Số giấy phép KDVT", prof["license_number"]), ("Tên đơn vị kinh doanh", prof["enterprise_name"]),
        ("Mã số thuế", prof["tax_id"]), ("Loại hình vận tải", prof["business_name_vi"]),
        ("Loại phù hiệu cấp", prof["badge_type"]), ("Quy mô đội xe cho phép", f"{prof['authorized_fleet_size']} xe"),
        ("Cơ quan cấp phép", prof["issuing_authority"]), ("Ngày cấp phép", prof["issue_date"]),
        ("Ngày hết hạn (5 năm)", prof["expiry_date"]), ("Trạng thái giấy phép", prof["status"]),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Khung pháp lý: {result['legal_framework']}[/dim]")


@transport_app.command("badge")
def badge_cmd(
    plate: str = typer.Argument(..., help="Biển số xe (vd: '29B-512.34' hoặc '51C-888.99')"),
    license_num: str = typer.Argument(..., help="Số giấy phép KDVT liên kết"),
    vehicle_type: str = typer.Option("PASSENGER_COACH_FIXED", "--type", "-t", help="Loại phương tiện: PASSENGER_COACH_FIXED, PASSENGER_CONTRACT, PASSENGER_TAXI, PASSENGER_BUS, CARGO_TRUCK, CARGO_CONTAINER, CARGO_SUPER_HEAVY"),
    year_built: int = typer.Option(2021, "--year", "-y", help="Năm sản xuất của xe"),
    capacity: float = typer.Option(45.0, "--capacity", "-c", help="Số chỗ ngồi hoặc tải trọng thiết kế (tấn)"),
    gps: bool = typer.Option(True, "--gps/--no-gps", help="Có lắp thiết bị giám sát hành trình (GSHT) hợp chuẩn"),
    camera: bool = typer.Option(True, "--camera/--no-camera", help="Có lắp camera giám sát người lái/khoang khách theo NĐ 10/2020"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định niên hạn, trang thiết bị an toàn và cấp phù hiệu xe kinh doanh vận tải."""
    from src.core.transport_engine import TransportEngine

    result = TransportEngine().issue_vehicle_badge(
        plate_number=plate, license_number=license_num, vehicle_type=vehicle_type,
        year_built=year_built, seats_or_tonnage=capacity, has_gps=gps, has_camera=camera,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["badge_profile"]
    status_color = "green" if prof["is_badge_granted"] else "red"
    status_text = "ĐỦ ĐIỀU KIỆN CẤP PHÙ HIỆU" if prof["is_badge_granted"] else "TỪ CHỐI CẤP PHÙ HIỆU"

    table = Table(title=f"Kết Quả Thẩm Định Cấp Phù Hiệu Xe — Biển Số {prof['plate_number']}")
    table.add_column("Tiêu chuẩn thẩm định kỹ thuật", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style=f"bold {status_color}")
    for k, v in [
        ("Biển kiểm soát", prof["plate_number"]), ("Loại phù hiệu yêu cầu", prof["badge_type"]),
        ("Loại hình vận tải", prof["business_name_vi"]), ("Năm sản xuất", str(prof["year_built"])),
        ("Tuổi phương tiện thực tế", f"{prof['vehicle_age_years']} năm"),
        ("Niên hạn sử dụng tối đa", f"{prof['max_legal_years']} năm"),
        ("Hợp lệ niên hạn (NĐ 10/2020)", "ĐẠT" if prof["is_lifespan_valid"] else "QUÁ NIÊN HẠN"),
        ("Thiết bị GSHT (GPS)", "HỢP CHUẨN" if prof["has_gps"] else "CHƯA CÓ / KHÔNG ĐẠT"),
        ("Camera giám sát trên xe", "ĐÃ LẮP ĐẶT" if prof["has_camera"] else "CHƯA LẮP ĐẶT"),
        ("Thời hạn hiệu lực phù hiệu", prof["badge_expiry_date"]), ("Kết luận thẩm định", status_text),
    ]:
        table.add_row(k, v)
    if prof["rejection_reason"]:
        table.add_row("Lý do từ chối", f"[bold red]{prof['rejection_reason']}[/bold red]")
    console.print(table)
    console.print(f"[dim]{result['legal_note']}[/dim]")


register_transport_operations(transport_app)
register_transport_queries(transport_app)

__all__ = ["transport_app", "transport_main", "license_cmd", "badge_cmd", "etc_cmd", "gps_cmd", "weight_cmd", "list_cmd", "status_cmd"]
