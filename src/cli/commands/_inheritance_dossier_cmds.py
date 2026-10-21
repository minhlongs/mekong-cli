# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 148: Inheritance Dossier, Compliance Audit & Estate Inspection CLI commands."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.panel import Panel

from src.cli.commands._inheritance_estate_cmds import (
    _render_status_dashboard,
    console,
    inheritance_app,
)
from src.core.inheritance_engine import InheritanceEngine


@inheritance_app.command("dossier")
def dossier(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Xuất trọn bộ Hồ sơ Pháp lý thừa kế phục vụ Công chứng, Sang tên Sổ đỏ & Ngân hàng."""
    engine = InheritanceEngine()
    try:
        res = engine.generate_inheritance_dossier(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(Panel.fit(
                f"[bold green]HỒ SƠ PHÁP LÝ THỪA KẾ (INHERITANCE LEGAL DOSSIER) — {res['dossier_id']}[/bold green]\n"
                f"Người để lại di sản: [bold cyan]{res['estate_metadata']['decedent_name']}[/bold cyan] | CCCD: {res['estate_metadata']['decedent_id_number']}\n"
                f"Ngày mở thừa kế: {res['estate_metadata']['date_of_death']} | Nơi mở: {res['estate_metadata']['place_of_opening']}\n"
                f"Tổng di sản phân chia: [bold yellow]{res['financial_summary']['net_distributable_estate']:,.0f} VND[/bold yellow]",
                box=box.DOUBLE,
            ))
            console.print("[bold underline]Thành phần hồ sơ bắt buộc gửi cơ quan công chứng/đăng ký đất đai:[/bold underline]")
            for req in res["notary_requirements"]:
                console.print(f"  • {req}")
    except Exception as e:
        console.print(f"[bold red]Lỗi xuất hồ sơ:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("audit")
def audit(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Thẩm định tuân thủ pháp luật thừa kế toàn diện (Civil Code 2015 Compliance Audit)."""
    engine = InheritanceEngine()
    try:
        res = engine.audit_compliance(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            status_style = "bold green" if res["is_compliant"] else "bold red"
            console.print(Panel.fit(
                f"[{status_style}]KẾT QUẢ THẨM ĐỊNH TUÂN THỦ PHÁP LUẬT THỪA KẾ[/{status_style}]\n"
                f"Hồ sơ: [bold]{res['estate_id']}[/bold] ({res['decedent_name']})\n"
                f"Đánh giá: [{status_style}]{res['compliance_rating']}[/{status_style}]\n"
                f"Vi phạm phát hiện: [bold]{res['issues_count']}[/bold] | Cảnh báo: [yellow]{res['warnings_count']}[/yellow]",
                box=box.ROUNDED,
            ))
            if res["issues"]:
                console.print("[bold red]Các vi phạm pháp luật cần khắc phục:[/bold red]")
                for iss in res["issues"]:
                    console.print(f"  ✖ {iss}")
            if res["warnings"]:
                console.print("[yellow]Các lưu ý pháp lý:[/yellow]")
                for w in res["warnings"]:
                    console.print(f"  ⚠ {w}")
    except Exception as e:
        console.print(f"[bold red]Lỗi thẩm định tuân thủ:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("show")
def show(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Xem chi tiết hồ sơ di sản thừa kế."""
    engine = InheritanceEngine()
    try:
        res = engine.get_estate(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(Panel.fit(
                f"[bold cyan]CHI TIẾT HỒ SƠ DI SẢN: {res['estate_id']}[/bold cyan]\n"
                f"Người để lại di sản: [bold]{res['decedent_name']}[/bold] (CCCD: {res['decedent_id_number']})\n"
                f"Ngày mất: {res['date_of_death']} | Nơi mất: {res['place_of_death']}\n"
                f"Nơi cư trú cuối: {res['last_residence']}\n"
                f"Người quản lý di sản: {res.get('administrator_name') or 'Chưa cử'}\n"
                f"Tổng tài sản: [bold yellow]{res['summary']['total_gross_assets']:,.0f} VND[/bold yellow] | Nợ: [red]{res['summary']['total_obligations']:,.0f} VND[/red]\n"
                f"Di sản thờ cúng: [yellow]{res['summary']['dedicated_worship_amount']:,.0f} VND[/yellow] | Di sản ròng: [bold green]{res['summary']['net_distributable_estate']:,.0f} VND[/bold green]",
                box=box.ROUNDED,
            ))
    except Exception as e:
        console.print(f"[bold red]Lỗi khi đọc hồ sơ:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("list")
def list_cmd(
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Danh sách các hồ sơ di sản thừa kế."""
    engine = InheritanceEngine()
    try:
        estates = engine.list_estates(limit)
        if json_output:
            console.print(json.dumps(estates, indent=2, ensure_ascii=False))
        else:
            _render_status_dashboard(estates)
    except Exception as e:
        console.print(f"[bold red]Lỗi khi liệt kê hồ sơ:[/bold red] {e}")
        raise typer.Exit(code=1)
