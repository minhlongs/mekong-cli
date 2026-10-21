# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Enrollment quota, digital degree issuance, and degree verification subcommands for Education CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def register_education_operations(education_app: typer.Typer) -> None:
    """Register quota, degree, and verify commands onto education_app."""
    education_app.command("quota")(quota_cmd)
    education_app.command("degree")(degree_cmd)
    education_app.command("verify")(verify_cmd)


def quota_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở giáo dục đào tạo"),
    major: str = typer.Argument(..., help="Tên ngành đào tạo tuyển sinh"),
    level: str = typer.Option("BACHELOR", "--level", help="Trình độ đào tạo: BACHELOR, MASTER, DOCTORATE"),
    faculty: int = typer.Option(30, "--faculty", "-f", help="Số lượng giảng viên toàn thời gian ngành"),
    floor: float = typer.Option(6000.0, "--floor", help="Diện tích sàn xây dựng phục vụ ngành (m2)"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm tuyển sinh"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định chỉ tiêu tuyển sinh hàng năm theo năng lực giảng viên và mặt bằng (Thông tư 03/2022/TT-BGDĐT)."""
    from src.core.education_engine import EducationEngine

    engine = EducationEngine()
    try:
        res = engine.calculate_enrollment_quota(
            institution_name=name,
            major_name=major,
            degree_level=level,
            fulltime_faculty_count=faculty,
            floor_area_sqm=floor,
            academic_year=year,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi xác định chỉ tiêu tuyển sinh:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]CHỈ TIÊU TUYỂN SINH HÀNG NĂM (THÔNG TƯ 03/2022/TT-BGDĐT)[/]")
    table.add_column("Thông số đào tạo", style="cyan", no_wrap=True)
    table.add_column("Chỉ tiêu thẩm định", style="white")

    table.add_row("Cơ sở đào tạo", res["institution_name"])
    table.add_row("Ngành tuyển sinh", res["major_name"])
    table.add_row("Mã ngành đào tạo", res["major_code"])
    table.add_row("Trình độ đào tạo", res["degree_level"])
    table.add_row("Năm học tuyển sinh", str(res["academic_year"]))
    table.add_row("Năng lực theo giảng viên", f"{res['capacity_by_faculty']:,} sinh viên (Quy đổi 20 SV/GV)")
    table.add_row("Năng lực theo diện tích sàn", f"{res['capacity_by_floor']:,} sinh viên (Chuẩn 2.8 m2/SV)")
    table.add_row("Chỉ tiêu tuyển sinh tối đa", f"[bold green]{res['max_annual_quota']:,}[/] sinh viên/năm")

    console.print(table)


def degree_cmd(
    name: str = typer.Argument(..., help="Họ và tên người học tốt nghiệp"),
    student_id: str = typer.Argument(..., help="Mã số sinh viên (MSSV)"),
    citizen_id: str = typer.Argument(..., help="Số Căn cước công dân (CCCD)"),
    major: str = typer.Argument(..., help="Ngành học đào tạo"),
    degree_type: str = typer.Option("BACHELOR", "--type", "-t", help="Loại bằng: BACHELOR, ENGINEER, MASTER, DOCTORATE"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm tốt nghiệp"),
    rank: str = typer.Option("XUẤT SẮC", "--rank", "-r", help="Xếp loại tốt nghiệp: XUẤT SẮC, GIỎI, KHÁ, TRUNG BÌNH"),
    institution: str = typer.Option("Trường Đại học Quốc tế Mekong", "--institution", "-i", help="Trường cấp bằng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Cấp văn bằng tốt nghiệp điện tử có mã số quốc gia và chữ ký mã hóa (Thông tư 21/2019/TT-BGDĐT)."""
    from src.core.education_engine import EducationEngine

    engine = EducationEngine()
    try:
        res = engine.issue_degree_certificate(
            student_name=name,
            student_id=student_id,
            citizen_id=citizen_id,
            major=major,
            degree_type=degree_type,
            graduation_year=year,
            classification=rank,
            issuing_institution=institution,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi cấp văn bằng tốt nghiệp:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]VĂN BẰNG TỐT NGHIỆP ĐIỆN TỬ QUỐC GIA[/]")
    table.add_column("Hạng mục văn bằng", style="cyan", no_wrap=True)
    table.add_column("Chi tiết", style="white")

    table.add_row("Họ và tên người học", f"[bold]{res['student_name']}[/]")
    table.add_row("Số Căn cước công dân", res["citizen_id"])
    table.add_row("Mã số sinh viên", res["student_id"])
    table.add_row("Loại văn bằng", f"[bold yellow]{res['degree_name_vi']}[/]")
    table.add_row("Ngành đào tạo", res["major"])
    table.add_row("Xếp loại tốt nghiệp", f"[bold green]{res['classification']}[/]")
    table.add_row("Số hiệu văn bằng quốc gia", f"[bold green]{res['serial_number']}[/]")
    table.add_row("Đơn vị cấp bằng", res["issuing_institution"])
    table.add_row("Chữ ký mật mã (Hash)", f"[dim]{res['digital_hash'][:32]}...[/]")
    table.add_row("Trạng thái", f"[bold green]{res['status']}[/]")

    console.print(table)


def verify_cmd(
    serial: str = typer.Argument(..., help="Số hiệu văn bằng quốc gia (VD: VB-2026-ABCD1234)"),
    citizen_id: str = typer.Argument(..., help="Số Căn cước công dân chủ văn bằng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu và xác thực tính hợp pháp, chống văn bằng giả mạo trên cơ sở dữ liệu quốc gia."""
    from src.core.education_engine import EducationEngine

    engine = EducationEngine()
    res = engine.verify_degree_authenticity(serial_number=serial, citizen_id=citizen_id)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if res["is_authentic"]:
        console.print(
            Panel(
                f"[bold green]VĂN BẰNG HỢP PHÁP VÀ ĐƯỢC XÁC THỰC BẢN QUYỀN TOÀN VẸN[/]\n\n"
                f"  Người được cấp bằng:  [bold]{res['student_name']}[/] (CCCD: {res['citizen_id']})\n"
                f"  Văn bằng:             [bold yellow]{res['degree_name_vi']}[/] - Ngành [bold]{res['major']}[/]\n"
                f"  Xếp loại tốt nghiệp:  [bold green]{res['classification']}[/]\n"
                f"  Cơ sở giáo dục cấp:   [bold]{res['issuing_institution']}[/]\n"
                f"  Mã số hiệu quốc gia:  [bold cyan]{res['serial_number']}[/]\n"
                f"  Toàn vẹn mật mã:      [bold green]HỢP LỆ (Chữ ký điện tử toàn vẹn)[/]",
                title="[bold green]KẾT QUẢ XÁC THỰC VĂN BẰNG ĐIỆN TỬ[/]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]CẢNH BÁO: VĂN BẰNG KHÔNG HỢP PHÁP HOẶC KHÔNG TỒN TẠI[/]\n\n"
                f"  Số hiệu tra cứu:     [bold]{res['serial_number']}[/]\n"
                f"  Trạng thái kiểm tra: [bold red]{res.get('verification_status', 'INVALID')}[/]\n"
                f"  Lý do cảnh báo:      {res.get('message', 'Chữ ký mật mã không khớp hoặc bị chỉnh sửa trái phép.')}",
                title="[bold red]XÁC THỰC VĂN BẰNG THẤT BẠI[/]",
                border_style="red",
            )
        )
