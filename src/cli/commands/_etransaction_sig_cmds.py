# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 117: Electronic Signatures, PKI Verification & Trust Tokens CLI commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.panel import Panel

from src.cli.commands._etransaction_msg_cmds import console, etransaction_app


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
