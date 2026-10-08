"""Typer CLI Commands for Maritime ISM Safety, Green Ship Recycling,

Port Reception Waste & ISPS Port Security Suite (Phases 243-246).

Statutory Frameworks:
- Phase 243: SOLAS Ch. IX & IMO ISM Code (DOC/SMC, DPA Audits, Major NC Downgrade, Emergency Drills)
- Phase 244: Hong Kong Convention 2009 (HKC) & LEP 2020 (IHM Table A/B, LDT Scrap Steel Yield, Salvage)
- Phase 245: MARPOL Annexes I-VI, Circular 39/2023 & Circular 41/2020 (AWN 24h Notice, No-Special-Fee Tariffs)
- Phase 246: ISPS Code Parts A & B, Decree 58/2017 & Decision 22/2017 (Security Levels 1-3, DoS, TVC Risk Index)
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_ism_recycling_waste_isps_engine import (
    GreenShipRecyclingIhmEngine,
    IhmMaterialCategory,
    IhmMaterialFinding,
    IsmCertificateType,
    IsmSafetyManagementEngine,
    IspsPortSecurityEngine,
    MaritimeSecurityLevel,
    PortReceptionWasteEngine,
)

console = Console()

ismsafety_app = typer.Typer(
    name="ismsafety",
    help="Hệ thống Quản lý An toàn Tàu biển ISM Code & Giám sát DPA (Phase 243)",
    no_args_is_help=True,
)

shiprecycling_app = typer.Typer(
    name="shiprecycling",
    help="Tái chế Tàu biển Xanh, Kiểm kê Vật liệu Nguy hại IHM theo Công ước HKC 2009 (Phase 244)",
    no_args_is_help=True,
)

portwaste_app = typer.Typer(
    name="portwaste",
    help="Tiếp nhận Chất thải Tàu biển tại Cảng & Biểu giá Gián tiếp Thông tư 39/2023 (Phase 245)",
    no_args_is_help=True,
)

ispssecurity_app = typer.Typer(
    name="ispssecurity",
    help="An ninh Cảng biển & Tàu biển ISPS Code, Tuyên bố An ninh DoS & Đánh giá Rủi ro TVC (Phase 246)",
    no_args_is_help=True,
)


# ==============================================================================
# PHASE 243 COMMANDS: ISM SAFETY MANAGEMENT & DPA AUDITS
# ==============================================================================

@ismsafety_app.command(name="check")
def ism_cert_check_cmd(
    cert_type: str = typer.Option("smc", "--type", "-t", help="Loại chứng chỉ: doc, smc, interim_doc, interim_smc"),
    cert_number: str = typer.Option("VN-SMC-2026-089", "--no", "-n", help="Số chứng nhận"),
    issue_date: str = typer.Option("2024-05-10", "--issue", "-i", help="Ngày cấp (YYYY-MM-DD)"),
    expiry_date: str = typer.Option("2029-05-09", "--expiry", "-e", help="Ngày hết hạn (YYYY-MM-DD)"),
    current_date: Optional[str] = typer.Option(None, "--cur-date", help="Ngày đánh giá (YYYY-MM-DD)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra hiệu lực chứng chỉ ISM (DOC/SMC) và thời hạn đánh giá định kỳ hàng năm/trung gian."""
    type_map = {
        "doc": IsmCertificateType.DOC,
        "smc": IsmCertificateType.SMC,
        "interim_doc": IsmCertificateType.INTERIM_DOC,
        "interim_smc": IsmCertificateType.INTERIM_SMC,
    }
    c_type = type_map.get(cert_type.lower(), IsmCertificateType.SMC)

    res = IsmSafetyManagementEngine.evaluate_certificate_validity(
        cert_type=c_type,
        cert_number=cert_number,
        issue_date_str=issue_date,
        expiry_date_str=expiry_date,
        current_date_str=current_date,
    )

    if as_json:
        console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
        return

    table = Table(title="KẾT QUẢ ĐÁNH GIÁ CHỨNG CHỈ QUẢN LÝ AN TOÀN ISM CODE", box=box.ROUNDED)
    table.add_column("Chỉ số / Tiêu chí", style="cyan")
    table.add_column("Giá trị", style="green" if res.is_valid else "red")

    table.add_row("Loại chứng chỉ", res.cert_type.value.upper())
    table.add_row("Số chứng chỉ", res.cert_number)
    table.add_row("Thời hạn hiệu lực", f"{res.issue_date} -> {res.expiry_date} ({res.days_to_expiry} ngày còn lại)")
    table.add_row("Tình trạng hiệu lực", "HỢP LỆ" if res.is_valid else "KHÔNG HỢP LỆ / HẾT HẠN")
    table.add_row("Cửa sổ đánh giá định kỳ", f"{res.audit_window_start} -> {res.audit_window_end}")
    table.add_row("Đang đến hạn đánh giá", "BẮT BUỘC ĐÁNH GIÁ NGAY" if res.audit_due else "Chưa đến hạn")
    table.add_row("Ghi chú luật định", res.remarks)

    console.print(table)


@ismsafety_app.command(name="audit")
def ism_audit_cmd(
    ship_name: str = typer.Option("MEKONG PRIDE", "--ship", "-s", help="Tên tàu"),
    imo: str = typer.Option("9876543", "--imo", help="Số IMO tàu"),
    major_nc: int = typer.Option(0, "--major-nc", help="Số lượng lỗi không phù hợp lớn (Major NC)"),
    minor_nc: int = typer.Option(2, "--minor-nc", help="Số lượng lỗi không phù hợp nhỏ (Minor NC)"),
    drills: int = typer.Option(11, "--drills", help="Số lượt thực tập khẩn cấp đã thực hiện"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá kết quả kiểm tra ISM SMS, xử lý Major NC đình chỉ tàu và kế hoạch khắc phục CAP."""
    findings = []
    for i in range(major_nc):
        findings.append({
            "clause": f"ISM 10.{i+1}",
            "description": f"Hỏng thiết bị an toàn trọng yếu chưa được khắc phục (Lỗi Major #{i+1})",
            "severity": "major_nc",
        })
    for i in range(minor_nc):
        findings.append({
            "clause": f"ISM 6.{i+1}",
            "description": f"Chưa cập nhật tài liệu quy trình SMS trên buồng lái (Lỗi Minor #{i+1})",
            "severity": "minor_nc",
        })

    res = IsmSafetyManagementEngine.evaluate_audit_findings(
        ship_name=ship_name,
        imo_number=imo,
        findings=findings,
        drills_conducted=drills,
        drills_required=12,
    )

    if as_json:
        console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
        return

    color = "red" if res.smc_suspended else "green"
    panel = Panel(
        f"[bold {color}]{res.audit_summary}[/bold {color}]\n"
        f"Major NC: {res.major_nc_count} | Minor NC: {res.minor_nc_count} | Quan sát: {res.observation_count}\n"
        f"Đình chỉ SMC: {'CÓ - NGUY CƠ LƯU GIỮ' if res.smc_suspended else 'KHÔNG'}\n"
        f"Thời hạn CAP khắc phục: {res.cap_deadline_days} ngày\n"
        f"Tỷ lệ hoàn thành thực tập: {res.drill_readiness_pct}%",
        title=f"KẾT QUẢ ĐÁNH GIÁ AN TOÀN TÀU {res.ship_name} (IMO: {res.imo_number})",
        box=box.DOUBLE,
    )
    console.print(panel)


# ==============================================================================
# PHASE 244 COMMANDS: GREEN SHIP RECYCLING & IHM VALUATION
# ==============================================================================

@shiprecycling_app.command(name="ihm")
def ihm_audit_cmd(
    asbestos_ppm: float = typer.Option(0.0, "--asbestos", help="Hàm lượng Amiăng (mg/kg hoặc ppm)"),
    pcb_ppm: float = typer.Option(10.0, "--pcb", help="Hàm lượng PCB (mg/kg)"),
    cybutryne_ppm: float = typer.Option(200.0, "--cybutryne", help="Sơn chống hà Cybutryne (mg/kg)"),
    cadmium_ppm: float = typer.Option(40.0, "--cadmium", help="Hàm lượng Cadmium Bảng B (mg/kg)"),
    lead_ppm: float = typer.Option(500.0, "--lead", help="Hàm lượng Chì Bảng B (mg/kg)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra tuân thủ Kiểm kê Vật liệu Nguy hại (IHM) theo Công ước Hồng Kông 2009."""
    samples = [
        {"material": IhmMaterialCategory.ASBESTOS.value, "location": "Nồi hơi/Vách cách nhiệt", "measured_mg_kg": asbestos_ppm, "estimated_mass_kg": 50.0 if asbestos_ppm > 0 else 0.0},
        {"material": IhmMaterialCategory.PCB.value, "location": "Dầu máy biến áp", "measured_mg_kg": pcb_ppm, "estimated_mass_kg": 20.0},
        {"material": IhmMaterialCategory.ANTI_FOULING_CYBUTRYNE.value, "location": "Lớp phủ vỏ ngầm", "measured_mg_kg": cybutryne_ppm, "estimated_mass_kg": 80.0},
        {"material": IhmMaterialCategory.CADMIUM.value, "location": "Ắc quy / mạ pin", "measured_mg_kg": cadmium_ppm, "estimated_mass_kg": 15.0},
        {"material": IhmMaterialCategory.LEAD.value, "location": "Lớp bọc cáp điện", "measured_mg_kg": lead_ppm, "estimated_mass_kg": 250.0},
    ]

    compliant, findings = GreenShipRecyclingIhmEngine.audit_ihm_materials(samples)

    if as_json:
        out = {
            "ihm_compliant": compliant,
            "findings": [f.__dict__ for f in findings],
        }
        console.print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    table = Table(title="KẾT QUẢ KIỂM TRA IHM - HONG KONG CONVENTION 2009", box=box.ROUNDED)
    table.add_column("Vật liệu", style="cyan")
    table.add_column("Vị trí", style="white")
    table.add_column("Đo được (mg/kg)", style="yellow")
    table.add_column("Ngưỡng cho phép", style="magenta")
    table.add_column("Phân loại", style="white")
    table.add_column("Kết luận", style="green")

    for f in findings:
        status_str = "[red]VƯỢT NGƯỠNG[/red]" if f.is_exceeded else "[green]ĐẠT[/green]"
        table.add_row(
            f.material.value,
            f.location,
            f"{f.measured_concentration_mg_kg:.1f}",
            f"{f.statutory_threshold_mg_kg:.1f}",
            "Bảng A (CẤM)" if f.is_table_a_prohibited else "Bảng B (Khai báo)",
            status_str,
        )

    console.print(table)
    summary_color = "green" if compliant else "red"
    console.print(f"[bold {summary_color}]KẾT LUẬN CHUNG: {'TUÂN THỦ IHM BẢNG A' if compliant else 'VI PHẠM VẬT LIỆU CẤM BẢNG A'}[/bold {summary_color}]")


@shiprecycling_app.command(name="salvage")
def recycling_salvage_cmd(
    ldt: float = typer.Option(8500.0, "--ldt", "-l", help="Trọng lượng tàu không tải LDT (tấn)"),
    steel_price: float = typer.Option(480.0, "--steel-price", help="Giá thép phế liệu (USD/tấn)"),
    haz_cost: float = typer.Option(650.0, "--haz-cost", help="Chi phí xử lý chất thải độc hại (USD/tấn)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán sản lượng thép tái chế, chi phí xử lý chất thải độc hại và giá trị thanh lý ròng."""
    # Run with empty sample findings (applies standard baseline)
    val = GreenShipRecyclingIhmEngine.calculate_recycling_valuation(
        ldt_tonnes=ldt,
        ihm_findings=[],
        steel_scrap_price_usd_tonne=steel_price,
        hazardous_treatment_tariff_usd_tonne=haz_cost,
    )

    if as_json:
        console.print(json.dumps(val.__dict__, indent=2, ensure_ascii=False))
        return

    table = Table(title="ĐỊNH GIÁ TÁI CHẾ TÀU BIỂN XANH (GREEN SHIP RECYCLING VALUATION)", box=box.ROUNDED)
    table.add_column("Chỉ tiêu kinh tế / kỹ thuật", style="cyan")
    table.add_column("Số lượng / Trọng lượng", style="yellow")
    table.add_column("Giá trị tài chính", style="green")

    table.add_row("Trọng lượng tàu không tải LDT", f"{val.ldt_tonnes:,.1f} tấn", "-")
    table.add_row("Thép kết cấu thu hồi (88%)", f"{val.recovered_steel_tonnes:,.1f} tấn", f"${val.recovered_steel_tonnes * steel_price:,.2f}")
    table.add_row("Kim loại màu thu hồi (3.5%)", f"{val.recovered_nonferrous_tonnes:,.1f} tấn", f"${val.recovered_nonferrous_tonnes * 1800.0:,.2f}")
    table.add_row("Chất thải nguy hại xử lý", f"{val.total_hazardous_waste_tonnes:,.2f} tấn", f"-${val.hazardous_disposal_cost_usd:,.2f}")
    table.add_row("Chi phí nhân công tháo dỡ", f"${95.0:.1f}/LDT", f"-${val.labor_demolition_cost_usd:,.2f}")
    table.add_row("TỔNG GIÁ TRỊ THANH LÝ RÒNG (USD)", "-", f"[bold green]${val.net_salvage_value_usd:,.2f}[/bold green]")
    table.add_row("QUY ĐỔI VN ĐỒNG (Tỷ VND)", "-", f"[bold yellow]{val.net_salvage_value_vnd / 1e9:,.2f} Tỷ VND[/bold yellow]")

    console.print(table)
    console.print(Panel(val.compliance_notes, title="CHỨNG CHỈ SẴN SÀNG TÁI CHẾ IRRC", box=box.ROUNDED))


# ==============================================================================
# PHASE 245 COMMANDS: PORT RECEPTION FACILITIES WASTE & CIRCULAR 39
# ==============================================================================

@portwaste_app.command(name="awn")
def portwaste_awn_cmd(
    hours_before: float = typer.Option(28.0, "--hours", "-h", help="Số giờ gửi thông báo trước khi cập cảng"),
    remaining_m3: float = typer.Option(15.0, "--remaining", "-r", help="Dung tích chứa chất thải còn trống (m3)"),
    tank_cap_m3: float = typer.Option(40.0, "--capacity", "-c", help="Tổng dung tích két chứa (m3)"),
    next_leg_gen_m3: float = typer.Option(8.0, "--next-gen", help="Lượng chất thải dự kiến phát sinh chặng kế tiếp (m3)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra thời hạn thông báo AWN 24h và điều kiện bắt buộc xả thải lên cảng."""
    res = PortReceptionWasteEngine.evaluate_awn_delivery_mandate(
        hours_before_arrival=hours_before,
        remaining_storage_m3=remaining_m3,
        total_tank_capacity_m3=tank_cap_m3,
        predicted_generation_next_leg_m3=next_leg_gen_m3,
    )

    if as_json:
        console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
        return

    table = Table(title="ĐÁNH GIÁ THÔNG BÁO TIẾP NHẬN CHẤT THẢI (AWN) CẢNG BIỂN", box=box.ROUNDED)
    table.add_column("Thông số", style="cyan")
    table.add_column("Giá trị", style="white")

    table.add_row("Thời gian gửi trước khi đến", f"{res.hours_before_arrival:.1f} giờ ({'Đúng hạn >=24h' if res.is_filed_on_time else 'TRỄ HẠN'})")
    table.add_row("Dung tích két còn trống", f"{res.remaining_storage_m3:.1f} m3 / Tổng {tank_cap_m3:.1f} m3")
    table.add_row("Nhu cầu chặng kế tiếp (+25% đệm)", f"{res.predicted_generation_next_leg_m3 * 1.25:.1f} m3")
    table.add_row("Quy định bơm xả bắt buộc", "[bold red]BẮT BUỘC XẢ THẢI LÊN CẢNG[/bold red]" if res.mandatory_discharge_required else "[green]Cho phép giữ lại trên tàu[/green]")

    console.print(table)
    console.print(f"[bold]{res.notification_summary}[/bold]")


@portwaste_app.command(name="tariff")
def portwaste_tariff_cmd(
    gt: float = typer.Option(35000.0, "--gt", help="Tổng dung tích tàu GT"),
    days: float = typer.Option(2.5, "--days", "-d", help="Số ngày lưu cầu bến cảng"),
    garbage_m3: float = typer.Option(18.0, "--garbage", "-g", help="Khối lượng rác sinh hoạt giao nộp (m3)"),
    sludge_m3: float = typer.Option(4.0, "--sludge", help="Dầu cặn Sludge giao nộp (m3)"),
    bilge_m3: float = typer.Option(6.0, "--bilge", help="Nước la-ghành lẫn dầu giao nộp (m3)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán biểu giá thu gom chất thải cảng biển theo Thông tư 39/2023/TT-BGTVT."""
    receipt = PortReceptionWasteEngine.calculate_port_waste_tariffs(
        gross_tonnage=gt,
        days_at_berth=days,
        delivered_garbage_m3=garbage_m3,
        annex_i_sludge_m3=sludge_m3,
        annex_i_bilge_m3=bilge_m3,
    )

    if as_json:
        console.print(json.dumps(receipt.__dict__, indent=2, ensure_ascii=False))
        return

    table = Table(title="HÓA ĐƠN THU PHÍ DỊCH VỤ THU GOM CHẤT THẢI CẢNG BIỂN", box=box.ROUNDED)
    table.add_column("Khoản mục chi phí", style="cyan")
    table.add_column("Khối lượng / Định mức", style="white")
    table.add_column("Số tiền (VND)", style="green")

    table.add_row("Phí thu gián tiếp (No-Special-Fee)", f"Tàu {gt:,.0f} GT", f"{receipt.indirect_waste_fee_vnd:,.0f} đ")
    table.add_row("Định mức rác sinh hoạt miễn phí kèm theo", f"{receipt.included_garbage_allowance_m3:.2f} m3", "Đã bao gồm")
    table.add_row("Rác sinh hoạt vượt định mức", f"{receipt.excess_garbage_m3:.2f} m3", f"{receipt.excess_garbage_fee_vnd:,.0f} đ")
    table.add_row("Chất thải nguy hại (Dầu cặn/nước lẫn dầu)", f"{sludge_m3 + bilge_m3:.2f} m3", f"{receipt.hazardous_waste_fee_vnd:,.0f} đ")
    table.add_row("TỔNG THANH TOÁN (VND)", "-", f"[bold yellow]{receipt.total_waste_fee_vnd:,.0f} VND[/bold yellow]")

    console.print(table)
    console.print(f"[dim]{receipt.statutory_tariff_ref}[/dim]")


# ==============================================================================
# PHASE 246 COMMANDS: ISPS PORT SECURITY & DECLARATION OF SECURITY (DOS)
# ==============================================================================

@ispssecurity_app.command(name="dos")
def isps_dos_cmd(
    ship_level: int = typer.Option(2, "--ship-level", "-s", help="Cấp độ an ninh tàu (1, 2, 3)"),
    port_level: int = typer.Option(1, "--port-level", "-p", help="Cấp độ an ninh bến cảng (1, 2, 3)"),
    dangerous_cargo: bool = typer.Option(False, "--danger-cargo/--normal-cargo", help="Có xếp dỡ hàng nguy hiểm"),
    sts: bool = typer.Option(False, "--sts/--no-sts", help="Hoạt động chuyển tải tàu sang tàu (STS)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá điều kiện bắt buộc ký Tuyên bố An ninh (Declaration of Security - DoS) theo ISPS Code A/5."""
    res = IspsPortSecurityEngine.evaluate_dos_requirement(
        ship_level=ship_level,
        port_level=port_level,
        has_dangerous_cargo=dangerous_cargo,
        is_sts_operation=sts,
    )

    if as_json:
        console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
        return

    color = "yellow" if res.dos_mandatory else "green"
    table = Table(title="ĐÁNH GIÁ TUYÊN BỐ AN NINH CẢNG BIỂN (ISPS DECLARATION OF SECURITY)", box=box.ROUNDED)
    table.add_column("Chỉ số an ninh", style="cyan")
    table.add_column("Chi tiết áp dụng", style=color)

    table.add_row("Cấp độ an ninh tàu", f"Cấp độ {res.ship_security_level.value}")
    table.add_row("Cấp độ an ninh cảng", f"Cấp độ {res.port_security_level.value}")
    table.add_row("Yêu cầu ký DoS", "[bold red]BẮT BUỘC KÝ TUYÊN BỐ AN NINH (DoS)[/bold red]" if res.dos_mandatory else "[green]Không bắt buộc DoS[/green]")
    table.add_row("Lý do / Căn cứ kích hoạt", res.governing_trigger)
    table.add_row("Tỷ lệ soi chiếu hành lý/hàng hóa", f"{res.access_screening_pct:.0f}%")
    table.add_row("Chu kỳ tuần tra bảo vệ", f"{res.max_patrol_interval_mins} phút/lượt")
    table.add_row("Thời gian triển khai lực lượng", f"{res.guard_deployment_time_mins} phút")
    table.add_row("Mã xác thực hồ sơ DoS", res.security_hash)

    console.print(table)


@ispssecurity_app.command(name="threat")
def isps_threat_cmd(
    facility: str = typer.Option("BẾN CẢNG CÁI MÉP - THỊ VẢI", "--facility", "-f", help="Tên cơ sở cảng biển"),
    threat: int = typer.Option(2, "--threat", "-t", help="Khả năng xảy ra mối đe dọa (1-5)"),
    vulnerability: int = typer.Option(3, "--vulnerability", "-v", help="Mức độ dễ bị tổn thương (1-5)"),
    consequence: int = typer.Option(4, "--consequence", "-c", help="Hậu quả nếu xảy ra sự cố (1-5)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán ma trận rủi ro an ninh TVC (Threat x Vulnerability x Consequence) và khuyến nghị cấp độ ISPS."""
    res = IspsPortSecurityEngine.calculate_tvc_risk_score(
        facility_name=facility,
        threat=threat,
        vulnerability=vulnerability,
        consequence=consequence,
    )

    if as_json:
        console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"ĐÁNH GIÁ RỦI RO AN NINH TVC: {res.facility_name}", box=box.ROUNDED)
    table.add_column("Yếu tố ma trận", style="cyan")
    table.add_column("Điểm số", style="yellow")

    table.add_row("Mối đe dọa (Threat Likelihood)", f"{res.threat_likelihood} / 5")
    table.add_row("Tính dễ bị tổn hại (Vulnerability)", f"{res.vulnerability_level} / 5")
    table.add_row("Mức độ hậu quả (Consequence)", f"{res.consequence_severity} / 5")
    table.add_row("Tổng điểm rủi ro TVC (T x V x C)", f"[bold red]{res.risk_score} / 125[/bold red]")
    table.add_row("Phân hạng rủi ro", f"[bold]{res.risk_tier.value.upper()}[/bold]")
    table.add_row("Khuyến nghị Cấp độ ISPS", f"[bold green]CẤP ĐỘ {res.recommended_level.value}[/bold green]")

    console.print(table)

    measures_str = "\n".join(f"- {m}" for m in res.mitigation_measures)
    console.print(Panel(measures_str, title="BIỆN PHÁP AN NINH KHUYẾN NGHỊ", box=box.ROUNDED))
