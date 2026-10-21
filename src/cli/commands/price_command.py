# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Price Management, Anti-Price Gouging & Valuation Suite (Phase 90)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

price_app = typer.Typer(name="price", help="Vietnamese Price Management, Anti-Price Gouging & Valuation Compliance Suite.")
console = Console()


@price_app.callback(invoke_without_command=True)
def price_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan hoạt động quản lý giá, bình ổn giá, chống tăng giá bất hợp lý và thẩm định giá."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.price_engine import PriceEngine
    s = PriceEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]HỆ THỐNG QUẢN LÝ GIÁ, BÌNH ỔN GIÁ & THẨM ĐỊNH GIÁ VIỆT NAM[/]\n\n"
        f"  Khung pháp lý:             [bold]{s['statutory_law']}[/]\n"
        f"  Hồ sơ kê khai giá:         [bold cyan]{s['total_price_declarations']}[/] hồ sơ ([bold yellow]{s['stabilized_commodities_declarations']}[/] thuộc danh mục bình ổn giá)\n"
        f"  Hậu kiểm niêm yết giá:     [bold]{s['total_price_posting_inspections']}[/] điểm bán ([bold red]{s['posting_violations_detected']}[/] vi phạm bán sai giá niêm yết)\n"
        f"  Chứng thư thẩm định giá:   [bold green]{s['total_valuation_certificates_issued']}[/] chứng thư đạt chuẩn TĐGVN | Tổng giá trị: [bold green]{s['total_appraised_asset_value_vnd']:,.0f} VND[/]\n"
        f"  Chống tăng giá bất hợp lý: [bold red]{s['price_gouging_cases_penalized']}[/] vụ đầu cơ/tăng giá xử phạt ([bold yellow]{s['total_illicit_recovery_and_fines_vnd']:,.0f} VND[/] thu hồi & phạt)",
        title="[bold green]Vietnam Price Surveillance, Anti-Gouging & Valuation Telemetry[/]", border_style="green",
    ))


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
    res = PriceEngine().declare_price(enterprise_name=enterprise, product_name=product, unit=unit, old_price_vnd=old_price, declared_price_vnd=new_price, effective_date=effective_date, is_stabilized_commodity=stabilized)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_approved"] else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ TIẾP NHẬN KÊ KHAI GIÁ (ĐIỀU 28 LUẬT GIÁ 2023)[/]\n\n"
        f"  Mã hồ sơ: [bold cyan]{res['declaration_code']}[/] | DN: [bold]{res['enterprise_name']}[/] | Hàng hóa: [white]{res['product_name']}[/] (ĐVT: {res['unit']})\n"
        f"  Giá cũ --> Giá mới: [white]{res['old_price_vnd']:,.0f} VND[/] --> [bold yellow]{res['declared_price_vnd']:,.0f} VND[/] ({res['change_pct']}%)\n"
        f"  Thuộc diện bình ổn: [bold]{'CÓ' if res['is_stabilized_good'] else 'KHÔNG'}[/] | Ngày hiệu lực: [cyan]{res['effective_date']}[/] | Trạng thái: [bold {color}]{res['status']}[/]\n"
        + (f"  Cảnh báo/Vi phạm: [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá: [bold green]Mức điều chỉnh giá hợp lý, đáp ứng điều kiện lưu thông[/]"),
        title=f"[bold {color}]Price Declaration Assessment[/]", border_style=color,
    ))


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
    res = PriceEngine().audit_price_posting(store_name=store, product_name=product, listed_price_vnd=listed, actual_selling_price_vnd=actual, is_posted_clearly=clearly_posted, currency=currency)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_compliant"] else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ KIỂM TRA NIÊM YẾT GIÁ (ĐIỀU 29 LUẬT GIÁ 2023)[/]\n\n"
        f"  Mã kiểm tra: [bold cyan]{res['audit_code']}[/] | Điểm KD: [bold]{res['store_name']}[/] | Hàng hóa: [white]{res['product_name']}[/]\n"
        f"  Giá niêm yết: [bold green]{res['listed_price_vnd']:,.0f} {res['currency']}[/] | Giá bán thực tế: [bold yellow]{res['actual_selling_price_vnd']:,.0f} {res['currency']}[/]\n"
        f"  Niêm yết rõ ràng: [white]{'ĐẠT CHUẨN' if res['is_posted_clearly'] else 'KHÔNG NIÊM YẾT'}[/] | Kết luận: [bold {color}]{res['status']}[/]"
        + (f"\n  Mức phạt ước tính: [bold red]{res['estimated_fine_vnd']:,.0f} VND (Nghị định 109/2013/NĐ-CP)[/]" if res["estimated_fine_vnd"] > 0 else "\n  Đánh giá: [bold green]Chấp hành đầy đủ quy định niêm yết giá[/]"),
        title=f"[bold {color}]Price Posting Compliance Audit[/]", border_style=color,
    ))


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
    res = PriceEngine().issue_valuation_certificate(appraisal_firm=firm, client_name=client, asset_description=asset, appraised_value_vnd=value, valuation_method=method, lead_appraiser=appraiser, licensed_appraisers_count=appraisers_count, has_firm_insurance=insurance)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_valid"] else "red"
    console.print(Panel(
        f"[bold {color}]CHỨNG THƯ THẨM ĐỊNH GIÁ TÀI SẢN (CHUẨN MỰC TĐGVN & LUẬT GIÁ 2023)[/]\n\n"
        f"  Số chứng thư: [bold cyan]{res['certificate_code']}[/] | Tổ chức: [bold]{res['appraisal_firm']}[/] | Khách hàng: [white]{res['client_name']}[/]\n"
        f"  Tài sản: [white]{res['asset_description']}[/] | Giá trị TĐ: [bold green]{res['appraised_value_vnd']:,.0f} VND[/] ({res['valuation_method']})\n"
        f"  TĐV chủ trì: [yellow]{res['lead_appraiser']}[/] ({res['licensed_appraisers_count']} TĐV) | Bảo hiểm: [white]{'ĐÃ THAM GIA' if res['has_firm_insurance'] else 'CHƯA MUA'}[/]\n"
        f"  Hiệu lực: [bold]{res['validity_period_months']} tháng[/] | Kết luận: [bold {color}]{res['status']}[/]\n"
        + (f"  Thiếu sót: [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Hiệu lực: [bold green]Chứng thư hợp lệ, có giá trị pháp lý[/]"),
        title=f"[bold {color}]Valuation Certificate Issuance[/]", border_style=color,
    ))


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
    res = PriceEngine().check_price_gouging(business_name=business, product_name=product, base_price_vnd=base, gouged_price_vnd=gouged, units_sold=units, is_crisis_period=crisis)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "red" if res["status"] == "PRICE_GOUGING_CONFIRMED" else "green"
    console.print(Panel(
        f"[bold {color}]THANH TRA HÀNH VI TĂNG GIÁ BẤT HỢP LÝ & GĂM HÀNG (ANTI-GOUGING)[/]\n\n"
        f"  Mã TT: [bold cyan]{res['audit_code']}[/] | Cơ sở: [bold]{res['business_name']}[/] | Mặt hàng: [white]{res['product_name']}[/] ({res['units_sold']:,} ĐV)\n"
        f"  Giá gốc --> Giá bán: [white]{res['base_price_vnd']:,.0f} VND[/] --> [bold red]{res['gouged_price_vnd']:,.0f} VND[/] (+{res['increase_pct']}%)\n"
        f"  Thu lợi bất chính: [bold red]{res['illicit_profit_vnd']:,.0f} VND[/] | Phạt HC: [bold red]{res['penalty_fine_vnd']:,.0f} VND[/]\n"
        f"  Kết luận thanh tra: [bold {color}]{res['legal_conclusion']}[/]",
        title=f"[bold {color}]Anti-Price Gouging Investigation[/]", border_style=color,
    ))


@price_app.command("list")
def list_records_cmd(category: str = typer.Argument("declarations", help="Danh mục: declarations, postings, valuations, gouging"), limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON")) -> None:
    """Tra cứu danh mục hồ sơ kê khai giá, niêm yết giá, chứng thư thẩm định hoặc xử lý tăng giá."""
    from src.core.price_engine import PriceEngine
    records = PriceEngine().list_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    table = Table(title=f"Danh mục quản lý giá & thẩm định giá [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["postings", "listing", "niem_yet"]:
        for col, st in (("Mã KT", "bold cyan"), ("Cửa hàng", "white"), ("Sản phẩm", "white"), ("Giá niêm yết", "green"), ("Giá bán TT", "yellow"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            c = "green" if r.get("status") == "COMPLIANT_POSTING" else "red"
            table.add_row(r.get("audit_code", ""), r.get("store_name", ""), r.get("product_name", ""), f"{r.get('listed_price_vnd', 0):,.0f} VND", f"{r.get('actual_selling_price_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")
    elif category in ["valuations", "appraisals", "tham_dinh"]:
        for col, st in (("Số chứng thư", "bold cyan"), ("Doanh nghiệp TĐG", "white"), ("Khách hàng", "yellow"), ("Phương pháp", "cyan"), ("Giá trị thẩm định", "bold green"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            c = "green" if r.get("is_valid") else "red"
            table.add_row(r.get("certificate_code", ""), r.get("appraisal_firm", ""), r.get("client_name", ""), r.get("valuation_method", ""), f"{r.get('appraised_value_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")
    elif category in ["gouging", "violations", "tang_gia"]:
        for col, st in (("Mã TT", "bold cyan"), ("Cơ sở vi phạm", "white"), ("Sản phẩm", "white"), ("Thu lợi bất chính", "bold red"), ("Tiền phạt", "red"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            table.add_row(r.get("audit_code", ""), r.get("business_name", ""), r.get("product_name", ""), f"{r.get('illicit_profit_vnd', 0):,.0f} VND", f"{r.get('penalty_fine_vnd', 0):,.0f} VND", r.get("status", ""))
    else:
        for col, st in (("Mã kê khai", "bold cyan"), ("Doanh nghiệp", "white"), ("Mặt hàng", "white"), ("Giá mới", "yellow"), ("Biến động", "cyan"), ("Trạng thái", "bold")):
            table.add_column(col, style=st)
        for r in records:
            c = "green" if r.get("status") == "DECLARATION_ACCEPTED" else "red"
            table.add_row(r.get("declaration_code", ""), r.get("enterprise_name", ""), r.get("product_name", ""), f"{r.get('declared_price_vnd', 0):,.0f} VND", f"{r.get('change_pct', 0)}%", f"[{c}]{r.get('status', '')}[/]")
    console.print(table)


@price_app.command("status")
def status_cmd(json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo chỉ số telemetry tổng hợp quản lý giá, bình ổn giá và thẩm định giá."""
    from src.core.price_engine import PriceEngine
    typer.echo(json.dumps(PriceEngine().get_status(), indent=2, ensure_ascii=False))
