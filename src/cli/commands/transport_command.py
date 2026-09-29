# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Road Transport, Logistics, Highway Tolling & ETC (Phase 73)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    engine = TransportEngine()
    result = engine.issue_business_license(
        enterprise_name=name,
        tax_id=tax_id,
        business_type=business_type,
        authorized_fleet_size=fleet,
        issuing_authority=authority,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Hồ Sơ Giấy Phép Kinh Doanh Vận Tải — {prof['license_number']}")
    table.add_column("Hạng mục cấp phép", style="cyan")
    table.add_column("Thông tin chi tiết", justify="right", style="bold green")

    table.add_row("Số giấy phép KDVT", prof["license_number"])
    table.add_row("Tên đơn vị kinh doanh", prof["enterprise_name"])
    table.add_row("Mã số thuế", prof["tax_id"])
    table.add_row("Loại hình vận tải", prof["business_name_vi"])
    table.add_row("Loại phù hiệu cấp", prof["badge_type"])
    table.add_row("Quy mô đội xe cho phép", f"{prof['authorized_fleet_size']} xe")
    table.add_row("Cơ quan cấp phép", prof["issuing_authority"])
    table.add_row("Ngày cấp phép", prof["issue_date"])
    table.add_row("Ngày hết hạn (5 năm)", prof["expiry_date"])
    table.add_row("Trạng thái giấy phép", prof["status"])

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

    engine = TransportEngine()
    result = engine.issue_vehicle_badge(
        plate_number=plate,
        license_number=license_num,
        vehicle_type=vehicle_type,
        year_built=year_built,
        seats_or_tonnage=capacity,
        has_gps=gps,
        has_camera=camera,
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

    table.add_row("Biển kiểm soát", prof["plate_number"])
    table.add_row("Loại phù hiệu yêu cầu", prof["badge_type"])
    table.add_row("Loại hình vận tải", prof["business_name_vi"])
    table.add_row("Năm sản xuất", str(prof["year_built"]))
    table.add_row("Tuổi phương tiện thực tế", f"{prof['vehicle_age_years']} năm")
    table.add_row("Niên hạn sử dụng tối đa", f"{prof['max_legal_years']} năm")
    table.add_row("Hợp lệ niên hạn (NĐ 10/2020)", "ĐẠT" if prof["is_lifespan_valid"] else "QUÁ NIÊN HẠN")
    table.add_row("Thiết bị GSHT (GPS)", "HỢP CHUẨN" if prof["has_gps"] else "CHƯA CÓ / KHÔNG ĐẠT")
    table.add_row("Camera giám sát trên xe", "ĐÃ LẮP ĐẶT" if prof["has_camera"] else "CHƯA LẮP ĐẶT")
    table.add_row("Thời hạn hiệu lực phù hiệu", prof["badge_expiry_date"])
    table.add_row("Kết luận thẩm định", status_text)

    if prof["rejection_reason"]:
        table.add_row("Lý do từ chối", f"[bold red]{prof['rejection_reason']}[/bold red]")

    console.print(table)
    console.print(f"[dim]{result['legal_note']}[/dim]")


@transport_app.command("etc")
def etc_cmd(
    plate: str = typer.Argument(..., help="Biển số xe (vd: '30E-123.45')"),
    etag: str = typer.Argument(..., help="Mã định danh thẻ RFID e-tag (vd: 'E-TAG-VETC-998877')"),
    station: str = typer.Option("Trạm BOT Pháp Vân - Cầu Giẽ", "--station", "-s", help="Tên trạm thu phí BOT"),
    vehicle_class: str = typer.Option("CLASS_1", "--class", "-c", help="Phân loại phương tiện ETC: CLASS_1, CLASS_2, CLASS_3, CLASS_4, CLASS_5"),
    provider: str = typer.Option("VETC", "--provider", "-p", help="Nhà cung cấp dịch vụ ETC: VETC hoặc EPASS"),
    balance: float = typer.Option(500000.0, "--balance", "-b", help="Số dư tài khoản giao thông (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xử lý giao dịch thu phí đường bộ tự động không dừng (ETC/MLFF) theo Quyết định 19/2020/QĐ-TTg."""
    from src.core.transport_engine import TransportEngine

    engine = TransportEngine()
    result = engine.process_etc_toll(
        plate_number=plate,
        etag_id=etag,
        bot_station_name=station,
        vehicle_class=vehicle_class,
        etc_provider=provider,
        account_balance_vnd=balance,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["transaction_profile"]
    status_color = "green" if prof["transaction_status"] == "SUCCESS" else "red"

    table = Table(title=f"Giao Dịch Thu Phí Điện Tử Không Dừng (ETC) — {prof['bot_station_name']}")
    table.add_column("Chi tiết giao dịch ETC", style="cyan")
    table.add_column("Thông số vận hành", justify="right", style="bold")

    table.add_row("Mã giao dịch", prof["transaction_id"])
    table.add_row("Biển số xe", prof["plate_number"])
    table.add_row("Mã định danh thẻ e-tag", prof["etag_id"])
    table.add_row("Nhà cung cấp ETC", prof["etc_provider"])
    table.add_row("Phân nhóm phương tiện", f"{prof['vehicle_class_name']} ({prof['vehicle_class']})")
    table.add_row("Mức phí dịch vụ sử dụng đường bộ", f"{prof['toll_fee_vnd']:,.0f} VND", style="bold yellow")
    table.add_row("Số dư tài khoản ban đầu", f"{prof['initial_balance_vnd']:,.0f} VND")
    table.add_row("Số dư tài khoản còn lại", f"{prof['remaining_balance_vnd']:,.0f} VND", style="bold green")
    table.add_row("Trạng thái giao dịch", prof["transaction_status"], style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Khung pháp lý: {result['regulatory_framework']}[/dim]")


@transport_app.command("gps")
def gps_cmd(
    plate: str = typer.Argument(..., help="Biển số xe (vd: '51B-234.56')"),
    driver: str = typer.Argument(..., help="Họ và tên lái xe"),
    license_num: str = typer.Argument(..., help="Số giấy phép lái xe"),
    continuous_hours: float = typer.Option(3.5, "--continuous", "-c", help="Thời gian lái xe liên tục (giờ)"),
    daily_hours: float = typer.Option(8.0, "--daily", "-d", help="Tổng thời gian lái xe trong ngày (giờ)"),
    rest_minutes: int = typer.Option(20, "--rest", "-r", help="Thời gian nghỉ sau phiên lái (phút)"),
    camera: bool = typer.Option(True, "--camera/--no-camera", help="Trạng thái kết nối camera giám sát"),
    gps: bool = typer.Option(True, "--gps/--no-gps", help="Trạng thái kết nối thiết bị GSHT"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Giám sát hành trình, kiểm tra thời gian lái xe liên tục (<= 4h) và trong ngày (<= 10h) theo TT 12/2020."""
    from src.core.transport_engine import TransportEngine

    engine = TransportEngine()
    result = engine.audit_journey_monitoring(
        plate_number=plate,
        driver_name=driver,
        driver_license_num=license_num,
        continuous_driving_hours=continuous_hours,
        daily_driving_hours=daily_hours,
        last_rest_minutes=rest_minutes,
        camera_online=camera,
        gps_online=gps,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    aud = result["journey_audit"]
    status_color = "green" if aud["is_compliant"] else "red"
    status_text = "ĐẠT QUY CHUẨN AN TOÀN" if aud["is_compliant"] else "PHÁT HIỆN VI PHẠM"

    table = Table(title=f"Kiểm Tra Dữ Liệu Thiết Bị GSHT & Camera — Xe {aud['plate_number']}")
    table.add_column("Chỉ số an toàn giao thông", style="cyan")
    table.add_column("Dữ liệu ghi nhận", justify="right", style="bold")

    table.add_row("Biển kiểm soát", aud["plate_number"])
    table.add_row("Họ tên lái xe", aud["driver_name"])
    table.add_row("Số giấy phép lái xe", aud["driver_license_num"])
    table.add_row("Thời gian lái liên tục (max 4.0h)", f"{aud['continuous_driving_hours']:.1f} giờ", style="yellow" if aud["continuous_driving_hours"] > 4.0 else "green")
    table.add_row("Tổng thời gian lái trong ngày (max 10.0h)", f"{aud['daily_driving_hours']:.1f} giờ", style="yellow" if aud["daily_driving_hours"] > 10.0 else "green")
    table.add_row("Thời gian nghỉ sau phiên lái (min 15p)", f"{aud['last_rest_minutes']} phút")
    table.add_row("Kết nối thiết bị GSHT (GPS)", "ONLINE" if aud["gps_online"] else "OFFLINE (VI PHẠM)")
    table.add_row("Kết nối Camera giám sát", "ONLINE" if aud["camera_online"] else "OFFLINE (VI PHẠM)")
    table.add_row("Đánh giá tuân thủ", status_text, style=f"bold {status_color}")

    if aud["violation_details"]:
        table.add_row("Chi tiết vi phạm", f"[bold red]{aud['violation_details']}[/bold red]")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@transport_app.command("weight")
def weight_cmd(
    plate: str = typer.Argument(..., help="Biển số xe (vd: '50H-999.88')"),
    config: str = typer.Option("ARTICULATED_5AXLE", "--config", "-c", help="Cấu hình trục xe: RIGID_2AXLE, RIGID_3AXLE, RIGID_4AXLE, RIGID_5AXLE, ARTICULATED_3AXLE, ARTICULATED_4AXLE, ARTICULATED_5AXLE, ARTICULATED_6AXLE"),
    weight: float = typer.Option(46.5, "--weight", "-w", help="Tổng trọng lượng xe cân thực tế (tấn)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra tải trọng trục và tổng trọng lượng xe, tính mức xử phạt quá tải theo NĐ 100/2019 & NĐ 123/2021."""
    from src.core.transport_engine import TransportEngine

    engine = TransportEngine()
    result = engine.audit_vehicle_weight(
        plate_number=plate,
        vehicle_configuration=config,
        gross_weight_tonnes=weight,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    aud = result["weight_audit"]
    is_violation = aud["is_overloaded"]
    status_color = "red" if is_violation else ("yellow" if aud["is_tolerance_zone"] else "green")
    status_text = "QUÁ TẢI — XỬ PHẠT HÀNH CHÍNH" if is_violation else ("DUNG SAI CHO PHÉP (<10%)" if aud["is_tolerance_zone"] else "ĐÚNG TẢI TRỌNG CHO PHÉP")

    table = Table(title=f"Phiếu Cân Tải Trọng Phương Tiện — Xe {aud['plate_number']}")
    table.add_column("Chỉ tiêu cân tải trọng", style="cyan")
    table.add_column("Kết quả cân & Xử lý", justify="right", style="bold")

    table.add_row("Biển kiểm soát", aud["plate_number"])
    table.add_row("Cấu hình phương tiện", f"{aud['configuration_name_vi']} ({aud['vehicle_configuration']})")
    table.add_row("Số lượng trục xe", f"{aud['axles_count']} trục")
    table.add_row("Tổng trọng lượng cân thực tế", f"{aud['gross_weight_tonnes']:.2f} tấn", style="bold")
    table.add_row("Tải trọng tối đa cho phép (TT 46/2015)", f"{aud['permitted_weight_tonnes']:.2f} tấn")
    table.add_row("Khối lượng quá tải", f"{aud['overload_tonnes']:.2f} tấn", style=f"bold {status_color}")
    table.add_row("Tỷ lệ % quá tải", f"{aud['overload_percentage']:.2f}%", style=f"bold {status_color}")
    table.add_row("Tiền phạt người điều khiển", f"{aud['fine_driver_vnd']:,.0f} VND", style="bold red" if aud["fine_driver_vnd"] > 0 else "dim")
    table.add_row("Tiền phạt chủ phương tiện", f"{aud['fine_owner_vnd']:,.0f} VND", style="bold red" if aud["fine_owner_vnd"] > 0 else "dim")
    table.add_row("Tổng tiền phạt xử lý", f"{aud['total_fine_vnd']:,.0f} VND", style="bold red" if aud["total_fine_vnd"] > 0 else "green")
    table.add_row("Tước quyền sử dụng GPLX", f"{aud['license_suspension_months']} tháng" if aud["license_suspension_months"] > 0 else "Không tước")
    table.add_row("Yêu cầu hạ tải tại trạm", "BẮT BUỘC HẠ TẢI" if aud["requires_offloading"] else "Không")
    table.add_row("Kết luận kiểm định", status_text, style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@transport_app.command("list")
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


@transport_app.command("status")
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
