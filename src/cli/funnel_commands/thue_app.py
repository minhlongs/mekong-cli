# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for Vietnam tax (Thuế) commands."""

from __future__ import annotations

import json
from typing import Optional

import typer

from src.commands.thue_dnvn import calculate_gtgt, calculate_tncn, calculate_tndn

__all__ = ["calculate_gtgt", "calculate_tncn", "calculate_tndn", "thue_app"]

thue_app = typer.Typer(
    name="thue",
    help="Thuế VN — TNCN lũy tiến, TNDN, GTGT (offline, không cần API)",
    no_args_is_help=False, add_completion=False, rich_markup_mode="rich",
)


@thue_app.callback(invoke_without_command=True)
def thue_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Hệ thống tính thuế Việt Nam — TNCN lũy tiến, TNDN, GTGT."""
    if ctx.invoked_subcommand is not None:
        return
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from src.core.thue_engine import ThueEngine

    status_data = ThueEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console = Console()
    console.print(
        Panel(
            f"[bold green]Hệ Thống Thuế Việt Nam (TNCN, TNDN, GTGT)[/]\n\n"
            f"  Tổng số lượt tính:       [cyan]{status_data['total_calculations']}[/]\n"
            f"  Tổng tiền thuế mô phỏng: [yellow]{status_data['total_tax_simulated']:,.0f} đ[/]\n"
            f"  Hồ sơ thuế mẫu:          [magenta]{status_data['total_profiles']}[/]\n"
            f"  Giảm trừ bản thân:       [bold]11.000.000 đ/tháng[/]\n"
            f"  Giảm trừ người PT:       [bold]4.400.000 đ/người/tháng[/]\n"
            f"  Thuế TNDN tiêu chuẩn:    [bold]20%[/] (Ưu đãi SME: [bold green]17%[/])",
            title="[bold blue]Thuế Doanh Nghiệp & Cá Nhân VN[/]", border_style="green",
        )
    )
    table = Table(title="Lịch Sử Tính Thuế Gần Nhất", show_header=True, header_style="bold magenta")
    for col in ("Mã Tính", "Loại Thuế", "Số Tiền Gốc", "Tiền Thuế", "Thuế Suất"):
        table.add_column(col)
    for c in status_data.get("recent_calculations", []):
        table.add_row(
            c["calc_id"], c["tax_type"].upper(), f"{c['gross_amount']:,.0f} đ",
            f"{c['tax_amount']:,.0f} đ", f"{c['effective_rate']:.1f}%",
        )
    console.print(table)


@thue_app.command(name="tncn")
def thue_tncn(
    monthly_income: int = typer.Argument(..., help="Thu nhập gộp/tháng (VND)"),
    dependents: int = typer.Option(0, "--dependents", "-d", help="Số người phụ thuộc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính thuế TNCN lũy tiến (Điều 22, Luật thuế TNCN)."""
    from src.core.thue_engine import ThueEngine

    result = ThueEngine().calculate_tncn(monthly_income, dependents=dependents)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    try:
        typer.echo(calculate_tncn(monthly_income, dependents=dependents).to_summary())
    except Exception:
        f = result["formatted"]
        typer.echo(
            f"=== TÍNH THUẾ TNCN ===\nThu nhập gộp:      {f['gross']}/tháng\n"
            f"Giảm trừ bản thân: {result['personal_deduction']:,.0f} đ\n"
            f"Giảm trừ PT:       {result['dependent_deduction']:,.0f} đ\n"
            f"Thu nhập tính thuế:{f['taxable']}\nTiền thuế TNCN:    {f['tax']}\n"
            f"Thu nhập thực nhận:{f['net']}\nThuế suất thực tế: {result['effective_rate_pct']:.1f}%\n"
        )


@thue_app.command(name="tndn")
def thue_tndn(
    annual_revenue: int = typer.Argument(..., help="Doanh thu năm (VND)"),
    profit: Optional[int] = typer.Option(None, "--profit", "-p", help="Lợi nhuận tính thuế (VND)"),
    sme: bool = typer.Option(True, "--sme/--no-sme", help="Áp dụng ưu đãi SME 17% nếu ≤ 3 tỷ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính thuế TNDN (20% tiêu chuẩn, 17% SME ≤ 3 tỷ/năm)."""
    from src.core.thue_engine import ThueEngine

    result = ThueEngine().calculate_tndn(annual_revenue, profit=profit, is_sme=sme)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    try:
        typer.echo(calculate_tndn(annual_revenue).to_summary())
    except Exception:
        f = result["formatted"]
        typer.echo(
            f"=== TÍNH THUẾ TNDN ===\nDoanh thu:       {f['revenue']}\n"
            f"Lợi nhuận ước tính: {f['profit']}\nThuế suất:       {result['applied_rate_pct']}%\n"
            f"Tiền thuế TNDN:  {f['tax']}\nLợi nhuận ròng:  {f['net_profit']}\n"
        )


@thue_app.command(name="gtgt")
def thue_gtgt(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    rate: int = typer.Option(10, "--rate", "-r", help="Thuế suất GTGT (0/5/8/10)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính thuế GTGT."""
    from src.core.thue_engine import ThueEngine

    result = ThueEngine().calculate_gtgt(amount, rate=rate)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    f = result["formatted"]
    typer.echo(f"Cơ sở: {f['subtotal']}\nThuế GTGT ({result['vat_rate_pct']}%): {f['vat']}\nTổng cộng: {f['total']}\n\n⚠️  Tra cứu tại thuedientu.gdt.gov.vn để xác nhận.")


@thue_app.command(name="status")
def thue_status(json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON")) -> None:
    """Xem tổng quan tình trạng tính thuế và số liệu mô phỏng."""
    from rich.console import Console
    from rich.panel import Panel
    from src.core.thue_engine import ThueEngine

    data = ThueEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    Console().print(
        Panel(
            f"Tổng số lượt tính: [cyan]{data['total_calculations']}[/]\n"
            f"Tổng tiền thuế mô phỏng: [yellow]{data['total_tax_simulated']:,.0f} đ[/]\n"
            f"Hồ sơ người nộp thuế: [magenta]{data['total_profiles']}[/]",
            title="[bold green]Trạng Thái Thuế VN[/]", border_style="green",
        )
    )


@thue_app.command(name="list")
def thue_list(
    tax_type: str = typer.Option("all", "--type", "-t", help="Lọc loại thuế (tncn, tndn, gtgt, all)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Liệt kê các phép tính thuế đã thực hiện."""
    from rich.console import Console
    from rich.table import Table
    from src.core.thue_engine import ThueEngine

    records = ThueEngine().list_calculations(tax_type=tax_type, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    table = Table(title=f"Lịch Sử Tính Thuế ({tax_type.upper()})", show_header=True, header_style="bold magenta")
    for col in ("Mã Tính", "Loại", "Số Tiền", "Tiền Thuế", "Thuế Suất", "Thời Gian"):
        table.add_column(col)
    for r in records:
        table.add_row(
            r["calc_id"], r["tax_type"].upper(), f"{r['gross_amount']:,.0f} đ",
            f"{r['tax_amount']:,.0f} đ", f"{r['effective_rate']:.1f}%", r["created_at"][:19],
        )
    Console().print(table)
