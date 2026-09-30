# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Commercial Mediation, Conciliation & ADR Suite (Phase 110)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

mediation_app = typer.Typer(
    name="mediation",
    help="Vietnamese Commercial Mediation, Conciliation & ADR Suite.",
)
console = Console()


@mediation_app.callback(invoke_without_command=True)
def mediation_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động Hòa giải thương mại, kết quả hòa giải thành và công nhận bản án Tòa án."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    telemetry = engine.get_mediation_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG HÒA GIẢI THƯƠNG MẠI, GIẢI QUYẾT TRANH CHẤP NGOÀI TÒA ÁN (ADR)[/]\n\n"
            f"  Khung pháp lý:             [bold]Nghị định số 22/2017/NĐ-CP & BLTTDS 2015 Chương XXXIII[/]\n"
            f"  Quy chế quốc tế:           [bold yellow]Công ước Singapore về Hòa giải 2018 (Singapore Convention)[/]\n\n"
            f"  Thỏa thuận hòa giải:       [bold]{telemetry['total_mediation_agreements']}[/] thỏa thuận / điều khoản mẫu\n"
            f"  Vụ việc đã thụ lý:         [bold]{telemetry['total_mediation_cases']}[/] vụ tranh chấp thương mại\n"
            f"  Tổng giá trị tranh chấp:   [bold yellow]{telemetry['total_claim_amount_vnd']:,.0f} VND[/]\n"
            f"  Tổng phí dịch vụ hòa giải: [bold]{telemetry['total_mediation_fees_vnd']:,.0f} VND[/]\n"
            f"  Hòa giải thành công:       [bold green]{telemetry['successful_settlements']}[/] / [bold]{telemetry['total_settlements']}[/] biên bản\n"
            f"  Tỷ lệ hòa giải thành:      [bold green]{telemetry['settlement_rate_pct']}%[/]\n"
            f"  Tổng giá trị thỏa thuận:   [bold cyan]{telemetry['total_settlement_amount_vnd']:,.0f} VND[/]\n"
            f"  Công nhận Tòa án có hiệu lực: [bold green]{telemetry['enforceable_judgments']}[/] quyết định cưỡng chế thi hành",
            title="[bold blue]Vietnam Commercial Mediation & ADR Telemetry[/]",
            border_style="blue",
        )
    )


@mediation_app.command("agreement")
def agreement_cmd(
    party_a: str = typer.Argument(..., help="Tên Bên A tham gia thỏa thuận"),
    party_b: str = typer.Argument(..., help="Tên Bên B tham gia thỏa thuận"),
    scope: str = typer.Option("Tất cả các tranh chấp phát sinh từ hoặc liên quan đến hợp đồng kinh tế", "--scope", "-s", help="Phạm vi tranh chấp áp dụng hòa giải"),
    center: str = typer.Option("VICMC", "--center", "-c", help="Tổ chức hòa giải: VICMC, VMC, AD_HOC"),
    lang: str = typer.Option("VIETNAMESE", "--lang", "-l", help="Ngôn ngữ tiến hành hòa giải"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Soạn thảo và thẩm tra thỏa thuận / điều khoản hòa giải thương mại mẫu theo Điều 11 Nghị định 22/2017/NĐ-CP."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    result = engine.draft_mediation_agreement(
        party_a=party_a,
        party_b=party_b,
        dispute_scope=scope,
        mediation_center=center,
        language=lang,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã thỏa thuận:[/]          [cyan]{result['agreement_id']}[/]\n"
            f"[bold]Bên A:[/]                  [bold]{result['party_a']}[/]\n"
            f"[bold]Bên B:[/]                  [bold]{result['party_b']}[/]\n"
            f"[bold]Tổ chức hòa giải:[/]       [bold yellow]{result['mediation_center']}[/]\n"
            f"[bold]Ngôn ngữ hòa giải:[/]      {result['language']}\n"
            f"[bold]Điều khoản mẫu:[/]         [italic green]{result['model_clause']}[/]\n"
            f"[bold]Hiệu lực pháp lý:[/]       [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]         {result['statutory_notes']}",
            title=f"[{status_color}]Thỏa Thuận Hòa Giải Thương Mại (Nghị Định 22/2017/NĐ-CP)[/]",
            border_style=status_color,
        )
    )


@mediation_app.command("case")
def case_cmd(
    party_a: str = typer.Argument(..., help="Bên yêu cầu hòa giải"),
    party_b: str = typer.Argument(..., help="Bên bị yêu cầu hòa giải"),
    amount: float = typer.Option(500000000.0, "--amount", "-a", help="Giá trị tranh chấp yêu cầu giải quyết (VND)"),
    category: str = typer.Option("SALE_OF_GOODS", "--category", "-c", help="Danh mục: SALE_OF_GOODS, TECH_SERVICES, CONSTRUCTION_EPC, SHAREHOLDER_INVEST, LOGISTICS_FREIGHT, INTELLECTUAL_PROPERTY"),
    mediator: str = typer.Option("Hòa giải viên Luật sư Lê Hoàng Long", "--mediator", "-m", help="Họ tên Hòa giải viên thương mại chỉ định"),
    exp: int = typer.Option(5, "--exp", help="Số năm kinh nghiệm hành nghề của hòa giải viên (luật định >= 2 năm)"),
    center: str = typer.Option("VICMC", "--center", help="Trung tâm hòa giải thụ lý"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thụ lý vụ việc hòa giải thương mại và chỉ định Hòa giải viên đạt chuẩn Điều 7 Nghị định 22/2017/NĐ-CP."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    result = engine.initiate_mediation_case(
        party_a=party_a,
        party_b=party_b,
        claim_amount_vnd=amount,
        dispute_category=category,
        mediator_name=mediator,
        mediator_experience_years=exp,
        mediation_center=center,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã hồ sơ hòa giải:[/]      [cyan]{result['case_id']}[/]\n"
            f"[bold]Các bên tranh chấp:[/]     [bold]{result['party_a']}[/] ↔ [bold]{result['party_b']}[/]\n"
            f"[bold]Lĩnh vực tranh chấp:[/]    {result['category_name']}\n"
            f"[bold]Giá trị tranh chấp:[/]     [bold yellow]{result['claim_amount_vnd']:,.0f} VND[/]\n"
            f"[bold]Hòa giải viên:[/]          [bold]{result['mediator_name']}[/] ({result['mediator_experience_years']} năm kinh nghiệm)\n"
            f"[bold]Phí dịch vụ hòa giải:[/]   [bold cyan]{result['mediation_fee_vnd']:,.0f} VND[/]\n"
            f"[bold]Tình trạng thụ lý:[/]      [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]         {result['statutory_notes']}",
            title=f"[{status_color}]Hồ Sơ Vụ Việc Hòa Giải Thương Mại Thụ Lý[/]",
            border_style=status_color,
        )
    )


@mediation_app.command("settle")
def settle_cmd(
    case_id: str = typer.Argument(..., help="Mã hồ sơ hòa giải đã thụ lý"),
    amount: float = typer.Option(350000000.0, "--amount", "-a", help="Số tiền các bên thỏa thuận bồi thường / thanh toán (VND)"),
    summary: str = typer.Option("Bên B đồng ý thanh toán cho Bên A số tiền thỏa thuận trong thời hạn 30 ngày và bàn giao sản phẩm phần mềm", "--summary", "-s", help="Tóm tắt nội dung thỏa thuận hòa giải thành"),
    mediator_sig: bool = typer.Option(True, "--mediator-sig/--no-mediator-sig", help="Có chữ ký xác nhận của Hòa giải viên thương mại"),
    parties_sig: bool = typer.Option(True, "--parties-sig/--no-parties-sig", help="Có chữ ký của đại diện hợp pháp các bên tranh chấp"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Lập Văn bản kết quả hòa giải thành theo Điều 15 Nghị định 22/2017/NĐ-CP."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    result = engine.create_settlement_record(
        case_id=case_id,
        settlement_amount_vnd=amount,
        settlement_summary=summary,
        mediator_signature=mediator_sig,
        parties_signature=parties_sig,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã văn bản hòa giải thành:[/] [cyan]{result['settlement_id']}[/]\n"
            f"[bold]Mã vụ việc liên kết:[/]       {result['case_id']}\n"
            f"[bold]Giá trị thỏa thuận thành:[/]  [bold yellow]{result['settlement_amount_vnd']:,.0f} VND[/]\n"
            f"[bold]Nội dung cam kết:[/]          [italic yellow]{result['settlement_summary']}[/]\n"
            f"[bold]Chữ ký Hòa giải viên:[/]      {'[green]Đã ký xác nhận[/]' if result['mediator_signature'] else '[red]Chưa ký[/]'}\n"
            f"[bold]Chữ ký các bên:[/]            {'[green]Đã ký đầy đủ[/]' if result['parties_signature'] else '[red]Chưa ký[/]'}\n"
            f"[bold]Tình trạng văn bản:[/]        [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Hiệu lực thi hành:[/]         {result['statutory_notes']}",
            title=f"[{status_color}]Văn Bản Kết Quả Hòa Giải Thành (Điều 15 NĐ 22/2017)[/]",
            border_style=status_color,
        )
    )


@mediation_app.command("recognize")
def recognize_cmd(
    settlement_id: str = typer.Argument(..., help="Mã văn bản kết quả hòa giải thành"),
    court: str = typer.Option("Tòa án nhân dân Thành phố Hà Nội", "--court", "-c", help="Tòa án có thẩm quyền công nhận"),
    months: float = typer.Option(2.0, "--months", "-m", help="Số tháng kể từ ngày lập văn bản hòa giải thành (thời hiệu <= 6 tháng)"),
    capacity: bool = typer.Option(True, "--capacity/--no-capacity", help="Các bên có đầy đủ năng lực hành vi dân sự"),
    voluntary: bool = typer.Option(True, "--voluntary/--no-voluntary", help="Thỏa thuận hoàn toàn trên cơ sở tự nguyện"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra thủ tục Tòa án công nhận kết quả hòa giải thành ngoài Tòa án theo BLTTDS 2015 Điều 416-419."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    result = engine.audit_court_recognition(
        settlement_id=settlement_id,
        court_name=court,
        filing_months_elapsed=months,
        has_capacity=capacity,
        is_voluntary=voluntary,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_recognized"] else "red"
    console.print(
        Panel(
            f"[bold]Mã quyết định công nhận:[/] [cyan]{result['recognition_id']}[/]\n"
            f"[bold]Văn bản hòa giải thành:[/]  {result['settlement_id']}\n"
            f"[bold]Tòa án giải quyết:[/]       [bold]{result['court_name']}[/]\n"
            f"[bold]Thời gian nộp đơn:[/]       {result['filing_months_elapsed']:.1f} tháng ({'[green]Trong thời hiệu 6 tháng[/]' if result['within_statute_limit'] else '[red]Quá thời hiệu[/]'})\n"
            f"[bold]Kết quả công nhận:[/]       [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Hiệu lực cưỡng chế THA:[/]   [bold green]{result['enforceability_order']}[/]\n"
            f"[bold]Nhận định của Tòa án:[/]     {result['statutory_notes']}",
            title=f"[{status_color}]Thẩm Tra Quyết Định Công Nhận Của Tòa Án (BLTTDS 2015)[/]",
            border_style=status_color,
        )
    )


@mediation_app.command("convention")
def convention_cmd(
    settlement_id: str = typer.Argument(..., help="Mã văn bản thỏa thuận hòa giải"),
    cross_border: bool = typer.Option(True, "--cross-border/--no-cross-border", help="Thỏa thuận mang tính chất quốc tế (xuyên biên giới)"),
    commercial: bool = typer.Option(True, "--commercial/--no-commercial", help="Tranh chấp phát sinh từ quan hệ thương mại"),
    attestation: bool = typer.Option(True, "--attestation/--no-attestation", help="Có xác nhận của Hòa giải viên thương mại"),
    consumer: bool = typer.Option(False, "--consumer/--no-consumer", help="Là tranh chấp tiêu dùng cá nhân hoặc gia đình (bị loại trừ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra điều kiện thi hành trực tiếp xuyên biên giới theo Công ước Singapore về Hòa giải 2018."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    result = engine.audit_singapore_convention(
        settlement_id=settlement_id,
        is_cross_border=cross_border,
        is_commercial=commercial,
        mediator_attestation=attestation,
        has_consumer_or_family=consumer,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_eligible"] else "red"
    console.print(
        Panel(
            f"[bold]Văn bản hòa giải:[/]        {result['settlement_id']}\n"
            f"[bold]Tính chất quốc tế:[/]       {'[green]Có[/]' if result['is_cross_border'] else '[red]Không[/]'}\n"
            f"[bold]Quan hệ thương mại:[/]      {'[green]Hợp chuẩn[/]' if result['is_commercial'] else '[red]Ngoài phạm vi[/]'}\n"
            f"[bold]Xác nhận Hòa giải viên:[/]  {'[green]Đạt chuẩn[/]' if result['mediator_attestation'] else '[red]Thiếu xác nhận[/]'}\n"
            f"[bold]Loại trừ tiêu dùng:[/]      {'[green]Không vi phạm[/]' if not result['has_consumer_or_family'] else '[red]Bị loại trừ[/]'}\n"
            f"[bold]Kết luận công ước:[/]       [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Thẩm Tra Công Ước Singapore Về Hòa Giải (Singapore Convention)[/]",
            border_style=status_color,
        )
    )


@mediation_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, AGREEMENTS, CASES, SETTLEMENTS, RECOGNITIONS"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa cần hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục thỏa thuận hòa giải, vụ việc thụ lý, biên bản hòa giải thành và quyết định công nhận Tòa án."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    records = engine.list_mediation_records(category=category, limit=limit)

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
            primary_id = item.get("case_id") or item.get("agreement_id") or item.get("settlement_id") or item.get("recognition_id") or ""
            detail = (
                f"{item.get('party_a', '')} ↔ {item.get('party_b', '')} ({item.get('claim_amount_vnd', 0):,.0f} VND)"
                if "party_a" in item
                else item.get("settlement_summary", "") or item.get("statutory_notes", "")
            )
            table.add_row(
                str(primary_id),
                str(item.get("status", "")),
                str(detail)[:60],
                str(item.get("created_at", ""))[:19],
            )
        console.print(table)


@mediation_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động hòa giải thương mại và công nhận Tòa án."""
    from src.core.mediation_engine import MediationEngine

    engine = MediationEngine()
    telemetry = engine.get_mediation_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Tổng thỏa thuận hòa giải:[/]   [cyan]{telemetry['total_mediation_agreements']}[/]\n"
            f"[bold]Vụ việc hòa giải thụ lý:[/]    [bold]{telemetry['total_mediation_cases']}[/]\n"
            f"[bold]Tổng giá trị tranh chấp:[/]    [bold yellow]{telemetry['total_claim_amount_vnd']:,.0f} VND[/]\n"
            f"[bold]Tổng phí hòa giải:[/]          [bold]{telemetry['total_mediation_fees_vnd']:,.0f} VND[/]\n"
            f"[bold]Văn bản hòa giải thành:[/]     [bold green]{telemetry['successful_settlements']}[/] / {telemetry['total_settlements']}\n"
            f"[bold]Tỷ lệ hòa giải thành:[/]       [bold green]{telemetry['settlement_rate_pct']}%[/]\n"
            f"[bold]Tổng giá trị thỏa thuận:[/]    [bold cyan]{telemetry['total_settlement_amount_vnd']:,.0f} VND[/]\n"
            f"[bold]Hồ sơ Tòa án công nhận:[/]     [bold]{telemetry['total_court_petitions']}[/] ([bold green]{telemetry['enforceable_judgments']}[/] có hiệu lực THADS)\n"
            f"[bold]Cơ sở dữ liệu:[/]              {telemetry['database_path']}",
            title="[bold blue]Chỉ Số Telemetry Hòa Giải Thương Mại Toàn Quốc[/]",
            border_style="blue",
        )
    )
