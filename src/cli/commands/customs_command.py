# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Customs Clearance, VNACCS Channeling & Cross-Border Logistics Engine (Phase 50)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
customs_app = typer.Typer(
    name="customs",
    help="Customs Clearance, VNACCS Channeling, HS Code Tariffs & Rules of Origin (C/O)",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


@customs_app.callback(invoke_without_command=True)
def customs_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Hải quan Điện tử (VNACCS), Phân luồng, Biểu thuế HS và Xuất xứ hàng hóa (C/O)."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG THÔNG QUAN HẢI QUAN ĐIỆN TỬ & PHÂN LUỒNG TỜ KHAI (VNACCS/VCIS)[/]\n\n"
            f"  Khung quy chuẩn:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Hệ thống xử lý:        [bold cyan]{status_data['vnaccs_version']}[/]\n"
            f"  Tỷ giá hải quan:       1 USD = {_format_vnd(status_data['reference_exchange_rate'])}\n"
            f"  Tổng số tờ khai:       [bold]{metrics['total_declarations']} tờ khai[/] (Tổng thuế: [bold green]{_format_vnd(metrics['total_tax_collected_vnd'])}[/])\n"
            f"  Phân luồng thông quan: [bold green]{metrics['green_channel_count']} Luồng Xanh[/] | [bold yellow]{metrics['yellow_channel_count']} Luồng Vàng[/] | [bold red]{metrics['red_channel_count']} Luồng Đỏ[/]\n"
            f"  Chứng nhận C/O đã cấp: [bold magenta]{metrics['co_certificates_issued']} chứng thư[/]\n"
            f"  Danh mục mã HS hỗ trợ: [bold]{metrics['supported_hs_codes']} mã chuẩn AHTN 8 chữ số[/]",
            title="[bold blue]VNACCS Customs Operations & Channeling Dashboard[/]",
            border_style="green",
        )
    )


@customs_app.command("hs-lookup")
def hs_lookup_cmd(
    hs_code: str = typer.Argument(..., help="Mã số HS 8 chữ số (ví dụ: 8471.30.20, 8542.31.00)"),
    fta: str = typer.Option("MFN", "--fta", "-f", help="Biểu thuế áp dụng (MFN, EVFTA, CPTPP, RCEP, ATIGA)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu mã số HS, mô tả hàng hóa, thuế suất MFN và ưu đãi FTA theo Thông tư 31/2022/TT-BTC."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    result = engine.lookup_hs_code(hs_code=hs_code, fta=fta)

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not result.get("ok"):
        console.print(f"[bold red]Lỗi:[/] {result.get('error')}")
        return

    console.print(
        Panel(
            f"[bold cyan]TRA CỨU BIỂU THUẾ HẢI QUAN AHTN: {result['hs_code']}[/]\n\n"
            f"  Mô tả hàng hóa:      [bold]{result['description']}[/]\n"
            f"  Đơn vị tính:         {result['unit']}\n"
            f"  Biểu thuế lựa chọn:  [bold yellow]{result['tariff_scheme']}[/]\n"
            f"  Thuế suất áp dụng:   [bold green]{result['applicable_duty_rate_pct']}%[/] (MFN gốc: {result['mfn_rate_pct']}%)\n"
            f"  Thuế suất GTGT NK:   [bold]{result['vat_rate_pct']}%[/]\n"
            f"  Chính sách quản lý:  {result['regulatory_notes']}\n"
            f"  Căn cứ pháp lý:      {result['statutory_reference']}",
            title="[bold blue]HS Code & Tariff Details[/]",
            border_style="cyan",
        )
    )


@customs_app.command("duty-calc")
def duty_calc_cmd(
    value_usd: float = typer.Argument(..., help="Trị giá hóa đơn thương mại (USD)"),
    hs_code: str = typer.Option("8471.30.20", "--hs", help="Mã số HS 8 chữ số"),
    freight_usd: float = typer.Option(0.0, "--freight", help="Cước vận chuyển quốc tế (F)"),
    insurance_usd: float = typer.Option(0.0, "--insurance", help="Phí bảo hiểm quốc tế (I)"),
    fta: str = typer.Option("MFN", "--fta", "-f", help="Biểu thuế (MFN, EVFTA, CPTPP)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi tiết trị giá tính thuế CIF, thuế nhập khẩu và thuế GTGT hàng nhập khẩu."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    result = engine.calculate_customs_duties(
        invoice_value_usd=value_usd,
        hs_code=hs_code,
        freight_usd=freight_usd,
        insurance_usd=insurance_usd,
        fta=fta,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]BẢNG TÍNH THUẾ NHẬP KHẨU VÀ NGHĨA VỤ NGÂN SÁCH (HS: {result['hs_code']})[/]\n\n"
            f"  Trị giá hóa đơn:     {_format_usd(result['invoice_value_usd'])}\n"
            f"  Trị giá tính thuế CIF: [bold]{_format_usd(result['cif_value_usd'])}[/] (~ [bold green]{_format_vnd(result['dutiable_value_vnd'])}[/])\n"
            f"  Thuế nhập khẩu:      [bold yellow]{result['import_duty_rate_pct']}%[/] -> [bold yellow]{_format_vnd(result['import_duty_vnd'])}[/]\n"
            f"  Thuế GTGT hàng NK:   [bold magenta]{result['vat_rate_pct']}%[/] -> [bold magenta]{_format_vnd(result['vat_vnd'])}[/]\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG THUẾ PHẢI NỘP:[/] [bold green]{_format_vnd(result['total_tax_vnd'])}[/]",
            title="[bold blue]Customs Duties & Import Tax Valuation[/]",
            border_style="cyan",
        )
    )


@customs_app.command("channel")
def evaluate_channel_cmd(
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp (MST)"),
    hs_code: str = typer.Argument(..., help="Mã HS hàng hóa"),
    value_usd: float = typer.Argument(..., help="Trị giá lô hàng (USD)"),
    origin: str = typer.Option("US", "--origin", help="Quốc gia xuất xứ"),
    tier: str = typer.Option("TIER_2_NORMAL", "--tier", help="Hạng tuân thủ doanh nghiệp (TIER_1_AEO, TIER_2_NORMAL, TIER_4_LOW)"),
    has_co: bool = typer.Option(True, "--co/--no-co", help="Có chứng nhận xuất xứ C/O hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá tiêu chí quản lý rủi ro và xác định phân luồng hải quan VNACCS (Xanh / Vàng / Đỏ)."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    result = engine.evaluate_customs_channel(
        enterprise_tax_id=tax_id,
        hs_code=hs_code,
        invoice_value_usd=value_usd,
        origin_country=origin,
        compliance_tier=tier,
        has_valid_co=has_co,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    color_map = {"GREEN": "green", "YELLOW": "yellow", "RED": "red"}
    ch_color = color_map.get(result["channel"], "white")

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ PHÂN LUỒNG TỰ ĐỘNG VNACCS/VCIS[/]\n\n"
            f"  Doanh nghiệp (MST):   [bold]{result['enterprise_tax_id']}[/] (Hạng: {result['compliance_tier']})\n"
            f"  Hàng hóa / Xuất xứ:   HS {result['hs_code']} | Xuất xứ: {result['origin_country']}\n"
            f"  Kết quả phân luồng:   [bold {ch_color}]{result['channel_name']}[/bold {ch_color}]\n"
            f"  Thời gian thông quan: {result['clearance_time']}\n"
            f"  Thao tác yêu cầu:     {result['action_required']}",
            title="[bold blue]VNACCS Automated Risk Assessment[/]",
            border_style=ch_color,
        )
    )


@customs_app.command("declare")
def declare_customs_cmd(
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    hs_code: str = typer.Argument(..., help="Mã HS hàng hóa"),
    name: str = typer.Argument(..., help="Tên hàng hóa thương mại"),
    value_usd: float = typer.Argument(..., help="Trị giá lô hàng (USD)"),
    origin: str = typer.Option("US", "--origin", help="Quốc gia xuất xứ"),
    decl_type: str = typer.Option("IMPORT_BUSINESS", "--type", help="Loại hình tờ khai"),
    tier: str = typer.Option("TIER_2_NORMAL", "--tier", help="Hạng tuân thủ"),
    has_co: bool = typer.Option(True, "--co/--no-co", help="Có C/O hợp lệ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thiết lập và đăng ký tờ khai hải quan điện tử chính thức trên hệ thống VNACCS/VCIS."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    result = engine.create_declaration(
        enterprise_tax_id=tax_id,
        hs_code=hs_code,
        commodity_name=name,
        invoice_value_usd=value_usd,
        origin_country=origin,
        declaration_type=decl_type,
        compliance_tier=tier,
        has_valid_co=has_co,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    color_map = {"GREEN": "green", "YELLOW": "yellow", "RED": "red"}
    ch_color = color_map.get(result["channel"], "white")

    console.print(
        Panel(
            f"[bold green]ĐÃ TIẾP NHẬN TỜ KHAI HẢI QUAN ĐIỆN TỬ: {result['declaration_id']}[/]\n\n"
            f"  Loại hình / Tên hàng: {result['declaration_type']} | [bold cyan]{result['commodity_name']}[/] (HS: {result['hs_code']})\n"
            f"  Doanh nghiệp (MST):   {result['enterprise_tax_id']} | Xuất xứ: {result['origin_country']}\n"
            f"  Trị giá tính thuế:    {_format_usd(result['invoice_value_usd'])} (~ {_format_vnd(result['dutiable_value_vnd'])})\n"
            f"  Phân luồng thông quan: [bold {ch_color}]{result['channel_name']}[/bold {ch_color}]\n"
            f"  Nghĩa vụ thuế:        Thuế NK: {_format_vnd(result['import_duty_vnd'])} | VAT: {_format_vnd(result['vat_vnd'])}\n"
            f"  Tổng thuế nộp NSNN:   [bold green]{_format_vnd(result['total_tax_vnd'])}[/]\n"
            f"  Trạng thái xử lý:     [bold]{result['status']}[/] ({result['statutory_timeline']})",
            title="[bold green]VNACCS Customs Declaration Processed[/]",
            border_style="green",
        )
    )


@customs_app.command("origin")
def verify_origin_cmd(
    form_type: str = typer.Argument(..., help="Mẫu C/O (EUR.1, CPTPP, D, E)"),
    hs_code: str = typer.Argument(..., help="Mã HS hàng hóa"),
    fob_usd: float = typer.Argument(..., help="Trị giá FOB xuất xưởng (USD)"),
    non_orig_usd: float = typer.Argument(..., help="Trị giá nguyên liệu không có xuất xứ (VNM USD)"),
    exporter: str = typer.Option("Doanh Nghiệp Xuất Khẩu Việt Nam", "--exporter", help="Tên doanh nghiệp xuất khẩu"),
    importer: str = typer.Option("DE", "--importer", help="Quốc gia nhập khẩu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định tiêu chí xuất xứ hàng hóa (RVC >= 40%) và cấp giấy chứng nhận C/O ưu đãi."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    result = engine.verify_rules_of_origin(
        form_type=form_type,
        hs_code=hs_code,
        fob_value_usd=fob_usd,
        non_originating_value_usd=non_orig_usd,
        exporter_name=exporter,
        importer_country=importer,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_eligible"] else "red"

    console.print(
        Panel(
            f"[bold cyan]THẨM ĐỊNH XUẤT XỨ HÀNG HÓA VÀ CẤP C/O: {result['co_id']}[/]\n\n"
            f"  Hiệp định / Mẫu C/O:  [bold]{result['form_name']}[/]\n"
            f"  Mã HS hàng hóa:       {result['hs_code']}\n"
            f"  Trị giá FOB / VNM:    FOB: {_format_usd(result['fob_value_usd'])} | Nguyên liệu ngoại: {_format_usd(result['non_originating_value_usd'])}\n"
            f"  Hàm lượng RVC:        [bold {status_color}]{result['rvc_pct']}%[/bold {status_color}] (Tiêu chuẩn: >= 40.0%)\n"
            f"  Kết quả thẩm định:    [bold {status_color}]{result['status']}[/bold {status_color}] (Mã tiêu chí: {result['criteria_code']})\n"
            f"  Thị trường đích:      {result['importer_country']}",
            title="[bold blue]Rules of Origin & C/O Eligibility Verification[/]",
            border_style=status_color,
        )
    )


@customs_app.command("list")
def list_declarations_cmd(
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng tờ khai tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục tờ khai hải quan đã đăng ký trên hệ thống."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    declarations = engine.list_declarations(limit=limit)

    if json_mode:
        typer.echo(json.dumps({"declarations": declarations, "total": len(declarations)}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Danh Sách Tờ Khai Hải Quan Điện Tử", border_style="cyan")
    table.add_column("Mã tờ khai", style="cyan")
    table.add_column("Mã HS", style="green")
    table.add_column("Tên hàng")
    table.add_column("Luồng", style="bold")
    table.add_column("Thuế nộp (VND)", style="yellow")
    table.add_column("Trạng thái")

    for d in declarations:
        table.add_row(
            d["declaration_id"],
            d["hs_code"],
            d["commodity_name"],
            d["channel"],
            _format_vnd(d["total_tax_vnd"]),
            d["status"],
        )

    console.print(table)


@customs_app.command("status")
def customs_status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON"),
) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu hải quan và phân bổ luồng VNACCS."""
    from src.core.customs_engine import CustomsEngine

    engine = CustomsEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]THÔNG SỐ QUẢN TRỊ HẢI QUAN ĐIỆN TỬ (VNACCS/VCIS)[/]\n\n"
            f"  Trạng thái:            {status_data['status'].upper()}\n"
            f"  Khung pháp lý:         {status_data['regulatory_framework']}\n"
            f"  Tỷ giá hạch toán:      1 USD = {_format_vnd(status_data['reference_exchange_rate'])}\n"
            f"  Tổng tờ khai tiếp nhận: {metrics['total_declarations']} bộ\n"
            f"  Số thuế đã thu:        {_format_vnd(metrics['total_tax_collected_vnd'])}\n"
            f"  Tỷ lệ luồng:           Xanh: {metrics['green_channel_count']} | Vàng: {metrics['yellow_channel_count']} | Đỏ: {metrics['red_channel_count']}\n"
            f"  Chứng thư C/O:         {metrics['co_certificates_issued']} chứng nhận\n"
            f"  Cơ sở dữ liệu:         {status_data['database']}",
            title="[bold blue]Customs Engine Telemetry[/]",
            border_style="green",
        )
    )
