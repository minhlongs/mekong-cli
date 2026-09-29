# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Statutory Payroll & Compensation (Phase 46)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
payroll_app = typer.Typer(
    name="payroll",
    help="Vietnamese Statutory Payroll, Gross-to-Net & Compensation Suite",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@payroll_app.callback(invoke_without_command=True)
def payroll_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan tiền lương dạng JSON"),
) -> None:
    """Vietnamese Statutory Payroll & Compensation Suite."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    rates = status_data["statutory_rates"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ TIỀN LƯƠNG & BẢO HIỂM BẮT BUỘC (VIỆT NAM)[/]\n\n"
            f"  Quy chuẩn:             {status_data['regulatory_framework']}\n"
            f"  Lương cơ sở hiện hành: [bold cyan]{_format_vnd(rates['luong_co_so'])}[/] (NĐ 73/2024)\n"
            f"  Trần đóng BHXH/BHYT:   [bold cyan]{_format_vnd(rates['ceiling_bhxh_bhyt'])}[/]\n"
            f"  Tỷ lệ trích nộp:       NLĐ [bold yellow]{rates['employee_insurance_rate']}[/] | NSDLĐ [bold magenta]{rates['employer_insurance_rate']}[/]\n"
            f"  Giảm trừ gia cảnh:     Bản thân [bold]{_format_vnd(rates['self_relief'])}[/] | Phụ thuộc [bold]{_format_vnd(rates['dependent_relief'])}/người[/]\n\n"
            f"  Tổng phiếu lương phát hành: [bold]{metrics['total_payslips_issued']}[/]\n"
            f"  Tổng quỹ lương Gross:       [bold green]{_format_vnd(metrics['total_gross_disbursed'])}[/]\n"
            f"  Tổng thực chi Net:          [bold cyan]{_format_vnd(metrics['total_net_paid'])}[/]\n"
            f"  Tổng thuế TNCN đã khấu trừ: [bold yellow]{_format_vnd(metrics['total_pit_tax_withheld'])}[/]\n"
            f"  Tổng chi phí công ty:       [bold magenta]{_format_vnd(metrics['total_employer_cost'])}[/]",
            title="[bold blue]Statutory Payroll & Compensation Dashboard[/]",
            border_style="green",
        )
    )

    payslips = engine.list_payslips(limit=5)
    if payslips:
        table = Table(title="Phiếu Lương Đã Phát Hành Gần Đây", show_header=True, header_style="bold magenta")
        table.add_column("Mã Phiếu", style="dim", width=18)
        table.add_column("Nhân Viên", style="bold cyan")
        table.add_column("Kỳ Lương", justify="center")
        table.add_column("Lương Gross", justify="right")
        table.add_column("BH NLĐ", justify="right", style="yellow")
        table.add_column("Thuế TNCN", justify="right", style="red")
        table.add_column("Thực Nhận (Net)", justify="right", style="bold green")

        for p in payslips:
            table.add_row(
                p["payslip_id"],
                p["employee_name"],
                p["month"],
                _format_vnd(p["gross_vnd"]),
                _format_vnd(p["emp_total_insurance"]),
                _format_vnd(p["pit_tax"]),
                _format_vnd(p["net_take_home"]),
            )
        console.print(table)


@payroll_app.command("gross-to-net")
def gross_to_net(
    gross: float = typer.Argument(..., help="Mức lương Gross (VND)"),
    dependents: int = typer.Option(0, "--dependents", "-d", help="Số người phụ thuộc"),
    region: int = typer.Option(1, "--region", "-r", help="Vùng áp dụng lương tối thiểu (1, 2, 3, 4)"),
    lunch: float = typer.Option(730_000, "--lunch", "-l", help="Phụ cấp ăn trưa (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi tiết từ lương Gross sang Net, bảo hiểm và thuế TNCN."""
    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine()
    result = engine.calculate_gross_to_net(
        gross=gross,
        dependents=dependents,
        region=region,
        lunch_allowance=lunch,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    emp = result["employee_deductions"]
    tax = result["tax_calculation"]
    comp = result["employer_burden"]

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ TÍNH LƯƠNG GROSS → NET (VÙNG {region})[/]\n\n"
            f"  [bold]Lương Gross hợp đồng:[/]      [bold green]{_format_vnd(result['gross'])}[/]\n"
            f"  Phụ cấp ăn trưa miễn thuế:    {_format_vnd(result['exempt_lunch_allowance'])}\n\n"
            f"[bold yellow]1. Bảo hiểm bắt buộc NLĐ đóng (10.5%):[/]\n"
            f"  - BHXH (8.0%):                {_format_vnd(emp['bhxh_8_pct'])}\n"
            f"  - BHYT (1.5%):                {_format_vnd(emp['bhyt_1_5_pct'])}\n"
            f"  - BHTN (1.0%):                {_format_vnd(emp['bhtn_1_pct'])}\n"
            f"  [bold yellow]→ Tổng bảo hiểm NLĐ:[/]         [bold yellow]{_format_vnd(emp['total_insurance'])}[/]\n\n"
            f"[bold blue]2. Thuế thu nhập cá nhân (TNCN):[/]\n"
            f"  - Thu nhập trước thuế:        {_format_vnd(tax['income_before_tax'])}\n"
            f"  - Giảm trừ bản thân:          {_format_vnd(tax['self_relief'])}\n"
            f"  - Giảm trừ người phụ thuộc:   {_format_vnd(tax['dependent_relief'])} ({dependents} người)\n"
            f"  - Thu nhập tính thuế:         {_format_vnd(tax['taxable_income'])}\n"
            f"  [bold red]→ Thuế TNCN phải nộp:[/]        [bold red]{_format_vnd(tax['pit_tax'])}[/]\n\n"
            f"[bold green]3. LƯƠNG THỰC NHẬN (NET):[/]      [bold green underline]{_format_vnd(result['net'])}[/]\n\n"
            f"[bold magenta]4. Chi phí Người sử dụng LĐ chịu (23.5%):[/]\n"
            f"  - BHXH NSDLĐ (17.5%):         {_format_vnd(comp['bhxh_17_5_pct'])}\n"
            f"  - BHYT NSDLĐ (3.0%):          {_format_vnd(comp['bhyt_3_pct'])}\n"
            f"  - BHTN NSDLĐ (1.0%):          {_format_vnd(comp['bhtn_1_pct'])}\n"
            f"  - Kinh phí công đoàn (2.0%):  {_format_vnd(comp['kpcd_2_pct'])}\n"
            f"  [bold magenta]→ Tổng chi phí doanh nghiệp:[/] [bold magenta]{_format_vnd(comp['total_cost_to_company'])}[/]",
            title="[bold green]Bảng Chi Tiết Tiền Lương[/]",
            border_style="cyan",
        )
    )


@payroll_app.command("net-to-gross")
def net_to_gross(
    net: float = typer.Argument(..., help="Mức lương Net mong muốn (VND)"),
    dependents: int = typer.Option(0, "--dependents", "-d", help="Số người phụ thuộc"),
    region: int = typer.Option(1, "--region", "-r", help="Vùng áp dụng lương tối thiểu (1, 2, 3, 4)"),
    lunch: float = typer.Option(730_000, "--lunch", "-l", help="Phụ cấp ăn trưa (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Quy đổi từ lương Net sang mức lương Gross hợp đồng tương đương."""
    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine()
    result = engine.calculate_net_to_gross(
        net=net,
        dependents=dependents,
        region=region,
        lunch_allowance=lunch,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]QUY ĐỔI NET → GROSS (VÙNG {region})[/]\n\n"
            f"  Mục tiêu Net thực nhận:       [bold green]{_format_vnd(result['target_net'])}[/]\n"
            f"  [bold yellow]Mức lương Gross cần ký:[/]      [bold yellow underline]{_format_vnd(result['solved_gross'])}[/]\n\n"
            f"  - Bảo hiểm NLĐ (10.5%):       {_format_vnd(result['employee_deductions']['total_insurance'])}\n"
            f"  - Thuế TNCN khấu trừ:         {_format_vnd(result['tax_calculation']['pit_tax'])}\n"
            f"  - Chi phí doanh nghiệp chịu:  [bold magenta]{_format_vnd(result['employer_burden']['total_cost_to_company'])}[/]",
            title="[bold blue]Net to Gross Converter[/]",
            border_style="green",
        )
    )


@payroll_app.command("payslip")
def payslip(
    employee_name: str = typer.Argument(..., help="Họ và tên nhân viên"),
    gross: float = typer.Argument(..., help="Mức lương Gross hợp đồng (VND)"),
    employee_id: str = typer.Option(None, "--id", "-i", help="Mã định danh nhân viên"),
    month: str = typer.Option(None, "--month", "-m", help="Kỳ lương (YYYY-MM)"),
    dependents: int = typer.Option(0, "--dependents", "-d", help="Số người phụ thuộc"),
    region: int = typer.Option(1, "--region", "-r", help="Vùng lương tối thiểu (1, 2, 3, 4)"),
    bonus: float = typer.Option(0.0, "--bonus", "-b", help="Thưởng / phụ cấp thêm (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Lập và lưu trữ phiếu lương điện tử cho nhân viên."""
    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine()
    result = engine.generate_payslip(
        employee_name=employee_name,
        gross=gross,
        employee_id=employee_id,
        month=month,
        dependents=dependents,
        region=region,
        bonus=bonus,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]PHIẾU LƯƠNG ĐIỆN TỬ: {result['payslip_id']}[/]\n\n"
            f"  Nhân viên:    [bold cyan]{result['employee_name']}[/] (ID: {result['employee_id']})\n"
            f"  Kỳ lương:     [bold]{result['month']}[/] (Vùng {region})\n"
            f"  Tổng Gross:   [bold green]{_format_vnd(result['gross'])}[/]\n"
            f"  Bảo hiểm NLĐ: [bold yellow]{_format_vnd(result['employee_deductions']['total_insurance'])}[/]\n"
            f"  Thuế TNCN:    [bold red]{_format_vnd(result['tax_calculation']['pit_tax'])}[/]\n"
            f"  [bold green underline]THỰC NHẬN (NET): {_format_vnd(result['net'])}[/]",
            title="[bold green]Electronic Payslip[/]",
            border_style="green",
        )
    )


@payroll_app.command("list")
def list_payslips(
    month: str = typer.Option("", "--month", "-m", help="Lọc theo kỳ lương (YYYY-MM)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách dạng JSON"),
) -> None:
    """Tra cứu danh sách phiếu lương điện tử đã lập."""
    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine()
    records = engine.list_payslips(month=month, limit=limit)

    if json_mode:
        typer.echo(json.dumps({"payslips": records, "total": len(records)}, indent=2, ensure_ascii=False))
        return

    if not records:
        console.print("[yellow]Chưa có phiếu lương nào được ghi nhận.[/]")
        return

    table = Table(title="Danh Sách Phiếu Lương Điện Tử", show_header=True, header_style="bold magenta")
    table.add_column("Mã Phiếu", style="dim", width=20)
    table.add_column("Nhân Viên", style="bold cyan")
    table.add_column("Kỳ", justify="center")
    table.add_column("Lương Gross", justify="right")
    table.add_column("BH NLĐ", justify="right", style="yellow")
    table.add_column("Thuế TNCN", justify="right", style="red")
    table.add_column("Thực Nhận (Net)", justify="right", style="bold green")

    for p in records:
        table.add_row(
            p["payslip_id"],
            p["employee_name"],
            p["month"],
            _format_vnd(p["gross_vnd"]),
            _format_vnd(p["emp_total_insurance"]),
            _format_vnd(p["pit_tax"]),
            _format_vnd(p["net_take_home"]),
        )
    console.print(table)


@payroll_app.command("status")
def payroll_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON"),
) -> None:
    """Kiểm tra thông số cấu hình và tổng hợp dữ liệu quỹ lương."""
    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG TIỀN LƯƠNG & BẢO HIỂM[/]\n\n"
            f"  Trạng thái:            {status_data['status'].upper()}\n"
            f"  Tổng phiếu lương:      {metrics['total_payslips_issued']}\n"
            f"  Tổng quỹ lương Gross:  {_format_vnd(metrics['total_gross_disbursed'])}\n"
            f"  Tổng thực chi Net:     {_format_vnd(metrics['total_net_paid'])}\n"
            f"  Tổng thuế TNCN giữ lại: {_format_vnd(metrics['total_pit_tax_withheld'])}\n"
            f"  Tổng chi phí công ty:  {_format_vnd(metrics['total_employer_cost'])}\n"
            f"  Cơ sở dữ liệu:         {status_data['database']}",
            title="[bold blue]Payroll Engine Status[/]",
            border_style="green",
        )
    )
