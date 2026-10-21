# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Aviation Baggage/Limitation, CISG 1980 & Incoterms (Phase 165)."""

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
    InternationalSalesIncotermsEngine,
)

console = Console()


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
