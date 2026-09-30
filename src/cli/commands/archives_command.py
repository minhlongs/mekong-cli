# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Archives, Digital Records & State Secrets Declassification Suite (Phase 103)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

archives_app = typer.Typer(
    name="archives",
    help="Vietnamese Archives, Digital Records & State Secrets Declassification Suite.",
)
console = Console()


@archives_app.callback(invoke_without_command=True)
def archives_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động lưu trữ số, niêm phong tài liệu, thời hạn bảo quản và giải mật bí mật nhà nước."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    telemetry = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(asdict(telemetry), indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ LƯU TRỮ SỐ & GIẢI MẬT BÍ MẬT NHÀ NƯỚC QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Lưu trữ 2024 (Luật 33/2024/QH15) & Luật BVBMNN 2018[/]\n"
            f"  Cơ quan quản lý chuyên môn: [bold yellow]Cục Văn thư và Lưu trữ Nhà nước (Bộ Nội vụ)[/]\n\n"
            f"  Tổng hồ sơ số hóa:         [bold]{telemetry.total_records}[/] hồ sơ ([bold green]{telemetry.compliant_sealed_records}[/] niêm phong hợp chuẩn PDF/A & SHA-256)\n"
            f"  Bảo quản vĩnh viễn:        [bold green]{telemetry.permanent_records}[/] hồ sơ lịch sử không thể thay thế\n"
            f"  Tài liệu bí mật nhà nước:  [bold]{telemetry.active_secrets}[/] hồ sơ đang bảo vệ mật | [bold green]{telemetry.declassified_records}[/] hồ sơ đã giải mật công khai\n"
            f"  Tiêu hủy hợp pháp:         [bold]{telemetry.approved_destructions}[/] hồ sơ hết thời hạn bảo quản được phê duyệt tiêu hủy\n"
            f"  Chứng chỉ hành nghề:       [bold green]{telemetry.certified_practitioners}[/] chuyên viên lưu trữ đạt chuẩn quốc gia\n"
            f"  Kho lưu trữ đạt chuẩn A:   [bold green]{telemetry.compliant_warehouses}[/] kho đáp ứng tiêu chuẩn nhiệt độ, độ ẩm & PCCC khí sạch",
            title="[bold blue]Vietnam National Archives & Digital Records Telemetry[/]",
            border_style="blue",
        )
    )


@archives_app.command("seal")
def seal_cmd(
    agency: str = typer.Argument(..., help="Mã cơ quan, tổ chức lưu trữ"),
    title: str = typer.Argument(..., help="Tiêu đề hồ sơ, tài liệu lưu trữ"),
    fmt: str = typer.Option("PDF/A-1a", "--format", "-f", help="Định dạng tệp: PDF/A-1a, PDF/A-2u, XML, TIFF, PNG, WAV, MP4"),
    checksum: Optional[str] = typer.Option(None, "--checksum", "-c", help="Mã băm SHA-256 xác thực toàn vẹn (tự động tính nếu để trống)"),
    signature: bool = typer.Option(True, "--signature/--no-signature", help="Có chữ ký số cơ quan"),
    tsa: bool = typer.Option(True, "--tsa/--no-tsa", help="Có dấu thời gian tin cậy TSA"),
    retention: str = typer.Option("PERMANENT", "--retention", "-r", help="Thời hạn bảo quản: PERMANENT, 70_YEARS, 20_YEARS, 10_YEARS, 5_YEARS"),
    security: str = typer.Option("UNCLASSIFIED", "--security", "-s", help="Cấp độ bảo mật: UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP_SECRET"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Niêm phong tài liệu lưu trữ điện tử theo Thông tư 02/2019/TT-BNV & Điều 13-17 Luật Lưu trữ 2024."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    res = engine.seal_electronic_record(
        agency_code=agency,
        title=title,
        doc_format=fmt,
        checksum=checksum,
        digital_signature=signature,
        tsa_timestamp=tsa,
        retention=retention,
        security_level=security,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.status == "SEALED_COMPLIANT" else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Không có lỗi vi phạm."

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ NIÊM PHONG TÀI LIỆU LƯU TRỮ ĐIỆN TỬ[/]\n\n"
            f"  Mã hồ sơ số:           [bold]{res.record_id}[/]\n"
            f"  Cơ quan lưu trữ:       {res.agency_code}\n"
            f"  Tiêu đề tài liệu:      [bold]{res.title}[/]\n"
            f"  Định dạng tệp:         [bold cyan]{res.format}[/]\n"
            f"  Mã băm SHA-256:        [yellow]{res.checksum_sha256}[/]\n"
            f"  Chữ ký số cơ quan:     [{'green' if res.digital_signature else 'red'}]{'HỢP LỆ' if res.digital_signature else 'THIẾU CHỮ KÝ SỐ'}[/]\n"
            f"  Dấu thời gian TSA:     [{'green' if res.tsa_timestamp else 'red'}]{'XÁC THỰC' if res.tsa_timestamp else 'THIẾU DẤU THỜI GIAN'}[/]\n"
            f"  Thời hạn bảo quản:     [bold]{res.retention}[/]\n"
            f"  Cấp độ mật:            [{'green' if res.security_level == 'UNCLASSIFIED' else 'bold red'}]{res.security_level}[/]\n"
            f"  Trạng thái niêm phong: [bold {status_color}]{res.status}[/bold {status_color}]\n\n"
            f"  Chi tiết thẩm định:\n{reasons_str}",
            title="[bold blue]Electronic Archival Record Sealing[/]",
            border_style="cyan",
        )
    )


@archives_app.command("appraise")
def appraise_cmd(
    record_id: str = typer.Argument(..., help="Mã hồ sơ lưu trữ cần thẩm định"),
    title: str = typer.Argument(..., help="Tiêu đề hồ sơ tài liệu"),
    year: int = typer.Option(..., "--year", "-y", help="Năm tạo lập tài liệu"),
    schedule: str = typer.Option("10_YEARS", "--schedule", help="Thời hạn lưu trữ theo quy chế: PERMANENT, 70_YEARS, 20_YEARS, 10_YEARS, 5_YEARS"),
    council: bool = typer.Option(True, "--council/--no-council", help="Đã thành lập Hội đồng xác định giá trị tài liệu (Điều 19)"),
    approval: bool = typer.Option(True, "--approval/--no-approval", help="Có ý kiến chấp thuận thẩm định của cơ quan quản lý lưu trữ"),
    director: bool = typer.Option(True, "--director/--no-director", help="Có Quyết định tiêu hủy của Người đứng đầu cơ quan"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm định thời hạn bảo quản và phê duyệt tiêu hủy tài liệu hết giá trị (Điều 18-22 Luật Lưu trữ 2024)."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    res = engine.appraise_retention(
        record_id=record_id,
        title=title,
        created_year=year,
        retention_schedule=schedule,
        has_appraisal_council=council,
        state_archives_approved=approval,
        director_signed=director,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if "APPROVED" in res.destruction_status or "PERMANENT" in res.destruction_status else "yellow"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Đủ điều kiện thủ tục."

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ THẨM ĐỊNH THỜI HẠN BẢO QUẢN & TIÊU HỦY TÀI LIỆU[/]\n\n"
            f"  Mã thẩm định:          [bold]{res.appraisal_id}[/]\n"
            f"  Mã hồ sơ:              {res.record_id} | Tiêu đề: [bold]{res.title}[/]\n"
            f"  Năm hình thành:        {res.created_year} ([bold]{res.years_elapsed} năm[/] đã trôi qua)\n"
            f"  Khung bảo quản:        [bold cyan]{res.retention_schedule}[/]\n"
            f"  Hết thời hạn bảo quản: [{'red' if res.is_expired else 'green'}]{'ĐÃ HẾT HẠN' if res.is_expired else 'ĐANG BẢO QUẢN'}[/]\n"
            f"  Kết luận xử lý:        [bold {status_color}]{res.destruction_status}[/bold {status_color}]\n"
            f"  Đánh giá nghiệp vụ:    {res.evaluation_notes}\n\n"
            f"  Căn cứ pháp lý & thủ tục:\n{reasons_str}",
            title="[bold blue]Retention Appraisal & Destruction Authorization[/]",
            border_style="cyan",
        )
    )


@archives_app.command("declassify")
def declassify_cmd(
    record_id: str = typer.Argument(..., help="Mã hồ sơ tài liệu mật"),
    title: str = typer.Argument(..., help="Tiêu đề tài liệu"),
    security: str = typer.Option("SECRET", "--security", "-s", help="Cấp độ bảo mật: TOP_SECRET (30y), SECRET (20y), CONFIDENTIAL (10y)"),
    year: int = typer.Option(..., "--year", "-y", help="Năm đóng dấu tài liệu mật"),
    authority: str = typer.Option("Bộ trưởng / Chủ tịch UBND tỉnh", "--auth", "-a", help="Người đứng đầu cơ quan có thẩm quyền giải mật"),
    early: bool = typer.Option(False, "--early", help="Đề nghị giải mật trước thời hạn quy định"),
    safe: bool = typer.Option(True, "--safe/--risk", help="Việc giải mật bảo đảm không gây nguy hại lợi ích quốc gia"),
    director: bool = typer.Option(True, "--director/--no-director", help="Có Quyết định giải mật của Người đứng đầu cơ quan"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Rà soát và thực hiện thủ tục giải mật tài liệu bí mật nhà nước (Luật BVBMNN 2018 & Luật Lưu trữ 2024)."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    res = engine.review_declassification(
        record_id=record_id,
        title=title,
        security_level=security,
        classified_year=year,
        authorized_by=authority,
        national_interest_safeguarded=safe,
        head_of_agency_approval=director,
        request_early=early,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.declassification_status == "DECLASSIFIED" else "yellow"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Không có điều kiện cản trở."

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ RÀ SOÁT GIẢI MẬT TÀI LIỆU BÍ MẬT NHÀ NƯỚC[/]\n\n"
            f"  Mã rà soát:            [bold]{res.review_id}[/]\n"
            f"  Hồ sơ:                 {res.record_id} | Tiêu đề: [bold]{res.title}[/]\n"
            f"  Cấp độ mật ban đầu:    [bold red]{res.original_security_level}[/]\n"
            f"  Năm xác định mật:      {res.classified_year} (Thời hạn bảo vệ: [bold]{res.statutory_term_years} năm[/])\n"
            f"  Thời gian đã bảo vệ:   [bold]{res.years_classified} năm[/] ([{'green' if res.term_expired else 'yellow'}]{'HẾT HẠN BẢO VỆ MẬT' if res.term_expired else 'TRONG THỜI HẠN BẢO VỆ'}[/])\n"
            f"  Giải mật trước hạn:    {'CÓ' if res.early_declassification else 'KHÔNG'}\n"
            f"  Thẩm quyền giải mật:   {res.authorized_by}\n"
            f"  Trạng thái giải mật:   [bold {status_color}]{res.declassification_status}[/bold {status_color}]\n\n"
            f"  Căn cứ pháp lý:\n{reasons_str}",
            title="[bold blue]State Secrets Declassification Review[/]",
            border_style="cyan",
        )
    )


@archives_app.command("practitioner")
def practitioner_cmd(
    name: str = typer.Argument(..., help="Họ và tên nhân sự đề nghị cấp chứng chỉ"),
    major: str = typer.Option("Lưu trữ học", "--major", "-m", help="Chuyên ngành tốt nghiệp đại học"),
    exp: int = typer.Option(3, "--exp", "-e", help="Số năm hoạt động thực tế trong lĩnh vực lưu trữ (tối thiểu 3 năm)"),
    exam: bool = typer.Option(True, "--exam/--no-exam", help="Đã đạt kỳ sát hạch cấp Chứng chỉ hành nghề lưu trữ"),
    clean: bool = typer.Option(True, "--clean/--disciplined", help="Lý lịch trong sạch, không vi phạm pháp luật"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra tiêu chuẩn cấp Chứng chỉ hành nghề lưu trữ theo Điều 54-57 Luật Lưu trữ 2024."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    res = engine.audit_practitioner(
        name=name,
        degree_major=major,
        experience_years=exp,
        passed_national_exam=exam,
        clean_record=clean,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.is_eligible else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Đạt đầy đủ tiêu chuẩn theo Điều 55 Luật Lưu trữ 2024."

    console.print(
        Panel(
            f"[bold cyan]THẨM ĐỊNH CHỨNG CHỈ HÀNH NGHỀ LƯU TRỮ[/]\n\n"
            f"  Mã thẩm định:          [bold]{res.audit_id}[/]\n"
            f"  Họ và tên:             [bold]{res.practitioner_name}[/]\n"
            f"  Chuyên ngành đào tạo:  {res.degree_major}\n"
            f"  Kinh nghiệm công tác:  [bold]{res.experience_years} năm[/] (quy chuẩn: >= 3 năm)\n"
            f"  Sát hạch quốc gia:     [{'green' if res.passed_national_exam else 'red'}]{'ĐẠT YÊU CẦU' if res.passed_national_exam else 'CHƯA ĐẠT'}[/]\n"
            f"  Lý lịch pháp lý:       [{'green' if res.clean_record else 'red'}]{'TRONG SẠCH' if res.clean_record else 'CÓ VI PHẠM'}[/]\n"
            f"  Kết luận đủ điều kiện: [bold {status_color}]{'ĐỦ ĐIỀU KIỆN CẤP CHỨNG CHỈ' if res.is_eligible else 'KHÔNG ĐỦ ĐIỀU KIỆN'}[/bold {status_color}]\n"
            f"  Số chứng chỉ cấp:      [bold green]{res.certificate_no}[/]\n\n"
            f"  Chi tiết tiêu chuẩn:\n{reasons_str}",
            title="[bold blue]Archival Practitioner Certification Audit[/]",
            border_style="cyan",
        )
    )


@archives_app.command("warehouse")
def warehouse_cmd(
    name: str = typer.Argument(..., help="Tên hoặc mã định danh kho lưu trữ"),
    temp: float = typer.Option(20.0, "--temp", "-t", help="Nhiệt độ kho (tiêu chuẩn: 18.0 - 22.0 °C)"),
    humidity: float = typer.Option(52.0, "--humidity", "-h", help="Độ ẩm không khí (tiêu chuẩn: 50.0 - 55.0 %)"),
    fire_gas: bool = typer.Option(True, "--fire-gas/--no-fire-gas", help="Có hệ thống PCCC tự động bằng khí sạch (FM200 / Novec 1230)"),
    cctv: bool = typer.Option(True, "--cctv/--no-cctv", help="Có hệ thống camera an ninh giám sát 24/7"),
    shelving: bool = typer.Option(True, "--shelving/--no-shelving", help="Có giá kệ chuyên dụng chống cháy, chống tĩnh điện"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Kiểm tra điều kiện môi trường và an toàn cơ sở vật chất kho lưu trữ tài liệu."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    res = engine.audit_warehouse(
        facility_name=name,
        temp_celsius=temp,
        humidity_pct=humidity,
        clean_gas_fire_system=fire_gas,
        cctv_247=cctv,
        fireproof_shelving=shelving,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.grade == "GRADE_A_COMPLIANT" else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Đạt đầy đủ tiêu chuẩn kho lưu trữ quốc gia."

    console.print(
        Panel(
            f"[bold cyan]KIỂM ĐỊNH ĐIỀU KIỆN KHO LƯU TRỮ TÀI LIỆU[/]\n\n"
            f"  Mã kiểm định:          [bold]{res.audit_id}[/]\n"
            f"  Kho lưu trữ:           [bold]{res.facility_name}[/]\n"
            f"  Nhiệt độ đo được:      [bold]{res.temp_celsius}°C[/] (tiêu chuẩn: 18.0 - 22.0°C)\n"
            f"  Độ ẩm không khí:       [bold]{res.humidity_pct}%[/] (tiêu chuẩn: 50.0 - 55.0%)\n"
            f"  PCCC khí sạch FM200:   [{'green' if res.clean_gas_fire_system else 'red'}]{'ĐẠT CHUẨN' if res.clean_gas_fire_system else 'KHÔNG ĐẠT'}[/]\n"
            f"  Camera giám sát 24/7:  [{'green' if res.cctv_247 else 'red'}]{'CÓ' if res.cctv_247 else 'THIẾU'}[/]\n"
            f"  Giá kệ chống cháy:     [{'green' if res.fireproof_shelving else 'red'}]{'ĐẠT CHUẨN' if res.fireproof_shelving else 'KHÔNG ĐẠT'}[/]\n"
            f"  Xếp hạng kiểm định:    [bold {status_color}]{res.grade}[/bold {status_color}]\n\n"
            f"  Chi tiết đánh giá:\n{reasons_str}",
            title="[bold blue]Archival Warehouse Condition Audit[/]",
            border_style="cyan",
        )
    )


@archives_app.command("list")
def list_cmd(
    category: str = typer.Option("all", "--category", "-c", help="Danh mục: all, records, appraisals, declassifications, practitioners, warehouses"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng kết quả tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ lưu trữ điện tử, thẩm định thời hạn, hồ sơ giải mật và chứng chỉ hành nghề."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    data = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if "electronic_records" in data and data["electronic_records"]:
        table = Table(title="Danh Sách Tài Liệu Lưu Trữ Điện Tử (Niêm Phong Số)", border_style="blue")
        table.add_column("Mã hồ sơ", style="cyan")
        table.add_column("Cơ quan", style="yellow")
        table.add_column("Tiêu đề", style="white")
        table.add_column("Định dạng", style="magenta")
        table.add_column("Thời hạn", style="blue")
        table.add_column("Cấp mật", style="red")
        table.add_column("Trạng thái", style="green")

        for r in data["electronic_records"]:
            table.add_row(
                r["record_id"],
                r["agency_code"],
                r["title"],
                r["format"],
                r["retention"],
                r["security_level"],
                r["status"],
            )
        console.print(table)

    if "retention_appraisals" in data and data["retention_appraisals"]:
        table = Table(title="Danh Sách Thẩm Định Thời Hạn & Tiêu Hủy", border_style="magenta")
        table.add_column("Mã thẩm định", style="cyan")
        table.add_column("Mã hồ sơ", style="yellow")
        table.add_column("Tiêu đề", style="white")
        table.add_column("Năm tạo", style="white")
        table.add_column("Khung thời hạn", style="blue")
        table.add_column("Kết luận xử lý", style="green")

        for r in data["retention_appraisals"]:
            table.add_row(
                r["appraisal_id"],
                r["record_id"],
                r["title"],
                str(r["created_year"]),
                r["retention_schedule"],
                r["destruction_status"],
            )
        console.print(table)

    if "declassification_reviews" in data and data["declassification_reviews"]:
        table = Table(title="Danh Sách Rà Soát Giải Mật Bí Mật Nhà Nước", border_style="cyan")
        table.add_column("Mã rà soát", style="cyan")
        table.add_column("Mã hồ sơ", style="yellow")
        table.add_column("Tiêu đề", style="white")
        table.add_column("Cấp độ ban đầu", style="red")
        table.add_column("Trạng thái giải mật", style="green")
        table.add_column("Người phê duyệt", style="white")

        for r in data["declassification_reviews"]:
            table.add_row(
                r["review_id"],
                r["record_id"],
                r["title"],
                r["original_security_level"],
                r["declassification_status"],
                r["authorized_by"],
            )
        console.print(table)


@archives_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry lưu trữ số và bảo mật quốc gia."""
    from src.core.archives_engine import ArchivesEngine

    engine = ArchivesEngine()
    telemetry = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(asdict(telemetry), indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ Số Telemetry Quản Lý Lưu Trữ Số Quốc Gia", border_style="blue")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="bold green")

    table.add_row("Tổng số hồ sơ điện tử", str(telemetry.total_records))
    table.add_row("Hồ sơ niêm phong số hợp chuẩn (PDF/A, SHA-256)", str(telemetry.compliant_sealed_records))
    table.add_row("Tài liệu lịch sử bảo quản vĩnh viễn", str(telemetry.permanent_records))
    table.add_row("Hồ sơ bí mật nhà nước đang bảo vệ", str(telemetry.active_secrets))
    table.add_row("Hồ sơ đã giải mật công khai", str(telemetry.declassified_records))
    table.add_row("Hồ sơ hết hạn được duyệt tiêu hủy", str(telemetry.approved_destructions))
    table.add_row("Chứng chỉ hành nghề lưu trữ đạt chuẩn", str(telemetry.certified_practitioners))
    table.add_row("Kho lưu trữ đạt chuẩn môi trường Hạng A", str(telemetry.compliant_warehouses))

    console.print(table)
