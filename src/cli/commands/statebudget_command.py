# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese State Budget, Fiscal Discipline & Treasury Allocations Suite (Phase 119)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

statebudget_app = typer.Typer(
    name="statebudget",
    help="Vietnamese State Budget, Fiscal Discipline & Public Treasury Allocations Suite.",
)
console = Console()


@statebudget_app.callback(invoke_without_command=True)
def statebudget_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan tình hình dự toán, cam kết chi và giải ngân ngân sách nhà nước qua Kho bạc Nhà nước."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    telemetry = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    reg = telemetry["regulatory_framework"]
    est = telemetry["budget_estimates"]
    exe = telemetry["treasury_execution"]
    dis = telemetry["fiscal_discipline"]

    rate_color = "green" if exe["execution_rate_pct"] >= 80 else ("yellow" if exe["execution_rate_pct"] >= 50 else "red")

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ DỰ TOÁN, CAM KẾT CHI & NGÂN SÁCH NHÀ NƯỚC QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:               [bold]{reg['law']}[/]\n"
            f"  Nghị định hướng dẫn thi hành:[bold yellow]{reg['decree_guideline']}[/] | Thông tư thực hiện: [bold yellow]{reg['circular_execution']}[/]\n\n"
            f"  Dự toán ngân sách được giao: [bold]{est['total_estimates']}[/] khoản dự toán\n"
            f"  - Tổng dự toán chi được duyệt: [bold yellow]{est['total_allocated_vnd']:,.0f} VND[/]\n\n"
            f"  Cam kết chi qua KBNN:        [bold cyan]{exe['total_committed_vnd']:,.0f} VND[/] ({exe['commitment_rate_pct']}% dự toán)\n"
            f"  Thực chi ngân sách (KBNN):   [bold green]{exe['total_disbursed_vnd']:,.0f} VND[/]\n"
            f"  - Tỷ lệ thực hiện dự toán:   [bold {rate_color}]{exe['execution_rate_pct']}%[/]\n\n"
            f"  Kiểm tra kỷ luật tài khóa:   [bold]{dis['total_audit_findings']}[/] vụ việc ([bold red]{dis['unresolved_critical_audits']}[/] vi phạm nghiêm trọng chưa khắc phục)\n"
            f"  - Giá trị vi phạm phát hiện: [bold red]{dis['total_violation_amount_vnd']:,.0f} VND[/]",
            title="[bold blue]Vietnam National State Budget & Public Treasury Telemetry[/]",
            border_style="blue",
        )
    )


@statebudget_app.command("estimate")
def estimate_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã số dự toán ngân sách (e.g. DT-2026-BGD-01)"),
    year: int = typer.Option(2026, "--year", help="Năm ngân sách tài chính"),
    level: str = typer.Option("CENTRAL_BUDGET", "--level", help="Cấp ngân sách (CENTRAL_BUDGET, PROVINCIAL_BUDGET, DISTRICT_BUDGET, COMMUNE_BUDGET)"),
    type: str = typer.Option("REGULAR_EXPENDITURE", "--type", help="Loại chi ngân sách (REGULAR_EXPENDITURE, DEVELOPMENT_INVESTMENT, DEBT_SERVICE_AND_INTEREST, CONTINGENCY_RESERVE, FINANCIAL_RESERVE_FUND, NATIONAL_RESERVE)"),
    sector: str = typer.Option("EDUCATION_AND_TRAINING", "--sector", help="Lĩnh vực chi (EDUCATION_AND_TRAINING, SCIENCE_AND_TECHNOLOGY, HEALTHCARE_AND_POPULATION, NATIONAL_DEFENSE, PUBLIC_SECURITY, ECONOMIC_SERVICES, ENVIRONMENT_PROTECTION, STATE_ADMINISTRATION, SOCIAL_SECURITY)"),
    unit: str = typer.Option(..., "--unit", "-u", help="Đơn vị thụ hưởng / Đơn vị sử dụng ngân sách"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền dự toán được giao (VND)"),
    approver: str = typer.Option("Quốc hội / HĐND", "--approver", help="Cơ quan quyết định giao dự toán"),
    decision: str = typer.Option("Nghị quyết giao dự toán ngân sách", "--decision", help="Số quyết định / Nghị quyết giao dự toán"),
    contingency: float = typer.Option(0.0, "--contingency", help="Tỷ lệ dự phòng ngân sách (%) (2-4% theo Điều 10)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Lập và phê duyệt dự toán ngân sách nhà nước theo Luật Ngân sách nhà nước 2015 (Điều 28-50)."""
    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    try:
        res = engine.create_estimate(
            estimate_code=code,
            fiscal_year=year,
            budget_level=level,
            expenditure_type=type,
            sector=sector,
            budget_unit=unit,
            allocated_amount_vnd=amount,
            approved_by=approver,
            decision_number=decision,
            contingency_rate_pct=contingency,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi lập dự toán ngân sách:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]PHÊ DUYỆT DỰ TOÁN NGÂN SÁCH NHÀ NƯỚC THÀNH CÔNG[/]\n\n"
            f"  Mã dự toán (ID):           [bold yellow]{res['estimate_id']}[/] ({res['estimate_code']})\n"
            f"  Năm ngân sách:             [bold]{res['fiscal_year']}[/] | Cấp ngân sách: [bold]{res['budget_level']}[/]\n"
            f"  Đơn vị sử dụng ngân sách:  [bold]{res['budget_unit']}[/]\n"
            f"  Lĩnh vực chi:              [bold]{res['sector']}[/] ({res['expenditure_type']})\n"
            f"  Số tiền giao dự toán:      [bold cyan]{res['allocated_amount_vnd']:,.0f} VND[/]\n"
            f"  Tỷ lệ dự phòng ngân sách:  [bold]{res['contingency_rate_pct']}%[/]\n"
            f"  Cơ quan quyết định giao:   [bold green]{res['approved_by']}[/] (Số: {res['decision_number']})",
            title="[bold blue]State Budget Estimate Approved (Law 83/2015/QH13)[/]",
            border_style="green",
        )
    )


@statebudget_app.command("commit")
def commit_cmd(
    estimate_id: str = typer.Argument(..., help="Mã dự toán (EST-...) hoặc mã số dự toán"),
    code: str = typer.Option(..., "--code", "-c", help="Mã số cam kết chi KBNN (e.g. CKC-2026-001)"),
    contract: str = typer.Option(..., "--contract", help="Số hợp đồng kinh tế / quyết định chỉ định thầu"),
    beneficiary: str = typer.Option(..., "--beneficiary", "-b", help="Tên nhà thầu / đơn vị thụ hưởng cam kết chi"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền đăng ký cam kết chi (VND)"),
    treasury: str = typer.Option("Kho bạc Nhà nước TP. Hà Nội", "--treasury", help="Kho bạc Nhà nước kiểm soát cam kết chi"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký cam kết chi ngân sách nhà nước qua Kho bạc Nhà nước theo Thông tư 342/2016/TT-BTC."""
    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    try:
        res = engine.register_commitment(
            estimate_id=estimate_id,
            commitment_code=code,
            contract_reference=contract,
            beneficiary_name=beneficiary,
            committed_amount_vnd=amount,
            treasury_office=treasury,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi đăng ký cam kết chi KBNN:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐĂNG KÝ CAM KẾT CHI KBNN THÀNH CÔNG[/]\n\n"
            f"  Mã cam kết chi (ID):       [bold yellow]{res['commitment_id']}[/] ({res['commitment_code']})\n"
            f"  Dự toán ngân sách liên kết:[bold]{res['estimate_id']}[/] ({res['estimate_code']})\n"
            f"  Hợp đồng kinh tế:          [bold]{res['contract_reference']}[/]\n"
            f"  Đơn vị thụ hưởng:          [bold]{res['beneficiary_name']}[/]\n"
            f"  Số tiền cam kết chi:       [bold cyan]{res['committed_amount_vnd']:,.0f} VND[/]\n"
            f"  Lũy kế cam kết chi:        [bold]{res['cumulative_committed_vnd']:,.0f} VND[/]\n"
            f"  Dự toán còn lại chưa CKC:  [bold green]{res['remaining_uncommitted_vnd']:,.0f} VND[/]\n"
            f"  Kho bạc Nhà nước xử lý:    [bold]{res['treasury_office']}[/]",
            title="[bold blue]State Treasury Spending Commitment Registered[/]",
            border_style="green",
        )
    )


@statebudget_app.command("payout")
def payout_cmd(
    estimate_id: str = typer.Argument(..., help="Mã dự toán (EST-...) hoặc mã số dự toán"),
    voucher: str = typer.Option(..., "--voucher", help="Số lệnh chi tiền / giấy rút dự toán ngân sách"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền thực xuất ngân sách (VND)"),
    category: str = typer.Option("ACTUAL_PAYOUT", "--category", help="Loại xuất chi (ACTUAL_PAYOUT, ADVANCE, ADVANCE_CLEARING)"),
    commitment_id: Optional[str] = typer.Option(None, "--commitment-id", help="Mã số cam kết chi liên kết (nếu có)"),
    treasury: str = typer.Option("Kho bạc Nhà nước TP. Hà Nội", "--treasury", help="Kho bạc Nhà nước thực hiện chi"),
    account: str = typer.Option("711-KBNN-DEFAULT", "--account", help="Tài khoản nhận tiền tại KBNN hoặc Ngân hàng thương mại"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Ghi chú nội dung chi ngân sách"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thực hiện xuất chi ngân sách qua Kho bạc Nhà nước theo Luật Ngân sách nhà nước 2015 (Điều 51-62)."""
    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    try:
        res = engine.record_payout(
            estimate_id=estimate_id,
            payment_voucher_number=voucher,
            payout_amount_vnd=amount,
            payout_category=category,
            commitment_id=commitment_id,
            treasury_office=treasury,
            recipient_account=account,
            notes=notes,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi xuất chi ngân sách nhà nước:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]XUẤT CHI NGÂN SÁCH QUA KBNN THÀNH CÔNG[/]\n\n"
            f"  Mã thanh toán (ID):        [bold yellow]{res['payout_id']}[/]\n"
            f"  Số chứng từ chi KBNN:      [bold]{res['payment_voucher_number']}[/] ({res['payout_category']})\n"
            f"  Dự toán ngân sách:         [bold]{res['estimate_id']}[/] ({res['estimate_code']})\n"
            f"  Số tiền xuất chi đợt này:  [bold cyan]{res['payout_amount_vnd']:,.0f} VND[/]\n"
            f"  Lũy kế chi năm {res['fiscal_year']}:       [bold]{res['total_disbursed_vnd']:,.0f} VND[/] / [bold]{res['allocated_amount_vnd']:,.0f} VND[/]\n"
            f"  Tỷ lệ thực hiện dự toán:   [bold green]{res['execution_rate_pct']}%[/]\n"
            f"  Dự toán còn lại:           [bold yellow]{res['remaining_estimate_vnd']:,.0f} VND[/]\n"
            f"  Kho bạc thực hiện:         [bold]{res['treasury_office']}[/] | Tài khoản: [bold]{res['recipient_account']}[/]",
            title="[bold blue]Treasury Payout Voucher Executed[/]",
            border_style="green",
        )
    )


@statebudget_app.command("audit")
def audit_cmd(
    year: int = typer.Option(2026, "--year", help="Năm ngân sách được kiểm tra"),
    unit: str = typer.Option(..., "--unit", "-u", help="Đơn vị dự toán bị thanh tra / kiểm toán"),
    violation: str = typer.Option("UNAUTHORIZED_EXPENDITURE", "--violation", help="Hành vi vi phạm (UNAUTHORIZED_EXPENDITURE, DEFICIT_CEILING_BREACH, LATE_FISCAL_SETTLEMENT, COMMISSION_KICKBACK, TREASURY_OVERDRAW)"),
    severity: str = typer.Option("HIGH", "--severity", help="Mức độ nghiêm trọng (LOW, MEDIUM, HIGH, CRITICAL)"),
    amount: float = typer.Option(0.0, "--amount", "-a", help="Giá trị sai phạm phát hiện (VND)"),
    measures: str = typer.Option(..., "--measures", "-m", help="Biện pháp xử lý, thu hồi hoặc kiến nghị kỷ luật"),
    agency: str = typer.Option("Kiểm toán Nhà nước", "--agency", help="Cơ quan tiến hành kiểm toán / thanh tra tài chính"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ghi nhận kết luận kiểm tra, kiểm toán kỷ luật tài khóa ngân sách nhà nước theo Điều 18 & 70-73."""
    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    try:
        res = engine.record_audit_finding(
            fiscal_year=year,
            target_budget_unit=unit,
            violation_type=violation,
            severity_level=severity,
            discovered_amount_vnd=amount,
            corrective_measures=measures,
            auditor_agency=agency,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi ghi nhận kết luận kiểm toán ngân sách:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    sev_color = "red" if res["severity_level"] in ("HIGH", "CRITICAL") else "yellow"
    console.print(
        Panel(
            f"[bold {sev_color}]GHI NHẬN KẾT LUẬN KIỂM TOÁN TÀI KHÓA NGÂN SÁCH[/]\n\n"
            f"  Mã hồ sơ kiểm toán (ID):   [bold yellow]{res['audit_id']}[/]\n"
            f"  Năm ngân sách kiểm tra:    [bold]{res['fiscal_year']}[/]\n"
            f"  Đơn vị sai phạm:           [bold]{res['target_budget_unit']}[/]\n"
            f"  Hành vi vi phạm:           [bold red]{res['violation_type']}[/] (Mức độ: [bold {sev_color}]{res['severity_level']}[/])\n"
            f"  Giá trị sai phạm phát hiện:[bold red]{res['discovered_amount_vnd']:,.0f} VND[/]\n"
            f"  Biện pháp khắc phục:       [bold]{res['corrective_measures']}[/]\n"
            f"  Cơ quan kiểm toán:         [bold green]{res['auditor_agency']}[/]",
            title="[bold blue]Fiscal Discipline Audit Inspection Recorded[/]",
            border_style=sev_color,
        )
    )


@statebudget_app.command("list")
def list_cmd(
    type: str = typer.Option("all", "--type", help="Loại bản ghi (all, estimates, commitments, payouts, audits)"),
    limit: int = typer.Option(20, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Liệt kê danh sách dự toán ngân sách, cam kết chi, chứng từ giải ngân và kết luận kiểm toán."""
    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    records = engine.list_records(category=type, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "estimates" in records and records["estimates"]:
        table = Table(title="Dự Toán Ngân Sách Nhà Nước Được Phê Duyệt (Luật 83/2015/QH13)")
        table.add_column("Mã Dự Toán", style="cyan")
        table.add_column("Đơn Vị Thụ Hưởng", style="bold")
        table.add_column("Cấp NS", style="white")
        table.add_column("Lĩnh Vực Chi", style="magenta")
        table.add_column("Số Tiền Giao", style="yellow")
        table.add_column("Cơ Quan Giao", style="green")
        for e in records["estimates"]:
            table.add_row(
                e["estimate_code"],
                e["budget_unit"][:30],
                e["budget_level"],
                e["sector"][:25],
                f"{e['allocated_amount_vnd']:,.0f} VND",
                e["approved_by"][:25],
            )
        console.print(table)

    if "commitments" in records and records["commitments"]:
        table = Table(title="Cam Kết Chi Qua Kho Bạc Nhà Nước (Thông tư 342/2016/TT-BTC)")
        table.add_column("Mã Cam Kết", style="cyan")
        table.add_column("Mã Dự Toán", style="white")
        table.add_column("Hợp Đồng", style="bold")
        table.add_column("Đơn Vị Thụ Hưởng", style="yellow")
        table.add_column("Số Tiền CKC", style="green")
        table.add_column("Kho Bạc", style="blue")
        for c in records["commitments"]:
            table.add_row(
                c["commitment_code"],
                c["estimate_id"],
                c["contract_reference"],
                c["beneficiary_name"][:25],
                f"{c['committed_amount_vnd']:,.0f} VND",
                c["treasury_office"][:25],
            )
        console.print(table)


@statebudget_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry, tốc độ chấp hành và kỷ luật ngân sách nhà nước toàn quốc."""
    from src.core.statebudget_engine import StateBudgetEngine

    engine = StateBudgetEngine()
    status = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(status, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]State Budget Subsystem Status:[/] {status['status']}")
    console.print(f"Tổng số khoản dự toán: {status['budget_estimates']['total_estimates']}")
    console.print(f"Tổng dự toán chi được duyệt: {status['budget_estimates']['total_allocated_vnd']:,.0f} VND")
    console.print(f"Tổng cam kết chi KBNN: {status['treasury_execution']['total_committed_vnd']:,.0f} VND ({status['treasury_execution']['commitment_rate_pct']}%)")
    console.print(f"Tổng thực chi KBNN: {status['treasury_execution']['total_disbursed_vnd']:,.0f} VND ({status['treasury_execution']['execution_rate_pct']}%)")
    console.print(f"Số vụ sai phạm kiểm toán: {status['fiscal_discipline']['total_audit_findings']} (Nghiêm trọng chưa giải quyết: {status['fiscal_discipline']['unresolved_critical_audits']})")
    console.print(f"Tổng tiền sai phạm: {status['fiscal_discipline']['total_violation_amount_vnd']:,.0f} VND")
