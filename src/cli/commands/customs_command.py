# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnam Customs, Foreign Exchange & Bonded Logistics CLI Commands (Phases 167 - 170)."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._customs_fx_tech import (
    check_profit_remittance,
    check_tech_registration,
    evaluate_sbv_loan,
    register_customs_fx_tech,
)
from src.cli.commands._customs_royalty_storage import (
    calc_royalty,
    check_customs_audit,
    check_storage_period,
    register_customs_royalty_storage,
)
from src.core.customs_fx_engine import (
    BondedLogisticsEngine,
    CustomsValuationOriginEngine,
    ForeignExchangeControlEngine,
    TechnologyTransferEngine,
)
from src.core.customs_engine import CustomsEngine

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
        summary = CustomsEngine().get_status()
        summary.update({
            "suite": "Mekong Customs, FX, Tech Transfer & Bonded Logistics Suite",
            "phases": [167, 168, 169, 170],
            "subcommands": [
                "hs-lookup", "duty-calc", "channel", "declare", "origin", "list", "status",
                "valuation", "rvc", "audit-check", "sbv-loan", "profit-remit",
                "tech-registration", "royalty", "storage-check",
            ],
            "legal_framework": [
                "Luật Hải quan 2014 & Thông tư 39/2015/TT-BTC", "Pháp lệnh Ngoại hối & Thông tư 12/2022/TT-NHNN",
                "Luật Chuyển giao công nghệ 2017 & Nghị định 76/2018/NĐ-CP", "Điều 61-88 Luật Hải quan 2014 & Nghị định 08/2015/NĐ-CP",
            ],
        })
        typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    table = Table(title="🏛️ MEKONG CUSTOMS, FX, TECH TRANSFER & BONDED LOGISTICS SUITE (PHASES 167-170)", box=box.ROUNDED)
    table.add_column("Lệnh (Command)", style="cyan", no_wrap=True)
    table.add_column("Phạm Vi / Căn Cứ", style="yellow")
    table.add_column("Mô Tả Chức Năng", style="green")
    for cmd, phase, desc in [
        ("hs-lookup / duty-calc / channel", "VNACCS / AHTN", "Tra cứu mã HS, tính thuế nhập khẩu và phân luồng tờ khai"),
        ("declare / origin / list / status", "VNACCS / VCIS", "Lập tờ khai điện tử, xác minh xuất xứ và theo dõi hồ sơ"),
        ("valuation", "Phase 167 (TT 39/2015)", "Tính trị giá hải quan tính thuế (Phương pháp 1)"),
        ("rvc", "Phase 167 (FTAs / ROO)", "Tính hàm lượng giá trị khu vực (RVC Build-down / Build-up)"),
        ("audit-check", "Phase 167 (Điều 77 LHQ)", "Kiểm tra thời hiệu kiểm tra sau thông quan 05 năm"),
        ("sbv-loan", "Phase 168 (TT 12/2022)", "Đánh giá nghĩa vụ đăng ký khoản vay nước ngoài với NHNN"),
        ("profit-remit", "Phase 168 (TT 186/2010)", "Kiểm tra điều kiện chuyển lợi nhuận FDI ra nước ngoài"),
        ("tech-registration", "Phase 169 (Luật CGCN 2017)", "Đánh giá nghĩa vụ đăng ký hợp đồng CGCN tại BKHCN"),
        ("royalty", "Phase 169 (NĐ 76/2018)", "Tính tiền bản quyền theo Doanh thu thuần & 25% Profit Split"),
        ("storage-check", "Phase 170 (Điều 61 LHQ)", "Kiểm tra thời hạn lưu kho ngoại quan (12-24T) & CFS (90N)"),
    ]:
        table.add_row(cmd, phase, desc)
    console.print(table)
    console.print("[dim]Gõ 'mekong customs <command> --help' để xem chi tiết từng lệnh.[/dim]\n")


def _emit_customs_result(result: dict[str, object], json_mode: bool, title: str) -> None:
    """Render a CustomsEngine result as JSON or a readable panel."""
    if json_mode:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return
    console.print(Panel.fit(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        title=title,
        border_style="cyan" if result.get("ok") else "red",
    ))


@customs_app.command("hs-lookup")
def lookup_hs_code(
    hs_code: str = typer.Argument(..., help="Mã HS/AHTN cần tra cứu"),
    fta: str = typer.Option("MFN", "--fta", help="Biểu thuế MFN hoặc mã FTA"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu mô tả hàng hóa, thuế suất MFN và ưu đãi theo FTA."""
    _emit_customs_result(CustomsEngine().lookup_hs_code(hs_code=hs_code, fta=fta), json_mode, "Tra cứu mã HS")


@customs_app.command("duty-calc")
def calculate_customs_duties(
    invoice_value_usd: float = typer.Argument(..., help="Trị giá hóa đơn (USD)"),
    hs_code: str = typer.Option("8471.30.20", "--hs", help="Mã HS/AHTN"),
    freight_usd: float = typer.Option(0.0, "--freight", help="Cước vận chuyển quốc tế (USD)"),
    insurance_usd: float = typer.Option(0.0, "--insurance", help="Phí bảo hiểm quốc tế (USD)"),
    exchange_rate: float = typer.Option(25_450.0, "--exchange-rate", help="Tỷ giá USD/VND"),
    fta: str = typer.Option("MFN", "--fta", help="Biểu thuế MFN hoặc mã FTA"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính thuế nhập khẩu và VAT trên trị giá CIF quy đổi."""
    engine = CustomsEngine()
    result = engine.calculate_customs_duties(
        invoice_value_usd=invoice_value_usd,
        hs_code=hs_code,
        freight_usd=freight_usd,
        insurance_usd=insurance_usd,
        exchange_rate=exchange_rate,
        fta=fta,
    )
    _emit_customs_result(result, json_mode, "Tính thuế nhập khẩu")


@customs_app.command("channel")
def evaluate_customs_channel(
    enterprise_tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    hs_code: str = typer.Argument(..., help="Mã HS/AHTN"),
    invoice_value_usd: float = typer.Argument(..., help="Trị giá hóa đơn (USD)"),
    origin_country: str = typer.Option("US", "--origin", help="Mã quốc gia xuất xứ"),
    compliance_tier: str = typer.Option("TIER_2_NORMAL", "--tier", help="Hạng tuân thủ doanh nghiệp"),
    has_valid_co: bool = typer.Option(True, "--valid-co/--no-valid-co", help="Có chứng nhận xuất xứ hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá rủi ro và phân luồng Xanh, Vàng hoặc Đỏ theo VNACCS."""
    result = CustomsEngine().evaluate_customs_channel(
        enterprise_tax_id=enterprise_tax_id,
        hs_code=hs_code,
        invoice_value_usd=invoice_value_usd,
        origin_country=origin_country,
        compliance_tier=compliance_tier,
        has_valid_co=has_valid_co,
    )
    _emit_customs_result(result, json_mode, "Phân luồng VNACCS")


@customs_app.command("declare")
def create_customs_declaration(
    enterprise_tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    hs_code: str = typer.Argument(..., help="Mã HS/AHTN"),
    commodity_name: str = typer.Argument(..., help="Tên hàng hóa"),
    invoice_value_usd: float = typer.Argument(..., help="Trị giá hóa đơn (USD)"),
    origin_country: str = typer.Option("US", "--origin", help="Mã quốc gia xuất xứ"),
    declaration_type: str = typer.Option("IMPORT_BUSINESS", "--type", help="Loại hình tờ khai"),
    compliance_tier: str = typer.Option("TIER_2_NORMAL", "--tier", help="Hạng tuân thủ doanh nghiệp"),
    has_valid_co: bool = typer.Option(True, "--valid-co/--no-valid-co", help="Có chứng nhận xuất xứ hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tạo và lưu tờ khai hải quan điện tử cùng kết quả phân luồng."""
    result = CustomsEngine().create_declaration(
        enterprise_tax_id=enterprise_tax_id,
        hs_code=hs_code,
        commodity_name=commodity_name,
        invoice_value_usd=invoice_value_usd,
        origin_country=origin_country,
        declaration_type=declaration_type,
        compliance_tier=compliance_tier,
        has_valid_co=has_valid_co,
    )
    _emit_customs_result(result, json_mode, "Tờ khai hải quan")


@customs_app.command("origin")
def verify_customs_origin(
    form_type: str = typer.Argument(..., help="Mẫu C/O, ví dụ EUR.1 hoặc CPTPP"),
    hs_code: str = typer.Argument(..., help="Mã HS/AHTN"),
    fob_value_usd: float = typer.Argument(..., help="Trị giá FOB (USD)"),
    non_originating_value_usd: float = typer.Argument(..., help="Trị giá nguyên liệu không có xuất xứ (USD)"),
    exporter_name: str = typer.Option("Doanh Nghiệp Xuất Khẩu Việt Nam", "--exporter"),
    importer_country: str = typer.Option("DE", "--importer"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá hàm lượng giá trị khu vực và điều kiện xuất xứ C/O."""
    result = CustomsEngine().verify_rules_of_origin(
        form_type=form_type,
        hs_code=hs_code,
        fob_value_usd=fob_value_usd,
        non_originating_value_usd=non_originating_value_usd,
        exporter_name=exporter_name,
        importer_country=importer_country,
    )
    _emit_customs_result(result, json_mode, "Xác minh xuất xứ hàng hóa")


@customs_app.command("list")
def list_customs_declarations(
    limit: int = typer.Option(50, min=1, max=500, help="Số tờ khai tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Liệt kê các tờ khai đã đăng ký trong cơ sở dữ liệu cục bộ."""
    result = {"declarations": CustomsEngine().list_declarations(limit=limit)}
    _emit_customs_result(result, json_mode, "Danh sách tờ khai")


@customs_app.command("status")
def customs_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hiển thị tình trạng xử lý và chỉ số VNACCS cục bộ."""
    _emit_customs_result(CustomsEngine().get_status(), json_mode, "Trạng thái VNACCS")


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
        invoice_price_vnd=invoice, freight_international_vnd=freight, insurance_international_vnd=insurance,
        royalties_license_fees_vnd=royalties, assists_value_vnd=assists, post_import_inland_freight_vnd=post_import_freight,
        post_import_construction_install_vnd=post_import_install, duties_taxes_in_vietnam_vnd=vn_taxes,
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
    console.print(f"[bold cyan]Tư vấn:[/] {result.advice_vn}\n[dim]Căn cứ pháp lý: {result.legal_basis}[/dim]\n")


@customs_app.command("rvc")
def calc_rvc(
    fob: float = typer.Argument(..., help="Giá FOB của sản phẩm xuất khẩu (VNĐ)"),
    non_originating: float = typer.Option(0.0, "--vnm", help="Giá trị nguyên liệu không có xuất xứ (VNM) (VNĐ)"),
    originating: float = typer.Option(0.0, "--vom", help="Giá trị nguyên liệu có xuất xứ nội khối (VOM) (VNĐ)"),
    formula: str = typer.Option("build_down", "--formula", help="Công thức tính: 'build_down' hoặc 'build_up'"),
    threshold: float = typer.Option(40.0, "--threshold", "-t", help="Ngưỡng RVC tối thiểu (%)"),
    agreement: str = typer.Option("ATIGA", "--agreement", "-a", help="Mã hiệp định (ATIGA, ACFTA, CPTPP, EVFTA)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính Hàm lượng giá trị khu vực (RVC) theo Quy tắc xuất xứ hàng hóa (Rules of Origin)."""
    result = CustomsValuationOriginEngine.calculate_regional_value_content(
        fob_price_vnd=fob, non_originating_value_vnd=non_originating, originating_value_vnd=originating,
        formula=formula, threshold_percentage=threshold, agreement_code=agreement,
    )
    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    badge = "[bold green]ĐẠT TIÊU CHÍ XUẤT XỨ (ORIGINATING)[/bold green]" if result.is_originating else "[bold red]KHÔNG ĐẠT TIÊU CHÍ (NON-ORIGINATING)[/bold red]"
    console.print(Panel.fit(
        f"[bold]Kết quả đánh giá:[/] {badge}\n[bold]Hiệp định thương mại:[/] {result.agreement_code}\n"
        f"[bold]Công thức áp dụng:[/] {result.calculation_formula}\n"
        f"[bold]Hàm lượng RVC đạt được:[/] [bold cyan]{result.rvc_percentage:.2f}%[/bold cyan] (Ngưỡng yêu cầu: {result.threshold_percentage:.1f}%)\n"
        f"[bold]Giá FOB thành phẩm:[/] {result.fob_price_vnd:,.0f} VNĐ\n\n[bold]Kết luận & Hướng dẫn:[/] {result.advice_vn}",
        title="[bold green]Quy Tắc Xuất Xứ: Hàm Lượng Giá Trị Khu Vực (RVC)[/bold green]",
        border_style="green" if result.is_originating else "red",
    ))


register_customs_fx_tech(customs_app)
register_customs_royalty_storage(customs_app)

__all__ = [
    "customs_app", "customs_default", "calc_customs_valuation", "calc_rvc",
    "check_customs_audit", "evaluate_sbv_loan", "check_profit_remittance",
    "check_tech_registration", "calc_royalty", "check_storage_period",
    "CustomsValuationOriginEngine", "ForeignExchangeControlEngine", "TechnologyTransferEngine", "BondedLogisticsEngine",
]
