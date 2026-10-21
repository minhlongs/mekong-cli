# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 182: Multimodal Freight Carbon Accounting & Scope 3 Decarbonization CLI."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._port_terminal_cmds import console
from src.cli.commands._tradefinance_lc_cmds import tradefinance_app
from src.core.port_supply_chain_engine import (
    FreightCarbonAccountingEngine,
    FreightTransportMode,
)


@tradefinance_app.command("carbon")
def tradefinance_carbon(
    route_id: str = typer.Option("RT-SGN-HPH", "--route", help="Mã lộ trình vận tải"),
    weight_tonnes: float = typer.Option(24.0, "--weight", "-w", help="Khối lượng hàng hóa (tấn)"),
    ocean_km: float = typer.Option(1500.0, "--ocean-km", help="Khoảng cách tàu biển container (km)"),
    barge_km: float = typer.Option(120.0, "--barge-km", help="Khoảng cách xà lan thủy nội địa (km)"),
    truck_km: float = typer.Option(60.0, "--truck-km", help="Khoảng cách xe đầu kéo container (km)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm kê phát thải KNK vận tải đa phương thức theo chuẩn ISO 14083 / GLEC v3.0."""
    legs = []
    if ocean_km > 0:
        legs.append(("Chặng Đường biển Feeder", FreightTransportMode.FEEDER_VESSEL, ocean_km))
    if barge_km > 0:
        legs.append(("Chặng Xà lan Mekong", FreightTransportMode.INLAND_WATERWAY_BARGE, barge_km))
    if truck_km > 0:
        legs.append(("Chặng Xe tải Kéo Cảng", FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4, truck_km))

    res = FreightCarbonAccountingEngine.calculate_multimodal_emissions(
        route_id=route_id,
        cargo_weight_tonnes=weight_tonnes,
        legs_data=legs,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="🌱 KIỂM KÊ KHÍ NHÀ KÍNH VẬN TẢI (ISO 14083 & GLEC v3.0)", box=box.ROUNDED)
    table.add_column("Chặng Vận tải / Phương thức", style="cyan")
    table.add_column("Cự ly", style="yellow", justify="right")
    table.add_column("Phát thải CO2e", style="magenta", justify="right")

    for leg in res.legs:
        table.add_row(f"{leg.leg_name} ({leg.mode.value})", f"{leg.distance_km:.1f} km", f"{leg.emissions_kg_co2e:,.1f} kg")

    table.add_section()
    table.add_row("[bold green]TỔNG PHÁT THẢI (WTW)[/bold green]", f"{res.total_distance_km:.1f} km", f"[bold green]{res.total_emissions_t_co2e:.3f} tCO2e[/bold green]")
    table.add_row("Cường độ Carbon Trung bình", "", f"{res.average_intensity_g_per_tkm:.1f} gCO2e/t·km")
    table.add_row("Chi phí Bù trừ Tín chỉ (NĐ 06/2022)", "", f"{res.offset_cost_vnd:,.0f} VND")

    console.print(table)


@tradefinance_app.command("modal-shift")
def tradefinance_modal_shift(
    origin: str = typer.Option("Bình Dương", "--from", help="Điểm xuất phát"),
    destination: str = typer.Option("Cái Mép", "--to", help="Điểm đến"),
    weight_tonnes: float = typer.Option(100.0, "--weight", "-w", help="Khối lượng hàng hóa (tấn)"),
    road_km: float = typer.Option(95.0, "--road-km", help="Cự ly đường bộ toàn tuyến (km)"),
    barge_km: float = typer.Option(85.0, "--barge-km", help="Cự ly xà lan đường thủy (km)"),
    drayage_km: float = typer.Option(15.0, "--drayage-km", help="Cự ly trung chuyển đầu cuối (km)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tối ưu hóa chuyển đổi xanh: Đánh giá tỷ lệ giảm CO2e khi chuyển từ Đường bộ sang Xà lan."""
    intermodal_legs = [
        ("Trung chuyển đường bộ", FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4, drayage_km),
        ("Vận chuyển xà lan", FreightTransportMode.INLAND_WATERWAY_BARGE, barge_km),
    ]

    res = FreightCarbonAccountingEngine.evaluate_modal_shift(
        origin=origin,
        destination=destination,
        cargo_weight_tonnes=weight_tonnes,
        road_distance_km=road_km,
        intermodal_legs=intermodal_legs,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="🔄 TỐI ƯU HÓA CHUYỂN ĐỔI PHƯƠNG THỨC XANH (MODAL SHIFT)", box=box.ROUNDED)
    table.add_column("Phương thức So sánh", style="cyan")
    table.add_column("Phát thải / Chuyến", style="magenta", justify="right")

    table.add_row("Đường bộ Thuần túy (Truck Baseline)", f"{res.baseline_road_emissions_t_co2e:.3f} tCO2e")
    table.add_row("Đa phương thức (Đường bộ + Xà lan)", f"{res.intermodal_emissions_t_co2e:.3f} tCO2e")
    table.add_section()
    table.add_row("[bold green]Lượng Giảm Phát thải[/bold green]", f"[bold green]{res.emissions_saved_t_co2e:.3f} tCO2e ({res.reduction_percentage:.1f}%)[/bold green]")
    table.add_row("Tiết kiệm Chi phí Tín chỉ Carbon/năm", f"{res.annual_cost_savings_offset_vnd:,.0f} VND")

    console.print(table)
    console.print(Panel(f"[bold green]KHUYẾN NGHỊ DECARBONIZATION:[/bold green] {res.green_recommendation}", border_style="green"))
