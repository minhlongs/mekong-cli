# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Notary, Legal Practice & Judicial Authentication Suite (Phase 89)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

notary_app = typer.Typer(name="notary", help="Vietnamese Notary, Legal Practice & Judicial Authentication Compliance Suite.")
console = Console()


@notary_app.callback(invoke_without_command=True)
def notary_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan hoạt động công chứng, luật sư và chứng thực tư pháp."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.notary_engine import NotaryEngine
    s = NotaryEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]HỆ THỐNG CÔNG CHỨNG, HÀNH NGHỀ LUẬT SƯ & CHỨNG THỰC TƯ PHÁP[/]\n\n"
        f"  Khung pháp lý:             [bold]{s['statutory_law']}[/]\n"
        f"  Hợp đồng công chứng:       [bold cyan]{s['approved_notarial_contracts']}/{s['total_notarial_contracts_executed']}[/] văn bản công chứng thành công\n"
        f"  Tài sản trong sổ ngăn chặn: [bold red]{s['active_blocked_assets_in_registry']}[/] bất động sản/tài sản bị phong tỏa giao dịch\n"
        f"  Hợp đồng dịch vụ pháp lý:   [bold yellow]{s['compliant_legal_agreements']}/{s['total_legal_agreements_audited']}[/] hợp đồng luật sư đạt chuẩn đạo đức nghề nghiệp\n"
        f"  Chứng thực bản sao & chữ ký:[bold magenta]{s['total_document_authentications']}[/] lượt chứng thực tại UBND/Tổ chức công chứng\n"
        f"  Tổng giá trị tài sản GD:   [bold green]{s['total_notarized_asset_value_vnd']:,.0f} VND[/] lưu trữ hồ sơ >= 20 năm",
        title="[bold green]Vietnam Notary, Legal Practice & Authentication Telemetry[/]", border_style="green",
    ))


@notary_app.command("contract")
def contract_cmd(
    title: str = typer.Argument(..., help="Tên hợp đồng, giao dịch yêu cầu công chứng"),
    office: str = typer.Option("Văn phòng Công chứng Sài Gòn", "--office", "-o", help="Tổ chức hành nghề công chứng"),
    notary_name: str = typer.Option("Nguyễn Văn Bình (CCV)", "--notary", "-n", help="Họ tên Công chứng viên"),
    party_a: str = typer.Option("Trần Minh Tuấn (Bên chuyển nhượng)", "--party-a", help="Bên A"),
    party_b: str = typer.Option("Lê Hoàng Oanh (Bên nhận chuyển nhượng)", "--party-b", help="Bên B"),
    contract_type: str = typer.Option("REAL_ESTATE_TRANSFER", "--type", "-t", help="Loại hợp đồng: REAL_ESTATE_TRANSFER, REAL_ESTATE_MORTGAGE, HOUSING_PURCHASE, INHERITANCE_DIVISION"),
    value: float = typer.Option(3_500_000_000.0, "--value", "-v", help="Giá trị giao dịch tài sản (VND)"),
    asset_id: str = typer.Option("GCN-QSDD-HCM-2026-001", "--asset-id", "-a", help="Mã định danh tài sản / Số Giấy chứng nhận QSDĐ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thực hiện công chứng hợp đồng, tra cứu cơ sở dữ liệu ngăn chặn và tính phí công chứng theo luật định."""
    from src.core.notary_engine import NotaryEngine
    res = NotaryEngine().notarize_contract(contract_title=title, notary_office=office, notary_public_name=notary_name, party_a=party_a, party_b=party_b, contract_type=contract_type, transaction_value_vnd=value, asset_id=asset_id)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_approved"] else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ THỰC HIỆN CÔNG CHỨNG HỢP ĐỒNG, GIAO DỊCH (LUẬT CÔNG CHỨNG 2014)[/]\n\n"
        f"  Số vào sổ công chứng:[bold cyan]{res['notary_book_number']}[/] | Hợp đồng: [bold]{res['contract_title']}[/]\n"
        f"  Tổ chức công chứng:  [white]{res['notary_office']}[/] | CCV: [yellow]{res['notary_public_name']}[/]\n"
        f"  Bên tham gia GD:     [white]Bên A:[/] {res['party_a']}  <-->  [white]Bên B:[/] {res['party_b']}\n"
        f"  Mã định danh tài sản:[cyan]{res['asset_id']}[/] ({res['contract_type']}) | Giá trị: [bold]{res['transaction_value_vnd']:,.0f} VND[/]\n"
        f"  Phí công chứng luật: [bold yellow]{res['statutory_notary_fee_vnd']:,.0f} VND[/] (TT 257/2016) | Bắt buộc CC: [bold]{'CÓ' if res['is_mandatory_notarization'] else 'Tự nguyện'}[/]\n"
        f"  Thời hạn lưu trữ:    [bold]Tối thiểu {res['archive_retention_years']} năm[/] | Trạng thái: [bold {color}]{res['status']}[/]\n"
        + (f"  Lý do từ chối/chặn:  [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Hậu kiểm ngăn chặn:  [bold green]Tài sản hợp pháp, không bị kê biên hoặc thế chấp trùng lặp[/]"),
        title=f"[bold {color}]Notarial Contract Certification[/]", border_style=color,
    ))


@notary_app.command("block")
def block_cmd(
    asset_id: str = typer.Argument(..., help="Mã định danh tài sản (Số sổ đỏ/sổ hồng hoặc số khung xe máy, ô tô)"),
    description: str = typer.Option("Quyền sử dụng đất tại Thửa 88, Tờ bản đồ số 12, P. Thảo Điền, TP. Thủ Đức", "--desc", "-d", help="Mô tả chi tiết tài sản"),
    reason: str = typer.Option("Kê biên tài sản bảo đảm thi hành án bản án dân sự phúc thẩm", "--reason", "-r", help="Lý do ngăn chặn giao dịch"),
    authority: str = typer.Option("Chi cục Thi hành án Dân sự TP. Thủ Đức", "--authority", help="Cơ quan có thẩm quyền yêu cầu ngăn chặn"),
    unblock: bool = typer.Option(False, "--unblock", help="Giải tỏa ngăn chặn giao dịch tài sản"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Quản lý danh sách tài sản ngăn chặn giao dịch trong Cơ sở dữ liệu công chứng (Điều 62 Luật Công chứng)."""
    from src.core.notary_engine import NotaryEngine
    res = NotaryEngine().manage_blocked_asset(asset_id=asset_id, asset_description=description, block_reason=reason, blocking_authority=authority, is_blocked=not unblock)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "red" if res["is_blocked"] else "green"
    console.print(Panel(
        f"[bold {color}]CẬP NHẬT CƠ SỞ DỮ LIỆU NGĂN CHẶN CÔNG CHỨNG GIAO DỊCH (ĐIỀU 62)[/]\n\n"
        f"  Mã tài sản: [bold cyan]{res['asset_id']}[/] | Hành động: [bold {color}]{res['action']}[/]\n"
        f"  Lý do phong tỏa: [white]{res['block_reason']}[/] | Cơ quan yêu cầu: [yellow]{res['blocking_authority']}[/]\n"
        f"  Kết luận: [bold]{res['summary']}[/]",
        title=f"[bold {color}]Notarial Blocked Asset Database[/]", border_style=color,
    ))


@notary_app.command("lawyer")
def lawyer_cmd(
    firm: str = typer.Argument(..., help="Tên tổ chức hành nghề luật sư"),
    attorney: str = typer.Option("LS. Phạm Quốc Toàn", "--attorney", "-a", help="Họ tên Luật sư phụ trách"),
    bar_card: str = typer.Option("LS-HN-2024-8899", "--card", "-c", help="Số Thẻ Luật sư"),
    client: str = typer.Option("Tập đoàn Công nghệ Alpha", "--client", help="Tên khách hàng / thân chủ"),
    matter: str = typer.Option("Đại diện tranh chấp hợp đồng mua bán cổ phần", "--matter", "-m", help="Nội dung vụ việc pháp lý"),
    fee: float = typer.Option(80_000_000.0, "--fee", "-f", help="Mức thù lao luật sư theo hợp đồng (VND)"),
    conflict: bool = typer.Option(False, "--conflict/--no-conflict", help="Có xung đột lợi ích giữa các bên trong cùng vụ việc"),
    insurance: bool = typer.Option(True, "--insurance/--no-insurance", help="Đã mua bảo hiểm trách nhiệm nghề nghiệp luật sư"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định hợp đồng dịch vụ pháp lý và tuân thủ quy tắc đạo đức nghề nghiệp luật sư (Luật Luật sư)."""
    from src.core.notary_engine import NotaryEngine
    res = NotaryEngine().audit_legal_practice_agreement(law_firm_name=firm, attorney_name=attorney, bar_card_number=bar_card, client_name=client, legal_matter=matter, fee_vnd=fee, has_conflict_of_interest=conflict, has_professional_insurance=insurance)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_compliant"] else "red"
    console.print(Panel(
        f"[bold {color}]THẨM ĐỊNH HỢP ĐỒNG DỊCH VỤ PHÁP LÝ & ĐẠO ĐỨC NGHỀ NGHIỆP LUẬT SƯ[/]\n\n"
        f"  Mã hợp đồng: [bold cyan]{res['agreement_code']}[/] | Tổ chức hành nghề: [bold]{res['law_firm_name']}[/]\n"
        f"  Luật sư đảm nhiệm: [yellow]{res['attorney_name']}[/] (Thẻ LS: [cyan]{res['bar_card_number']}[/]) | Thân chủ: [white]{res['client_name']}[/]\n"
        f"  Vụ việc pháp lý: [white]{res['legal_matter']}[/] | Thù lao: [bold green]{res['fee_vnd']:,.0f} VND[/]\n"
        f"  Bảo hiểm nghề nghiệp: [bold]{'ĐÃ MUA' if res['has_professional_insurance'] else 'CHƯA MUA'}[/] | Xung đột lợi ích: [bold {color}]{'CÓ XUNG ĐỘT' if res['has_conflict_of_interest'] else 'KHÔNG CÓ'}[/]\n"
        f"  Kết luận: [bold {color}]{res['status']}[/]\n"
        + (f"  Vi phạm: [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá: [bold green]Hợp đồng dịch vụ pháp lý tuân thủ đầy đủ Luật Luật sư[/]"),
        title=f"[bold {color}]Legal Practice Compliance Evaluation[/]", border_style=color,
    ))


@notary_app.command("auth")
def auth_cmd(
    title: str = typer.Argument(..., help="Tên văn bản, giấy tờ yêu cầu chứng thực"),
    auth_type: str = typer.Option("COPY_AUTHENTICATION", "--type", "-t", help="Loại chứng thực: COPY_AUTHENTICATION, SIGNATURE_AUTHENTICATION"),
    body: str = typer.Option("UBND Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh", "--body", "-b", help="Cơ quan thực hiện chứng thực"),
    copies: int = typer.Option(5, "--copies", "-c", help="Số bản yêu cầu chứng thực"),
    valid: bool = typer.Option(True, "--valid/--invalid", help="Bản chính nguyên vẹn, hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Chứng thực bản sao từ bản chính hoặc chứng thực chữ ký cá nhân theo Nghị định 23/2015/NĐ-CP."""
    from src.core.notary_engine import NotaryEngine
    res = NotaryEngine().authenticate_document(document_title=title, auth_type=auth_type, authenticating_body=body, number_of_copies=copies, is_original_valid=valid)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["status"] == "AUTHENTICATED_COMPLIANT" else "red"
    console.print(Panel(
        f"[bold {color}]CHỨNG THỰC BẢN SAO / CHỮ KÝ (NGHỊ ĐỊNH SỐ 23/2015/NĐ-CP)[/]\n\n"
        f"  Mã chứng thực: [bold cyan]{res['auth_code']}[/] | Văn bản: [bold]{res['document_title']}[/] ({res['auth_type']})\n"
        f"  Cơ quan chứng thực: [white]{res['authenticating_body']}[/] | Số bản: [yellow]{res['number_of_copies']}[/] bản | Lệ phí: [bold green]{res['statutory_fee_vnd']:,.0f} VND[/]\n"
        f"  Bản chính hợp lệ: [bold]{'HỢP LỆ' if res['is_original_valid'] else 'KHÔNG HỢP LỆ'}[/] | Trạng thái: [bold {color}]{res['status']}[/] ({res['legal_conclusion']})",
        title=f"[bold {color}]Document Authentication & Attestation[/]", border_style=color,
    ))


@notary_app.command("list")
def list_records_cmd(category: str = typer.Argument("contracts", help="Danh mục: contracts, blocked, agreements, authentications"), limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON")) -> None:
    """Tra cứu danh mục hợp đồng công chứng, tài sản bị ngăn chặn, hợp đồng luật sư hoặc chứng thực."""
    from src.core.notary_engine import NotaryEngine
    records = NotaryEngine().list_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    table = Table(title=f"Danh mục hồ sơ công chứng & bổ trợ tư pháp [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["blocked", "blocked_assets", "ngan_chan"]:
        for col, st in (("Mã tài sản", "bold cyan"), ("Mô tả", "white"), ("Lý do ngăn chặn", "red"), ("Cơ quan yêu cầu", "yellow"), ("Thời điểm", "white")):
            table.add_column(col, style=st)
        for r in records:
            table.add_row(r.get("asset_id", ""), r.get("asset_description", ""), r.get("block_reason", ""), r.get("blocking_authority", ""), r.get("created_at", "")[:19])
    elif category in ["agreements", "law_firms", "luat_su"]:
        for col, st in (("Mã HĐ", "bold cyan"), ("Tổ chức LS", "white"), ("Luật sư", "yellow"), ("Thân chủ", "magenta"), ("Thù lao", "green"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            c = "green" if r.get("is_compliant") else "red"
            table.add_row(r.get("agreement_code", ""), r.get("law_firm_name", ""), r.get("attorney_name", ""), r.get("client_name", ""), f"{r.get('fee_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")
    elif category in ["authentications", "copies", "chung_thuc"]:
        for col, st in (("Mã CT", "bold cyan"), ("Tên văn bản", "white"), ("Loại", "yellow"), ("Cơ quan", "magenta"), ("Số bản", "white"), ("Lệ phí", "green"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            c = "green" if r.get("status") == "AUTHENTICATED_COMPLIANT" else "red"
            table.add_row(r.get("auth_code", ""), r.get("document_title", ""), r.get("auth_type", ""), r.get("authenticating_body", ""), str(r.get("number_of_copies", 0)), f"{r.get('statutory_fee_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")
    else:
        for col, st in (("Số sổ CC", "bold cyan"), ("Tên hợp đồng", "white"), ("Loại HĐ", "yellow"), ("Mã tài sản", "magenta"), ("Giá trị GD", "green"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            c = "green" if r.get("is_approved") else "red"
            table.add_row(r.get("notary_book_number", ""), r.get("contract_title", ""), r.get("contract_type", ""), r.get("asset_id", ""), f"{r.get('transaction_value_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")
    console.print(table)


@notary_app.command("status")
def status_cmd(json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hoạt động công chứng, luật sư và chứng thực."""
    from src.core.notary_engine import NotaryEngine
    typer.echo(json.dumps(NotaryEngine().get_status(), indent=2, ensure_ascii=False))
