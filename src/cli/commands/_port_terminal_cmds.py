# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 179: Seaport Terminal Tariffs (TT 39/2023), DEM/DET Escalations & SOLAS VGM CLI."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.port_supply_chain_engine import (
    CargoStatus,
    ContainerType,
    PortArea,
    SeaportTerminalOpsEngine,
)

console = Console()

port_app = typer.Typer(
    name="port",
    help="PORT — Vietnam Seaport Terminal Operations, DEM/DET & SOLAS VGM Suite (Phase 179)",
    no_args_is_help=False,
)


@port_app.callback(invoke_without_command=True)
def port_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Quản trị Cảng biển, Biểu phí THC, DEM/DET & Cân VGM."""
    if ctx.invoked_subcommand is not None:
        return
    if json_mode:
        data = {
            "suite": "Mekong Seaport Terminal Operations & SOLAS VGM Suite (Phase 179)",
            "statutory_basis": [
                "Circular 39/2023/TT-BGTVT (Vietnam Seaport Tariffs & Container Stevedoring)",
                "Vietnam Maritime Code 2015 Article 168 (Statutory Maritime Lien for Unpaid Demurrage)",
                "IMO SOLAS Chapter VI Regulation 2 & MSC.1/Circ.1475 (Verified Gross Mass)",
                "Decree 58/2017/ND-CP (Maritime Transport & Seaport Administration)",
            ],
            "commands": ["tariff", "dem-det", "vgm"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Seaport Terminal Operations & Maritime Suite (Phase 179)[/bold cyan]\n"
            "[dim]Kiểm soát chi phí bốc dỡ cảng biển, lũy tiến phạt lưu bãi/lưu vỏ và cân tải trọng SOLAS.[/dim]\n\n"
            "• [bold green]tariff[/bold green]   : Biểu phí bốc dỡ container (Lạch Huyện, Đà Nẵng, Cái Mép, Cát Lái - TT 39/2023).\n"
            "• [bold yellow]dem-det[/bold yellow]  : Lũy tiến phí lưu bãi/vỏ (Tier 1-3) & cảnh báo quyền cầm giữ hàng (Điều 168 BLLHH).\n"
            "• [bold blue]vgm[/bold blue]      : Xác thực dung sai cân SOLAS VGM (+/-5% hoặc 500kg) & cấp lệnh hạ bãi Gate-in.",
            title="⚓ [bold]QUẢN TRỊ CẢNG BIỂN & SOLAS VGM[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@port_app.command("tariff")
def port_tariff(
    area: str = typer.Option("AREA_III_SOUTH", "--area", "-a", help="Cụm cảng (AREA_I_NORTH, AREA_II_CENTRAL, AREA_III_SOUTH)"),
    container_type: str = typer.Option("DRY_40FT", "--container", "-c", help="Loại container (DRY_20FT, DRY_40FT, DRY_45FT, REEFER_20FT, REEFER_40FT, OOG_FLATRACK, DG_CONTAINER)"),
    status: str = typer.Option("LADEN", "--status", "-s", help="Trạng thái hàng (LADEN: có hàng, EMPTY: vỏ rỗng)"),
    reefer_hours: float = typer.Option(0.0, "--reefer-hours", "-r", help="Số giờ cắm điện lạnh container reefer"),
    imo: bool = typer.Option(False, "--imo", help="Hàng nguy hiểm IMO/DG (+50% phụ phí)"),
    oog: bool = typer.Option(False, "--oog", help="Hàng quá khổ quá tải OOG (+100% phụ phí)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi phí xếp dỡ cảng biển và phụ phí theo Thông tư 39/2023/TT-BGTVT."""
    area_enum = PortArea.__members__.get(area.upper(), PortArea.AREA_III_SOUTH)
    c_type_enum = ContainerType.__members__.get(container_type.upper(), ContainerType.DRY_40FT)
    status_enum = CargoStatus.__members__.get(status.upper(), CargoStatus.LADEN)

    res = SeaportTerminalOpsEngine.calculate_port_tariff(
        port_area=area_enum, container_type=c_type_enum, cargo_status=status_enum,
        reefer_plug_hours=reefer_hours, is_imo_dangerous=imo, is_oog=oog,
    )
    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="⚓ BIỂU PHÍ BỐC DỠ CẢNG BIỂN (THÔNG TƯ 39/2023/TT-BGTVT)", box=box.ROUNDED)
    table.add_column("Hạng mục Phí", style="cyan", justify="left")
    table.add_column("Chi tiết / Mức tính", style="magenta", justify="right")
    for k, v in [
        ("Khu vực Cảng biển", area_enum.value),
        ("Loại Container & Trạng thái", f"{c_type_enum.value} ({status_enum.value})"),
        ("Phí xếp dỡ cơ bản (THC)", f"{res.base_thc_vnd:,.0f} VND"),
    ]:
        table.add_row(k, v)
    if res.reefer_power_vnd > 0:
        table.add_row(f"Điện lạnh Reefer ({reefer_hours:.1f}h)", f"{res.reefer_power_vnd:,.0f} VND")
    if res.surcharge_vnd > 0:
        table.add_row("Phụ phí Đặc thù (IMO / OOG)", f"{res.surcharge_vnd:,.0f} VND")
    table.add_section()
    table.add_row("[bold green]TỔNG CỘNG CHI PHÍ[/bold green]", f"[bold green]{res.total_port_charge_vnd:,.0f} VND[/bold green]")
    console.print(table)


@port_app.command("dem-det")
def port_dem_det(
    container_id: str = typer.Option("TCLU8291045", "--id", help="Số hiệu container ISO"),
    container_type: str = typer.Option("DRY_40FT", "--type", "-t", help="Loại container (DRY_20FT, DRY_40FT, DRY_45FT)"),
    days_incurred: int = typer.Option(8, "--days", "-d", help="Tổng số ngày lưu bãi/lưu vỏ thực tế"),
    free_days: int = typer.Option(5, "--free-days", "-f", help="Số ngày miễn phí (Free time) theo hãng tàu"),
    cif_value_usd: float = typer.Option(25000.0, "--cif-usd", help="Trị giá CIF lô hàng (USD) để xét quyền cầm giữ hàng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán phí lũy tiến Demurrage/Detention (DEM/DET) & đánh giá quyền cầm giữ hàng (Điều 168 BLLHH 2015)."""
    c_type_enum = ContainerType.__members__.get(container_type.upper(), ContainerType.DRY_40FT)
    res = SeaportTerminalOpsEngine.calculate_dem_det(
        container_id=container_id, container_type=c_type_enum, days_incurred=days_incurred,
        free_days_allowed=free_days, cargo_cif_value_usd=cif_value_usd,
    )
    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="⚠️ QUẢN TRỊ DEM/DET & QUYỀN CẦM GIỮ HÀNG HẢI", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")
    for k, v in [
        ("Số hiệu Container", res.container_id), ("Hạn Miễn phí (Free Time)", f"{res.free_days_allowed} ngày"),
        ("Thời gian Thực tế", f"{res.days_incurred} ngày"), ("Số ngày Quá hạn (Overdue)", f"{res.overdue_days} ngày"),
        ("Giai đoạn Lũy tiến", res.stage.value), ("Đơn giá phạt hiện tại", f"${res.daily_rate_usd:,.2f} USD/ngày"),
    ]:
        table.add_row(k, v)
    table.add_section()
    table.add_row("[bold red]Tổng Phạt Quá Hạn (USD)[/bold red]", f"[bold red]${res.total_penalty_usd:,.2f} USD[/bold red]")
    table.add_row("Quy đổi tương đương (VND)", f"{res.total_penalty_vnd:,.0f} VND")
    table.add_row("Cảnh báo Cầm giữ hàng (Điều 168)", "[bold red]CÓ CẢNH BÁO[/bold red]" if res.carrier_lien_warning else "[bold green]AN TOÀN[/bold green]")
    console.print(table)
    if res.carrier_lien_warning:
        console.print(Panel(f"[bold red]CẢNH BÁO PHÁP LÝ:[/bold red] {res.lien_rationale}", border_style="red"))


@port_app.command("vgm")
def port_vgm(
    container_id: str = typer.Option("MSKU1092834", "--id", help="Số hiệu container ISO"),
    declared_kg: float = typer.Option(24500.0, "--declared", "-w", help="Khối lượng VGM khai báo (kg)"),
    measured_kg: float = typer.Option(24850.0, "--measured", "-m", help="Khối lượng cân thực tế tại bàn cân cảng (kg)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xác thực sai số khối lượng toàn bộ SOLAS VGM theo quy chuẩn IMO MSC.1/Circ.1475."""
    res = SeaportTerminalOpsEngine.verify_solas_vgm(container_id=container_id, declared_vgm_kg=declared_kg, verified_scale_kg=measured_kg)
    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="⚖️ XÁC THỰC TẢI TRỌNG SOLAS VGM (IMO CHAPTER VI REG 2)", box=box.ROUNDED)
    table.add_column("Chỉ số Kiểm tra", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")
    for k, v in [
        ("Số hiệu Container", res.container_id), ("VGM Khai báo (Shipper Declared)", f"{res.declared_vgm_kg:,.1f} kg"),
        ("VGM Thực tế (Terminal Weighbridge)", f"{res.verified_scale_kg:,.1f} kg"),
        ("Chênh lệch Tuyệt đối", f"{res.variance_kg:,.1f} kg ({res.variance_pct:.2f}%)"),
        ("Dung sai Tối đa Cho phép (min 5%, 500kg)", f"{res.max_allowable_variance_kg:,.1f} kg"),
    ]:
        table.add_row(k, v)
    table.add_section()
    table.add_row("Trạng thái Tuân thủ", "[bold green]HỢP LỆ (COMPLIANT)[/bold green]" if res.is_compliant else "[bold red]VI PHẠM (NON-COMPLIANT)[/bold red]")
    table.add_row("Lệnh Cấp Phép Hạ Bãi / Xếp Tàu", f"[bold]{res.gate_in_status}[/bold]")
    console.print(table)
    if not res.is_compliant:
        console.print(Panel(f"[bold red]TỪ CHỐI XẾP TÀU (NO VGM, NO LOAD):[/bold red]\n{res.rejection_reason}\nƯớc tính phí phạt cân lại: {res.penalty_estimate_vnd:,.0f} VND", border_style="red"))
