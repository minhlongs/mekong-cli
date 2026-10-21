# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Commercial Arbitration & Out-of-Court Dispute Resolution Suite (Phase 107)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

arbitration_app = typer.Typer(name="arbitration", help="Vietnamese Commercial Arbitration, Out-of-Court Dispute Resolution & New York Convention Suite.")
console = Console()


@arbitration_app.callback(invoke_without_command=True)
def arbitration_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan giải quyết tranh chấp trọng tài thương mại, phán quyết trọng tài và thi hành án quốc tế."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.arbitration_engine import ArbitrationEngine
    t = ArbitrationEngine().get_arbitration_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold blue]HỆ THỐNG TRỌNG TÀI THƯƠNG MẠI & GIẢI QUYẾT TRANH CHẤP NGOÀI TÒA ÁN[/]\n\n"
        f"  Khung pháp lý:             [bold]Luật Trọng tài thương mại 2010 & Công ước New York 1958[/]\n"
        f"  Tổ chức trọng tài chủ lực: [bold yellow]VIAC (Trung tâm Trọng tài Quốc tế Việt Nam)[/]\n\n"
        f"  Thỏa thuận trọng tài:      [bold]{t['total_arbitration_clauses']}[/] ([bold green]{t['valid_clauses']}[/] điều khoản mẫu hợp lệ)\n"
        f"  Vụ kiện thụ lý giải quyết: [bold]{t['total_arbitration_claims']}[/] vụ việc ([bold yellow]{t['total_dispute_amount_vnd']:,.0f} VND[/] giá trị tranh chấp)\n"
        f"  Phí trọng tài thu nộp:     [bold cyan]{t['total_fees_collected_vnd']:,.0f} VND[/]\n"
        f"  Phán quyết trọng tài:      [bold]{t['total_awards_rendered']}[/] ([bold green]{t['total_amount_awarded_vnd']:,.0f} VND[/] số tiền chấp thuận thi hành)\n"
        f"  Phán quyết nước ngoài:     [bold]{t['total_foreign_dossiers']}[/] hồ sơ ([bold green]{t['eligible_foreign_dossiers']}[/] đủ điều kiện công nhận tại Việt Nam, [bold yellow]${t['total_foreign_amount_usd']:,.2f}[/])",
        title="[bold blue]Vietnam Commercial Arbitration & Dispute Resolution Telemetry[/]", border_style="blue",
    ))


@arbitration_app.command("clause")
def clause_cmd(
    title: str = typer.Argument(..., help="Tên hợp đồng kinh tế / thương mại"),
    institution: str = typer.Option("VIAC", "--inst", "-i", help="Tổ chức trọng tài: VIAC, SIAC, ICC, HKIAC, AD_HOC"),
    seat: str = typer.Option("Hà Nội", "--seat", "-s", help="Địa điểm giải quyết trọng tài"),
    governing_law: str = typer.Option("VIETNAMESE_LAW", "--law", "-l", help="Luật nội dung áp dụng"),
    language: str = typer.Option("VIETNAMESE", "--lang", help="Ngôn ngữ trọng tài: VIETNAMESE, ENGLISH"),
    arbitrators: int = typer.Option(3, "--arbitrators", "-a", help="Số lượng trọng tài viên (1 hoặc 3)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Soạn thảo và thẩm định điều khoản trọng tài mẫu theo Luật Trọng tài thương mại 2010."""
    from src.core.arbitration_engine import ArbitrationEngine
    r = ArbitrationEngine().draft_arbitration_clause(contract_title=title, institution=institution, seat=seat, governing_law=governing_law, language=language, num_arbitrators=arbitrators)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_valid"] else "red"
    console.print(Panel(
        f"[bold]Mã điều khoản:[/] [cyan]{r['clause_id']}[/] | [bold]Hợp đồng:[/] [bold]{r['contract_title']}[/]\n"
        f"[bold]Tổ chức trọng tài:[/] {r['institution_name']} ({r['seat']}) | [bold]Luật:[/] {r['governing_law']} | [bold]Ngôn ngữ:[/] {r['language']}\n"
        f"[bold]Số trọng tài viên:[/] {r['num_arbitrators']} | [bold]Tính hợp lệ:[/] [{sc}]{'HỢP LỆ' if r['is_valid'] else 'VÔ HIỆU'}[/]\n"
        f"[bold]Nội dung điều khoản mẫu:[/]\n[italic yellow]{r['model_clause']}[/]\n[bold]Ghi chú pháp lý:[/] {r['statutory_notes']}",
        title=f"[{sc}]Điều Khoản Trọng Tài Thương Mại Hợp Đồng[/]", border_style=sc,
    ))


@arbitration_app.command("claim")
def claim_cmd(
    claimant: str = typer.Argument(..., help="Tên Nguyên đơn khởi kiện"),
    respondent: str = typer.Option(..., "--respondent", "-r", help="Tên Bị đơn"),
    subject: str = typer.Option("Tranh chấp hợp đồng mua bán hàng hóa quốc tế", "--subject", help="Nội dung tranh chấp"),
    amount: float = typer.Option(5000000000.0, "--amount", help="Giá trị yêu cầu khởi kiện (VND)"),
    arbitrators: int = typer.Option(3, "--arbitrators", "-a", help="Hội đồng 1 hay 3 trọng tài viên"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thụ lý đơn khởi kiện trọng tài và tính biểu phí trọng tài VIAC theo Điều 30-34 Luật TTTM."""
    from src.core.arbitration_engine import ArbitrationEngine
    r = ArbitrationEngine().file_arbitration_claim(claimant=claimant, respondent=respondent, dispute_subject=subject, dispute_amount_vnd=amount, tribunal_size=arbitrators)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold]Mã vụ kiện trọng tài:[/] [cyan]{r['claim_id']}[/] | [bold]Nguyên đơn:[/] [bold]{r['claimant']}[/] vs [bold]Bị đơn:[/] {r['respondent']}\n"
        f"[bold]Nội dung tranh chấp:[/] {r['dispute_subject']}\n"
        f"[bold]Giá trị khởi kiện:[/] [yellow]{r['dispute_amount_vnd']:,.0f} VND[/] | [bold]Hội đồng:[/] {r['tribunal_size']} trọng tài viên\n"
        f"[bold]Phí trọng tài VIAC:[/] [bold cyan]{r['arbitration_fee_vnd']:,.0f} VND[/] | [bold]Trạng thái:[/] [green]{r['status']}[/]",
        title="[green]Thụ Lý Đơn Khởi Kiện Trọng Tài VIAC[/]", border_style="green",
    ))


@arbitration_app.command("award")
def award_cmd(
    claim_id: str = typer.Argument(..., help="Mã vụ kiện trọng tài"),
    president: str = typer.Option("GS. TS. Lê Hồng Hạnh", "--president", "-p", help="Chủ tịch Hội đồng Trọng tài"),
    granted_pct: float = typer.Option(100.0, "--granted-pct", "-g", help="Tỷ lệ chấp thuận yêu cầu khởi kiện (%)"),
    awarded_amount: Optional[float] = typer.Option(None, "--amount", help="Số tiền chấp thuận thanh toán (VND)"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Ngày tuyên phán quyết (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Ban hành phán quyết trọng tài chung thẩm và thẩm tra nguy cơ bị hủy theo Điều 60, 61, 68."""
    from src.core.arbitration_engine import ArbitrationEngine
    r = ArbitrationEngine().render_arbitral_award(claim_id=claim_id, tribunal_president=president, claim_granted_pct=granted_pct, amount_awarded_vnd=awarded_amount, award_date=date)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold]Mã phán quyết:[/] [cyan]{r['award_id']}[/] (Vụ kiện: {r['claim_id']}) | [bold]Chủ tịch HĐTT:[/] [bold]{r['tribunal_president']}[/] ({r['award_date']})\n"
        f"[bold]Tỷ lệ chấp thuận:[/] {r['claim_granted_pct']}% | [bold]Số tiền bồi thường:[/] [bold yellow]{r['amount_awarded_vnd']:,.0f} VND[/]\n"
        f"[bold]Giá trị pháp lý:[/] {'[green]CHUNG THẨM BẮT BUỘC THI HÀNH[/]' if r['is_final_binding'] else '[red]Chưa hiệu lực[/]'} | [bold]Nguy cơ hủy:[/] [green]{r['set_aside_risk']} (Tuân thủ Điều 68)[/]\n"
        f"[bold]Căn cứ pháp lý:[/] {r['statutory_notes']}",
        title="[green]Phán Quyết Trọng Tài Thương Mại Chung Thẩm[/]", border_style="green",
    ))


@arbitration_app.command("foreign")
def foreign_cmd(
    tribunal: str = typer.Argument(..., help="Tổ chức trọng tài nước ngoài (SIAC, ICC, HKIAC)"),
    country: str = typer.Option("Singapore", "--country", "-c", help="Quốc gia nơi ban hành phán quyết"),
    amount_usd: float = typer.Option(2500000.0, "--amount-usd", help="Giá trị phán quyết bằng USD"),
    ny_member: bool = typer.Option(True, "--ny-member/--no-ny-member", help="Quốc gia thành viên Công ước New York 1958"),
    consular: bool = typer.Option(True, "--consular/--no-consular", help="Đã hợp pháp hóa lãnh sự phán quyết và thỏa thuận trọng tài"),
    years: float = typer.Option(1.5, "--years", "-y", help="Số năm kể từ ngày phán quyết có hiệu lực (tối đa 3 năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra hồ sơ yêu cầu công nhận và cho thi hành phán quyết trọng tài nước ngoài theo Công ước New York."""
    from src.core.arbitration_engine import ArbitrationEngine
    r = ArbitrationEngine().enforce_foreign_award(foreign_tribunal=tribunal, origin_country=country, award_amount_usd=amount_usd, new_york_convention_member=ny_member, consular_authenticated=consular, years_since_award=years)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_eligible"] else "red"
    console.print(Panel(
        f"[bold]Mã hồ sơ công nhận:[/] [cyan]{r['dossier_id']}[/] | [bold]Trọng tài:[/] [bold]{r['foreign_tribunal']}[/] ({r['origin_country']}) | [yellow]${r['award_amount_usd']:,.2f} USD[/]\n"
        f"[bold]Công ước New York 1958:[/] {'[green]Thành viên hợp lệ[/]' if r['new_york_convention_member'] else '[red]Không thuộc thành viên[/]'} | [bold]Hợp pháp hóa lãnh sự:[/] {'[green]Đầy đủ[/]' if r['consular_authenticated'] else '[red]Chưa hợp pháp hóa[/]'}\n"
        f"[bold]Thời hiệu yêu cầu (3 năm):[/] {'[green]Còn thời hiệu[/]' if r['statute_of_limitations_valid'] else '[red]Hết thời hiệu[/]'} | [bold]Kết luận:[/] [{sc}][bold]{r['status']}[/][/]\n"
        f"[bold]Căn cứ pháp lý:[/] {r['statutory_notes']}",
        title=f"[{sc}]Thẩm Tra Công Nhận Phán Quyết Trọng Tài Nước Ngoài[/]", border_style=sc,
    ))


@arbitration_app.command("list")
def list_cmd(category: str = typer.Option("ALL", "--category", "-c", help="Danh mục tra cứu: ALL, CLAUSES, CLAIMS, AWARDS, FOREIGN"), limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Tra cứu danh mục điều khoản trọng tài, vụ kiện khởi kiện, phán quyết ban hành và hồ sơ quốc tế."""
    from src.core.arbitration_engine import ArbitrationEngine
    records = ArbitrationEngine().list_arbitration_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    if records.get("claims"):
        table = Table(title="Danh Sách Vụ Kiện Trọng Tài Thương Mại")
        for col, st in (("Mã Vụ Kiện", "cyan"), ("Nguyên Đơn", "bold"), ("Bị Đơn", ""), ("Giá Trị Tranh Chấp", "yellow"), ("Phí VIAC", "cyan"), ("Trạng Thái", "")):
            table.add_column(col, style=st)
        for row in records["claims"]:
            table.add_row(row["claim_id"], row["claimant"], row["respondent"], f"{row['dispute_amount_vnd']:,.0f} VND", f"{row['arbitration_fee_vnd']:,.0f} VND", row["status"])
        console.print(table)
    if records.get("awards"):
        table = Table(title="Danh Sách Phán Quyết Trọng Tài Đã Ban Hành")
        for col, st in (("Mã Phán Quyết", "cyan"), ("Vụ Kiện", ""), ("Chủ Tịch HĐTT", "bold"), ("Ngày Tuyên", ""), ("Số Tiền Phán Quyết", "yellow"), ("Rủi Ro Hủy", "green")):
            table.add_column(col, style=st)
        for row in records["awards"]:
            table.add_row(row["award_id"], row["claim_id"], row["tribunal_president"], row["award_date"], f"{row['amount_awarded_vnd']:,.0f} VND", row["set_aside_risk"])
        console.print(table)


@arbitration_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Hiển thị tổng quan các chỉ số telemetry trọng tài thương mại quốc gia."""
    from src.core.arbitration_engine import ArbitrationEngine
    t = ArbitrationEngine().get_arbitration_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    table = Table(title="Vietnam Commercial Arbitration Telemetry")
    table.add_column("Chỉ Số Trọng Tài Thương Mại", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")
    for k, v in (("Tổng điều khoản trọng tài đăng ký", str(t["total_arbitration_clauses"])), ("Điều khoản trọng tài hợp chuẩn", str(t["valid_clauses"])), ("Tổng vụ kiện trọng tài thụ lý", str(t["total_arbitration_claims"])), ("Tổng giá trị tranh chấp thụ lý", f"{t['total_dispute_amount_vnd']:,.0f} VND"), ("Tổng phí trọng tài thu nộp", f"{t['total_fees_collected_vnd']:,.0f} VND"), ("Tổng phán quyết trọng tài ban hành", str(t["total_awards_rendered"])), ("Tổng giá trị phán quyết buộc thi hành", f"{t['total_amount_awarded_vnd']:,.0f} VND"), ("Hồ sơ công nhận phán quyết nước ngoài", f"{t['eligible_foreign_dossiers']} / {t['total_foreign_dossiers']}"), ("Tổng giá trị phán quyết quốc tế", f"${t['total_foreign_amount_usd']:,.2f} USD")):
        table.add_row(k, v)
    console.print(table)
