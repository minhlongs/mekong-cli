# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""IP command panel construction — dashboard, fee schedule, portfolio & status."""

from __future__ import annotations

from typing import Callable

from rich.panel import Panel
from rich.table import Table

# Portfolio listing: one row per asset kind, in trademarks -> patents -> copyrights order.
_PORTFOLIO_COLUMNS = (
    ("Loại TS", "bold"),
    ("Mã hồ sơ", "cyan"),
    ("Tên tác phẩm / Nhãn hiệu", "green"),
    ("Phân nhóm / Lĩnh vực", None),
    ("Trạng thái", "yellow"),
)


def build_portfolio_table(portfolio: dict) -> Table:
    """Build the IP portfolio table; the caller prints it."""
    table = Table(title="Danh Mục Tài Sản Sở Hữu Trí Tuệ", border_style="cyan")
    for header, style in _PORTFOLIO_COLUMNS:
        table.add_column(header, style=style)
    for tm in portfolio["trademarks"]:
        table.add_row("Nhãn hiệu", tm["mark_id"], tm["mark_name"], f"Nhóm {tm['nice_class']}", tm["status"])
    for pat in portfolio["patents"]:
        table.add_row("Sáng chế", pat["patent_id"], pat["title"], pat["technical_field"], pat["status"])
    for cp in portfolio["software_copyrights"]:
        table.add_row("Bản quyền PM", cp["copyright_id"], cp["software_name"], f"v{cp['version']}", cp["status"])
    return table


def build_dashboard(status_data: dict) -> Panel:
    """Build the IP portfolio overview panel; the caller prints it."""
    metrics = status_data["metrics"]
    return Panel(
        f"[bold green]HỆ THỐNG QUẢN LÝ TÀI SẢN TRÍ TUỆ (IP) & BẢO HỘ THƯƠNG HIỆU[/]\n\n"
        f"  Khung quy chuẩn:       [bold]{status_data['regulatory_framework']}[/]\n"
        f"  Phân loại quốc tế:     [bold cyan]{status_data['nice_classification_version']}[/]\n"
        f"  Nhãn hiệu đã nộp:      [bold green]{metrics['registered_trademarks']} đơn[/]\n"
        f"  Sáng chế đã soạn:      [bold yellow]{metrics['drafted_patents']} đơn[/]\n"
        f"  Bản quyền phần mềm:    [bold magenta]{metrics['software_copyrights']} hồ sơ[/]\n"
        f"  Nhóm ngành Nice hỗ trợ: [bold]{metrics['supported_nice_classes']} nhóm ngành trọng yếu[/]",
        title="[bold blue]Intellectual Property Portfolio Dashboard[/]",
        border_style="green",
    )


def build_fees_panel(fees: dict, format_vnd: Callable[[float], str]) -> Panel:
    """Build the statutory fee schedule panel; the caller prints it."""
    return Panel(
        f"[bold cyan]BẢNG TÍNH LỆ PHÍ NHÀ NƯỚC SỞ HỮU TRÍ TUỆ (THÔNG TƯ 263/2016/TT-BTC)[/]\n\n"
        f"  Lệ phí nhãn hiệu:    [bold green]{format_vnd(fees['trademark_fees_vnd'])}[/] ({fees['trademark_classes_count']} nhóm ngành)\n"
        f"  Lệ phí sáng chế:     [bold yellow]{format_vnd(fees['patent_fees_vnd'])}[/] ({fees['patent_claims_count']} điểm yêu cầu bảo hộ)\n"
        f"  Lệ phí bản quyền PM: [bold magenta]{format_vnd(fees['software_copyright_fees_vnd'])}[/] ({fees['software_copyrights_count']} phần mềm)\n"
        f"  ---------------------------------------------------\n"
        f"  [bold]TỔNG LỆ PHÍ NHÀ NƯỚC:[/] [bold green]{format_vnd(fees['total_official_fees_vnd'])}[/]",
        title="[bold blue]State Intellectual Property Fees[/]",
        border_style="cyan",
    )


def build_status_panel(status_data: dict) -> Panel:
    """Build the IP engine telemetry panel; the caller prints it."""
    metrics = status_data["metrics"]
    return Panel(
        f"[bold green]THÔNG SỐ QUẢN TRỊ HỆ THỐNG SỞ HỮU TRÍ TUỆ (IP)[/]\n\n"
        f"  Trạng thái:            {status_data['status'].upper()}\n"
        f"  Khung pháp lý:         {status_data['regulatory_framework']}\n"
        f"  Phân loại Nice:        {status_data['nice_classification_version']}\n"
        f"  Nhãn hiệu đăng ký:     {metrics['registered_trademarks']} đơn\n"
        f"  Sáng chế lưu trữ:      {metrics['drafted_patents']} đơn\n"
        f"  Bản quyền phần mềm:    {metrics['software_copyrights']} hồ sơ\n"
        f"  Cơ sở dữ liệu:         {status_data['database']}",
        title="[bold blue]IP Regulatory Engine Status[/]",
        border_style="green",
    )
