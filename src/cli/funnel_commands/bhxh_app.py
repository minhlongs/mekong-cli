# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for Vietnam social insurance (BHXH) commands."""

from __future__ import annotations

import json

import typer

bhxh_app = typer.Typer(
    name="bhxh",
    help="Bảo hiểm xã hội VN — BHXH, BHYT, BHTN, hồ sơ D02-LT (NĐ 73/2024 & NĐ 74/2024)",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


@bhxh_app.callback(invoke_without_command=True)
def bhxh_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Hệ thống trích nộp Bảo hiểm Xã hội, BHYT, BHTN và kê khai D02-LT."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.bhxh_engine import BhxhEngine

    status_data = BhxhEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    regs = status_data["statutory_regulations"]
    console.print(
        Panel(
            f"[bold green]Hệ Thống Bảo Hiểm Xã Hội Việt Nam (BHXH - BHYT - BHTN)[/]\n\n"
            f"  Căn cứ pháp lý:          [cyan]{regs['decree']}[/]\n"
            f"  Mức lương cơ sở:         [yellow]{regs['base_salary_vnd']:,.0f} đ/tháng[/]\n"
            f"  Mức trần đóng BHXH/BHYT: [magenta]{regs['ceiling_bhxh_bhyt_vnd']:,.0f} đ/tháng[/]\n"
            f"  Tỷ lệ Người lao động:    [bold]10.5%[/] (BHXH 8%, BHYT 1.5%, BHTN 1%)\n"
            f"  Tỷ lệ Doanh nghiệp:      [bold green]21.5%[/] (BHXH 17.5%, BHYT 3%, BHTN 1%)\n"
            f"  Tổng trích nộp bắt buộc: [bold red]32.0%[/]\n"
            f"  Nhân sự đăng ký:         [cyan]{status_data['total_employees']}[/] (Hoạt động: {status_data['active_employees']})\n"
            f"  Hồ sơ kê khai D02-LT:    [bold blue]{status_data['total_declarations']}[/]\n"
            f"  Tổng quỹ trích nộp:      [yellow]{status_data['total_contributions_simulated']:,.0f} đ[/]",
            title="[bold blue]BHXH & Lao Động Doanh Nghiệp VN[/]",
            border_style="green",
        )
    )

    table = Table(title="Lịch Sử Tính Đóng BHXH Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã Tính", style="dim", width=16)
    table.add_column("Lương Gốc", justify="right", width=14)
    table.add_column("NLĐ Đóng (10.5%)", justify="right", width=16)
    table.add_column("DN Đóng (21.5%)", justify="right", width=16)
    table.add_column("Tổng Trích Nộp", justify="right", width=16)
    table.add_column("Lương Thực Lĩnh", justify="right", width=16)

    for c in status_data.get("recent_calculations", []):
        table.add_row(
            c["calc_id"],
            f"{c['salary_gross']:,.0f} đ",
            f"{c['nl_total']:,.0f} đ",
            f"{c['dn_total']:,.0f} đ",
            f"{c['total_contribution']:,.0f} đ",
            f"{c['salary_gross'] - c['nl_total']:,.0f} đ",
        )
    console.print(table)


@bhxh_app.command(name="calc")
def bhxh_calc(
    salary: float = typer.Argument(..., help="Mức tiền lương đóng bảo hiểm (Gross)"),
    region: int = typer.Option(1, "--region", "-r", help="Vùng lương tối thiểu (1, 2, 3, 4)"),
    kpcd: bool = typer.Option(False, "--kpcd", help="Bao gồm kinh phí công đoàn 2%"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính chi tiết tỷ lệ trích nộp BHXH, BHYT, BHTN cho NLĐ và Doanh nghiệp."""
    from src.core.bhxh_engine import BhxhEngine, format_vnd

    res = BhxhEngine().calculate_contribution(salary=salary, region=region, include_kpcd=kpcd)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    capped_str = " (Đã chạm mức trần 46.800.000 đ)" if res["is_capped"] else ""
    console.print(
        Panel(
            f"[bold]Mức lương tính bảo hiểm:[/] [yellow]{format_vnd(res['salary_gross'])}[/]{capped_str}\n"
            f"[bold]Vùng áp dụng:[/] Vùng {res['region']}\n"
            f"[bold]NLĐ trích nộp (10.5%):[/] [cyan]{format_vnd(res['employee']['total'])}[/]\n"
            f"[bold]DN trích nộp ({'23.5%' if kpcd else '21.5%'}):[/] [magenta]{format_vnd(res['employer']['total'])}[/]\n"
            f"[bold green]Tổng quỹ bảo hiểm nộp về CQ BHXH:[/] [bold green]{format_vnd(res['total_contribution'])}[/]\n"
            f"[bold blue]Lương thực lĩnh sau bảo hiểm:[/] [bold blue]{format_vnd(res['net_salary_estimated'])}[/]",
            title=f"[bold green]Chi Tiết Trích Nộp BHXH — {res['calc_id']}[/]",
            border_style="green",
        )
    )

    table = Table(title="Bảng Tỷ Lệ Trích Nộp Theo Quy Định", show_header=True, header_style="bold cyan")
    table.add_column("Khoản Trích Nộp", style="bold", width=22)
    table.add_column("NLĐ Đóng", justify="right", width=18)
    table.add_column("NSDLĐ Đóng", justify="right", width=18)
    table.add_column("Tổng Tỷ Lệ", justify="right", width=16)

    table.add_row("BHXH (Hưu trí / Ốm đau)", f"8.0% ({format_vnd(res['employee']['bhxh_8pct'])})", f"17.5% ({format_vnd(res['employer']['bhxh_17_5pct'])})", "25.5%")
    table.add_row("BHYT (Y tế)", f"1.5% ({format_vnd(res['employee']['bhyt_1_5pct'])})", f"3.0% ({format_vnd(res['employer']['bhyt_3pct'])})", "4.5%")
    table.add_row("BHTN (Thất nghiệp)", f"1.0% ({format_vnd(res['employee']['bhtn_1pct'])})", f"1.0% ({format_vnd(res['employer']['bhtn_1pct'])})", "2.0%")
    if kpcd:
        table.add_row("KPCĐ (Công đoàn)", "0.0%", f"2.0% ({format_vnd(res['employer']['kpcd_2pct'])})", "2.0%")
    table.add_row("[bold]TỔNG CỘNG[/]", f"[bold cyan]{format_vnd(res['employee']['total'])}[/]", f"[bold magenta]{format_vnd(res['employer']['total'])}[/]", f"[bold green]{format_vnd(res['total_contribution'])}[/]")
    console.print(table)


from src.cli.funnel_commands.bhxh_ops import (  # noqa: E402, F401
    bhxh_declaration,
    bhxh_employees,
    bhxh_status,
)
