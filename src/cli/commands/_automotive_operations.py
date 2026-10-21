# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RVC localization, EV battery safety audit, and vehicle inspection subcommands for Automotive CLI."""

from __future__ import annotations

import json
import typing

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_automotive_operations(automotive_app: typer.Typer) -> None:
    """Register rvc, battery, and inspect commands onto automotive_app."""
    automotive_app.command("rvc")(rvc_cmd)
    automotive_app.command("battery")(battery_cmd)
    automotive_app.command("inspect")(inspect_cmd)


def rvc_cmd(
    model: str = typer.Argument(..., help="Tên dòng xe"),
    fob: float = typer.Argument(..., help="Giá FOB xuất xưởng của xe (VND)"),
    vnm: float = typer.Argument(..., help="Trị giá nguyên liệu nhập khẩu ngoài ASEAN - VNM (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán tỷ lệ hàm lượng giá trị khu vực RVC theo Hiệp định thương mại ATIGA Form D."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.calculate_rvc_localization(
            model_name=model,
            fob_price_vnd=fob,
            non_originating_materials_vnd=vnm,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tính toán tỷ lệ nội địa hóa RVC:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]TÍNH TOÁN HÀM LƯỢNG GIÁ TRỊ KHU VỰC (RVC - ATIGA FORM D)[/]")
    table.add_column("Khoản mục chi phí", style="cyan", no_wrap=True)
    table.add_column("Giá trị", style="white")

    table.add_row("Dòng xe thẩm định", res["model_name"])
    table.add_row("Giá xuất xưởng FOB", f"{res['fob_price_vnd']:,.0f} VND")
    table.add_row("Nguyên liệu ngoại nhập (VNM)", f"{res['non_originating_materials_vnd']:,.0f} VND")
    table.add_row("Giá trị gia tăng nội khối", f"{res['local_value_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ RVC đạt được", f"[bold green]{res['rvc_rate_pct']:.2f}%[/] (Ngưỡng yêu cầu: >= {res['statutory_rvc_threshold_pct']:.0f}%)")
    status_str = "[bold green]ĐỦ ĐIỀU KIỆN CẤP C/O FORM D (Thuế nhập khẩu 0% ASEAN)[/]" if res["is_eligible_form_d"] else "[bold red]KHÔNG ĐỦ ĐIỀU KIỆN FORM D[/]"
    table.add_row("Kết luận ưu đãi thuế", status_str)

    console.print(table)


def battery_cmd(
    model: str = typer.Argument(..., help="Tên mẫu xe điện (EV Model)"),
    chemistry: str = typer.Option("LFP", "--chemistry", "-c", help="Hóa học pin: LFP, NMC, SOLID_STATE"),
    voltage: float = typer.Option(400.0, "--voltage", "-v", help="Điện áp định danh pack pin (V)"),
    capacity: float = typer.Option(87.7, "--capacity", help="Dung lượng pin danh định (kWh)"),
    overcharge: bool = typer.Option(True, "--overcharge/--no-overcharge", help="Thử nghiệm quá nạp an toàn"),
    short_circuit: bool = typer.Option(True, "--short-circuit/--no-short-circuit", help="Thử nghiệm ngắn mạch ngoài an toàn"),
    ip67: bool = typer.Option(True, "--ip67/--no-ip67", help="Đạt chuẩn ngâm nước sâu IP67"),
    thermal: bool = typer.Option(True, "--thermal/--no-thermal", help="Thử nghiệm chống cháy lan nhiệt giữa các cell an toàn"),
    cutoff: float = typer.Option(35.0, "--cutoff", help="Thời gian ngắt điện cao áp khi có va chạm (ms, trần: <= 100ms)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm toán an toàn pin xe điện và hệ thống điện cao áp theo QCVN 91:2019/BGTVT."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.audit_ev_battery_safety(
            model_name=model,
            battery_chemistry=chemistry,
            nominal_voltage_v=voltage,
            pack_capacity_kwh=capacity,
            overcharge_test_passed=overcharge,
            short_circuit_test_passed=short_circuit,
            water_immersion_ip67=ip67,
            thermal_propagation_safe=thermal,
            crash_cutoff_ms=cutoff,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi kiểm toán an toàn pin xe điện:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]KIỂM TOÁN AN TOÀN PIN XE ĐIỆN THEO QCVN 91:2019/BGTVT[/]")
    table.add_column("Hạng mục thử nghiệm an toàn", style="cyan", no_wrap=True)
    table.add_column("Kết quả đo đạc", style="white")

    table.add_row("Mẫu xe điện", res["model_name"])
    table.add_row("Hóa học pin", res["battery_chemistry"])
    table.add_row("Điện áp định danh", f"{res['nominal_voltage_v']:.1f} V DC")
    table.add_row("Dung lượng pack pin", f"{res['pack_capacity_kwh']:.1f} kWh")
    table.add_row("Thời gian ngắt mạch va chạm", f"{res['crash_cutoff_ms']:.1f} ms (Trần an toàn: <= 100 ms)")
    table.add_row("Thử nghiệm quá nạp", "[bold green]ĐẠT[/]" if res["test_results"]["overcharge_test"] else "[bold red]HỎNG[/]")
    table.add_row("Thử nghiệm ngắn mạch", "[bold green]ĐẠT[/]" if res["test_results"]["short_circuit_test"] else "[bold red]HỎNG[/]")
    table.add_row("Kháng nước ngâm sâu IP67", "[bold green]ĐẠT IP67[/]" if res["test_results"]["water_immersion_ip67"] else "[bold red]KHÔNG ĐẠT[/]")
    table.add_row("Chống cháy lan nhiệt cell", "[bold green]AN TOÀN[/]" if res["test_results"]["thermal_propagation_safe"] else "[bold red]NGUY HIỂM[/]")
    table.add_row("Chứng nhận QCVN 91:2019", f"[bold {'green' if res['is_qcvn91_certified'] else 'red'}]{res['verdict']}[/]")

    console.print(table)


def inspect_cmd(
    plate: str = typer.Argument(..., help="Biển kiểm soát xe (VD: 51K-999.88)"),
    category: str = typer.Option("PASSENGER_CAR_UNDER_9", "--category", "-c", help="Hạng mục: PASSENGER_CAR_UNDER_9, COMMERCIAL_PASSENGER, COMMERCIAL_TRUCK, ELECTRIC_VEHICLE"),
    commercial: bool = typer.Option(False, "--commercial/--non-commercial", help="Xe có kinh doanh vận tải"),
    year: int = typer.Option(2024, "--year", "-y", help="Năm sản xuất xe"),
    last_date: typing.Optional[str] = typer.Option(None, "--last-date", "-d", help="Ngày kiểm định gần nhất (YYYY-MM-DD), bỏ trống nếu xe mới"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán chu kỳ và thời hạn đăng kiểm xe cơ giới theo Thông tư 08/2023/TT-BGTVT."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    try:
        res = engine.calculate_inspection_schedule(
            plate_number=plate,
            vehicle_category=category,
            is_commercial=commercial,
            manufacture_year=year,
            last_inspection_date=last_date,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tính toán chu kỳ đăng kiểm:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]LỊCH HẠN ĐĂNG KIỂM XE CƠ GIỚI (THÔNG TƯ 08/2023/TT-BGTVT)[/]")
    table.add_column("Thông số phương tiện", style="cyan", no_wrap=True)
    table.add_column("Thông tin kiểm định", style="white")

    table.add_row("Biển số xe", f"[bold]{res['plate_number']}[/]")
    table.add_row("Phân loại phương tiện", res["vehicle_category_name_vi"])
    table.add_row("Mục đích sử dụng", "[bold yellow]Kinh doanh vận tải[/]" if res["is_commercial"] else "Không kinh doanh")
    table.add_row("Năm sản xuất / Tuổi xe", f"Năm {res['manufacture_year']} ({res['vehicle_age_years']} năm tuổi)")
    table.add_row("Chu kỳ kiểm định", f"[bold cyan]{res['cycle_months']} tháng[/]")
    table.add_row("Miễn kiểm định lần đầu", "[bold green]CÓ (Miễn đăng kiểm lần đầu xe mới)[/]" if res["is_exempt_first_inspection"] else "Không miễn")
    table.add_row("Hạn đăng kiểm tiếp theo", f"[bold green]{res['next_inspection_due_date']}[/]")

    console.print(table)
