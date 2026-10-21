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
corporate_app = typer.Typer(name="corporate", help="Vietnamese Corporate Governance, Business Incorporation & Statutory Legal Filings", add_completion=False)


def _format_vnd(amount: int) -> str:
    return f"{amount:,} VND".replace(",", ".")


def _print_filings_table(docs: list[dict], title: str, company_col: str, type_col: str) -> None:
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Mã Văn Bản", style="dim", width=18)
    table.add_column(company_col, style="bold cyan")
    table.add_column(type_col, justify="center", style="yellow")
    table.add_column("Tiêu Đề", style="white")
    for d in docs:
        table.add_row(d["doc_id"], d["company_name"], d["doc_type"], d["title"])
    console.print(table)


@corporate_app.callback(invoke_without_command=True)
def corporate_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON")) -> None:
    """Vietnamese Corporate Governance, Business Incorporation & Statutory Legal Filings."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.corporate_engine import CorporateEngine

    engine = CorporateEngine()
    status_data = engine.get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]HỆ THỐNG QUẢN TRỊ DOANH NGHIỆP & HỒ SƠ PHÁP LÝ (LUẬT DOANH NGHIỆP 2020)[/]\n\n"
        f"  Khung quy chuẩn:       [bold]{status_data['governance_framework']}[/]\n"
        f"  Số thực thể đã lập:    [bold cyan]{m['registered_entities']} doanh nghiệp[/]\n"
        f"  Tổng vốn điều lệ:      [bold green]{_format_vnd(m['total_charter_capital_vnd'])}[/]\n"
        f"  Số văn kiện pháp lý:   [bold yellow]{m['statutory_documents_generated']} văn bản (Điều lệ, Nghị quyết)[/]\n"
        f"  Loại hình doanh nghiệp: {', '.join(m['supported_entity_types'])}\n"
        f"  Danh mục mã ngành VSIC: [bold]{m['vsic_sectors_catalog']} nhóm ngành chuẩn[/]",
        title="[bold blue]Corporate Governance & Incorporation Dashboard[/]", border_style="green",
    ))
    docs = engine.list_filings(limit=5)
    if docs:
        _print_filings_table(docs, "Văn Kiện & Hồ Sơ Pháp Lý Gần Nhất", "Tên Doanh Nghiệp", "Loại Văn Kiện")


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

    res = CorporateEngine().generate_charter(company_name=company_name, entity_type=entity_type, charter_capital=capital, legal_rep_name=legal_rep, address=address)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]ĐIỀU LỆ HOẠT ĐỘNG DOANH NGHIỆP: {res['charter_id']}[/]\n\n"
        f"  Tên công ty:        [bold cyan]{res['company_name']}[/]\n  Loại hình:          [bold yellow]{res['entity_type_label']}[/]\n"
        f"  Vốn điều lệ:        [bold green]{res['charter_capital_vnd']}[/]\n  Người đại diện:     [bold]{res['legal_rep_name']}[/]\n"
        f"  Trụ sở chính:       {res['address']}\n"
        f"  Cấu trúc điều lệ:   [bold]{res['chapters_count']} Chương, {res['articles_count']} Điều[/] (Điều 24 Luật DN 2020)",
        title="[bold green]Corporate Charter Generated[/]", border_style="green",
    ))


@corporate_app.command("resolution")
def generate_resolution(
    company_name: str = typer.Argument(..., help="Tên công ty"),
    resolution_type: str = typer.Option("APPOINTMENT", "--type", "-t", help="Loại nghị quyết (APPOINTMENT, CAPITAL_INCREASE, BRANCH)"),
    title: str = typer.Option("", "--title", help="Tiêu đề nghị quyết tùy chỉnh"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soạn thảo Nghị quyết / Quyết định của Hội đồng thành viên / Hội đồng quản trị."""
    from src.core.corporate_engine import CorporateEngine

    res = CorporateEngine().generate_resolution(company_name=company_name, resolution_type=resolution_type, title=title)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold cyan]NGHỊ QUYẾT PHÁP LÝ: {res['resolution_id']}[/]\n\n"
        f"  Doanh nghiệp:       [bold]{res['company_name']}[/]\n  Loại nghị quyết:    [bold yellow]{res['resolution_type']}[/]\n"
        f"  Tiêu đề:            [bold]{res['title']}[/]\n  Số điều quyết nghị: [bold green]{res['decisions_count']} điều khoản[/]",
        title="[bold blue]Corporate Resolution Drafted[/]", border_style="cyan",
    ))


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

    res = CorporateEngine().create_filing_dossier(company_name=company_name, entity_type=entity_type, charter_capital=capital, legal_rep_name=legal_rep, main_industry=industry)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    doc_list_text = "".join(["\n  - " + d["title"] + " [" + d["status"] + "]" for d in res["documents"]])
    console.print(Panel(
        f"[bold green]BỘ HỒ SƠ ĐĂNG KÝ DOANH NGHIỆP: {res['dossier_id']}[/]\n\n"
        f"  Công ty:            [bold cyan]{res['company_name']}[/]\n  Loại hình:          [bold yellow]{res['entity_type_label']}[/]\n"
        f"  Vốn điều lệ:        [bold green]{res['charter_capital_vnd']}[/]\n  Người đại diện:     [bold]{res['legal_rep_name']}[/]\n"
        f"  Ngành nghề chính:   Mã [bold cyan]{res['main_industry']}[/] — {res['main_industry_name']}\n"
        f"  Cổng nộp trực tuyến: [underline blue]{res['filing_portal']}[/]\n  Cơ quan thụ lý:     {res['statutory_authority']}\n\n"
        f"  [bold]Danh mục văn kiện trong hồ sơ:[/{doc_list_text}",
        title="[bold green]Statutory Incorporation Dossier Ready[/]", border_style="green",
    ))


@corporate_app.command("list")
def list_filings(limit: int = typer.Option(20, "--limit", "-n", help="Số lượng văn bản tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Tra cứu các văn kiện pháp lý và hồ sơ đã khởi tạo."""
    from src.core.corporate_engine import CorporateEngine

    docs = CorporateEngine().list_filings(limit=limit)
    if json_mode:
        typer.echo(json.dumps({"filings": docs, "total": len(docs)}, indent=2, ensure_ascii=False))
        return
    if not docs:
        console.print("[yellow]Chưa có văn kiện pháp lý nào được lập.[/]")
        return
    _print_filings_table(docs, "Danh Sách Hồ Sơ & Văn Kiện Pháp Lý", "Công Ty", "Loại")


@corporate_app.command("status")
def corporate_status(json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON")) -> None:
    """Xem trạng thái cơ sở dữ liệu pháp trị và tổng quan đăng ký kinh doanh."""
    from src.core.corporate_engine import CorporateEngine

    status_data = CorporateEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]TRẠNG THÁI CƠ SỞ PHÁP LÝ DOANH NGHIỆP[/]\n\n"
        f"  Trạng thái:            {status_data['status'].upper()}\n  Khung pháp lý:         {status_data['governance_framework']}\n"
        f"  Số thực thể quản lý:   {m['registered_entities']}\n  Số văn bản đã lập:     {m['statutory_documents_generated']}\n"
        f"  Tổng vốn đăng ký:      {_format_vnd(m['total_charter_capital_vnd'])}\n  Cơ sở dữ liệu:         {status_data['database']}",
        title="[bold blue]Corporate Engine Status[/]", border_style="green",
    ))
