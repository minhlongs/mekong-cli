# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List and status subcommands for Education CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def register_education_queries(education_app: typer.Typer) -> None:
    """Register list and status commands onto education_app."""
    education_app.command("list")(list_cmd)
    education_app.command("status")(status_cmd)


def list_cmd(
    target: str = typer.Argument("institutions", help="Loại danh mục: institutions, accreditations, quotas, degrees"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục cơ sở giáo dục, hồ sơ kiểm định, chỉ tiêu tuyển sinh hoặc văn bằng đã cấp."""
    from src.core.education_engine import EducationEngine

    engine = EducationEngine()
    tgt = target.lower().strip()

    if tgt in ("institutions", "schools", "unis"):
        records = engine.list_institutions(limit=limit)
        title = "DANH SÁCH CƠ SỞ GIÁO DỤC ĐƯỢC CẤP PHÉP"
    elif tgt in ("accreditations", "audits"):
        records = engine.list_accreditations(limit=limit)
        title = "HỒ SƠ KIỂM ĐỊNH CHẤT LƯỢNG GIÁO DỤC ĐẠI HỌC"
    elif tgt in ("quotas", "admissions"):
        records = engine.list_enrollment_quotas(limit=limit)
        title = "CHỈ TIÊU TUYỂN SINH CÁC NGÀNH ĐÀO TẠO"
    elif tgt in ("degrees", "diplomas"):
        records = engine.list_digital_degrees(limit=limit)
        title = "SỔ CẤP PHÁT VĂN BẰNG TỐT NGHIỆP QUỐC GIA"
    else:
        console.print(f"[bold red]Danh mục không hợp lệ:[/] '{target}'. Hỗ trợ: institutions, accreditations, quotas, degrees")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"[bold green]{title}[/]")
    if tgt in ("institutions", "schools", "unis"):
        table.add_column("Mã GP", style="cyan")
        table.add_column("Tên cơ sở giáo dục", style="white")
        table.add_column("Loại hình", style="yellow")
        table.add_column("Vốn ĐT (tỷ VND)", justify="right")
        table.add_column("Diện tích (m2)", justify="right")
        table.add_column("Trạng thái", style="green")
        for r in records:
            table.add_row(
                r["license_id"],
                r["institution_name"],
                r["institution_type"],
                f"{r['investment_capital_vnd'] / 1e9:,.1f}",
                f"{r['land_area_sqm']:,.0f}",
                r["status"],
            )
    elif tgt in ("accreditations", "audits"):
        table.add_column("Mã KĐ", style="cyan")
        table.add_column("Cơ sở GDĐH", style="white")
        table.add_column("STR", justify="right")
        table.add_column("Tiến sĩ (%)", justify="right")
        table.add_column("Sàn/SV (m2)", justify="right")
        table.add_column("Kết luận", style="green")
        for r in records:
            table.add_row(
                r["audit_id"],
                r["institution_name"],
                f"{r['student_faculty_ratio']}:1",
                f"{r['phd_faculty_ratio_pct']}%",
                f"{r['floor_area_per_student_sqm']}",
                r["accreditation_verdict"],
            )
    elif tgt in ("quotas", "admissions"):
        table.add_column("Mã ngành", style="cyan")
        table.add_column("Ngành đào tạo", style="white")
        table.add_column("Trường", style="yellow")
        table.add_column("Trình độ", style="magenta")
        table.add_column("Chỉ tiêu/năm", justify="right", style="green")
        for r in records:
            table.add_row(
                r["major_code"],
                r["major_name"],
                r["institution_name"],
                r["degree_level"],
                f"{r['max_quota']:,}",
            )
    else:
        table.add_column("Số hiệu VB", style="cyan")
        table.add_column("Người học", style="white")
        table.add_column("CCCD", style="yellow")
        table.add_column("Loại bằng", style="magenta")
        table.add_column("Xếp loại", style="green")
        for r in records:
            table.add_row(
                r["serial_number"],
                r["student_name"],
                r["citizen_id"],
                r["degree_name_vi"],
                r["classification"],
            )

    console.print(table)


def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xuất báo cáo trạng thái hệ thống giáo dục, chỉ tiêu tuyển sinh và văn bằng số."""
    from src.core.education_engine import EducationEngine

    engine = EducationEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    inst = status_data["institutions"]
    acc = status_data["accreditation"]
    qta = status_data["enrollment_quotas"]
    deg = status_data["degree_registry"]

    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG GIÁO DỤC QUỐC GIA (EDUCATION ENGINE)[/]\n\n"
            f"  Cơ quan quản lý:     [bold]{status_data['statutory_law']}[/]\n"
            f"  Đã cấp phép:         [bold cyan]{inst['total_licensed']}[/] cơ sở giáo dục\n"
            f"  Đợt kiểm định đạt:   [bold green]{acc['accredited_institutions']}/{acc['total_audits']}[/] hồ sơ\n"
            f"  Tổng chỉ tiêu SV:    [bold cyan]{qta['total_annual_intake']:,}[/] sinh viên/năm\n"
            f"  Văn bằng toàn vẹn:   [bold green]{deg['valid_degrees']}/{deg['total_degrees_issued']}[/] văn bằng tốt nghiệp",
            title="[bold green]Education System Status[/]",
            border_style="green",
        )
    )
