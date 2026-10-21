# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating (Phase 76)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._tourism_operations import (
    adventure_cmd,
    booking_cmd,
    guide_cmd,
    register_tourism_operations,
)
from src.cli.commands._tourism_queries import (
    list_cmd,
    register_tourism_queries,
    status_cmd,
)

console = Console()
tourism_app = typer.Typer(
    name="tourism",
    help="Tourism — Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating",
    add_completion=False,
)


@tourism_app.callback(invoke_without_command=True)
def tourism_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Du lịch, Lữ hành, Xếp hạng Khách sạn Sao & An toàn Mạo hiểm."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.tourism_engine import TourismEngine

    engine = TourismEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ DU LỊCH & LỮ HÀNH VIỆT NAM (LUẬT DU LỊCH 2017 & TCVN 4391:2015)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Giấy phép lữ hành:   [bold cyan]{m['active_travel_licenses']} doanh nghiệp lữ hành đang hoạt động[/]\n"
            f"  Cơ sở lưu trú:       [bold green]{m['total_rated_accommodations']} khách sạn / resort đã thẩm định[/] (Đạt chuẩn sao: [bold green]{m['certified_star_hotels']}[/])\n"
            f"  Hướng dẫn viên:      [bold cyan]{m['certified_tour_guides']} hướng dẫn viên được cấp thẻ hành nghề[/]\n"
            f"  Du lịch mạo hiểm:    [bold]{m['adventure_safety_audits']} tour thẩm định[/] (Đủ điều kiện an toàn: [bold green]{m['cleared_adventure_tours']}[/])\n"
            f"  Lượng khách phục vụ: [bold]{m['total_tourists_served']:,} lượt khách[/] ({m['total_tour_bookings']} tour bookings)\n"
            f"  Tổng doanh thu tour: [bold green]{m['total_tourism_revenue_vnd']:,.0f} VND[/]",
            title="[bold blue]Vietnam Tourism, Hospitality & Travel Telemetry[/]",
            border_style="green",
        )
    )


@tourism_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp kinh doanh lữ hành (vd: 'Công ty Cổ phần Du lịch Saigontourist')"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp (10 số)"),
    license_type: str = typer.Option("DOMESTIC_TRAVEL", "--type", "-t", help="Loại giấy phép: DOMESTIC_TRAVEL, INTERNATIONAL_INBOUND, INTERNATIONAL_OUTBOUND, INTERNATIONAL_FULL"),
    escrow: float = typer.Option(100_000_000.0, "--escrow", "-e", help="Số tiền ký quỹ tại ngân hàng thương mại (VND)"),
    bank: str = typer.Option("Vietcombank", "--bank", "-b", help="Ngân hàng nhận ký quỹ"),
    responsible: str = typer.Option("Nguyễn Văn Hùng", "--responsible", "-r", help="Người phụ trách kinh doanh dịch vụ lữ hành"),
    qualification: str = typer.Option("Cử nhân Lữ hành", "--qualification", "-q", help="Trình độ chuyên môn của người phụ trách"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra điều kiện ký quỹ và cấp Giấy phép kinh doanh dịch vụ lữ hành theo Luật Du lịch 2017."""
    from src.core.tourism_engine import TourismEngine

    result = TourismEngine().issue_travel_license(
        enterprise_name=name, tax_id=tax_id, license_type=license_type, escrow_amount_vnd=escrow,
        escrow_bank=bank, responsible_person=responsible, qualification=qualification,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Giấy Phép Kinh Doanh Dịch Vụ Lữ Hành — {prof['enterprise_name']}")
    table.add_column("Chỉ tiêu thẩm định lữ hành", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")
    for k, v in [
        ("Số giấy phép lữ hành", prof["license_number"]), ("Tên doanh nghiệp", prof["enterprise_name"]),
        ("Mã số thuế", prof["tax_id"]), ("Phạm vi hoạt động", prof["license_type_name_vi"]),
        ("Tiền ký quỹ thực tế", f"{prof['escrow_amount_vnd']:,.0f} VND"),
        ("Mức ký quỹ tối thiểu", f"{prof['min_required_escrow_vnd']:,.0f} VND"),
        ("Ngân hàng ký quỹ", prof["escrow_bank"]), ("Người phụ trách điều hành", prof["responsible_person"]),
        ("Cơ quan cấp phép", prof["licensing_authority"]), ("Trạng thái giấy phép", prof["status"]),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@tourism_app.command("rating")
def rating_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở lưu trú (vd: 'Vinpearl Resort & Spa Phú Quốc')"),
    acc_type: str = typer.Option("RESORT", "--type", "-t", help="Loại cơ sở: HOTEL, RESORT, APARTMENT, CRUISE"),
    rooms: int = typer.Option(120, "--rooms", "-r", help="Tổng số lượng buồng phòng ngủ"),
    province: str = typer.Option("Kiên Giang", "--province", "-p", help="Tỉnh / Thành phố"),
    star: str = typer.Option("5_STAR", "--star", "-s", help="Hạng sao đề nghị: 1_STAR, 2_STAR, 3_STAR, 4_STAR, 5_STAR"),
    pool: bool = typer.Option(True, "--pool/--no-pool", help="Có hồ bơi"),
    restaurant: bool = typer.Option(True, "--restaurant/--no-restaurant", help="Có nhà hàng phục vụ ăn uống"),
    conference: bool = typer.Option(True, "--conference/--no-conference", help="Có phòng họp, hội thảo"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định và công nhận hạng sao cơ sở lưu trú du lịch theo chuẩn quốc gia TCVN 4391:2015."""
    from src.core.tourism_engine import TourismEngine

    result = TourismEngine().rate_accommodation(
        establishment_name=name, accommodation_type=acc_type, room_count=rooms, province=province,
        star_rating=star, has_swimming_pool=pool, has_restaurant=restaurant, has_conference_room=conference,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["rating_profile"]
    status_color = "green" if prof["is_rating_compliant"] else "red"
    status_text = "ĐẠT CHUẨN CÔNG NHẬN SAO" if prof["is_rating_compliant"] else "CHƯA ĐỦ ĐIỀU KIỆN TIÊU CHUẨN"

    table = Table(title=f"Thẩm Định Xếp Hạng Sao Lưu Trú Du Lịch — {prof['establishment_name']}")
    table.add_column("Chỉ tiêu xếp hạng TCVN 4391", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold")
    for k, v in [
        ("Tên cơ sở lưu trú", prof["establishment_name"]), ("Phân loại cơ sở", prof["accommodation_type"]),
        ("Địa bàn tỉnh/thành", prof["province"]),
        ("Quy mô buồng phòng", f"{prof['room_count']} phòng (Yêu cầu min: {prof['min_required_rooms']} phòng)"),
        ("Hạng sao đề nghị", prof["star_name_vi"]),
        ("Nhà hàng phục vụ", "CÓ ĐẠT CHUẨN" if prof["has_restaurant"] else "KHÔNG CÓ"),
        ("Hồ bơi thư giãn", "CÓ ĐẠT CHUẨN" if prof["has_swimming_pool"] else "KHÔNG CÓ"),
        ("Phòng họp hội nghị", "CÓ ĐẠT CHUẨN" if prof["has_conference_room"] else "KHÔNG CÓ"),
        ("Cơ quan thẩm định", prof["eval_authority"]),
        ("Kết luận thẩm tra", f"[bold {status_color}]{status_text}[/bold {status_color}]"),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Tiêu chuẩn áp dụng: {result['statutory_reference']}[/dim]")


register_tourism_operations(tourism_app)
register_tourism_queries(tourism_app)

__all__ = ["tourism_app", "tourism_main", "license_cmd", "rating_cmd", "guide_cmd", "adventure_cmd", "booking_cmd", "list_cmd", "status_cmd"]
