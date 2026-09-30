"""
CLI commands for Vietnamese Tax Administration, Electronic Invoices & Tax Audits (Luật Quản lý thuế số 38/2019/QH14).
"""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
taxadmin_app = typer.Typer(
    name="taxadmin",
    help="Vietnamese Tax Administration, Electronic Invoices & Tax Audit Compliance Suite (Luật Quản lý thuế số 38/2019/QH14 & NĐ 123/2020/NĐ-CP)",
    no_args_is_help=False,
)


@taxadmin_app.callback(invoke_without_command=True)
def taxadmin_default(ctx: typer.Context) -> None:
    """Mặc định hiển thị tổng quan quản lý thuế và hóa đơn điện tử nếu không có lệnh con."""
    if ctx.invoked_subcommand is None:
        status_cmd(json_mode=False)


@taxadmin_app.command("taxpayer")
def register_taxpayer_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã số thuế (10 số hoặc 13 số)"),
    name: str = typer.Option(..., "--name", "-n", help="Tên người nộp thuế / doanh nghiệp"),
    rep: str = typer.Option(..., "--rep", "-r", help="Người đại diện theo pháp luật"),
    type: str = typer.Option("ENTERPRISE", "--type", "-t", help="Loại NNT (ENTERPRISE, INDIVIDUAL_BUSINESS, FOREIGN_CONTRACTOR, DEPENDENT_UNIT)"),
    office: str = typer.Option("Cục Thuế TP. Hà Nội", "--office", "-o", help="Cơ quan thuế quản lý trực tiếp"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký thông tin người nộp thuế vào Hệ thống Đăng ký thuế quốc gia (Điều 30-35)."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    try:
        res = engine.register_taxpayer(
            tax_code=code,
            taxpayer_name=name,
            legal_rep=rep,
            taxpayer_type=type,
            tax_office=office,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi đăng ký người nộp thuế:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐĂNG KÝ NGƯỜI NỘP THUẾ THÀNH CÔNG (LUẬT QUẢN LÝ THUẾ 2019)[/]\n\n"
            f"  Mã hệ thống (ID):       [bold yellow]{res['taxpayer_id']}[/]\n"
            f"  Mã số thuế (MST):        [bold cyan]{res['tax_code']}[/]\n"
            f"  Tên NNT:                 [bold]{res['taxpayer_name']}[/]\n"
            f"  Người đại diện PL:       [bold]{res['legal_rep']}[/]\n"
            f"  Phân loại:               [bold magenta]{res['taxpayer_type']}[/]\n"
            f"  Cơ quan thuế quản lý:    [bold blue]{res['tax_office']}[/]\n"
            f"  Trạng thái hoạt động:    [bold green]{res['status']}[/]",
            title="[bold blue]Taxpayer Registration Certificate[/]",
            border_style="green",
        )
    )


@taxadmin_app.command("assess")
def assess_tax_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã số thuế của NNT"),
    type: str = typer.Option("CIT", "--type", "-t", help="Loại thuế (CIT, VAT, PIT, FCT, EXCISE, RESOURCE_ROYALTY, ENVIRONMENTAL)"),
    period: str = typer.Option("2026-Q1", "--period", "-p", help="Kỳ tính thuế (VD: 2026-Q1, 2026-M03)"),
    declared: float = typer.Option(0.0, "--declared", "-d", help="Số thuế tự khai (VND)"),
    assessed: float = typer.Option(0.0, "--assessed", "-a", help="Số thuế cơ quan ấn định/xác định (VND)"),
    due_date: str = typer.Option(..., "--due-date", help="Hạn nộp thuế luật định (YYYY-MM-DD)"),
    paid: float = typer.Option(0.0, "--paid", help="Số tiền thuế đã nộp vào NSNN (VND)"),
    calc_date: Optional[str] = typer.Option(None, "--calc-date", help="Ngày tính tiền chậm nộp (YYYY-MM-DD, mặc định: hôm nay)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định nghĩa vụ thuế, tính tiền chậm nộp 0.03%/ngày và biện pháp cưỡng chế thuế (Điều 59 & 124-125)."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    try:
        res = engine.assess_tax_and_interest(
            tax_code=code,
            tax_type=type,
            tax_period=period,
            declared_amount_vnd=declared,
            assessed_amount_vnd=assessed,
            due_date_str=due_date,
            paid_amount_vnd=paid,
            current_date_str=calc_date,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi xác định nghĩa vụ thuế:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    enforce_style = "bold red" if res["enforcement_measure"] != "NONE" else "green"
    exit_style = "bold red" if res["exit_suspension"] else "dim"

    console.print(
        Panel(
            f"[bold cyan]THÔNG BÁO NGHĨA VỤ THUẾ & TIỀN CHẬM NỘP (ĐIỀU 59 LUẬT 38/2019/QH14)[/]\n\n"
            f"  Mã thông báo (ID):       [bold yellow]{res['assessment_id']}[/]\n"
            f"  Mã số thuế:              [bold]{res['tax_code']}[/]\n"
            f"  Sắc thuế / Kỳ thuế:      [bold magenta]{res['tax_type']}[/] ({res['tax_period']})\n"
            f"  Số thuế phải nộp:        [bold]{res['effective_tax_vnd']:,.0f} VND[/] (Đã nộp: {res['paid_amount_vnd']:,.0f} VND)\n"
            f"  Số thuế còn nợ NSNN:     [bold red]{res['outstanding_tax_vnd']:,.0f} VND[/]\n"
            f"  Hạn nộp / Số ngày trễ:   [bold]{res['due_date']}[/] ([bold red]{res['days_overdue']} ngày[/])\n"
            f"  Tiền chậm nộp (0.03%/d): [bold red]{res['late_payment_interest_vnd']:,.0f} VND[/]\n"
            f"  Tổng số tiền phải nộp:   [bold yellow]{res['total_payable_vnd']:,.0f} VND[/]\n"
            f"  Biện pháp cưỡng chế:     [{enforce_style}]{res['enforcement_measure']}[/]\n"
            f"  Tạm hoãn xuất cảnh:      [{exit_style}]{'ÁP DỤNG (ĐIỀU 66)' if res['exit_suspension'] else 'KHÔNG'}[/]",
            title="[bold blue]Tax Assessment & Enforcement Statement[/]",
            border_style="yellow" if res["outstanding_tax_vnd"] > 0 else "green",
        )
    )


@taxadmin_app.command("invoice")
def issue_invoice_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Ký hiệu hóa đơn (VD: 1C26TAA-0000001)"),
    type: str = typer.Option("VAT_INVOICE", "--type", "-t", help="Loại hóa đơn (VAT_INVOICE, SALES_INVOICE, CASH_REGISTER_INVOICE)"),
    seller: str = typer.Option(..., "--seller", "-s", help="Mã số thuế người bán"),
    buyer_tax: str = typer.Option("0100109106", "--buyer-tax", help="Mã số thuế người mua"),
    buyer_name: str = typer.Option(..., "--buyer-name", help="Tên đơn vị người mua"),
    amount: float = typer.Option(..., "--amount", "-a", help="Tổng tiền hàng chưa thuế (VND)"),
    vat_rate: float = typer.Option(10.0, "--vat-rate", help="Thuế suất GTGT (0.0, 5.0, 8.0, 10.0)"),
    cqt_code: bool = typer.Option(True, "--cqt-code/--no-cqt-code", help="Cấp mã xác thực của cơ quan thuế"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Phát hành Hóa đơn điện tử có mã hoặc không có mã của cơ quan thuế (Nghị định 123/2020/NĐ-CP)."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    try:
        res = engine.issue_electronic_invoice(
            invoice_code=code,
            invoice_type=type,
            seller_tax_code=seller,
            buyer_tax_code=buyer_tax,
            buyer_name=buyer_name,
            subtotal_vnd=amount,
            vat_rate_pct=vat_rate,
            with_tax_authority_code=cqt_code,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi phát hành hóa đơn điện tử:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]PHÁT HÀNH HÓA ĐƠN ĐIỆN TỬ THÀNH CÔNG (NGHỊ ĐỊNH 123/2020/NĐ-CP)[/]\n\n"
            f"  Ký hiệu hóa đơn:         [bold yellow]{res['invoice_code']}[/]\n"
            f"  Loại hóa đơn:            [bold cyan]{res['invoice_type']}[/]\n"
            f"  Mã CQT cấp:              [bold green]{res['tax_authority_code'] or 'KHÔNG MÃ (ĐIỀU 91)'}[/]\n"
            f"  Người bán (MST):         [bold]{res['seller_name']}[/] ({res['seller_tax_code']})\n"
            f"  Người mua (MST):         [bold]{res['buyer_name']}[/] ({res['buyer_tax_code']})\n"
            f"  Tiền hàng chưa thuế:     [bold]{res['subtotal_vnd']:,.0f} VND[/]\n"
            f"  Thuế GTGT ({res['vat_rate_pct']:.0f}%):       [bold magenta]{res['vat_amount_vnd']:,.0f} VND[/]\n"
            f"  Tổng tiền thanh toán:    [bold yellow]{res['total_amount_vnd']:,.0f} VND[/]\n"
            f"  Trạng thái phát hành:    [bold green]{res['issue_status']}[/]",
            title="[bold blue]Electronic Invoice Authenticated[/]",
            border_style="green",
        )
    )


@taxadmin_app.command("adjust")
def adjust_invoice_cmd(
    orig_code: str = typer.Argument(..., help="Ký hiệu hóa đơn gốc có sai sót"),
    action: str = typer.Option(..., "--action", "-a", help="Hành động xử lý (ADJUST, REPLACE, CANCEL_FORM_04)"),
    new_code: Optional[str] = typer.Option(None, "--new-code", help="Ký hiệu hóa đơn mới (bắt buộc với ADJUST/REPLACE)"),
    diff: float = typer.Option(0.0, "--diff", help="Số tiền điều chỉnh tăng/giảm trước thuế (VND)"),
    reason: str = typer.Option("Sai sót thông tin hóa đơn", "--reason", help="Lý do điều chỉnh/thay thế/hủy theo Mẫu 04/SS-HĐĐT"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xử lý hóa đơn điện tử có sai sót theo Điều 19 Nghị định số 123/2020/NĐ-CP."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    try:
        res = engine.adjust_electronic_invoice(
            original_invoice_code=orig_code,
            action=action,
            new_invoice_code=new_code,
            adjusted_diff_vnd=diff,
            explanation=reason,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi xử lý hóa đơn sai sót:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold yellow]XỬ LÝ HÓA ĐƠN ĐIỆN TỬ CÓ SAI SÓT (ĐIỀU 19 NGHỊ ĐỊNH 123/2020/NĐ-CP)[/]\n\n"
            f"  Hành vi xử lý:           [bold cyan]{res['action']}[/]\n"
            f"  Hóa đơn gốc:             [bold]{res['original_invoice_code']}[/]\n"
            f"  Hóa đơn mới / Mẫu 04:    [bold green]{res.get('new_invoice_code') or res.get('form_04_notice')}[/]\n"
            f"  Trạng thái cập nhật:     [bold yellow]{res['status']}[/]\n"
            f"  Lý do / Căn cứ:          [bold]{res['explanation']}[/]\n"
            f"  Thời điểm xử lý:         [dim]{res['processed_at']}[/]",
            title="[bold blue]E-Invoice Correction & Reconciliation[/]",
            border_style="yellow",
        )
    )


@taxadmin_app.command("audit")
def record_audit_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã số thuế của doanh nghiệp được thanh tra"),
    type: str = typer.Option("FIELD_EXAMINATION", "--type", "-t", help="Loại kiểm tra/thanh tra (DESK_EXAMINATION, FIELD_EXAMINATION, COMPREHENSIVE_INSPECTION, TRANSFER_PRICING_INSPECTION)"),
    office: str = typer.Option("Cục Thuế TP. Hà Nội", "--office", "-o", help="Cơ quan thuế tiến hành thanh tra"),
    decision: str = typer.Option(..., "--decision", "-d", help="Số quyết định thanh tra / kiểm tra"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm tài chính được thanh tra"),
    underdeclared: float = typer.Option(..., "--underdeclared", "-u", help="Số tiền thuế khai thiếu / trốn thuế (VND)"),
    evasion: bool = typer.Option(False, "--evasion/--no-evasion", help="Xác định là hành vi trốn thuế (phạt 1x - 3x theo Điều 17 NĐ 125)"),
    multiplier: float = typer.Option(1.0, "--multiplier", "-m", help="Hệ số phạt trốn thuế (1.0 đến 3.0)"),
    days: int = typer.Option(30, "--days", help="Số ngày chậm nộp tính lãi"),
    reason: str = typer.Option("Khai sai dẫn đến thiếu số thuế phải nộp", "--reason", help="Nội dung kết luận sai phạm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ghi nhận kết luận kiểm tra, thanh tra thuế và xử phạt vi phạm hành chính (Nghị định 125/2020/NĐ-CP)."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    try:
        res = engine.record_tax_audit(
            tax_code=code,
            audit_type=type,
            tax_office=office,
            decision_number=decision,
            audit_year=year,
            underdeclared_tax_vnd=underdeclared,
            is_tax_evasion=evasion,
            evasion_penalty_multiplier=multiplier,
            late_payment_days=days,
            violation_description=reason,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi ghi nhận kết luận thanh tra thuế:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    sev_color = "red" if res["is_tax_evasion"] else "yellow"
    console.print(
        Panel(
            f"[bold {sev_color}]KẾT LUẬN THANH TRA / KIỂM TRA THUẾ (NGHỊ ĐỊNH 125/2020/NĐ-CP)[/]\n\n"
            f"  Mã hồ sơ kết luận (ID):   [bold yellow]{res['audit_id']}[/]\n"
            f"  Doanh nghiệp (MST):       [bold]{res['taxpayer_name']}[/] ({res['tax_code']})\n"
            f"  Quyết định số:            [bold]{res['decision_number']}[/] (Năm: [bold]{res['audit_year']}[/])\n"
            f"  Hình thức thanh tra:      [bold magenta]{res['audit_type']}[/]\n"
            f"  Thuế truy thu:            [bold red]{res['underdeclared_tax_vnd']:,.0f} VND[/]\n"
            f"  Tiền phạt vi phạm:        [bold red]{res['penalty_amount_vnd']:,.0f} VND[/] (Tỷ lệ: [bold {sev_color}]{res['penalty_rate']}[/])\n"
            f"  Tiền chậm nộp (0.03%/d):  [bold red]{res['late_payment_fee_vnd']:,.0f} VND[/]\n"
            f"  Tổng truy thu và xử phạt: [bold yellow]{res['total_recovery_vnd']:,.0f} VND[/]\n"
            f"  Hành vi sai phạm:         [bold]{res['violation_description']}[/]\n"
            f"  Cơ quan ban hành:         [bold green]{res['tax_office']}[/]",
            title="[bold blue]Tax Audit Conclusion & Sanction Order[/]",
            border_style=sev_color,
        )
    )


@taxadmin_app.command("list")
def list_cmd(
    type: str = typer.Option("all", "--type", help="Loại bản ghi (all, taxpayers, assessments, invoices, audits)"),
    limit: int = typer.Option(20, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Liệt kê danh sách người nộp thuế, nghĩa vụ thuế, hóa đơn điện tử hoặc kết luận thanh tra."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    records = engine.list_records(category=type, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "taxpayers" in records and records["taxpayers"]:
        table = Table(title="Danh Sách Người Nộp Thuế Đăng Ký (Luật 38/2019/QH14)")
        table.add_column("MST", style="cyan", no_wrap=True)
        table.add_column("Tên NNT", style="bold")
        table.add_column("Người Đại Diện", style="white")
        table.add_column("Loại NNT", style="magenta")
        table.add_column("Cơ Quan Thuế", style="green")
        table.add_column("Trạng Thái", style="yellow")
        for t in records["taxpayers"]:
            table.add_row(
                t["tax_code"],
                t["taxpayer_name"][:30],
                t["legal_rep"][:20],
                t["taxpayer_type"],
                t["tax_office"][:25],
                t["status"],
            )
        console.print(table)

    if "invoices" in records and records["invoices"]:
        table = Table(title="Hóa Đơn Điện Tử Đã Phát Hành (Nghị định 123/2020/NĐ-CP)")
        table.add_column("Ký Hiệu", style="cyan", no_wrap=True)
        table.add_column("Loại HĐ", style="magenta")
        table.add_column("Người Bán", style="white")
        table.add_column("Người Mua", style="green")
        table.add_column("Tổng Tiền", style="yellow")
        table.add_column("Trạng Thái", style="bold")
        for inv in records["invoices"]:
            table.add_row(
                inv["invoice_code"],
                inv["invoice_type"][:15],
                inv["seller_name"][:20],
                inv["buyer_name"][:20],
                f"{inv['total_amount_vnd']:,.0f} VND",
                inv["issue_status"],
            )
        console.print(table)


@taxadmin_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dưới dạng JSON"),
) -> None:
    """Hiển thị tổng quan tình hình thu nộp ngân sách, phát hành hóa đơn điện tử và cưỡng chế thuế."""
    from src.core.taxadmin_engine import TaxAdminEngine

    engine = TaxAdminEngine()
    telemetry = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ THUẾ & HÓA ĐƠN ĐIỆN TỬ QUỐC GIA (LUẬT 38/2019/QH14)[/]\n\n"
            f"  Số lượng NNT đăng ký:         [bold yellow]{telemetry['taxpayer_count']}[/]\n"
            f"  Số thông báo thuế phát hành:   [bold cyan]{telemetry['assessment_count']}[/]\n"
            f"  Số hóa đơn điện tử đã cấp mã:  [bold green]{telemetry['invoice_count']}[/]\n"
            f"  Số hồ sơ thanh tra kết luận:   [bold magenta]{telemetry['audit_count']}[/]\n\n"
            f"  Tổng số thuế ấn định/tự khai:  [bold]{telemetry['total_assessed_vnd']:,.0f} VND[/]\n"
            f"  Tổng số thuế đã nộp vào NSNN:  [bold green]{telemetry['total_paid_vnd']:,.0f} VND[/] (Tỷ lệ thu: [bold green]{telemetry['collection_rate_pct']}%[/])\n"
            f"  Tiền chậm nộp phát sinh:       [bold red]{telemetry['total_late_payment_interest_vnd']:,.0f} VND[/]\n"
            f"  Doanh thu ghi nhận qua HĐĐT:   [bold]{telemetry['total_invoice_revenue_vnd']:,.0f} VND[/] (Thuế GTGT: [bold]{telemetry['total_vat_collected_vnd']:,.0f} VND[/])\n"
            f"  Tổng truy thu qua thanh tra:   [bold yellow]{telemetry['total_audit_recovery_vnd']:,.0f} VND[/] (Tiền phạt: [bold red]{telemetry['total_penalties_vnd']:,.0f} VND[/])\n\n"
            f"  Hồ sơ đang cưỡng chế thuế:     [bold red]{telemetry['enforcing_count']}[/]\n"
            f"  Số NNT bị tạm hoãn xuất cảnh:  [bold red]{telemetry['exit_suspended_count']}[/] (Điều 66)\n"
            f"  Cơ sở dữ liệu hoạt động:       [dim]{telemetry['database_path']}[/]",
            title="[bold blue]National Tax Administration Telemetry[/]",
            border_style="green",
        )
    )
