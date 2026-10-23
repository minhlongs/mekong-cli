# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Public Procurement, National E-GP Electronic Tender & Bid Evaluation Engine (Phase 52)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from src.cli.commands.tender_commands_records_table import build_table
from src.cli.commands.tender_commands_records_table import format_vnd as _format_vnd

console = Console()
tender_app = typer.Typer(name="tender", help="Public Procurement, National E-GP Electronic Tender Dossiers & Bid Evaluation under Bidding Law 2023", add_completion=False)


@tender_app.callback(invoke_without_command=True)
def tender_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON")) -> None:
    """Hệ thống Quản trị Đấu thầu Quốc gia (E-GP), Thẩm định Hồ sơ Mời thầu (E-HSMT) & Đánh giá E-HSDT."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.tender_engine import TenderEngine
    status_data = TenderEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]HỆ THỐNG ĐẤU THẦU ĐIỆN TỬ QUỐC GIA (E-GP) & ĐÁNH GIÁ E-HSDT[/]\n\n"
        f"  Khung pháp lý:         [bold]{status_data['regulatory_framework']}[/]\n"
        f"  Cổng thông tin đấu thầu:[bold cyan]{status_data['national_egp_system']}[/]\n"
        f"  Tổng số gói thầu:      [bold]{m['total_tenders']} gói[/] (Tổng dự toán: [bold green]{_format_vnd(m['total_budget_vnd'])}[/])\n"
        f"  Hồ sơ dự thầu tiếp nhận: [bold]{m['total_bids_submitted']} hồ sơ[/] (Đạt yêu cầu: [bold green]{m['qualified_bids']}[/])\n"
        f"  Hiệu quả tiết kiệm NSNN: [bold yellow]{m['average_savings_rate_pct']}%[/] bình quân qua đấu thầu cạnh tranh\n"
        f"  Quy trình đánh giá:    [bold]4 bước chuẩn Nghị định 24/2024/NĐ-CP (Hợp lệ -> Năng lực -> Kỹ thuật -> Tài chính)[/]",
        title="[bold blue]National E-GP Public Procurement Dashboard[/]", border_style="green",
    ))


@tender_app.command("method")
def evaluate_method_cmd(
    package_type: str = typer.Argument(..., help="Loại gói thầu (GOODS, CONSULTING, WORKS, NON_CONSULTING)"),
    budget_vnd: float = typer.Argument(..., help="Giá gói thầu / Dự toán được duyệt (VND)"),
    urgent: bool = typer.Option(False, "--urgent", help="Gói thầu cấp bách, thiên tai, dịch bệnh (Điều 23.1.a)"),
    proprietary: bool = typer.Option(False, "--proprietary", help="Gói thầu công nghệ bản quyền độc quyền (Điều 23.1.c)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định và tư vấn hình thức lựa chọn nhà thầu theo Luật Đấu thầu 2023."""
    from src.core.tender_engine import TenderEngine
    r = TenderEngine().evaluate_procurement_method(package_type=package_type, budget_vnd=budget_vnd, is_urgent=urgent, is_proprietary_tech=proprietary)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    mc = "green" if r["recommended_method"] == "OPEN_BIDDING" else ("yellow" if r["recommended_method"] == "COMPETITIVE_QUOTATION" else "cyan")
    console.print(Panel(
        f"[bold {mc}]KẾT QUẢ THẨM ĐỊNH HÌNH THỨC LỰA CHỌN NHÀ THẦU[/]\n\n"
        f"  Loại gói thầu:        [bold]{r['package_type']}[/] (Dự toán: {_format_vnd(r['budget_vnd'])})\n"
        f"  Hình thức đề xuất:    [bold {mc}]{r['recommended_method']}[/bold {mc}] | Căn cứ: [bold]{r['governing_article']}[/]\n"
        f"  Lý do thẩm định:      {r['statutory_justification']}\n"
        f"  Hạn mức chỉ định thầu: {_format_vnd(r['direct_contracting_cap_vnd'])}\n"
        f"  Bảo đảm dự thầu:      {'Bắt buộc' if r['bid_security_required'] else 'Không yêu cầu'}"
        + (f" ({r['bid_security_rate_pct']}% ~ {_format_vnd(r['bid_security_estimated_vnd'])})" if r["bid_security_required"] else ""),
        title="[bold blue]Procurement Method Advisory[/]", border_style=mc,
    ))


@tender_app.command("create")
def create_tender_cmd(
    name: str = typer.Argument(..., help="Tên gói thầu"),
    entity: str = typer.Argument(..., help="Tên bên mời thầu / Chủ đầu tư"),
    budget_vnd: float = typer.Argument(..., help="Giá gói thầu dự toán (VND)"),
    package_type: str = typer.Option("GOODS", "--type", "-t", help="Loại gói thầu (GOODS, CONSULTING, WORKS, NON_CONSULTING)"),
    method: str = typer.Option(None, "--method", "-m", help="Hình thức lựa chọn nhà thầu"),
    days: int = typer.Option(15, "--days", "-d", help="Thời gian chuẩn bị E-HSDT (ngày)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tạo lập và phát hành gói thầu E-HSMT trên Hệ thống Mạng Đấu thầu Quốc gia."""
    from src.core.tender_engine import TenderEngine
    r = TenderEngine().create_tender(package_name=name, procuring_entity=entity, budget_vnd=budget_vnd, package_type=package_type, procurement_method=method, submission_days=days)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    crit = r["statutory_criteria"]
    console.print(Panel(
        f"[bold green]ĐÃ PHÁT HÀNH HỒ SƠ MỜI THẦU ĐIỆN TỬ (E-HSMT): {r['package_number']}[/]\n\n"
        f"  Tên gói thầu:         [bold cyan]{r['package_name']}[/] | Bên mời thầu: [bold]{r['procuring_entity']}[/]\n"
        f"  Hình thức đấu thầu:   [bold yellow]{r['procurement_method']}[/] ({r['package_type']}) | Giá gói thầu: [bold green]{_format_vnd(r['budget_vnd'])}[/]\n"
        f"  Bảo đảm dự thầu:      [bold magenta]{_format_vnd(r['bid_security_vnd'])}[/] | Hạn nộp E-HSDT: {r['submission_deadline']}\n"
        f"  Tiêu chuẩn năng lực:  Doanh thu 3 năm >= {_format_vnd(crit['min_3yr_avg_revenue_vnd'])} | HĐ tương tự >= {_format_vnd(crit['min_similar_contract_val_vnd'])}\n"
        f"  Hệ thống phát hành:   {r['egp_system']}",
        title="[bold green]E-HSMT Published on National E-GP[/]", border_style="green",
    ))


@tender_app.command("eval")
def evaluate_bid_cmd(
    tender_id: str = typer.Argument(..., help="Mã gói thầu (tender_id hoặc package_number)"),
    bidder: str = typer.Argument(..., help="Tên nhà thầu tham dự"),
    price_vnd: float = typer.Argument(..., help="Giá dự thầu (VND)"),
    tax_id: str = typer.Option("0101234567", "--tax", "--tax-id", help="Mã số thuế nhà thầu"),
    revenue_3yr: float = typer.Option(0.0, "--rev-3yr", "--revenue", help="Doanh thu bình quân 3 năm gần nhất"),
    contract_val: float = typer.Option(0.0, "--contract-val", "--similar", help="Giá trị hợp đồng tương tự đã thực hiện"),
    tech_score: float = typer.Option(85.0, "--tech", "--tech-score", help="Điểm kỹ thuật đánh giá"),
    has_security: bool = typer.Option(True, "--security/--no-security", help="Có bảo đảm dự thầu hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá hồ sơ dự thầu E-HSDT theo quy trình 4 bước của Nghị định 24/2024/NĐ-CP."""
    from src.core.tender_engine import TenderEngine
    r = TenderEngine().evaluate_bid(tender_id=tender_id, bidder_name=bidder, bid_price_vnd=price_vnd, bidder_tax_id=tax_id, revenue_3yr_avg_vnd=revenue_3yr, similar_contract_val_vnd=contract_val, tech_score=tech_score, has_valid_security=has_security)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    if not r.get("ok"):
        console.print(f"[bold red]Lỗi đánh giá:[/] {r.get('error')}")
        return
    sc = "green" if r["overall_qualified"] else "red"
    console.print(Panel(
        f"[bold cyan]KẾT QUẢ ĐÁNH GIÁ E-HSDT: {r['bidder_name']} (MST: {r['bidder_tax_id']})[/]\n\n"
        f"  Gói thầu:             [bold]{r['package_name']}[/] (Dự toán: {_format_vnd(r['budget_vnd'])})\n"
        f"  Giá dự thầu:          [bold yellow]{_format_vnd(r['bid_price_vnd'])}[/] (Tiết kiệm NSNN: [bold green]{r['savings_rate_pct']}%[/])\n"
        f"  Bước 1 (Hợp lệ): {'[bold green]ĐẠT[/]' if r['step_1_eligibility'] else '[bold red]KHÔNG ĐẠT[/]'} | Bước 2 (Năng lực): {'[bold green]ĐẠT[/]' if r['step_2_capacity'] else '[bold red]KHÔNG ĐẠT[/]'}\n"
        f"  Bước 3 (Kỹ thuật): {'[bold green]ĐẠT[/]' if r['step_3_technical'] else '[bold red]KHÔNG ĐẠT[/]'} | Bước 4 (Tài chính): {'[bold green]ĐẠT[/]' if r['step_4_financial'] else '[bold red]KHÔNG ĐẠT[/]'}\n"
        f"  [bold]KẾT LUẬN TỔ CHUYÊN GIA:[/] [bold {sc}]{r['recommendation']}[/bold {sc}] ({r['evaluation_notes']})",
        title="[bold blue]E-HSDT Statutory 4-Step Evaluation[/]", border_style=sc,
    ))


@tender_app.command("collusion-scan")
def collusion_scan_cmd(tender_id: str = typer.Argument(..., help="Mã gói thầu cần rà soát thông thầu"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Quét và phát hiện dấu hiệu vi phạm điều cấm thông thầu / dàn xếp giá theo Điều 16 Luật Đấu thầu 2023."""
    from src.core.tender_engine import TenderEngine
    r = TenderEngine().detect_bid_collusion(tender_id=tender_id)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    if not r.get("ok"):
        console.print(f"[bold red]Lỗi rà soát:[/] {r.get('error')}")
        return
    rk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}.get(r["collusion_risk"], "white")
    flags_text = "".join(f"\n    {idx}. [{rf['severity']}] [bold]{rf['type']}[/]: {rf['description']}\n       -> Căn cứ: {rf['statutory_basis']}" for idx, rf in enumerate(r["red_flags"], 1))
    console.print(Panel(
        f"[bold {rk_color}]KẾT QUẢ RÀ SOÁT TÍNH CẠNH TRANH VÀ DẤU HIỆU THÔNG THẦU[/]\n\n"
        f"  Gói thầu:             [bold]{r['package_name']}[/] | Tổng hồ sơ rà soát: {r['total_bids_scanned']} nhà thầu\n"
        f"  Nguy cơ thông thầu:   [bold {rk_color}]{r['collusion_risk']}[/bold {rk_color}] (Điểm cảnh báo: {r['risk_score']}/100)\n"
        f"  Dấu hiệu bất thường:  {flags_text or 'Không phát hiện hiện tượng dàn xếp giá bất thường.'}\n"
        f"  Kết luận pháp lý:     {r['legal_conclusion']}",
        title="[bold blue]Bid Collusion & Competition Integrity Audit (Điều 16)[/]", border_style=rk_color,
    ))


@tender_app.command("list")
def list_tenders_cmd(status: str = typer.Option("ALL", "--status", "-s", help="Bộ lọc trạng thái (ALL, PUBLISHED, CLOSED)"), limit: int = typer.Option(20, "--limit", "-l", help="Số lượng gói thầu hiển thị"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Truy vấn danh mục các gói thầu điện tử đã phát hành trên hệ thống."""
    from src.core.tender_engine import TenderEngine
    tenders = TenderEngine().list_tenders(status=status, limit=limit)
    if json_mode:
        typer.echo(json.dumps({"ok": True, "tenders": tenders, "total": len(tenders)}, indent=2, ensure_ascii=False))
        return
    console.print(build_table(tenders))


@tender_app.command("status")
def tender_status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON")) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu đấu thầu điện tử và hiệu quả tiết kiệm ngân sách."""
    from src.core.tender_engine import TenderEngine
    s = TenderEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    m = s["metrics"]
    console.print(Panel(
        f"[bold green]THÔNG SỐ QUẢN TRỊ ĐẤU THẦU ĐIỆN TỬ (NATIONAL E-GP)[/]\n\n"
        f"  Trạng thái: {s['status'].upper()} | Khung pháp luật: {s['regulatory_framework']}\n"
        f"  Cổng thông tin: {s['national_egp_system']} | Tổng gói thầu quản lý: {m['total_tenders']} gói thầu\n"
        f"  Tổng dự toán ngân sách: {_format_vnd(m['total_budget_vnd'])} | Hồ sơ dự thầu: {m['total_bids_submitted']} bộ (Đạt: {m['qualified_bids']})\n"
        f"  Tỷ lệ tiết kiệm NSNN: [bold green]{m['average_savings_rate_pct']}%[/] | Cơ sở dữ liệu: {s['database']}",
        title="[bold blue]Tender Engine Telemetry[/]", border_style="green",
    ))
