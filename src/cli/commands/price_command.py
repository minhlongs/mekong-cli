# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Price Management, Anti-Price Gouging & Valuation Suite (Phase 90)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

price_app = typer.Typer(
    name="price",
    help="Vietnamese Price Management, Anti-Price Gouging & Valuation Compliance Suite.",
)
console = Console()


@price_app.callback(invoke_without_command=True)
def price_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động quản lý giá, bình ổn giá, chống tăng giá bất hợp lý và thẩm định giá."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ GIÁ, BÌNH ỔN GIÁ & THẨM ĐỊNH GIÁ VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['statutory_law']}[/]\n"
            f"  Hồ sơ kê khai giá:         [bold cyan]{status_data['total_price_declarations']}[/] hồ sơ ([bold yellow]{status_data['stabilized_commodities_declarations']}[/] thuộc danh mục bình ổn giá)\n"
            f"  Hậu kiểm niêm yết giá:     [bold]{status_data['total_price_posting_inspections']}[/] điểm bán ([bold red]{status_data['posting_violations_detected']}[/] vi phạm bán sai giá niêm yết)\n"
            f"  Chứng thư thẩm định giá:   [bold green]{status_data['total_valuation_certificates_issued']}[/] chứng thư đạt chuẩn TĐGVN\n"
            f"  Tổng giá trị thẩm định:    [bold green]{status_data['total_appraised_asset_value_vnd']:,.0f} VND[/]\n"
            f"  Chống tăng giá bất hợp lý: [bold red]{status_data['price_gouging_cases_penalized']}[/] vụ đầu cơ/tăng giá xử phạt ([bold yellow]{status_data['total_illicit_recovery_and_fines_vnd']:,.0f} VND[/] thu hồi & phạt)",
            title="[bold green]Vietnam Price Surveillance, Anti-Gouging & Valuation Telemetry[/]",
            border_style="green",
        )
    )


@price_app.command("declare")
def declare_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp kê khai giá"),
    product: str = typer.Option("Sữa bột dinh dưỡng trẻ em Mekong Smart 900g", "--product", "-p", help="Tên hàng hóa, dịch vụ kê khai"),
    unit: str = typer.Option("Hộp", "--unit", "-u", help="Đơn vị tính"),
    old_price: float = typer.Option(450_000.0, "--old", help="Mức giá hiện hành (VND)"),
    new_price: float = typer.Option(480_000.0, "--new", help="Mức giá kê khai mới (VND)"),
    effective_date: str = typer.Option("2026-10-01", "--date", "-d", help="Ngày bắt đầu áp dụng mức giá mới"),
    stabilized: bool = typer.Option(True, "--stabilized/--non-stabilized", help="Hàng hóa thuộc danh mục bình ổn giá"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kê khai giá hàng hóa, dịch vụ theo Điều 28 Luật Giá 2023 và kiểm tra biên độ tăng giá."""
    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    res = engine.declare_price(
        enterprise_name=enterprise,
        product_name=product,
        unit=unit,
        old_price_vnd=old_price,
        declared_price_vnd=new_price,
        effective_date=effective_date,
        is_stabilized_commodity=stabilized,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_approved"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ TIẾP NHẬN KÊ KHAI GIÁ (ĐIỀU 28 LUẬT GIÁ 2023)[/]\n\n"
            f"  Mã hồ sơ kê khai:    [bold cyan]{res['declaration_code']}[/]\n"
            f"  Doanh nghiệp kê khai:[bold]{res['enterprise_name']}[/]\n"
            f"  Hàng hóa / Dịch vụ:  [white]{res['product_name']}[/] (ĐVT: {res['unit']})\n"
            f"  Giá cũ  -->  Giá mới:[white]{res['old_price_vnd']:,.0f} VND[/] --> [bold yellow]{res['declared_price_vnd']:,.0f} VND[/]\n"
            f"  Tỷ lệ điều chỉnh:    [bold]{res['change_pct']}%[/]\n"
            f"  Thuộc diện bình ổn:  [bold]{'CÓ (Thuộc danh mục quản lý đặc biệt)' if res['is_stabilized_good'] else 'KHÔNG'}[/]\n"
            f"  Ngày hiệu lực:       [cyan]{res['effective_date']}[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            + (f"  Cảnh báo/Vi phạm:    [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:            [bold green]Mức điều chỉnh giá hợp lý, đáp ứng điều kiện lưu thông trên thị trường[/]"),
            title=f"[bold {color}]Price Declaration Assessment[/]",
            border_style=color,
        )
    )


@price_app.command("posting")
def posting_cmd(
    store: str = typer.Argument(..., help="Tên cửa hàng, siêu thị, điểm kinh doanh"),
    product: str = typer.Option("Thịt lợn nạc thăn sạch 1kg", "--product", "-p", help="Tên hàng hóa niêm yết"),
    listed: float = typer.Option(135_000.0, "--listed", "-l", help="Mức giá niêm yết công khai (VND)"),
    actual: float = typer.Option(150_000.0, "--actual", "-a", help="Mức giá bán thực tế thu của khách (VND)"),
    clearly_posted: bool = typer.Option(True, "--posted/--unposted", help="Có niêm yết giá công khai rõ ràng"),
    currency: str = typer.Option("VND", "--curr", "-c", help="Đơn vị tiền tệ niêm yết (bắt buộc VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hậu kiểm tuân thủ quy định niêm yết giá theo Điều 29 Luật Giá 2023 và xử phạt bán sai giá niêm yết."""
    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    res = engine.audit_price_posting(
        store_name=store,
        product_name=product,
        listed_price_vnd=listed,
        actual_selling_price_vnd=actual,
        is_posted_clearly=clearly_posted,
        currency=currency,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_comp = res["is_compliant"]
    color = "green" if is_comp else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ KIỂM TRA NIÊM YẾT GIÁ (ĐIỀU 29 LUẬT GIÁ 2023)[/]\n\n"
            f"  Mã kiểm tra:         [bold cyan]{res['audit_code']}[/]\n"
            f"  Điểm kinh doanh:     [bold]{res['store_name']}[/]\n"
            f"  Hàng hóa kiểm tra:   [white]{res['product_name']}[/]\n"
            f"  Giá niêm yết:        [bold green]{res['listed_price_vnd']:,.0f} {res['currency']}[/]\n"
            f"  Giá bán thực tế:     [bold yellow]{res['actual_selling_price_vnd']:,.0f} {res['currency']}[/]\n"
            f"  Niêm yết rõ ràng:    [white]{'ĐẠT CHUẨN' if res['is_posted_clearly'] else 'KHÔNG NIÊM YẾT'}[/]\n"
            f"  Kết luận:            [bold {color}]{res['status']}[/]"
            + (f"\n  Mức phạt ước tính:   [bold red]{res['estimated_fine_vnd']:,.0f} VND (Nghị định 109/2013/NĐ-CP)[/]" if res["estimated_fine_vnd"] > 0 else "\n  Đánh giá:            [bold green]Chấp hành đầy đủ quy định niêm yết giá, bán đúng giá niêm yết[/]"),
            title=f"[bold {color}]Price Posting Compliance Audit[/]",
            border_style=color,
        )
    )


@price_app.command("valuation")
def valuation_cmd(
    firm: str = typer.Argument(..., help="Tên doanh nghiệp thẩm định giá"),
    client: str = typer.Option("Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)", "--client", help="Khách hàng yêu cầu thẩm định"),
    asset: str = typer.Option("Khu đất thương mại dịch vụ 5,000m2 tại Quận Cầu Giấy, Hà Nội", "--asset", help="Mô tả tài sản thẩm định"),
    value: float = typer.Option(250_000_000_000.0, "--value", "-v", help="Giá trị tài sản thẩm định (VND)"),
    method: str = typer.Option("MARKET_COMPARISON", "--method", "-m", help="Phương pháp: MARKET_COMPARISON, COST_APPROACH, INCOME_APPROACH"),
    appraiser: str = typer.Option("Thẩm định viên Lê Quốc Doanh (Thẻ TĐV 8899/TĐG)", "--appraiser", help="Tên thẩm định viên chủ trì"),
    appraisers_count: int = typer.Option(4, "--appraisers", help="Số lượng thẩm định viên về giá của công ty (tối thiểu 3)"),
    insurance: bool = typer.Option(True, "--insurance/--no-insurance", help="Có bảo hiểm trách nhiệm nghề nghiệp"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ban hành và thẩm tra Chứng thư Thẩm định giá theo Chuẩn mực Thẩm định giá Việt Nam (TĐGVN)."""
    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    res = engine.issue_valuation_certificate(
        appraisal_firm=firm,
        client_name=client,
        asset_description=asset,
        appraised_value_vnd=value,
        valuation_method=method,
        lead_appraiser=appraiser,
        licensed_appraisers_count=appraisers_count,
        has_firm_insurance=insurance,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_valid = res["is_valid"]
    color = "green" if is_valid else "red"

    console.print(
        Panel(
            f"[bold {color}]CHỨNG THƯ THẨM ĐỊNH GIÁ TÀI SẢN (CHUẨN MỰC TĐGVN & LUẬT GIÁ 2023)[/]\n\n"
            f"  Số chứng thư:        [bold cyan]{res['certificate_code']}[/]\n"
            f"  Tổ chức thẩm định:   [bold]{res['appraisal_firm']}[/]\n"
            f"  Khách hàng/Đối tác:  [white]{res['client_name']}[/]\n"
            f"  Tài sản thẩm định:   [white]{res['asset_description']}[/]\n"
            f"  Giá trị thẩm định:   [bold green]{res['appraised_value_vnd']:,.0f} VND[/]\n"
            f"  Phương pháp áp dụng: [bold cyan]{res['valuation_method']}[/]\n"
            f"  TĐV chịu trách nhiệm:[yellow]{res['lead_appraiser']}[/]\n"
            f"  Số lượng TĐV hợp lệ: [white]{res['licensed_appraisers_count']} TĐV (Yêu cầu >= 3 TĐV)[/]\n"
            f"  Bảo hiểm nghề nghiệp:[white]{'ĐÃ THAM GIA' if res['has_firm_insurance'] else 'CHƯA MUA'}[/]\n"
            f"  Thời hạn hiệu lực:   [bold]{res['validity_period_months']} tháng kể từ ngày ban hành[/]\n"
            f"  Kết luận pháp lý:    [bold {color}]{res['status']}[/]\n"
            + (f"  Thiếu sót:           [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Hiệu lực:            [bold green]Chứng thư hợp lệ, có giá trị pháp lý làm căn cứ thế chấp / giao dịch[/]"),
            title=f"[bold {color}]Valuation Certificate Issuance[/]",
            border_style=color,
        )
    )


@price_app.command("gouge")
def gouge_cmd(
    business: str = typer.Argument(..., help="Tên cơ sở kinh doanh kiểm tra"),
    product: str = typer.Option("Bao gạo ST25 5kg", "--product", "-p", help="Tên hàng hóa thiết yếu"),
    base: float = typer.Option(180_000.0, "--base", "-b", help="Mức giá cơ sở bình thường (VND)"),
    gouged: float = typer.Option(270_000.0, "--gouged", "-g", help="Mức giá bán tăng vọt bị tố cáo (VND)"),
    units: int = typer.Option(500, "--units", "-u", help="Số lượng đơn vị đã bán ra"),
    crisis: bool = typer.Option(True, "--crisis/--normal", help="Trong thời kỳ bão lũ, thiên tai, dịch bệnh hoặc bình ổn giá"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra và xử lý hành vi đầu cơ găm hàng, tăng giá bất hợp lý trong thiên tai dịch bệnh."""
    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    res = engine.check_price_gouging(
        business_name=business,
        product_name=product,
        base_price_vnd=base,
        gouged_price_vnd=gouged,
        units_sold=units,
        is_crisis_period=crisis,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_gouge = res["status"] == "PRICE_GOUGING_CONFIRMED"
    color = "red" if is_gouge else "green"

    console.print(
        Panel(
            f"[bold {color}]THANH TRA HÀNH VI TĂNG GIÁ BẤT HỢP LÝ & GĂM HÀNG (ANTI-GOUGING)[/]\n\n"
            f"  Mã thanh tra:        [bold cyan]{res['audit_code']}[/]\n"
            f"  Cơ sở kinh doanh:    [bold]{res['business_name']}[/]\n"
            f"  Mặt hàng kiểm tra:   [white]{res['product_name']}[/]\n"
            f"  Giá gốc  -->  Giá bán:[white]{res['base_price_vnd']:,.0f} VND[/] --> [bold red]{res['gouged_price_vnd']:,.0f} VND[/] (+{res['increase_pct']}%)\n"
            f"  Số lượng đã tiêu thụ:[yellow]{res['units_sold']:,}[/] đơn vị sản phẩm\n"
            f"  Thu lợi bất chính:   [bold red]{res['illicit_profit_vnd']:,.0f} VND (Buộc nộp lại ngân sách)[/]\n"
            f"  Mức phạt hành chính: [bold red]{res['penalty_fine_vnd']:,.0f} VND (Nghị định 109/2013/NĐ-CP)[/]\n"
            f"  Thời kỳ áp dụng:     [bold]{'Thời kỳ thiên tai / dịch bệnh / bình ổn giá' if res['is_crisis_period'] else 'Thời kỳ bình thường'}[/]\n"
            f"  Kết luận thanh tra:  [bold {color}]{res['legal_conclusion']}[/]",
            title=f"[bold {color}]Anti-Price Gouging Investigation[/]",
            border_style=color,
        )
    )


@price_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("declarations", help="Danh mục: declarations, postings, valuations, gouging"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ kê khai giá, niêm yết giá, chứng thư thẩm định hoặc xử lý tăng giá."""
    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục quản lý giá & thẩm định giá [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["postings", "listing", "niem_yet"]:
        table.add_column("Mã KT", style="bold cyan")
        table.add_column("Cửa hàng", style="white")
        table.add_column("Sản phẩm", style="white")
        table.add_column("Giá niêm yết", style="green")
        table.add_column("Giá bán TT", style="yellow")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "COMPLIANT_POSTING" else "red"
            table.add_row(r.get("audit_code", ""), r.get("store_name", ""), r.get("product_name", ""), f"{r.get('listed_price_vnd', 0):,.0f} VND", f"{r.get('actual_selling_price_vnd', 0):,.0f} VND", f"[{color}]{r.get('status', '')}[/]")
    elif category in ["valuations", "appraisals", "tham_dinh"]:
        table.add_column("Số chứng thư", style="bold cyan")
        table.add_column("Doanh nghiệp TĐG", style="white")
        table.add_column("Khách hàng", style="yellow")
        table.add_column("Phương pháp", style="cyan")
        table.add_column("Giá trị thẩm định", style="bold green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_valid") else "red"
            table.add_row(r.get("certificate_code", ""), r.get("appraisal_firm", ""), r.get("client_name", ""), r.get("valuation_method", ""), f"{r.get('appraised_value_vnd', 0):,.0f} VND", f"[{color}]{r.get('status', '')}[/]")
    elif category in ["gouging", "violations", "tang_gia"]:
        table.add_column("Mã TT", style="bold cyan")
        table.add_column("Cơ sở vi phạm", style="white")
        table.add_column("Sản phẩm", style="white")
        table.add_column("Thu lợi bất chính", style="bold red")
        table.add_column("Tiền phạt", style="red")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            table.add_row(r.get("audit_code", ""), r.get("business_name", ""), r.get("product_name", ""), f"{r.get('illicit_profit_vnd', 0):,.0f} VND", f"{r.get('penalty_fine_vnd', 0):,.0f} VND", r.get("status", ""))
    else:
        table.add_column("Mã kê khai", style="bold cyan")
        table.add_column("Doanh nghiệp", style="white")
        table.add_column("Mặt hàng", style="white")
        table.add_column("Giá mới", style="yellow")
        table.add_column("Biến động", style="cyan")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "DECLARATION_ACCEPTED" else "red"
            table.add_row(r.get("declaration_code", ""), r.get("enterprise_name", ""), r.get("product_name", ""), f"{r.get('declared_price_vnd', 0):,.0f} VND", f"{r.get('change_pct', 0)}%", f"[{color}]{r.get('status', '')}[/]")

    console.print(table)


@price_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp quản lý giá, bình ổn giá và thẩm định giá."""
    from src.core.price_engine import PriceEngine

    engine = PriceEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
