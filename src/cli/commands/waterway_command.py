# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Inland Waterway Transport, River Ports & Navigation (Phase 74)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
waterway_app = typer.Typer(
    name="waterway",
    help="Waterway — Vietnamese Inland Waterway Transport, River Ports & Canal Navigation",
    add_completion=False,
)


@waterway_app.callback(invoke_without_command=True)
def waterway_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Vận tải Thủy Nội địa, Cảng Bến, Luồng Tuyến & Cấp Phép Rời Bến."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ GIAO THÔNG ĐƯỜNG THỦY NỘI ĐỊA & CẢNG BẾN (LUẬT GTĐTNĐ & NĐ 08/2021)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Luồng tuyến kỹ thuật:[bold cyan]{m['registered_waterway_channels']} tuyến luồng[/] (Tổng chiều dài: [bold]{m['total_channel_length_km']:,.1f} km[/])\n"
            f"  Cảng bến thủy:       [bold green]{m['active_river_ports']} cảng bến đang hoạt động[/]\n"
            f"  Đội tàu & sà lan:    [bold cyan]{m['registered_vessels']} phương tiện đăng ký[/] (Hợp lệ niên hạn NĐ 111: [bold green]{m['valid_lifespan_vessels']}[/])\n"
            f"  Thủ tục Cảng vụ:     [bold]{m['total_clearance_requests']} hồ sơ rời cảng[/] (Được cấp phép rời bến: [bold green]{m['cleared_port_departures']}[/])\n"
            f"  Thuyền trưởng:       [bold green]{m['certified_captains']} thuyền trưởng đạt chuẩn T1-T4[/]\n"
            f"  Vận tải sà lan:      [bold]{m['barge_freight_bills']} vận đơn[/] (Doanh thu cước: [bold green]{m['total_barge_freight_revenue_vnd']:,.0f} VND[/])",
            title="[bold blue]Vietnam Inland Waterways & River Ports Telemetry[/]",
            border_style="green",
        )
    )


@waterway_app.command("channel")
def channel_cmd(
    code: str = typer.Argument(..., help="Mã tuyến luồng (vd: 'CH-TIEN-01' hoặc 'CH-CHO-GAO')"),
    name: str = typer.Argument(..., help="Tên tuyến luồng kỹ thuật (vd: 'Tuyến Kênh Huyết Mạch Chợ Gạo')"),
    grade: str = typer.Option("GRADE_I", "--grade", "-g", help="Cấp kỹ thuật luồng: SPECIAL, GRADE_I, GRADE_II, GRADE_III, GRADE_IV, GRADE_V"),
    length: float = typer.Option(28.5, "--length", "-l", help="Chiều dài đoạn luồng (km)"),
    depth: float = typer.Option(3.5, "--depth", "-d", help="Độ sâu chạy tàu thiết kế (m)"),
    clearance: float = typer.Option(10.0, "--clearance", "-c", help="Tĩnh không thông thuyền cầu (m)"),
    basin: str = typer.Option("Đồng bằng Sông Cửu Long", "--basin", "-b", help="Lưu vực sông (ĐBSCL, Sông Hồng, Bắc Bộ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký tuyến luồng kỹ thuật đường thủy nội địa theo chuẩn TCVN 5664:2009."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.register_channel(
        channel_code=code,
        channel_name=name,
        technical_grade=grade,
        length_km=length,
        depth_m=depth,
        bridge_clearance_m=clearance,
        river_basin=basin,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["channel_profile"]
    table = Table(title=f"Hồ Sơ Tuyến Luồng Kỹ Thuật — {prof['channel_name']} ({prof['channel_code']})")
    table.add_column("Chỉ tiêu luồng thủy nội địa", style="cyan")
    table.add_column("Thông số kỹ thuật", justify="right", style="bold green")

    table.add_row("Mã tuyến luồng", prof["channel_code"])
    table.add_row("Tên tuyến luồng", prof["channel_name"])
    table.add_row("Cấp kỹ thuật luồng", f"{prof['grade_name_vi']} ({prof['technical_grade']})")
    table.add_row("Chiều dài đoạn tuyến", f"{prof['length_km']:.1f} km")
    table.add_row("Độ sâu chạy tàu thực tế", f"{prof['depth_m']:.2f} m")
    table.add_row("Độ sâu tối thiểu quy chuẩn", f"{prof['min_required_depth_m']:.2f} m")
    table.add_row("Tĩnh không thông thuyền cầu", f"{prof['bridge_clearance_m']:.2f} m")
    table.add_row("Tĩnh không cầu tối thiểu", f"{prof['min_required_clearance_m']:.2f} m")
    table.add_row("Đạt chuẩn độ sâu TCVN 5664", "ĐẠT CHUẨN" if prof["is_depth_standard_compliant"] else "CHƯA ĐẠT")
    table.add_row("Lưu vực sông", prof["river_basin"])

    console.print(table)
    console.print(f"[dim]Căn cứ kỹ thuật: {result['statutory_reference']}[/dim]")


@waterway_app.command("port")
def port_cmd(
    code: str = typer.Argument(..., help="Mã cảng bến (vd: 'PRT-MY-THO' hoặc 'PRT-CAN-THO')"),
    name: str = typer.Argument(..., help="Tên cảng hoặc bến thủy nội địa"),
    port_type: str = typer.Option("CARGO_PORT", "--type", "-t", help="Loại cảng: CARGO_PORT, PASSENGER_PORT, CONTAINER_PORT, INDUSTRIAL_PORT"),
    channel: str = typer.Option("CH-TIEN-01", "--channel", "-c", help="Mã tuyến luồng liên kết"),
    province: str = typer.Option("Tiền Giang", "--province", "-p", help="Tỉnh / Thành phố trực thuộc"),
    dwt: float = typer.Option(3000.0, "--dwt", "-w", help="Trọng tải phương tiện lớn nhất tiếp nhận (DWT)"),
    teu: int = typer.Option(500, "--teu", help="Năng lực bốc dỡ container (TEU)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký cảng, bến thủy nội địa và năng lực tiếp nhận phương tiện theo NĐ 08/2021/NĐ-CP."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.register_port(
        port_code=code,
        port_name=name,
        port_type=port_type,
        channel_code=channel,
        province=province,
        max_dwt=dwt,
        max_teu_capacity=teu,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["port_profile"]
    table = Table(title=f"Hồ Sơ Đăng Ký Cảng Bến Thủy Nội Địa — {prof['port_name']}")
    table.add_column("Chỉ tiêu năng lực cảng bến", style="cyan")
    table.add_column("Thông số công bố", justify="right", style="bold green")

    table.add_row("Mã định danh cảng", prof["port_code"])
    table.add_row("Tên cảng bến thủy", prof["port_name"])
    table.add_row("Phân loại chức năng", prof["port_type"])
    table.add_row("Tuyến luồng kết nối", prof["channel_code"])
    table.add_row("Địa bàn tỉnh/thành", prof["province"])
    table.add_row("Trọng tải tàu tiếp nhận (DWT)", f"{prof['max_dwt']:,.0f} DWT")
    table.add_row("Sức chứa bãi container", f"{prof['max_teu_capacity']} TEU")
    table.add_row("Trạng thái công bố cảng", prof["status"])

    console.print(table)
    console.print(f"[dim]Khung pháp lý: {result['statutory_reference']}[/dim]")


@waterway_app.command("vessel")
def vessel_cmd(
    vr: str = typer.Argument(..., help="Số đăng kiểm VR (vd: 'VR-22001188')"),
    name: str = typer.Argument(..., help="Tên phương tiện thủy (vd: 'Sà lan Hưng Phát 36')"),
    vessel_type: str = typer.Option("CARGO_BARGE_CONTAINER", "--type", "-t", help="Loại tàu: PASSENGER_STEEL, PASSENGER_WOOD_COMPOSITE, PASSENGER_HIGH_SPEED, CARGO_BARGE_DRY, CARGO_BARGE_CONTAINER, TUGBOAT_PUSHER, TANKER_DANGEROUS_LIQUID"),
    year_built: int = typer.Option(2021, "--year", "-y", help="Năm đóng phương tiện"),
    material: str = typer.Option("STEEL", "--material", "-m", help="Vật liệu vỏ: STEEL, COMPOSITE, WOOD"),
    capacity: float = typer.Option(1500.0, "--capacity", "-c", help="Trọng tải toàn phần DWT hoặc sức chở khách"),
    ais: bool = typer.Option(True, "--ais/--no-ais", help="Trang bị thiết bị nhận dạng tự động AIS Class A/B"),
    vhf: bool = typer.Option(True, "--vhf/--no-vhf", help="Trang bị máy thông tin vô tuyến VHF hàng hải"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký phương tiện thủy nội địa và kiểm tra niên hạn theo Nghị định 111/2014/NĐ-CP."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.register_vessel(
        vr_number=vr,
        vessel_name=name,
        vessel_type=vessel_type,
        year_built=year_built,
        hull_material=material,
        dwt_or_passengers=capacity,
        has_ais=ais,
        has_vhf=vhf,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["vessel_profile"]
    status_color = "green" if prof["is_lifespan_valid"] else "red"
    status_text = "HỢP LỆ NIÊN HẠN LƯU HÀNH" if prof["is_lifespan_valid"] else "HẾT NIÊN HẠN SỬ DỤNG (ĐÌNH CHỈ)"

    table = Table(title=f"Đăng Ký & Thẩm Tra Niên Hạn Tàu Thủy — {prof['vessel_name']} ({prof['vr_number']})")
    table.add_column("Chỉ tiêu đăng kiểm kỹ thuật", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold")

    table.add_row("Số đăng kiểm VR", prof["vr_number"])
    table.add_row("Tên phương tiện thủy", prof["vessel_name"])
    table.add_row("Phân loại phương tiện", prof["vessel_type_name_vi"])
    table.add_row("Vật liệu vỏ tàu", prof["hull_material"])
    table.add_row("Năm đóng phương tiện", str(prof["year_built"]))
    table.add_row("Tuổi phương tiện thực tế", f"{prof['age_years']} năm")
    table.add_row("Niên hạn tối đa (NĐ 111/2014)", f"{prof['max_legal_years']} năm")
    table.add_row("Trọng tải / Sức chở", f"{prof['dwt_or_passengers']:,.0f}")
    table.add_row("Thiết bị AIS", "ĐÃ LẮP ĐẶT" if prof["has_ais"] else "CHƯA CÓ")
    table.add_row("Máy vô tuyến VHF", "ĐÃ LẮP ĐẶT" if prof["has_vhf"] else "CHƯA CÓ")
    table.add_row("Kết luận kiểm định", status_text, style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@waterway_app.command("clearance")
def clearance_cmd(
    vr: str = typer.Argument(..., help="Số đăng kiểm VR của phương tiện"),
    port: str = typer.Argument(..., help="Mã cảng bến xin rời"),
    captain: str = typer.Argument(..., help="Họ tên thuyền trưởng"),
    tier: str = typer.Option("T2", "--tier", "-t", help="Hạng bằng thuyền trưởng: T1, T2, T3, T4"),
    cargo: str = typer.Option("CONTAINER", "--cargo", "-c", help="Loại hàng: CONTAINER, RICE, SAND_STONE, PETROLEUM, PASSENGERS"),
    volume: float = typer.Option(48.0, "--volume", "-v", help="Khối lượng hàng tấn hoặc số TEU"),
    passengers: int = typer.Option(0, "--passengers", "-p", help="Số lượng hành khách"),
    ais: bool = typer.Option(True, "--ais-online/--no-ais-online", help="Tín hiệu AIS hoạt động bình thường"),
    vhf: bool = typer.Option(True, "--vhf-online/--no-vhf-online", help="Tín hiệu máy VHF bình thường"),
    lifejackets: bool = typer.Option(True, "--lifejackets/--no-lifejackets", help="Đủ phao cứu sinh áo phao trên tàu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định an toàn và cấp Giấy phép rời cảng bến thủy nội địa (Cảng vụ Đường thủy)."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    result = engine.issue_port_clearance(
        vr_number=vr,
        port_code=port,
        captain_name=captain,
        captain_license_tier=tier,
        cargo_type=cargo,
        cargo_volume=volume,
        passengers_count=passengers,
        ais_online=ais,
        vhf_online=vhf,
        lifejackets_sufficient=lifejackets,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["clearance_profile"]
    status_color = "green" if prof["is_cleared"] else "red"
    status_text = "CHẤP THUẬN RỜI CẢNG BẾN" if prof["is_cleared"] else "TỪ CHỐI CẤP PHÉP RỜI BẾN"

    table = Table(title=f"Giấy Phép Rời Cảng Bến Thủy Nội Địa — Mã {prof['clearance_id']}")
    table.add_column("Hạng mục kiểm tra Cảng vụ", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold")

    table.add_row("Mã giấy phép rời bến", prof["clearance_id"])
    table.add_row("Số đăng kiểm tàu", prof["vr_number"])
    table.add_row("Cảng bến xuất bến", prof["port_code"])
    table.add_row("Thuyền trưởng điều khiển", f"{prof['captain_name']} (Bằng hạng {prof['captain_license_tier']})")
    table.add_row("Loại hàng hóa vận chuyển", prof["cargo_type"])
    table.add_row("Khối lượng hàng hóa", f"{prof['cargo_volume']:,.1f}")
    table.add_row("Số hành khách đi cùng", f"{prof['passengers_count']} người")
    table.add_row("Tín hiệu nhận dạng AIS", "ONLINE" if prof["ais_online"] else "MẤT TÍN HIỆU")
    table.add_row("Máy vô tuyến VHF", "HOẠT ĐỘNG" if prof["vhf_online"] else "HỎNG / KHÔNG CÓ")
    table.add_row("Thiết bị cứu sinh áo phao", "ĐẦY ĐỦ ĐẠT CHUẨN" if prof["lifejackets_sufficient"] else "THIẾU ÁO PHAO")
    table.add_row("Quyết định Cảng vụ", status_text, style=f"bold {status_color}")

    if prof["rejection_reason"]:
        table.add_row("Lý do từ chối rời bến", f"[bold red]{prof['rejection_reason']}[/bold red]")

    console.print(table)
    console.print(f"[dim]Thẩm quyền cấp: {result['statutory_reference']}[/dim]")


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

    if res_type in ("channels", "channel"):
        items = engine.list_channels(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Tuyến Luồng Đường Thủy Nội Địa (TCVN 5664)")
        table.add_column("Mã Luồng", style="cyan")
        table.add_column("Tên Tuyến Luồng", style="bold")
        table.add_column("Cấp Luồng", justify="center")
        table.add_column("Chiều Dài", justify="right")
        table.add_column("Độ Sâu", justify="right")
        table.add_column("Tĩnh Không Cầu", justify="right")
        table.add_column("Lưu Vực")
        for item in items.data:
            table.add_row(
                item["channel_code"],
                item["channel_name"],
                item["technical_grade"],
                f"{item['length_km']:.1f} km",
                f"{item['depth_m']:.2f} m",
                f"{item['bridge_clearance_m']:.2f} m",
                item["river_basin"],
            )
        console.print(table)

    elif res_type in ("ports", "port"):
        items = engine.list_ports(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Cảng & Bến Thủy Nội Địa (NĐ 08/2021)")
        table.add_column("Mã Cảng", style="cyan")
        table.add_column("Tên Cảng Bến", style="bold")
        table.add_column("Phân Loại")
        table.add_column("Luồng")
        table.add_column("Tỉnh/Thành")
        table.add_column("Max DWT", justify="right")
        table.add_column("Trạng Thái", justify="center", style="green")
        for item in items.data:
            table.add_row(
                item["port_code"],
                item["port_name"],
                item["port_type"],
                item["channel_code"],
                item["province"],
                f"{item['max_dwt']:,.0f} DWT",
                item["status"],
            )
        console.print(table)

    elif res_type in ("vessels", "vessel"):
        items = engine.list_vessels(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Phương Tiện Thủy Nội Địa (NĐ 111/2014)")
        table.add_column("Số VR", style="cyan")
        table.add_column("Tên Tàu / Sà Lan", style="bold")
        table.add_column("Loại Phương Tiện")
        table.add_column("Năm Đóng", justify="center")
        table.add_column("Tuổi Tàu", justify="center")
        table.add_column("Trọng Tải", justify="right")
        table.add_column("Niên Hạn", justify="center")
        for item in items.data:
            valid_txt = "[green]HỢP LỆ[/]" if item["is_lifespan_valid"] else "[red]HẾT HẠN[/]"
            table.add_row(
                item["vr_number"],
                item["vessel_name"],
                item["vessel_type"],
                str(item["year_built"]),
                f"{item['age_years']} năm",
                f"{item['dwt_or_passengers']:,.0f}",
                valid_txt,
            )
        console.print(table)

    elif res_type in ("clearances", "clearance"):
        items = engine.list_clearances(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giấy Phép Rời Cảng Bến Thủy Nội Địa")
        table.add_column("Mã Giấy Phép", style="cyan")
        table.add_column("Số VR", style="bold")
        table.add_column("Cảng Bến")
        table.add_column("Thuyền Trưởng")
        table.add_column("Hàng Hóa")
        table.add_column("Kết Quả", justify="center")
        table.add_column("Thời Gian Cấp")
        for item in items.data:
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
        items = engine.list_captains(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Thuyền Trưởng Thủy Nội Địa")
        table.add_column("Số Bằng", style="cyan")
        table.add_column("Họ Và Tên", style="bold")
        table.add_column("Hạng Bằng", justify="center")
        table.add_column("Thâm Niên", justify="right")
        table.add_column("Sức Khỏe", justify="center")
        table.add_column("Hiệu Lực", justify="center", style="green")
        for item in items.data:
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
        items = engine.list_freight_bills(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Vận Đơn Vận Tải Sà Lan")
        table.add_column("Mã Vận Đơn", style="cyan")
        table.add_column("Chủ Hàng", style="bold")
        table.add_column("Loại Hàng")
        table.add_column("Khối Lượng", justify="right")
        table.add_column("Cự Ly", justify="right")
        table.add_column("Tổng Cước", justify="right", style="bold green")
        for item in items.data:
            table.add_row(
                item["bill_id"],
                item["shipper_name"],
                item["cargo_type"],
                f"{item['volume_tons_or_teu']:,.1f}",
                f"{item['distance_km']:.1f} km",
                f"{item['total_charge_vnd']:,.0f} VND",
            )
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'channels', 'ports', 'vessels', 'clearances', 'captains', 'bills'")


@waterway_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của mạng lưới vận tải đường thủy nội địa và cảng bến."""
    from src.core.waterway_engine import WaterwayEngine

    engine = WaterwayEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Giao Thông Đường Thủy Nội Địa & Cảng Bến")
    table.add_column("Chỉ số vận hành thủy nội địa", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Tuyến luồng kỹ thuật đăng ký", str(m["registered_waterway_channels"]))
    table.add_row("Tổng chiều dài mạng lưới luồng", f"{m['total_channel_length_km']:,.1f} km")
    table.add_row("Cảng bến thủy đang hoạt động", str(m["active_river_ports"]))
    table.add_row("Phương tiện thủy đăng ký", str(m["registered_vessels"]))
    table.add_row("Phương tiện còn niên hạn lưu hành", str(m["valid_lifespan_vessels"]))
    table.add_row("Hồ sơ xin phép rời bến Cảng vụ", str(m["total_clearance_requests"]))
    table.add_row("Số lượt cấp phép rời cảng thành công", str(m["cleared_port_departures"]))
    table.add_row("Thuyền trưởng được công nhận bằng T1-T4", str(m["certified_captains"]))
    table.add_row("Số lượng vận đơn sà lan hàng hóa", str(m["barge_freight_bills"]))
    table.add_row("Tổng doanh thu cước vận tải sà lan", f"{m['total_barge_freight_revenue_vnd']:,.0f} VND")

    console.print(table)
