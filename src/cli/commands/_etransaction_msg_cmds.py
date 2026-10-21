# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 117: Electronic Data Messages & Paper-to-Electronic Conversion CLI commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

etransaction_app = typer.Typer(
    name="etransaction",
    help="Vietnamese Electronic Transactions, Digital Signatures, Trust Services & Data Messages Suite.",
)
console = Console()


@etransaction_app.callback(invoke_without_command=True)
def etransaction_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động giao dịch điện tử, chữ ký số, dịch vụ tin cậy và hợp đồng điện tử CeCA."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    telemetry = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    reg = telemetry["regulatory_framework"]
    msg = telemetry["data_messages"]
    sig = telemetry["signatures"]
    tru = telemetry["trust_services"]
    ctr = telemetry["contracts"]

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ GIAO DỊCH ĐIỆN TỬ, CHỮ KÝ SỐ & DỊCH VỤ TIN CẬY QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:               [bold]{reg['general_law']}[/]\n"
            f"  Nghị định chữ ký số:         [bold yellow]{reg['pki_decree']}[/] | Nghị định CeCA: [bold yellow]{reg['ceca_decree']}[/]\n"
            f"  Ngày hiệu lực thi hành:      [bold green]{reg['effective_date']}[/]\n\n"
            f"  Thông điệp dữ liệu (Đ9-11):  [bold]{msg['total']}[/] thông điệp ([bold green]{msg['originals']}[/] bản gốc, [bold cyan]{msg['paper_converted']}[/] chuyển đổi từ giấy)\n"
            f"  Chữ ký điện tử & Chữ ký số:  [bold]{sig['total']}[/] chữ ký ([bold green]{sig['valid']}[/] hợp lệ, [bold blue]{sig['qualified_pki']}[/] chữ ký số an toàn PKI)\n"
            f"  - Tỷ lệ tuân thủ pháp lý:    [bold green]{sig['compliance_rate_pct']}%[/]\n\n"
            f"  Dịch vụ tin cậy (Đ28-32):    [bold]{tru['total_tokens']}[/] chứng thư/token phát hành\n"
            f"  - Dấu thời gian (RFC 3161):  [bold yellow]{tru['timestamp_tokens']}[/] dấu | Dấu xác thực CeCA: [bold yellow]{tru['ceca_tokens']}[/] con dấu\n\n"
            f"  Hợp đồng điện tử (Đ34-38):   [bold]{ctr['total']}[/] hợp đồng ([bold green]{ctr['fully_executed']}[/] đã ký kết hoàn tất)\n"
            f"  - Chứng thực CeCA (NĐ 52):   [bold red]{ctr['ceca_verified']}[/] hợp đồng có gắn dấu xác thực CeCA",
            title="[bold blue]Vietnam Electronic Transactions & Digital Trust Telemetry[/]",
            border_style="blue",
        )
    )


@etransaction_app.command("message")
def message_cmd(
    title: str = typer.Argument(..., help="Tiêu đề thông điệp dữ liệu / chứng từ điện tử"),
    content: str = typer.Option(..., "--content", "-c", help="Nội dung chuỗi hoặc payload của thông điệp"),
    originator: str = typer.Option(..., "--originator", "-o", help="Người khởi tạo / Bên gửi thông điệp"),
    recipient: str = typer.Option(..., "--recipient", "-r", help="Bên nhận thông điệp dữ liệu"),
    format_type: str = typer.Option("json", "--format", help="Định dạng dữ liệu (json, xml, pdf_metadata, text, edi)"),
    original: bool = typer.Option(True, "--original/--copy", help="Xác nhận là bản gốc (Điều 10) hay bản sao"),
    retention: int = typer.Option(10, "--retention", help="Thời hạn lưu trữ bắt buộc (năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tạo và lưu trữ thông điệp dữ liệu có giá trị pháp lý theo Luật GDĐT 2023 Điều 9-11."""
    from src.core.etransaction_engine import ETransactionEngine
    try:
        res = ETransactionEngine().create_data_message(
            title=title, content=content, originator=originator, recipient=recipient,
            format_type=format_type, is_original=original, retention_years=retention,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi khởi tạo thông điệp dữ liệu:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]KHỞI TẠO THÔNG ĐIỆP DỮ LIỆU PHÁP LÝ THÀNH CÔNG[/]\n\n"
        f"  Mã thông điệp (ID):        [bold yellow]{res['message_id']}[/]\n"
        f"  Tiêu đề chứng từ:          [bold]{res['title']}[/]\n"
        f"  Bên gửi:                   [bold]{res['originator']}[/] -> Bên nhận: [bold]{res['recipient']}[/]\n"
        f"  Định dạng:                 [bold]{res['format_type'].upper()}[/] | Lưu trữ: [bold]{res['retention_period_years']} năm[/]\n"
        f"  Mã băm toàn vẹn (SHA-256): [bold cyan]{res['content_hash']}[/]\n\n"
        f"  Giá trị như văn bản (Đ9):  [bold green]ĐẠT[/]\n"
        f"  Giá trị như bản gốc (Đ10): [bold green]{'ĐẠT' if res['is_original'] else 'KHÔNG (Bản sao)'}[/]\n"
        f"  Chứng cứ pháp lý (Đ11):    [bold green]ĐẠT[/]",
        title="[bold blue]Data Message Created (Law 20/2023/QH15)[/]", border_style="green",
    ))


@etransaction_app.command("verify-msg")
def verify_msg_cmd(
    message_id: str = typer.Argument(..., help="Mã thông điệp dữ liệu cần xác minh (MSG-...)"),
    presented_content: Optional[str] = typer.Option(None, "--content", help="Nội dung kiểm tra đối chiếu tính toàn vẹn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác minh tính toàn vẹn và giá trị chứng cứ của thông điệp dữ liệu theo Điều 9-11."""
    from src.core.etransaction_engine import ETransactionEngine
    try:
        res = ETransactionEngine().verify_data_message(message_id=message_id, presented_content=presented_content)
    except Exception as exc:
        console.print(f"[bold red]Lỗi xác minh thông điệp dữ liệu:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    st_style = "green" if res["integrity_verified"] else "red"
    st_text = "TOÀN VẸN (KHÔNG BỊ THAY ĐỔI)" if res["integrity_verified"] else "BỊ XÂM PHẠM / SAI LỆCH NỘI DUNG"
    console.print(Panel(
        f"[bold {st_style}]KẾT QUẢ GIÁM ĐỊNH TOÀN VẸN THÔNG ĐIỆP DỮ LIỆU[/]\n\n"
        f"  Mã thông điệp:             [bold]{res['message_id']}[/] - [bold]{res['title']}[/]\n"
        f"  Bên gửi:                   [bold]{res['originator']}[/] -> Bên nhận: [bold]{res['recipient']}[/]\n"
        f"  Trạng thái toàn vẹn:       [bold {st_style}]{st_text}[/]\n"
        f"  Mã băm lưu trữ:            [bold]{res['stored_hash']}[/]\n"
        f"  Mã băm xác minh:           [bold]{res['verified_hash']}[/]\n\n"
        f"  Chữ ký điện tử liên kết:   [bold]{res['signatures_count']}[/] chữ ký\n"
        f"  Dấu thời gian/tin cậy:     [bold]{res['trust_tokens_count']}[/] con dấu",
        title="[bold blue]Data Message Verification[/]", border_style=st_style,
    ))


@etransaction_app.command("convert")
def convert_cmd(
    paper_ref: str = typer.Option(..., "--paper-ref", help="Số hiệu / Ký hiệu văn bản giấy gốc"),
    converted_by: str = typer.Option(..., "--converted-by", help="Cơ quan / Tổ chức thực hiện chuyển đổi"),
    content: str = typer.Option(..., "--content", "-c", help="Nội dung số hóa từ văn bản giấy"),
    title: str = typer.Option(..., "--title", help="Tiêu đề văn bản chuyển đổi"),
    recipient: str = typer.Option(..., "--recipient", help="Cơ quan / Cá nhân tiếp nhận"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Chuyển đổi văn bản giấy sang thông điệp dữ liệu điện tử theo Điều 12 Luật GDĐT 2023."""
    from src.core.etransaction_engine import ETransactionEngine
    try:
        res = ETransactionEngine().convert_paper_to_electronic(
            paper_ref=paper_ref, converted_by=converted_by, content=content, title=title, recipient=recipient,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi chuyển đổi văn bản giấy:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]CHUYỂN ĐỔI VĂN BẢN GIẤY SANG ĐIỆN TỬ THÀNH CÔNG (ĐIỀU 12)[/]\n\n"
        f"  Mã thông điệp chuyển đổi:  [bold yellow]{res['message_id']}[/]\n"
        f"  Văn bản giấy nguồn:        [bold]{paper_ref}[/]\n"
        f"  Cơ quan thực hiện:         [bold]{res['originator']}[/]\n"
        f"  Mã băm toàn vẹn:           [bold cyan]{res['content_hash']}[/]\n"
        f"  Căn cứ pháp lý:            [bold]Luật Giao dịch điện tử 2023 Điều 12[/]",
        title="[bold blue]Paper-to-Electronic Conversion[/]", border_style="green",
    ))
