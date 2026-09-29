# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Education, Higher Education, Accreditation & Degree Registry Suite (Phase 82)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    engine = EducationEngine()
    try:
        res = engine.license_institution(
            institution_name=name,
            institution_type=inst_type,
            tax_id=tax_id,
            investment_capital_vnd=capital,
            land_area_sqm=land,
            campus_address=address,
            decision_signer=authority,
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

    table.add_row("Tên cơ sở giáo dục", res["institution_name"])
    table.add_row("Loại hình cơ sở GD", f"[bold yellow]{res['institution_name_vi']}[/]")
    table.add_row("Mã định danh giấy phép", f"[bold green]{res['license_id']}[/]")
    table.add_row("Mã số thuế", res["tax_id"])
    table.add_row("Vốn đầu tư đăng ký", f"{res['investment_capital_vnd']:,.0f} VND (Chuẩn tối thiểu: {res['statutory_min_capital_vnd']:,.0f} VND)")
    table.add_row("Diện tích đất khuôn viên", f"{res['land_area_sqm']:,.0f} m2 (Chuẩn tối thiểu: {res['statutory_min_land_sqm']:,.0f} m2)")
    table.add_row("Địa điểm xây dựng", res["campus_address"])
    table.add_row("Số quyết định thành lập", f"[bold green]{res['decision_number']}[/]")
    table.add_row("Cơ quan ban hành", res["governing_body"])
    table.add_row("Căn cứ pháp lý", res["statutory_ref"])

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

    engine = EducationEngine()
    try:
        res = engine.audit_accreditation(
            institution_name=name,
            total_students=students,
            total_faculty=faculty,
            phd_faculty_count=phd,
            floor_area_sqm=floor,
            average_criteria_score=score,
            passed_criteria_count=passed,
            reporting_year=year,
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

    table.add_row("Cơ sở giáo dục", res["institution_name"])
    table.add_row("Mã kiểm định", res["audit_id"])
    table.add_row("Tỷ lệ SV/Giảng viên (STR)", f"{res['student_faculty_ratio']}:1 (Trần tối đa: <= 20:1)")
    table.add_row("Tỷ lệ Tiến sĩ cơ hữu", f"{res['phd_faculty_ratio_pct']}% (Chuẩn tối thiểu: >= 35%)")
    table.add_row("Diện tích sàn/sinh viên", f"{res['floor_area_per_student_sqm']} m2/SV (Chuẩn tối thiểu: >= 2.8 m2)")
    table.add_row("Điểm TB tiêu chí", f"{res['average_criteria_score']}/7.0 (Mức Đạt: >= 4.0)")
    table.add_row("Số tiêu chí Đạt", f"{res['passed_criteria_count']}/{res['total_criteria']} tiêu chí")
    verdict_color = "green" if res["is_accredited"] else ("yellow" if res["accreditation_verdict"] == "CONDITIONAL" else "red")
    table.add_row("Kết luận kiểm định", f"[bold {verdict_color}]{res['accreditation_verdict']}[/]")
    table.add_row("Thời hạn công nhận", f"{res['validity_years']} năm")

    console.print(table)


@education_app.command("quota")
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


@education_app.command("degree")
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


@education_app.command("verify")
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


@education_app.command("list")
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


@education_app.command("status")
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
