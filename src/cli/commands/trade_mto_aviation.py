# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Multimodal Transport (MTO, Phase 163) & Civil Aviation (Phase 164) CLI subcommands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.trade_transport_engine import (
    AirCarrierLiabilityEngine,
    MultimodalTransportEngine,
)

console = Console()


def calc_mto_liability(
    loss: float = typer.Argument(..., help="Giá trị tổn thất thực tế yêu cầu bồi thường (VNĐ)"),
    packages: int = typer.Option(1, "--packages", "-p", help="Số lượng kiện/bao bì hàng hóa"),
    weight: float = typer.Option(100.0, "--weight", "-w", help="Tổng trọng lượng cả bì (kg)"),
    sea_leg: bool = typer.Option(True, "--sea/--no-sea", help="Có chặng đường biển hoặc đường thủy nội địa"),
    sdr_rate: float = typer.Option(34_500.0, "--sdr-rate", help="Tỷ giá quy đổi VND/SDR"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính giới hạn trách nhiệm bồi thường của Người kinh doanh vận tải đa phương thức (Điều 24 NĐ 87/2009/NĐ-CP)."""
    result = MultimodalTransportEngine.calculate_unlocalized_loss_liability(
        packages_count=packages,
        gross_weight_kg=weight,
        actual_loss_vnd=loss,
        has_sea_or_waterway_leg=sea_leg,
        sdr_rate_vnd=sdr_rate,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Bồi Thường Vận Tải Đa Phương Thức (MTO)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")
    table.add_row("Thiệt hại thực tế yêu cầu", f"{result.actual_loss_vnd:,.0f} VNĐ")
    table.add_row("Số kiện / Trọng lượng", f"{result.packages_count} kiện / {result.gross_weight_kg:,.1f} kg")
    table.add_row("Chặng biển/thủy nội địa", "Có" if result.has_sea_or_waterway_leg else "Không (Chỉ đường bộ/sắt)")
    table.add_row("Mức trần luật định (SDR)", f"{result.statutory_ceiling_sdr:,.2f} SDR")
    table.add_row("Mức trần luật định (VNĐ)", f"{result.statutory_ceiling_vnd:,.0f} VNĐ")
    table.add_row("[bold green]Số tiền MTO phải bồi thường[/]", f"[bold green]{result.operator_payable_vnd:,.0f} VNĐ[/]")
    table.add_row("Áp dụng mức trần giới hạn", "[bold red]Có[/]" if result.is_limited else "[green]Không (Bồi thường đủ)[/]")
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


def calc_mto_delay(
    freight: float = typer.Argument(..., help="Tiền cước vận chuyển của số hàng giao chậm (VNĐ)"),
    loss: float = typer.Argument(..., help="Tổn thất thực tế do giao hàng chậm phát sinh (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính bồi thường do chậm giao hàng trong vận tải đa phương thức (Khoản 3 Điều 24 NĐ 87/2009/NĐ-CP)."""
    result = MultimodalTransportEngine.calculate_delay_liability(
        freight_charge_vnd=freight,
        delay_loss_claimed_vnd=loss,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Bồi Thường Chậm Giao Hàng (MTO)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")
    table.add_row("Tiền cước vận chuyển", f"{result.freight_charge_vnd:,.0f} VNĐ")
    table.add_row("Thiệt hại phát sinh yêu cầu", f"{result.delay_loss_claimed_vnd:,.0f} VNĐ")
    table.add_row("Trần tối đa luật định (2x cước)", f"{result.statutory_ceiling_vnd:,.0f} VNĐ")
    table.add_row("[bold green]Số tiền bồi thường phải trả[/]", f"[bold green]{result.payable_compensation_vnd:,.0f} VNĐ[/]")
    table.add_row("Bị khống chế trần 2 lần cước", "[bold red]Có[/]" if result.is_capped_at_double_freight else "[green]Không[/]")
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


def check_mto_limitation(
    delivery_date: str = typer.Argument(..., help="Ngày giao hàng hoặc ngày lẽ ra phải giao hàng (YYYY-MM-DD)"),
    filing_date: Optional[str] = typer.Option(None, "--filing-date", "-f", help="Ngày nộp đơn khiếu nại/khởi kiện (mặc định hôm nay)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra thời hiệu khởi kiện 09 tháng vận tải đa phương thức (Điều 29 NĐ 87/2009/NĐ-CP)."""
    status = MultimodalTransportEngine.check_claim_limitation(
        delivery_date_str=delivery_date,
        filing_date_str=filing_date,
    )
    if json_mode:
        typer.echo(json.dumps(status.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold green]TRONG THỜI HIỆU[/bold green]" if status.is_within_9_months else "[bold red]HẾT THỜI HIỆU KHỞI KIỆN[/bold red]"
    console.print(
        Panel.fit(
            f"[bold]Tình trạng:[/] {badge}\n"
            f"[bold]Ngày giao hàng:[/] {status.delivery_date} | [bold]Ngày khởi kiện:[/] {status.filing_date}\n"
            f"[bold]Số ngày đã trôi qua:[/] {status.days_passed} / 270 ngày (09 tháng)\n"
            f"[bold]Thời gian còn lại:[/] {status.remaining_days} ngày\n"
            f"[bold]Đánh giá:[/] {status.advice_vn}",
            title="[bold cyan]Thời Hiệu Khởi Kiện Vận Tải Đa Phương Thức[/bold cyan]",
            border_style="green" if status.is_within_9_months else "red",
        )
    )


def calc_aviation_injury(
    damage_amount: float = typer.Argument(..., help="Thiệt hại sức khỏe/tính mạng thực tế yêu cầu bồi thường (VNĐ)"),
    sdr_rate: float = typer.Option(34_500.0, "--sdr-rate", help="Tỷ giá quy đổi VND/SDR"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính bồi thường thiệt hại tính mạng, sức khỏe hành khách hàng không (Điều 160 Luật HKDD 2006 & Montreal 1999)."""
    result = AirCarrierLiabilityEngine.calculate_passenger_injury_liability(
        actual_damage_claimed_vnd=damage_amount,
        sdr_rate_vnd=sdr_rate,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Bồi Thường Tính Mạng / Sức Khỏe Hành Khách Hàng Không", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")
    table.add_row("Thiệt hại thực tế yêu cầu", f"{result.actual_damage_claimed_vnd:,.0f} VNĐ")
    table.add_row("Hạn mức Tầng 1 (Trách nhiệm nghiêm ngặt)", f"{result.tier1_strict_ceiling_sdr:,.0f} SDR ({result.tier1_strict_ceiling_vnd:,.0f} VNĐ)")
    table.add_row("[bold green]Khoản bồi thường vô điều kiện (Tầng 1)[/]", f"[bold green]{result.carrier_payable_strict_vnd:,.0f} VNĐ[/]")
    table.add_row("Vượt hạn mức Tầng 1 (Yêu cầu xét lỗi)", "[bold red]Có[/]" if result.requires_carrier_fault_for_excess else "[green]Không[/]")
    console.print(table)
    console.print(f"[bold cyan]Đánh giá:[/] {result.advice_vn}")
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


def calc_aviation_cargo(
    weight: float = typer.Argument(..., help="Tổng trọng lượng hàng hóa cả bì (kg)"),
    loss: float = typer.Argument(..., help="Giá trị hàng hóa thực tế bị mất mát/hư hỏng (VNĐ)"),
    sdr_rate: float = typer.Option(34_500.0, "--sdr-rate", help="Tỷ giá quy đổi VND/SDR"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính bồi thường mất mát, hư hại hàng hóa đường hàng không (Điều 166 Luật HKDD 2006 & Montreal 1999 - 22 SDR/kg)."""
    result = AirCarrierLiabilityEngine.calculate_cargo_liability(
        gross_weight_kg=weight,
        actual_loss_vnd=loss,
        sdr_rate_vnd=sdr_rate,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Bồi Thường Hàng Hóa Đường Hàng Không (Air Cargo)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")
    table.add_row("Trọng lượng hàng hóa", f"{result.gross_weight_kg:,.1f} kg")
    table.add_row("Thiệt hại thực tế yêu cầu", f"{result.actual_loss_vnd:,.0f} VNĐ")
    table.add_row("Giới hạn trách nhiệm (22 SDR/kg)", f"{result.cargo_limit_sdr:,.2f} SDR ({result.statutory_ceiling_vnd:,.0f} VNĐ)")
    table.add_row("[bold green]Số tiền hãng hàng không bồi thường[/]", f"[bold green]{result.carrier_payable_vnd:,.0f} VNĐ[/]")
    table.add_row("Áp dụng mức trần giới hạn", "[bold red]Có[/]" if result.is_limited else "[green]Không (Bồi thường toàn bộ)[/]")
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")
