# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ETC tolling, GPS journey monitoring, and vehicle weight audit subcommands for Transport CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_transport_operations(transport_app: typer.Typer) -> None:
    """Register etc, gps, and weight commands onto transport_app."""
    transport_app.command("etc")(etc_cmd)
    transport_app.command("gps")(gps_cmd)
    transport_app.command("weight")(weight_cmd)


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
