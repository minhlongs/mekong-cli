# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Commercial Contract, E-Sign & Legal Risk Assessment Engine (Phase 51)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
contract_app = typer.Typer(name="contract", help="Commercial Contracts, E-Signatures & Legal Risk Assessment under Vietnamese Law", add_completion=False)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@contract_app.callback(invoke_without_command=True)
def contract_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON")) -> None:
    """Hệ thống Quản trị Hợp đồng Thương mại, Thẩm định Rủi ro Pháp lý & Ký số Điện tử."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.contract_engine import ContractEngine
    status_data = ContractEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]HỆ THỐNG SOẠN THẢO, THẨM ĐỊNH RỦI RO & KÝ SỐ HỢP ĐỒNG THƯƠNG MẠI[/]\n\n"
        f"  Khung pháp lý cốt lõi:  [bold]{status_data['regulatory_framework']}[/]\n"
        f"  Mẫu hợp đồng chuẩn:    [bold cyan]{', '.join(status_data['available_templates'])}[/]\n"
        f"  Tổng số hợp đồng:      [bold]{m['total_contracts']} văn kiện[/] (Tổng giá trị: [bold green]{_format_vnd(m['total_contract_value_vnd'])}[/])\n"
        f"  Trạng thái thực hiện:   [bold green]{m['signed_contracts']} Đã ký số[/] | [bold yellow]{m['drafted_contracts']} Bản thảo[/]\n"
        f"  Phân tầng rủi ro:       [bold red]{m['high_risk_contracts']} Rủi ro cao[/] | [bold yellow]{m['medium_risk_contracts']} Rủi ro vừa[/] | [bold green]{m['low_risk_contracts']} Rủi ro thấp[/]\n"
        f"  Chứng thư ký số cấp:   [bold magenta]{m['e_signatures_issued']} chữ ký điện tử an toàn (TSA SHA-256)[/]",
        title="[bold blue]Commercial Contract Operations & Legal Risk Dashboard[/]", border_style="green",
    ))


@contract_app.command("draft")
def draft_contract_cmd(
    template: str = typer.Argument(..., help="Loại mẫu hợp đồng (SOFTWARE_DEV, COMMERCIAL_SALE, NDA, DISTRIBUTION)"),
    party_a: str = typer.Argument(..., help="Tên Bên A (Bên giao việc / Mua hàng)"),
    party_b: str = typer.Argument(..., help="Tên Bên B (Bên cung cấp / Bán hàng)"),
    value_vnd: float = typer.Option(0.0, "--value", "-v", help="Tổng giá trị hợp đồng (VND)"),
    party_a_tax_id: str = typer.Option("0100000001", "--tax-a", help="Mã số thuế Bên A"),
    party_b_tax_id: str = typer.Option("0300000002", "--tax-b", help="Mã số thuế Bên B"),
    scope: str = typer.Option("", "--scope", "-s", help="Mô tả tóm tắt phạm vi công việc / giao dịch"),
    penalty_pct: float = typer.Option(8.0, "--penalty", "-p", help="Mức phạt vi phạm % (Tối đa 8% theo Điều 301 Luật Thương mại)"),
    dispute: str = typer.Option("VIAC", "--dispute", "-d", help="Cơ quan tài phán giải quyết tranh chấp (VIAC hoặc Tòa án)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soạn thảo hợp đồng thương mại chuẩn hóa tuân thủ Luật Thương mại 2005 & Bộ luật Dân sự 2015."""
    from src.core.contract_engine import ContractEngine
    result = ContractEngine().draft_contract(template_type=template, party_a_name=party_a, party_b_name=party_b, contract_value_vnd=value_vnd, party_a_tax_id=party_a_tax_id, party_b_tax_id=party_b_tax_id, scope_summary=scope, penalty_rate_pct=penalty_pct, dispute_forum=dispute)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if not result.get("ok"):
        console.print(f"[bold red]Lỗi soạn thảo:[/] {result.get('error')}")
        return
    rk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}.get(result["risk_level"], "white")
    console.print(Panel(
        f"[bold cyan]ĐÃ KHỞI TẠO HỢP ĐỒNG THƯƠNG MẠI: {result['contract_number']}[/]\n\n"
        f"  Tiêu đề:              [bold]{result['title']}[/] | Mã HĐ: [bold yellow]{result['contract_id']}[/]\n"
        f"  Chủ thể giao kết:     Bên A: [bold]{result['party_a_name']}[/] (MST: {result['party_a_tax_id']}) | Bên B: [bold]{result['party_b_name']}[/] (MST: {result['party_b_tax_id']})\n"
        f"  Giá trị hợp đồng:     [bold green]{_format_vnd(result['contract_value_vnd'])}[/] | Phạt vi phạm: [bold]{result['penalty_rate_pct']}%[/] (Trần: 8.0%)\n"
        f"  Cơ quan tài phán:     [bold]{result['dispute_forum']}[/] | Mã băm: {result['content_sha256'][:24]}...\n"
        f"  Đánh giá rủi ro:      Điểm: [bold {rk_color}]{result['risk_score']}/100[/] ([bold {rk_color}]{result['risk_level']}[/]) | Trạng thái: [bold green]{result['status']}[/]",
        title="[bold blue]Commercial Contract Drafted Successfully[/]", border_style="cyan",
    ))


@contract_app.command("risk-check")
def risk_check_cmd(text: str = typer.Argument(..., help="Nội dung điều khoản hợp đồng cần quét rủi ro"), penalty_pct: float = typer.Option(None, "--penalty", "-p", help="Tỷ lệ phạt vi phạm thỏa thuận trong hợp đồng"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Quét và thẩm định các điều khoản vi phạm pháp luật."""
    from src.core.contract_engine import ContractEngine
    result = ContractEngine().assess_contract_risk(contract_text=text, penalty_pct=penalty_pct)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    rk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}.get(result["risk_level"], "white")
    flags_text = "".join(f"\n    {idx}. [{rf['severity']}] [bold]{rf['clause']}[/]: {rf['issue']}\n       -> Căn cứ: {rf['legal_basis']}" for idx, rf in enumerate(result["red_flags"], 1))
    recs_text = "".join(f"\n    {idx}. {rec}" for idx, rec in enumerate(result["recommendations"], 1))
    console.print(Panel(
        f"[bold {rk_color}]KẾT QUẢ THẨM ĐỊNH RỦI RO PHÁP LÝ HỢP ĐỒNG[/]\n\n"
        f"  Chỉ số rủi ro:       [bold {rk_color}]{result['risk_score']}/100[/] ([bold {rk_color}]{result['risk_level']}[/])\n"
        f"  Đánh giá luật định:  {result['statutory_eval']}\n"
        f"  Cảnh báo đỏ ({result['red_flags_count']}):{flags_text or ' Không phát hiện điều khoản vi phạm nghiêm trọng.'}\n\n"
        f"  Kiến nghị điều chỉnh:{recs_text or ' Không có kiến nghị sửa đổi.'}",
        title="[bold blue]Legal Risk & Redline Assessment[/]", border_style=rk_color,
    ))


@contract_app.command("sign")
def sign_contract_cmd(
    contract_id: str = typer.Argument(..., help="Mã hợp đồng (contract_id hoặc contract_number)"),
    signer_name: str = typer.Argument(..., help="Họ và tên người ký"),
    title: str = typer.Option("Giám đốc điều hành", "--title", "-t", help="Chức danh người ký"),
    tax_id: str = typer.Option("0100000001", "--tax", help="Mã số thuế doanh nghiệp ký kết"),
    org: str = typer.Option("", "--org", "-o", help="Tên tổ chức doanh nghiệp"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Ký số điện tử an toàn cho hợp đồng theo Luật Giao dịch điện tử 2023 & Nghị định 130/2018/NĐ-CP."""
    from src.core.contract_engine import ContractEngine
    result = ContractEngine().sign_contract(contract_id=contract_id, signer_name=signer_name, signer_title=title, signer_tax_id=tax_id, organization_name=org)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if not result.get("ok"):
        console.print(f"[bold red]Lỗi ký số:[/] {result.get('error')}")
        return
    console.print(Panel(
        f"[bold green]CHỨNG THỰC KÝ SỐ ĐIỆN TỬ AN TOÀN THÀNH CÔNG: {result['signature_id']}[/]\n\n"
        f"  Hợp đồng số:         [bold cyan]{result['contract_number']}[/] (ID: {result['contract_id']})\n"
        f"  Người ký đại diện:   [bold]{result['signer_name']}[/] - [bold]{result['signer_title']}[/] ({result['organization_name']} - MST: {result['signer_tax_id']})\n"
        f"  Dấu thời gian TSA:   [bold yellow]{result['tsa_timestamp']}[/] | Mã băm: [bold green]{result['signature_hash']}[/]\n"
        f"  Hiệu lực pháp lý:    {result['legal_status']} ({result['statutory_basis']})",
        title="[bold green]E-Signature Certified (TSA SHA-256)[/]", border_style="green",
    ))


@contract_app.command("verify")
def verify_signature_cmd(signature_id: str = typer.Argument(..., help="Mã chữ ký số hoặc mã băm chữ ký"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Xác minh tính xác thực, tính toàn vẹn dữ liệu và dấu thời gian của chữ ký số điện tử."""
    from src.core.contract_engine import ContractEngine
    result = ContractEngine().verify_signature(signature_id=signature_id)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if not result.get("ok"):
        console.print(f"[bold red]Lỗi kiểm tra:[/] {result.get('error')}")
        return
    sc = "green" if result["is_valid"] else "red"
    console.print(Panel(
        f"[bold {sc}]KẾT QUẢ XÁC MINH CHỮ KÝ ĐIỆN TỬ: {result['signature_id']}[/]\n\n"
        f"  Hợp đồng liên quan:  [bold]{result['contract_number']}[/] | Chủ thể ký: [bold]{result['signer_name']}[/] ({result['signer_title']} - MST: {result['signer_tax_id']})\n"
        f"  Dấu thời gian TSA:   {result['tsa_timestamp']}\n"
        f"  Tính toàn vẹn (Hash):{'[bold green]NGUYÊN VẸN (KHÔNG BỊ SỬA ĐỔI)[/]' if result['integrity_verified'] else '[bold red]BỊ SỬA ĐỔI HOẶC SAI DỮ LIỆU[/]'}\n"
        f"  Kết luận pháp lý:    [bold {sc}]{result['statutory_validity']}[/]",
        title="[bold blue]E-Signature Cryptographic Verification[/]", border_style=sc,
    ))


@contract_app.command("list")
def list_contracts_cmd(status: str = typer.Option("ALL", "--status", "-s", help="Bộ lọc trạng thái (ALL, DRAFTED, SIGNED)"), limit: int = typer.Option(20, "--limit", "-l", help="Số lượng hợp đồng hiển thị"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Truy vấn danh mục hợp đồng thương mại và trạng thái ký kết."""
    from src.core.contract_engine import ContractEngine
    contracts = ContractEngine().list_contracts(status=status, limit=limit)
    if json_mode:
        typer.echo(json.dumps({"contracts": contracts, "total": len(contracts)}, indent=2, ensure_ascii=False))
        return
    table = Table(title="Danh Mục Hợp Đồng Thương Mại Doanh Nghiệp", border_style="cyan")
    for col, st in (("Mã HĐ", "cyan"), ("Số HĐ", "bold"), ("Loại mẫu", "green"), ("Bên A", "white"), ("Bên B", "white"), ("Giá trị (VND)", "yellow"), ("Rủi ro", "magenta"), ("Trạng thái", "")):
        table.add_column(col, style=st)
    for c in contracts:
        table.add_row(c["contract_id"], c["contract_number"], c["template_type"], c["party_a_name"], c["party_b_name"], _format_vnd(c["contract_value_vnd"]), f"{c['risk_level']} ({c['risk_score']})", c["status"])
    console.print(table)


@contract_app.command("status")
def contract_status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON")) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu hợp đồng thương mại và chứng thư ký số."""
    from src.core.contract_engine import ContractEngine
    s = ContractEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    m = s["metrics"]
    console.print(Panel(
        f"[bold green]THÔNG SỐ QUẢN TRỊ HỢP ĐỒNG THƯƠNG MẠI & KÝ SỐ[/]\n\n"
        f"  Trạng thái: {s['status'].upper()} | Khung pháp luật: {s['regulatory_framework']}\n"
        f"  Mẫu hợp đồng hỗ trợ: {', '.join(s['available_templates'])}\n"
        f"  Tổng hợp đồng: {m['total_contracts']} (Đã ký số: {m['signed_contracts']} | Đang soạn: {m['drafted_contracts']})\n"
        f"  Phân loại rủi ro: Cao: {m['high_risk_contracts']} | Vừa: {m['medium_risk_contracts']} | Thấp: {m['low_risk_contracts']}\n"
        f"  Chữ ký điện tử đã cấp: {m['e_signatures_issued']} | Cơ sở dữ liệu: {s['database']}",
        title="[bold blue]Contract Engine Telemetry[/]", border_style="green",
    ))
