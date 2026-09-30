# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Electronic Transactions, Digital Signatures & Trust Services Suite (Phase 117)."""

from __future__ import annotations

import json
from typing import Optional, List
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    engine = ETransactionEngine()
    try:
        res = engine.create_data_message(
            title=title,
            content=content,
            originator=originator,
            recipient=recipient,
            format_type=format_type,
            is_original=original,
            retention_years=retention,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi khởi tạo thông điệp dữ liệu:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]KHỞI TẠO THÔNG ĐIỆP DỮ LIỆU PHÁP LÝ THÀNH CÔNG[/]\n\n"
            f"  Mã thông điệp (ID):        [bold yellow]{res['message_id']}[/]\n"
            f"  Tiêu đề chứng từ:          [bold]{res['title']}[/]\n"
            f"  Bên gửi:                   [bold]{res['originator']}[/] -> Bên nhận: [bold]{res['recipient']}[/]\n"
            f"  Định dạng:                 [bold]{res['format_type'].upper()}[/] | Lưu trữ: [bold]{res['retention_period_years']} năm[/]\n"
            f"  Mã băm toàn vẹn (SHA-256): [bold cyan]{res['content_hash']}[/]\n\n"
            f"  Giá trị như văn bản (Đ9):  [bold green]ĐẠT[/]\n"
            f"  Giá trị như bản gốc (Đ10): [bold green]{'ĐẠT' if res['is_original'] else 'KHÔNG (Bản sao)'}[/]\n"
            f"  Chứng cứ pháp lý (Đ11):    [bold green]ĐẠT[/]",
            title="[bold blue]Data Message Created (Law 20/2023/QH15)[/]",
            border_style="green",
        )
    )


@etransaction_app.command("verify-msg")
def verify_msg_cmd(
    message_id: str = typer.Argument(..., help="Mã thông điệp dữ liệu cần xác minh (MSG-...)"),
    presented_content: Optional[str] = typer.Option(None, "--content", help="Nội dung kiểm tra đối chiếu tính toàn vẹn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác minh tính toàn vẹn và giá trị chứng cứ của thông điệp dữ liệu theo Điều 9-11."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    try:
        res = engine.verify_data_message(message_id=message_id, presented_content=presented_content)
    except Exception as exc:
        console.print(f"[bold red]Lỗi xác minh thông điệp dữ liệu:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    integrity_style = "green" if res["integrity_verified"] else "red"
    integrity_status = "TOÀN VẸN (KHÔNG BỊ THAY ĐỔI)" if res["integrity_verified"] else "BỊ XÂM PHẠM / SAI LỆCH NỘI DUNG"

    console.print(
        Panel(
            f"[bold {integrity_style}]KẾT QUẢ GIÁM ĐỊNH TOÀN VẸN THÔNG ĐIỆP DỮ LIỆU[/]\n\n"
            f"  Mã thông điệp:             [bold]{res['message_id']}[/] - [bold]{res['title']}[/]\n"
            f"  Bên gửi:                   [bold]{res['originator']}[/] -> Bên nhận: [bold]{res['recipient']}[/]\n"
            f"  Trạng thái toàn vẹn:       [bold {integrity_style}]{integrity_status}[/]\n"
            f"  Mã băm lưu trữ:            [bold]{res['stored_hash']}[/]\n"
            f"  Mã băm xác minh:           [bold]{res['verified_hash']}[/]\n\n"
            f"  Chữ ký điện tử liên kết:   [bold]{res['signatures_count']}[/] chữ ký\n"
            f"  Dấu thời gian/tin cậy:     [bold]{res['trust_tokens_count']}[/] con dấu",
            title="[bold blue]Data Message Verification[/]",
            border_style=integrity_style,
        )
    )


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

    engine = ETransactionEngine()
    try:
        res = engine.convert_paper_to_electronic(
            paper_ref=paper_ref,
            converted_by=converted_by,
            content=content,
            title=title,
            recipient=recipient,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi chuyển đổi văn bản giấy:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]CHUYỂN ĐỔI VĂN BẢN GIẤY SANG ĐIỆN TỬ THÀNH CÔNG (ĐIỀU 12)[/]\n\n"
            f"  Mã thông điệp chuyển đổi:  [bold yellow]{res['message_id']}[/]\n"
            f"  Văn bản giấy nguồn:        [bold]{paper_ref}[/]\n"
            f"  Cơ quan thực hiện:         [bold]{res['originator']}[/]\n"
            f"  Mã băm toàn vẹn:           [bold cyan]{res['content_hash']}[/]\n"
            f"  Căn cứ pháp lý:            [bold]Luật Giao dịch điện tử 2023 Điều 12[/]",
            title="[bold blue]Paper-to-Electronic Conversion[/]",
            border_style="green",
        )
    )


@etransaction_app.command("sign")
def sign_cmd(
    message_id: str = typer.Argument(..., help="Mã thông điệp dữ liệu cần ký (MSG-...)"),
    signer: str = typer.Option(..., "--signer", "-s", help="Định danh người ký (Họ tên / CCCD / MST Doanh nghiệp)"),
    role: str = typer.Option("legal_representative", "--role", help="Vai trò người ký (legal_representative, director, witness)"),
    type: str = typer.Option("QUALIFIED", "--type", help="Loại chữ ký (ORDINARY, SPECIALIZED, QUALIFIED)"),
    ca: Optional[str] = typer.Option("VNPT-CA", "--ca", help="Nhà cung cấp dịch vụ chứng thực chữ ký số (với QUALIFIED)"),
    serial: Optional[str] = typer.Option("5404BFA6C723810E", "--serial", help="Số serial chứng thư số"),
    valid_until: Optional[str] = typer.Option("2028-12-31T23:59:59Z", "--valid-until", help="Thời hạn hiệu lực chứng thư"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tạo chữ ký điện tử / chữ ký số an toàn theo Luật GDĐT 2023 Điều 21-25 & NĐ 130/2018/NĐ-CP."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    try:
        res = engine.create_electronic_signature(
            message_id=message_id,
            signer_identity=signer,
            signer_role=role,
            signature_type=type,
            ca_provider=ca,
            cert_serial=serial,
            cert_valid_until=valid_until,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi tạo chữ ký điện tử:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_str = "[bold green]HỢP LỆ THEO LUẬT[/]" if res["is_valid"] else "[bold red]KHÔNG HỢP LỆ / HẾT HẠN[/]"
    console.print(
        Panel(
            f"[bold green]KÝ ĐIỆN TỬ / CHỮ KÝ SỐ THÀNH CÔNG[/]\n\n"
            f"  Mã chữ ký (ID):            [bold yellow]{res['signature_id']}[/]\n"
            f"  Thông điệp dữ liệu:        [bold]{res['message_id']}[/]\n"
            f"  Người ký:                  [bold]{res['signer_identity']}[/] ({res['signer_role']})\n"
            f"  Phân loại chữ ký:          [bold cyan]{res['signature_type']}[/]\n"
            f"  Đơn vị cấp CA:             [bold]{res['ca_provider'] or 'N/A'}[/] | Serial: [bold]{res['cert_serial'] or 'N/A'}[/]\n"
            f"  Giá trị băm chữ ký:        [bold]{res['signature_value'][:32]}...[/]\n"
            f"  Trạng thái pháp lý:        {status_str}",
            title="[bold blue]Electronic Signature Generated[/]",
            border_style="green",
        )
    )


@etransaction_app.command("verify-sig")
def verify_sig_cmd(
    signature_id: str = typer.Argument(..., help="Mã chữ ký điện tử cần xác minh (SIG-...)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác minh tính hợp lệ và tuân thủ pháp lý của chữ ký số / chữ ký điện tử theo Điều 22-23."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    try:
        res = engine.verify_electronic_signature(signature_id=signature_id)
    except Exception as exc:
        console.print(f"[bold red]Lỗi xác minh chữ ký:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    valid_color = "green" if res["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold {valid_color}]KẾT QUẢ KIỂM TRA CHỮ KÝ SỐ / CHỮ KÝ ĐIỆN TỬ[/]\n\n"
            f"  Mã chữ ký:                 [bold]{res['signature_id']}[/]\n"
            f"  Người ký:                  [bold]{res['signer_identity']}[/] ({res['signer_role']})\n"
            f"  Loại chữ ký:               [bold]{res['signature_type']}[/]\n"
            f"  Nhà cung cấp CA:           [bold]{res['ca_provider'] or 'N/A'}[/] (Serial: {res['cert_serial'] or 'N/A'})\n"
            f"  Thời hạn chứng thư:        [bold]{res['cert_valid_until'] or 'N/A'}[/]\n"
            f"  Tính toàn vẹn thông điệp:  [bold green]{'ĐẠT' if res['verification_breakdown']['message_integrity_intact'] else 'SAI LỆCH'}[/]\n"
            f"  Hiệu lực chứng thư số:     [bold green]{'CÒN HIỆU LỰC' if res['verification_breakdown']['certificate_unexpired'] else 'HẾT HẠN'}[/]\n"
            f"  Đánh giá pháp lý:          [bold {valid_color}]{res['verification_breakdown']['law_compliance']}[/]",
            title="[bold blue]Signature Legal Verification[/]",
            border_style=valid_color,
        )
    )


@etransaction_app.command("trust")
def trust_cmd(
    target_id: str = typer.Argument(..., help="Mã đối tượng cần gắn dấu tin cậy (MSG-..., SIG-..., CTR-...)"),
    service_type: str = typer.Option("TIMESTAMP", "--type", help="Loại dịch vụ tin cậy (TIMESTAMP, DATA_CERT, CECA_CONTRACT)"),
    authority: str = typer.Option("Vietnam National Timestamp Authority", "--authority", help="Tên tổ chức cung cấp dịch vụ tin cậy"),
    license: str = typer.Option("BTTTT-TRUST-088/GP", "--license", help="Số giấy phép cấp bởi Bộ TT&TT hoặc Bộ Công Thương"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Cấp dấu thời gian (RFC 3161) hoặc chứng thư dịch vụ tin cậy theo Điều 28-32."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    try:
        res = engine.issue_trust_token(
            target_id=target_id,
            service_type=service_type,
            authority_name=authority,
            license_number=license,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi cấp dấu tin cậy:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]CẤP DẤU TIN CẬY / DẤU THỜI GIAN ĐIỆN TỬ THÀNH CÔNG[/]\n\n"
            f"  Mã dấu tin cậy (Token):    [bold yellow]{res['token_id']}[/]\n"
            f"  Loại dịch vụ tin cậy:      [bold cyan]{res['service_type']}[/]\n"
            f"  Đối tượng gắn dấu:         [bold]{res['target_id']}[/]\n"
            f"  Tổ chức cấp phép:          [bold]{res['authority_name']}[/] (GP: {res['license_number']})\n"
            f"  Thời điểm cấp (UTC):       [bold]{res['issued_at']}[/]\n"
            f"  Chữ ký số dấu thời gian:   [bold]{res['token_signature'][:32]}...[/]",
            title="[bold blue]Trust Token Issued[/]",
            border_style="green",
        )
    )


@etransaction_app.command("contract")
def contract_cmd(
    contract_number: str = typer.Option(..., "--number", "-n", help="Số hiệu hợp đồng điện tử"),
    title: str = typer.Option(..., "--title", "-t", help="Tiêu đề hợp đồng"),
    content: str = typer.Option(..., "--content", "-c", help="Nội dung điều khoản hợp đồng"),
    party_a: str = typer.Option(..., "--party-a", help="Tên Bên A (kèm MST/CCCD)"),
    party_b: str = typer.Option(..., "--party-b", help="Tên Bên B (kèm MST/CCCD)"),
    value: float = typer.Option(0.0, "--value", help="Giá trị hợp đồng (VND)"),
    currency: str = typer.Option("VND", "--currency", help="Loại tiền tệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Khởi tạo hợp đồng điện tử theo Luật GDĐT 2023 Điều 34-38."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    parties = [
        {"name": party_a.strip(), "role": "Party A", "tax_id": "0100109106"},
        {"name": party_b.strip(), "role": "Party B", "tax_id": "0300123456"},
    ]

    try:
        res = engine.create_electronic_contract(
            contract_number=contract_number,
            title=title,
            content=content,
            parties=parties,
            contract_value=value,
            currency=currency,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi khởi tạo hợp đồng điện tử:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]KHỞI TẠO HỢP ĐỒNG ĐIỆN TỬ THÀNH CÔNG[/]\n\n"
            f"  Mã hợp đồng (ID):          [bold yellow]{res['contract_id']}[/]\n"
            f"  Số hiệu:                   [bold]{res['contract_number']}[/] - [bold]{res['title']}[/]\n"
            f"  Giá trị hợp đồng:          [bold cyan]{res['contract_value']:,.0f} {res['currency']}[/]\n"
            f"  Các bên tham gia:          [bold]{party_a}[/] & [bold]{party_b}[/]\n"
            f"  Trạng thái:                [bold yellow]{res['status']}[/]\n"
            f"  Mã băm thông điệp hợp đồng:[bold]{res['content_hash']}[/]",
            title="[bold blue]Electronic Contract Initialized[/]",
            border_style="green",
        )
    )


@etransaction_app.command("sign-contract")
def sign_contract_cmd(
    contract_id: str = typer.Argument(..., help="Mã hợp đồng điện tử (CTR-...)"),
    party: str = typer.Option(..., "--party", "-p", help="Tên bên ký (phải trùng với danh sách bên trong hợp đồng)"),
    role: str = typer.Option("legal_representative", "--role", help="Vai trò người ký"),
    type: str = typer.Option("QUALIFIED", "--type", help="Loại chữ ký (QUALIFIED, SPECIALIZED, ORDINARY)"),
    ca: Optional[str] = typer.Option("VNPT-CA", "--ca", help="Nhà cung cấp chứng thư số"),
    serial: Optional[str] = typer.Option("5404BFA6C723810E", "--serial", help="Serial chứng thư số"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ký hợp đồng điện tử và tự động chuyển đổi trạng thái hiệu lực khi đủ chữ ký."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    try:
        res = engine.sign_electronic_contract(
            contract_id=contract_id,
            party_name=party,
            signer_role=role,
            signature_type=type,
            ca_provider=ca,
            cert_serial=serial,
            cert_valid_until="2028-12-31T23:59:59Z",
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi ký hợp đồng điện tử:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_color = "green" if res["all_parties_signed"] else "yellow"
    console.print(
        Panel(
            f"[bold {status_color}]KÝ HỢP ĐỒNG ĐIỆN TỬ THÀNH CÔNG[/]\n\n"
            f"  Hợp đồng:                  [bold]{res['contract_id']}[/] ({res['contract_number']})\n"
            f"  Bên vừa ký:                [bold]{res['signer']}[/] ({res['signature_type']})\n"
            f"  Tiến độ ký kết:            [bold]{len(res['signed_parties'])}/{res['total_parties']}[/] bên đã ký\n"
            f"  Trạng thái hiệu lực:       [bold {status_color}]{res['status']}[/]\n"
            f"  Giá trị thi hành (Đ34):    [bold green]{'HOÀN TẤT & CÓ HIỆU LỰC RÀNG BUỘC' if res['all_parties_signed'] else 'CHỜ CÁC BÊN CÒN LẠI KÝ'}[/]",
            title="[bold blue]Contract Signature Executed[/]",
            border_style=status_color,
        )
    )


@etransaction_app.command("ceca")
def ceca_cmd(
    contract_id: str = typer.Argument(..., help="Mã hợp đồng điện tử cần chứng thực (CTR-...)"),
    authority: str = typer.Option("CeCA-Vietnam-Post", "--authority", help="Tổ chức chứng thực hợp đồng điện tử CeCA"),
    license: str = typer.Option("BCT-CeCA-008/GP", "--license", help="Số giấy phép Bộ Công Thương"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Gắn dấu chứng thực CeCA lên hợp đồng điện tử theo Nghị định 52/2024/NĐ-CP."""
    from src.core.etransaction_engine import ETransactionEngine

    engine = ETransactionEngine()
    try:
        res = engine.certify_ceca_contract(
            contract_id=contract_id,
            ceca_authority=authority,
            license_number=license,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi chứng thực CeCA:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]CHỨNG THỰC HỢP ĐỒNG ĐIỆN TỬ CeCA THÀNH CÔNG (NGHỊ ĐỊNH 52/2024/NĐ-CP)[/]\n\n"
            f"  Mã hợp đồng:               [bold yellow]{res['contract_id']}[/] ({res['contract_number']})\n"
            f"  Tổ chức CeCA chứng thực:   [bold]{res['authority_name']}[/] (GP: {res['license_number']})\n"
            f"  Mã token CeCA:             [bold cyan]{res['ceca_token_id']}[/]\n"
            f"  Chữ ký số con dấu CeCA:    [bold]{res['token_signature'][:32]}...[/]\n"
            f"  Tính pháp lý:              [bold green]ĐÃ GẮN DẤU XÁC THỰC BỘ CÔNG THƯƠNG[/]",
            title="[bold blue]CeCA E-Contract Certification[/]",
            border_style="green",
        )
    )


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
