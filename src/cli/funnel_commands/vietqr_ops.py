# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VietQR transaction history, reconciliation recording, and status commands."""

from __future__ import annotations

import json

import typer

from src.cli.funnel_commands.vietqr_app import vietqr_app


@vietqr_app.command(name="transactions")
def vietqr_transactions(
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng giao dịch hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách giao dịch dạng JSON"),
) -> None:
    """Xem lịch sử các giao dịch chuyển khoản ngân hàng đã đối soát."""
    from src.core.vietqr_engine import VietQrEngine

    txs = VietQrEngine().list_transactions(limit=limit)
    if json_mode:
        typer.echo(json.dumps({"total": len(txs), "transactions": txs}, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Lịch Sử Giao Dịch Chuyển Khoản Ngân Hàng", show_header=True, header_style="bold cyan")
    table.add_column("Mã GD", style="dim", width=14)
    table.add_column("Mã GD Ngân Hàng", style="bold", width=18)
    table.add_column("Số Tiền", justify="right", width=16)
    table.add_column("Nội Dung Chuyển Khoản", width=24)
    table.add_column("Trạng Thái", justify="center", width=12)
    table.add_column("Thời Gian", style="dim", width=22)

    for tx in txs:
        table.add_row(
            tx["transaction_id"],
            tx["bank_tx_id"],
            f"{tx['amount_vnd']:,.0f} đ",
            tx["memo"],
            f"[green]{tx['status']}[/]",
            tx["received_at"][:19],
        )
    Console().print(table)


@vietqr_app.command(name="record")
def vietqr_record(
    tx_id: str = typer.Argument(..., help="Mã giao dịch ngân hàng (e.g. FT26090123)"),
    amount: int = typer.Argument(..., help="Số tiền thanh toán đã nhận (VND)"),
    memo: str = typer.Option("", "--memo", "-m", help="Nội dung giao dịch"),
    order_id: str = typer.Option("", "--order", help="Mã đơn hàng liên kết"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả ghi nhận dạng JSON"),
) -> None:
    """Ghi nhận đối soát giao dịch chuyển khoản ngân hàng (idempotent)."""
    from src.core.vietqr_engine import VietQrEngine

    res = VietQrEngine().record_transaction(
        bank_tx_id=tx_id,
        amount_vnd=amount,
        memo=memo,
        matched_order_id=order_id or None,
    )
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    dup_str = " [yellow](Giao dịch đã tồn tại - Bỏ qua trùng lặp)[/]" if res.get("is_duplicate") else ""
    Console().print(
        Panel(
            f"[bold green]GHI NHẬN ĐỐI SOÁT GIAO DỊCH THÀNH CÔNG[/]{dup_str}\n\n"
            f"  Mã hệ thống:      [bold]{res['transaction_id']}[/]\n"
            f"  Mã GD ngân hàng:  [bold cyan]{res['bank_tx_id']}[/]\n"
            f"  Số tiền nhận:     [bold green]{res['amount_vnd']:,.0f} đ[/]\n"
            f"  Nội dung:         [yellow]{res['memo']}[/]\n"
            f"  Đơn hàng:         {res.get('matched_order_id') or '(Không có)'}\n"
            f"  Trạng thái:       [bold green]{res['status'].upper()}[/]",
            title="[bold blue]Đối Soát Giao Dịch VietQR[/]",
            border_style="green",
        )
    )


@vietqr_app.command(name="status")
def vietqr_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dạng JSON"),
) -> None:
    """Kiểm tra trạng thái hệ thống VietQR và số liệu thanh toán."""
    from src.core.vietqr_engine import VietQrEngine

    status_data = VietQrEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    acc = status_data["default_account"]
    Console().print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG VIETQR / NAPAS 247[/]\n\n"
            f"Trạng thái:             [bold green]{status_data['status'].upper()}[/]\n"
            f"Cổng xử lý:             {status_data['gateway']}\n"
            f"Tài khoản thụ hưởng:    {acc['account_number']} ({acc['bank']})\n"
            f"Số mã QR đã tạo:        [bold]{status_data['total_qr_generated']}[/]\n"
            f"Giao dịch đối soát:     [cyan]{status_data['total_transactions_recorded']}[/]\n"
            f"Tổng dòng tiền nhận:    [bold green]{status_data['total_volume_received_vnd']:,.0f} đ[/]\n"
            f"Ngân hàng hỗ trợ:       {status_data['supported_banks_count']} ngân hàng",
            title="[bold blue]VietQR Gateway Telemetry[/]",
            border_style="green",
        )
    )
