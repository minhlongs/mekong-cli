# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite (Phase 111)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

forensic_app = typer.Typer(
    name="forensic",
    help="Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite.",
)
console = Console()


@forensic_app.callback(invoke_without_command=True)
def forensic_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động Giám định tư pháp, kết luận giám định và bảo toàn chuỗi chứng cứ điện tử."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    telemetry = engine.get_forensic_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG GIÁM ĐỊNH TƯ PHÁP, CHỨNG CỨ ĐIỆN TỬ & KỸ THUẬT HÌNH SỰ[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Giám định tư pháp 2012 (sửa đổi 2020) & BLTTHS 2015[/]\n"
            f"  Chế tài hình sự:           [bold yellow]Điều 382 BLHS 2015 (Chịu trách nhiệm về tính trung thực)[/]\n\n"
            f"  Giám định viên tư pháp:    [bold]{telemetry['total_experts']}[/] chuyên gia ([bold green]{telemetry['certified_experts']}[/] đủ chuẩn hành nghề)\n"
            f"  Quyết định trưng cầu:      [bold]{telemetry['total_requisitions']}[/] hồ sơ từ cơ quan tiến hành tố tụng\n"
            f"  Tổng chi phí tạm tính:     [bold yellow]{telemetry['total_estimated_fees_vnd']:,.0f} VND[/]\n"
            f"  Kết luận giám định đã lập: [bold]{telemetry['total_conclusions']}[/] ([bold green]{telemetry['valid_conclusions']}[/] hợp chuẩn Điều 32)\n"
            f"  Tỷ lệ kết luận hợp chuẩn:  [bold green]{telemetry['validity_rate_pct']}%[/]\n"
            f"  Chuỗi bảo quản chứng cứ:   [bold]{telemetry['total_custody_records']}[/] vật chứng ([bold green]{telemetry['admissible_evidence_records']}[/] hợp lệ tố tụng)",
            title="[bold blue]Vietnam Judicial Expertise & Forensic Telemetry[/]",
            border_style="blue",
        )
    )


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
    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    result = engine.register_judicial_expert(
        full_name=name,
        domain=domain,
        degree=degree,
        years_experience=exp,
        card_number=card,
        issuing_authority=authority,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_certified"] else "red"
    console.print(
        Panel(
            f"[bold]Mã số giám định viên:[/]   [cyan]{result['expert_id']}[/]\n"
            f"[bold]Họ và tên:[/]              [bold]{result['full_name']}[/]\n"
            f"[bold]Lĩnh vực chuyên môn:[/]    {result['domain_description']}\n"
            f"[bold]Văn bằng đào tạo:[/]       {result['degree']}\n"
            f"[bold]Kinh nghiệm thực tế:[/]    {result['years_experience']} năm ({'[green]Đạt chuẩn >= 5 năm[/]' if result['years_experience'] >= 5 else '[red]Chưa đủ thâm niên[/]'})\n"
            f"[bold]Số thẻ Giám định viên:[/]  [bold yellow]{result['card_number']}[/]\n"
            f"[bold]Cơ quan bổ nhiệm:[/]       {result['issuing_authority']}\n"
            f"[bold]Tình trạng thẩm tra:[/]    [{status_color}][bold]{result['status']}[/][/]",
            title=f"[{status_color}]Hồ Sơ Giám Định Viên Tư Pháp (Điều 7 Luật GĐTP)[/]",
            border_style=status_color,
        )
    )


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
    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    result = engine.solicit_assessment(
        requesting_agency=agency,
        case_code=case_code,
        assessment_target=target,
        domain=domain,
        dispute_value_vnd=value,
        deadline_days=deadline,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã quyết định trưng cầu:[/] [cyan]{result['requisition_id']}[/]\n"
            f"[bold]Cơ quan trưng cầu:[/]       [bold]{result['requesting_agency']}[/]\n"
            f"[bold]Vụ án / Vụ việc:[/]          {result['case_code']}\n"
            f"[bold]Lĩnh vực giám định:[/]      {result['domain_description']}\n"
            f"[bold]Nội dung cần giám định:[/]  [italic yellow]{result['assessment_target']}[/]\n"
            f"[bold]Chi phí giám định dự tính:[/] [bold cyan]{result['estimated_fee_vnd']:,.0f} VND[/]\n"
            f"[bold]Thời hạn giám định:[/]      {result['deadline_days']} ngày\n"
            f"[bold]Tình trạng tiếp nhận:[/]    [bold green]{result['status']}[/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title="[green]Quyết Định Trưng Cầu Giám Định Tư Pháp[/]",
            border_style="green",
        )
    )


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
    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    result = engine.issue_expert_conclusion(
        requisition_id=requisition_id,
        lead_expert_id=expert_id,
        methodology=method,
        conclusion_verdict=verdict,
        has_sworn_statement=sworn,
        has_conflict_of_interest=conflict,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã bản kết luận:[/]         [cyan]{result['conclusion_id']}[/]\n"
            f"[bold]Hồ sơ trưng cầu:[/]         {result['requisition_id']}\n"
            f"[bold]Giám định viên chủ trì:[/]  [bold]{result['lead_expert_id']}[/]\n"
            f"[bold]Phương pháp thực hiện:[/]   {result['methodology']}\n"
            f"[bold]Kết luận chuyên môn:[/]     [italic yellow]{result['conclusion_verdict']}[/]\n"
            f"[bold]Cam đoan Điều 382 BLHS:[/]  {'[green]Đã cam đoan tính trung thực[/]' if result['has_sworn_statement'] else '[red]Thiếu cam đoan[/]'}\n"
            f"[bold]Xung đột lợi ích:[/]        {'[red]Phát hiện xung đột[/]' if result['has_conflict_of_interest'] else '[green]Độc lập vô tư[/]'}\n"
            f"[bold]Hiệu lực pháp lý:[/]        [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Giá trị chứng cứ:[/]        {result['statutory_notes']}",
            title=f"[{status_color}]Kết Luận Giám Định Tư Pháp (Điều 32 Luật GĐTP)[/]",
            border_style=status_color,
        )
    )


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
    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    result = engine.audit_digital_chain_of_custody(
        evidence_name=name,
        source_device=device,
        raw_evidence_data=data,
        write_blocker_used=blocker,
        seizure_witnesses_count=witnesses,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_admissible"] else "red"
    console.print(
        Panel(
            f"[bold]Mã biên bản bảo quản:[/]   [cyan]{result['custody_id']}[/]\n"
            f"[bold]Vật chứng điện tử:[/]      [bold]{result['evidence_name']}[/]\n"
            f"[bold]Thiết bị nguồn:[/]         {result['source_device']}\n"
            f"[bold]Mã băm SHA-256:[/]         [bold yellow]{result['sha256_hash']}[/]\n"
            f"[bold]Thiết bị chống ghi:[/]     {'[green]Sử dụng Write-Blocker hợp chuẩn[/]' if result['write_blocker_used'] else '[red]Không dùng[/]'}\n"
            f"[bold]Người chứng kiến:[/]       {result['seizure_witnesses_count']} người ({'[green]Đạt chuẩn >= 2 người[/]' if result['seizure_witnesses_count'] >= 2 else '[red]Thiếu người chứng kiến[/]'})\n"
            f"[bold]Tính hợp chuẩn chứng cứ:[/] [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ tố tụng:[/]         {result['statutory_notes']}",
            title=f"[{status_color}]Chuỗi Bảo Quản Chứng Cứ Điện Tử (Chain of Custody)[/]",
            border_style=status_color,
        )
    )


@forensic_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, EXPERTS, REQUISITIONS, CONCLUSIONS, CUSTODY"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa cần hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục giám định viên, quyết định trưng cầu, bản kết luận và chuỗi chứng cứ điện tử."""
    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    records = engine.list_forensic_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for cat_key, items in records.items():
        if not items:
            continue
        table = Table(title=f"Danh mục {cat_key.replace('_', ' ').upper()} ({len(items)} bản ghi)")
        table.add_column("Mã định danh", style="cyan")
        table.add_column("Trạng thái", style="green")
        table.add_column("Chi tiết", style="white")
        table.add_column("Thời gian", style="dim")

        for item in items:
            primary_id = item.get("expert_id") or item.get("requisition_id") or item.get("conclusion_id") or item.get("custody_id") or ""
            detail = (
                f"{item.get('full_name', '')} ({item.get('domain', '')})"
                if "full_name" in item
                else item.get("assessment_target", "") or item.get("conclusion_verdict", "") or item.get("evidence_name", "")
            )
            table.add_row(
                str(primary_id),
                str(item.get("status", "")),
                str(detail)[:60],
                str(item.get("created_at", ""))[:19],
            )
        console.print(table)


@forensic_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động giám định tư pháp toàn quốc."""
    from src.core.forensic_engine import ForensicEngine

    engine = ForensicEngine()
    telemetry = engine.get_forensic_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Giám định viên tư pháp:[/]   [cyan]{telemetry['total_experts']}[/] ([bold green]{telemetry['certified_experts']}[/] đủ chuẩn)\n"
            f"[bold]Quyết định trưng cầu:[/]     [bold]{telemetry['total_requisitions']}[/]\n"
            f"[bold]Tổng phí giám định ước tính:[/] [bold yellow]{telemetry['total_estimated_fees_vnd']:,.0f} VND[/]\n"
            f"[bold]Kết luận giám định đã lập:[/] [bold]{telemetry['total_conclusions']}[/] ([bold green]{telemetry['valid_conclusions']}[/] hợp chuẩn)\n"
            f"[bold]Tỷ lệ kết luận hợp chuẩn:[/]  [bold green]{telemetry['validity_rate_pct']}%[/]\n"
            f"[bold]Chuỗi bảo quản chứng cứ:[/]  [bold]{telemetry['total_custody_records']}[/] ([bold green]{telemetry['admissible_evidence_records']}[/] hợp chuẩn BLTTHS)\n"
            f"[bold]Cơ sở dữ liệu:[/]            {telemetry['database_path']}",
            title="[bold blue]Chỉ Số Telemetry Giám Định Tư Pháp Quốc Gia[/]",
            border_style="blue",
        )
    )
