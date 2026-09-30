"""
CLI commands for Vietnamese Public Debt Management & Sovereign Credit (Luật Quản lý nợ công số 20/2017/QH14).
"""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
publicdebt_app = typer.Typer(
    name="publicdebt",
    help="Vietnamese Public Debt, Sovereign Bonds, ODA On-Lending & Debt Safety Red Lines Suite (Luật Quản lý nợ công số 20/2017/QH14)",
    no_args_is_help=False,
)


@publicdebt_app.callback(invoke_without_command=True)
def publicdebt_default(ctx: typer.Context) -> None:
    """Mặc định hiển thị tổng quan quản lý nợ công và chỉ tiêu an toàn nếu không có lệnh con."""
    if ctx.invoked_subcommand is None:
        status_cmd(json_mode=False)


@publicdebt_app.command("instrument")
def register_instrument_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã định danh công cụ nợ (VD: TPCP-2026-10Y, WB-ODA-VN01)"),
    category: str = typer.Option("GOVERNMENT_DEBT", "--category", help="Nhóm nợ công (GOVERNMENT_DEBT, GOVERNMENT_GUARANTEED_DEBT, LOCAL_GOVERNMENT_DEBT)"),
    type: str = typer.Option("TREASURY_BOND", "--type", "-t", help="Loại công cụ nợ (TREASURY_BOND, ODA_LOAN, CONCESSIONAL_FOREIGN_LOAN, SOVEREIGN_EUROBOND, POLICY_BANK_BOND, CORPORATE_GUARANTEED_LOAN, MUNICIPAL_BOND, ONLENT_ODA_LOAN)"),
    creditor: str = typer.Option(..., "--creditor", help="Tên chủ nợ / nhà đầu tư (VD: Kho bạc Nhà nước, World Bank, JICA, ADB)"),
    borrower: str = typer.Option(..., "--borrower", help="Tên cơ quan/đơn vị vay nợ (VD: Chính phủ Việt Nam, UBND TP. Hà Nội, EVN)"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền vay gốc theo nguyên tệ"),
    currency: str = typer.Option("VND", "--currency", help="Nguyên tệ khoản vay (VND, USD, JPY, EUR)"),
    fx_rate: float = typer.Option(1.0, "--fx-rate", help="Tỷ giá quy đổi sang VND"),
    rate: float = typer.Option(..., "--rate", "-r", help="Lãi suất vay (%/năm)"),
    tenor: int = typer.Option(..., "--tenor", help="Kỳ hạn vay nợ (năm)"),
    issue_date: str = typer.Option(..., "--issue-date", help="Ngày phát hành / ký hiệp định (YYYY-MM-DD)"),
    guarantee_fee: float = typer.Option(0.0, "--guarantee-fee", help="Phí bảo lãnh Chính phủ (%/năm)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký công cụ nợ công, trái phiếu Chính phủ hoặc hiệp định vay nước ngoài (Điều 4 & 27-31)."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    try:
        res = engine.register_debt_instrument(
            debt_code=code,
            debt_category=category,
            instrument_type=type,
            creditor_name=creditor,
            borrower_name=borrower,
            principal_amount=amount,
            interest_rate_pct=rate,
            tenor_years=tenor,
            issuance_date_str=issue_date,
            original_currency=currency,
            fx_rate_to_vnd=fx_rate,
            guarantee_fee_pct=guarantee_fee,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi đăng ký công cụ nợ công:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐĂNG KÝ CÔNG CỤ NỢ CÔNG THÀNH CÔNG (LUẬT 20/2017/QH14)[/]\n\n"
            f"  Mã hệ thống (ID):        [bold yellow]{res['instrument_id']}[/]\n"
            f"  Mã công cụ nợ:           [bold cyan]{res['debt_code']}[/]\n"
            f"  Phân nhóm nợ:            [bold magenta]{res['debt_category']}[/]\n"
            f"  Loại công cụ:            [bold]{res['instrument_type']}[/]\n"
            f"  Chủ nợ:                  [bold green]{res['creditor_name']}[/]\n"
            f"  Bên vay nợ:              [bold blue]{res['borrower_name']}[/]\n"
            f"  Số tiền vay gốc:         [bold yellow]{res['principal_amount']:,.2f} {res['original_currency']}[/] (~[bold yellow]{res['principal_vnd']:,.0f} VND[/])\n"
            f"  Lãi suất / Kỳ hạn:       [bold]{res['interest_rate_pct']:.2f}%/năm[/] ([bold]{res['tenor_years']} năm[/])\n"
            f"  Ngày ký / Ngày đáo hạn:  [bold]{res['issuance_date']}[/] -> [bold red]{res['maturity_date']}[/]\n"
            f"  Trạng thái hiệu lực:     [bold green]{res['status']}[/]",
            title="[bold blue]Public Debt Borrowing Instrument Registered[/]",
            border_style="green",
        )
    )


@publicdebt_app.command("schedule")
def schedule_cmd(
    debt_code: str = typer.Option(..., "--code", "-c", help="Mã công cụ nợ"),
    period: str = typer.Option("2026-K1", "--period", "-p", help="Kỳ trả nợ (VD: 2026-K1, 2026-Q2)"),
    due_date: str = typer.Option(..., "--due-date", help="Hạn thanh toán nghĩa vụ trả nợ (YYYY-MM-DD)"),
    principal: float = typer.Option(..., "--principal", help="Tiền gốc phải trả (VND)"),
    interest: float = typer.Option(..., "--interest", help="Tiền lãi phải trả (VND)"),
    fees: float = typer.Option(0.0, "--fees", help="Phí cam kết / phí quản lý / phí bảo lãnh (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Lập lịch trình trả nợ gốc, lãi và phí quản lý nợ công (Điều 54)."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    try:
        res = engine.schedule_debt_service(
            debt_code=debt_code,
            payment_period=period,
            due_date_str=due_date,
            principal_due_vnd=principal,
            interest_due_vnd=interest,
            fees_due_vnd=fees,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi lập lịch trình trả nợ công:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]LẬP LỊCH TRÌNH NGHĨA VỤ TRẢ NỢ CÔNG (ĐIỀU 54 LUẬT 20/2017/QH14)[/]\n\n"
            f"  Mã lịch trình (ID):      [bold yellow]{res['schedule_id']}[/]\n"
            f"  Mã công cụ nợ:           [bold cyan]{res['debt_code']}[/] ({res['borrower_name']})\n"
            f"  Kỳ trả nợ / Hạn trả:     [bold]{res['payment_period']}[/] (Đáo hạn: [bold red]{res['due_date']}[/])\n"
            f"  Gốc phải trả:            [bold]{res['principal_due_vnd']:,.0f} VND[/]\n"
            f"  Lãi phải trả:            [bold]{res['interest_due_vnd']:,.0f} VND[/]\n"
            f"  Phí liên quan:           [bold]{res['fees_due_vnd']:,.0f} VND[/]\n"
            f"  Tổng nghĩa vụ trả nợ:    [bold yellow]{res['total_due_vnd']:,.0f} VND[/]\n"
            f"  Trạng thái:              [bold yellow]{res['status']}[/]",
            title="[bold blue]Debt Service Installment Scheduled[/]",
            border_style="cyan",
        )
    )


@publicdebt_app.command("repay")
def repay_cmd(
    schedule_id: str = typer.Argument(..., help="Mã lịch trình trả nợ (Schedule ID)"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền thực tế thanh toán trả nợ (VND)"),
    date_str: Optional[str] = typer.Option(None, "--date", help="Ngày thanh toán (YYYY-MM-DD, mặc định: hôm nay)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thực hiện trích quỹ tích lũy trả nợ hoặc NSNN để thanh toán nghĩa vụ nợ công (Điều 55-57)."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    try:
        res = engine.execute_debt_repayment(
            schedule_id=schedule_id,
            paid_amount_vnd=amount,
            payment_date_str=date_str,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi thanh toán trả nợ công:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_color = "green" if res["status"] == "PAID" else "yellow"
    console.print(
        Panel(
            f"[bold green]XÁC NHẬN THANH TOÁN TRẢ NỢ CÔNG THÀNH CÔNG[/]\n\n"
            f"  Mã lịch trình:           [bold yellow]{res['schedule_id']}[/]\n"
            f"  Mã công cụ nợ:           [bold cyan]{res['debt_code']}[/]\n"
            f"  Tổng nghĩa vụ phải trả:  [bold]{res['total_due_vnd']:,.0f} VND[/]\n"
            f"  Đã thanh toán lũy kế:    [bold green]{res['cumulative_paid_vnd']:,.0f} VND[/]\n"
            f"  Nghĩa vụ còn lại:        [bold red]{res['remaining_due_vnd']:,.0f} VND[/]\n"
            f"  Trạng thái thanh toán:   [bold {status_color}]{res['status']}[/]\n"
            f"  Ngày thanh toán:         [dim]{res['paid_at']}[/]",
            title="[bold blue]Public Debt Service Repayment Executed[/]",
            border_style=status_color,
        )
    )


@publicdebt_app.command("onlend")
def onlend_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã hợp đồng cho vay lại ODA (VD: CVL-2026-HCM-01)"),
    parent_debt: str = typer.Option(..., "--parent-debt", help="Mã hiệp định vay ODA gốc của Chính phủ"),
    borrower: str = typer.Option(..., "--borrower", "-b", help="Cơ quan/doanh nghiệp vay lại (UBND tỉnh/thành phố hoặc DNNN)"),
    project: str = typer.Option(..., "--project", help="Tên dự án sử dụng vốn vay lại"),
    amount: float = typer.Option(..., "--amount", "-a", help="Hạn mức vốn ODA cho vay lại (VND)"),
    fee: float = typer.Option(0.25, "--fee", help="Phí cho vay lại (%/năm theo Nghị định 97/2018/NĐ-CP)"),
    risk: str = typer.Option("LOW", "--risk", help="Hạng rủi ro tín dụng đơn vị vay lại (LOW, MEDIUM, HIGH)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ký kết hợp đồng cho vay lại vốn vay ODA và vay ưu đãi nước ngoài (Nghị định 97/2018/NĐ-CP)."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    try:
        res = engine.register_onlending_agreement(
            onlending_code=code,
            parent_debt_code=parent_debt,
            sub_borrower_name=borrower,
            project_name=project,
            allocated_amount_vnd=amount,
            onlending_fee_pct=fee,
            credit_risk_tier=risk,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi đăng ký hợp đồng cho vay lại ODA:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]KÝ KẾT HỢP ĐỒNG CHO VAY LẠI VỐN VAY ODA THÀNH CÔNG (NGHỊ ĐỊNH 97/2018/NĐ-CP)[/]\n\n"
            f"  Mã hợp đồng:             [bold yellow]{res['onlending_code']}[/]\n"
            f"  Hiệp định ODA gốc:       [bold cyan]{res['parent_debt_code']}[/]\n"
            f"  Đơn vị vay lại:          [bold]{res['sub_borrower_name']}[/]\n"
            f"  Dự án đầu tư:            [bold]{res['project_name']}[/]\n"
            f"  Hạn mức vốn cho vay lại: [bold yellow]{res['allocated_amount_vnd']:,.0f} VND[/]\n"
            f"  Phí cho vay lại:         [bold]{res['onlending_fee_pct']:.2f}%/năm[/]\n"
            f"  Phân loại rủi ro:        [bold magenta]{res['credit_risk_tier']}[/]\n"
            f"  Ngày ký thỏa thuận:      [dim]{res['signed_date']}[/]",
            title="[bold blue]ODA On-Lending Agreement Established[/]",
            border_style="green",
        )
    )


@publicdebt_app.command("safety")
def safety_cmd(
    year: int = typer.Option(2026, "--year", "-y", help="Năm tài khóa đánh giá chỉ tiêu an toàn"),
    gdp: float = typer.Option(..., "--gdp", help="Quy mô GDP danh nghĩa quốc gia (VND)"),
    revenue: float = typer.Option(..., "--revenue", help="Tổng dự toán thu ngân sách nhà nước (VND)"),
    ext_debt: Optional[float] = typer.Option(None, "--ext-debt", help="Tổng nợ nước ngoài của quốc gia (VND, mặc định: tự động tính)"),
    debt_service: Optional[float] = typer.Option(None, "--debt-service", help="Nghĩa vụ trả nợ trực tiếp của Chính phủ (VND, mặc định: tự động tính)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá chỉ tiêu an toàn nợ công và giới hạn đỏ theo Nghị quyết Quốc hội (Điều 19)."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    try:
        res = engine.assess_sovereign_debt_safety(
            fiscal_year=year,
            gdp_vnd=gdp,
            budget_revenue_vnd=revenue,
            national_external_debt_vnd=ext_debt,
            annual_direct_debt_service_vnd=debt_service,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi đánh giá an toàn nợ công:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    sev_color = "red" if res["is_ceiling_breached"] else ("yellow" if res["risk_level"] == "CAUTION" else "green")

    console.print(
        Panel(
            f"[bold {sev_color}]BÁO CÁO ĐÁNH GIÁ CHỈ TIÊU AN TOÀN NỢ CÔNG QUỐC GIA (ĐIỀU 19 LUẬT 20/2017/QH14)[/]\n\n"
            f"  Năm tài khóa:            [bold]{res['fiscal_year']}[/]\n"
            f"  Tổng nợ công quốc gia:   [bold yellow]{res['total_public_debt_vnd']:,.0f} VND[/]\n\n"
            f"  1. Nợ công / GDP:        [bold {sev_color}]{res['public_debt_gdp_pct']}%[/] (Trần Quốc hội: [bold]{res['statutory_ceilings']['MAX_PUBLIC_DEBT_GDP_PCT']}%[/])\n"
            f"  2. Nợ Chính phủ / GDP:   [bold]{res['gov_debt_gdp_pct']}%[/] (Trần Quốc hội: [bold]{res['statutory_ceilings']['MAX_GOV_DEBT_GDP_PCT']}%[/])\n"
            f"  3. Nợ nước ngoài / GDP:  [bold]{res['external_debt_gdp_pct']}%[/] (Trần Quốc hội: [bold]{res['statutory_ceilings']['MAX_EXTERNAL_DEBT_GDP_PCT']}%[/])\n"
            f"  4. Trả nợ / Thu NSNN:    [bold]{res['debt_service_revenue_pct']}%[/] (Giới hạn: [bold]{res['statutory_ceilings']['MAX_DIRECT_DEBT_SERVICE_REVENUE_PCT']}%[/])\n\n"
            f"  Tình trạng vi phạm trần: [bold {sev_color}]{'VI PHẠM TRẦN NỢ CÔNG' if res['is_ceiling_breached'] else 'AN TOÀN TRONG GIỚI HẠN'}[/]\n"
            f"  Cấp độ rủi ro:           [bold {sev_color}]{res['risk_level']}[/]\n"
            f"  Chi tiết cảnh báo:       [italic]{'; '.join(res['breaches']) if res['breaches'] else 'Các chỉ số an toàn nợ công đều nằm trong ngưỡng kiểm soát lành mạnh'}[/]",
            title="[bold blue]Sovereign Debt Sustainability & Safety Red Lines[/]",
            border_style=sev_color,
        )
    )


@publicdebt_app.command("list")
def list_cmd(
    type: str = typer.Option("all", "--type", help="Loại bản ghi (all, instruments, schedules, onlending, assessments)"),
    limit: int = typer.Option(20, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Liệt kê danh sách công cụ nợ, lịch trả nợ, hiệp định cho vay lại ODA hoặc hồ sơ an toàn nợ."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    records = engine.list_records(category=type, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "instruments" in records and records["instruments"]:
        table = Table(title="Danh Sách Công Cụ Nợ Công & Trái Phiếu Chính Phủ (Luật 20/2017/QH14)")
        table.add_column("Mã Nợ", style="cyan", no_wrap=True)
        table.add_column("Phân Nhóm", style="magenta")
        table.add_column("Loại Công Cụ", style="white")
        table.add_column("Bên Vay", style="bold")
        table.add_column("Giá Trị (VND)", style="yellow")
        table.add_column("Lãi Suất", style="green")
        table.add_column("Đáo Hạn", style="red")
        for i in records["instruments"]:
            table.add_row(
                i["debt_code"],
                i["debt_category"][:18],
                i["instrument_type"][:18],
                i["borrower_name"][:20],
                f"{i['principal_vnd']:,.0f}",
                f"{i['interest_rate_pct']:.2f}%",
                i["maturity_date"],
            )
        console.print(table)

    if "onlending" in records and records["onlending"]:
        table = Table(title="Hợp Đồng Cho Vay Lại Vốn Vay ODA (Nghị định 97/2018/NĐ-CP)")
        table.add_column("Mã Hợp Đồng", style="cyan", no_wrap=True)
        table.add_column("Hiệp Định Gốc", style="white")
        table.add_column("Bên Vay Lại", style="bold")
        table.add_column("Dự Án", style="magenta")
        table.add_column("Vốn Vay Lại (VND)", style="yellow")
        table.add_column("Phí CVL", style="green")
        for o in records["onlending"]:
            table.add_row(
                o["onlending_code"],
                o["parent_debt_code"],
                o["sub_borrower_name"][:20],
                o["project_name"][:20],
                f"{o['allocated_amount_vnd']:,.0f}",
                f"{o['onlending_fee_pct']:.2f}%",
            )
        console.print(table)


@publicdebt_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dưới dạng JSON"),
) -> None:
    """Hiển thị tổng quan tình hình nợ công, nợ Chính phủ, quỹ trả nợ và an toàn nợ quốc gia."""
    from src.core.publicdebt_engine import PublicDebtEngine

    engine = PublicDebtEngine()
    telemetry = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    sev_color = "red" if telemetry["is_ceiling_breached"] else ("yellow" if telemetry["latest_safety_risk_level"] == "CAUTION" else "green")

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ NỢ CÔNG & TÍN NHIỆM QUỐC GIA (LUẬT 20/2017/QH14)[/]\n\n"
            f"  Số lượng công cụ nợ đăng ký:    [bold yellow]{telemetry['instrument_count']}[/]\n"
            f"  Số kỳ hạn trả nợ đã lập:        [bold cyan]{telemetry['schedule_count']}[/]\n"
            f"  Hợp đồng cho vay lại ODA:       [bold green]{telemetry['onlending_count']}[/]\n"
            f"  Hồ sơ đánh giá an toàn:         [bold magenta]{telemetry['safety_assessment_count']}[/]\n\n"
            f"  Tổng dư nợ công quốc gia:       [bold yellow]{telemetry['total_public_debt_vnd']:,.0f} VND[/]\n"
            f"    - Nợ Chính phủ:               [bold]{telemetry['government_debt_vnd']:,.0f} VND[/]\n"
            f"    - Nợ được CP bảo lãnh:        [bold]{telemetry['government_guaranteed_debt_vnd']:,.0f} VND[/]\n"
            f"    - Nợ chính quyền địa phương:  [bold]{telemetry['local_government_debt_vnd']:,.0f} VND[/]\n\n"
            f"  Tổng nghĩa vụ nợ đến hạn:       [bold]{telemetry['total_debt_service_due_vnd']:,.0f} VND[/]\n"
            f"  Đã thanh toán trả nợ:           [bold green]{telemetry['total_debt_service_paid_vnd']:,.0f} VND[/] (Tỷ lệ trả nợ: [bold green]{telemetry['debt_service_repayment_ratio_pct']}%[/])\n"
            f"  Tổng vốn ODA cho vay lại:       [bold yellow]{telemetry['total_onlent_allocated_vnd']:,.0f} VND[/]\n\n"
            f"  Cấp độ an toàn nợ công:         [bold {sev_color}]{telemetry['latest_safety_risk_level']}[/]\n"
            f"  Cảnh báo vi phạm trần nợ:       [bold {sev_color}]{'VI PHẠM NGHỊ QUYẾT QUỐC HỘI' if telemetry['is_ceiling_breached'] else 'AN TOÀN TUÂN THỦ LUẬT ĐỊNH'}[/]\n"
            f"  Cơ sở dữ liệu hoạt động:        [dim]{telemetry['database_path']}[/]",
            title="[bold blue]National Public Debt Management Telemetry[/]",
            border_style=sev_color,
        )
    )
