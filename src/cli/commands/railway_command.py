# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Railway Transport, High-Speed Rail & Metro (Phase 72)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
railway_app = typer.Typer(
    name="railway",
    help="Railway — Vietnamese Railway Transport, High-Speed Rail (HSR 350 km/h) & Urban Metro",
    add_completion=False,
)


@railway_app.callback(invoke_without_command=True)
def railway_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Vận tải Đường sắt, Đường sắt Tốc độ cao Bắc - Nam & Metro đô thị."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ ĐƯỜNG SẮT, ĐƯỜNG SẮT TỐC ĐỘ CAO & METRO (LUẬT ĐƯỜNG SẮT & NQ 172/2024)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Tuyến đường sắt:     [bold cyan]{m['registered_railway_lines']} tuyến[/] (Tổng chiều dài mạng lưới: [bold]{m['total_rail_network_km']:,.1f} km[/])\n"
            f"  Hành lang an toàn:   [bold]{m['corridor_safety_audits']} đoạn kiểm định[/] (Đạt chuẩn NĐ 56/2018: [bold green]{m['compliant_corridor_sections']}[/])\n"
            f"  Phương tiện đầu máy: [bold]{m['registered_rolling_stock_vehicles']} phương tiện[/] (Hợp lệ niên hạn NĐ 65: [bold green]{m['legal_active_rolling_stock']}[/])\n"
            f"  Vận tải hàng hóa:    [bold]{m['freight_transport_orders']} vận đơn[/] (Sản lượng: [bold]{m['total_freight_transported_tons']:,.1f} tấn[/] | Doanh thu cước: [bold green]{m['total_freight_revenue_vnd']:,.0f} VND[/])\n"
            f"  Cấp phép lái tàu:    [bold]{m['driver_license_audits']} hồ sơ sát hạch[/] (Được cấp giấy phép: [bold green]{m['licensed_train_drivers']}[/])",
            title="[bold blue]Vietnam National Railway, High-Speed Rail & Urban Metro Telemetry[/]",
            border_style="green",
        )
    )


@railway_app.command("line")
def line_cmd(
    name: str = typer.Argument(..., help="Tên tuyến đường sắt (vd: Tuyến Đường Sắt Tốc Độ Cao Bắc - Nam)"),
    code: str = typer.Argument(..., help="Mã tuyến đường sắt (vd: HSR-BN-01)"),
    category: str = typer.Option("HIGH_SPEED_RAIL", "--category", "-c", help="Phân loại tuyến: HIGH_SPEED_RAIL, URBAN_METRO, NATIONAL_RAIL, INDUSTRIAL_RAIL"),
    gauge: str = typer.Option("STANDARD_1435MM", "--gauge", "-g", help="Khổ đường ray: STANDARD_1435MM, METRE_1000MM, DUAL_GAUGE"),
    length: float = typer.Option(1541.0, "--length", "-l", help="Chiều dài toàn tuyến (km)"),
    stations: int = typer.Option(23, "--stations", "-s", help="Số lượng nhà ga"),
    speed: float = typer.Option(350.0, "--speed", "-v", help="Tốc độ thiết kế tối đa (km/h)"),
    electrified: bool = typer.Option(True, "--electrified/--diesel", help="Tuyến điện khí hóa hay dùng đầu máy diesel"),
    operator: str = typer.Option("Tổng Công ty Đường sắt Việt Nam (VNR)", "--operator", "-o", help="Đơn vị quản lý khai thác"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký tuyến đường sắt hạ tầng, khổ đường ray và tốc độ thiết kế theo Luật Đường sắt 2017."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    result = engine.register_railway_line(
        line_name=name,
        line_code=code,
        rail_category=category,
        gauge_type=gauge,
        length_km=length,
        stations_count=stations,
        design_speed_kmh=speed,
        is_electrified=electrified,
        operator_name=operator,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["line_profile"]
    table = Table(title=f"Hồ Sơ Đăng Ký Tuyến Đường Sắt — {prof['line_name']} ({prof['line_code']})")
    table.add_column("Chỉ tiêu hạ tầng kỹ thuật", style="cyan")
    table.add_column("Thông số vận hành", justify="right", style="bold green")

    table.add_row("Tên tuyến đường sắt", prof["line_name"])
    table.add_row("Mã định danh tuyến", prof["line_code"])
    table.add_row("Phân loại tuyến", prof["rail_category_vi"])
    table.add_row("Khổ đường ray", prof["gauge_name_vi"])
    table.add_row("Chiều rộng khổ ray", f"{prof['gauge_mm']} mm")
    table.add_row("Chiều dài toàn tuyến", f"{prof['length_km']:,.1f} km")
    table.add_row("Số lượng ga tiếp nhận", f"{prof['stations_count']} ga")
    table.add_row("Tốc độ thiết kế tối đa", f"{prof['design_speed_kmh']:,.0f} km/h")
    table.add_row("Phương thức cấp năng lượng", prof["electrification_status"])
    table.add_row("Hành lang an toàn tối thiểu", f">= {prof['statutory_corridor_min_m']:.1f} m")
    table.add_row("Hàng rào cách ly bảo vệ", "[bold green]BẮT BUỘC CÁCH LY HOÀN TOÀN[/]" if prof["barrier_mandatory"] else "Không bắt buộc")
    table.add_row("Đơn vị vận hành", prof["operator_name"])

    console.print(table)


@railway_app.command("corridor")
def corridor_cmd(
    line_id: str = typer.Argument(..., help="Mã tuyến đường sắt (RLN-xxxx)"),
    structure: str = typer.Option("AT_GRADE", "--structure", "-s", help="Kết cấu công trình: AT_GRADE, ELEVATED_VIADUCT, UNDERGROUND_TUNNEL, URBAN_AT_GRADE"),
    speed: float = typer.Option(350.0, "--speed", "-v", help="Tốc độ chạy tàu tại lý trình kiểm định (km/h)"),
    buffer: float = typer.Option(22.0, "--buffer", "-b", help="Khoảng cách đệm an toàn thực tế từ mép ngoài ray/công trình (m)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định hành lang an toàn giao thông đường sắt theo Nghị định 56/2018/NĐ-CP."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    result = engine.audit_safety_corridor(
        line_id=line_id,
        structure_type=structure,
        speed_kmh=speed,
        actual_buffer_m=buffer,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    c = result["corridor_audit"]
    table = Table(title=f"Thẩm Định Hành Lang An Toàn Đường Sắt — {c['line_id']} ({result['audit_id']})")
    table.add_column("Chỉ tiêu thẩm định hành lang", style="cyan")
    table.add_column("Thông số", justify="right", style="bold green")

    table.add_row("Mã tuyến đường sắt", c["line_id"])
    table.add_row("Loại kết cấu công trình", c["structure_type"])
    table.add_row("Tốc độ đoạn tuyến", f"{c['speed_kmh']:,.0f} km/h")
    table.add_row("Khoảng cách đệm thực tế", f"{c['actual_buffer_m']:,.1f} m")
    table.add_row("Khoảng cách tối thiểu theo luật", f">= {c['required_buffer_m']:,.1f} m")
    table.add_row("Căn cứ pháp lý", c["statutory_criterion"])
    table.add_row("Đánh giá an toàn", "[bold green]ĐẠT CHUẨN AN TOÀN[/]" if c["is_corridor_compliant"] else "[bold red]VI PHẠM HÀNH LANG[/]")

    console.print(table)
    verdict_style = "bold green" if c["is_corridor_compliant"] else "bold red"
    console.print(f"[{verdict_style}]KẾT LUẬN: {c['corridor_verdict']}[/]")


@railway_app.command("stock")
def stock_cmd(
    code: str = typer.Argument(..., help="Số hiệu đoàn tàu / đầu máy / toa xe (vd: HSR-EMU-350-01)"),
    vehicle_type: str = typer.Option("EMU_TRAINSET", "--type", "-t", help="Loại phương tiện: EMU_TRAINSET, LOCOMOTIVE_DIESEL, LOCOMOTIVE_ELECTRIC, PASSENGER_COACH, FREIGHT_WAGON"),
    maker: str = typer.Option("Hitachi Rail / CRRC", "--maker", "-m", help="Nhà chế tạo phương tiện"),
    year: int = typer.Option(2024, "--year", "-y", help="Năm sản xuất xuất xưởng"),
    gauge: str = typer.Option("STANDARD_1435MM", "--gauge", "-g", help="Khổ ray phương tiện: STANDARD_1435MM, METRE_1000MM"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký phương tiện đường sắt và kiểm tra niên hạn sử dụng theo Nghị định 65/2018/NĐ-CP."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    result = engine.register_rolling_stock(
        vehicle_code=code,
        vehicle_type=vehicle_type,
        manufacturer=maker,
        year_built=year,
        gauge_type=gauge,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    r = result["rolling_stock"]
    table = Table(title=f"Hồ Sơ Đăng Kiểm Niên Hạn Phương Tiện Đường Sắt — {r['vehicle_code']} ({result['vehicle_id']})")
    table.add_column("Chỉ tiêu phương tiện đường sắt", style="cyan")
    table.add_column("Thông số kỹ thuật & Pháp lý", justify="right", style="bold green")

    table.add_row("Số hiệu phương tiện", r["vehicle_code"])
    table.add_row("Loại phương tiện", r["vehicle_type"])
    table.add_row("Nhà chế tạo", r["manufacturer"])
    table.add_row("Năm xuất xưởng", str(r["year_built"]))
    table.add_row("Tuổi phương tiện hiện tại", f"{r['age_years']} năm")
    table.add_row("Niên hạn tối đa cho phép", f"{r['max_legal_years']} năm")
    table.add_row("Thời gian còn được phép lưu hành", f"[bold yellow]{r['years_remaining']} năm[/]")
    table.add_row("Khổ ray tương thích", r["gauge_type"])
    table.add_row("Tình trạng pháp lý niên hạn", "[bold green]HỢP LỆ LƯU HÀNH[/]" if r["is_lifespan_valid"] else "[bold red]HẾT NIÊN HẠN[/]")

    console.print(table)
    verdict_style = "bold green" if r["is_lifespan_valid"] else "bold red"
    console.print(f"[{verdict_style}]KẾT LUẬN ĐĂNG KIỂM: {r['lifespan_verdict']}[/]")


@railway_app.command("freight")
def freight_cmd(
    shipper: str = typer.Argument(..., help="Tên chủ hàng / doanh nghiệp gửi hàng"),
    cargo_type: str = typer.Option("CONTAINER_TEU", "--type", "-t", help="Loại hàng hóa: CONTAINER_TEU, BULK_AGRICULTURAL, HEAVY_INDUSTRIAL, GENERAL_CARGO"),
    weight: float = typer.Option(24.0, "--weight", "-w", help="Khối lượng hàng hóa vận chuyển (tấn)"),
    distance: float = typer.Option(850.0, "--distance", "-d", help="Cự ly vận chuyển đường sắt (km)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính cước vận tải hàng hóa đường sắt theo tấn-km và quy chế giá cước đường sắt."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    result = engine.calculate_freight_tariff(
        shipper_name=shipper,
        cargo_type=cargo_type,
        weight_tons=weight,
        distance_km=distance,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["freight_bill"]
    table = Table(title=f"Biểu Cước Vận Tải Hàng Hóa Đường Sắt — {b['shipper_name']} ({result['order_id']})")
    table.add_column("Hạng mục tính cước", style="cyan")
    table.add_column("Định mức & Thành tiền", justify="right", style="bold green")

    table.add_row("Chủ hàng", b["shipper_name"])
    table.add_row("Loại hàng hóa", b["cargo_type"])
    table.add_row("Khối lượng tính cước", f"{b['weight_tons']:,.1f} tấn")
    table.add_row("Cự ly vận tải", f"{b['distance_km']:,.1f} km")
    table.add_row("Sản lượng luân chuyển", f"{b['ton_km']:,.1f} tấn.km")
    table.add_row("Đơn giá cước cơ bản", f"{b['rate_per_ton_km_vnd']:,.0f} VND/tấn.km")
    table.add_row("Tiền cước vận chuyển", f"{b['base_freight_vnd']:,.0f} VND")
    table.add_row("Phí xếp dỡ ga (Terminal Handling)", f"{b['terminal_handling_vnd']:,.0f} VND")
    table.add_row("Tổng trước thuế", f"{b['subtotal_vnd']:,.0f} VND")
    table.add_row("Thuế VAT (10%)", f"{b['vat_vnd']:,.0f} VND")
    table.add_row("TỔNG CƯỚC THANH TOÁN", f"[bold yellow]{b['total_amount_vnd']:,.0f} VND[/]")

    console.print(table)


@railway_app.command("driver")
def driver_cmd(
    name: str = typer.Argument(..., help="Họ tên lái tàu"),
    license_type: str = typer.Option("HIGH_SPEED_EMU", "--type", "-t", help="Hạng giấy phép: HIGH_SPEED_EMU, URBAN_METRO, DIESEL_ELECTRIC"),
    age: int = typer.Option(35, "--age", "-a", help="Tuổi lái tàu (21 - 60)"),
    exp: int = typer.Option(36, "--exp", "-e", help="Thời gian tập sự thực hành lái phụ (tháng)"),
    health: int = typer.Option(1, "--health", "-h", help="Phân loại sức khỏe (1 = Loại 1, 2 = Loại 2)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện cấp giấy phép lái tàu theo Thông tư 33/2018/TT-BGTVT."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    result = engine.audit_train_driver_license(
        driver_name=name,
        license_type=license_type,
        driver_age=age,
        experience_months=exp,
        health_class=health,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    d = result["driver_license_audit"]
    table = Table(title=f"Thẩm Định Sát Hạch Giấy Phép Lái Tàu — {d['driver_name']} ({result['license_id']})")
    table.add_column("Tiêu chuẩn sát hạch chức danh", style="cyan")
    table.add_column("Hồ sơ thực tế", justify="right")
    table.add_column("Quy định TT 33/2018", justify="right")
    table.add_column("Kết luận", justify="center")

    table.add_row(
        "Độ tuổi lái tàu",
        f"{d['driver_age']} tuổi",
        "21 - 60 tuổi",
        "[bold green]ĐẠT[/]" if d["age_compliant"] else "[bold red]KHÔNG ĐẠT[/]",
    )
    table.add_row(
        "Thời gian tập sự lái phụ",
        f"{d['experience_months']} tháng",
        f">= {d['required_experience_months']} tháng",
        "[bold green]ĐẠT[/]" if d["experience_compliant"] else "[bold red]THIẾU TẬP SỰ[/]",
    )
    table.add_row(
        "Tiêu chuẩn sức khỏe chạy tàu",
        f"Sức khỏe Loại {d['health_class']}",
        "Loại 1 (Bắt buộc)",
        "[bold green]ĐẠT[/]" if d["health_compliant"] else "[bold red]KHÔNG ĐẠT[/]",
    )

    console.print(table)
    verdict_style = "bold green" if d["is_license_granted"] else "bold red"
    console.print(f"[{verdict_style}]KẾT LUẬN SÁT HẠCH: {d['license_verdict']}[/]")


@railway_app.command("list")
def list_cmd(
    category: str = typer.Argument("lines", help="Danh mục: lines (tuyến đường sắt), corridor (hành lang an toàn), stock (phương tiện), freight (vận đơn hàng hóa), drivers (giấy phép lái tàu)"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh sách tuyến đường sắt, hành lang an toàn, đầu máy toa xe, cước vận tải hoặc bằng lái tàu."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    cat = category.lower().strip()

    if cat in ("lines", "line"):
        records = engine.list_railway_lines(limit=limit)
        key = "railway_lines"
    elif cat in ("corridor", "corridors", "safety"):
        records = engine.list_corridor_audits(limit=limit)
        key = "corridor_audits"
    elif cat in ("stock", "vehicles", "trains"):
        records = engine.list_rolling_stock(limit=limit)
        key = "rolling_stock"
    elif cat in ("freight", "orders", "cargo"):
        records = engine.list_freight_orders(limit=limit)
        key = "freight_orders"
    elif cat in ("drivers", "driver", "licenses"):
        records = engine.list_driver_licenses(limit=limit)
        key = "driver_licenses"
    else:
        records = engine.list_railway_lines(limit=limit)
        key = "railway_lines"

    if json_mode:
        typer.echo(json.dumps({key: records.data}, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Dữ Liệu Đường Sắt & Metro ({category.upper()}) — {len(records)} Bản Ghi")
    if records:
        for k in records[0].keys():
            table.add_column(k, style="cyan")
        for item in records:
            table.add_row(*[str(item[k]) for k in item.keys()])
    else:
        table.add_column("Thông báo", style="yellow")
        table.add_row("Chưa có bản ghi nào được ghi nhận.")

    console.print(table)


@railway_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Báo cáo tổng quan hệ thống đường sắt, đường sắt tốc độ cao và metro."""
    from src.core.railway_engine import RailwayEngine

    engine = RailwayEngine()
    data = engine.get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    table = Table(title="Tổng Quan Vận Tải Đường Sắt & Metro (Railway Telemetry)")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Tuyến đường sắt đã đăng ký", str(m["registered_railway_lines"]))
    table.add_row("Tổng chiều dài mạng lưới đường ray", f"{m['total_rail_network_km']:,.1f} km")
    table.add_row("Đoạn hành lang an toàn kiểm định", str(m["corridor_safety_audits"]))
    table.add_row("Đoạn hành lang đạt chuẩn NĐ 56/2018", str(m["compliant_corridor_sections"]))
    table.add_row("Đầu máy toa xe đã kiểm định niên hạn", str(m["registered_rolling_stock_vehicles"]))
    table.add_row("Phương tiện đủ điều kiện lưu hành", str(m["legal_active_rolling_stock"]))
    table.add_row("Vận đơn hàng hóa đường sắt", str(m["freight_transport_orders"]))
    table.add_row("Tổng sản lượng hàng hóa", f"{m['total_freight_transported_tons']:,.1f} tấn")
    table.add_row("Tổng doanh thu cước vận tải", f"{m['total_freight_revenue_vnd']:,.0f} VND")
    table.add_row("Hồ sơ sát hạch lái tàu", str(m["driver_license_audits"]))
    table.add_row("Lái tàu được cấp giấy phép", str(m["licensed_train_drivers"]))

    console.print(table)
