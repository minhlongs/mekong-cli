# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite (Phase 111)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

forensic_app = typer.Typer(name="forensic", help="Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite.")
console = Console()


def _engine():
    from src.core.forensic_engine import ForensicEngine
    return ForensicEngine()


@forensic_app.callback(invoke_without_command=True)
def forensic_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan hoạt động Giám định tư pháp, kết luận giám định và bảo toàn chuỗi chứng cứ điện tử."""
    if ctx.invoked_subcommand is not None:
        return
    t = _engine().get_forensic_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold blue]HỆ THỐNG GIÁM ĐỊNH TƯ PHÁP, CHỨNG CỨ ĐIỆN TỬ & KỸ THUẬT HÌNH SỰ[/]\n\n"
        f"  Khung pháp lý & Chế tài:   [bold]Luật Giám định tư pháp 2012 (sửa đổi 2020) & BLTTHS 2015[/] ([bold yellow]Điều 382 BLHS 2015[/])\n"
        f"  Giám định viên tư pháp:    [bold]{t['total_experts']}[/] chuyên gia ([bold green]{t['certified_experts']}[/] đủ chuẩn) | Trưng cầu: [bold]{t['total_requisitions']}[/] ([bold yellow]{t['total_estimated_fees_vnd']:,.0f} VND[/])\n"
        f"  Kết luận & Bảo quản CC:    [bold]{t['total_conclusions']}[/] ([bold green]{t['valid_conclusions']}[/] hợp chuẩn Điều 32 — [bold green]{t['validity_rate_pct']}%[/]) | [bold]{t['total_custody_records']}[/] vật chứng ([bold green]{t['admissible_evidence_records']}[/] hợp lệ)",
        title="[bold blue]Vietnam Judicial Expertise & Forensic Telemetry[/]", border_style="blue",
    ))


@forensic_app.command("expert")
def expert_cmd(
    name: str = typer.Argument(..., help="Họ và tên Giám định viên tư pháp"),
    domain: str = typer.Option("DIGITAL_EVIDENCE", "--domain", "-d", help="Lĩnh vực: FINANCIAL_ACCOUNTING, DIGITAL_EVIDENCE, CONSTRUCTION_QUALITY, INTELLECTUAL_PROPERTY, DOCUMENT_SIGNATURE"),
    degree: str = typer.Option("Kỹ sư An toàn Thông tin / Thạc sĩ KHMT", "--degree", help="Văn bằng chuyên môn đào tạo"),
    exp: int = typer.Option(7, "--exp", "-e", help="Số năm kinh nghiệm thực tế (luật định >= 5 năm theo Điều 7)"),
    card: str = typer.Option("GĐTP-08/2023/BTP", "--card", "-c", help="Số thẻ giám định viên tư pháp hoặc quyết định bổ nhiệm"),
    authority: str = typer.Option("Bộ Tư pháp", "--authority", "-a", help="Cơ quan có thẩm quyền bổ nhiệm/cấp thẻ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký và thẩm tra hồ sơ Giám định viên tư pháp theo Điều 7 Luật Giám định tư pháp."""
    r = _engine().register_judicial_expert(name, domain, degree, exp, card, authority)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_certified"] else "red"
    exp_tag = "[green]Đạt chuẩn >= 5 năm[/]" if r["years_experience"] >= 5 else "[red]Chưa đủ thâm niên[/]"
    console.print(Panel(
        f"[bold]Mã số GĐV & Họ tên:[/] [cyan]{r['expert_id']}[/] — [bold]{r['full_name']}[/] ({r['domain_description']}) | {r['degree']}\n"
        f"[bold]Thâm niên & Số thẻ:[/] {r['years_experience']} năm ({exp_tag}) | [bold yellow]{r['card_number']}[/] ({r['issuing_authority']}) | [{sc}][bold]{r['status']}[/][/]",
        title=f"[{sc}]Hồ Sơ Giám Định Viên Tư Pháp (Điều 7 Luật GĐTP)[/]", border_style=sc,
    ))


@forensic_app.command("solicit")
def solicit_cmd(
    agency: str = typer.Argument(..., help="Cơ quan tiến hành tố tụng trưng cầu (Tòa án, VKS, CQĐT)"),
    case_code: str = typer.Argument(..., help="Mã số thụ lý vụ án / vụ việc"),
    target: str = typer.Option("Phân tích mã nguồn và nhật ký máy chủ lưu vết hành vi xâm nhập trái phép", "--target", "-t", help="Đối tượng và nội dung yêu cầu giám định"),
    domain: str = typer.Option("DIGITAL_EVIDENCE", "--domain", "-d", help="Lĩnh vực giám định"),
    value: float = typer.Option(2000000000.0, "--value", "-v", help="Giá trị tranh chấp hoặc thiệt hại ước tính (VND)"),
    deadline: int = typer.Option(30, "--deadline", help="Thời hạn thực hiện giám định (ngày)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tiếp nhận và lập hồ sơ trưng cầu giám định tư pháp theo Điều 25-26 Luật GĐTP."""
    r = _engine().solicit_assessment(agency, case_code, target, domain, value, deadline)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold]Mã quyết định trưng cầu:[/] [cyan]{r['requisition_id']}[/] | [bold]Vụ án:[/] {r['case_code']} ({r['requesting_agency']} — {r['domain_description']})\n"
        f"[bold]Nội dung & Chi phí:[/]      [italic yellow]{r['assessment_target']}[/] | [bold cyan]{r['estimated_fee_vnd']:,.0f} VND[/] ({r['deadline_days']} ngày) | [bold green]{r['status']}[/] — {r['statutory_notes']}",
        title="[green]Quyết Định Trưng Cầu Giám Định Tư Pháp[/]", border_style="green",
    ))


@forensic_app.command("conclude")
def conclude_cmd(
    requisition_id: str = typer.Argument(..., help="Mã hồ sơ trưng cầu giám định"),
    expert_id: str = typer.Argument(..., help="Mã Giám định viên tư pháp chủ trì"),
    method: str = typer.Option("Phân tích tĩnh và động phần mềm, so sánh mã băm SHA-256 đối chiếu chữ ký số", "--method", "-m", help="Phương pháp khoa học kỹ thuật giám định"),
    verdict: str = typer.Option("Phát hiện 12 đoạn mã nguồn sao chép nguyên mẫu từ tài sản trí tuệ của nguyên đơn, tỷ lệ tương đồng 94.2%", "--verdict", "-v", help="Kết luận chuyên môn của giám định viên"),
    sworn: bool = typer.Option(True, "--sworn/--no-sworn", help="Cam kết chịu trách nhiệm hình sự theo Điều 382 BLHS"),
    conflict: bool = typer.Option(False, "--conflict/--no-conflict", help="Có xung đột lợi ích theo Điều 34 Luật GĐTP"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Ban hành Kết luận giám định tư pháp chuẩn hóa theo Điều 32 Luật Giám định tư pháp."""
    r = _engine().issue_expert_conclusion(requisition_id, expert_id, method, verdict, sworn, conflict)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_valid"] else "red"
    console.print(Panel(
        f"[bold]Mã bản kết luận:[/]        [cyan]{r['conclusion_id']}[/] (Trưng cầu: {r['requisition_id']} | GĐV: [bold]{r['lead_expert_id']}[/])\n"
        f"[bold]Phương pháp & Kết luận:[/] {r['methodology']} -> [italic yellow]{r['conclusion_verdict']}[/]\n"
        f"[bold]Cam đoan & Hiệu lực:[/]    {'[green]Đã cam đoan tính trung thực[/]' if r['has_sworn_statement'] else '[red]Thiếu cam đoan[/]'} | {'[red]Phát hiện xung đột[/]' if r['has_conflict_of_interest'] else '[green]Độc lập vô tư[/]'} | [{sc}][bold]{r['status']}[/][/] — {r['statutory_notes']}",
        title=f"[{sc}]Kết Luận Giám Định Tư Pháp (Điều 32 Luật GĐTP)[/]", border_style=sc,
    ))


@forensic_app.command("custody")
def custody_cmd(
    name: str = typer.Argument(..., help="Tên vật chứng / dữ liệu điện tử"),
    device: str = typer.Option("Máy chủ cơ sở dữ liệu Dell PowerEdge R750 SN: 8HJ92", "--device", "-d", help="Thiết bị chứa dữ liệu nguồn"),
    data: str = typer.Option("Forensic bit-stream image raw database payload 2026-09-30", "--data", help="Chuỗi dữ liệu trích xuất để tạo mã băm SHA-256"),
    blocker: bool = typer.Option(True, "--write-blocker/--no-write-blocker", help="Sử dụng thiết bị chống ghi chuyên dụng"),
    witnesses: int = typer.Option(2, "--witnesses", "-w", help="Số lượng người chứng kiến niêm phong (luật định >= 2 người)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra và xác lập chuỗi bảo quản chứng cứ kỹ thuật số (Chain of Custody) theo Điều 99, 107 BLTTHS 2015."""
    r = _engine().audit_digital_chain_of_custody(name, device, data, blocker, witnesses)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_admissible"] else "red"
    console.print(Panel(
        f"[bold]Mã biên bản bảo quản:[/] [cyan]{r['custody_id']}[/] | [bold]Vật chứng:[/] [bold]{r['evidence_name']}[/] ({r['source_device']})\n"
        f"[bold]SHA-256 & Bảo toàn:[/]   [bold yellow]{r['sha256_hash']}[/] | {'[green]Sử dụng Write-Blocker hợp chuẩn[/]' if r['write_blocker_used'] else '[red]Không dùng[/]'} ({r['seizure_witnesses_count']} chứng kiến)\n"
        f"[bold]Tính hợp chuẩn:[/]       [{sc}][bold]{r['status']}[/][/] — {r['statutory_notes']}",
        title=f"[{sc}]Chuỗi Bảo Quản Chứng Cứ Điện Tử (Chain of Custody)[/]", border_style=sc,
    ))


@forensic_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, EXPERTS, REQUISITIONS, CONCLUSIONS, CUSTODY"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa cần hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục giám định viên, quyết định trưng cầu, bản kết luận và chuỗi chứng cứ điện tử."""
    records = _engine().list_forensic_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    for cat_key, items in records.items():
        if not items:
            continue
        table = Table(title=f"Danh mục {cat_key.replace('_', ' ').upper()} ({len(items)} bản ghi)")
        for col, st in [("Mã định danh", "cyan"), ("Trạng thái", "green"), ("Chi tiết", "white"), ("Thời gian", "dim")]:
            table.add_column(col, style=st)
        for item in items:
            pid = item.get("expert_id") or item.get("requisition_id") or item.get("conclusion_id") or item.get("custody_id") or ""
            detail = f"{item.get('full_name', '')} ({item.get('domain', '')})" if "full_name" in item else (item.get("assessment_target") or item.get("conclusion_verdict") or item.get("evidence_name") or "")
            table.add_row(str(pid), str(item.get("status", "")), str(detail)[:60], str(item.get("created_at", ""))[:19])
        console.print(table)


@forensic_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động giám định tư pháp toàn quốc."""
    t = _engine().get_forensic_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold]Giám định viên tư pháp:[/]   [cyan]{t['total_experts']}[/] ([bold green]{t['certified_experts']}[/] đủ chuẩn) | [bold]Trưng cầu:[/] [bold]{t['total_requisitions']}[/] ([bold yellow]{t['total_estimated_fees_vnd']:,.0f} VND[/])\n"
        f"[bold]Kết luận & Bảo quản CC:[/]   [bold]{t['total_conclusions']}[/] ([bold green]{t['valid_conclusions']}[/] hợp chuẩn — [bold green]{t['validity_rate_pct']}%[/]) | [bold]{t['total_custody_records']}[/] ([bold green]{t['admissible_evidence_records']}[/] hợp chuẩn BLTTHS) | DB: {t['database_path']}",
        title="[bold blue]Chỉ Số Telemetry Giám Định Tư Pháp Quốc Gia[/]", border_style="blue",
    ))
