# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Vietnam Customs, Foreign Exchange & Bonded Logistics CLI Commands (Phases 167 - 170).

Provides CLI commands for:
- Phase 167: Vietnam Customs Valuation & Regional Value Content (RVC) Engine
- Phase 168: SBV Foreign Loan Registration & FDI Profit Remittance Engine
- Phase 169: Technology Transfer & IP Royalty Calculation Engine
- Phase 170: Bonded Warehouse & CFS Storage Duration Engine
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.customs_fx_engine import (
    CustomsValuationOriginEngine,
    ForeignExchangeControlEngine,
    TechnologyTransferEngine,
    BondedLogisticsEngine,
)

customs_app = typer.Typer(
    name="customs",
    help="Customs — Vietnam Customs Valuation, Foreign Exchange, Tech Transfer & Bonded Logistics Suite",
    no_args_is_help=False,
)
console = Console()


@customs_app.callback(invoke_without_command=True)
def customs_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Hải Quan, Quản Lý Ngoại Hối, Chuyển Giao Công Nghệ & Kho Ngoại Quan."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Customs, FX, Tech Transfer & Bonded Logistics Suite",
            "phases": [167, 168, 169, 170],
            "subcommands": [
                "valuation",
                "rvc",
                "audit-check",
                "sbv-loan",
                "profit-remit",
                "tech-registration",
                "royalty",
                "storage-check",
            ],
            "legal_framework": [
                "Luật Hải quan 2014 & Thông tư 39/2015/TT-BTC",
                "Pháp lệnh Ngoại hối & Thông tư 12/2022/TT-NHNN",
                "Luật Chuyển giao công nghệ 2017 & Nghị định 76/2018/NĐ-CP",
                "Điều 61-88 Luật Hải quan 2014 & Nghị định 08/2015/NĐ-CP",
            ],
        }
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    table = Table(
        title="🏛️ MEKONG CUSTOMS, FX, TECH TRANSFER & BONDED LOGISTICS SUITE (PHASES 167-170)",
        box=box.ROUNDED,
    )
    table.add_column("Lệnh (Command)", style="cyan", no_wrap=True)
    table.add_column("Phạm Vi / Căn Cứ", style="yellow")
    table.add_column("Mô Tả Chức Năng", style="green")

    table.add_row("valuation", "Phase 167 (TT 39/2015)", "Tính trị giá hải quan tính thuế (Phương pháp 1)")
    table.add_row("rvc", "Phase 167 (FTAs / ROO)", "Tính hàm lượng giá trị khu vực (RVC Build-down / Build-up)")
    table.add_row("audit-check", "Phase 167 (Điều 77 LHQ)", "Kiểm tra thời hiệu kiểm tra sau thông quan 05 năm")
    table.add_row("sbv-loan", "Phase 168 (TT 12/2022)", "Đánh giá nghĩa vụ đăng ký khoản vay nước ngoài với NHNN")
    table.add_row("profit-remit", "Phase 168 (TT 186/2010)", "Kiểm tra điều kiện chuyển lợi nhuận FDI ra nước ngoài")
    table.add_row("tech-registration", "Phase 169 (Luật CGCN 2017)", "Đánh giá nghĩa vụ đăng ký hợp đồng CGCN tại BKHCN")
    table.add_row("royalty", "Phase 169 (NĐ 76/2018)", "Tính tiền bản quyền theo Doanh thu thuần & 25% Profit Split")
    table.add_row("storage-check", "Phase 170 (Điều 61 LHQ)", "Kiểm tra thời hạn lưu kho ngoại quan (12-24T) & CFS (90N)")

    console.print(table)
    console.print(
        "[dim]Gõ 'mekong customs <command> --help' để xem chi tiết từng lệnh.[/dim]\n"
    )


# ============================================================================
# 1. PHASE 167: CUSTOMS VALUATION & ROO SUBCOMMANDS
# ============================================================================


@customs_app.command("valuation")
def calc_customs_valuation(
    invoice: float = typer.Argument(..., help="Giá mua trên hóa đơn thương mại (VNĐ)"),
    freight: float = typer.Option(0.0, "--freight", "-f", help="Cước vận chuyển quốc tế (F) (VNĐ)"),
    insurance: float = typer.Option(0.0, "--insurance", "-i", help="Phí bảo hiểm quốc tế (I) (VNĐ)"),
    royalties: float = typer.Option(0.0, "--royalties", "-r", help="Tiền bản quyền / phí giấy phép điều chỉnh cộng (VNĐ)"),
    assists: float = typer.Option(0.0, "--assists", "-a", help="Khoản trợ cấp / chi phí cung cấp nguyên phụ liệu (VNĐ)"),
    post_import_freight: float = typer.Option(0.0, "--post-freight", help="Cước vận chuyển sau nhập khẩu điều chỉnh trừ (VNĐ)"),
    post_import_install: float = typer.Option(0.0, "--post-install", help="Chi phí xây dựng, lắp đặt sau nhập khẩu điều chỉnh trừ (VNĐ)"),
    vn_taxes: float = typer.Option(0.0, "--vn-taxes", help="Thuế và phí tại Việt Nam điều chỉnh trừ (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính trị giá hải quan tính thuế theo Phương pháp 1 (Trị giá giao dịch - Điều 5 TT 39/2015/TT-BTC)."""
    result = CustomsValuationOriginEngine.calculate_transaction_value(
        invoice_price_vnd=invoice,
        freight_international_vnd=freight,
        insurance_international_vnd=insurance,
        royalties_license_fees_vnd=royalties,
        assists_value_vnd=assists,
        post_import_inland_freight_vnd=post_import_freight,
        post_import_construction_install_vnd=post_import_install,
        duties_taxes_in_vietnam_vnd=vn_taxes,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Xác Định Trị Giá Hải Quan Tính Thuế (Method 1)", box=box.ROUNDED)
    table.add_column("Chỉ Tiêu", style="cyan")
    table.add_column("Giá Trị (VNĐ)", style="yellow", justify="right")

    table.add_row("Giá hóa đơn (Invoice Price)", f"{result.invoice_price_vnd:,.0f} VNĐ")
    table.add_row("Tổng điều chỉnh cộng (Additions)", f"+ {result.total_additions_vnd:,.0f} VNĐ")
    table.add_row("Tổng điều chỉnh trừ (Deductions)", f"- {result.total_deductions_vnd:,.0f} VNĐ")
    table.add_row("[bold green]Trị giá hải quan tính thuế[/]", f"[bold green]{result.assessable_customs_value_vnd:,.0f} VNĐ[/]")

    console.print(table)
    console.print(f"[bold cyan]Tư vấn:[/] {result.advice_vn}")
    console.print(f"[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


@customs_app.command("rvc")
def calc_rvc(
    fob: float = typer.Argument(..., help="Giá FOB của sản phẩm xuất khẩu (VNĐ)"),
    non_originating: float = typer.Option(0.0, "--vnm", help="Giá trị nguyên liệu không có xuất xứ (VNM) (VNĐ)"),
    originating: float = typer.Option(0.0, "--vom", help="Giá trị nguyên liệu có xuất xứ nội khối (VOM) (VNĐ)"),
    formula: str = typer.Option("build_down", "--formula", help="Công thức tính: 'build_down' (gián tiếp) hoặc 'build_up' (trực tiếp)"),
    threshold: float = typer.Option(40.0, "--threshold", "-t", help="Ngưỡng RVC tối thiểu (%)"),
    agreement: str = typer.Option("ATIGA", "--agreement", "-a", help="Mã hiệp định (ATIGA, ACFTA, CPTPP, EVFTA)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính Hàm lượng giá trị khu vực (RVC) theo Quy tắc xuất xứ hàng hóa (Rules of Origin)."""
    result = CustomsValuationOriginEngine.calculate_regional_value_content(
        fob_price_vnd=fob,
        non_originating_value_vnd=non_originating,
        originating_value_vnd=originating,
        formula=formula,
        threshold_percentage=threshold,
        agreement_code=agreement,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold green]ĐẠT TIÊU CHÍ XUẤT XỨ (ORIGINATING)[/bold green]" if result.is_originating else "[bold red]KHÔNG ĐẠT TIÊU CHÍ (NON-ORIGINATING)[/bold red]"

    console.print(
        Panel.fit(
            f"[bold]Kết quả đánh giá:[/] {badge}\n"
            f"[bold]Hiệp định thương mại:[/] {result.agreement_code}\n"
            f"[bold]Công thức áp dụng:[/] {result.calculation_formula}\n"
            f"[bold]Hàm lượng RVC đạt được:[/] [bold cyan]{result.rvc_percentage:.2f}%[/bold cyan] (Ngưỡng yêu cầu: {result.threshold_percentage:.1f}%)\n"
            f"[bold]Giá FOB thành phẩm:[/] {result.fob_price_vnd:,.0f} VNĐ\n\n"
            f"[bold]Kết luận & Hướng dẫn:[/] {result.advice_vn}",
            title="[bold green]Quy Tắc Xuất Xứ: Hàm Lượng Giá Trị Khu Vực (RVC)[/bold green]",
            border_style="green" if result.is_originating else "red",
        )
    )


@customs_app.command("audit-check")
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


# ============================================================================
# 2. PHASE 168: FOREIGN EXCHANGE & SBV LOAN SUBCOMMANDS
# ============================================================================


@customs_app.command("sbv-loan")
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


@customs_app.command("profit-remit")
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


# ============================================================================
# 3. PHASE 169: TECH TRANSFER & IP ROYALTY SUBCOMMANDS
# ============================================================================


@customs_app.command("tech-registration")
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


@customs_app.command("royalty")
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


# ============================================================================
# 4. PHASE 170: BONDED LOGISTICS SUBCOMMANDS
# ============================================================================


@customs_app.command("storage-check")
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
