# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Post-clearance audit check, IP royalty calculation, and bonded storage subcommands for Customs CLI."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.customs_fx_engine import (
    BondedLogisticsEngine,
    CustomsValuationOriginEngine,
    TechnologyTransferEngine,
)

console = Console()


def register_customs_royalty_storage(customs_app: typer.Typer) -> None:
    """Register audit-check, royalty, and storage-check commands onto customs_app."""
    customs_app.command("audit-check")(check_customs_audit)
    customs_app.command("royalty")(calc_royalty)
    customs_app.command("storage-check")(check_storage_period)


def check_customs_audit(
    declaration_date: str = typer.Argument(..., help="Ngày đăng ký tờ khai hải quan (YYYY-MM-DD)"),
    audit_date: Optional[str] = typer.Option(None, "--audit-date", "-a", help="Ngày kiểm tra (mặc định hôm nay)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra thời hiệu kiểm tra sau thông quan 05 năm (Điều 77 Luật Hải quan 2014)."""
    status = CustomsValuationOriginEngine.check_post_clearance_audit(
        declaration_date_str=declaration_date,
        audit_date_str=audit_date,
    )

    if json_mode:
        typer.echo(json.dumps(status.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold yellow]CÒN TRONG THỜI HIỆU KIỂM TRA[/bold yellow]" if status.is_within_5_year_audit_window else "[bold green]ĐÃ HẾT THỜI HIỆU THÔNG THƯỜNG[/bold green]"

    console.print(
        Panel.fit(
            f"[bold]Tình trạng:[/] {badge}\n"
            f"[bold]Ngày đăng ký tờ khai:[/] {status.declaration_date} | [bold]Ngày kiểm tra:[/] {status.audit_date}\n"
            f"[bold]Số ngày đã trôi qua:[/] {status.days_passed} / 1,825 ngày (05 năm)\n"
            f"[bold]Thời gian còn lại:[/] {status.remaining_days} ngày\n\n"
            f"[bold]Đánh giá pháp lý:[/] {status.advice_vn}",
            title="[bold yellow]Thời Hiệu Kiểm Tra Sau Thông Quan (Điều 77 LHQ)[/bold yellow]",
            border_style="yellow" if status.is_within_5_year_audit_window else "green",
        )
    )


def calc_royalty(
    revenue: float = typer.Argument(..., help="Doanh thu gộp từ sản phẩm sử dụng công nghệ/nhãn hiệu (VNĐ)"),
    rate: float = typer.Option(3.0, "--rate", "-r", help="Tỷ lệ phí bản quyền (%)"),
    discounts: float = typer.Option(0.0, "--discounts", "-d", help="Chiết khấu thương mại và hàng bán trả lại (VNĐ)"),
    shipping: float = typer.Option(0.0, "--shipping", "-s", help="Chi phí đóng gói và vận chuyển (VNĐ)"),
    taxes: float = typer.Option(0.0, "--taxes", "-t", help="Thuế gián thu (VAT, TTĐB) (VNĐ)"),
    profit: Optional[float] = typer.Option(None, "--profit", "-p", help="Lợi nhuận hoạt động dự kiến (để so sánh chuẩn 25% Profit Split) (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính tiền bản quyền (Running Royalty) theo Doanh thu thuần (Điều 22 Luật CGCN 2017)."""
    result = TechnologyTransferEngine.calculate_running_royalty(
        gross_revenue_vnd=revenue,
        discounts_returns_vnd=discounts,
        packing_shipping_vnd=shipping,
        duties_taxes_vnd=taxes,
        royalty_rate_pct=rate,
        projected_operating_profit_vnd=profit,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Tính Tiền Bản Quyền Công Nghệ & SHTT (Running Royalty)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị (VNĐ)", style="yellow", justify="right")

    table.add_row("Doanh thu gộp (Gross Revenue)", f"{result.gross_revenue_vnd:,.0f} VNĐ")
    table.add_row("Tổng các khoản giảm trừ (Deductions)", f"- {result.deductions_vnd:,.0f} VNĐ")
    table.add_row("Doanh thu thuần (Net Sales)", f"{result.net_sales_vnd:,.0f} VNĐ")
    table.add_row("Tỷ lệ phí bản quyền (Royalty Rate)", f"{result.royalty_rate_pct:.2f}%")
    table.add_row("[bold green]Tiền bản quyền phải trả[/]", f"[bold green]{result.royalty_payable_vnd:,.0f} VNĐ[/]")
    if result.profit_split_benchmark_vnd > 0:
        table.add_row("Mức tham chiếu 25% Profit Split", f"{result.profit_split_benchmark_vnd:,.0f} VNĐ")

    console.print(table)
    console.print(f"[bold]Nhận định:[/] {result.advice_vn}")
    console.print(f"[dim]Căn cứ: {result.legal_basis}[/dim]\n")


def check_storage_period(
    facility_type: str = typer.Argument(..., help="Loại kho: 'bonded' (Kho ngoại quan), 'cfs' (Trạm CFS), 'suspended' (Kho bảo thuế)"),
    entry_date: str = typer.Argument(..., help="Ngày hàng hóa đưa vào kho (YYYY-MM-DD)"),
    check_date: Optional[str] = typer.Option(None, "--check-date", "-c", help="Ngày kiểm tra (mặc định hôm nay)"),
    extended: bool = typer.Option(False, "--extended", "-e", help="Hàng đã được gia hạn 1 lần trước đó"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra thời hạn lưu kho ngoại quan (12-24 tháng) & Trạm thu gom hàng lẻ CFS (90 ngày)."""
    status = BondedLogisticsEngine.evaluate_storage_period(
        facility_type=facility_type,
        entry_date_str=entry_date,
        check_date_str=check_date,
        already_extended=extended,
    )

    if json_mode:
        payload = {
            "facility_type": status.facility_type.value,
            "entry_date": status.entry_date,
            "check_date": status.check_date,
            "days_stored": status.days_stored,
            "statutory_max_initial_days": status.statutory_max_initial_days,
            "maximum_possible_days_with_extension": status.maximum_possible_days_with_extension,
            "is_within_initial_term": status.is_within_initial_term,
            "is_expired": status.is_expired,
            "can_request_extension": status.can_request_extension,
            "remaining_initial_days": status.remaining_initial_days,
            "remaining_total_days": status.remaining_total_days,
            "allowed_operations": status.allowed_operations,
            "advice_vn": status.advice_vn,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    badge = "[bold red]ĐÃ HẾT HẠN LƯU KHO[/bold red]" if status.is_expired else "[bold green]TRONG THỜI HẠN LƯU KHO HỢP LỆ[/bold green]"

    console.print(
        Panel.fit(
            f"[bold]Loại hình kho:[/] {status.facility_type.value.upper()}\n"
            f"[bold]Tình trạng:[/] {badge}\n"
            f"[bold]Ngày nhập kho:[/] {status.entry_date} | [bold]Ngày kiểm tra:[/] {status.check_date}\n"
            f"[bold]Số ngày đã lưu kho:[/] {status.days_stored} ngày\n"
            f"[bold]Thời gian còn lại đợt đầu:[/] {status.remaining_initial_days} ngày\n"
            f"[bold]Thời gian tối đa còn lại:[/] {status.remaining_total_days} ngày\n"
            f"[bold]Khả năng xin gia hạn:[/] {'Đủ điều kiện xin gia hạn 12 tháng' if status.can_request_extension else 'Không thể gia hạn thêm'}\n\n"
            f"[bold]Dịch vụ được phép:[/] {', '.join(status.allowed_operations)}\n\n"
            f"[bold]Hướng dẫn:[/] {status.advice_vn}",
            title="[bold green]Thời Hạn Lưu Kho Ngoại Quan & CFS (Điều 61 LHQ)[/bold green]",
            border_style="red" if status.is_expired else "green",
        )
    )
