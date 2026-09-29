# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Securities, Stock Exchanges & Capital Markets (Phase 79)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
securities_app = typer.Typer(
    name="securities",
    help="Securities — Vietnamese Securities, Stock Exchanges & Capital Markets Suite",
    add_completion=False,
)


@securities_app.callback(invoke_without_command=True)
def securities_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Thị trường Chứng khoán, Chào bán IPO & Kiểm soát Rủi ro Giao dịch Ký quỹ."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    offs = status_data["offerings"]
    lists = status_data["listings"]
    margin = status_data["margin_risk"]
    safety = status_data["brokerage_safety_car"]
    practs = status_data["practitioners"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG THỊ TRƯỜNG CHỨNG KHOÁN & THẨM ĐỊNH NIÊM YẾT (LUẬT CHỨNG KHOÁN 2019)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Đợt chào bán/IPO:    [bold cyan]{offs['total']}[/] hồ sơ ([bold green]{offs['approved_ipos']}[/] đợt chào bán được cấp phép UBCKNN)\n"
            f"  Cổ phiếu niêm yết:   [bold green]{lists['total_listed']}[/] mã ([bold cyan]{lists['hose_stocks']}[/] HOSE, [bold yellow]{lists['hnx_stocks']}[/] HNX, [bold magenta]{lists['upcom_stocks']}[/] UPCoM)\n"
            f"  Tài khoản ký quỹ:    [bold]{margin['monitored_accounts']:,}[/] TK giám sát ([bold yellow]{margin['active_margin_calls']}[/] Margin Call, [bold red]{margin['active_force_sells']}[/] Bán giải chấp)\n"
            f"  An toàn vốn CTCK:    [bold green]{safety['compliant_firms_ratio_gte_180']}/{safety['total_firm_audits']}[/] đợt kiểm tra đạt tỷ lệ an toàn tài chính (CAR >= 180%)\n"
            f"  Người hành nghề CK:  [bold cyan]{practs['total_licensed']}[/] chuyên gia có chứng chỉ hành nghề UBCKNN",
            title="[bold blue]Vietnam Securities & Capital Markets Telemetry[/]",
            border_style="green",
        )
    )


@securities_app.command("offering")
def offering_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp đăng ký chào bán (vd: 'Công ty Cổ phần Công nghệ Mekong')"),
    ticker: str = typer.Argument(..., help="Mã cổ phiếu dự kiến (vd: 'MKT')"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    offering_type: str = typer.Option("IPO", "--type", "-t", help="Loại hình: IPO, PUBLIC_OFFERING, RIGHTS_ISSUE, PRIVATE_PLACEMENT"),
    capital: float = typer.Option(50_000_000_000.0, "--capital", "-c", help="Vốn điều lệ thực góp (VND)"),
    shares: int = typer.Option(5_000_000, "--shares", "-s", help="Số lượng cổ phiếu chào bán"),
    price: float = typer.Option(20_000.0, "--price", "-p", help="Giá chào bán dự kiến (VND/CP)"),
    roe: float = typer.Option(8.5, "--roe", help="ROE năm liền trước (%)"),
    two_years_profitable: bool = typer.Option(True, "--profitable/--unprofitable", help="Kinh doanh 2 năm liền trước có lãi"),
    has_losses: bool = typer.Option(False, "--accum-losses/--no-accum-losses", help="Có lỗ lũy kế không"),
    shareholders: int = typer.Option(150, "--shareholders", help="Số lượng nhà đầu tư không phải cổ đông lớn"),
    ratio: float = typer.Option(18.0, "--ratio", help="Tỷ lệ cổ phiếu biểu quyết bán cho cổ đông nhỏ (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện chào bán cổ phiếu ra công chúng hoặc IPO theo Luật Chứng khoán 2019."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    result = engine.audit_public_offering(
        enterprise_name=name,
        ticker_symbol=ticker,
        tax_id=tax_id,
        offering_type=offering_type,
        charter_capital_vnd=capital,
        shares_offered=shares,
        offering_price_vnd=price,
        roe_prior_year_pct=roe,
        two_years_profitable=two_years_profitable,
        has_accumulated_losses=has_losses,
        non_major_shareholder_count=shareholders,
        non_major_ratio_pct=ratio,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Thẩm Định Chào Bán Cổ Phiếu / IPO — {result['ticker_symbol']}")
    table.add_column("Chỉ tiêu thẩm định", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")

    table.add_row("Tên doanh nghiệp", result["enterprise_name"])
    table.add_row("Mã chứng khoán", result["ticker_symbol"])
    table.add_row("Loại hình chào bán", result["offering_name_vi"])
    table.add_row("Vốn điều lệ thực góp", f"{result['charter_capital_vnd']:,.0f} VND")
    table.add_row("Số lượng CP chào bán", f"{result['shares_offered']:,} CP")
    table.add_row("Giá chào bán", f"{result['offering_price_vnd']:,.0f} VND/CP")
    table.add_row("Tổng giá trị huy động", f"{result['total_offering_value_vnd']:,.0f} VND")
    table.add_row("Kết luận thẩm định", f"[bold green]{result['audit_verdict']}[/]" if result["is_approved"] else f"[bold red]{result['audit_verdict']}[/]")
    table.add_row("Mã số tiếp nhận UBCKNN", result["ssc_registration_number"])
    table.add_row("Căn cứ pháp lý", result["statutory_ref"])

    console.print(table)
    if result["rejection_reasons"]:
        console.print("[bold red]Lý do không đạt chuẩn chào bán:[/bold red]")
        for reason in result["rejection_reasons"]:
            console.print(f"  [red]- {reason}[/red]")


@securities_app.command("listing")
def listing_cmd(
    ticker: str = typer.Argument(..., help="Mã chứng khoán niêm yết (vd: 'MKT')"),
    company: str = typer.Argument(..., help="Tên công ty niêm yết"),
    exchange: str = typer.Option("HOSE", "--exchange", "-e", help="Sàn giao dịch: HOSE, HNX, UPCOM"),
    shares: int = typer.Option(50_000_000, "--shares", "-s", help="Số lượng cổ phiếu niêm yết"),
    par: float = typer.Option(10_000.0, "--par", help="Mệnh giá cổ phiếu (VND)"),
    price: float = typer.Option(35_000.0, "--price", "-p", help="Giá tham chiếu ngày đầu tiên (VND)"),
    capital: float = typer.Option(500_000_000_000.0, "--capital", "-c", help="Vốn điều lệ thực góp (VND)"),
    roe: float = typer.Option(12.5, "--roe", help="ROE năm gần nhất (%)"),
    years: int = typer.Option(5, "--years", "-y", help="Số năm hoạt động dưới dạng CTCP"),
    shareholders: int = typer.Option(450, "--shareholders", help="Số lượng cổ đông không phải cổ đông lớn"),
    has_losses: bool = typer.Option(False, "--accum-losses/--no-accum-losses", help="Có lỗ lũy kế không"),
    overdue_debt: bool = typer.Option(False, "--overdue-debt/--no-overdue-debt", help="Có nợ quá hạn trên 1 năm không"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra tiêu chuẩn niêm yết cổ phiếu trên HOSE, HNX hoặc UPCoM theo Nghị định 155/2020/NĐ-CP."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    result = engine.verify_listing_qualification(
        ticker_symbol=ticker,
        company_name=company,
        exchange=exchange,
        listed_shares=shares,
        par_value_vnd=par,
        current_market_price_vnd=price,
        charter_capital_vnd=capital,
        roe_pct=roe,
        operating_years=years,
        shareholder_count_non_major=shareholders,
        has_accumulated_losses=has_losses,
        has_overdue_debt_1yr=overdue_debt,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Thẩm Định Niêm Yết Chứng Khoán — {result['ticker_symbol']} ({result['exchange']})")
    table.add_column("Chỉ tiêu niêm yết", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold green")

    table.add_row("Mã cổ phiếu", result["ticker_symbol"])
    table.add_row("Tên tổ chức phát hành", result["company_name"])
    table.add_row("Sàn giao dịch", f"{result['exchange']} ({result['exchange_name_vi']})")
    table.add_row("Khối lượng niêm yết", f"{result['listed_shares']:,} CP")
    table.add_row("Vốn hóa thị trường", f"{result['market_cap_vnd']:,.0f} VND")
    table.add_row("Số quyết định niêm yết", result["listing_decision_number"])
    table.add_row("Kết luận phê duyệt", f"[bold green]{result['audit_verdict']}[/]" if result["is_approved"] else f"[bold red]{result['audit_verdict']}[/]")
    table.add_row("Ngày niêm yết", result["listing_date"])
    table.add_row("Căn cứ pháp lý", result["statutory_ref"])

    console.print(table)
    if result["rejections"]:
        console.print("[bold red]Lý do từ chối niêm yết:[/bold red]")
        for rej in result["rejections"]:
            console.print(f"  [red]- {rej}[/red]")


@securities_app.command("margin")
def margin_cmd(
    name: str = typer.Argument(..., help="Họ và tên nhà đầu tư"),
    investor_id: str = typer.Argument(..., help="Số tài khoản giao dịch chứng khoán (vd: '026C123456')"),
    firm: str = typer.Option("Công ty CP Chứng khoán Mekong", "--firm", "-f", help="Công ty chứng khoán quản lý"),
    assets: float = typer.Option(500_000_000.0, "--assets", "-a", help="Tổng giá trị tài sản trong tiểu khoản margin (VND)"),
    loan: float = typer.Option(250_000_000.0, "--loan", "-l", help="Dư nợ vay giao dịch ký quỹ (VND)"),
    collateral: float = typer.Option(500_000_000.0, "--collateral", help="Giá trị tài sản bảo đảm định giá (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Giám sát tỷ lệ ký quỹ tài khoản, phát hiện Margin Call hoặc Force Sell (Thông tư 120/2020/TT-BTC)."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    result = engine.audit_margin_account(
        investor_name=name,
        investor_id=investor_id,
        brokerage_firm=firm,
        total_asset_value_vnd=assets,
        loan_balance_vnd=loan,
        collateral_value_vnd=collateral,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Quản Lý Rủi Ro Ký Quỹ — Tài Khoản {result['investor_id']}")
    table.add_column("Chỉ số an toàn tài khoản", style="cyan")
    table.add_column("Thông số", justify="right", style="bold green")

    table.add_row("Nhà đầu tư", result["investor_name"])
    table.add_row("Số tài khoản giao dịch", result["investor_id"])
    table.add_row("Tổng tài sản thực tế", f"{result['total_asset_value_vnd']:,.0f} VND")
    table.add_row("Dư nợ vay Margin", f"{result['loan_balance_vnd']:,.0f} VND")
    table.add_row("Giá trị tài sản ròng (Equity)", f"{result['equity_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ ký quỹ thực tế (R)", f"{result['margin_ratio_pct']}%")
    table.add_row("Tỷ lệ ký quỹ duy trì (MMR)", f"{result['maintenance_margin_req_pct']}%")
    table.add_row("Ngưỡng bán giải chấp (Force Sell)", f"{result['force_sell_threshold_pct']}%")
    table.add_row("Trạng thái rủi ro", f"[bold red]{result['status']}[/]" if result["status"] != "NORMAL" else f"[bold green]{result['status']}[/]")
    table.add_row("Số tiền cần bổ sung", f"{result['deficit_amount_vnd']:,.0f} VND")

    console.print(table)
    if result["status"] == "FORCE_SELL":
        console.print(f"[bold red]{result['action_required']}[/bold red]")
    elif result["status"] == "MARGIN_CALL":
        console.print(f"[bold yellow]{result['action_required']}[/bold yellow]")
    else:
        console.print(f"[dim]{result['action_required']}[/dim]")


@securities_app.command("safety")
def safety_cmd(
    firm: str = typer.Argument(..., help="Tên công ty chứng khoán (CTCK)"),
    tax_id: str = typer.Argument(..., help="Mã số thuế CTCK"),
    liquid: float = typer.Option(1_200_000_000_000.0, "--liquid", "-l", help="Vốn khả dụng (Liquid Capital - VND)"),
    market_risk: float = typer.Option(200_000_000_000.0, "--market-risk", help="Giá trị rủi ro thị trường (VND)"),
    settle_risk: float = typer.Option(100_000_000_000.0, "--settle-risk", help="Giá trị rủi ro thanh toán (VND)"),
    op_risk: float = typer.Option(150_000_000_000.0, "--op-risk", help="Giá trị rủi ro hoạt động (VND)"),
    quarter: str = typer.Option("Q3/2026", "--quarter", "-q", help="Kỳ báo cáo"),
    notes: str = typer.Option("", "--notes", help="Ghi chú"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra Tỷ lệ an toàn tài chính (CAR) của công ty chứng khoán theo Thông tư 121/2020/TT-BTC."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    result = engine.audit_firm_financial_safety(
        firm_name=firm,
        tax_id=tax_id,
        liquid_capital_vnd=liquid,
        market_risk_vnd=market_risk,
        settlement_risk_vnd=settle_risk,
        operational_risk_vnd=op_risk,
        reporting_quarter=quarter,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Tỷ Lệ An Toàn Tài Chính CTCK — {result['firm_name']} ({result['reporting_quarter']})")
    table.add_column("Chỉ tiêu an toàn vốn", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Tên công ty chứng khoán", result["firm_name"])
    table.add_row("Mã số thuế", result["tax_id"])
    table.add_row("Vốn khả dụng (Liquid Capital)", f"{result['liquid_capital_vnd']:,.0f} VND")
    table.add_row("Rủi ro thị trường", f"{result['market_risk_vnd']:,.0f} VND")
    table.add_row("Rủi ro thanh toán", f"{result['settlement_risk_vnd']:,.0f} VND")
    table.add_row("Rủi ro hoạt động", f"{result['operational_risk_vnd']:,.0f} VND")
    table.add_row("Tổng giá trị rủi ro", f"{result['total_risk_exposure_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ an toàn tài chính (CAR)", f"[bold green]{result['capital_adequacy_ratio_pct']}%[/]" if result["is_compliant"] else f"[bold red]{result['capital_adequacy_ratio_pct']}%[/]")
    table.add_row("Chuẩn tối thiểu luật định", f"{result['statutory_min_pct']}%")
    table.add_row("Xếp loại trạng thái", result["status_name_vi"])
    table.add_row("Biện pháp quản lý", result["regulatory_action"])

    console.print(table)


@securities_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Họ và tên người xin cấp chứng chỉ hành nghề"),
    id_card: str = typer.Argument(..., help="Số CCCD hoặc Hộ chiếu"),
    license_type: str = typer.Option("BROKERAGE", "--type", "-t", help="Loại CCHN: BROKERAGE, FINANCIAL_ANALYSIS, FUND_MANAGEMENT, INVESTMENT_BANKING"),
    firm: str = typer.Option("Công ty Cổ phần Chứng khoán Mekong", "--firm", "-f", help="Công ty chứng khoán/Quản lý quỹ trực thuộc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Cấp Chứng chỉ hành nghề chứng khoán chuyên nghiệp theo Luật Chứng khoán 2019."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    result = engine.issue_practitioner_license(
        practitioner_name=name,
        id_card_or_passport=id_card,
        license_type=license_type,
        firm_affiliation=firm,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Chứng Chỉ Hành Nghề Chứng Khoán — {result['practitioner_name']}")
    table.add_column("Thông tin người hành nghề", style="cyan")
    table.add_column("Chi tiết", justify="right", style="bold green")

    table.add_row("Mã chứng chỉ", result["ssc_license_number"])
    table.add_row("Họ và tên chuyên gia", result["practitioner_name"])
    table.add_row("Số định danh cá nhân", result["id_card_or_passport"])
    table.add_row("Loại chứng chỉ nghiệp vụ", result["license_name_vi"])
    table.add_row("Tổ chức công tác", result["firm_affiliation"])
    table.add_row("Ngày cấp", result["issue_date"])
    table.add_row("Hạn hiệu lực", result["expiry_date"])
    table.add_row("Trạng thái", result["compliance_status"])

    console.print(table)
    console.print(f"[dim]{result['message']}[/dim]")


@securities_app.command("list")
def list_cmd(
    list_type: str = typer.Option("listings", "--type", "-t", help="Loại danh sách: offerings, listings, margin, safety, practitioners"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách dạng JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ chào bán, cổ phiếu niêm yết, tài khoản margin, an toàn vốn hoặc CCHN."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    type_clean = list_type.strip().lower()

    if type_clean in ["offerings", "offering", "ipo"]:
        data = engine.list_offerings(limit=limit)
    elif type_clean in ["listings", "listing", "stocks"]:
        data = engine.list_listings(limit=limit)
    elif type_clean in ["margin", "margin_accounts", "accounts"]:
        data = engine.list_margin_accounts(limit=limit)
    elif type_clean in ["safety", "firm_safety", "car"]:
        data = engine.list_firm_safeties(limit=limit)
    elif type_clean in ["practitioners", "licenses", "cchn"]:
        data = engine.list_practitioners(limit=limit)
    else:
        raise ValueError(f"Loại danh sách không hợp lệ: '{list_type}'. Hỗ trợ: offerings, listings, margin, safety, practitioners")

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Dữ Liệu Chứng Khoán ({type_clean.upper()})")
    table.add_column("Mã định danh", style="dim")
    table.add_column("Tên đối tượng / Tổ chức", style="bold cyan")
    table.add_column("Phân loại / Sàn", style="yellow")
    table.add_column("Trạng thái", style="bold green")

    for item in data:
        id_str = item.get("ticker_symbol") or item.get("offering_id") or item.get("account_id") or item.get("audit_id") or item.get("ssc_license_number") or ""
        name_str = item.get("company_name") or item.get("enterprise_name") or item.get("investor_name") or item.get("firm_name") or item.get("practitioner_name") or ""
        type_str = item.get("exchange") or item.get("offering_type") or str(item.get("margin_ratio_pct", "")) or item.get("safety_status") or item.get("license_type") or ""
        status_str = item.get("status") or item.get("audit_verdict") or item.get("safety_status") or item.get("compliance_status") or ""
        table.add_row(str(id_str), str(name_str), str(type_str), str(status_str))

    console.print(table)


@securities_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo trạng thái dạng JSON"),
) -> None:
    """Kiểm tra tình trạng toàn diện thị trường chứng khoán và quản trị rủi ro."""
    from src.core.securities_engine import SecuritiesEngine

    engine = SecuritiesEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG CHỨNG KHOÁN & THỊ TRƯỜNG VỐN VIỆT NAM — TRẠNG THÁI TỔNG THỂ[/]\n\n"
            f"  Trạng thái hoạt động:  [bold green]{status_data['status']}[/]\n"
            f"  Khung pháp lý chuẩn:   [bold]{status_data['statutory_law']}[/]\n"
            f"  Đường dẫn dữ liệu:     [dim]{status_data['database_path']}[/]\n"
            f"  Hồ sơ chào bán IPO:    [bold cyan]{status_data['offerings']['total']}[/] hồ sơ\n"
            f"  Cổ phiếu niêm yết:     [bold green]{status_data['listings']['total_listed']}[/] mã\n"
            f"  Tài khoản ký quỹ:      [bold]{status_data['margin_risk']['monitored_accounts']}[/] tài khoản\n"
            f"  An toàn vốn CTCK:      [bold green]{status_data['brokerage_safety_car']['compliant_firms_ratio_gte_180']}[/] đợt kiểm tra đạt chuẩn",
            title="[bold blue]Securities System Health Status[/]",
            border_style="green",
        )
    )
