# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MedTech command record-table construction — Chỉ số / Giá trị layouts.

Keeps the Vietnamese column headers, titles and status colours of the MedTech
suite local while delegating the repeated table shapes to the shared builders,
so medtech_command.py stays within the file-size limit.
"""

from __future__ import annotations

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_key_value_table as _kv


def build_device_table(device_name: str, device_id: str, prof: dict) -> Table:
    """Build the medical-device registration profile table; the caller prints it."""
    rows = (
        ("Tên trang thiết bị", prof["device_name"]),
        ("Phân loại rủi ro", prof["risk_description"]),
        ("Cơ quan cấp phép", prof["licensing_authority"]),
        ("Hình thức quản lý", prof["approval_type"]),
        ("Số lưu hành / Công bố", f"[bold yellow]{prof['market_auth_number']}[/]"),
        ("Thời hạn hiệu lực", prof["validity_period"]),
        ("Chứng chỉ tham chiếu (CFS)", prof["reference_cfs_agency"]),
        ("Đánh giá thử nghiệm lâm sàng", "[bold green]MIỄN THỬ NGHIỆM LÂM SÀNG[/]" if prof["is_clinical_trial_exempt"] else "[bold red]BẮT BUỘC THỬ LÂM SÀNG[/]"),
        ("Lý do pháp lý", prof["exemption_reason"]),
        ("Thời gian xử lý quy định", f"{prof['statutory_review_days']} ngày làm việc"),
    )
    return _kv(
        f"Hồ Sơ Đăng Ký Lưu Hành Trang Thiết Bị Y Tế — {device_name} ({device_id})",
        rows,
        "cyan",
        headers=("Chỉ tiêu quản lý trang thiết bị y tế", "Thông số & Kết quả thẩm định"),
        value_style="bold green",
        justify_value=True,
    )


def build_price_table(declaration_id: str, p: dict) -> Table:
    """Build the device price-declaration table; the caller prints it."""
    rows = (
        ("Mã thiết bị", p["device_id"]),
        ("Giá vốn CIF / Giá thành", f"{p['cif_cost_vnd']:,.0f} VND"),
        ("Giá bán buôn dự kiến", f"{p['wholesale_price_vnd']:,.0f} VND"),
        ("Giá bán lẻ tối đa", f"{p['retail_price_vnd']:,.0f} VND"),
        ("Biên lợi nhuận bán buôn", f"[bold yellow]{p['markup_percentage']:.2f}%[/]"),
        ("Mức trần biên độ theo NĐ 07", f"{p['statutory_markup_cap_pct']:.1f}%"),
        ("Đánh giá hợp lệ", "[bold green]HỢP LỆ — ĐỦ ĐIỀU KIỆN NIÊM YẾT CỔNG BYT[/]" if p["is_markup_compliant"] else "[bold red]VƯỢT TRẦN LỢI NHUẬN ĐỊNH MỨC[/]"),
    )
    return _kv(
        f"Kê Khai Giá Trang Thiết Bị Y Tế — {p['device_name']} ({declaration_id})",
        rows,
        "cyan",
        headers=("Chỉ số kê khai giá", "Giá trị kê khai (VND)"),
        value_style="bold",
        justify_value=True,
    )


def build_facility_table(facility_id: str, f: dict) -> Table:
    """Build the healthcare-facility licensing evaluation table; the caller prints it."""
    rows = (
        ("Hình thức tổ chức", f["facility_type_vi"], f["facility_type"], "[bold green]HỢP LỆ[/]"),
        ("Quy mô giường bệnh", f"{f['bed_capacity']} giường", f">={f['min_beds_required']} giường", "[bold green]ĐẠT[/]" if f["bed_capacity_compliant"] else "[bold red]THIẾU GIƯỜNG[/]"),
        ("Diện tích sàn bình quân", f"{f['floor_m2_per_bed']:.1f} m2/giường", ">= 50 m2/giường" if f["min_beds_required"] > 0 else ">= 40 m2", "[bold green]ĐẠT[/]" if f["floor_area_compliant"] else "[bold red]CHẬT HẸP[/]"),
        ("Thâm niên bác sĩ CCHN", f"{f['cmo_practice_months']} tháng", f">={f['min_cmo_practice_months']} tháng", "[bold green]ĐẠT[/]" if f["cmo_qualification_compliant"] else "[bold red]CHƯA ĐỦ THÂM NIÊN[/]"),
        ("Số giấy phép hoạt động", f"[bold yellow]{f['operating_license_no']}[/]", "Cấp mã định danh", "[bold green]CẤP PHÉP[/]" if f["is_license_approved"] else "[bold red]TỪ CHỐI[/]"),
    )
    table = Table(title=f"Thẩm Định Giấy Phép Hoạt Động Y Tế — {f['facility_name']} ({facility_id})")
    for col, just in (("Tiêu chí điều kiện pháp lý", "left"), ("Kết quả thẩm tra", "right"), ("Chuẩn Luật 15/2023", "center"), ("Đánh giá", "center")):
        table.add_column(col, justify=just)
    for row in rows:
        table.add_row(*row)
    return table


def build_trial_table(trial_id: str, t: dict) -> Table:
    """Build the clinical-trial protocol table; the caller prints it."""
    rows = (
        ("Mã thiết bị y tế", t["device_id"]),
        ("Tên đề cương", t["trial_title"]),
        ("Giai đoạn nghiên cứu", f"Phase {t['trial_phase']} ({t['phase_description']})"),
        ("Chủ nhiệm đề tài (PI)", t["principal_investigator"]),
        ("Địa điểm thử nghiệm", t["study_site"]),
        ("Cỡ mẫu đối tượng", f"{t['target_subjects']} người bệnh"),
        ("Phê duyệt Hội đồng Đạo đức (IRB)", "[bold green]ĐÃ PHÊ DUYỆT[/]" if t["is_irb_approved"] else "[bold red]CHỜ PHÊ DUYỆT[/]"),
        ("Mã số IRB quốc gia", t["irb_approval_code"]),
        ("Trạng thái thử nghiệm", f"[bold yellow]{t['status']}[/]"),
    )
    return _kv(
        f"Đề Cương Thử Nghiệm Lâm Sàng Trang Thiết Bị Y Tế — {trial_id}",
        rows,
        "cyan",
        headers=("Chỉ tiêu nghiên cứu lâm sàng", "Thông số phê duyệt"),
        value_style="bold",
        justify_value=True,
    )


def build_records_table(category: str, records: list[dict]) -> Table:
    """Build the records listing table; the caller prints it."""
    table = Table(title=f"Danh Sách Dữ Liệu Y Tế & Trang Thiết Bị ({category.upper()}) — {len(records)} Bản Ghi")
    if records:
        for k in records[0].keys():
            table.add_column(k, style="cyan")
        for item in records:
            table.add_row(*[str(item[k]) for k in item.keys()])
    else:
        table.add_column("Thông báo", style="yellow")
        table.add_row("Chưa có bản ghi nào được ghi nhận.")
    return table


def build_status_table(m: dict) -> Table:
    """Build the Telemetry overview table; the caller prints it."""
    rows = (
        ("Trang thiết bị y tế đã đăng ký", str(m["registered_medical_devices"])),
        ("Thiết bị miễn thử nghiệm lâm sàng (CFS)", str(m["clinical_trial_exempt_devices"])),
        ("Hồ sơ kê khai giá trang thiết bị", str(m["price_declarations_filed"])),
        ("Hồ sơ kê khai giá hợp lệ (<= 35%)", str(m["compliant_price_declarations"])),
        ("Cơ sở khám chữa bệnh đã thẩm định", str(m["healthcare_facilities_evaluated"])),
        ("Cơ sở y tế được cấp phép hoạt động", str(m["licensed_healthcare_facilities"])),
        ("Tổng số giường bệnh nội trú", f"{m['total_hospital_beds_licensed']:,}"),
        ("Đề cương thử nghiệm lâm sàng đã tạo", str(m["clinical_trials_initiated"])),
        ("Thử nghiệm lâm sàng đang hoạt động", str(m["active_enrolling_trials"])),
    )
    return _kv(
        "Tổng Quan Quản Lý Y Tế & Trang Thiết Bị (MedTech Telemetry)",
        rows,
        "cyan",
        headers=("Chỉ số đo lường", "Giá trị"),
        value_style="bold green",
        justify_value=True,
    )
