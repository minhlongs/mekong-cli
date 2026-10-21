# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission & EV Compliance Suite (Phase 83)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._automotive_operations import (
    battery_cmd,
    inspect_cmd,
    register_automotive_operations,
    rvc_cmd,
)
from src.cli.commands._automotive_queries import (
    list_cmd,
    register_automotive_queries,
    status_cmd,
)

automotive_app = typer.Typer(
    name="automotive",
    help="Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission & EV Compliance Suite.",
)
console = Console()


@automotive_app.callback(invoke_without_command=True)
def automotive_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan ngành sản xuất ô tô, chứng nhận kiểu loại VTA, pin xe điện và chu kỳ đăng kiểm."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    mfg = status_data["manufacturers"]
    vta = status_data["type_approval"]
    ev = status_data["electric_vehicles"]
    ins = status_data["inspections"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ SẢN XUẤT Ô TÔ, CHỨNG NHẬN VTA & PIN XE ĐIỆN VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Cơ sở sản xuất ô tô: [bold cyan]{mfg['compliant_facilities']}/{mfg['total_licensed']}[/] nhà máy đạt chuẩn NĐ 116/NĐ 17 (Đường thử >= 800m)\n"
            f"  Chứng nhận VTA & E5: [bold green]{vta['certified_models']}/{vta['total_vta_audits']}[/] kiểu loại đạt chuẩn Euro 5 ([bold yellow]{vta['form_d_atiga_eligible']}[/] mẫu đủ chuẩn ATIGA Form D RVC >= 40%)\n"
            f"  An toàn pin xe điện: [bold green]{ev['qcvn91_certified_packs']}/{ev['total_battery_audits']}[/] pack pin EV đạt chuẩn QCVN 91:2019/BGTVT\n"
            f"  Đăng kiểm phương tiện:[bold cyan]{ins['total_scheduled']}[/] lượt phương tiện ([bold green]{ins['exempt_first_time']}[/] xe mới miễn đăng kiểm lần đầu TT 08/2023)",
            title="[bold green]Vietnam Automotive Manufacturing & Compliance Telemetry[/]",
            border_style="green",
        )
    )


@automotive_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp sản xuất, lắp ráp ô tô"),
    tax_id: str = typer.Option("0108877665", "--tax-id", help="Mã số thuế doanh nghiệp"),
    address: str = typer.Option("KCN Đình Vũ - Cát Hải, Hải Phòng, Việt Nam", "--address", "-a", help="Địa chỉ nhà máy"),
    track: float = typer.Option(850.0, "--track", "-t", help="Chiều dài đường thử xe nội bộ (m, tối thiểu 800m)"),
    side_slip: bool = typer.Option(True, "--side-slip/--no-side-slip", help="Có thiết bị đo trượt ngang bánh xe"),
    brake: bool = typer.Option(True, "--brake/--no-brake", help="Có thiết bị thử phanh xe"),
    emission: bool = typer.Option(True, "--emission/--no-emission", help="Có thiết bị phân tích nồng độ khí thải"),
    service_centers: int = typer.Option(45, "--service-centers", "-s", help="Số lượng cơ sở bảo hành, bảo dưỡng ủy quyền"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện sản xuất, lắp ráp ô tô theo Nghị định 116/2017/NĐ-CP & Nghị định 17/2020/NĐ-CP."""
    from src.core.automotive_engine import AutomotiveEngine
    try:
        res = AutomotiveEngine().license_manufacturer(
            company_name=name, tax_id=tax_id, factory_address=address, test_track_length_m=track,
            has_side_slip_tester=side_slip, has_brake_tester=brake, has_emission_tester=emission,
            authorized_service_centers_count=service_centers,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi thẩm định điều kiện sản xuất ô tô:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]KẾT QUẢ THẨM ĐỊNH ĐIỀU KIỆN SẢN XUẤT, LẮP RÁP Ô TÔ[/]")
    table.add_column("Hạng mục điều kiện", style="cyan", no_wrap=True)
    table.add_column("Nội dung thẩm định", style="white")
    for k, v in [
        ("Doanh nghiệp sản xuất", res["company_name"]), ("Mã số thuế", res["tax_id"]),
        ("Địa chỉ nhà máy", res["factory_address"]),
        ("Đường thử nội bộ", f"{res['test_track_length_m']:.1f} m (Chuẩn tối thiểu: {res['statutory_min_track_length_m']:.0f} m)"),
        ("Thiết bị đo trượt ngang", "[bold green]ĐẠT CHUẨN[/]" if res["equipment_readiness"]["side_slip_tester"] else "[bold red]THIẾU[/]"),
        ("Thiết bị thử phanh", "[bold green]ĐẠT CHUẨN[/]" if res["equipment_readiness"]["brake_tester"] else "[bold red]THIẾU[/]"),
        ("Thiết bị đo khí thải", "[bold green]ĐẠT CHUẨN[/]" if res["equipment_readiness"]["emission_tester"] else "[bold red]THIẾU[/]"),
        ("Mạng lưới bảo hành ủy quyền", f"{res['authorized_service_centers_count']} cơ sở trên toàn quốc"),
        ("Số giấy phép sản xuất", f"[bold green]{res['license_number']}[/]"),
        ("Kết luận thẩm định", f"[bold {'green' if res['is_compliant'] else 'red'}]{res['status']}[/]"),
    ]:
        table.add_row(k, v)
    console.print(table)


@automotive_app.command("vta")
def vta_cmd(
    model: str = typer.Argument(..., help="Tên dòng xe / mẫu mã (Model)"),
    v_type: str = typer.Option("PASSENGER_CAR_UNDER_9", "--type", "-t", help="Loại xe: PASSENGER_CAR_UNDER_9, COMMERCIAL_PASSENGER, COMMERCIAL_TRUCK, ELECTRIC_VEHICLE"),
    powertrain: str = typer.Option("GASOLINE", "--powertrain", "-p", help="Động cơ: GASOLINE, DIESEL, ELECTRIC, HYBRID"),
    co: float = typer.Option(0.65, "--co", help="Phát thải CO (g/km, trần Euro 5: 1.00 g/km)"),
    nox: float = typer.Option(0.045, "--nox", help="Phát thải NOx (g/km, trần Euro 5: 0.060 g/km)"),
    pm: float = typer.Option(0.002, "--pm", help="Phát thải hạt bụi mịn PM (g/km, trần Euro 5: 0.0045 g/km)"),
    rvc: float = typer.Option(42.5, "--rvc", "-r", help="Tỷ lệ nội địa hóa khu vực RVC (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định Chứng nhận kiểu loại ô tô (VTA) theo Thông tư 25/2019/TT-BGTVT và chuẩn Euro 5."""
    from src.core.automotive_engine import AutomotiveEngine
    try:
        res = AutomotiveEngine().audit_type_approval(
            model_name=model, vehicle_type=v_type, powertrain_type=powertrain,
            co_g_km=co, nox_g_km=nox, pm_g_km=pm, rvc_rate_pct=rvc,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi thẩm định chứng nhận kiểu loại VTA:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]CHỨNG NHẬN CHẤT LƯỢNG AN TOÀN KỸ THUẬT VÀ BVMT KIỂU LOẠI (VTA)[/]")
    table.add_column("Chỉ số thẩm định", style="cyan", no_wrap=True)
    table.add_column("Kết quả thử nghiệm", style="white")
    for k, v in [
        ("Dòng xe (Model)", res["model_name"]), ("Phân loại xe", res["vehicle_type_name_vi"]),
        ("Hệ truyền động", res["powertrain_type"]), ("Nồng độ phát thải CO", f"{res['co_g_km']:.3f} g/km"),
        ("Nồng độ phát thải NOx", f"{res['nox_g_km']:.3f} g/km"), ("Nồng độ phát thải PM", f"{res['pm_g_km']:.4f} g/km"),
        ("Tiêu chuẩn khí thải", f"[bold yellow]{res['emission_standard']}[/]"),
        ("Đạt chuẩn khí thải Euro 5", "[bold green]ĐẠT CHUẨN[/]" if res["is_emission_compliant"] else "[bold red]KHÔNG ĐẠT[/]"),
        ("Tỷ lệ nội địa hóa (RVC)", f"{res['rvc_rate_pct']:.2f}% (ATIGA Form D: {'[bold green]HƯỞNG THUẾ 0%[/]' if res['is_rvc_eligible_form_d'] else '[bold red]CHƯA ĐỦ ĐIỀU KIỆN[/]'})"),
        ("Mã chứng chỉ VTA (Cục Đăng kiểm)", f"[bold green]{res['vta_certificate_no']}[/]"),
        ("Trạng thái phê duyệt", f"[bold {'green' if res['status'] == 'CERTIFIED' else 'red'}]{res['status']}[/]"),
    ]:
        table.add_row(k, v)
    console.print(table)


register_automotive_operations(automotive_app)
register_automotive_queries(automotive_app)

__all__ = ["automotive_app", "automotive_main", "license_cmd", "vta_cmd", "rvc_cmd", "battery_cmd", "inspect_cmd", "list_cmd", "status_cmd"]
