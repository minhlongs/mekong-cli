# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Foreign Direct Investment (FDI) & SBV Capital Compliance (Phase 48)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
fdi_app = typer.Typer(
    name="fdi",
    help="Foreign Direct Investment (FDI), DICA Capital Accounts & SBV Foreign Loan Compliance",
    add_completion=False,
)


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@fdi_app.callback(invoke_without_command=True)
def fdi_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Foreign Direct Investment (FDI), DICA Capital Accounts & SBV Foreign Loan Compliance."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.fdi_engine import FdiEngine

    engine = FdiEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ ĐẦU TƯ TRỰC TIẾP NƯỚC NGOÀI (FDI) & NGOẠI HỐI NHNN[/]\n\n"
            f"  Khung quy chuẩn:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Tỷ giá tham chiếu:     [bold cyan]1 USD = {_format_vnd(status_data['reference_exchange_rate'])}[/]\n"
            f"  Dự án FDI đăng ký:     [bold]{metrics['active_fdi_projects']} dự án[/] (Tổng vốn: [bold green]{_format_usd(metrics['total_invested_capital_usd'])}[/])\n"
            f"  Khoản vay nước ngoài:  [bold yellow]{metrics['total_foreign_loans_registered']} khoản vay[/] (Tổng trị giá: [bold yellow]{_format_usd(metrics['total_foreign_loans_usd'])}[/])\n"
            f"  Chuyển lợi nhuận ngoại tệ: [bold magenta]{metrics['total_profit_remittances']} đợt[/] (Tổng tiền: [bold magenta]{_format_usd(metrics['total_profit_remitted_usd'])}[/])\n"
            f"  Ngành cam kết mở cửa:  [bold]{metrics['supported_market_sectors']} nhóm ngành (WTO, CPTPP, EVFTA)[/]",
            title="[bold blue]FDI & SBV Capital Compliance Dashboard[/]",
            border_style="green",
        )
    )


@fdi_app.command("market-access")
def check_market_access(
    sector: str = typer.Argument(..., help="Mã phân ngành (IT_SOFTWARE, DATA_PROCESSING, MANAGEMENT_CONSULTING, TELECOM_VALUE_ADDED, LOGISTICS_FREIGHT, ADVERTISING)"),
    ratio: float = typer.Option(100.0, "--ratio", "-r", help="Tỷ lệ sở hữu vốn nước ngoài dự kiến (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu điều kiện tiếp cận thị trường và trần sở hữu vốn nước ngoài (FDI)."""
    from src.core.fdi_engine import FdiEngine

    engine = FdiEngine()
    result = engine.check_market_access(sector_code=sector, foreign_ratio=ratio)

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not result.get("ok"):
        console.print(f"[bold red]Lỗi:[/] {result.get('error')}")
        return

    status_color = "green" if result["is_compliant"] else "red"

    console.print(
        Panel(
            f"[bold cyan]ĐIỀU KIỆN TIẾP CẬN THỊ TRƯỜNG FDI — {result['sector_name'].upper()}[/]\n\n"
            f"  Phân ngành:          {result['sector_code']} ({result['cpc_code']})\n"
            f"  Tỷ lệ đề xuất:       [bold]{result['requested_ratio']}%[/]\n"
            f"  Trần tối đa cho phép: [bold green]{result['max_allowed_ratio']}%[/]\n"
            f"  Kết luận thẩm định:  [bold {status_color}]{result['verdict']}[/bold {status_color}]\n"
            f"  Hiệp ước áp dụng:    {', '.join(result['treaties'])}\n"
            f"  Điều kiện chi tiết:  {result['conditions']}",
            title="[bold blue]FDI Market Access Verification[/]",
            border_style="cyan",
        )
    )


@fdi_app.command("remittance")
def verify_remittance(
    amount_usd: float = typer.Argument(..., help="Số tiền lợi nhuận muốn chuyển ra nước ngoài (USD)"),
    tax_year: int = typer.Argument(..., help="Năm tài chính phát sinh lợi nhuận"),
    audited: bool = typer.Option(False, "--audited", "-a", help="Đã có Báo cáo tài chính kiểm toán độc lập"),
    tax_cleared: bool = typer.Option(False, "--tax-cleared", "-t", help="Đã hoàn thành nghĩa vụ quyết toán thuế TNDN"),
    loss: float = typer.Option(0.0, "--loss", "-l", help="Số lỗ lũy kế chưa chuyển (USD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện chuyển lợi nhuận hợp pháp ra nước ngoài (Thông tư 186/2010/TT-BTC)."""
    from src.core.fdi_engine import FdiEngine

    engine = FdiEngine()
    result = engine.verify_profit_remittance(
        amount_usd=amount_usd,
        tax_year=tax_year,
        is_audited=audited,
        has_tax_clearance=tax_cleared,
        accumulated_loss_usd=loss,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_eligible"] else "red"
    deficiency_text = ""
    if result["deficiencies"]:
        deficiency_text = "\n\n[bold red]Khiếm khuyết cần khắc phục:[/]\n" + "\n".join(["- " + d for d in result["deficiencies"]])

    console.print(
        Panel(
            f"[bold cyan]THẨM ĐỊNH HỒ SƠ CHUYỂN LỢI NHUẬN RA NƯỚC NGOÀI: {result['remittance_id']}[/]\n\n"
            f"  Số tiền chuyển:      [bold green]{_format_usd(result['amount_usd'])}[/] (~ {_format_vnd(result['amount_vnd'])})\n"
            f"  Năm tài chính:       Kỳ {result['tax_year']}\n"
            f"  Kết quả xét duyệt:   [bold {status_color}]{result['status']}[/bold {status_color}]\n"
            f"  Bắt buộc chuyển qua: [bold yellow]Tài khoản DICA mở tại ngân hàng được phép[/]\n"
            f"  Thời hạn thông báo:  Ít nhất 07 ngày làm việc trước khi chuyển gửi cơ quan thuế"
            f"{deficiency_text}",
            title="[bold blue]Profit Remittance Assessment (TT 186/2010)[/]",
            border_style="green" if result["is_eligible"] else "red",
        )
    )


@fdi_app.command("foreign-loan")
def evaluate_loan(
    amount_usd: float = typer.Argument(..., help="Số tiền vay nước ngoài (USD)"),
    tenor_months: int = typer.Argument(..., help="Thời hạn vay (tháng)"),
    interest_rate: float = typer.Argument(..., help="Lãi suất vay (%/năm)"),
    lender: str = typer.Option("Tổ chức tài chính quốc tế", "--lender", "-l", help="Bên cho vay nước ngoài"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định đăng ký khoản vay nước ngoài với Ngân hàng Nhà nước (Thông tư 12/2022/TT-NHNN)."""
    from src.core.fdi_engine import FdiEngine

    engine = FdiEngine()
    result = engine.evaluate_foreign_loan(
        amount_usd=amount_usd,
        tenor_months=tenor_months,
        interest_rate_pct=interest_rate,
        lender_name=lender,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    req_color = "red" if result["sbv_registration_required"] else "green"
    req_text = "BẮT BUỘC ĐĂNG KÝ VỚI NHNN TRƯỚC KHI RÚT VỐN" if result["sbv_registration_required"] else "KHÔNG YÊU CẦU ĐĂNG KÝ TRƯỚC (BÁO CÁO ĐỊNH KỲ QUÝ)"

    console.print(
        Panel(
            f"[bold cyan]THẨM ĐỊNH KHOẢN VAY NƯỚC NGOÀI: {result['loan_id']}[/]\n\n"
            f"  Số tiền vay:         [bold green]{_format_usd(result['amount_usd'])}[/] (~ {_format_vnd(result['amount_vnd'])})\n"
            f"  Thời hạn vay:        [bold]{result['tenor_months']} tháng[/] ({result['loan_type']})\n"
            f"  Lãi suất thỏa thuận: [bold yellow]{result['interest_rate_pct']}%/năm[/] (Đánh giá: {result['interest_status']})\n"
            f"  Nghĩa vụ với NHNN:   [bold {req_color}]{req_text}[/bold {req_color}]\n"
            f"  Quy định trích dẫn:  Thông tư 12/2022/TT-NHNN về vay, trả nợ nước ngoài của doanh nghiệp",
            title="[bold blue]Foreign Loan SBV Compliance Evaluation[/]",
            border_style="cyan",
        )
    )


@fdi_app.command("irc")
def generate_irc(
    project_name: str = typer.Argument(..., help="Tên dự án đầu tư nước ngoài"),
    capital_usd: float = typer.Argument(..., help="Quy mô vốn đầu tư (USD)"),
    investor: str = typer.Option("Singapore", "--investor", "-i", help="Quốc gia nhà đầu tư"),
    sector: str = typer.Option("IT_SOFTWARE", "--sector", "-s", help="Lĩnh vực đầu tư"),
    location: str = typer.Option("Hà Nội", "--location", "-l", help="Địa điểm thực hiện dự án"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soạn thảo hồ sơ đề xuất dự án xin cấp Giấy chứng nhận đăng ký đầu tư (IRC)."""
    from src.core.fdi_engine import FdiEngine

    engine = FdiEngine()
    result = engine.generate_irc_dossier(
        project_name=project_name,
        capital_usd=capital_usd,
        investor_country=investor,
        sector_code=sector,
        location=location,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    doc_list_text = "".join(["\n  - " + d["title"] + " [" + d["status"] + "]" for d in result["documents"]])

    console.print(
        Panel(
            f"[bold green]HỒ SƠ XIN CẤP GIẤY CHỨNG NHẬN ĐẦU TƯ (IRC): {result['project_id']}[/]\n\n"
            f"  Tên dự án:           [bold cyan]{result['project_name']}[/]\n"
            f"  Quốc gia đầu tư:     [bold]{result['investor_country']}[/]\n"
            f"  Quy mô vốn:          [bold green]{_format_usd(result['capital_usd'])}[/] (~ {_format_vnd(result['capital_vnd'])})\n"
            f"  Ngành nghề:          {result['sector_name']} ({result['sector_code']})\n"
            f"  Địa điểm thực hiện:  {result['location']}\n"
            f"  Cơ quan cấp phép:    {result['statutory_authority']}\n"
            f"  Thời hạn giải quyết: {result['statutory_timeline']}\n\n"
            f"  [bold]Danh mục hồ sơ thành phần:[/{doc_list_text}",
            title="[bold green]Investment Registration Certificate (IRC) Dossier Ready[/]",
            border_style="green",
        )
    )


@fdi_app.command("status")
def fdi_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON"),
) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu đầu tư nước ngoài và quản lý ngoại hối."""
    from src.core.fdi_engine import FdiEngine

    engine = FdiEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]THÔNG SỐ QUẢN TRỊ DÒNG VỐN ĐẦU TƯ FDI & NGOẠI HỐI[/]\n\n"
            f"  Trạng thái:            {status_data['status'].upper()}\n"
            f"  Khung pháp lý:         {status_data['regulatory_framework']}\n"
            f"  Tỷ giá tham chiếu:     1 USD = {_format_vnd(status_data['reference_exchange_rate'])}\n"
            f"  Dự án FDI quản lý:     {metrics['active_fdi_projects']} dự án ({_format_usd(metrics['total_invested_capital_usd'])})\n"
            f"  Khoản vay đăng ký:     {metrics['total_foreign_loans_registered']} khoản ({_format_usd(metrics['total_foreign_loans_usd'])})\n"
            f"  Lợi nhuận chuyển đi:   {metrics['total_profit_remittances']} đợt ({_format_usd(metrics['total_profit_remitted_usd'])})\n"
            f"  Cơ sở dữ liệu:         {status_data['database']}",
            title="[bold blue]FDI Regulatory Engine Status[/]",
            border_style="green",
        )
    )
