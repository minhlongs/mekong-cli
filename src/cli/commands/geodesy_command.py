# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Geodesy, Cartography & Geographic Information System (GIS) Suite (Phase 91)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

geodesy_app = typer.Typer(
    name="geodesy",
    help="Vietnamese Geodesy, National Coordinates (VN-2000), Map Sovereignty & Cadastral GIS Suite.",
)
console = Console()


@geodesy_app.callback(invoke_without_command=True)
def geodesy_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động đo đạc bản đồ, hệ tọa độ VN-2000, kiểm tra chủ quyền bản đồ và địa chính."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG ĐO ĐẠC BẢN ĐỒ, TỌA ĐỘ QUỐC GIA VN-2000 & CHỦ QUYỀN BIỂN ĐẢO[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['statutory_law']}[/]\n"
            f"  Hệ tọa độ chuẩn:           [bold cyan]{status_data['national_coordinate_system']}[/]\n"
            f"  Điểm tọa độ đã xử lý:      [bold cyan]{status_data['total_coordinate_points_transformed']}[/] điểm ([bold green]{status_data['valid_vietnam_territory_points']}[/] trong lãnh thổ VN)\n"
            f"  Hậu kiểm chủ quyền bản đồ: [bold]{status_data['total_map_sovereignty_inspections']}[/] ấn phẩm ([bold red]{status_data['prohibited_maps_detected']}[/] vi phạm cấm lưu hành)\n"
            f"  Tổng tiền phạt chủ quyền:  [bold red]{status_data['total_sovereignty_penalties_vnd']:,.0f} VND[/] (Nghị định 18/2020/NĐ-CP)\n"
            f"  Giấy phép hoạt động đo đạc:[bold green]{status_data['active_geodesy_operating_licenses']}[/] giấy phép hợp lệ / {status_data['total_geodesy_licenses_processed']} hồ sơ\n"
            f"  Kiểm tra đo đạc địa chính: [bold]{status_data['total_cadastral_surveys_audited']}[/] thửa đất ([bold green]{status_data['compliant_cadastral_surveys']}[/] đạt chuẩn sai số Thông tư 25/2014)",
            title="[bold green]Vietnam Geodesy, Cartography & Sovereignty GIS Telemetry[/]",
            border_style="green",
        )
    )


@geodesy_app.command("coord")
def coord_cmd(
    point: str = typer.Argument(..., help="Mã định danh điểm tọa độ (VD: MOC-HN-001)"),
    lat: float = typer.Option(21.028511, "--lat", help="Vĩ độ (Latitude) theo độ thập phân"),
    lon: float = typer.Option(105.854444, "--lon", help="Kinh độ (Longitude) theo độ thập phân"),
    zone: int = typer.Option(3, "--zone", "-z", help="Múi chiếu: 3 độ (k0=0.9999) hoặc 6 độ (k0=0.9996)"),
    province: str = typer.Option("HÀ NỘI", "--province", "-p", help="Tỉnh/Thành phố xác định kinh tuyến trục"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Chuyển đổi và kiểm tra tọa độ trắc địa phẳng VN-2000 từ kinh vĩ độ WGS-84 theo Quyết định 83/2000/QĐ-TTg."""
    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    res = engine.validate_coordinate_system(
        point_id=point,
        latitude=lat,
        longitude=lon,
        zone_deg=zone,
        province=province,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_vn = res["is_in_vietnam"]
    color = "green" if is_vn else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ CHUYỂN ĐỔI TỌA ĐỘ VN-2000 (QUYẾT ĐỊNH 83/2000/QĐ-TTg)[/]\n\n"
            f"  Mã tính toán:        [bold cyan]{res['conversion_code']}[/]\n"
            f"  Mã điểm đo:          [bold]{res['point_id']}[/]\n"
            f"  Tọa độ cầu WGS-84:   Vĩ độ: [white]{res['latitude']}[/] | Kinh độ: [white]{res['longitude']}[/]\n"
            f"  Tỉnh/Kinh tuyến trục:[yellow]{res['province']}[/] (KTT: [bold]{res['central_meridian_deg']}°[/])\n"
            f"  Múi chiếu & Tỷ lệ k0:Múi [cyan]{res['zone_deg']}°[/] (k0 = [cyan]{res['scale_factor_k0']}[/])\n"
            f"  Tọa độ phẳng X (Bắc):[bold green]{res['x_northing_m']:,.3f} m[/]\n"
            f"  Tọa độ phẳng Y (Đông):[bold green]{res['y_easting_m']:,.3f} m[/] (Đã cộng Y0 = 500,000m)\n"
            f"  Lãnh thổ Việt Nam:   [bold {color}]{'TRONG PHẠM VI LÃNH THỔ VN' if is_vn else 'NGOÀI LÃNH THỔ VN'}[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]",
            title=f"[bold {color}]VN-2000 Coordinate System Transformation[/]",
            border_style=color,
        )
    )


@geodesy_app.command("sovereignty")
def sovereignty_cmd(
    title: str = typer.Argument(..., help="Tên ấn phẩm, website, ứng dụng hoặc bản đồ kiểm tra"),
    publisher: str = typer.Option("Nền tảng Bản đồ Trực tuyến", "--publisher", help="Đơn vị xuất bản hoặc phát hành"),
    hoang_sa: bool = typer.Option(True, "--hoang-sa/--no-hoang-sa", help="Bản đồ thể hiện đầy đủ quần đảo Hoàng Sa"),
    truong_sa: bool = typer.Option(True, "--truong-sa/--no-truong-sa", help="Bản đồ thể hiện đầy đủ quần đảo Trường Sa"),
    nine_dash: bool = typer.Option(False, "--nine-dash/--no-nine-dash", help="Bản đồ có đường chín đoạn (đường lưỡi bò) phi pháp"),
    map_type: str = typer.Option("DIGITAL_WEB", "--type", help="Loại: DIGITAL_WEB, PRINTED_ATLAS, MOBILE_APP"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định tính toàn vẹn chủ quyền lãnh thổ biển đảo trên bản đồ theo Điều 6 Luật Đo đạc và bản đồ."""
    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    res = engine.audit_map_sovereignty(
        map_title=title,
        publisher_or_platform=publisher,
        has_hoang_sa=hoang_sa,
        has_truong_sa=truong_sa,
        has_nine_dash_line=nine_dash,
        map_type=map_type,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH CHỦ QUYỀN BIỂN ĐẢO TRÊN BẢN ĐỒ (ĐIỀU 6 LUẬT ĐO ĐẠC VÀ BẢN ĐỒ)[/]\n\n"
            f"  Mã thẩm định:        [bold cyan]{res['audit_code']}[/]\n"
            f"  Tên bản đồ/Ấn phẩm:  [bold]{res['map_title']}[/]\n"
            f"  Đơn vị phát hành:    [white]{res['publisher_or_platform']}[/] (Hình thức: {res['map_type']})\n"
            f"  Quần đảo Hoàng Sa:   [white]{'THỂ HIỆN HỢP LỆ' if res['has_hoang_sa'] else '[bold red]THIẾU/SAI LỆCH[/]'}[/]\n"
            f"  Quần đảo Trường Sa:  [white]{'THỂ HIỆN HỢP LỆ' if res['has_truong_sa'] else '[bold red]THIẾU/SAI LỆCH[/]'}[/]\n"
            f"  Đường chín đoạn:     [bold]{'[bold red]PHÁT HIỆN ĐƯỜNG LƯỠI BÒ PHI PHÁP[/]' if res['has_nine_dash_line'] else 'KHÔNG CÓ'}[/]\n"
            f"  Kết luận pháp lý:    [bold {color}]{res['status']}[/]\n"
            + (f"  Vi phạm nghiêm cấm:  [bold red]{'; '.join(res['deficiencies'])}[/]\n" if res["deficiencies"] else "")
            + (f"  Mức phạt ước tính:   [bold red]{res['penalty_fine_vnd']:,.0f} VND (Nghị định 18/2020/NĐ-CP)[/]\n" if res["penalty_fine_vnd"] > 0 else "")
            + f"  Biện pháp xử lý:     [bold]{res['legal_consequence']}[/]",
            title=f"[bold {color}]Map Sovereignty & Territorial Integrity Audit[/]",
            border_style=color,
        )
    )


@geodesy_app.command("license")
def license_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp xin cấp phép đo đạc bản đồ"),
    director: str = typer.Option("Kỹ sư Nguyễn Thành Long", "--director", help="Họ tên người phụ trách kỹ thuật"),
    experience: int = typer.Option(6, "--exp", help="Số năm kinh nghiệm đo đạc bản đồ của người phụ trách (>= 5 năm)"),
    surveyors: int = typer.Option(3, "--surveyors", help="Số lượng kỹ thuật viên có chứng chỉ hành nghề (>= 2)"),
    calibrated: bool = typer.Option(True, "--calibrated/--uncalibrated", help="Thiết bị đo đạc đã kiểm định, hiệu chuẩn"),
    scope: str = typer.Option("CADASTRAL_AND_TOPOGRAPHIC", "--scope", help="Phạm vi hoạt động đo đạc bản đồ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện và cấp Giấy phép hoạt động đo đạc và bản đồ theo Điều 51-52 Luật Đo đạc và bản đồ."""
    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    res = engine.license_geodesy_activity(
        enterprise_name=enterprise,
        technical_director=director,
        years_experience=experience,
        certified_surveyors_count=surveyors,
        has_calibrated_instruments=calibrated,
        scope=scope,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_approved"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH HỒ SƠ CẤP GIẤY PHÉP ĐO ĐẠC VÀ BẢN ĐỒ (ĐIỀU 51, 52)[/]\n\n"
            f"  Số giấy phép:        [bold cyan]{res['license_code']}[/]\n"
            f"  Tên doanh nghiệp:    [bold]{res['enterprise_name']}[/]\n"
            f"  Người PT kỹ thuật:   [white]{res['technical_director']}[/] ([bold]{res['years_experience']} năm kinh nghiệm[/] - Yêu cầu >= 5 năm)\n"
            f"  Kỹ thuật viên CCHN:  [white]{res['certified_surveyors_count']} nhân sự[/] (Yêu cầu >= 2 nhân sự)\n"
            f"  Kiểm định thiết bị:  [white]{'ĐẠT CHUẨN HIỆU CHUẨN' if res['has_calibrated_instruments'] else 'CHƯA KIỂM ĐỊNH'}[/]\n"
            f"  Phạm vi hoạt động:   [cyan]{res['scope']}[/]\n"
            f"  Thời hạn giấy phép:  [bold]{res['validity_years']} năm[/]\n"
            f"  Kết luận thẩm tra:   [bold {color}]{res['status']}[/]\n"
            + (f"  Thiếu sót hồ sơ:     [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:            [bold green]Hồ sơ đầy đủ, đủ điều kiện cấp Giấy phép hoạt động đo đạc và bản đồ[/]"),
            title=f"[bold {color}]Geodesy Operating License Qualification Assessment[/]",
            border_style=color,
        )
    )


@geodesy_app.command("cadastral")
def cadastral_cmd(
    parcel: str = typer.Argument(..., help="Mã định danh thửa đất hoặc tờ bản đồ (VD: THUA-45-TO-12)"),
    province: str = typer.Option("HÀ NỘI", "--province", "-p", help="Tỉnh/Thành phố nơi có thửa đất"),
    scale: str = typer.Option("1:500", "--scale", "-s", help="Tỷ lệ bản đồ địa chính: 1:500, 1:1000, 1:2000, 1:5000"),
    area: str = typer.Option("URBAN", "--area", "-a", help="Khu vực: URBAN (đô thị) hoặc RURAL (nông thôn)"),
    error: float = typer.Option(0.05, "--error", "-e", help="Sai số trung phương vị trí ranh đất đo được (m)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra sai số đo đạc ranh thửa đất bản đồ địa chính theo Điều 8 Thông tư 25/2014/TT-BTNMT."""
    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    res = engine.inspect_cadastral_survey(
        parcel_id=parcel,
        province=province,
        map_scale=scale,
        area_type=area,
        measured_boundary_error_m=error,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KIỂM TRA ĐỘ CHÍNH XÁC ĐO ĐẠC ĐỊA CHÍNH (THÔNG TƯ 25/2014/TT-BTNMT)[/]\n\n"
            f"  Mã kiểm tra:         [bold cyan]{res['survey_code']}[/]\n"
            f"  Thửa đất / Tờ BĐ:    [bold]{res['parcel_id']}[/] ({res['province']})\n"
            f"  Tỷ lệ bản đồ:        [white]{res['map_scale']}[/] (Khu vực: [yellow]{res['area_type']}[/])\n"
            f"  Sai số đo được:      [bold green]{res['measured_boundary_error_m']} m[/]\n"
            f"  Hạn mức sai số tối đa:[bold]{res['max_boundary_error_m']} m[/]\n"
            f"  Độ chính xác vị trí: [bold {color}]{'ĐẠT CHUẨN KỸ THUẬT' if is_ok else 'VƯỢT HẠN MỨC SAI SỐ'}[/]\n"
            f"  Kết luận nghiệm thu: [bold {color}]{res['status']}[/]\n"
            + (f"  Chi tiết sai số:     [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:            [bold green]Kết quả đo đạc ranh thửa đất đủ điều kiện nghiệm thu và đăng ký đất đai[/]"),
            title=f"[bold {color}]Cadastral Survey Accuracy Inspection[/]",
            border_style=color,
        )
    )


@geodesy_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("coordinates", help="Danh mục: coordinates, sovereignty, licenses, surveys"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục điểm tọa độ, thẩm định bản đồ, giấy phép đo đạc hoặc hồ sơ đo đạc địa chính."""
    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục đo đạc bản đồ & địa chính [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["sovereignty", "maps", "bien_gioi", "chu_quyen"]:
        table.add_column("Mã TĐ", style="bold cyan")
        table.add_column("Tên bản đồ", style="white")
        table.add_column("Nền tảng", style="yellow")
        table.add_column("Hoàng Sa", style="cyan")
        table.add_column("Trường Sa", style="cyan")
        table.add_column("Đường 9 đoạn", style="red")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_compliant") else "red"
            table.add_row(
                r.get("audit_code", ""),
                r.get("map_title", ""),
                r.get("publisher_or_platform", ""),
                "CÓ" if r.get("has_hoang_sa") else "KHÔNG",
                "CÓ" if r.get("has_truong_sa") else "KHÔNG",
                "CÓ" if r.get("has_nine_dash_line") else "KHÔNG",
                f"[{color}]{r.get('status', '')}[/]",
            )
    elif category in ["licenses", "enterprises", "giay_phep"]:
        table.add_column("Số giấy phép", style="bold cyan")
        table.add_column("Tên doanh nghiệp", style="white")
        table.add_column("Phụ trách KT", style="yellow")
        table.add_column("Kinh nghiệm", style="cyan")
        table.add_column("Kỹ thuật viên", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_approved") else "red"
            table.add_row(
                r.get("license_code", ""),
                r.get("enterprise_name", ""),
                r.get("technical_director", ""),
                f"{r.get('years_experience', 0)} năm",
                f"{r.get('certified_surveyors_count', 0)} CCHN",
                f"[{color}]{r.get('status', '')}[/]",
            )
    elif category in ["surveys", "cadastral", "dia_chinh"]:
        table.add_column("Mã KT", style="bold cyan")
        table.add_column("Thửa đất", style="white")
        table.add_column("Tỉnh/Thành", style="yellow")
        table.add_column("Tỷ lệ", style="cyan")
        table.add_column("Sai số đo (m)", style="green")
        table.add_column("Sai số max (m)", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_compliant") else "red"
            table.add_row(
                r.get("survey_code", ""),
                r.get("parcel_id", ""),
                r.get("province", ""),
                r.get("map_scale", ""),
                f"{r.get('measured_boundary_error_m', 0):.3f}",
                f"{r.get('max_boundary_error_m', 0):.3f}",
                f"[{color}]{r.get('status', '')}[/]",
            )
    else:
        table.add_column("Mã tính toán", style="bold cyan")
        table.add_column("Điểm đo", style="white")
        table.add_column("Vĩ độ (Lat)", style="white")
        table.add_column("Kinh độ (Lon)", style="white")
        table.add_column("Tọa độ X (Bắc)", style="green")
        table.add_column("Tọa độ Y (Đông)", style="green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_in_vietnam") else "red"
            table.add_row(
                r.get("conversion_code", ""),
                r.get("point_id", ""),
                f"{r.get('latitude', 0):.6f}",
                f"{r.get('longitude', 0):.6f}",
                f"{r.get('x_northing_m', 0):,.2f} m",
                f"{r.get('y_easting_m', 0):,.2f} m",
                f"[{color}]{r.get('status', '')}[/]",
            )

    console.print(table)


@geodesy_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp trắc địa bản đồ, tọa độ VN-2000 và chủ quyền lãnh thổ."""
    from src.core.geodesy_engine import GeodesyEngine

    engine = GeodesyEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
