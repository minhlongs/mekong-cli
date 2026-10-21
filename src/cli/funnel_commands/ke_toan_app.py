# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for Vietnam accounting (Kế toán) commands."""

from __future__ import annotations

import json

import typer

from src.commands.ke_toan import create_invoice

__all__ = ["create_invoice", "ke_toan_app"]

ke_toan_app = typer.Typer(
    name="ke-toan",
    help="Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


@ke_toan_app.callback(invoke_without_command=True)
def ke_toan_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.ke_toan_engine import KeToanEngine

    status_data = KeToanEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(
        Panel(
            f"[bold green]HỆ THỐNG KẾ TOÁN VAS & HÓA ĐƠN ĐIỆN TỬ TT78[/]\n"
            f"  Trạng thái:            [bold cyan]{status_data['status'].upper()}[/]\n"
            f"  Tổng số hóa đơn:       [bold]{status_data['total_invoices']}[/]\n"
            f"  Tổng doanh thu:        [yellow]{status_data['total_revenue']:,.0f} đ[/]\n"
            f"  Thuế GTGT đầu ra:      [green]{status_data['total_vat_output']:,.0f} đ[/]\n"
            f"  Tổng tiền thanh toán:  [bold magenta]{status_data['total_gross_invoiced']:,.0f} đ[/]\n"
            f"  Bút toán VAS ghi sổ:   [bold]{status_data['total_journal_entries']}[/]\n"
            f"  Doanh số phát sinh:    [cyan]{status_data['total_ledger_turnover']:,.0f} đ[/]\n"
            f"  Danh mục tài khoản:    [bold]{status_data['total_accounts']} tài khoản VAS[/]",
            title="[bold blue]Kế Toán Doanh Nghiệp VN[/]",
            border_style="green",
        )
    )

    table = Table(title="Hóa Đơn Điện Tử Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã Hóa Đơn", style="dim", width=18)
    table.add_column("Người Mua", style="cyan", width=20)
    table.add_column("Tiền Hàng", justify="right", width=16)
    table.add_column("Thuế GTGT", justify="right", width=16)
    table.add_column("Tổng Cộng", justify="right", width=16)

    for inv in status_data.get("recent_invoices", []):
        table.add_row(
            inv["invoice_id"],
            inv["buyer_name"],
            f"{inv['subtotal']:,.0f} đ",
            f"{inv['vat_amount']:,.0f} đ",
            f"{inv['total_amount']:,.0f} đ",
        )
    console.print(table)


@ke_toan_app.command(name="create")
def ke_toan_create(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tạo hóa đơn đơn giản và in summary."""
    from src.core.ke_toan_engine import KeToanEngine

    inv_data = KeToanEngine().create_invoice(
        amount=amount, vat_rate=vat_rate, buyer=buyer, seller=seller,
        seller_tax_code=seller_tax_code, description=description,
    )
    if json_mode:
        typer.echo(json.dumps(inv_data, indent=2, ensure_ascii=False))
        return

    invoice = create_invoice(
        amount=amount, vat_rate=vat_rate, buyer=buyer, seller=seller,
        seller_tax_code=seller_tax_code, description=description,
    )
    typer.echo(invoice.to_summary())


@ke_toan_app.command(name="xml")
def ke_toan_xml(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
) -> None:
    """Xuất XML hóa đơn theo schema TT78/2021."""
    invoice = create_invoice(
        amount=amount, vat_rate=vat_rate, buyer=buyer, seller=seller,
        seller_tax_code=seller_tax_code, description=description,
    )
    typer.echo(invoice.to_xml())


@ke_toan_app.command(name="journal")
def ke_toan_journal(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xuất bút toán kế toán VAS (JSON)."""
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()
    inv_data = engine.create_invoice(
        amount=amount, vat_rate=vat_rate, buyer=buyer, seller=seller,
        seller_tax_code=seller_tax_code, description=description, save=False,
    )
    jrn = engine.create_vas_journal(inv_data, save=True)
    if json_mode:
        typer.echo(json.dumps(jrn, indent=2, ensure_ascii=False))
        return

    invoice = create_invoice(
        amount=amount, vat_rate=vat_rate, buyer=buyer, seller=seller,
        seller_tax_code=seller_tax_code, description=description,
    )
    typer.echo(json.dumps(invoice.to_journal_entry(), ensure_ascii=False, indent=2))


@ke_toan_app.command(name="summary")
def ke_toan_summary(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
) -> None:
    """In summary hóa đơn (dạng text dễ đọc)."""
    invoice = create_invoice(
        amount=amount, vat_rate=vat_rate, buyer=buyer, seller=seller,
        seller_tax_code=seller_tax_code, description=description,
    )
    typer.echo(invoice.to_summary())


from src.cli.funnel_commands.ke_toan_telemetry import (  # noqa: E402, F401
    ke_toan_list,
    ke_toan_status,
)
