# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Education, Higher Education, Accreditation & Degree Registry Suite (Phase 82)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._education_operations import (
    degree_cmd,
    quota_cmd,
    register_education_operations,
    verify_cmd,
)
from src.cli.commands._education_queries import (
    list_cmd,
    register_education_queries,
    status_cmd,
)

education_app = typer.Typer(
    name="education",
    help="Vietnamese Education, Higher Education, Accreditation & Degree Registry Suite.",
)
console = Console()


@education_app.callback(invoke_without_command=True)
def education_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hệ thống giáo dục, kiểm định chất lượng, chỉ tiêu tuyển sinh và văn bằng số."""
    if ctx.invoked_subcommand is not None:
        return

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
            f"[bold green]HỆ THỐNG GIÁO DỤC, KIỂM ĐỊNH ĐẠI HỌC & VĂN BẰNG ĐIỆN TỬ VIỆT NAM[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Cơ sở giáo dục:      [bold cyan]{inst['total_licensed']}[/] cơ sở đã cấp phép ([bold green]{inst['universities']}[/] trường Đại học)\n"
            f"  Kiểm định chất lượng:[bold green]{acc['accredited_institutions']}/{acc['total_audits']}[/] đợt kiểm định đạt chuẩn quốc gia (TT 12/2017)\n"
            f"  Chỉ tiêu tuyển sinh: [bold cyan]{qta['total_annual_intake']:,}[/] sinh viên hàng năm trên [bold]{qta['total_declared_majors']}[/] ngành đào tạo\n"
            f"  Sổ văn bằng điện tử: [bold green]{deg['valid_degrees']}/{deg['total_degrees_issued']}[/] văn bằng tốt nghiệp quốc gia (TT 21/2019)",
            title="[bold green]Vietnam National Education & Degree Registry Telemetry[/]",
            border_style="green",
        )
    )


@education_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở giáo dục"),
    inst_type: str = typer.Option("UNIVERSITY", "--type", "-t", help="Loại hình: UNIVERSITY, BRANCH_CAMPUS, K12_SCHOOL, COLLEGE, FOREIGN_INVESTED_UNI"),
    tax_id: str = typer.Option("0109988771", "--tax-id", help="Mã số thuế cơ sở GD"),
    capital: float = typer.Option(1_200_000_000_000.0, "--capital", "-c", help="Vốn đầu tư đăng ký (VND)"),
    land: float = typer.Option(60_000.0, "--land", "-l", help="Diện tích đất khuôn viên trường (m2)"),
    address: str = typer.Option("Khu Đô thị Đại học, TP. Thủ Đức, TP. Hồ Chí Minh", "--address", "-a", help="Địa điểm trụ sở chính"),
    authority: str = typer.Option("Thủ tướng Chính phủ & Bộ GD&ĐT", "--authority", help="Cơ quan cấp quyết định thành lập"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện đầu tư và cấp phép thành lập cơ sở giáo dục (Nghị định 125/2024/NĐ-CP)."""
    from src.core.education_engine import EducationEngine
    try:
        res = EducationEngine().license_institution(
            institution_name=name, institution_type=inst_type, tax_id=tax_id,
            investment_capital_vnd=capital, land_area_sqm=land, campus_address=address, decision_signer=authority,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi cấp phép cơ sở giáo dục:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]QUYẾT ĐỊNH THÀNH LẬP & CẤP PHÉP HOẠT ĐỘNG GIÁO DỤC[/]")
    table.add_column("Hạng mục thẩm định", style="cyan", no_wrap=True)
    table.add_column("Nội dung", style="white")
    for k, v in [
        ("Tên cơ sở giáo dục", res["institution_name"]), ("Loại hình cơ sở GD", f"[bold yellow]{res['institution_name_vi']}[/]"),
        ("Mã định danh giấy phép", f"[bold green]{res['license_id']}[/]"), ("Mã số thuế", res["tax_id"]),
        ("Vốn đầu tư đăng ký", f"{res['investment_capital_vnd']:,.0f} VND (Chuẩn tối thiểu: {res['statutory_min_capital_vnd']:,.0f} VND)"),
        ("Diện tích đất khuôn viên", f"{res['land_area_sqm']:,.0f} m2 (Chuẩn tối thiểu: {res['statutory_min_land_sqm']:,.0f} m2)"),
        ("Địa điểm xây dựng", res["campus_address"]), ("Số quyết định thành lập", f"[bold green]{res['decision_number']}[/]"),
        ("Cơ quan ban hành", res["governing_body"]), ("Căn cứ pháp lý", res["statutory_ref"]),
    ]:
        table.add_row(k, v)
    console.print(table)


@education_app.command("accredit")
def accredit_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở giáo dục đại học thẩm định"),
    students: int = typer.Argument(..., help="Quy mô tổng số sinh viên chính quy"),
    faculty: int = typer.Argument(..., help="Tổng số giảng viên cơ hữu"),
    phd: int = typer.Argument(..., help="Số lượng giảng viên có trình độ Tiến sĩ"),
    floor: float = typer.Argument(..., help="Tổng diện tích sàn xây dựng phục vụ đào tạo (m2)"),
    score: float = typer.Option(4.5, "--score", "-s", help="Điểm trung bình tiêu chí kiểm định (thang điểm 1-7)"),
    passed: int = typer.Option(100, "--passed", "-p", help="Số lượng tiêu chí Đạt (trên tổng số 111 tiêu chí)"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm báo cáo kiểm định"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm định chất lượng cơ sở giáo dục đại học theo 25 tiêu chuẩn, 111 tiêu chí (Thông tư 12/2017/TT-BGDĐT)."""
    from src.core.education_engine import EducationEngine
    try:
        res = EducationEngine().audit_accreditation(
            institution_name=name, total_students=students, total_faculty=faculty, phd_faculty_count=phd,
            floor_area_sqm=floor, average_criteria_score=score, passed_criteria_count=passed, reporting_year=year,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi kiểm định chất lượng GDĐH:[/] {exc}")
        raise typer.Exit(code=1)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]KẾT QUẢ KIỂM ĐỊNH CHẤT LƯỢNG CƠ SỞ GIÁO DỤC ĐẠI HỌC[/]")
    table.add_column("Chỉ số kiểm định", style="cyan", no_wrap=True)
    table.add_column("Kết quả thẩm định", style="white")
    verdict_color = "green" if res["is_accredited"] else ("yellow" if res["accreditation_verdict"] == "CONDITIONAL" else "red")
    for k, v in [
        ("Cơ sở giáo dục", res["institution_name"]), ("Mã kiểm định", res["audit_id"]),
        ("Tỷ lệ SV/Giảng viên (STR)", f"{res['student_faculty_ratio']}:1 (Trần tối đa: <= 20:1)"),
        ("Tỷ lệ Tiến sĩ cơ hữu", f"{res['phd_faculty_ratio_pct']}% (Chuẩn tối thiểu: >= 35%)"),
        ("Diện tích sàn/sinh viên", f"{res['floor_area_per_student_sqm']} m2/SV (Chuẩn tối thiểu: >= 2.8 m2)"),
        ("Điểm TB tiêu chí", f"{res['average_criteria_score']}/7.0 (Mức Đạt: >= 4.0)"),
        ("Số tiêu chí Đạt", f"{res['passed_criteria_count']}/{res['total_criteria']} tiêu chí"),
        ("Kết luận kiểm định", f"[bold {verdict_color}]{res['accreditation_verdict']}[/]"),
        ("Thời hạn công nhận", f"{res['validity_years']} năm"),
    ]:
        table.add_row(k, v)
    console.print(table)


register_education_operations(education_app)
register_education_queries(education_app)

__all__ = ["education_app", "education_main", "license_cmd", "accredit_cmd", "quota_cmd", "degree_cmd", "verify_cmd", "list_cmd", "status_cmd"]
