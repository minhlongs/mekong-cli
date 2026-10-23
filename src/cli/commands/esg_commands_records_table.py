# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ESG suite record-table and status-panel construction."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table


def format_usd(amount: float) -> str:
    return f"${amount:,.2f}"


def format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")

_COLUMNS = (("Mã hồ sơ", "cyan"), ("Doanh nghiệp", "bold"), ("Năm", "white"), ("Scope 1 (t)", "yellow"), ("Scope 2 (t)", "yellow"), ("Tổng phát thải (tCO2e)", "bold red"), ("Bắt buộc MRV", ""))


def build_overview_panel(s: dict) -> Panel:
    """Build the ESG overview panel; the caller prints it."""
    m = s["metrics"]
    return Panel(
        f"[bold green]HỆ THỐNG QUẢN TRỊ ESG & GIAO DỊCH TÍN CHỈ CARBON QUỐC GIA[/]\n\n"
        f"  Khung pháp lý: [bold]{s['regulatory_framework']}[/] | Quy chuẩn: [bold cyan]{s['standards']}[/]\n"
        f"  Hồ sơ kiểm kê KNK: [bold]{m['total_ghg_inventories']} doanh nghiệp[/] (Tổng phát thải: [bold yellow]{m['total_emissions_tracked_tco2e']:,.2f} tCO2e[/])\n"
        f"  Giao dịch tín chỉ carbon: [bold]{m['total_carbon_transactions']} lệnh[/] (Khối lượng: [bold green]{m['total_credits_traded_tco2e']:,.1f} tCO2e[/] ~ {format_usd(m['total_credits_value_usd'])})\n"
        f"  Đánh giá xếp hạng ESG: [bold]{m['total_esg_ratings']} doanh nghiệp[/] (Điểm trung bình: [bold cyan]{m['average_esg_composite_score']}/100[/])",
        title="[bold blue]National ESG & Carbon Market Dashboard[/]", border_style="green",
    )


def build_status_panel(res: dict) -> Panel:
    """Build the ESG telemetry status panel; the caller prints it."""
    m = res["metrics"]
    return Panel(
        f"[bold green]TRẠNG THÁI HỆ THỐNG ESG & THỊ TRƯỜNG CARBON[/]\n\n"
        f"  Tổng hồ sơ kiểm kê: [bold]{m['total_ghg_inventories']}[/] DN | Tổng phát thải KNK: [bold yellow]{m['total_emissions_tracked_tco2e']:,.2f} tCO2e[/]\n"
        f"  Tín chỉ carbon khớp: [bold green]{m['total_credits_traded_tco2e']:,.1f} tCO2e[/] (~ {format_usd(m['total_credits_value_usd'])})\n"
        f"  Xếp hạng tín nhiệm ESG: [bold]{m['total_esg_ratings']}[/] DN (TB: [bold cyan]{m['average_esg_composite_score']}/100[/]) | DB: {res['database']}",
        title="[bold blue]ESG Engine Telemetry[/]", border_style="green",
    )


def build_inventory_table(inventories: list[dict]) -> Table:
    """Build the GHG inventory table; the caller prints it."""
    table = Table(title="Danh Sách Kiểm Kê Khí Nhà Kính (GHG Inventories)", border_style="cyan")
    for header, style in _COLUMNS:
        table.add_column(header, style=style)
    for inv in inventories:
        table.add_row(inv["inventory_id"], inv["enterprise_name"], str(inv["reporting_year"]), f"{inv['scope1_tco2e']:,.1f}", f"{inv['scope2_tco2e']:,.1f}", f"{inv['total_tco2e']:,.1f}", "BẮT BUỘC" if inv["is_mandatory_reporting"] else "Tự nguyện")
    return table
