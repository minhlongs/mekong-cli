# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 117: Electronic Contracts & CeCA Certification CLI commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.panel import Panel

from src.cli.commands._etransaction_msg_cmds import console, etransaction_app


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
