# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SBV foreign loan, FDI profit remittance, and tech transfer registration subcommands for Customs CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel

from src.core.customs_fx_engine import (
    ForeignExchangeControlEngine,
    TechnologyTransferEngine,
)

console = Console()


def register_customs_fx_tech(customs_app: typer.Typer) -> None:
    """Register sbv-loan, profit-remit, and tech-registration commands onto customs_app."""
    customs_app.command("sbv-loan")(evaluate_sbv_loan)
    customs_app.command("profit-remit")(check_profit_remittance)
    customs_app.command("tech-registration")(check_tech_registration)


def evaluate_sbv_loan(
    amount: float = typer.Argument(..., help="Số tiền gốc khoản vay nước ngoài"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Loại tiền tệ (USD, EUR, JPY, v.v.)"),
    tenor: int = typer.Option(..., "--tenor", "-t", help="Thời hạn khoản vay (tháng)"),
    is_extended: bool = typer.Option(False, "--extended", help="Khoản vay ngắn hạn gia hạn thành trên 1 năm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá nghĩa vụ đăng ký khoản vay nước ngoài với Ngân hàng Nhà nước (Thông tư 12/2022/TT-NHNN)."""
    result = ForeignExchangeControlEngine.evaluate_sbv_loan_registration(
        principal_amount=amount,
        currency=currency,
        tenor_months=tenor,
        is_extended_short_term=is_extended,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold red]BẮT BUỘC ĐĂNG KÝ VỚI NHNN[/bold red]" if result.requires_sbv_registration else "[bold green]KHÔNG PHẢI ĐĂNG KÝ NHNN[/bold green]"

    console.print(
        Panel.fit(
            f"[bold]Đánh giá nghĩa vụ:[/] {badge}\n"
            f"[bold]Số tiền khoản vay:[/] {result.principal_amount:,.2f} {result.currency}\n"
            f"[bold]Thời hạn vay:[/] {result.tenor_months} tháng ({result.tenor_category.value})\n"
            f"[bold]Thời hạn nộp hồ sơ đăng ký:[/] {result.registration_deadline_days} ngày làm việc kể từ ngày ký hợp đồng vay\n"
            f"[bold]Yêu cầu tài khoản:[/] {result.account_type_required}\n\n"
            f"[bold cyan]Hướng dẫn tuân thủ:[/] {result.advice_vn}\n"
            f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]",
            title="[bold yellow]Quản Lý Ngoại Hối: Đăng Ký Vay Nước Ngoài (SBV)[/bold yellow]",
            border_style="red" if result.requires_sbv_registration else "green",
        )
    )


def check_profit_remittance(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp FDI"),
    profit: float = typer.Argument(..., help="Lợi nhuận sau thuế năm hiện tại (VNĐ)"),
    losses: float = typer.Option(0.0, "--losses", "-l", help="Lỗ lũy kế chưa chuyển (VNĐ)"),
    audited: bool = typer.Option(True, "--audited/--no-audited", help="Đã có Báo cáo tài chính kiểm toán độc lập"),
    tax_clean: bool = typer.Option(True, "--tax-clean/--tax-debt", help="Đã hoàn thành toàn bộ nghĩa vụ thuế TNDN"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra điều kiện chuyển lợi nhuận FDI ra nước ngoài (Thông tư 186/2010/TT-BTC)."""
    result = ForeignExchangeControlEngine.check_fdi_profit_remittance(
        enterprise_name=enterprise,
        current_year_net_profit_vnd=profit,
        accumulated_losses_vnd=losses,
        has_audited_financial_statements=audited,
        tax_obligations_completed=tax_clean,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold green]ĐỦ ĐIỀU KIỆN CHUYỂN LỢI NHUẬN[/bold green]" if result.is_eligible_for_remittance else "[bold red]CHƯA ĐỦ ĐIỀU KIỆN CHUYỂN TIỀN[/bold red]"

    console.print(
        Panel.fit(
            f"[bold]Doanh nghiệp:[/] {result.fdi_enterprise_name}\n"
            f"[bold]Kết luận:[/] {badge}\n"
            f"[bold]Lợi nhuận ròng năm:[/] {result.net_profit_vnd:,.0f} VNĐ\n"
            f"[bold]Lỗ lũy kế tồn đọng:[/] {result.accumulated_losses_vnd:,.0f} VNĐ\n"
            f"[bold]BCTC kiểm toán:[/] {'Đã có' if result.has_audited_financial_report else 'Chưa có'}\n"
            f"[bold]Nghĩa vụ thuế:[/] {'Đã hoàn thành' if result.tax_obligations_completed else 'Còn nợ thuế'}\n"
            f"[bold green]Số tiền tối đa được chuyển:[/] [bold green]{result.maximum_remittance_amount_vnd:,.0f} VNĐ[/bold green]\n\n"
            f"[bold]Hướng dẫn:[/] {result.advice_vn}",
            title="[bold green]Chuyển Lợi Nhuận FDI Ra Nước Ngoài (TT 186/2010)[/bold green]",
            border_style="green" if result.is_eligible_for_remittance else "red",
        )
    )


def check_tech_registration(
    transfer_type: str = typer.Argument(..., help="Loại hình chuyển giao (ví dụ: 'Nhập khẩu công nghệ từ Đức')"),
    cross_border: bool = typer.Option(True, "--cross-border/--domestic", help="Chuyển giao công nghệ xuyên biên giới"),
    state_capital: bool = typer.Option(False, "--state-capital/--private-capital", help="Có sử dụng ngân sách hoặc vốn nhà nước"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá nghĩa vụ đăng ký hợp đồng Chuyển giao công nghệ tại BKHCN (Điều 31 Luật CGCN 2017)."""
    result = TechnologyTransferEngine.evaluate_contract_registration(
        transfer_type=transfer_type,
        is_cross_border=cross_border,
        involves_state_capital=state_capital,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold red]BẮT BUỘC ĐĂNG KÝ TẠI BKHCN / SỞ KHCN[/bold red]" if result.requires_mandatory_registration else "[bold green]ĐĂNG KÝ TỰ NGUYỆN[/bold green]"

    console.print(
        Panel.fit(
            f"[bold]Đối tượng CGCN:[/] {result.transfer_type}\n"
            f"[bold]Nghĩa vụ đăng ký:[/] {badge}\n"
            f"[bold]Cơ quan tiếp nhận:[/] {result.registration_authority}\n"
            f"[bold]Thời hạn nộp hồ sơ:[/] {result.registration_deadline_days} ngày kể từ ngày ký hợp đồng\n\n"
            f"[bold]Khuyến nghị:[/] {result.advice_vn}",
            title="[bold cyan]Đăng Ký Hợp Đồng Chuyển Giao Công Nghệ (Luật CGCN 2017)[/bold cyan]",
            border_style="red" if result.requires_mandatory_registration else "green",
        )
    )
