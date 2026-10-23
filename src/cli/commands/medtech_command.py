# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials (Phase 70)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from src.cli.commands.medtech_commands_records_table import (
    build_device_table,
    build_facility_table,
    build_price_table,
    build_records_table,
    build_status_table,
    build_trial_table,
)

console = Console()
medtech_app = typer.Typer(name="medtech", help="MedTech — Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials", add_completion=False)


@medtech_app.callback(invoke_without_command=True)
def medtech_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON")) -> None:
    """Hệ thống Quản lý Trang thiết bị y tế, Cấp phép Cơ sở Y tế & Đánh giá Thử nghiệm Lâm sàng."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.medtech_engine import MedtechEngine
    status_data = MedtechEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    m = status_data["metrics"]
    console.print(Panel(
        f"[bold green]HỆ THỐNG QUẢN LÝ TRANG THIẾT BỊ Y TẾ & GIẤY PHÉP KHÁM CHỮA BỆNH (NĐ 98/2021 & NĐ 07/2023)[/]\n\n"
        f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
        f"  Trang thiết bị y tế: [bold cyan]{m['registered_medical_devices']} thiết bị[/] (Miễn thử nghiệm lâm sàng CFS: [bold green]{m['clinical_trial_exempt_devices']}[/])\n"
        f"  Kê khai giá thiết bị:[bold]{m['price_declarations_filed']} hồ sơ kê khai[/] (Hợp lệ biên lợi nhuận <= 35%: [bold green]{m['compliant_price_declarations']}[/])\n"
        f"  Cơ sở khám chữa bệnh:[bold]{m['healthcare_facilities_evaluated']} cơ sở thẩm định[/] (Được cấp giấy phép: [bold green]{m['licensed_healthcare_facilities']}[/] | Tổng số giường bệnh: [bold cyan]{m['total_hospital_beds_licensed']:,} giường[/])\n"
        f"  Thử nghiệm lâm sàng: [bold]{m['clinical_trials_initiated']} đề cương[/] (Đang thu nhận bệnh nhân: [bold yellow]{m['active_enrolling_trials']}[/])",
        title="[bold blue]Vietnam MedTech & Healthcare Regulatory Telemetry Control Center[/]", border_style="cyan",
    ))


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
    result = MedtechEngine().register_medical_device(device_name=name, risk_class=risk_class, manufacturer=maker, country_of_origin=origin, importer_name=importer, intended_use=use, reference_cfs=cfs)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    prof = result["device_profile"]
    console.print(build_device_table(prof["device_name"], result["device_id"], prof))


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
    result = MedtechEngine().declare_device_price(device_id=device_id, device_name=name, cif_cost_vnd=cif, wholesale_price_vnd=wholesale, retail_price_vnd=retail)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    p = result["price_declaration"]
    console.print(build_price_table(result["declaration_id"], p))


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
    result = MedtechEngine().evaluate_facility_license(facility_name=name, facility_type=fac_type, province=province, bed_capacity=beds, total_floor_area_m2=area, chief_medical_officer=cmo, cmo_practice_months=months)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    f = result["facility_evaluation"]
    console.print(build_facility_table(result["facility_id"], f))


@medtech_app.command("trial")
def trial_cmd(
    device_id: str = typer.Argument(..., help="Mã trang thiết bị y tế (DEV-xxxx)"),
    title: str = typer.Argument(..., help="Tên đề cương nghiên cứu thử nghiệm lâm sàng"),
    phase: int = typer.Option(2, "--phase", help="Giai đoạn thử nghiệm lâm sàng (1, 2, hoặc 3)"),
    pi: str = typer.Option("GS.TS. Phạm Nhật An", "--pi", help="Chủ nhiệm đề tài nghiên cứu lâm sàng"),
    site: str = typer.Option("Bệnh viện Đại học Y Dược TP.HCM", "--site", help="Cơ sở nghiên cứu thử nghiệm"),
    subjects: int = typer.Option(120, "--subjects", "-s", help="Cỡ mẫu đối tượng tham gia thử nghiệm"),
    irb: bool = typer.Option(True, "--irb/--no-irb", help="Đã được Hội đồng Đạo đức phê duyệt"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đăng ký đề cương thử nghiệm lâm sàng trang thiết bị y tế theo Thông tư 29/2023/TT-BYT."""
    from src.core.medtech_engine import MedtechEngine
    result = MedtechEngine().submit_clinical_trial_protocol(device_id=device_id, trial_title=title, trial_phase=phase, principal_investigator=pi, study_site=site, target_subjects=subjects, irb_approved=irb)
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return
    t = result["trial_profile"]
    console.print(build_trial_table(result["trial_id"], t))


@medtech_app.command("list")
def list_cmd(category: str = typer.Argument("devices", help="Danh mục: devices, prices, facilities, trials"), limit: int = typer.Option(50, "--limit", "-n", help="Số lượng bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON")) -> None:
    """Tra cứu danh sách thiết bị y tế, hồ sơ kê khai giá, cơ sở khám chữa bệnh hoặc thử nghiệm lâm sàng."""
    from src.core.medtech_engine import MedtechEngine
    engine, cat = MedtechEngine(), category.lower().strip()
    records, key = (engine.list_price_declarations(limit=limit), "price_declarations") if cat in ("prices", "price") else ((engine.list_healthcare_facilities(limit=limit), "healthcare_facilities") if cat in ("facilities", "facility") else ((engine.list_clinical_trials(limit=limit), "clinical_trials") if cat in ("trials", "trial") else (engine.list_medical_devices(limit=limit), "medical_devices")))
    if json_mode:
        typer.echo(json.dumps({key: records.data}, indent=2, ensure_ascii=False))
        return
    console.print(build_records_table(category, records))


@medtech_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON")) -> None:
    """Báo cáo tổng quan hệ thống trang thiết bị y tế, giá kê khai và cơ sở khám chữa bệnh."""
    from src.core.medtech_engine import MedtechEngine
    data = MedtechEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    m = data["metrics"]
    console.print(build_status_table(m))
