# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 148: Estate Share Calculation, Division Agreements & Statute of Limitations CLI commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._inheritance_estate_cmds import console, inheritance_app
from src.core.inheritance_engine import (
    InheritanceEngine,
    NotaryProcedureType,
)


@inheritance_app.command("calculate")
def calculate(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Tính toán phân chia di sản thừa kế theo luật, di chúc & suất bắt buộc Điều 644."""
    engine = InheritanceEngine()
    try:
        res = engine.calculate_statutory_shares(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(Panel.fit(
                f"[bold cyan]KẾT QUẢ TÍNH TOÁN PHÂN CHIA DI SẢN — HỒ SƠ {res['estate_id']}[/bold cyan]\n"
                f"Người để lại di sản: [bold]{res['decedent_name']}[/bold] (Mở thừa kế: {res['date_of_death']})\n"
                f"Chế độ thừa kế: [bold green]{res['succession_mode']}[/bold green]\n"
                f"Tổng tài sản: [bold]{res['gross_assets']:,.0f} VND[/bold] | Nợ đã trả: [red]{res['total_obligations_paid']:,.0f} VND[/red]\n"
                f"Di sản thờ cúng: [yellow]{res['dedicated_worship_deducted']:,.0f} VND[/yellow] | Di sản ròng phân chia: [bold yellow]{res['net_distributable_estate']:,.0f} VND[/bold yellow]\n"
                f"1 Suất thừa kế theo luật: [cyan]{res['one_statutory_share_reference']:,.0f} VND[/cyan] | 2/3 Suất Điều 644: [magenta]{res['forced_heir_2_3_share_reference']:,.0f} VND[/magenta]",
                box=box.ROUNDED,
            ))

            table = Table(title="Bảng phân bổ di sản thừa kế cho từng đồng thừa kế", box=box.SIMPLE_HEAVY)
            table.add_column("Người thừa kế", style="bold green")
            table.add_column("Quan hệ", style="cyan")
            table.add_column("Hàng thừa kế", style="white")
            table.add_column("Số tiền nhận (VND)", style="bold yellow", justify="right")
            table.add_column("Tỷ lệ (%)", style="magenta", justify="right")
            table.add_column("Căn cứ pháp lý", style="dim")

            for a in res["allocations"]:
                table.add_row(
                    a["full_name"],
                    a["relationship"],
                    a["heir_rank"],
                    f"{a['allocated_amount']:,.0f}",
                    f"{a['allocated_percentage']:.2f}%",
                    a["rule_applied"],
                )
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Lỗi khi tính toán phân chia:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("divide")
def divide(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    office: str = typer.Option(..., "--office", "-o", help="Tổ chức hành nghề công chứng thực hiện phân chia"),
    procedure: str = typer.Option(NotaryProcedureType.DIVISION_AGREEMENT.value, "--procedure", "-p", help="DIVISION_AGREEMENT / ACCEPTANCE_DECLARATION"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Ngày công chứng phân chia"),
    ubnd: Optional[str] = typer.Option(None, "--ubnd", help="UBND cấp xã nơi niêm yết thông báo thừa kế 15 ngày"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Lập Văn bản thỏa thuận phân chia di sản / Khai nhận di sản & kiểm tra niêm yết 15 ngày (Điều 57, 58 Luật Công chứng)."""
    engine = InheritanceEngine()
    try:
        res = engine.execute_division_agreement(
            estate_id=estate_id,
            procedure_type=procedure,
            notary_office=office,
            division_date=date,
            public_posting_ubnd=ubnd,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Lập văn bản phân chia di sản thành công![/bold green] Mã thỏa thuận: [cyan]{res['agreement_id']}[/cyan]")
            console.print(f"Thủ tục: [bold]{res['procedure_type']}[/bold] tại [yellow]{res['notary_office']}[/yellow]")
            console.print(f"Niêm yết công khai: {res['public_posting']['start_date']} đến {res['public_posting']['end_date']} tại UBND: [cyan]{res['public_posting']['ubnd_location']}[/cyan] (Đủ 15 ngày)")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi lập văn bản phân chia:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("statute-check")
def statute_check(
    dod: str = typer.Option(..., "--dod", help="Ngày mở thừa kế / ngày chết (YYYY-MM-DD)"),
    date: Optional[str] = typer.Option(None, "--current-date", help="Ngày kiểm tra thời hiệu"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Kiểm tra thời hiệu thừa kế 30 năm (BĐS), 10 năm (động sản), 03 năm (nghĩa vụ nợ) (Điều 623 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.check_statute_of_limitations(dod, date)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            table = Table(title=f"Kiểm tra Thời hiệu Thừa kế (Điều 623 BLDS 2015) — Ngày chết: {dod}", box=box.ROUNDED)
            table.add_column("Loại quyền yêu cầu", style="bold green")
            table.add_column("Thời hiệu luật định", style="cyan")
            table.add_column("Hạn chót", style="white")
            table.add_column("Số năm còn lại", style="yellow")
            table.add_column("Trạng thái", style="bold magenta")

            re = res["real_estate_claim"]
            mv = res["movable_property_claim"]
            ob = res["creditor_obligation_claim"]

            table.add_row("Yêu cầu chia Di sản Bất động sản", f"{re['limitation_years']} năm", re["deadline"], f"{re['remaining_years']} năm", re["status"])
            table.add_row("Yêu cầu chia Di sản Động sản", f"{mv['limitation_years']} năm", mv["deadline"], f"{mv['remaining_years']} năm", mv["status"])
            table.add_row("Yêu cầu thực hiện nghĩa vụ tài sản", f"{ob['limitation_years']} năm", ob["deadline"], f"{ob['remaining_years']} năm", ob["status"])

            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Lỗi kiểm tra thời hiệu:[/bold red] {e}")
        raise typer.Exit(code=1)
