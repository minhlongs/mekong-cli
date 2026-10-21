# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BHXH employee roster, D02-LT declarations, and status commands."""

from __future__ import annotations

import json

import typer

from src.cli.funnel_commands.bhxh_app import bhxh_app


@bhxh_app.command(name="employees")
def bhxh_employees(
    status: str = typer.Option("all", "--status", "-s", help="Lọc theo trạng thái (active, all)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem danh sách nhân sự tham gia đóng BHXH trong doanh nghiệp."""
    from src.core.bhxh_engine import BhxhEngine, format_vnd

    emps = BhxhEngine().list_employees(status=status)
    if json_mode:
        typer.echo(json.dumps({"total": len(emps), "employees": emps}, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Danh Sách Nhân Sự Tham Gia BHXH", show_header=True, header_style="bold magenta")
    table.add_column("Mã NV", style="dim", width=12)
    table.add_column("Họ Và Tên", style="bold cyan", width=22)
    table.add_column("Mã Số BHXH", style="dim", width=14)
    table.add_column("Lương Đóng BHXH", justify="right", width=18)
    table.add_column("Vùng", justify="center", width=8)
    table.add_column("Phòng Ban", width=16)
    table.add_column("Trạng Thái", justify="center", width=12)

    for e in emps:
        table.add_row(
            e["employee_id"],
            e["full_name"],
            e["bhxh_code"],
            format_vnd(e["salary_insurance"]),
            str(e["region"]),
            e["department"],
            f"[green]{e['status']}[/]" if e["status"] == "active" else e["status"],
        )
    Console().print(table)


@bhxh_app.command(name="declaration")
def bhxh_declaration(
    change_type: str = typer.Argument(..., help="Loại biến động: bao_tang | bao_giam | dieu_chinh_luong"),
    employee_id: str = typer.Argument(..., help="Mã nhân viên (e.g. EMP-001)"),
    month: str = typer.Option("", "--month", "-m", help="Tháng hiệu lực (MM/YYYY)"),
    new_salary: float = typer.Option(0.0, "--new-salary", help="Mức lương mới nếu điều chỉnh"),
    note: str = typer.Option("", "--note", help="Ghi chú hồ sơ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Lập hồ sơ điện tử Mẫu D02-LT (Báo tăng / Báo giảm / Điều chỉnh lương đóng BHXH)."""
    from src.core.bhxh_engine import BhxhEngine

    res = BhxhEngine().create_declaration_d02lt(
        change_type=change_type,
        employee_id=employee_id,
        effective_month=month,
        new_salary=new_salary,
        note=note,
    )
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    Console().print(
        Panel(
            f"[bold green]Hồ Sơ Điện Tử Mẫu D02-LT Đã Khởi Tạo[/]\n\n"
            f"  Mã hồ sơ:       [bold]{res['declaration_id']}[/]\n"
            f"  Quy chuẩn:      {res['standard']}\n"
            f"  Nghiệp vụ:      [cyan]{res['change_type']}[/]\n"
            f"  Mã nhân viên:   [yellow]{res['employee_id']}[/] ({res['full_name']})\n"
            f"  Kỳ hiệu lực:    [magenta]{res['effective_month']}[/]\n"
            f"  Lương cũ:       {res['old_salary']:,.0f} đ\n"
            f"  Lương mới:      [bold green]{res['new_salary']:,.0f} đ[/]\n"
            f"  Trạng thái:     [bold blue]{res['status']}[/]\n"
            f"  Ghi chú:        {res['note']}",
            title="[bold blue]Hồ Sơ Kê Khai BHXH D02-LT[/]",
            border_style="green",
        )
    )


@bhxh_app.command(name="status")
def bhxh_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Kiểm tra trạng thái tuân thủ BHXH và các mốc quy định pháp lý."""
    from src.core.bhxh_engine import BhxhEngine

    status_data = BhxhEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    regs = status_data["statutory_regulations"]
    Console().print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG BHXH VIỆT NAM[/]\n\n"
            f"Trạng thái:             [bold green]{status_data['status'].upper()}[/]\n"
            f"Nghị định áp dụng:      [cyan]{regs['decree']}[/]\n"
            f"Mức lương cơ sở:        [yellow]{regs['base_salary_vnd']:,.0f} đ[/]\n"
            f"Trần đóng BHXH/BHYT:    [magenta]{regs['ceiling_bhxh_bhyt_vnd']:,.0f} đ[/]\n"
            f"Tổng nhân sự:           [bold]{status_data['total_employees']}[/] (Hoạt động: {status_data['active_employees']})\n"
            f"Số lượt tính đóng:      [cyan]{status_data['total_calculations']}[/]\n"
            f"Hồ sơ D02-LT đã lập:    [bold blue]{status_data['total_declarations']}[/]\n"
            f"Tổng quỹ bảo hiểm:      [bold green]{status_data['total_contributions_simulated']:,.0f} đ[/]",
            title="[bold blue]BHXH Telemetry[/]",
            border_style="green",
        )
    )
