"""
CLI Commands for Mekong International Trade, Transport & Trade Remedies Suite (Phases 163 - 166).

Covers:
1. Multimodal Transport (MTO) Liability & Limitations (Phase 163)
2. Civil Aviation Carrier Compensation & Montreal 1999 (Phase 164)
3. CISG 1980 Sales Contract Remedies & Incoterms 2020 (Phase 165)
4. Vietnamese Trade Remedies, Anti-Dumping & Safeguards (Phase 166)
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.core.trade_transport_engine import (
    MultimodalTransportEngine,
    AirCarrierLiabilityEngine,
    InternationalSalesIncotermsEngine,
    TradeRemediesEngine,
)

trade_app = typer.Typer(
    name="trade",
    help="Hệ thống Vận tải đa phương thức, Hàng không dân dụng, Hợp đồng CISG 1980, Incoterms 2020 & Phòng vệ thương mại (Phases 163 - 166).",
)
console = Console()


@trade_app.callback(invoke_without_command=True)
def trade_summary(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới dạng JSON"),
) -> None:
    """Tổng quan bộ giải pháp Mekong International Trade, Transport & Trade Remedies Suite."""
    if ctx.invoked_subcommand is not None:
        return

    data = {
        "suite": "Mekong Trade, Transport & Remedies Suite",
        "phases": ["163", "164", "165", "166"],
        "modules": {
            "mto": "Multimodal Transport Operator Liability (NĐ 87/2009/NĐ-CP & NĐ 144/2018/NĐ-CP)",
            "aviation": "Civil Aviation Carrier Liability (Luật HKDD 2006/2014 & Montreal Convention 1999)",
            "cisg_incoterms": "CISG 1980 International Sales of Goods & Incoterms 2020 Rules",
            "trade_remedies": "Trade Remedies, Anti-Dumping & Safeguards (Luật QLNT 2017 & NĐ 10/2018/NĐ-CP)",
        },
        "status": "active",
    }

    if json_mode:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            "[bold cyan]MEKONG TRADE, TRANSPORT & TRADE REMEDIES SUITE[/bold cyan]\n"
            "[italic dim]Căn cứ: NĐ 87/2009, Luật HKDD 2006, Montreal 1999, CISG 1980, Incoterms 2020 & Luật QLNT 2017[/italic dim]\n\n"
            "  [bold yellow]1. Vận tải đa phương thức:[/]  Trần 666.67 SDR/kiện & 2.0 SDR/kg, trần chậm giao 2x cước, thời hiệu 9 tháng\n"
            "  [bold yellow]2. Hàng không dân dụng:[/]    Trách nhiệm nghiêm ngặt 128,821 SDR, 22 SDR/kg hàng hóa, thời hiệu 2 năm\n"
            "  [bold yellow]3. CISG & Incoterms 2020:[/]  Vi phạm cơ bản Điều 25, Giảm giá hàng Điều 50, 11 quy tắc Incoterms (CIP/CIF)\n"
            "  [bold yellow]4. Phòng vệ thương mại:[/]    Biên độ phá giá (De Minimis 2.0%), thị phần < 3.0%, gia tăng nhập khẩu tự vệ",
            title="[bold green]Phases 163 - 166 Overview[/bold green]",
            border_style="cyan",
        )
    )


# ============================================================================
# 1. MULTIMODAL TRANSPORT (MTO) SUBCOMMANDS (PHASE 163)
# ============================================================================

@trade_app.command("mto-liability")
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


@trade_app.command("mto-delay")
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


@trade_app.command("mto-limitation")
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


# ============================================================================
# 2. CIVIL AVIATION CARRIER LIABILITY (PHASE 164)
# ============================================================================

@trade_app.command("aviation-injury")
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


@trade_app.command("aviation-cargo")
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


@trade_app.command("aviation-baggage")
def calc_aviation_baggage(
    loss: float = typer.Argument(..., help="Tổn thất thực tế phát sinh (VNĐ)"),
    passengers: int = typer.Option(1, "--passengers", "-p", help="Số lượng hành khách bị ảnh hưởng"),
    claim_type: str = typer.Option("baggage", "--type", "-t", help="Loại khiếu nại: 'baggage' (Hành lý 1,288 SDR) hoặc 'delay' (Chậm chuyến 5,346 SDR)"),
    sdr_rate: float = typer.Option(34_500.0, "--sdr-rate", help="Tỷ giá quy đổi VND/SDR"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính bồi thường hành lý hoặc chậm chuyến bay (Điều 162, 166 Luật HKDD & Montreal 1999)."""
    result = AirCarrierLiabilityEngine.calculate_baggage_or_delay_liability(
        claim_type=claim_type,
        passengers_count=passengers,
        actual_loss_vnd=loss,
        sdr_rate_vnd=sdr_rate,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    title_label = "Hành Lý (Baggage)" if claim_type.lower() == "baggage" else "Chậm Chuyến (Flight Delay)"
    table = Table(title=f"Bồi Thường Hàng Không: {title_label}", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")

    table.add_row("Số hành khách", f"{result.passengers_count} người")
    table.add_row("Thiệt hại thực tế yêu cầu", f"{result.actual_loss_vnd:,.0f} VNĐ")
    table.add_row("Mức trần luật định (SDR)", f"{result.statutory_limit_sdr:,.2f} SDR")
    table.add_row("Mức trần luật định (VNĐ)", f"{result.statutory_ceiling_vnd:,.0f} VNĐ")
    table.add_row("[bold green]Số tiền hãng hàng không bồi thường[/]", f"[bold green]{result.carrier_payable_vnd:,.0f} VNĐ[/]")
    table.add_row("Áp dụng mức trần giới hạn", "[bold red]Có[/]" if result.is_limited else "[green]Không[/]")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


@trade_app.command("aviation-limitation")
def check_aviation_limitation(
    arrival_date: str = typer.Argument(..., help="Ngày máy bay đến nơi hoặc ngày lẽ ra phải đến (YYYY-MM-DD)"),
    action_date: Optional[str] = typer.Option(None, "--action-date", "-a", help="Ngày khởi kiện (mặc định hôm nay)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra thời hiệu khởi kiện 02 năm hàng không dân dụng (Điều 173 Luật HKDD 2006)."""
    status = AirCarrierLiabilityEngine.check_aviation_claim_limitation(
        arrival_date_str=arrival_date,
        action_date_str=action_date,
    )

    if json_mode:
        typer.echo(json.dumps(status.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold green]TRONG THỜI HIỆU[/bold green]" if status.is_within_2_years else "[bold red]HẾT THỜI HIỆU KHỞI KIỆN[/bold red]"
    console.print(
        Panel.fit(
            f"[bold]Tình trạng:[/] {badge}\n"
            f"[bold]Ngày đến nơi:[/] {status.arrival_date} | [bold]Ngày khởi kiện:[/] {status.action_date}\n"
            f"[bold]Số ngày đã trôi qua:[/] {status.days_passed} / 730 ngày (02 năm)\n"
            f"[bold]Thời gian còn lại:[/] {status.remaining_days} ngày\n"
            f"[bold]Đánh giá:[/] {status.advice_vn}",
            title="[bold cyan]Thời Hiệu Khởi Kiện Hàng Không Dân Dụng[/bold cyan]",
            border_style="green" if status.is_within_2_years else "red",
        )
    )


# ============================================================================
# 3. CISG 1980 & INCOTERMS 2020 SUBCOMMANDS (PHASE 165)
# ============================================================================

@trade_app.command("cisg-breach")
def evaluate_cisg_breach(
    deprived: bool = typer.Option(True, "--deprived/--not-deprived", help="Vi phạm tước bỏ đáng kể lợi ích kỳ vọng theo hợp đồng"),
    foreseeable: bool = typer.Option(True, "--foreseeable/--unforeseeable", help="Bên vi phạm có thể lường trước được hậu quả"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá Vi phạm cơ bản hợp đồng & Quyền hủy hợp đồng theo Điều 25 Công ước Viên 1980 (CISG)."""
    result = InternationalSalesIncotermsEngine.evaluate_fundamental_breach(
        substantially_deprives_expectation=deprived,
        was_foreseeable=foreseeable,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold red]VI PHẠM CƠ BẢN (FUNDAMENTAL BREACH)[/bold red]" if result.is_fundamental_breach else "[bold green]VI PHẠM THÔNG THƯỜNG[/bold green]"
    avoidance_badge = "[bold red]ĐƯỢC QUYỀN HỦY HỢP ĐỒNG (AVOIDANCE)[/bold red]" if result.entitled_to_avoid_contract else "[yellow]KHÔNG ĐƯỢC HỦY HỢP ĐỒNG[/yellow]"

    console.print(
        Panel.fit(
            f"[bold]Kết luận:[/] {badge}\n"
            f"[bold]Quyền hủy hợp đồng (Art. 49/64):[/] {avoidance_badge}\n"
            f"[bold]Tước bỏ lợi ích kỳ vọng:[/] {'Có' if result.substantially_deprives_expectation else 'Không'}\n"
            f"[bold]Có thể lường trước:[/] {'Có' if result.was_foreseeable_by_breaching_party else 'Không'}\n\n"
            f"[bold cyan]Hướng dẫn xử lý:[/] {result.advice_vn}\n"
            f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]",
            title="[bold cyan]Đánh Giá Vi Phạm Cơ Bản (CISG 1980)[/bold cyan]",
            border_style="red" if result.is_fundamental_breach else "green",
        )
    )


@trade_app.command("cisg-reduction")
def calc_cisg_reduction(
    price: float = typer.Argument(..., help="Giá trị thỏa thuận trong hợp đồng (VNĐ)"),
    delivered_val: float = typer.Argument(..., help="Giá trị thực tế của hàng hóa được giao tại thời điểm giao hàng (VNĐ)"),
    conforming_val: float = typer.Argument(..., help="Giá trị hàng hóa nếu đúng hợp đồng (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính giảm giá hàng khi hàng không phù hợp hợp đồng theo Điều 50 Công ước Viên 1980 (CISG)."""
    result = InternationalSalesIncotermsEngine.calculate_cisg_price_reduction(
        agreed_contract_price_vnd=price,
        value_of_delivered_goods_vnd=delivered_val,
        value_if_conforming_vnd=conforming_val,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Giảm Giá Hàng Hóa Không Phù Hợp (Điều 50 CISG)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")

    table.add_row("Giá trị hợp đồng ban đầu", f"{result.agreed_contract_price_vnd:,.0f} VNĐ")
    table.add_row("Giá trị hàng thực giao", f"{result.value_of_delivered_goods_vnd:,.0f} VNĐ")
    table.add_row("Giá trị hàng nếu đúng chuẩn", f"{result.value_if_conforming_vnd:,.0f} VNĐ")
    table.add_row("Tỷ lệ giá trị thực/chuẩn", f"{result.reduction_ratio_pct:.2f}%")
    table.add_row("[bold green]Giá mới bên mua phải trả[/]", f"[bold green]{result.reduced_price_payable_vnd:,.0f} VNĐ[/]")
    table.add_row("[bold red]Số tiền được giảm trừ[/]", f"[bold red]{result.price_abatement_amount_vnd:,.0f} VNĐ[/]")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


@trade_app.command("incoterms")
def lookup_incoterms(
    term: str = typer.Argument(..., help="Mã điều kiện Incoterms (EXW, FCA, CPT, CIP, DAP, DPU, DDP, FAS, FOB, CFR, CIF)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu chi tiết quy tắc Incoterms 2020 & Nghĩa vụ bảo hiểm bắt buộc."""
    rule = InternationalSalesIncotermsEngine.lookup_incoterms_rule(term)
    if not rule:
        console.print(f"[bold red]Lỗi:[/] Không tìm thấy quy tắc Incoterms '{term}'. Vui lòng nhập đúng 1 trong 11 quy tắc Incoterms 2020.")
        return

    if json_mode:
        payload = {
            "code": rule.code,
            "name_vn": rule.name_vn,
            "group": rule.group.value,
            "risk_transfer_point_vn": rule.risk_transfer_point_vn,
            "mandatory_insurance": rule.mandatory_insurance,
            "carriage_contract_party": rule.carriage_contract_party,
            "advice_vn": rule.advice_vn,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold]Quy tắc:[/] [bold cyan]{rule.code} — {rule.name_vn}[/bold cyan]\n"
            f"[bold]Phương thức vận tải:[/] {'Mọi phương thức (Any Mode)' if rule.group.value == 'any_mode' else 'Đường biển & Thủy nội địa (Sea/Inland)'}\n"
            f"[bold]Điểm chuyển giao rủi ro:[/] {rule.risk_transfer_point_vn}\n"
            f"[bold]Bảo hiểm bắt buộc:[/] [yellow]{rule.mandatory_insurance}[/yellow]\n"
            f"[bold]Bên thuê phương tiện vận chuyển:[/] [cyan]{rule.carriage_contract_party}[/cyan]\n\n"
            f"[bold]Khuyến nghị áp dụng:[/] {rule.advice_vn}",
            title=f"[bold green]Incoterms 2020: {rule.code}[/bold green]",
            border_style="cyan",
        )
    )


# ============================================================================
# 4. TRADE REMEDIES & ANTI-DUMPING SUBCOMMANDS (PHASE 166)
# ============================================================================

@trade_app.command("anti-dumping")
def calc_anti_dumping(
    normal_val: float = typer.Argument(..., help="Giá trị thông thường tại nước xuất khẩu (VNĐ)"),
    export_price: float = typer.Argument(..., help="Giá xuất khẩu sang Việt Nam (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính biên độ bán phá giá (Dumping Margin) theo Điều 77 & 78 Luật Quản lý ngoại thương 2017."""
    result = TradeRemediesEngine.calculate_dumping_margin(
        normal_value_vnd=normal_val,
        export_price_vnd=export_price,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Biên Độ Bán Phá Giá (Dumping Margin)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")

    table.add_row("Giá trị thông thường (NV)", f"{result.normal_value_vnd:,.0f} VNĐ")
    table.add_row("Giá xuất khẩu (EP)", f"{result.export_price_vnd:,.0f} VNĐ")
    table.add_row("[bold cyan]Biên độ bán phá giá[/]", f"[bold cyan]{result.dumping_margin_pct:.2f}%[/]")
    table.add_row("Dưới ngưỡng tối thiểu (De Minimis < 2%)", "[bold green]Có[/]" if result.is_de_minimis else "[bold red]Không[/]")
    table.add_row("[bold green]Đủ điều kiện xem xét áp thuế[/]", "[bold red]ĐỦ ĐIỀU KIỆN[/]" if result.is_subject_to_anti_dumping else "[green]KHÔNG ÁP THUẾ[/]")

    console.print(table)
    console.print(f"[bold cyan]Đánh giá:[/] {result.advice_vn}")
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


@trade_app.command("trade-remedy")
def assess_trade_remedy(
    country: str = typer.Argument(..., help="Tên quốc gia xuất khẩu"),
    dumping_margin: float = typer.Argument(..., help="Biên độ bán phá giá (%)"),
    volume_share: float = typer.Argument(..., help="Tỷ trọng khối lượng nhập khẩu vào VN (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện áp dụng thuế chống bán phá giá tổng hợp (Điều 78, 81, 82 Luật QLNT 2017)."""
    result = TradeRemediesEngine.assess_anti_dumping_application(
        exporting_country=country,
        dumping_margin_pct=dumping_margin,
        import_volume_share_pct=volume_share,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    status_badge = "[bold red]ĐỦ ĐIỀU KIỆN ÁP THUẾ[/bold red]" if result.can_impose_duty else "[bold green]KHÔNG ÁP THUẾ[/bold green]"
    console.print(
        Panel.fit(
            f"[bold]Quốc gia xuất khẩu:[/] {result.exporting_country}\n"
            f"[bold]Tình trạng:[/] {status_badge}\n"
            f"[bold]Biên độ bán phá giá:[/] {result.dumping_margin_pct:.2f}%\n"
            f"[bold]Tỷ trọng nhập khẩu:[/] {result.import_volume_share_pct:.2f}% ({'Không đáng kể <3%' if result.is_volume_negligible else 'Đáng kể >=3%'})\n"
            f"[bold]Thuế suất tối đa cho phép:[/] [bold yellow]{result.maximum_duty_rate_pct:.2f}%[/bold yellow]\n"
            f"[bold]Thời hạn áp dụng tối đa:[/] {result.max_duration_years} năm (có rà soát định kỳ)\n\n"
            f"[bold cyan]Kết luận:[/] {result.advice_vn}\n"
            f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]",
            title=f"[bold cyan]Thẩm Tra Áp Thuế Chống Bán Phá Giá: {result.exporting_country}[/bold cyan]",
            border_style="red" if result.can_impose_duty else "green",
        )
    )


@trade_app.command("safeguard-surge")
def assess_safeguard(
    base_qty: float = typer.Argument(..., help="Khối lượng nhập khẩu kỳ cơ sở"),
    current_qty: float = typer.Argument(..., help="Khối lượng nhập khẩu kỳ điều tra hiện tại"),
    threshold: float = typer.Option(30.0, "--threshold", "-t", help="Ngưỡng gia tăng đột biến (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá mức gia tăng đột biến nhập khẩu phục vụ biện pháp tự vệ (Điều 88 Luật QLNT 2017)."""
    result = TradeRemediesEngine.assess_safeguard_surge(
        base_import_quantity=base_qty,
        current_import_quantity=current_qty,
        threshold_surge_rate_pct=threshold,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold red]GIA TĂNG ĐỘT BIẾN (ĐỦ ĐIỀU KIỆN TỰ VỆ)[/bold red]" if result.is_substantial_increase else "[bold green]MỨC TĂNG BÌNH THƯỜNG[/bold green]"
    console.print(
        Panel.fit(
            f"[bold]Đánh giá:[/bold] {badge}\n"
            f"[bold]Khối lượng cơ sở:[/] {result.base_import_quantity:,.0f} | [bold]Khối lượng hiện tại:[/] {result.current_import_quantity:,.0f}\n"
            f"[bold]Tỷ lệ tăng trưởng:[/] [bold yellow]+{result.surge_rate_pct:.2f}%[/bold yellow]\n"
            f"[bold]Kết luận:[/] {result.advice_vn}\n"
            f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]",
            title="[bold cyan]Đánh Giá Gia Tăng Nhập Khẩu Tự Vệ (Safeguards)[/bold cyan]",
            border_style="red" if result.is_substantial_increase else "green",
        )
    )
