# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 117: E-Transaction Record Listing & Telemetry Status CLI commands."""

from __future__ import annotations

import json

import typer
from rich.table import Table

from src.cli.commands._etransaction_msg_cmds import console, etransaction_app


@etransaction_app.command("list")
def list_cmd(
    type: str = typer.Option("all", "--type", help="Loại bản ghi (all, messages, signatures, trust_tokens, contracts)"),
    limit: int = typer.Option(20, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Liệt kê danh sách thông điệp dữ liệu, chữ ký số, dấu tin cậy và hợp đồng điện tử."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    records = engine.list_records(record_type=type, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "messages" in records and records["messages"]:
        table = Table(title="Danh Sách Thông Điệp Dữ Liệu (Law 20/2023/QH15)")
        table.add_column("Mã Thông Điệp", style="cyan")
        table.add_column("Tiêu Đề", style="bold")
        table.add_column("Bên Gửi", style="green")
        table.add_column("Bên Nhận", style="yellow")
        table.add_column("Bản Gốc", style="magenta")
        table.add_column("Chuyển Đổi Giấy", style="blue")
        for m in records["messages"]:
            table.add_row(
                m["message_id"],
                m["title"],
                m["originator"],
                m["recipient"],
                "Có" if m["is_original"] else "Không",
                "Có" if m["is_paper_converted"] else "Không",
            )
        console.print(table)

    if "contracts" in records and records["contracts"]:
        table = Table(title="Danh Sách Hợp Đồng Điện Tử (CeCA)")
        table.add_column("Mã Hợp Đồng", style="cyan")
        table.add_column("Số Hiệu", style="bold")
        table.add_column("Tiêu Đề", style="white")
        table.add_column("Giá Trị", style="yellow")
        table.add_column("Trạng Thái", style="green")
        table.add_column("Dấu CeCA", style="red")
        for c in records["contracts"]:
            table.add_row(
                c["contract_id"],
                c["contract_number"],
                c["title"],
                f"{c['contract_value']:,.0f} {c['currency']}",
                c["status"],
                "ĐÃ CHỨNG THỰC" if c["ceca_verified"] else "CHƯA",
            )
        console.print(table)


@etransaction_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra chỉ số đo lường và tình trạng vận hành hệ thống giao dịch điện tử."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    status = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(status, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]E-Transaction Subsystem Status:[/] {status['status']}")
    console.print(f"Tổng thông điệp dữ liệu: {status['data_messages']['total']}")
    console.print(f"Tổng chữ ký số: {status['signatures']['total']} (Tỷ lệ tuân thủ: {status['signatures']['compliance_rate_pct']}%)")
    console.print(f"Tổng hợp đồng điện tử: {status['contracts']['total']} ({status['contracts']['ceca_verified']} có chứng thực CeCA)")
