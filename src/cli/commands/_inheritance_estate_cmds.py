# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 148: Estate Creation, Asset Inventory & Obligation Registration CLI commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.inheritance_engine import (
    AssetCategory,
    InheritanceEngine,
    ObligationPriority,
    SuccessionType,
)

inheritance_app = typer.Typer(
    name="inheritance",
    help="Vietnamese Inheritance, Wills, Estate Administration & Succession Regimes Suite (BLDS 2015 Điều 609-662).",
    no_args_is_help=False,
)
app = inheritance_app
console = Console()


def _render_status_dashboard(estates: list) -> None:
    console.print(Panel.fit(
        "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — PHÁP LUẬT THỪA KẾ & DI SẢN[/bold cyan]\n"
        "[bold green]BẢNG ĐIỀU HÀNH QUẢN LÝ DI SẢN, DI CHÚC & PHÂN CHIA THỪA KẾ (BLDS 2015)[/bold green]\n"
        "[dim]Civil Code 2015 (Articles 609-662) & Law on Notarization 2014 (Articles 57-59)[/dim]",
        box=box.DOUBLE, border_style="cyan",
    ))
    table = Table(title="Tổng quan Hồ sơ Quản lý Di sản Thừa kế (Estate Succession Telemetry)", box=box.ROUNDED, show_header=True)
    for col, style in [("Mã Di sản (ID)", "bold green"), ("Người để lại di sản", "cyan"), ("Ngày mở thừa kế", "white"), ("Hình thức thừa kế", "magenta"), ("Trạng thái", "bold yellow")]:
        table.add_column(col, style=style)

    if not estates:
        table.add_row("Chưa có dữ liệu", "-", "-", "-", "-")
    else:
        for est in estates[:10]:
            status_text = "[bold green]Đã phân chia[/bold green]" if est.get("is_settled") else "[yellow]Đang xử lý[/yellow]"
            table.add_row(est.get("estate_id", "-"), est.get("decedent_name", "-"), est.get("date_of_death", "-"), est.get("succession_type", "-"), status_text)
    console.print(table)


@inheritance_app.callback(invoke_without_command=True)
def main(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", help="Output in JSON format")):
    """National Inheritance, Wills & Estate Administration Dashboard."""
    if ctx.invoked_subcommand is None:
        estates = InheritanceEngine().list_estates()
        console.print(json.dumps(estates, indent=2, ensure_ascii=False)) if json_output else _render_status_dashboard(estates)


@inheritance_app.command("estate-create")
def estate_create(
    decedent_name: str = typer.Option(..., "--name", "-n", help="Họ và tên người để lại di sản"),
    decedent_id: str = typer.Option(..., "--id-number", "-i", help="Số CCCD/Định danh cá nhân của người chết"),
    dob: str = typer.Option(..., "--dob", help="Ngày sinh (YYYY-MM-DD)"),
    date_of_death: str = typer.Option(..., "--dod", help="Ngày chết / Ngày mở thừa kế (YYYY-MM-DD)"),
    place_of_death: str = typer.Option("Hà Nội, Việt Nam", "--pod", help="Nơi chết"),
    last_residence: str = typer.Option("Hà Nội, Việt Nam", "--residence", "-r", help="Nơi cư trú cuối cùng"),
    administrator_name: Optional[str] = typer.Option(None, "--admin", help="Người quản lý di sản (Điều 616)"),
    worship_amount: float = typer.Option(0.0, "--worship", help="Di sản dành cho việc thờ cúng (Điều 645)"),
    succession_type: str = typer.Option(SuccessionType.INTESTATE.value, "--type", "-t", help="TESTAMENTARY / INTESTATE / MIXED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Ghi chú thêm"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Mở hồ sơ quản lý di sản thừa kế (Articles 609, 611, 612 BLDS 2015)."""
    try:
        res = InheritanceEngine().create_estate(
            decedent_name=decedent_name, decedent_id_number=decedent_id, decedent_dob=dob,
            date_of_death=date_of_death, place_of_death=place_of_death, last_residence=last_residence,
            administrator_name=administrator_name, dedicated_worship_amount=worship_amount,
            succession_type=succession_type, notes=notes,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Mở hồ sơ di sản thành công![/bold green] Mã hồ sơ: [cyan]{res['estate_id']}[/cyan]")
            console.print(f"Người để lại di sản: [bold]{res['decedent_name']}[/bold] (Ngày chết: {res['date_of_death']})")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi mở hồ sơ di sản:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("asset-add")
def asset_add(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    asset_name: str = typer.Option(..., "--name", "-n", help="Tên tài sản di sản"),
    category: str = typer.Option(AssetCategory.REAL_ESTATE.value, "--category", "-c", help="REAL_ESTATE, VEHICLE, BANK_DEPOSIT_SAVINGS, CORPORATE_SHARES_EQUITY, PRECIOUS_ASSET, CASH_MONETARY, OTHER"),
    value: float = typer.Option(..., "--value", "-v", help="Giá trị ước tính (VND)"),
    is_sole_ownership: bool = typer.Option(True, "--sole/--common", help="Tài sản riêng của người chết hay tài sản chung"),
    ownership_share: float = typer.Option(1.0, "--share", "-s", help="Tỷ lệ sở hữu của người chết (mặc định 1.0 cho tài sản riêng, 0.5 cho tài sản chung vợ chồng)"),
    doc_ref: Optional[str] = typer.Option(None, "--doc", help="Số giấy tờ sở hữu (Sổ đỏ, sổ tiết kiệm, cà vẹt xe)"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Địa chỉ / nơi tọa lạc của tài sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Thêm tài sản vào danh mục kiểm kê di sản thừa kế (Điều 612 BLDS 2015)."""
    try:
        res = InheritanceEngine().add_estate_asset(
            estate_id=estate_id, asset_name=asset_name, category=category, estimated_value=value,
            is_sole_ownership=is_sole_ownership, ownership_share=ownership_share,
            legal_document_ref=doc_ref, location=location,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Đã thêm tài sản di sản:[/bold green] [cyan]{res['asset_name']}[/cyan] (Mã: {res['asset_id']})")
            console.print(f"Giá trị di sản thực nhận: [bold yellow]{res['net_estate_value']:,.0f} VND[/bold yellow] (Tỷ lệ: {res['ownership_share']*100:.0f}%)")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi thêm tài sản:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("obligation-add")
def obligation_add(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    creditor: str = typer.Option(..., "--creditor", help="Tên chủ nợ / người có quyền"),
    obligation_name: str = typer.Option(..., "--name", "-n", help="Nội dung nghĩa vụ tài sản"),
    priority: str = typer.Option(ObligationPriority.P1_BURIAL_EXPENSES.value, "--priority", "-p", help="Thứ tự ưu tiên thanh toán theo Điều 658 BLDS 2015 (P1_BURIAL_EXPENSES đến P9_OTHER_OBLIGATIONS)"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền nghĩa vụ (VND)"),
    legal_basis: Optional[str] = typer.Option(None, "--basis", help="Căn cứ pháp lý / hợp đồng vay"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Ghi nhận nghĩa vụ tài sản và nợ của người chết theo thứ tự ưu tiên (Điều 615 & 658 BLDS 2015)."""
    try:
        res = InheritanceEngine().add_estate_obligation(
            estate_id=estate_id, creditor_name=creditor, obligation_name=obligation_name,
            priority=priority, amount=amount, legal_basis=legal_basis,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Đã ghi nhận nghĩa vụ tài sản:[/bold green] [yellow]{res['obligation_name']}[/yellow]")
            console.print(f"Chủ nợ: {res['creditor_name']} | Ưu tiên: {res['priority']} | Số tiền: [bold]{res['amount']:,.0f} VND[/bold]")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi ghi nhận nghĩa vụ tài sản:[/bold red] {e}")
        raise typer.Exit(code=1)
