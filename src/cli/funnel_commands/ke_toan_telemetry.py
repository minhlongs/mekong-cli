# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Ke Toan status and list telemetry commands."""

from __future__ import annotations

import json

import typer

from src.cli.funnel_commands.ke_toan_app import ke_toan_app


@ke_toan_app.command(name="status")
def ke_toan_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem trạng thái hệ thống kế toán và sổ sách phát sinh."""
    from src.core.ke_toan_engine import KeToanEngine

    data = KeToanEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    Console().print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG KẾ TOÁN VAS[/]\n"
            f"Tổng số hóa đơn:       [bold]{data['total_invoices']}[/]\n"
            f"Tổng doanh thu:        [yellow]{data['total_revenue']:,.0f} đ[/]\n"
            f"Thuế GTGT đầu ra:      [green]{data['total_vat_output']:,.0f} đ[/]\n"
            f"Tổng tiền thanh toán:  [bold magenta]{data['total_gross_invoiced']:,.0f} đ[/]\n"
            f"Bút toán VAS ghi sổ:   [bold]{data['total_journal_entries']}[/]\n"
            f"Doanh số phát sinh:    [cyan]{data['total_ledger_turnover']:,.0f} đ[/]\n"
            f"Danh mục tài khoản:    [bold]{data['total_accounts']} tài khoản VAS[/]",
            title="[bold blue]Hệ Thống Kế Toán[/]",
            border_style="green",
        )
    )


@ke_toan_app.command(name="list")
def ke_toan_list(
    list_type: str = typer.Option("all", "--type", "-t", help="Lọc loại (invoice, journal, all)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Liệt kê danh sách hóa đơn hoặc bút toán VAS đã ghi sổ."""
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()
    if list_type == "journal":
        records = engine.list_journal_entries(limit=limit)
    elif list_type == "invoice":
        records = engine.list_invoices(limit=limit)
    else:
        records = {
            "invoices": engine.list_invoices(limit=limit),
            "journal_entries": engine.list_journal_entries(limit=limit),
        }

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    if list_type in ("invoice", "all"):
        invs = records if list_type == "invoice" else records["invoices"]
        table = Table(title="Danh Sách Hóa Đơn Điện Tử", show_header=True, header_style="bold magenta")
        table.add_column("Mã Hóa Đơn", style="dim", width=18)
        table.add_column("Người Mua", style="cyan", width=20)
        table.add_column("Tiền Hàng", justify="right", width=16)
        table.add_column("Thuế GTGT", justify="right", width=16)
        table.add_column("Tổng Tiền", justify="right", width=16)
        table.add_column("Ngày Lập", style="dim")

        for r in invs:
            table.add_row(
                r["invoice_id"],
                r["buyer_name"],
                f"{r['subtotal']:,.0f} đ",
                f"{r['vat_amount']:,.0f} đ",
                f"{r['total_amount']:,.0f} đ",
                r["invoice_date"],
            )
        Console().print(table)
