# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 181: Pharma Cold Chain Integrity, Arrhenius MKT & GDP Quarantine Holds CLI."""

from __future__ import annotations

import json
from typing import List

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._port_terminal_cmds import console
from src.cli.commands._tradefinance_lc_cmds import tradefinance_app
from src.core.port_supply_chain_engine import (
    ColdChainPharmaGDPEngine,
    PharmaStorageClass,
    TemperatureExcursionEvent,
)


@tradefinance_app.command("mkt")
def tradefinance_mkt(
    batch_id: str = typer.Option("VAX-2026-0914", "--batch", help="Mã số lô hàng sinh phẩm / vaccine"),
    temps: str = typer.Option("4.2,4.5,5.1,5.8,6.2,4.8,3.9,4.4", "--temps", "-t", help="Dữ liệu nhiệt độ đo định kỳ (°C), phân cách dấu phẩy"),
    storage_class: str = typer.Option("COLD_CHAIN", "--class", "-c", help="Loại bảo quản (COLD_CHAIN: +2 to +8°C, DEEP_FROZEN, CONTROLLED_ROOM_TEMP)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán Nhiệt độ Động học Trung bình (Arrhenius MKT) theo chuẩn Dược điển USP <1079>."""
    temp_list = [float(x.strip()) for x in temps.split(",") if x.strip()]
    try:
        class_enum = PharmaStorageClass[storage_class.upper()]
    except KeyError:
        class_enum = PharmaStorageClass.COLD_CHAIN

    res = ColdChainPharmaGDPEngine.calculate_mkt(
        batch_id=batch_id,
        temperatures_celsius=temp_list,
        storage_class=class_enum,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="❄️ PHÂN TÍCH NHIỆT ĐỘ ĐỘNG HỌC MKT (USP <1079> & TT 02/2018)", box=box.ROUNDED)
    table.add_column("Thông số", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")

    table.add_row("Mã số Lô hàng", res.batch_id)
    table.add_row("Số lượng mẫu đo", f"{res.sample_count} điểm")
    table.add_row("Nhiệt độ Thấp nhất / Cao nhất", f"{res.min_temp_c:.1f}°C / {res.max_temp_c:.1f}°C")
    table.add_row("Trung bình số học (Arithmetic)", f"{res.arithmetic_mean_c:.2f}°C")
    table.add_row("Năng lượng kích hoạt (Arrhenius ΔH)", f"{res.activation_energy_kj_mol} kJ/mol")
    table.add_section()
    table.add_row("[bold cyan]Nhiệt độ Động học (MKT)[/bold cyan]", f"[bold cyan]{res.mkt_celsius:.2f}°C[/bold cyan]")
    table.add_row("Quyết định Đảm bảo Chất lượng", f"[bold]{res.disposition.value}[/bold]")

    console.print(table)


@tradefinance_app.command("coldchain")
def tradefinance_coldchain(
    shipment_id: str = typer.Option("SHP-COLD-8812", "--id", help="Mã lô hàng vận tải lạnh"),
    transit_hours: float = typer.Option(48.0, "--transit-hours", help="Tổng thời gian vận chuyển (giờ)"),
    excursion_hours: float = typer.Option(0.0, "--excursion-hours", help="Tổng số giờ nhiệt độ vượt ngưỡng cho phép"),
    peak_temp: float = typer.Option(6.5, "--peak-temp", help="Nhiệt độ đỉnh cao nhất ghi nhận (°C)"),
    min_temp: float = typer.Option(2.5, "--min-temp", help="Nhiệt độ thấp nhất ghi nhận (°C)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá toàn vẹn chuỗi lạnh Dược phẩm và lệnh Biệt trữ theo Thông tư 02/2018/TT-BYT."""
    events: List[TemperatureExcursionEvent] = []
    if excursion_hours > 0:
        delta = max(0.0, peak_temp - 8.0)
        events.append(
            TemperatureExcursionEvent(
                start_time_iso="2026-10-05T12:00:00",
                duration_hours=excursion_hours,
                peak_temp_c=peak_temp,
                delta_over_limit_c=delta,
            )
        )
    if min_temp < 0.0:
        events.append(
            TemperatureExcursionEvent(
                start_time_iso="2026-10-05T18:00:00",
                duration_hours=1.0,
                peak_temp_c=min_temp,
                delta_over_limit_c=abs(min_temp),
            )
        )

    res = ColdChainPharmaGDPEngine.assess_cold_chain_excursions(
        shipment_id=shipment_id,
        storage_class=PharmaStorageClass.COLD_CHAIN,
        total_transit_hours=transit_hours,
        excursion_events=events,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="🏥 GIÁM SÁT CHUỖI LẠNH GDP DƯỢC PHẨM (TT 02/2018/TT-BYT)", box=box.ROUNDED)
    table.add_column("Chỉ số Đánh giá", style="cyan")
    table.add_column("Kết quả", style="magenta", justify="right")

    table.add_row("Mã Chuyến hàng", res.shipment_id)
    table.add_row("Thời gian Vận chuyển", f"{res.total_transit_hours:.1f} giờ")
    table.add_row("Thời gian Vượt ngưỡng", f"{res.cumulative_excursion_hours:.1f} giờ")
    table.add_row("Tải nhiệt tích lũy (Degree-Hours)", f"{res.severity_degree_hours:.1f} °C·h")
    table.add_row("Sự cố đông đá (Freeze Breach < 0°C)", "[bold red]CÓ BIẾN CỐ[/bold red]" if res.freeze_violation else "[bold green]KHÔNG[/bold green]")
    table.add_section()
    table.add_row("Trạng thái Xuất xưởng", f"[bold]{res.disposition.value}[/bold]")

    console.print(table)
    if res.quarantine_hold_rationale:
        console.print(Panel(f"[bold red]CĂN CỨ BIỆT TRỮ / ĐIỀU TRA:[/bold red] {res.quarantine_hold_rationale}", border_style="red"))
