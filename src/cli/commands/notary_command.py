# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Notary, Legal Practice & Judicial Authentication Suite (Phase 89)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

notary_app = typer.Typer(
    name="notary",
    help="Vietnamese Notary, Legal Practice & Judicial Authentication Compliance Suite.",
)
console = Console()


@notary_app.callback(invoke_without_command=True)
def notary_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động công chứng, luật sư và chứng thực tư pháp."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.notary_engine import NotaryEngine

    engine = NotaryEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG CÔNG CHỨNG, HÀNH NGHỀ LUẬT SƯ & CHỨNG THỰC TƯ PHÁP[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['statutory_law']}[/]\n"
            f"  Hợp đồng công chứng:       [bold cyan]{status_data['approved_notarial_contracts']}/{status_data['total_notarial_contracts_executed']}[/] văn bản công chứng thành công\n"
            f"  Tài sản trong sổ ngăn chặn: [bold red]{status_data['active_blocked_assets_in_registry']}[/] bất động sản/tài sản bị phong tỏa giao dịch\n"
            f"  Hợp đồng dịch vụ pháp lý:   [bold yellow]{status_data['compliant_legal_agreements']}/{status_data['total_legal_agreements_audited']}[/] hợp đồng luật sư đạt chuẩn đạo đức nghề nghiệp\n"
            f"  Chứng thực bản sao & chữ ký:[bold magenta]{status_data['total_document_authentications']}[/] lượt chứng thực tại UBND/Tổ chức công chứng\n"
            f"  Tổng giá trị tài sản GD:   [bold green]{status_data['total_notarized_asset_value_vnd']:,.0f} VND[/] lưu trữ hồ sơ >= 20 năm",
            title="[bold green]Vietnam Notary, Legal Practice & Authentication Telemetry[/]",
            border_style="green",
        )
    )


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

    engine = NotaryEngine()
    res = engine.notarize_contract(
        contract_title=title,
        notary_office=office,
        notary_public_name=notary_name,
        party_a=party_a,
        party_b=party_b,
        contract_type=contract_type,
        transaction_value_vnd=value,
        asset_id=asset_id,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_appr = res["is_approved"]
    color = "green" if is_appr else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THỰC HIỆN CÔNG CHỨNG HỢP ĐỒNG, GIAO DỊCH (LUẬT CÔNG CHỨNG 2014)[/]\n\n"
            f"  Số vào sổ công chứng:[bold cyan]{res['notary_book_number']}[/]\n"
            f"  Tên hợp đồng:        [bold]{res['contract_title']}[/]\n"
            f"  Tổ chức công chứng:  [white]{res['notary_office']}[/] | CCV: [yellow]{res['notary_public_name']}[/]\n"
            f"  Bên tham gia GD:     [white]Bên A:[/] {res['party_a']}  <-->  [white]Bên B:[/] {res['party_b']}\n"
            f"  Mã định danh tài sản:[cyan]{res['asset_id']}[/] (Loại: [bold]{res['contract_type']}[/])\n"
            f"  Giá trị giao dịch:   [bold]{res['transaction_value_vnd']:,.0f} VND[/]\n"
            f"  Phí công chứng luật: [bold yellow]{res['statutory_notary_fee_vnd']:,.0f} VND[/] (Thông tư 257/2016/TT-BTC)\n"
            f"  Bắt buộc công chứng: [bold]{'CÓ (Theo Luật Đất đai / Nhà ở)' if res['is_mandatory_notarization'] else 'KHÔNG (Tự nguyện)'}[/]\n"
            f"  Thời hạn lưu trữ:    [bold]Tối thiểu {res['archive_retention_years']} năm (Bản chính lưu trữ vĩnh viễn)[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            + (f"  Lý do từ chối/chặn:  [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Hậu kiểm ngăn chặn:  [bold green]Tài sản hợp pháp, không bị kê biên hoặc thế chấp trùng lặp[/]"),
            title=f"[bold {color}]Notarial Contract Certification[/]",
            border_style=color,
        )
    )


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

    engine = NotaryEngine()
    res = engine.manage_blocked_asset(
        asset_id=asset_id,
        asset_description=description,
        block_reason=reason,
        blocking_authority=authority,
        is_blocked=not unblock,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    color = "red" if res["is_blocked"] else "green"
    console.print(
        Panel(
            f"[bold {color}]CẬP NHẬT CƠ SỞ DỮ LIỆU NGĂN CHẶN CÔNG CHỨNG GIAO DỊCH (ĐIỀU 62)[/]\n\n"
            f"  Mã tài sản:          [bold cyan]{res['asset_id']}[/]\n"
            f"  Hành động:           [bold {color}]{res['action']}[/]\n"
            f"  Lý do phong tỏa:     [white]{res['block_reason']}[/]\n"
            f"  Cơ quan yêu cầu:     [yellow]{res['blocking_authority']}[/]\n"
            f"  Kết luận:            [bold]{res['summary']}[/]",
            title=f"[bold {color}]Notarial Blocked Asset Database[/]",
            border_style=color,
        )
    )


@notary_app.command("lawyer")
def lawyer_cmd(
    firm: str = typer.Argument(..., help="Tên tổ chức hành nghề luật sư (Văn phòng Luật sư / Công ty Luật)"),
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

    engine = NotaryEngine()
    res = engine.audit_legal_practice_agreement(
        law_firm_name=firm,
        attorney_name=attorney,
        bar_card_number=bar_card,
        client_name=client,
        legal_matter=matter,
        fee_vnd=fee,
        has_conflict_of_interest=conflict,
        has_professional_insurance=insurance,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_comp = res["is_compliant"]
    color = "green" if is_comp else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH HỢP ĐỒNG DỊCH VỤ PHÁP LÝ & ĐẠO ĐỨC NGHỀ NGHIỆP LUẬT SƯ[/]\n\n"
            f"  Mã hợp đồng:         [bold cyan]{res['agreement_code']}[/]\n"
            f"  Tổ chức hành nghề:   [bold]{res['law_firm_name']}[/]\n"
            f"  Luật sư đảm nhiệm:   [yellow]{res['attorney_name']}[/] (Thẻ LS: [cyan]{res['bar_card_number']}[/])\n"
            f"  Khách hàng/Thân chủ: [white]{res['client_name']}[/]\n"
            f"  Vụ việc pháp lý:     [white]{res['legal_matter']}[/]\n"
            f"  Thù lao dịch vụ:     [bold green]{res['fee_vnd']:,.0f} VND[/]\n"
            f"  Bảo hiểm nghề nghiệp:[bold]{'ĐÃ MUA' if res['has_professional_insurance'] else 'CHƯA MUA (Vi phạm quy định)'}[/]\n"
            f"  Xung đột lợi ích:    [bold {color}]{'CÓ XUNG ĐỘT (Vi phạm Điều 9 Luật Luật sư)' if res['has_conflict_of_interest'] else 'KHÔNG CÓ XUNG ĐỘT'}[/]\n"
            f"  Kết luận:            [bold {color}]{res['status']}[/]\n"
            + (f"  Vi phạm:             [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:            [bold green]Hợp đồng dịch vụ pháp lý tuân thủ đầy đủ Luật Luật sư[/]"),
            title=f"[bold {color}]Legal Practice Compliance Evaluation[/]",
            border_style=color,
        )
    )


@notary_app.command("auth")
def auth_cmd(
    title: str = typer.Argument(..., help="Tên văn bản, giấy tờ yêu cầu chứng thực"),
    auth_type: str = typer.Option("COPY_AUTHENTICATION", "--type", "-t", help="Loại chứng thực: COPY_AUTHENTICATION (bản sao), SIGNATURE_AUTHENTICATION (chữ ký)"),
    body: str = typer.Option("UBND Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh", "--body", "-b", help="Cơ quan thực hiện chứng thực"),
    copies: int = typer.Option(5, "--copies", "-c", help="Số bản yêu cầu chứng thực"),
    valid: bool = typer.Option(True, "--valid/--invalid", help="Bản chính nguyên vẹn, hợp lệ, không có dấu hiệu tẩy xóa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Chứng thực bản sao từ bản chính hoặc chứng thực chữ ký cá nhân theo Nghị định 23/2015/NĐ-CP."""
    from src.core.notary_engine import NotaryEngine

    engine = NotaryEngine()
    res = engine.authenticate_document(
        document_title=title,
        auth_type=auth_type,
        authenticating_body=body,
        number_of_copies=copies,
        is_original_valid=valid,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["status"] == "AUTHENTICATED_COMPLIANT"
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]CHỨNG THỰC BẢN SAO / CHỮ KÝ (NGHỊ ĐỊNH SỐ 23/2015/NĐ-CP)[/]\n\n"
            f"  Mã chứng thực:       [bold cyan]{res['auth_code']}[/]\n"
            f"  Tên văn bản:         [bold]{res['document_title']}[/]\n"
            f"  Loại chứng thực:     [cyan]{res['auth_type']}[/]\n"
            f"  Cơ quan chứng thực:  [white]{res['authenticating_body']}[/]\n"
            f"  Số bản chứng thực:   [yellow]{res['number_of_copies']}[/] bản\n"
            f"  Bản chính hợp lệ:    [bold]{'HỢP LỆ' if res['is_original_valid'] else 'BỊ TẨY XÓA / KHÔNG HỢP LỆ'}[/]\n"
            f"  Lệ phí chứng thực:   [bold green]{res['statutory_fee_vnd']:,.0f} VND[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            f"  Kết luận:            [bold]{res['legal_conclusion']}[/]",
            title=f"[bold {color}]Document Authentication & Attestation[/]",
            border_style=color,
        )
    )


@notary_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("contracts", help="Danh mục: contracts, blocked, agreements, authentications"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hợp đồng công chứng, tài sản bị ngăn chặn, hợp đồng luật sư hoặc chứng thực."""
    from src.core.notary_engine import NotaryEngine

    engine = NotaryEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ công chứng & bổ trợ tư pháp [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["blocked", "blocked_assets", "ngan_chan"]:
        table.add_column("Mã tài sản", style="bold cyan")
        table.add_column("Mô tả", style="white")
        table.add_column("Lý do ngăn chặn", style="red")
        table.add_column("Cơ quan yêu cầu", style="yellow")
        table.add_column("Thời điểm", style="white")
        for r in records:
            table.add_row(r.get("asset_id", ""), r.get("asset_description", ""), r.get("block_reason", ""), r.get("blocking_authority", ""), r.get("created_at", "")[:19])
    elif category in ["agreements", "law_firms", "luat_su"]:
        table.add_column("Mã HĐ", style="bold cyan")
        table.add_column("Tổ chức LS", style="white")
        table.add_column("Luật sư", style="yellow")
        table.add_column("Thân chủ", style="magenta")
        table.add_column("Thù lao", style="green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_compliant") else "red"
            table.add_row(r.get("agreement_code", ""), r.get("law_firm_name", ""), r.get("attorney_name", ""), r.get("client_name", ""), f"{r.get('fee_vnd', 0):,.0f} VND", f"[{color}]{r.get('status', '')}[/]")
    elif category in ["authentications", "copies", "chung_thuc"]:
        table.add_column("Mã CT", style="bold cyan")
        table.add_column("Tên văn bản", style="white")
        table.add_column("Loại", style="yellow")
        table.add_column("Cơ quan", style="magenta")
        table.add_column("Số bản", style="white")
        table.add_column("Lệ phí", style="green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "AUTHENTICATED_COMPLIANT" else "red"
            table.add_row(r.get("auth_code", ""), r.get("document_title", ""), r.get("auth_type", ""), r.get("authenticating_body", ""), str(r.get("number_of_copies", 0)), f"{r.get('statutory_fee_vnd', 0):,.0f} VND", f"[{color}]{r.get('status', '')}[/]")
    else:
        table.add_column("Số sổ CC", style="bold cyan")
        table.add_column("Tên hợp đồng", style="white")
        table.add_column("Loại HĐ", style="yellow")
        table.add_column("Mã tài sản", style="magenta")
        table.add_column("Giá trị GD", style="green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_approved") else "red"
            table.add_row(r.get("notary_book_number", ""), r.get("contract_title", ""), r.get("contract_type", ""), r.get("asset_id", ""), f"{r.get('transaction_value_vnd', 0):,.0f} VND", f"[{color}]{r.get('status', '')}[/]")

    console.print(table)


@notary_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hoạt động công chứng, luật sư và chứng thực."""
    from src.core.notary_engine import NotaryEngine

    engine = NotaryEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
