# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 240: Cold Ironing (Onshore Power Supply) CLI commands."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_vts_coldironing_ghg_bunkering_engine import ColdIroningEngine

console = Console()

coldironing_app = typer.Typer(
    name="coldironing",
    help="Cấp điện bờ Onshore Power Supply (OPS/Cold Ironing), giảm phát thải & chi phí (Phase 240).",
)


@coldironing_app.command(name="energy")
def cold_ironing_energy_cmd(
    power_mw: float = typer.Option(
        2.5, "--power", "-p", help="Công suất phụ tải tàu tại bến (MW)"
    ),
    hours: float = typer.Option(
        24.0, "--hours", "-h", help="Thời gian neo đậu cấp điện tại cầu cảng (giờ)"
    ),
    grid_hz: int = typer.Option(50, "--grid-hz", help="Tần số lưới điện bờ (50 Hz tại VN)"),
    ship_hz: int = typer.Option(
        60, "--ship-hz", help="Tần số điện lưới trên tàu (60 Hz tiêu chuẩn)"
    ),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Tính toán lượng điện năng cấp từ bờ và tổn hao chuyển đổi tần số Static Frequency Converter."""
    res = ColdIroningEngine.calculate_energy(
        hotel_power_mw=power_mw,
        berth_duration_hours=hours,
        grid_frequency_hz=grid_hz,
        ship_frequency_hz=ship_hz,
    )
    data = {
        "hotel_power_mw": res.hotel_power_mw,
        "berth_duration_hours": res.berth_duration_hours,
        "total_energy_mwh": res.total_energy_mwh,
        "grid_frequency_hz": res.grid_frequency_hz,
        "ship_frequency_hz": res.ship_frequency_hz,
        "converter_loss_mwh": res.converter_loss_mwh,
        "net_billed_mwh": res.net_billed_mwh,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Tính Toán Điện Năng Cấp Bờ (Cold Ironing / OPS)")
    table.add_column("Thông số", style="cyan")
    table.add_column("Kết quả", style="green")
    table.add_row("Công suất phụ tải tại bến", f"{res.hotel_power_mw} MW")
    table.add_row("Thời gian cấp điện", f"{res.berth_duration_hours} giờ")
    table.add_row("Tổng năng lượng tiêu thụ", f"{res.total_energy_mwh:.3f} MWh")
    table.add_row(
        "Chuyển đổi tần số", f"{res.grid_frequency_hz} Hz → {res.ship_frequency_hz} Hz"
    )
    table.add_row("Tổn hao bộ biến tần (SFC Loss)", f"{res.converter_loss_mwh:.3f} MWh")
    table.add_row("Điện năng thanh toán ghi nhận", f"{res.net_billed_mwh:.3f} MWh")
    console.print(table)


@coldironing_app.command(name="emissions")
def cold_ironing_emissions_cmd(
    mwh: float = typer.Option(
        60.0, "--mwh", help="Tổng năng lượng phụ tải tiêu thụ tại bến (MWh)"
    ),
    billed_mwh: float = typer.Option(
        61.8, "--billed-mwh", help="Năng lượng thanh toán từ lưới điện (MWh)"
    ),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Tính toán lượng khí thải cắt giảm (CO2, SOx, NOx, PM2.5) so với chạy máy phát diesel MGO."""
    res = ColdIroningEngine.calculate_emissions_avoided(
        total_energy_mwh=mwh,
        net_billed_mwh=billed_mwh,
    )
    data = {
        "baseline_mgo_tonnes": res.baseline_mgo_tonnes,
        "mgo_co2_tonnes": res.mgo_co2_tonnes,
        "grid_co2_tonnes": res.grid_co2_tonnes,
        "net_co2_avoided_tonnes": res.net_co2_avoided_tonnes,
        "sox_avoided_tonnes": res.sox_avoided_tonnes,
        "nox_avoided_tonnes": res.nox_avoided_tonnes,
        "pm25_avoided_tonnes": res.pm25_avoided_tonnes,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đo Lường Cắt Giảm Phát Thải Cảng Xanh (Cold Ironing)")
    table.add_column("Chỉ số phát thải", style="cyan")
    table.add_column("Giá trị cắt giảm", style="green")
    table.add_row("Dầu MGO tránh phải đốt", f"{res.baseline_mgo_tonnes:.4f} tấn")
    table.add_row("CO2 phát thải cơ sở từ MGO", f"{res.mgo_co2_tonnes:.3f} tấn CO2")
    table.add_row("CO2 phát thải từ điện lưới", f"{res.grid_co2_tonnes:.3f} tấn CO2")
    table.add_row("NET CO2 CẮT GIẢM RÒNG", f"{res.net_co2_avoided_tonnes:.3f} tấn CO2")
    table.add_row("SOx cắt giảm tránh được", f"{res.sox_avoided_tonnes:.4f} tấn SOx")
    table.add_row("NOx cắt giảm tránh được", f"{res.nox_avoided_tonnes:.4f} tấn NOx")
    table.add_row("Bụi mịn PM2.5 cắt giảm", f"{res.pm25_avoided_tonnes:.4f} tấn PM2.5")
    console.print(table)


@coldironing_app.command(name="cost")
def cold_ironing_cost_cmd(
    billed_mwh: float = typer.Option(
        40.0, "--billed-mwh", help="Năng lượng thanh toán từ lưới điện (MWh)"
    ),
    mgo_tonnes: float = typer.Option(
        8.6, "--mgo-tonnes", help="Lượng dầu MGO cơ sở thay thế (tấn)"
    ),
    elec_price: float = typer.Option(
        3200.0, "--elec-price", help="Giá điện bán lẻ cho cảng (VND/kWh)"
    ),
    infra_fee: float = typer.Option(
        2000000.0, "--infra-fee", help="Phí hạ tầng cấp điện cầu cảng (VND)"
    ),
    mgo_price: float = typer.Option(
        850.0, "--mgo-price", help="Giá dầu MGO quốc tế (USD/tấn)"
    ),
    fx: float = typer.Option(25400.0, "--fx", help="Tỷ giá quy đổi USD/VND"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Đánh giá hiệu quả kinh tế: so sánh chi phí cấp điện bờ và chi phí nhiên liệu diesel MGO."""
    res = ColdIroningEngine.evaluate_cost_savings(
        net_billed_mwh=billed_mwh,
        baseline_mgo_tonnes=mgo_tonnes,
        electricity_price_per_kwh_vnd=elec_price,
        green_infra_fee_vnd=infra_fee,
        mgo_price_per_tonne_usd=mgo_price,
        fx_usd_vnd=fx,
    )
    data = {
        "electricity_cost": res.electricity_cost,
        "green_berth_infrastructure_fee": res.green_berth_infrastructure_fee,
        "total_shore_power_cost": res.total_shore_power_cost,
        "mgo_fuel_saved_cost": res.mgo_fuel_saved_cost,
        "net_financial_savings": res.net_financial_savings,
        "currency": res.currency,
        "audit_hash": res.audit_hash,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đánh Giá Hiệu Quả Kinh Tế Điện Bờ (Cold Ironing)")
    table.add_column("Chỉ tiêu tài chính", style="cyan")
    table.add_column("Giá trị", style="green")
    table.add_row("Tiền điện tiêu thụ", f"{res.electricity_cost:,.2f} {res.currency}")
    table.add_row(
        "Phí hạ tầng cầu cảng xanh",
        f"{res.green_berth_infrastructure_fee:,.2f} {res.currency}",
    )
    table.add_row(
        "Tổng chi phí cấp điện bờ",
        f"{res.total_shore_power_cost:,.2f} {res.currency}",
    )
    table.add_row(
        "Chi phí dầu MGO tiết kiệm", f"{res.mgo_fuel_saved_cost:,.2f} {res.currency}"
    )
    table.add_row(
        "TIẾT KIỆM TÀI CHÍNH RÒNG", f"{res.net_financial_savings:,.2f} {res.currency}"
    )
    table.add_row("Mã xác thực Audit Hash", f"{res.audit_hash}")
    console.print(table)
