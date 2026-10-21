# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for VietQR / Napas 247 instant payment commands."""

from __future__ import annotations

import json

import typer

vietqr_app = typer.Typer(
    name="vietqr",
    help="VietQR / Napas 247 — thanh toán chuyển khoản, tạo mã QR EMVCo, đối soát",
    add_completion=False,
)


@vietqr_app.callback(invoke_without_command=True)
def vietqr_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan VietQR dạng JSON"),
) -> None:
    """VietQR / Napas 247 — thanh toán chuyển khoản, tạo mã QR EMVCo, đối soát."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.vietqr_engine import VietQrEngine

    status_data = VietQrEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    acc = status_data["default_account"]
    console.print(
        Panel(
            f"[bold green]CỔNG THANH TOÁN VIETQR & NAPAS 247 TỰ ĐỘNG[/]\n"
            f"  Trạng thái:            [bold green]{status_data['status'].upper()}[/]\n"
            f"  Cổng thanh toán:       [cyan]{status_data['gateway']}[/]\n"
            f"  Quy chuẩn áp dụng:     {', '.join(status_data['statutory_standards'])}\n"
            f"  Tài khoản mặc định:    [yellow]{acc['account_number']}[/] — [bold]{acc['bank']}[/] ({acc['account_holder']})\n"
            f"  Số mã QR đã tạo:       [bold]{status_data['total_qr_generated']}[/]\n"
            f"  Giao dịch đối soát:    [bold cyan]{status_data['total_transactions_recorded']}[/]\n"
            f"  Tổng tiền đã nhận:     [bold green]{status_data['total_volume_received_vnd']:,.0f} đ[/]\n"
            f"  Ngân hàng liên kết:    [bold]{status_data['supported_banks_count']} ngân hàng Napas 247[/]",
            title="[bold blue]Hệ Thống Thanh Toán VietQR[/]",
            border_style="green",
        )
    )

    table = Table(title="Giao Dịch Thanh Toán Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã GD", style="dim", width=14)
    table.add_column("Mã Ngân Hàng", style="cyan", width=16)
    table.add_column("Số Tiền", justify="right", width=16)
    table.add_column("Nội Dung Chuyển Khoản", width=26)
    table.add_column("Trạng Thái", justify="center", width=12)

    for tx in status_data.get("recent_transactions", []):
        table.add_row(
            tx["transaction_id"],
            tx["bank_tx_id"],
            f"{tx['amount_vnd']:,.0f} đ",
            tx["memo"],
            f"[green]{tx['status']}[/]",
        )
    console.print(table)


@vietqr_app.command(name="generate")
def vietqr_generate(
    amount: int = typer.Argument(0, help="Số tiền thanh toán (VND, 0 = động/người chuyển nhập)"),
    memo: str = typer.Option("", "--memo", "-m", help="Nội dung chuyển khoản (e.g. MK-INV-1001)"),
    bank: str = typer.Option("MB", "--bank", "-b", help="Mã ngân hàng (MB, VCB, CTG, BIDV, TCB, ACB, TPB)"),
    account: str = typer.Option("", "--account", "-a", help="Số tài khoản thụ hưởng"),
    name: str = typer.Option("", "--name", "-n", help="Tên chủ tài khoản thụ hưởng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu QR dạng JSON"),
) -> None:
    """Tạo mã thanh toán VietQR chuẩn EMVCo và QuickLink Napas 247."""
    from src.core.vietqr_engine import VietQrEngine

    res = VietQrEngine().generate_qr(
        bank=bank, account_number=account, account_name=name, amount_vnd=amount, memo=memo,
    )
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    amount_str = f"{res['amount_vnd']:,.0f} đ" if res["amount_vnd"] > 0 else "Người chuyển tự nhập số tiền"
    Console().print(
        Panel(
            f"[bold green]MÃ THANH TOÁN VIETQR ĐÃ TẠO THÀNH CÔNG[/]\n\n"
            f"  Mã QR:          [bold]{res['qr_id']}[/]\n"
            f"  Ngân hàng:      [bold cyan]{res['bank_full']}[/] (BIN: {res['bank_bin']})\n"
            f"  Số tài khoản:   [bold yellow]{res['account_number']}[/]\n"
            f"  Chủ tài khoản:  [bold]{res['account_holder']}[/]\n"
            f"  Số tiền:        [bold magenta]{amount_str}[/]\n"
            f"  Nội dung:       [bold green]{res['memo'] or '(Không có)'}[/]\n\n"
            f"[bold cyan]QuickLink URL (Hiển thị ảnh QR):[/]\n{res['quicklink_url']}\n\n"
            f"[bold dim]Chuỗi EMVCo Payload:[/] [dim]{res['emvco_payload'][:60]}...[/dim]",
            title="[bold blue]VietQR Napas 247 Instant Transfer[/]",
            border_style="green",
        )
    )


@vietqr_app.command(name="banks")
def vietqr_banks(
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách ngân hàng dạng JSON"),
) -> None:
    """Tra cứu danh sách các ngân hàng liên kết Napas 247 và mã BIN."""
    from src.core.vietqr_engine import VietQrEngine

    banks = VietQrEngine().list_banks()
    if json_mode:
        typer.echo(json.dumps({"total": len(banks), "banks": banks}, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Danh Sách Ngân Hàng Napas 247 Hỗ Trợ VietQR", show_header=True, header_style="bold magenta")
    table.add_column("Mã BIN", style="dim", width=10)
    table.add_column("Ký Hiệu", style="bold cyan", width=10)
    table.add_column("Tên Ngân Hàng", width=45)

    for b in banks:
        table.add_row(b["bin"], b["short_name"], b["full_name"])
    Console().print(table)


from src.cli.funnel_commands.vietqr_ops import (  # noqa: E402, F401
    vietqr_record,
    vietqr_status,
    vietqr_transactions,
)
