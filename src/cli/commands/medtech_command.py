# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials (Phase 70)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
medtech_app = typer.Typer(
    name="medtech",
    help="MedTech — Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials",
    add_completion=False,
)


@medtech_app.callback(invoke_without_command=True)
def medtech_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Trang thiết bị y tế, Cấp phép Cơ sở Y tế & Đánh giá Thử nghiệm Lâm sàng."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ TRANG THIẾT BỊ Y TẾ & GIẤY PHÉP KHÁM CHỮA BỆNH (NĐ 98/2021 & NĐ 07/2023)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Trang thiết bị y tế: [bold cyan]{m['registered_medical_devices']} thiết bị[/] (Miễn thử nghiệm lâm sàng CFS: [bold green]{m['clinical_trial_exempt_devices']}[/])\n"
            f"  Kê khai giá thiết bị:[bold]{m['price_declarations_filed']} hồ sơ kê khai[/] (Hợp lệ biên lợi nhuận <= 35%: [bold green]{m['compliant_price_declarations']}[/])\n"
            f"  Cơ sở khám chữa bệnh:[bold]{m['healthcare_facilities_evaluated']} cơ sở thẩm định[/] (Được cấp giấy phép: [bold green]{m['licensed_healthcare_facilities']}[/] | Tổng số giường bệnh: [bold cyan]{m['total_hospital_beds_licensed']:,} giường[/])\n"
            f"  Thử nghiệm lâm sàng: [bold]{m['clinical_trials_initiated']} đề cương[/] (Đang thu nhận bệnh nhân: [bold yellow]{m['active_enrolling_trials']}[/])",
            title="[bold blue]Vietnam MedTech & Healthcare Regulatory Telemetry Control Center[/]",
            border_style="cyan",
        )
    )


@medtech_app.command("device")
def device_cmd(
    name: str = typer.Argument(..., help="Tên trang thiết bị y tế"),
    risk_class: str = typer.Option("CLASS_B", "--class", "-c", help="Phân loại rủi ro: CLASS_A, CLASS_B, CLASS_C, CLASS_D"),
    maker: str = typer.Option("Siemens Healthineers", "--maker", "-m", help="Nhà sản xuất"),
    origin: str = typer.Option("Germany", "--origin", help="Nước xuất xứ"),
    importer: str = typer.Option("Công ty TNHH Thiết Bị Y Tế Sài Gòn", "--importer", "-i", help="Doanh nghiệp đứng tên đăng ký lưu hành"),
    use: str = typer.Option("Hệ thống siêu âm màu Doppler chẩn đoán tim mạch", "--use", "-u", help="Mục đích sử dụng"),
    cfs: typing.Optional[str] = typer.Option("CE", "--cfs", help="Cơ quan tham chiếu đã cấp phép CFS: FDA, CE, PMDA, TGA, HEALTH_CANADA"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Phân loại rủi ro và đăng ký số lưu hành trang thiết bị y tế theo Nghị định 98/2021/NĐ-CP."""
    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    result = engine.register_medical_device(
        device_name=name,
        risk_class=risk_class,
        manufacturer=maker,
        country_of_origin=origin,
        importer_name=importer,
        intended_use=use,
        reference_cfs=cfs,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["device_profile"]
    table = Table(title=f"Hồ Sơ Đăng Ký Lưu Hành Trang Thiết Bị Y Tế — {prof['device_name']} ({result['device_id']})")
    table.add_column("Chỉ tiêu quản lý trang thiết bị y tế", style="cyan")
    table.add_column("Thông số & Kết quả thẩm định", justify="right", style="bold green")

    table.add_row("Tên trang thiết bị", prof["device_name"])
    table.add_row("Phân loại rủi ro", prof["risk_description"])
    table.add_row("Cơ quan cấp phép", prof["licensing_authority"])
    table.add_row("Hình thức quản lý", prof["approval_type"])
    table.add_row("Số lưu hành / Công bố", f"[bold yellow]{prof['market_auth_number']}[/]")
    table.add_row("Thời hạn hiệu lực", prof["validity_period"])
    table.add_row("Chứng chỉ tham chiếu (CFS)", prof["reference_cfs_agency"])
    table.add_row("Đánh giá thử nghiệm lâm sàng", "[bold green]MIỄN THỬ NGHIỆM LÂM SÀNG[/]" if prof["is_clinical_trial_exempt"] else "[bold red]BẮT BUỘC THỬ LÂM SÀNG[/]")
    table.add_row("Lý do pháp lý", prof["exemption_reason"])
    table.add_row("Thời gian xử lý quy định", f"{prof['statutory_review_days']} ngày làm việc")

    console.print(table)


@medtech_app.command("price")
def price_cmd(
    device_id: str = typer.Argument(..., help="Mã thiết bị y tế (DEV-xxxx)"),
    name: str = typer.Argument(..., help="Tên thương mại thiết bị y tế"),
    cif: float = typer.Option(..., "--cif", "-c", help="Giá vốn nhập khẩu CIF hoặc giá thành sản xuất (VND)"),
    wholesale: float = typer.Option(..., "--wholesale", "-w", help="Giá bán buôn dự kiến kê khai (VND)"),
    retail: float = typer.Option(..., "--retail", "-r", help="Giá bán lẻ tối đa dự kiến (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kê khai giá và kiểm soát biên lợi nhuận trang thiết bị y tế theo Nghị định 07/2023/NĐ-CP."""
    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    result = engine.declare_device_price(
        device_id=device_id,
        device_name=name,
        cif_cost_vnd=cif,
        wholesale_price_vnd=wholesale,
        retail_price_vnd=retail,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    p = result["price_declaration"]
    table = Table(title=f"Kê Khai Giá Trang Thiết Bị Y Tế — {p['device_name']} ({result['declaration_id']})")
    table.add_column("Chỉ số kê khai giá", style="cyan")
    table.add_column("Giá trị kê khai (VND)", justify="right", style="bold")

    table.add_row("Mã thiết bị", p["device_id"])
    table.add_row("Giá vốn CIF / Giá thành", f"{p['cif_cost_vnd']:,.0f} VND")
    table.add_row("Giá bán buôn dự kiến", f"{p['wholesale_price_vnd']:,.0f} VND")
    table.add_row("Giá bán lẻ tối đa", f"{p['retail_price_vnd']:,.0f} VND")
    table.add_row("Biên lợi nhuận bán buôn", f"[bold yellow]{p['markup_percentage']:.2f}%[/]")
    table.add_row("Mức trần biên độ theo NĐ 07", f"{p['statutory_markup_cap_pct']:.1f}%")
    table.add_row("Đánh giá hợp lệ", "[bold green]HỢP LỆ — ĐỦ ĐIỀU KIỆN NIÊM YẾT CỔNG BYT[/]" if p["is_markup_compliant"] else "[bold red]VƯỢT TRẦN LỢI NHUẬN ĐỊNH MỨC[/]")

    console.print(table)


@medtech_app.command("facility")
def facility_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở khám bệnh, chữa bệnh"),
    fac_type: str = typer.Option("GENERAL_HOSPITAL", "--type", "-t", help="Loại cơ sở: GENERAL_HOSPITAL, SPECIALIZED_HOSPITAL, POLYCLINIC, SPECIALIZED_CLINIC"),
    province: str = typer.Option("Hà Nội", "--province", "-p", help="Tỉnh / Thành phố"),
    beds: int = typer.Option(100, "--beds", "-b", help="Quy mô giường bệnh nội trú"),
    area: float = typer.Option(6000.0, "--area", "-a", help="Tổng diện tích sàn xây dựng (m2)"),
    cmo: str = typer.Option("PGS.TS. Trần Quốc Tuấn", "--cmo", help="Bác sĩ phụ trách chuyên môn kỹ thuật"),
    months: int = typer.Option(60, "--months", "-m", help="Số tháng hành nghề khám chữa bệnh của người phụ trách"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện cấp giấy phép hoạt động cơ sở y tế theo Luật Khám bệnh, chữa bệnh 2023."""
    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    result = engine.evaluate_facility_license(
        facility_name=name,
        facility_type=fac_type,
        province=province,
        bed_capacity=beds,
        total_floor_area_m2=area,
        chief_medical_officer=cmo,
        cmo_practice_months=months,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    f = result["facility_evaluation"]
    table = Table(title=f"Thẩm Định Giấy Phép Hoạt Động Y Tế — {f['facility_name']} ({result['facility_id']})")
    table.add_column("Tiêu chí điều kiện pháp lý", style="cyan")
    table.add_column("Kết quả thẩm tra", justify="right", style="bold")
    table.add_column("Chuẩn Luật 15/2023", justify="center")
    table.add_column("Đánh giá", justify="center")

    table.add_row("Hình thức tổ chức", f["facility_type_vi"], f["facility_type"], "[bold green]HỢP LỆ[/]")
    table.add_row("Quy mô giường bệnh", f"{f['bed_capacity']} giường", f">={f['min_beds_required']} giường", "[bold green]ĐẠT[/]" if f["bed_capacity_compliant"] else "[bold red]THIẾU GIƯỜNG[/]")
    table.add_row("Diện tích sàn bình quân", f"{f['floor_m2_per_bed']:.1f} m2/giường", ">= 50 m2/giường" if f["min_beds_required"] > 0 else ">= 40 m2", "[bold green]ĐẠT[/]" if f["floor_area_compliant"] else "[bold red]CHẬT HẸP[/]")
    table.add_row("Thâm niên bác sĩ CCHN", f"{f['cmo_practice_months']} tháng", f">={f['min_cmo_practice_months']} tháng", "[bold green]ĐẠT[/]" if f["cmo_qualification_compliant"] else "[bold red]CHƯA ĐỦ THÂM NIÊN[/]")
    table.add_row("Số giấy phép hoạt động", f"[bold yellow]{f['operating_license_no']}[/]", "Cấp mã định danh", "[bold green]CẤP PHÉP[/]" if f["is_license_approved"] else "[bold red]TỪ CHỐI[/]")

    console.print(table)


@medtech_app.command("trial")
def trial_cmd(
    device_id: str = typer.Argument(..., help="Mã trang thiết bị y tế (DEV-xxxx)"),
    title: str = typer.Argument(..., help="Tên đề cương nghiên cứu thử nghiệm lâm sàng"),
    phase: int = typer.Option(2, "--phase", help="Giai đoạn thử nghiệm lâm sàng (1, 2, hoặc 3)"),
    pi: str = typer.Option("GS.TS. Phạm Nhật An", "--pi", help="Chủ nhiệm đề tài nghiên cứu lâm sàng"),
    site: str = typer.Option("Bệnh viện Đại học Y Dược TP.HCM", "--site", help="Cơ sở nghiên cứu thử nghiệm"),
    subjects: int = typer.Option(120, "--subjects", "-s", help="Cỡ mẫu đối tượng tham gia thử nghiệm"),
    irb: bool = typer.Option(True, "--irb/--no-irb", help="Đã được Hội đồng Đạo đức trong nghiên cứu y sinh học phê duyệt"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký đề cương thử nghiệm lâm sàng trang thiết bị y tế theo Thông tư 29/2023/TT-BYT."""
    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    result = engine.submit_clinical_trial_protocol(
        device_id=device_id,
        trial_title=title,
        trial_phase=phase,
        principal_investigator=pi,
        study_site=site,
        target_subjects=subjects,
        irb_approved=irb,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    t = result["trial_profile"]
    table = Table(title=f"Đề Cương Thử Nghiệm Lâm Sàng Trang Thiết Bị Y Tế — {result['trial_id']}")
    table.add_column("Chỉ tiêu nghiên cứu lâm sàng", style="cyan")
    table.add_column("Thông số phê duyệt", justify="right", style="bold")

    table.add_row("Mã thiết bị y tế", t["device_id"])
    table.add_row("Tên đề cương", t["trial_title"])
    table.add_row("Giai đoạn nghiên cứu", f"Phase {t['trial_phase']}")
    table.add_row("Mô tả giai đoạn", t["phase_description"])
    table.add_row("Chủ nhiệm đề tài (PI)", t["principal_investigator"])
    table.add_row("Địa điểm thử nghiệm", t["study_site"])
    table.add_row("Cỡ mẫu đối tượng", f"{t['target_subjects']} người bệnh")
    table.add_row("Phê duyệt Hội đồng Đạo đức (IRB)", "[bold green]ĐÃ PHÊ DUYỆT[/]" if t["is_irb_approved"] else "[bold red]CHỜ PHÊ DUYỆT[/]")
    table.add_row("Mã số IRB quốc gia", t["irb_approval_code"])
    table.add_row("Trạng thái thử nghiệm", f"[bold yellow]{t['status']}[/]")

    console.print(table)


@medtech_app.command("list")
def list_cmd(
    category: str = typer.Argument("devices", help="Danh mục: devices (thiết bị), prices (kê khai giá), facilities (cơ sở y tế), trials (thử nghiệm lâm sàng)"),
    limit: int = typer.Option(50, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh sách thiết bị y tế, hồ sơ kê khai giá, cơ sở khám chữa bệnh hoặc thử nghiệm lâm sàng."""
    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    cat = category.lower().strip()

    if cat in ("devices", "device"):
        records = engine.list_medical_devices(limit=limit)
        key = "medical_devices"
    elif cat in ("prices", "price"):
        records = engine.list_price_declarations(limit=limit)
        key = "price_declarations"
    elif cat in ("facilities", "facility"):
        records = engine.list_healthcare_facilities(limit=limit)
        key = "healthcare_facilities"
    elif cat in ("trials", "trial"):
        records = engine.list_clinical_trials(limit=limit)
        key = "clinical_trials"
    else:
        records = engine.list_medical_devices(limit=limit)
        key = "medical_devices"

    if json_mode:
        typer.echo(json.dumps({key: records.data}, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh Sách Dữ Liệu Y Tế & Trang Thiết Bị ({category.upper()}) — {len(records)} Bản Ghi")
    if records:
        for k in records[0].keys():
            table.add_column(k, style="cyan")
        for item in records:
            table.add_row(*[str(item[k]) for k in item.keys()])
    else:
        table.add_column("Thông báo", style="yellow")
        table.add_row("Chưa có bản ghi nào được ghi nhận.")

    console.print(table)


@medtech_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Báo cáo tổng quan hệ thống trang thiết bị y tế, giá kê khai và cơ sở khám chữa bệnh."""
    from src.core.medtech_engine import MedtechEngine

    engine = MedtechEngine()
    data = engine.get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    table = Table(title="Tổng Quan Quản Lý Y Tế & Trang Thiết Bị (MedTech Telemetry)")
    table.add_column("Chỉ số đo lường", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Trang thiết bị y tế đã đăng ký", str(m["registered_medical_devices"]))
    table.add_row("Thiết bị miễn thử nghiệm lâm sàng (CFS)", str(m["clinical_trial_exempt_devices"]))
    table.add_row("Hồ sơ kê khai giá trang thiết bị", str(m["price_declarations_filed"]))
    table.add_row("Hồ sơ kê khai giá hợp lệ (<= 35%)", str(m["compliant_price_declarations"]))
    table.add_row("Cơ sở khám chữa bệnh đã thẩm định", str(m["healthcare_facilities_evaluated"]))
    table.add_row("Cơ sở y tế được cấp phép hoạt động", str(m["licensed_healthcare_facilities"]))
    table.add_row("Tổng số giường bệnh nội trú", f"{m['total_hospital_beds_licensed']:,}")
    table.add_row("Đề cương thử nghiệm lâm sàng đã tạo", str(m["clinical_trials_initiated"]))
    table.add_row("Thử nghiệm lâm sàng đang hoạt động", str(m["active_enrolling_trials"]))

    console.print(table)
