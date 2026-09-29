# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating (Phase 76)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    engine = TourismEngine()
    result = engine.issue_travel_license(
        enterprise_name=name,
        tax_id=tax_id,
        license_type=license_type,
        escrow_amount_vnd=escrow,
        escrow_bank=bank,
        responsible_person=responsible,
        qualification=qualification,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Giấy Phép Kinh Doanh Dịch Vụ Lữ Hành — {prof['enterprise_name']}")
    table.add_column("Chỉ tiêu thẩm định lữ hành", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")

    table.add_row("Số giấy phép lữ hành", prof["license_number"])
    table.add_row("Tên doanh nghiệp", prof["enterprise_name"])
    table.add_row("Mã số thuế", prof["tax_id"])
    table.add_row("Phạm vi hoạt động", prof["license_type_name_vi"])
    table.add_row("Tiền ký quỹ thực tế", f"{prof['escrow_amount_vnd']:,.0f} VND")
    table.add_row("Mức ký quỹ tối thiểu", f"{prof['min_required_escrow_vnd']:,.0f} VND")
    table.add_row("Ngân hàng ký quỹ", prof["escrow_bank"])
    table.add_row("Người phụ trách điều hành", prof["responsible_person"])
    table.add_row("Cơ quan cấp phép", prof["licensing_authority"])
    table.add_row("Trạng thái giấy phép", prof["status"])

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

    engine = TourismEngine()
    result = engine.rate_accommodation(
        establishment_name=name,
        accommodation_type=acc_type,
        room_count=rooms,
        province=province,
        star_rating=star,
        has_swimming_pool=pool,
        has_restaurant=restaurant,
        has_conference_room=conference,
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

    table.add_row("Tên cơ sở lưu trú", prof["establishment_name"])
    table.add_row("Phân loại cơ sở", prof["accommodation_type"])
    table.add_row("Địa bàn tỉnh/thành", prof["province"])
    table.add_row("Quy mô buồng phòng", f"{prof['room_count']} phòng (Yêu cầu min: {prof['min_required_rooms']} phòng)")
    table.add_row("Hạng sao đề nghị", prof["star_name_vi"])
    table.add_row("Nhà hàng phục vụ", "CÓ ĐẠT CHUẨN" if prof["has_restaurant"] else "KHÔNG CÓ")
    table.add_row("Hồ bơi thư giãn", "CÓ ĐẠT CHUẨN" if prof["has_swimming_pool"] else "KHÔNG CÓ")
    table.add_row("Phòng họp hội nghị", "CÓ ĐẠT CHUẨN" if prof["has_conference_room"] else "KHÔNG CÓ")
    table.add_row("Cơ quan thẩm định", prof["eval_authority"])
    table.add_row("Kết luận thẩm tra", status_text, style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Tiêu chuẩn áp dụng: {result['statutory_reference']}[/dim]")


@tourism_app.command("guide")
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


@tourism_app.command("adventure")
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


@tourism_app.command("booking")
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


@tourism_app.command("list")
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
        table.add_column("Số Giấy Phép", style="cyan")
        table.add_column("Tên Doanh Nghiệp Lữ Hành", style="bold")
        table.add_column("Mã Số Thuế")
        table.add_column("Loại Hình")
        table.add_column("Tiền Ký Quỹ", justify="right")
        table.add_column("Ngân Hàng")
        for item in items.data:
            table.add_row(
                item["license_number"],
                item["enterprise_name"],
                item["tax_id"],
                item["license_type"],
                f"{item['escrow_amount_vnd']:,.0f} VND",
                item["escrow_bank"],
            )
        console.print(table)

    elif res_type in ("accommodations", "hotels", "resorts"):
        items = engine.list_accommodations(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Cơ Sở Lưu Trú & Xếp Hạng Sao (TCVN 4391)")
        table.add_column("Mã Cơ Sở", style="cyan")
        table.add_column("Tên Khách Sạn / Resort", style="bold")
        table.add_column("Loại Hình")
        table.add_column("Tỉnh/Thành")
        table.add_column("Số Phòng", justify="right")
        table.add_column("Hạng Sao", justify="center", style="bold yellow")
        table.add_column("Chuẩn Hóa", justify="center", style="green")
        for item in items.data:
            table.add_row(
                item["rating_id"],
                item["establishment_name"],
                item["accommodation_type"],
                item["province"],
                str(item["room_count"]),
                f"{item['star_count']}★ ({item['star_rating']})",
                "ĐẠT CHUẨN" if item["is_rating_compliant"] else "CHƯA ĐẠT",
            )
        console.print(table)

    elif res_type in ("guides", "tour_guides"):
        items = engine.list_tour_guides(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hướng Dẫn Viên Du Lịch Được Cấp Thẻ")
        table.add_column("Số Thẻ", style="cyan")
        table.add_column("Họ Và Tên", style="bold")
        table.add_column("Loại Thẻ")
        table.add_column("Ngoại Ngữ")
        table.add_column("Trình Độ")
        table.add_column("Hạn Thẻ", justify="center")
        for item in items.data:
            table.add_row(
                item["card_number"],
                item["full_name"],
                item["card_type"],
                item["language"],
                item["qualification"],
                item["expiry_date"],
            )
        console.print(table)

    elif res_type in ("adventure", "adventure_audits"):
        items = engine.list_adventure_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Thẩm Định An Toàn Tour Mạo Hiểm")
        table.add_column("Mã Audit", style="cyan")
        table.add_column("Tên Tour Mạo Hiểm", style="bold")
        table.add_column("Loại Hình")
        table.add_column("Địa Điểm")
        table.add_column("Kết Luận", justify="center")
        for item in items.data:
            st_color = "green" if item["is_safety_cleared"] else "red"
            st_txt = "CHO PHÉP" if item["is_safety_cleared"] else "ĐÌNH CHỈ"
            table.add_row(
                item["audit_id"],
                item["tour_name"],
                item["adventure_type"],
                item["location"],
                f"[{st_color}]{st_txt}[/]",
            )
        console.print(table)

    elif res_type in ("bookings", "booking"):
        items = engine.list_bookings(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Booking Tour & Đặt Chỗ Du Lịch")
        table.add_column("Mã Booking", style="cyan")
        table.add_column("Khách Hàng", style="bold")
        table.add_column("Quốc Tịch")
        table.add_column("Phân Loại")
        table.add_column("Số Khách", justify="right")
        table.add_column("Doanh Thu", justify="right", style="bold green")
        table.add_column("Khởi Hành", justify="center")
        for item in items.data:
            table.add_row(
                item["booking_id"],
                item["tourist_name"],
                item["nationality"],
                item["tour_type"],
                str(item["passengers_count"]),
                f"{item['total_revenue_vnd']:,.0f} VND",
                item["start_date"],
            )
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'accommodations', 'guides', 'adventure', 'bookings'")


@tourism_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của ngành du lịch, lữ hành và khách sạn."""
    from src.core.tourism_engine import TourismEngine

    engine = TourismEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Ngành Du Lịch & Lữ Hành Việt Nam")
    table.add_column("Chỉ số ngành du lịch & khách sạn", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Giấy phép lữ hành đang hoạt động", str(m["active_travel_licenses"]))
    table.add_row("Tổng số cơ sở lưu trú thẩm định", str(m["total_rated_accommodations"]))
    table.add_row("Cơ sở lưu trú đạt chuẩn sao", str(m["certified_star_hotels"]))
    table.add_row("Hướng dẫn viên du lịch có thẻ", str(m["certified_tour_guides"]))
    table.add_row("Hồ sơ thẩm định an toàn mạo hiểm", str(m["adventure_safety_audits"]))
    table.add_row("Tour mạo hiểm đủ điều kiện an toàn", str(m["cleared_adventure_tours"]))
    table.add_row("Tổng số booking tour du lịch", str(m["total_tour_bookings"]))
    table.add_row("Tổng lượt khách phục vụ", f"{m['total_tourists_served']:,} khách")
    table.add_row("Tổng doanh thu ngành du lịch", f"{m['total_tourism_revenue_vnd']:,.0f} VND")

    console.print(table)
