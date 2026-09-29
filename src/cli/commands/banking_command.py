# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Commercial Banking, Credit Institutions & Basel II Suite (Phase 80)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

banking_app = typer.Typer(
    name="banking",
    help="Vietnamese Commercial Banking, Credit Underwriting, Basel II CAR & CIC Suite.",
)
console = Console()


@banking_app.callback(invoke_without_command=True)
def banking_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hệ thống ngân hàng, an toàn vốn Basel II và giám sát nợ xấu CIC."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    insts = status_data["institutions"]
    credit = status_data["credit_underwriting"]
    car = status_data["basel_ii_car"]
    cic = status_data["asset_quality_cic"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ NGÂN HÀNG & AN TOÀN VỐN (LUẬT CÁC TCTD 2024)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  TCTD được cấp phép:  [bold cyan]{insts['total_licensed']}[/] tổ chức ([bold green]{insts['commercial_banks']}[/] Ngân hàng Thương mại)\n"
            f"  Hồ sơ cấp tín dụng:  [bold green]{credit['approved_facilities']}/{credit['total_facilities']}[/] khoản vay phê duyệt đạt chuẩn (Dư nợ: [bold cyan]{credit['total_approved_balance_vnd']:,.0f}[/] VND)\n"
            f"  An toàn vốn Basel II:[bold green]{car['compliant_audits_ratio_gte_8pct']}/{car['total_audits']}[/] đợt kiểm tra đạt chuẩn tỷ lệ an toàn vốn (CAR >= 8.0%)\n"
            f"  Chất lượng tín dụng: [bold]{cic['classified_loans_count']}[/] khoản phân loại ([bold red]{cic['npl_loans_count']}[/] nợ xấu NPL - Tỷ lệ: [bold yellow]{cic['npl_ratio_pct']}%[/])\n"
            f"  Trích lập dự phòng:  [bold cyan]{cic['total_provisions_vnd']:,.0f}[/] VND (Dự phòng cụ thể + chung)",
            title="[bold blue]Vietnam Commercial Banking & Basel II Telemetry[/]",
            border_style="green",
        )
    )


@banking_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên tổ chức tín dụng (vd: 'Ngân hàng TMCP Phát triển Mekong')"),
    institution_type: str = typer.Option("COMMERCIAL_BANK", "--type", "-t", help="Loại hình: COMMERCIAL_BANK, POLICY_BANK, FINANCE_COMPANY, FINANCIAL_LEASING, FOREIGN_BANK_BRANCH"),
    tax_id: str = typer.Option("0100000001", "--tax-id", help="Mã số thuế tổ chức tín dụng"),
    capital: float = typer.Option(3_500_000_000_000.0, "--capital", "-c", help="Vốn điều lệ thực góp (VND)"),
    address: str = typer.Option("Hà Nội, Việt Nam", "--address", "-a", help="Địa chỉ trụ sở chính"),
    governor: str = typer.Option("Thống đốc Ngân hàng Nhà nước Việt Nam", "--governor", help="Người ký quyết định cấp phép"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra vốn pháp định và cấp giấy phép thành lập tổ chức tín dụng (Luật Các TCTD 2024)."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    try:
        res = engine.license_institution(
            institution_name=name,
            institution_type=institution_type,
            tax_id=tax_id,
            charter_capital_vnd=capital,
            headquarters_address=address,
            governor_signed_by=governor,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi cấp phép TCTD:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]GIẤY PHÉP THÀNH LẬP & HOẠT ĐỘNG TỔ CHỨC TÍN DỤNG (NHNN)[/]")
    table.add_column("Thuộc tính", style="cyan", no_wrap=True)
    table.add_column("Chi tiết", style="white")

    table.add_row("Tên tổ chức tín dụng", res["institution_name"])
    table.add_row("Loại hình pháp lý", res["institution_name_vi"])
    table.add_row("Số Giấy phép NHNN", f"[bold green]{res['sbv_license_number']}[/]")
    table.add_row("Vốn điều lệ thực góp", f"[bold cyan]{res['charter_capital_vnd']:,.0f}[/] VND (Pháp định: {res['statutory_min_capital_vnd']:,.0f} VND)")
    table.add_row("Mã số thuế", res["tax_id"])
    table.add_row("Trụ sở chính", res["headquarters_address"])
    table.add_row("Ngày cấp phép", res["license_date"])
    table.add_row("Người ký phê chuẩn", res["governor_signed_by"])
    table.add_row("Căn cứ pháp lý", res["statutory_ref"])

    console.print(table)


@banking_app.command("credit")
def credit_cmd(
    borrower: str = typer.Argument(..., help="Tên khách hàng vay vốn (Cá nhân hoặc Doanh nghiệp)"),
    borrower_id: str = typer.Argument(..., help="Số CCCD hoặc Mã số thuế khách hàng vay"),
    amount: float = typer.Argument(..., help="Số tiền cấp tín dụng đề xuất (VND)"),
    rate: float = typer.Option(8.5, "--rate", "-r", help="Lãi suất cho vay (%/năm)"),
    term: int = typer.Option(12, "--term", "-t", help="Thời hạn vay (tháng)"),
    purpose: str = typer.Option("Tài trợ vốn lưu động sản xuất kinh doanh", "--purpose", help="Mục đích sử dụng vốn"),
    collateral: str = typer.Option("REAL_ESTATE", "--collateral", help="Loại TSBĐ: REAL_ESTATE, VEHICLE, DEPOSIT, STOCKS, NONE"),
    collateral_value: float = typer.Option(0.0, "--value", help="Giá trị định giá TSBĐ (VND)"),
    bank_equity: float = typer.Option(20_000_000_000_000.0, "--bank-equity", help="Vốn tự có của ngân hàng (VND)"),
    corporate: bool = typer.Option(True, "--corporate/--retail", help="Khách hàng doanh nghiệp hay cá nhân"),
    bank_name: str = typer.Option("Ngân hàng TMCP Mekong", "--bank", help="Tên ngân hàng tài trợ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định hạn mức tín dụng và giới hạn tập trung rủi ro 14% vốn tự có (Điều 136 Luật Các TCTD)."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    try:
        res = engine.underwrite_credit(
            borrower_name=borrower,
            borrower_id=borrower_id,
            loan_amount_vnd=amount,
            interest_rate_pct=rate,
            term_months=term,
            purpose=purpose,
            collateral_type=collateral,
            collateral_value_vnd=collateral_value,
            bank_equity_vnd=bank_equity,
            is_corporate=corporate,
            institution_name=bank_name,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi thẩm định tín dụng:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    verdict_badge = "[bold green]PHÊ DUYỆT (APPROVED)[/]" if res["is_approved"] else "[bold red]TỪ CHỐI (REJECTED)[/]"
    table = Table(title=f"KẾT QUẢ THẨM ĐỊNH TÍN DỤNG: {verdict_badge}")
    table.add_column("Hạng mục thẩm tra", style="cyan", no_wrap=True)
    table.add_column("Giá trị", style="white")

    table.add_row("Khách hàng vay vốn", f"{res['borrower_name']} ({'Doanh nghiệp' if res['is_corporate'] else 'Cá nhân'})")
    table.add_row("Mã định danh/MST", res["borrower_id"])
    table.add_row("Số tiền vay đề xuất", f"[bold cyan]{res['loan_amount_vnd']:,.0f}[/] VND")
    table.add_row("Lãi suất & Thời hạn", f"{res['interest_rate_pct']}%/năm | {res['term_months']} tháng")
    table.add_row("Tỷ lệ/Vốn tự có ngân hàng", f"[bold yellow]{res['exposure_ratio_pct']}%[/] (Giới hạn tối đa: {res['statutory_limit_pct']}%)")
    table.add_row("Tài sản bảo đảm (TSBĐ)", f"{res['collateral_type']} (Định giá: {res['collateral_value_vnd']:,.0f} VND - LTV: {res['ltv_pct']}%)")
    table.add_row("Số hợp đồng tín dụng", res["contract_number"])
    table.add_row("Nhóm nợ ban đầu (CIC)", f"Nhóm {res['cic_debt_group']} (Nợ đủ tiêu chuẩn)")

    if res["rejection_reasons"]:
        reasons_str = "\n".join(f"- {r}" for r in res["rejection_reasons"])
        table.add_row("Lý do từ chối", f"[bold red]{reasons_str}[/]")

    console.print(table)


@banking_app.command("car")
def car_cmd(
    bank: str = typer.Argument(..., help="Tên ngân hàng (vd: 'Ngân hàng TMCP Mekong')"),
    tier1: float = typer.Argument(..., help="Vốn cấp 1 - Vốn chủ sở hữu, quỹ dự trữ (VND)"),
    tier2: float = typer.Argument(..., help="Vốn cấp 2 - Trái phiếu chuyển đổi, quỹ dự phòng (VND)"),
    credit_rwa: float = typer.Argument(..., help="Tài sản có rủi ro tín dụng (VND)"),
    market_rwa: float = typer.Argument(..., help="Tài sản có rủi ro thị trường (VND)"),
    op_rwa: float = typer.Argument(..., help="Tài sản có rủi ro hoạt động (VND)"),
    quarter: str = typer.Option("Q3/2026", "--quarter", "-q", help="Kỳ báo cáo an toàn vốn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra Tỷ lệ an toàn vốn CAR theo chuẩn mực Basel II (Thông tư 41/2016/TT-NHNN)."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    try:
        res = engine.audit_capital_adequacy(
            institution_name=bank,
            tier1_capital_vnd=tier1,
            tier2_capital_vnd=tier2,
            credit_rwa_vnd=credit_rwa,
            market_rwa_vnd=market_rwa,
            operational_rwa_vnd=op_rwa,
            reporting_quarter=quarter,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tính toán an toàn vốn CAR:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_badge = (
        f"[bold green]{res['status_name_vi']}[/]"
        if res["is_compliant"]
        else f"[bold red]{res['status_name_vi']}[/]"
    )
    table = Table(title=f"BÁO CÁO AN TOÀN VỐN BASEL II (CAR): {status_badge}")
    table.add_column("Chỉ số Basel II", style="cyan", no_wrap=True)
    table.add_column("Giá trị", style="white")

    table.add_row("Ngân hàng kiểm toán", res["institution_name"])
    table.add_row("Kỳ báo cáo", res["reporting_quarter"])
    table.add_row("Vốn cấp 1 (Tier 1)", f"{res['tier1_capital_vnd']:,.0f} VND")
    table.add_row("Vốn cấp 2 (Tier 2)", f"{res['tier2_capital_vnd']:,.0f} VND")
    table.add_row("Tổng vốn tự có", f"[bold cyan]{res['total_own_capital_vnd']:,.0f}[/] VND")
    table.add_row("Tổng tài sản có rủi ro (RWA)", f"[bold]{res['total_rwa_vnd']:,.0f}[/] VND (Tín dụng + TT + HĐ)")
    table.add_row("Tỷ lệ an toàn vốn (CAR)", f"[bold green]{res['car_ratio_pct']}%[/] (Tối thiểu luật định: {res['statutory_min_car_pct']}%)")
    table.add_row("Tình trạng an toàn", status_badge)
    table.add_row("Khuyến nghị giám sát", res["action_required"])

    console.print(table)


@banking_app.command("debt")
def debt_cmd(
    contract: str = typer.Argument(..., help="Số hợp đồng tín dụng"),
    borrower: str = typer.Argument(..., help="Tên khách hàng vay"),
    balance: float = typer.Argument(..., help="Số dư nợ còn lại (VND)"),
    overdue_days: int = typer.Option(0, "--overdue", "-d", help="Số ngày quá hạn nợ gốc hoặc lãi"),
    collateral: float = typer.Option(0.0, "--collateral", "-c", help="Giá trị TSBĐ khấu trừ dự phòng (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Phân loại 5 nhóm nợ CIC và tính toán trích lập dự phòng rủi ro (Thông tư 11/2021/TT-NHNN)."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    try:
        res = engine.classify_credit_debt(
            contract_number=contract,
            borrower_name=borrower,
            outstanding_balance_vnd=balance,
            overdue_days=overdue_days,
            deductible_collateral_vnd=collateral,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi phân loại nợ CIC:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    npl_badge = "[bold red]NỢ XẤU (NPL)[/]" if res["is_npl"] else "[bold green]NỢ ĐỦ TIÊU CHUẨN / CHÚ Ý[/]"
    table = Table(title=f"KẾT QUẢ PHÂN LOẠI NỢ CIC & DỰ PHÒNG: {npl_badge}")
    table.add_column("Hạng mục", style="cyan", no_wrap=True)
    table.add_column("Chi tiết", style="white")

    table.add_row("Khách hàng vay", res["borrower_name"])
    table.add_row("Hợp đồng tín dụng", res["contract_number"])
    table.add_row("Số ngày quá hạn", f"[bold yellow]{res['overdue_days']}[/] ngày")
    table.add_row("Phân nhóm nợ CIC", f"[bold cyan]Nhóm {res['debt_group']}[/] ({res['group_name_vi']})")
    table.add_row("Số dư nợ gốc", f"[bold]{res['outstanding_balance_vnd']:,.0f}[/] VND")
    table.add_row("Giá trị TSBĐ khấu trừ", f"{res['deductible_collateral_vnd']:,.0f} VND")
    table.add_row("Số dư chịu rủi ro ròng", f"{res['net_exposure_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ dự phòng cụ thể", f"{res['specific_provision_rate_pct']}%")
    table.add_row("Dự phòng rủi ro cụ thể", f"[bold yellow]{res['specific_provision_vnd']:,.0f}[/] VND")
    table.add_row("Dự phòng rủi ro chung (0.75%)", f"[bold cyan]{res['general_provision_vnd']:,.0f}[/] VND")
    table.add_row("Tổng dự phòng trích lập", f"[bold red]{res['total_provision_vnd']:,.0f}[/] VND")

    console.print(table)


@banking_app.command("liquidity")
def liquidity_cmd(
    bank: str = typer.Argument(..., help="Tên ngân hàng (vd: 'Ngân hàng TMCP Mekong')"),
    loans: float = typer.Argument(..., help="Tổng dư nợ cho vay (VND)"),
    deposits: float = typer.Argument(..., help="Tổng tiền gửi huy động (VND)"),
    short_funds: float = typer.Argument(..., help="Tổng nguồn vốn ngắn hạn huy động (VND)"),
    mid_long_loans: float = typer.Argument(..., help="Dư nợ cho vay trung và dài hạn (VND)"),
    report_date: str = typer.Option(None, "--date", help="Ngày chốt số liệu (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra giới hạn an toàn thanh khoản: Tỷ lệ LDR (<=85%) và vốn ngắn hạn cho vay trung dài hạn (<=30%)."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    try:
        res = engine.audit_liquidity_ratios(
            institution_name=bank,
            total_loans_vnd=loans,
            total_deposits_vnd=deposits,
            short_term_funds_vnd=short_funds,
            mid_long_loans_vnd=mid_long_loans,
            reporting_date=report_date,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi thẩm tra thanh khoản:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_badge = "[bold green]ĐẠT CHUẨN THANH KHOẢN[/]" if res["overall_status"] == "COMPLIANT" else "[bold red]VI PHẠM GIỚI HẠN THANH KHOẢN[/]"
    table = Table(title=f"BÁO CÁO GIỚI HẠN AN TOÀN THANH KHOẢN: {status_badge}")
    table.add_column("Chỉ số an toàn", style="cyan", no_wrap=True)
    table.add_column("Thực tế", style="white")
    table.add_column("Giới hạn NHNN", style="yellow")
    table.add_column("Đánh giá", style="white")

    ldr_stat = "[bold green]ĐẠT[/]" if res["ldr_compliant"] else "[bold red]VƯỢT TRẦN[/]"
    table.add_row(
        "Tỷ lệ LDR (Cho vay / Tiền gửi)",
        f"[bold]{res['ldr_ratio_pct']}%[/]",
        f"Tối đa {res['ldr_max_limit_pct']}%",
        ldr_stat,
    )

    short_stat = "[bold green]ĐẠT[/]" if res["short_for_mid_long_compliant"] else "[bold red]VƯỢT TRẦN[/]"
    table.add_row(
        "Vốn ngắn hạn cho vay trung dài hạn",
        f"[bold]{res['short_for_mid_long_ratio_pct']}%[/]",
        f"Tối đa {res['short_for_mid_long_max_limit_pct']}%",
        short_stat,
    )

    table.add_row("Tổng dư nợ cho vay", f"{res['total_loans_vnd']:,.0f} VND", "-", "-")
    table.add_row("Tổng tiền gửi huy động", f"{res['total_deposits_vnd']:,.0f} VND", "-", "-")
    table.add_row("Nguồn vốn ngắn hạn", f"{res['short_term_funds_vnd']:,.0f} VND", "-", "-")
    table.add_row("Dư nợ trung và dài hạn", f"{res['mid_long_loans_vnd']:,.0f} VND", "-", "-")

    console.print(table)


@banking_app.command("list")
def list_cmd(
    resource_type: str = typer.Option("licenses", "--type", "-t", help="Tài nguyên: licenses, credit, car, debt, liquidity"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh sách giấy phép ngân hàng, khoản tín dụng, an toàn vốn CAR, phân loại nợ."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    res_type = resource_type.lower().strip()

    if res_type in ("licenses", "license", "banks", "tctd"):
        records = engine.list_licenses(limit=limit)
    elif res_type in ("credit", "loans", "facilities", "tindung"):
        records = engine.list_credit_facilities(limit=limit)
    elif res_type in ("car", "basel", "capital", "antoanvon"):
        records = engine.list_car_audits(limit=limit)
    elif res_type in ("debt", "cic", "provisions", "noxau"):
        records = engine.list_debt_classifications(limit=limit)
    elif res_type in ("liquidity", "ldr", "thanhkhoan"):
        records = engine.list_liquidity_audits(limit=limit)
    else:
        records = engine.list_licenses(limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"DANH MỤC DỮ LIỆU NGÂN HÀNG: {resource_type.upper()} ({len(records)} bản ghi)")
    if not records:
        console.print(f"[yellow]Chưa có dữ liệu nào cho mục '{resource_type}'.[/]")
        return

    first_item = records[0]
    keys = list(first_item.keys())[:6]
    for k in keys:
        table.add_column(k.replace("_", " ").title(), style="cyan")

    for rec in records:
        row_values = []
        for k in keys:
            v = rec.get(k, "")
            if isinstance(v, float):
                row_values.append(f"{v:,.0f}" if v > 1000 else f"{v:.2f}")
            else:
                row_values.append(str(v))
        table.add_row(*row_values)

    console.print(table)


@banking_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo telemetry tổng hợp tình hình hoạt động ngân hàng, an toàn vốn và rủi ro tín dụng."""
    from src.core.banking_engine import BankingEngine

    engine = BankingEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print_json(data=data)
