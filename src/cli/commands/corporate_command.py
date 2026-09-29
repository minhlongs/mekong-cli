# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Corporate Governance & Business Incorporation (Phase 47)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
corporate_app = typer.Typer(
    name="corporate",
    help="Vietnamese Corporate Governance, Business Incorporation & Statutory Legal Filings",
    add_completion=False,
)


def _format_vnd(amount: int) -> str:
    return f"{amount:,} VND".replace(",", ".")


@corporate_app.callback(invoke_without_command=True)
def corporate_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Vietnamese Corporate Governance, Business Incorporation & Statutory Legal Filings."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN TRỊ DOANH NGHIỆP & HỒ SƠ PHÁP LÝ (LUẬT DOANH NGHIỆP 2020)[/]\n\n"
            f"  Khung quy chuẩn:       [bold]{status_data['governance_framework']}[/]\n"
            f"  Số thực thể đã lập:    [bold cyan]{metrics['registered_entities']} doanh nghiệp[/]\n"
            f"  Tổng vốn điều lệ:      [bold green]{_format_vnd(metrics['total_charter_capital_vnd'])}[/]\n"
            f"  Số văn kiện pháp lý:   [bold yellow]{metrics['statutory_documents_generated']} văn bản (Điều lệ, Nghị quyết)[/]\n"
            f"  Loại hình doanh nghiệp: {', '.join(metrics['supported_entity_types'])}\n"
            f"  Danh mục mã ngành VSIC: [bold]{metrics['vsic_sectors_catalog']} nhóm ngành chuẩn[/]",
            title="[bold blue]Corporate Governance & Incorporation Dashboard[/]",
            border_style="green",
        )
    )

    docs = engine.list_filings(limit=5)
    if docs:
        table = Table(title="Văn Kiện & Hồ Sơ Pháp Lý Gần Nhất", show_header=True, header_style="bold magenta")
        table.add_column("Mã Văn Bản", style="dim", width=18)
        table.add_column("Tên Doanh Nghiệp", style="bold cyan")
        table.add_column("Loại Văn Kiện", justify="center", style="yellow")
        table.add_column("Tiêu Đề", style="white")

        for d in docs:
            table.add_row(
                d["doc_id"],
                d["company_name"],
                d["doc_type"],
                d["title"],
            )
        console.print(table)


@corporate_app.command("charter")
def generate_charter(
    company_name: str = typer.Argument(..., help="Tên công ty tiếng Việt"),
    entity_type: str = typer.Option("TNHH_1TV", "--type", "-t", help="Loại hình (TNHH_1TV, TNHH_2TV, JSC)"),
    capital: int = typer.Option(1_000_000_000, "--capital", "-c", help="Vốn điều lệ (VND)"),
    legal_rep: str = typer.Option("Nguyễn Văn A", "--legal-rep", "-r", help="Họ và tên Người đại diện theo pháp luật"),
    address: str = typer.Option("Hà Nội, Việt Nam", "--address", "-a", help="Địa chỉ trụ sở chính"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tạo Điều lệ hoạt động công ty chuẩn 10 chương theo Điều 24 Luật Doanh nghiệp 2020."""
    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    result = engine.generate_charter(
        company_name=company_name,
        entity_type=entity_type,
        charter_capital=capital,
        legal_rep_name=legal_rep,
        address=address,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐIỀU LỆ HOẠT ĐỘNG DOANH NGHIỆP: {result['charter_id']}[/]\n\n"
            f"  Tên công ty:        [bold cyan]{result['company_name']}[/]\n"
            f"  Loại hình:          [bold yellow]{result['entity_type_label']}[/]\n"
            f"  Vốn điều lệ:        [bold green]{result['charter_capital_vnd']}[/]\n"
            f"  Người đại diện:     [bold]{result['legal_rep_name']}[/]\n"
            f"  Trụ sở chính:       {result['address']}\n"
            f"  Cấu trúc điều lệ:   [bold]{result['chapters_count']} Chương, {result['articles_count']} Điều[/] (Điều 24 Luật DN 2020)",
            title="[bold green]Corporate Charter Generated[/]",
            border_style="green",
        )
    )


@corporate_app.command("resolution")
def generate_resolution(
    company_name: str = typer.Argument(..., help="Tên công ty"),
    resolution_type: str = typer.Option("APPOINTMENT", "--type", "-t", help="Loại nghị quyết (APPOINTMENT, CAPITAL_INCREASE, BRANCH)"),
    title: str = typer.Option("", "--title", help="Tiêu đề nghị quyết tùy chỉnh"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soạn thảo Nghị quyết / Quyết định của Hội đồng thành viên / Hội đồng quản trị."""
    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    result = engine.generate_resolution(
        company_name=company_name,
        resolution_type=resolution_type,
        title=title,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]NGHỊ QUYẾT PHÁP LÝ: {result['resolution_id']}[/]\n\n"
            f"  Doanh nghiệp:       [bold]{result['company_name']}[/]\n"
            f"  Loại nghị quyết:    [bold yellow]{result['resolution_type']}[/]\n"
            f"  Tiêu đề:            [bold]{result['title']}[/]\n"
            f"  Số điều quyết nghị: [bold green]{result['decisions_count']} điều khoản[/]",
            title="[bold blue]Corporate Resolution Drafted[/]",
            border_style="cyan",
        )
    )


@corporate_app.command("dossier")
def create_filing_dossier(
    company_name: str = typer.Argument(..., help="Tên công ty đăng ký thành lập"),
    entity_type: str = typer.Option("TNHH_1TV", "--type", "-t", help="Loại hình (TNHH_1TV, TNHH_2TV, JSC)"),
    capital: int = typer.Option(1_000_000_000, "--capital", "-c", help="Vốn điều lệ (VND)"),
    legal_rep: str = typer.Option("Nguyễn Văn A", "--legal-rep", "-r", help="Người đại diện theo pháp luật"),
    industry: str = typer.Option("6201", "--industry", "-i", help="Mã ngành kinh tế chính (VSIC)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tổng hợp bộ hồ sơ đăng ký thành lập doanh nghiệp theo Nghị định 01/2021/NĐ-CP."""
    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    result = engine.create_filing_dossier(
        company_name=company_name,
        entity_type=entity_type,
        charter_capital=capital,
        legal_rep_name=legal_rep,
        main_industry=industry,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    doc_list_text = "".join(["\n  - " + d["title"] + " [" + d["status"] + "]" for d in result["documents"]])
    console.print(
        Panel(
            f"[bold green]BỘ HỒ SƠ ĐĂNG KÝ DOANH NGHIỆP: {result['dossier_id']}[/]\n\n"
            f"  Công ty:            [bold cyan]{result['company_name']}[/]\n"
            f"  Loại hình:          [bold yellow]{result['entity_type_label']}[/]\n"
            f"  Vốn điều lệ:        [bold green]{result['charter_capital_vnd']}[/]\n"
            f"  Người đại diện:     [bold]{result['legal_rep_name']}[/]\n"
            f"  Ngành nghề chính:   Mã [bold cyan]{result['main_industry']}[/] — {result['main_industry_name']}\n"
            f"  Cổng nộp trực tuyến: [underline blue]{result['filing_portal']}[/]\n"
            f"  Cơ quan thụ lý:     {result['statutory_authority']}\n\n"
            f"  [bold]Danh mục văn kiện trong hồ sơ:[/{doc_list_text}",
            title="[bold green]Statutory Incorporation Dossier Ready[/]",
            border_style="green",
        )
    )


@corporate_app.command("list")
def list_filings(
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng văn bản tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu các văn kiện pháp lý và hồ sơ đã khởi tạo."""
    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    docs = engine.list_filings(limit=limit)

    if json_mode:
        typer.echo(json.dumps({"filings": docs, "total": len(docs)}, indent=2, ensure_ascii=False))
        return

    if not docs:
        console.print("[yellow]Chưa có văn kiện pháp lý nào được lập.[/]")
        return

    table = Table(title="Danh Sách Hồ Sơ & Văn Kiện Pháp Lý", show_header=True, header_style="bold magenta")
    table.add_column("Mã Văn Bản", style="dim", width=18)
    table.add_column("Công Ty", style="bold cyan")
    table.add_column("Loại", justify="center", style="yellow")
    table.add_column("Tiêu Đề", style="white")

    for d in docs:
        table.add_row(
            d["doc_id"],
            d["company_name"],
            d["doc_type"],
            d["title"],
        )
    console.print(table)


@corporate_app.command("status")
def corporate_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON"),
) -> None:
    """Xem trạng thái cơ sở dữ liệu pháp trị và tổng quan đăng ký kinh doanh."""
    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI CƠ SỞ PHÁP LÝ DOANH NGHIỆP[/]\n\n"
            f"  Trạng thái:            {status_data['status'].upper()}\n"
            f"  Khung pháp lý:         {status_data['governance_framework']}\n"
            f"  Số thực thể quản lý:   {metrics['registered_entities']}\n"
            f"  Số văn bản đã lập:     {metrics['statutory_documents_generated']}\n"
            f"  Tổng vốn đăng ký:      {_format_vnd(metrics['total_charter_capital_vnd'])}\n"
            f"  Cơ sở dữ liệu:         {status_data['database']}",
            title="[bold blue]Corporate Engine Status[/]",
            border_style="green",
        )
    )
