# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite (Phase 97)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

radiation_app = typer.Typer(
    name="radiation",
    help="Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite.",
)
console = Console()


@radiation_app.callback(invoke_without_command=True)
def radiation_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan an toàn bức xạ, cấp phép cơ sở bức xạ, quản lý nguồn phóng xạ và liều kế cá nhân."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold magenta]HỆ THỐNG QUẢN LÝ AN TOÀN BỨC XẠ & AN NINH NGUỒN PHÓNG XẠ[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan cấp phép & QL:     [bold yellow]{status_data['competent_authority']}[/]\n"
            f"  Cơ sở tiến hành CV bức xạ: [bold]{status_data['total_licensed_facilities']}[/] cơ sở ([bold green]{status_data['compliant_licensed_facilities']}[/] đạt chuẩn cấp phép NĐ 142/2020)\n"
            f"  Hồ sơ liều kế cá nhân:     [bold cyan]{status_data['personal_dosimetry_records_count']}[/] lượt đo kiểm liều nghề nghiệp\n"
            f"  Nguồn phóng xạ giám sát:   [bold]{status_data['monitored_radioactive_sources']}[/] nguồn ([bold green]{status_data['gps_active_radioactive_sources']}[/] nguồn kích hoạt định vị GPS thời gian thực)\n"
            f"  Thiết bị X-quang y tế QA:  [bold]{status_data['medical_xray_machines_inspected']}[/] máy kiểm định ([bold green]{status_data['compliant_medical_xray_machines']}[/] đạt chuẩn TTLT 13/2014)",
            title="[bold magenta]Vietnam Radiation Safety & Nuclear Source Security Telemetry[/]",
            border_style="magenta",
        )
    )


@radiation_app.command("license")
def license_cmd(
    facility: str = typer.Argument(..., help="Tên cơ sở tiến hành công việc bức xạ (Bệnh viện, Công ty NDT, Viện nghiên cứu)"),
    fac_type: str = typer.Option("HOSPITAL_RADIOLOGY", "--fac-type", "-t", help="Loại cơ sở: HOSPITAL_RADIOLOGY, INDUSTRIAL_NDT, RESEARCH_LAB, IRRADIATION_PLANT"),
    equipment: str = typer.Option("MEDICAL_XRAY", "--equipment", "-e", help="Thiết bị: MEDICAL_XRAY, CT_SCANNER, INDUSTRIAL_GAMMA_CAMERA, LINEAR_ACCELERATOR"),
    safety_officer: bool = typer.Option(True, "--officer/--no-officer", help="Có người phụ trách an toàn có Chứng chỉ nhân viên bức xạ"),
    emergency_plan: bool = typer.Option(True, "--emergency/--no-emergency", help="Đã phê duyệt Kế hoạch ứng phó sự cố bức xạ cấp cơ sở"),
    shielding: bool = typer.Option(True, "--shielding/--no-shielding", help="Phòng che chắn / kho lưu giữ đạt chuẩn"),
    warning_signs: bool = typer.Option(True, "--signs/--no-signs", help="Có đèn cảnh báo phát tia và biển báo bức xạ"),
    leak_rate: float = typer.Option(0.25, "--leak-rate", "-r", help="Suất liều rò rỉ bức xạ ngoài buồng chiếu (uSv/h) - Tối đa 0.5 uSv/h"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra hồ sơ cấp Giấy phép tiến hành công việc bức xạ theo Nghị định 142/2020/NĐ-CP và Luật Năng lượng nguyên tử."""
    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    res = engine.audit_radiation_facility_license(
        facility_name=facility,
        facility_type=fac_type,
        equipment_type=equipment,
        safety_officer_certified=safety_officer,
        emergency_plan_approved=emergency_plan,
        storage_shielding_compliant=shielding,
        has_warning_signs=warning_signs,
        radiation_leak_dose_rate_uSv_h=leak_rate,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_eligible"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH GIẤY PHÉP TIẾN HÀNH CÔNG VIỆC BỨC XẠ (NGHỊ ĐỊNH 142/2020/NĐ-CP)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['license_id']}[/]\n"
            f"  Cơ sở hoạt động:          [bold]{res['facility_name']}[/] ([white]{res['facility_type']}[/])\n"
            f"  Thiết bị / Nguồn bức xạ:  [cyan]{res['equipment_type']}[/]\n"
            f"  Người phụ trách ATBX:     [white]{'CÓ CHỨNG CHỈ ATBX CHÍNH THỨC' if res['safety_officer_certified'] else '[bold red]CHƯA CÓ CHỨNG CHỈ[/]'}[/]\n"
            f"  Kế hoạch ứng phó sự cố:   [white]{'ĐÃ ĐƯỢC PHÊ DUYỆT' if res['emergency_plan_approved'] else '[bold red]CHƯA PHÊ DUYỆT[/]'}[/]\n"
            f"  Che chắn buồng chiếu:     [white]{'ĐẠT CHUẨN' if res['storage_shielding_compliant'] else '[bold red]KHÔNG ĐẠT CHUẨN[/]'}[/]\n"
            f"  Suất liều rò rỉ ngoài:    [yellow]{res['radiation_leak_dose_rate_uSv_h']} uSv/h[/] ({'ĐẠT CHUẨN <= 0.5 uSv/h' if res['radiation_leak_dose_rate_uSv_h'] <= 0.5 else '[bold red]VƯỢT GIỚI HẠN[/]'})\n"
            f"  Kết luận thẩm định:       [bold {color}]{'ĐỦ ĐIỀU KIỆN CẤP PHÉP 03 NĂM' if is_ok else 'KHÔNG ĐỦ ĐIỀU KIỆN CẤP PHÉP'}[/]\n"
            + (f"  Nội dung thiếu sót:       [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:                 [bold green]Cơ sở đáp ứng đầy đủ điều kiện an toàn bức xạ theo luật định[/]"),
            title=f"[bold {color}]Radiation Facility Licensing Audit[/]",
            border_style=color,
        )
    )


@radiation_app.command("dose")
def dose_cmd(
    name: str = typer.Argument(..., help="Họ và tên nhân viên bức xạ"),
    emp_id: str = typer.Option("NV-001", "--id", help="Mã nhân viên bức xạ"),
    facility: str = typer.Option("Bệnh viện Đa khoa Quốc tế", "--facility", "-f", help="Tên cơ sở làm việc"),
    quarter: int = typer.Option(1, "--quarter", "-q", help="Quý đo đọc liều kế (1-4)"),
    year: int = typer.Option(2026, "--year", "-y", help="Năm theo dõi"),
    dose: float = typer.Option(1.2, "--dose", "-d", help="Liều hiệu dụng quý đo được (mSv)"),
    cumulative: float = typer.Option(4.5, "--cumulative", "-c", help="Liều tích lũy trong năm tính đến hiện tại (mSv) - Giới hạn 20 mSv/năm"),
    period_days: int = typer.Option(90, "--days", help="Số ngày đeo liều kế trong chu kỳ đo"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ghi nhận và đánh giá kết quả đo liều kế cá nhân của nhân viên bức xạ theo Thông tư 19/2012/TT-BKHCN."""
    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    res = engine.record_personal_dosimetry(
        employee_name=name,
        employee_id=emp_id,
        facility_name=facility,
        quarter=quarter,
        year=year,
        effective_dose_mSv=dose,
        cumulative_annual_dose_mSv=cumulative,
        wearing_period_days=period_days,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_danger = "CRITICAL" in res["status"]
    is_warn = "WARNING" in res["status"]
    color = "red" if is_danger else ("yellow" if is_warn else "green")

    console.print(
        Panel(
            f"[bold {color}]HỒ SƠ THEO DÕI LIỀU CHIẾU XẠ CÁ NHÂN (THÔNG TƯ 19/2012/TT-BKHCN)[/]\n\n"
            f"  Mã bản ghi:               [bold cyan]{res['record_id']}[/]\n"
            f"  Nhân viên bức xạ:         [bold]{res['employee_name']}[/] (Mã NV: [white]{res['employee_id']}[/])\n"
            f"  Cơ sở công tác:           [white]{res['facility_name']}[/]\n"
            f"  Kỳ đo liều:               [cyan]Quý {res['quarter']}/{res['year']}[/] (Chu kỳ: [white]{res['wearing_period_days']} ngày[/])\n"
            f"  Liều hiệu dụng quý:       [bold yellow]{res['effective_dose_mSv']} mSv[/]\n"
            f"  Liều tích lũy năm:        [bold {color}]{res['cumulative_annual_dose_mSv']} mSv / 20 mSv[/] ({res['cumulative_annual_dose_mSv'] / 20.0 * 100:.1f}% hạn mức)\n"
            f"  Đánh giá an toàn liều:    [bold {color}]{res['status']}[/]\n\n"
            f"  Khuyến nghị chuyên môn:\n" + "\n".join(f"    - [white]{r}[/]" for r in res["recommendations"]),
            title=f"[bold {color}]Personal Dosimetry Assessment[/]",
            border_style=color,
        )
    )


@radiation_app.command("source")
def source_cmd(
    serial: str = typer.Argument(..., help="Số hiệu / Mã nguồn phóng xạ (Serial No)"),
    isotope: str = typer.Option("IR-192", "--isotope", "-i", help="Đồng vị phóng xạ: IR-192, CO-60, CS-137, AM-241, KR-85"),
    initial_act: float = typer.Option(80.0, "--init-act", help="Hoạt độ ban đầu (Curie - Ci)"),
    current_act: float = typer.Option(45.0, "--cur-act", help="Hoạt độ hiện tại (Curie - Ci)"),
    app_type: str = typer.Option("INDUSTRIAL_NDT", "--type", "-t", help="Ứng dụng: INDUSTRIAL_NDT, RADIOTHERAPY, WELL_LOGGING, GAUGING"),
    gps: bool = typer.Option(True, "--gps/--no-gps", help="Có lắp thiết bị định vị GPS giám sát hành trình"),
    gps_signal: bool = typer.Option(True, "--signal/--no-signal", help="Tín hiệu GPS đang kết nối thời gian thực"),
    perimeter: bool = typer.Option(True, "--perimeter/--out-perimeter", help="Nguồn phóng xạ nằm trong phạm vi cấp phép"),
    vault: bool = typer.Option(True, "--vault/--no-vault", help="Kho cất giữ nguồn khóa an toàn và có camera giám sát"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Giám sát an ninh nguồn phóng xạ và kiểm tra định vị GPS thời gian thực theo Quyết định 446/QĐ-BKHCN."""
    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    res = engine.audit_radioactive_source_security(
        source_serial=serial,
        isotope=isotope,
        initial_activity_curie=initial_act,
        current_activity_curie=current_act,
        application_type=app_type,
        has_gps_tracker=gps,
        gps_signal_active=gps_signal,
        within_authorized_perimeter=perimeter,
        storage_vault_secured=vault,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_breach = "CRITICAL" in res["security_status"]
    is_warn = "WARNING" in res["security_status"]
    color = "red" if is_breach else ("yellow" if is_warn else "green")

    console.print(
        Panel(
            f"[bold {color}]GIÁM SÁT AN NINH NGUỒN PHÓNG XẠ & ĐỊNH VỊ GPS (QUYẾT ĐỊNH 446/QĐ-BKHCN)[/]\n\n"
            f"  Mã kiểm tra:              [bold cyan]{res['audit_id']}[/]\n"
            f"  Số hiệu nguồn:            [bold]{res['source_serial']}[/] (Đồng vị: [bold yellow]{res['isotope']}[/])\n"
            f"  Hoạt độ phóng xạ:         Hiện tại: [cyan]{res['current_activity_curie']} Ci[/] (Ban đầu: [white]{res['initial_activity_curie']} Ci[/])\n"
            f"  Phân nhóm an ninh IAEA:   [bold red]NHÓM {res['iaea_category']}[/] (Mức độ nguy hiểm cao)\n"
            f"  Ứng dụng nguồn:           [white]{res['application_type']}[/]\n"
            f"  Giám sát hành trình GPS:  [white]{'ĐÃ LẮP THIẾT BỊ GPS' if res['has_gps_tracker'] else '[bold red]CHƯA CÓ GPS[/]'}[/] | Tín hiệu: [white]{'KẾT NỐI 24/7' if res['gps_signal_active'] else '[bold red]MẤT TÍN HIỆU[/]'}[/]\n"
            f"  Phạm vi cho phép:         [white]{'TRONG VÙNG ĐĂNG KÝ' if res['within_authorized_perimeter'] else '[bold red]NGOÀI PHẠM VI CHO PHÉP (NGHI MẤT NGUỒN)[/]'}[/]\n"
            f"  Kho lưu giữ an toàn:      [white]{'BẢO VỆ 2 LỚP + CAMERA' if res['storage_vault_secured'] else '[bold red]KHO KHÔNG AN TOÀN[/]'}[/]\n"
            f"  Trạng thái an ninh:       [bold {color}]{res['security_status']}[/]\n"
            + (f"  Hành vi vi phạm:          [bold red]{'; '.join(res['violations'])}[/]" if res["violations"] else "  Đánh giá:                 [bold green]An ninh nguồn phóng xạ bảo đảm tuyệt đối theo quy chuẩn quốc gia[/]"),
            title=f"[bold {color}]Radioactive Source Security Inspection[/]",
            border_style=color,
        )
    )


@radiation_app.command("xray")
def xray_cmd(
    clinic: str = typer.Argument(..., help="Tên phòng khám hoặc bệnh viện sở hữu máy"),
    model: str = typer.Option("Siemens Multix Impact", "--model", "-m", help="Model / Hãng sản xuất máy X-quang"),
    mach_type: str = typer.Option("CONVENTIONAL_XRAY", "--type", "-t", help="Loại máy: CONVENTIONAL_XRAY, CT_SCANNER, MAMMOGRAPHY, DENTAL_XRAY"),
    kvp: float = typer.Option(3.5, "--kvp", help="Độ sai số điện áp phát tia kVp (%) - Chuẩn <= +-10%"),
    timer: float = typer.Option(4.0, "--timer", help="Độ sai số thời gian phát tia (%) - Chuẩn <= +-10%"),
    lead: float = typer.Option(2.0, "--lead", help="Chiều dày chì che chắn phòng (mm Pb) - Chuẩn >= 2.0 mm Pb"),
    inspection_months: int = typer.Option(8, "--months", help="Số tháng kể từ lần kiểm định gần nhất - Chuẩn 12 tháng (Răng: 24 tháng)"),
    warning_light: bool = typer.Option(True, "--light/--no-light", help="Đèn tín hiệu cảnh báo phát tia hoạt động"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra kiểm định định kỳ và đảm bảo chất lượng (QA) máy X-quang y tế theo TTLT 13/2014/TTLT-BKHCN-BYT."""
    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    res = engine.inspect_medical_xray_machine(
        clinic_name=clinic,
        machine_model=model,
        machine_type=mach_type,
        kvp_accuracy_pct=kvp,
        timer_accuracy_pct=timer,
        lead_shielding_thickness_mm=lead,
        last_inspection_months_ago=inspection_months,
        warning_light_operational=warning_light,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KIỂM ĐỊNH & ĐẢM BẢO CHẤT LƯỢNG MÁY X-QUANG Y TẾ (TTLT 13/2014)[/]\n\n"
            f"  Mã kiểm định QA:          [bold cyan]{res['inspection_id']}[/]\n"
            f"  Cơ sở y tế:               [bold]{res['clinic_name']}[/]\n"
            f"  Thiết bị kiểm định:       [cyan]{res['machine_model']}[/] ([white]{res['machine_type']}[/])\n"
            f"  Độ chính xác điện áp:     [white]{res['kvp_accuracy_pct']}%[/] ({'ĐẠT <= +-10%' if abs(res['kvp_accuracy_pct']) <= 10.0 else '[bold red]SAI SỐ CAO[/]'})\n"
            f"  Độ chính xác thời gian:   [white]{res['timer_accuracy_pct']}%[/] ({'ĐẠT <= +-10%' if abs(res['timer_accuracy_pct']) <= 10.0 else '[bold red]SAI SỐ CAO[/]'})\n"
            f"  Che chắn chì phòng chụp:  [white]{res['lead_shielding_thickness_mm']} mm Pb[/] ({'ĐẠT CHUẨN' if res['lead_shielding_thickness_mm'] >= 2.0 else '[bold red]THIẾU CHIỀU DÀY CHÌ[/]'})\n"
            f"  Thời hạn kiểm định:       [white]{res['last_inspection_months_ago']} tháng[/] ({'CÒN HẠN' if res['last_inspection_months_ago'] <= 12 else '[bold red]QUÁ HẠN KIỂM ĐỊNH[/]'})\n"
            f"  Đèn báo phát tia:         [white]{'HOẠT ĐỘNG' if res['warning_light_operational'] else '[bold red]HỎNG ĐÈN CẢNH BÁO[/]'}[/]\n"
            f"  Đánh giá kiểm định:       [bold {color}]{res['qa_rating']}[/]\n"
            + (f"  Nội dung thiếu sót:       [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Kết luận:                 [bold green]Thiết bị đạt đầy đủ tiêu chuẩn kiểm định an toàn bức xạ y tế[/]"),
            title=f"[bold {color}]Medical X-Ray QA Inspection[/]",
            border_style=color,
        )
    )


@radiation_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'facilities', 'dosimetry', 'sources', 'xray'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ cấp phép bức xạ, đo liều cá nhân, an ninh nguồn và kiểm định X-quang."""
    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if not records:
        console.print(f"[yellow]Không có dữ liệu trong danh mục '{category}'.[/]")
        return

    table = Table(title=f"Danh mục hồ sơ an toàn bức xạ & nguồn phóng xạ ({category})")
    table.add_column("Loại hồ sơ", style="cyan")
    table.add_column("Mã hồ sơ", style="bold")
    table.add_column("Tên cơ sở / Nhân viên / Nguồn", style="green")
    table.add_column("Kết quả / Trạng thái", style="yellow")
    table.add_column("Thời gian khởi tạo", style="white")

    for r in records:
        rtype = r.get("type", "")
        if rtype == "facility_license":
            table.add_row(
                "Cấp phép cơ sở",
                r["license_id"],
                r["facility_name"],
                "Đủ điều kiện" if r["is_eligible"] else "Thiếu điều kiện",
                r["created_at"][:19],
            )
        elif rtype == "personal_dosimetry":
            table.add_row(
                "Liều kế cá nhân",
                r["record_id"],
                f"{r['employee_name']} (Q{r['quarter']}/{r['year']})",
                f"{r['effective_dose_mSv']} mSv ({r['status'][:30]})",
                r["created_at"][:19],
            )
        elif rtype == "source_security":
            table.add_row(
                "An ninh nguồn",
                r["audit_id"],
                f"{r['source_serial']} ({r['isotope']})",
                r["security_status"][:35],
                r["created_at"][:19],
            )
        elif rtype == "xray_inspection":
            table.add_row(
                "Kiểm định X-quang",
                r["inspection_id"],
                f"{r['clinic_name']} - {r['machine_model']}",
                r["qa_rating"][:35],
                r["created_at"][:19],
            )

    console.print(table)


@radiation_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp hệ thống an toàn bức xạ và an ninh nguồn phóng xạ quốc gia."""
    from src.core.radiation_engine import RadiationEngine

    engine = RadiationEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold magenta]TELEMETRY AN TOÀN BỨC XẠ & AN NINH HẠT NHÂN[/]\n\n"
            f"  Trạng thái:                [bold green]{data['status'].upper()}[/]\n"
            f"  Cơ sở bức xạ kiểm tra:     [bold]{data['total_licensed_facilities']}[/] ([bold green]{data['compliant_licensed_facilities']}[/] đủ điều kiện)\n"
            f"  Hồ sơ liều kế theo dõi:    [bold cyan]{data['personal_dosimetry_records_count']}[/] lượt đo đọc\n"
            f"  Nguồn phóng xạ giám sát:   [bold]{data['monitored_radioactive_sources']}[/] nguồn ([bold green]{data['gps_active_radioactive_sources']}[/] kết nối GPS)\n"
            f"  Máy X-quang y tế QA:       [bold]{data['medical_xray_machines_inspected']}[/] máy ([bold green]{data['compliant_medical_xray_machines']}[/] đạt chuẩn)\n"
            f"  Cơ sở dữ liệu SQLite WAL:  [white]{data['db_path']}[/]",
            title="[bold magenta]Radiation Safety Telemetry Status[/]",
            border_style="magenta",
        )
    )
