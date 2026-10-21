"""Typer CLI Commands for Dangerous Cargo Terminal Handling, Tugboat Escort, Berthage & Channel Clearance.

Phases 231-234:
- Phase 231: mekong dangerouscargo validate / segregation
- Phase 232: mekong tugescort evaluate / reqs
- Phase 233: mekong berthmooring berthage / mooring
- Phase 234: mekong channelclearance ukc / airdraft / refusal
"""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.table import Table

from src.cli.commands.maritime_channel_clearance_commands import (
    calculate_air_draft,
    calculate_dynamic_ukc,
    channelclearance_app,
    evaluate_clearance_refusal,
)
from src.cli.commands.maritime_hazardous_tug_commands import (
    check_imdg_segregation,
    dangerouscargo_app,
    evaluate_tugboat_towage,
    tugescort_app,
    validate_dangerous_cargo,
)
from src.core.maritime_hazardous_tug_berth_clearance_engine import (
    BerthageAndMooringTariffEngine,
    BerthUsageMode,
    VesselTradeType,
)

console = Console()

berthmooring_app = typer.Typer(
    name="berthmooring",
    help="Tính phí cầu bến, phao neo & giá dịch vụ buộc/cởi dây tàu biển theo TT 39/2023 & TT 12/2024 (Phase 233).",
)


@berthmooring_app.command(name="berthage")
def calculate_berthage_fee(
    gt: float = typer.Option(25000.0, "--gt", help="Dung tích toàn phần của tàu (Gross Tonnage)"),
    hours: float = typer.Option(36.0, "--hours", "-h", help="Thời gian neo cập cầu bến (giờ)"),
    trade: str = typer.Option("international", "--trade", help="Loại tuyến: international hoặc domestic"),
    mode: str = typer.Option("cargo_operations", "--mode", "-m", help="Mục đích sử dụng: cargo_operations, waiting_or_repair, unauthorized_overstay"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán phí cầu bến theo Thông tư 39/2023/TT-BGTVT."""
    try:
        t_enum = VesselTradeType(trade)
        m_enum = BerthUsageMode(mode)
    except ValueError as e:
        console.print(f"[bold red]Lỗi tham số:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = BerthageAndMooringTariffEngine.calculate_berthage(gt, hours, t_enum, m_enum)

    if as_json:
        console.print(json.dumps({
            "vessel_gt": res.vessel_gt,
            "trade_type": res.trade_type.value,
            "usage_mode": res.usage_mode.value,
            "duration_hours": res.duration_hours,
            "gt_hours": res.gt_hours,
            "base_rate_per_gt_hour": res.base_rate_per_gt_hour,
            "currency": res.currency,
            "base_amount": res.base_amount,
            "overstay_penalty_amount": res.overstay_penalty_amount,
            "total_berthage_amount": res.total_berthage_amount,
        }, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Bảng Tính Phí Cầu Bến Cảng Biển (TT 39/2023 - GT: {gt:,})")
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị", style="white")
    table.add_row("Dung tích GT", f"{gt:,}")
    table.add_row("Thời gian neo đậu", f"{hours:.1f} giờ ({res.gt_hours:,.0f} GT-giờ)")
    table.add_row("Tuyến hành trình", trade.upper())
    table.add_row("Mục đích cập cầu", mode)
    table.add_row("Đơn giá", f"{res.base_rate_per_gt_hour} {res.currency}/GT-giờ")
    table.add_row("Phạt quá hạn (nếu có)", f"{res.overstay_penalty_amount:,.2f} {res.currency}")
    table.add_row("TỔNG TIỀN PHÍ CẦU BẾN", f"[bold green]{res.total_berthage_amount:,.2f} {res.currency}[/bold green]")

    console.print(table)


@berthmooring_app.command(name="mooring")
def calculate_mooring_service(
    gt: float = typer.Option(18000.0, "--gt", help="Dung tích toàn phần của tàu (Gross Tonnage)"),
    operations: int = typer.Option(2, "--ops", help="Số lượt tác nghiệp: 1 (chỉ buộc hoặc cởi), 2 (cả buộc và cởi dây)"),
    trade: str = typer.Option("international", "--trade", help="Loại tuyến: international hoặc domestic"),
    night: bool = typer.Option(False, "--night", help="Làm đêm (18h-06h, +40%)"),
    holiday: bool = typer.Option(False, "--holiday", help="Làm ngày lễ/tết (+100%)"),
    hazardous: bool = typer.Option(False, "--hazardous", help="Tàu chở hàng nguy hiểm (+25%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính giá dịch vụ buộc cởi dây tàu biển theo khung giá Thông tư 39/2023."""
    try:
        t_enum = VesselTradeType(trade)
    except ValueError as e:
        console.print(f"[bold red]Lỗi loại tuyến:[/bold red] {e}")
        raise typer.Exit(code=1)

    res = BerthageAndMooringTariffEngine.calculate_mooring_service(
        gross_tonnage=gt,
        operations_count=operations,
        trade_type=t_enum,
        is_night=night,
        is_holiday=holiday,
        has_hazardous_cargo=hazardous,
    )

    if as_json:
        console.print(json.dumps({
            "vessel_gt": res.vessel_gt,
            "tier_name": res.tier_name,
            "operations_count": res.operations_count,
            "base_tariff_per_turn": res.base_tariff_per_turn,
            "currency": res.currency,
            "required_line_handlers": res.required_line_handlers,
            "requires_launch_boat": res.requires_launch_boat,
            "night_surcharge_amount": res.night_surcharge_amount,
            "holiday_surcharge_amount": res.holiday_surcharge_amount,
            "hazardous_surcharge_amount": res.hazardous_surcharge_amount,
            "total_mooring_amount": res.total_mooring_amount,
        }, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Dịch Vụ Buộc/Cởi Dây Tàu Biển (GT: {gt:,})")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Chi tiết", style="white")
    table.add_row("Khung phân hạng", res.tier_name)
    table.add_row("Số công nhân bắt buộc", f"{res.required_line_handlers} người")
    table.add_row("Cano đưa dây", "BẮT BUỘC" if res.requires_launch_boat else "Không yêu cầu")
    table.add_row("Đơn giá cơ sở / lượt", f"{res.base_tariff_per_turn:,.2f} {res.currency}")
    table.add_row("Phụ phí ban đêm (+40%)", f"{res.night_surcharge_amount:,.2f} {res.currency}")
    table.add_row("Phụ phí ngày Lễ (+100%)", f"{res.holiday_surcharge_amount:,.2f} {res.currency}")
    table.add_row("Phụ phí hàng độc hại (+25%)", f"{res.hazardous_surcharge_amount:,.2f} {res.currency}")
    table.add_row("TỔNG CHI PHÍ BUỘC/CỞI DÂY", f"[bold green]{res.total_mooring_amount:,.2f} {res.currency}[/bold green]")

    console.print(table)


__all__ = [
    "berthmooring_app",
    "calculate_air_draft",
    "calculate_berthage_fee",
    "calculate_dynamic_ukc",
    "calculate_mooring_service",
    "channelclearance_app",
    "check_imdg_segregation",
    "console",
    "dangerouscargo_app",
    "evaluate_clearance_refusal",
    "evaluate_tugboat_towage",
    "tugescort_app",
    "validate_dangerous_cargo",
]
