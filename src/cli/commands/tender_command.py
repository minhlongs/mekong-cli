# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Public Procurement, National E-GP Electronic Tender & Bid Evaluation Engine (Phase 52)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
tender_app = typer.Typer(
    name="tender",
    help="Public Procurement, National E-GP Electronic Tender Dossiers & Bid Evaluation under Bidding Law 2023",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@tender_app.callback(invoke_without_command=True)
def tender_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Đấu thầu Quốc gia (E-GP), Thẩm định Hồ sơ Mời thầu (E-HSMT) & Đánh giá E-HSDT (Luật Đấu thầu 2023)."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG ĐẤU THẦU ĐIỆN TỬ QUỐC GIA (E-GP) & ĐÁNH GIÁ E-HSDT[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cổng thông tin đấu thầu:[bold cyan]{status_data['national_egp_system']}[/]\n"
            f"  Tổng số gói thầu:      [bold]{metrics['total_tenders']} gói[/] (Tổng dự toán: [bold green]{_format_vnd(metrics['total_budget_vnd'])}[/])\n"
            f"  Hồ sơ dự thầu tiếp nhận: [bold]{metrics['total_bids_submitted']} hồ sơ[/] (Đạt yêu cầu: [bold green]{metrics['qualified_bids']}[/])\n"
            f"  Hiệu quả tiết kiệm NSNN: [bold yellow]{metrics['average_savings_rate_pct']}%[/] bình quân qua đấu thầu cạnh tranh\n"
            f"  Quy trình đánh giá:    [bold]4 bước chuẩn Nghị định 24/2024/NĐ-CP (Hợp lệ -> Năng lực -> Kỹ thuật -> Tài chính)[/]",
            title="[bold blue]National E-GP Public Procurement Dashboard[/]",
            border_style="green",
        )
    )


@tender_app.command("method")
def evaluate_method_cmd(
    package_type: str = typer.Argument(..., help="Loại gói thầu (GOODS, CONSULTING, WORKS, NON_CONSULTING)"),
    budget_vnd: float = typer.Argument(..., help="Giá gói thầu / Dự toán được duyệt (VND)"),
    urgent: bool = typer.Option(False, "--urgent", help="Gói thầu cấp bách, thiên tai, dịch bệnh (Điều 23.1.a)"),
    proprietary: bool = typer.Option(False, "--proprietary", help="Gói thầu công nghệ bản quyền độc quyền (Điều 23.1.c)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định và tư vấn hình thức lựa chọn nhà thầu theo Luật Đấu thầu 2023 (Chỉ định thầu, Chào hàng cạnh tranh, Đấu thầu rộng rãi)."""
    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    result = engine.evaluate_procurement_method(
        package_type=package_type,
        budget_vnd=budget_vnd,
        is_urgent=urgent,
        is_proprietary_tech=proprietary,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    method_color = "green" if result["recommended_method"] == "OPEN_BIDDING" else ("yellow" if result["recommended_method"] == "COMPETITIVE_QUOTATION" else "cyan")

    console.print(
        Panel(
            f"[bold {method_color}]KẾT QUẢ THẨM ĐỊNH HÌNH THỨC LỰA CHỌN NHÀ THẦU[/]\n\n"
            f"  Loại gói thầu:        [bold]{result['package_type']}[/] (Dự toán: {_format_vnd(result['budget_vnd'])})\n"
            f"  Hình thức đề xuất:    [bold {method_color}]{result['recommended_method']}[/bold {method_color}]\n"
            f"  Căn cứ pháp lý:       [bold]{result['governing_article']}[/]\n"
            f"  Lý do thẩm định:      {result['statutory_justification']}\n"
            f"  Hạn mức chỉ định thầu: {_format_vnd(result['direct_contracting_cap_vnd'])}\n"
            f"  Bảo đảm dự thầu:      {'Bắt buộc' if result['bid_security_required'] else 'Không yêu cầu'}"
            + (f" ({result['bid_security_rate_pct']}% ~ {_format_vnd(result['bid_security_estimated_vnd'])})" if result["bid_security_required"] else ""),
            title="[bold blue]Procurement Method Advisory[/]",
            border_style=method_color,
        )
    )


@tender_app.command("create")
def create_tender_cmd(
    name: str = typer.Argument(..., help="Tên gói thầu"),
    entity: str = typer.Argument(..., help="Tên bên mời thầu / Chủ đầu tư"),
    budget_vnd: float = typer.Argument(..., help="Giá gói thầu dự toán (VND)"),
    package_type: str = typer.Option("GOODS", "--type", "-t", help="Loại gói thầu (GOODS, CONSULTING, WORKS, NON_CONSULTING)"),
    method: str = typer.Option(None, "--method", "-m", help="Hình thức lựa chọn nhà thầu (Mặc định tự động thẩm định)"),
    days: int = typer.Option(15, "--days", "-d", help="Thời gian chuẩn bị E-HSDT (ngày)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tạo lập và phát hành gói thầu E-HSMT trên Hệ thống Mạng Đấu thầu Quốc gia."""
    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    result = engine.create_tender(
        package_name=name,
        procuring_entity=entity,
        budget_vnd=budget_vnd,
        package_type=package_type,
        procurement_method=method,
        submission_days=days,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    crit = result["statutory_criteria"]

    console.print(
        Panel(
            f"[bold green]ĐÃ PHÁT HÀNH HỒ SƠ MỜI THẦU ĐIỆN TỬ (E-HSMT): {result['package_number']}[/]\n\n"
            f"  Tên gói thầu:         [bold cyan]{result['package_name']}[/]\n"
            f"  Bên mời thầu:         [bold]{result['procuring_entity']}[/]\n"
            f"  Hình thức đấu thầu:   [bold yellow]{result['procurement_method']}[/] ({result['package_type']})\n"
            f"  Giá gói thầu:         [bold green]{_format_vnd(result['budget_vnd'])}[/]\n"
            f"  Bảo đảm dự thầu:      [bold magenta]{_format_vnd(result['bid_security_vnd'])}[/]\n"
            f"  Hạn nộp E-HSDT:       {result['submission_deadline']}\n"
            f"  Tiêu chuẩn năng lực:  Doanh thu 3 năm >= {_format_vnd(crit['min_3yr_avg_revenue_vnd'])} | HĐ tương tự >= {_format_vnd(crit['min_similar_contract_val_vnd'])}\n"
            f"  Hệ thống phát hành:   {result['egp_system']}",
            title="[bold green]E-HSMT Published on National E-GP[/]",
            border_style="green",
        )
    )


@tender_app.command("eval")
def evaluate_bid_cmd(
    tender_id: str = typer.Argument(..., help="Mã gói thầu (tender_id hoặc package_number)"),
    bidder: str = typer.Argument(..., help="Tên nhà thầu tham dự"),
    price_vnd: float = typer.Argument(..., help="Giá dự thầu (VND)"),
    tax_id: str = typer.Option("0101234567", "--tax", "--tax-id", help="Mã số thuế nhà thầu"),
    revenue_3yr: float = typer.Option(0.0, "--rev-3yr", "--revenue", help="Doanh thu bình quân 3 năm gần nhất"),
    contract_val: float = typer.Option(0.0, "--contract-val", "--similar", help="Giá trị hợp đồng tương tự đã thực hiện"),
    tech_score: float = typer.Option(85.0, "--tech", "--tech-score", help="Điểm kỹ thuật đánh giá (thang điểm 100, sàn 70)"),
    has_security: bool = typer.Option(True, "--security/--no-security", help="Có bảo đảm dự thầu hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá hồ sơ dự thầu E-HSDT theo quy trình 4 bước của Nghị định 24/2024/NĐ-CP."""
    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    result = engine.evaluate_bid(
        tender_id=tender_id,
        bidder_name=bidder,
        bid_price_vnd=price_vnd,
        bidder_tax_id=tax_id,
        revenue_3yr_avg_vnd=revenue_3yr,
        similar_contract_val_vnd=contract_val,
        tech_score=tech_score,
        has_valid_security=has_security,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not result.get("ok"):
        console.print(f"[bold red]Lỗi đánh giá:[/] {result.get('error')}")
        return

    status_color = "green" if result["overall_qualified"] else "red"

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ ĐÁNH GIÁ E-HSDT: {result['bidder_name']} (MST: {result['bidder_tax_id']})[/]\n\n"
            f"  Gói thầu:             [bold]{result['package_name']}[/] (Dự toán: {_format_vnd(result['budget_vnd'])})\n"
            f"  Giá dự thầu:          [bold yellow]{_format_vnd(result['bid_price_vnd'])}[/] (Tiết kiệm NSNN: [bold green]{result['savings_rate_pct']}%[/])\n"
            f"  Bước 1 (Tính hợp lệ): {'[bold green]ĐẠT[/]' if result['step_1_eligibility'] else '[bold red]KHÔNG ĐẠT[/]'}\n"
            f"  Bước 2 (Năng lực):    {'[bold green]ĐẠT[/]' if result['step_2_capacity'] else '[bold red]KHÔNG ĐẠT[/]'}\n"
            f"  Bước 3 (Kỹ thuật):    {'[bold green]ĐẠT[/]' if result['step_3_technical'] else '[bold red]KHÔNG ĐẠT[/]'}\n"
            f"  Bước 4 (Tài chính):   {'[bold green]ĐẠT[/]' if result['step_4_financial'] else '[bold red]KHÔNG ĐẠT[/]'}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]KẾT LUẬN TỔ CHUYÊN GIA:[/] [bold {status_color}]{result['recommendation']}[/bold {status_color}]\n"
            f"  Ghi chú đánh giá:     {result['evaluation_notes']}",
            title="[bold blue]E-HSDT Statutory 4-Step Evaluation[/]",
            border_style=status_color,
        )
    )


@tender_app.command("collusion-scan")
def collusion_scan_cmd(
    tender_id: str = typer.Argument(..., help="Mã gói thầu cần rà soát thông thầu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Quét và phát hiện dấu hiệu vi phạm điều cấm thông thầu / dàn xếp giá theo Điều 16 Luật Đấu thầu 2023."""
    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    result = engine.detect_bid_collusion(tender_id=tender_id)

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not result.get("ok"):
        console.print(f"[bold red]Lỗi rà soát:[/] {result.get('error')}")
        return

    color_map = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}
    rk_color = color_map.get(result["collusion_risk"], "white")

    flags_text = ""
    for idx, rf in enumerate(result["red_flags"], 1):
        flags_text += f"\n    {idx}. [{rf['severity']}] [bold]{rf['type']}[/]: {rf['description']}\n       -> Căn cứ: {rf['statutory_basis']}"

    console.print(
        Panel(
            f"[bold {rk_color}]KẾT QUẢ RÀ SOÁT TÍNH CẠNH TRANH VÀ DẤU HIỆU THÔNG THẦU[/]\n\n"
            f"  Gói thầu:             [bold]{result['package_name']}[/]\n"
            f"  Tổng hồ sơ rà soát:   {result['total_bids_scanned']} nhà thầu tham dự\n"
            f"  Nguy cơ thông thầu:   [bold {rk_color}]{result['collusion_risk']}[/bold {rk_color}] (Điểm cảnh báo: {result['risk_score']}/100)\n"
            f"  Dấu hiệu bất thường:  {flags_text if flags_text else 'Không phát hiện hiện tượng dàn xếp giá bất thường.'}\n"
            f"  Kết luận pháp lý:     {result['legal_conclusion']}",
            title="[bold blue]Bid Collusion & Competition Integrity Audit (Điều 16)[/]",
            border_style=rk_color,
        )
    )


@tender_app.command("list")
def list_tenders_cmd(
    status: str = typer.Option("ALL", "--status", "-s", help="Bộ lọc trạng thái (ALL, PUBLISHED, CLOSED)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng gói thầu hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục các gói thầu điện tử đã phát hành trên hệ thống."""
    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    tenders = engine.list_tenders(status=status, limit=limit)

    if json_mode:
        typer.echo(json.dumps({"ok": True, "tenders": tenders, "total": len(tenders)}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Danh Mục Gói Thầu Mua Sắm Công (National E-GP)", border_style="cyan")
    table.add_column("Mã gói thầu", style="cyan")
    table.add_column("Số E-GP", style="bold")
    table.add_column("Tên gói thầu", style="white")
    table.add_column("Chủ đầu tư", style="green")
    table.add_column("Hình thức", style="yellow")
    table.add_column("Dự toán (VND)", style="magenta")
    table.add_column("Trạng thái")

    for t in tenders:
        table.add_row(
            t["tender_id"],
            t["package_number"],
            t["package_name"],
            t["procuring_entity"],
            t["procurement_method"],
            _format_vnd(t["budget_vnd"]),
            t["status"],
        )

    console.print(table)


@tender_app.command("status")
def tender_status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON"),
) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu đấu thầu điện tử và hiệu quả tiết kiệm ngân sách."""
    from src.core.tender_engine import TenderEngine

    engine = TenderEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]THÔNG SỐ QUẢN TRỊ ĐẤU THẦU ĐIỆN TỬ (NATIONAL E-GP)[/]\n\n"
            f"  Trạng thái:            {status_data['status'].upper()}\n"
            f"  Khung pháp luật:       {status_data['regulatory_framework']}\n"
            f"  Cổng thông tin:        {status_data['national_egp_system']}\n"
            f"  Tổng gói thầu quản lý: {metrics['total_tenders']} gói thầu\n"
            f"  Tổng dự toán ngân sách: {_format_vnd(metrics['total_budget_vnd'])}\n"
            f"  Hồ sơ dự thầu:         {metrics['total_bids_submitted']} bộ (Đạt: {metrics['qualified_bids']})\n"
            f"  Tỷ lệ tiết kiệm NSNN:  [bold green]{metrics['average_savings_rate_pct']}%[/]\n"
            f"  Cơ sở dữ liệu:         {status_data['database']}",
            title="[bold blue]Tender Engine Telemetry[/]",
            border_style="green",
        )
    )
