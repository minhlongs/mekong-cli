"""CLI Commands for Mekong International Trade, Transport & Trade Remedies Suite (Phases 163 - 166)."""

from __future__ import annotations

import json
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.trade_cisg_remedies import (
    calc_aviation_baggage, calc_cisg_reduction, check_aviation_limitation,
    evaluate_cisg_breach, lookup_incoterms,
)
from src.cli.commands.trade_mto_aviation import (
    calc_aviation_cargo, calc_aviation_injury, calc_mto_delay,
    calc_mto_liability, check_mto_limitation,
)
from src.core.trade_transport_engine import TradeRemediesEngine

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

    console.print(Panel.fit(
        "[bold cyan]MEKONG TRADE, TRANSPORT & TRADE REMEDIES SUITE[/bold cyan]\n"
        "[italic dim]Căn cứ: NĐ 87/2009, Luật HKDD 2006, Montreal 1999, CISG 1980, Incoterms 2020 & Luật QLNT 2017[/italic dim]\n\n"
        "  [bold yellow]1. Vận tải đa phương thức:[/]  Trần 666.67 SDR/kiện & 2.0 SDR/kg, trần chậm giao 2x cước, thời hiệu 9 tháng\n"
        "  [bold yellow]2. Hàng không dân dụng:[/]    Trách nhiệm nghiêm ngặt 128,821 SDR, 22 SDR/kg hàng hóa, thời hiệu 2 năm\n"
        "  [bold yellow]3. CISG & Incoterms 2020:[/]  Vi phạm cơ bản Điều 25, Giảm giá hàng Điều 50, 11 quy tắc Incoterms (CIP/CIF)\n"
        "  [bold yellow]4. Phòng vệ thương mại:[/]    Biên độ phá giá (De Minimis 2.0%), thị phần < 3.0%, gia tăng nhập khẩu tự vệ",
        title="[bold green]Phases 163 - 166 Overview[/bold green]",
        border_style="cyan",
    ))


trade_app.command("mto-liability")(calc_mto_liability)
trade_app.command("mto-delay")(calc_mto_delay)
trade_app.command("mto-limitation")(check_mto_limitation)
trade_app.command("aviation-injury")(calc_aviation_injury)
trade_app.command("aviation-cargo")(calc_aviation_cargo)
trade_app.command("aviation-baggage")(calc_aviation_baggage)
trade_app.command("aviation-limitation")(check_aviation_limitation)
trade_app.command("cisg-breach")(evaluate_cisg_breach)
trade_app.command("cisg-reduction")(calc_cisg_reduction)
trade_app.command("incoterms")(lookup_incoterms)


@trade_app.command("anti-dumping")
def calc_anti_dumping(
    normal_val: float = typer.Argument(..., help="Giá trị thông thường tại nước xuất khẩu (VNĐ)"),
    export_price: float = typer.Argument(..., help="Giá xuất khẩu sang Việt Nam (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính biên độ bán phá giá (Dumping Margin) theo Điều 77 & 78 Luật Quản lý ngoại thương 2017."""
    result = TradeRemediesEngine.calculate_dumping_margin(normal_value_vnd=normal_val, export_price_vnd=export_price)
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Biên Độ Bán Phá Giá (Dumping Margin)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị", style="yellow", justify="right")
    for k, v in [
        ("Giá trị thông thường (NV)", f"{result.normal_value_vnd:,.0f} VNĐ"),
        ("Giá xuất khẩu (EP)", f"{result.export_price_vnd:,.0f} VNĐ"),
        ("[bold cyan]Biên độ bán phá giá[/]", f"[bold cyan]{result.dumping_margin_pct:.2f}%[/]"),
        ("Dưới ngưỡng tối thiểu (De Minimis < 2%)", "[bold green]Có[/]" if result.is_de_minimis else "[bold red]Không[/]"),
        ("[bold green]Đủ điều kiện xem xét áp thuế[/]", "[bold red]ĐỦ ĐIỀU KIỆN[/]" if result.is_subject_to_anti_dumping else "[green]KHÔNG ÁP THUẾ[/]"),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[bold cyan]Đánh giá:[/] {result.advice_vn}\n[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


@trade_app.command("trade-remedy")
def assess_trade_remedy(
    country: str = typer.Argument(..., help="Tên quốc gia xuất khẩu"),
    dumping_margin: float = typer.Argument(..., help="Biên độ bán phá giá (%)"),
    volume_share: float = typer.Argument(..., help="Tỷ trọng khối lượng nhập khẩu vào VN (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện áp dụng thuế chống bán phá giá tổng hợp (Điều 78, 81, 82 Luật QLNT 2017)."""
    result = TradeRemediesEngine.assess_anti_dumping_application(
        exporting_country=country, dumping_margin_pct=dumping_margin, import_volume_share_pct=volume_share,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    status_badge = "[bold red]ĐỦ ĐIỀU KIỆN ÁP THUẾ[/bold red]" if result.can_impose_duty else "[bold green]KHÔNG ÁP THUẾ[/bold green]"
    console.print(Panel.fit(
        f"[bold]Quốc gia xuất khẩu:[/] {result.exporting_country}\n"
        f"[bold]Tình trạng:[/] {status_badge}\n"
        f"[bold]Biên độ bán phá giá:[/] {result.dumping_margin_pct:.2f}%\n"
        f"[bold]Tỷ trọng nhập khẩu:[/] {result.import_volume_share_pct:.2f}% ({'Không đáng kể <3%' if result.is_volume_negligible else 'Đáng kể >=3%'})\n"
        f"[bold]Thuế suất tối đa cho phép:[/] [bold yellow]{result.maximum_duty_rate_pct:.2f}%[/bold yellow]\n"
        f"[bold]Thời hạn áp dụng tối đa:[/] {result.max_duration_years} năm (có rà soát định kỳ)\n\n"
        f"[bold cyan]Kết luận:[/] {result.advice_vn}\n[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]",
        title=f"[bold cyan]Thẩm Tra Áp Thuế Chống Bán Phá Giá: {result.exporting_country}[/bold cyan]",
        border_style="red" if result.can_impose_duty else "green",
    ))


@trade_app.command("safeguard-surge")
def assess_safeguard(
    base_qty: float = typer.Argument(..., help="Khối lượng nhập khẩu kỳ cơ sở"),
    current_qty: float = typer.Argument(..., help="Khối lượng nhập khẩu kỳ điều tra hiện tại"),
    threshold: float = typer.Option(30.0, "--threshold", "-t", help="Ngưỡng gia tăng đột biến (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá mức gia tăng đột biến nhập khẩu phục vụ biện pháp tự vệ (Điều 88 Luật QLNT 2017)."""
    result = TradeRemediesEngine.assess_safeguard_surge(
        base_import_quantity=base_qty, current_import_quantity=current_qty, threshold_surge_rate_pct=threshold,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold red]GIA TĂNG ĐỘT BIẾN (ĐỦ ĐIỀU KIỆN TỰ VỆ)[/bold red]" if result.is_substantial_increase else "[bold green]MỨC TĂNG BÌNH THƯỜNG[/bold green]"
    console.print(Panel.fit(
        f"[bold]Đánh giá:[/bold] {badge}\n"
        f"[bold]Khối lượng cơ sở:[/] {result.base_import_quantity:,.0f} | [bold]Khối lượng hiện tại:[/] {result.current_import_quantity:,.0f}\n"
        f"[bold]Tỷ lệ tăng trưởng:[/] [bold yellow]+{result.surge_rate_pct:.2f}%[/bold yellow]\n"
        f"[bold]Kết luận:[/] {result.advice_vn}\n[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]",
        title="[bold cyan]Đánh Giá Gia Tăng Nhập Khẩu Tự Vệ (Safeguards)[/bold cyan]",
        border_style="red" if result.is_substantial_increase else "green",
    ))
