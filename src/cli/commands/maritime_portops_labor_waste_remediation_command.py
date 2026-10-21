"""Typer CLI Commands for Maritime Port Operations, Cargo Handling Liability, Marine Labor Safety & Remediation Escrow (Phases 227-230)."""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_portops_labor_waste_remediation_engine import (
    StevedoreTerminalLiabilityEngine, EnclosedSpaceAtmosphereTest, MarineLaborSafetyEngine,
    PortWasteReceptionEngine, MarpolWasteCategory, MaritimeRemediationEscrowEngine, OilPersistenceClass,
)

console = Console()

stevedore_app = typer.Typer(name="stevedore", help="Đánh giá trách nhiệm bồi thường bốc dỡ cảng biển & giới hạn theo kiện/kg BLLHH 2015 (Phase 227).")
maritimesafety_app = typer.Typer(name="maritimesafety", help="An toàn lao động hàng hải, kiểm toán buồng kín & bồi thường tai nạn lao động MLC 2006 (Phase 228).")
portwaste_app = typer.Typer(name="portwaste", help="Quản lý và thẩm định chuyển giao chất thải tàu biển tại cảng theo TT 41/2020/TT-BGTVT (Phase 229).")
remediationescrow_app = typer.Typer(name="remediationescrow", help="Tính toán ký quỹ phục hồi môi trường biển & bảo lãnh ngân hàng sự cố tràn dầu (Phase 230).")


def _print_kv_table(title: str, col1: str, col2: str, rows: list[tuple[str, str]], no_wrap: bool = False) -> None:
    table = Table(title=title)
    table.add_column(col1, style="cyan", no_wrap=no_wrap)
    table.add_column(col2, style="magenta")
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)


@stevedore_app.command("assess")
def assess_stevedore_liability(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu chở hàng"),
    terminal: str = typer.Option(..., "--terminal", "-t", help="Tên doanh nghiệp cảng / bến cảng"),
    packages: int = typer.Option(..., "--packages", "-p", help="Số kiện hàng bị tổn thất"),
    weight: float = typer.Option(..., "--weight", "-w", help="Tổng trọng lượng hàng tổn thất (kg)"),
    claimed_loss: float = typer.Option(..., "--claimed-loss", help="Giá trị tổn thất khiếu nại (SDR)"),
    declared_value: Optional[float] = typer.Option(None, "--declared-value", help="Giá trị kê khai trước khi bốc dỡ (SDR)"),
    days_since_delivery: int = typer.Option(10, "--days-since-delivery", help="Số ngày kể từ khi giao hàng"),
    notice_days: int = typer.Option(1, "--notice-days", help="Số ngày gửi thông báo khiếu nại sau giao hàng"),
    apparent: bool = typer.Option(True, "--apparent/--concealed", help="Tổn thất rõ rệt ngoài bao bì hay ẩn tì bên trong"),
    reckless: bool = typer.Option(False, "--reckless/--normal", help="Hành vi cẩu thả nghiêm trọng biết trước hậu quả"),
) -> None:
    """Đánh giá trách nhiệm bồi thường bốc dỡ cảng biển theo Điều 214-224 BLLHH 2015."""
    res = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name=vessel, terminal_operator=terminal, package_count=packages, gross_weight_kg=weight,
        claimed_loss_sdr=claimed_loss, declared_cargo_value_sdr=declared_value,
        days_since_delivery=days_since_delivery, notice_given_days_after_delivery=notice_days,
        is_apparent_damage=apparent, is_gross_recklessness=reckless,
    )
    _print_kv_table(f"ĐÁNH GIÁ TRÁCH NHIỆM BỐC DỠ CẢNG BIỂN: {terminal.upper()} (TÀU {vessel.upper()})", "Chỉ số thẩm định", "Giá trị", [
        ("Số kiện / Trọng lượng", f"{res.package_count} kiện | {res.gross_weight_kg:,.1f} kg"),
        ("Tổn thất khiếu nại", f"{res.claimed_loss_sdr:,.2f} SDR"),
        ("Hạn mức theo kiện (500 SDR)", f"{res.per_package_limit_sdr:,.2f} SDR"),
        ("Hạn mức theo kg (2 SDR)", f"{res.per_kg_limit_sdr:,.2f} SDR"),
        ("Hạn mức luật định áp dụng", f"{res.applicable_statutory_limit_sdr:,.2f} SDR"),
        ("Thông báo tổn thất hợp lệ", "ĐẠT" if res.notice_of_damage_valid else "KHÔNG HỢP LỆ"),
        ("Thời hiệu khởi kiện (1 năm)", "HẾT THỜI HIỆU" if res.is_timebarred else "TRONG THỜI HIỆU"),
        ("Mất quyền giới hạn (Cẩu thả)", "CÓ" if res.is_limitation_lost_recklessness else "KHÔNG"),
        ("Doanh nghiệp cảng phải trả (SDR)", f"{res.terminal_payable_sdr:,.2f} SDR"),
        ("Doanh nghiệp cảng phải trả (VND)", f"{res.terminal_payable_vnd:,.0f} VND"),
        ("Phần tổn thất chủ hàng tự chịu", f"{res.uncompensated_cargo_loss_sdr:,.2f} SDR"),
    ], no_wrap=True)
    if res.findings:
        console.print(Panel("\n".join(f"- {f}" for f in res.findings), title="Kết luận pháp lý & Miễn trách", border_style="yellow"))


@maritimesafety_app.command("audit-entry")
def audit_enclosed_space_entry(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu"),
    space: str = typer.Option(..., "--space", "-s", help="Tên không gian kín (Hầm hàng, Két dằn, Kho xích...)"),
    o2: float = typer.Option(..., "--o2", help="Nồng độ Oxy (%) - Chuẩn tối thiểu 20.9%"),
    lel: float = typer.Option(0.0, "--lel", help="Nồng độ khí dễ cháy LEL (%) - Tối đa 1.0%"),
    h2s: float = typer.Option(0.0, "--h2s", help="Khí độc H2S (ppm) - Tối đa 5 ppm"),
    co: float = typer.Option(0.0, "--co", help="Khí độc CO (ppm) - Tối đa 25 ppm"),
    ventilation: float = typer.Option(30.0, "--ventilation", help="Thời gian thông gió cơ học liên tục (phút)"),
    detector: bool = typer.Option(True, "--detector/--no-detector", help="Thiết bị đo khí đa chỉ tiêu đã hiệu chuẩn"),
    standby: bool = typer.Option(True, "--standby/--no-standby", help="Bố trí thuyền viên thường trực cảnh giới ngoài cửa"),
    harness: bool = typer.Option(True, "--harness/--no-harness", help="Sẵn sàng dây đai an toàn & thiết bị cứu nạn khẩn cấp"),
) -> None:
    """Kiểm toán cấp phép làm việc trong không gian kín theo IMO Res. A.1050(27)."""
    res = MarineLaborSafetyEngine.audit_enclosed_space_entry(vessel, space, EnclosedSpaceAtmosphereTest(o2, lel, h2s, co, ventilation, detector, standby, harness))
    table = Table(title=f"KIỂM TOÁN AN TOÀN VÀO BUỒNG KÍN: {space.upper()} (TÀU {vessel.upper()})")
    table.add_column("Hạng mục an toàn", style="cyan", no_wrap=True)
    table.add_column("Kết quả đo", style="magenta")
    table.add_column("Đánh giá", style="green")
    for k, v1, v2 in [
        ("Nồng độ Oxy (O2 >= 20.9%)", f"{o2:.1f} %", "ĐẠT" if res.oxygen_pass else "KHÔNG ĐẠT"),
        ("Khí dễ cháy (LEL <= 1.0%)", f"{lel:.1f} %", "ĐẠT" if res.lel_pass else "NGUY HIỂM"),
        ("Khí độc H2S (<= 5.0 ppm)", f"{h2s:.1f} ppm", "ĐẠT" if res.h2s_pass else "VƯỢT NGƯỠNG"),
        ("Khí độc CO (<= 25.0 ppm)", f"{co:.1f} ppm", "ĐẠT" if res.co_pass else "VƯỢT NGƯỠNG"),
        ("Thông gió (>= 30 phút)", f"{ventilation:.1f} phút", "ĐẠT" if res.ventilation_pass else "THIẾU THỜI GIAN"),
        ("Trang thiết bị bảo hộ & Trực cứu nạn", "Đầy đủ" if res.safety_gear_ready else "Thiếu sót", "ĐẠT" if res.safety_gear_ready else "KHÔNG ĐẠT"),
    ]:
        table.add_row(k, v1, v2)
    console.print(table)
    decision = "CẤP PHÉP VÀO KHÔNG GIAN KÍN (PERMIT ISSUED)" if res.is_entry_permitted else "NGHIÊM CẤM VÀO (ENTRY PROHIBITED)"
    console.print(Panel(decision, title="Quyết định an toàn lao động", border_style="green" if res.is_entry_permitted else "red"))
    if res.deficiencies:
        console.print(Panel("\n".join(f"- {d}" for d in res.deficiencies), title="Cảnh báo an toàn", border_style="red"))


@maritimesafety_app.command("calc-injury")
def calculate_occupational_injury(
    seafarer: str = typer.Option(..., "--seafarer", "-s", help="Họ tên thuyền viên bị nạn"),
    salary: float = typer.Option(..., "--salary", help="Mức lương tháng làm căn cứ bồi thường (VND)"),
    disability: float = typer.Option(..., "--disability", "-d", help="Tỷ lệ suy giảm khả năng lao động (%)"),
    employer_fault: float = typer.Option(100.0, "--employer-fault", help="Tỷ lệ lỗi của chủ tàu/người sử dụng lao động (%)"),
    medical_costs: float = typer.Option(0.0, "--medical-costs", help="Chi phí y tế cấp cứu, điều trị chủ tàu chi trả (VND)"),
) -> None:
    """Tính toán chế độ bồi thường tai nạn lao động theo Luật ATVSLĐ 2015 & MLC 2006."""
    res = MarineLaborSafetyEngine.calculate_occupational_injury_compensation(seafarer, salary, disability, employer_fault, medical_costs)
    _print_kv_table(f"BỒI THƯỜNG TAI NẠN LAO ĐỘNG HÀNG HẢI: {seafarer.upper()}", "Chỉ tiêu", "Số liệu", [
        ("Mức lương tháng căn cứ", f"{salary:,.0f} VND"), ("Tỷ lệ suy giảm lao động", f"{disability:.1f} %"),
        ("Tỷ lệ lỗi của chủ tàu", f"{employer_fault:.1f} %"), ("Số tháng lương luật định", f"{res['statutory_salary_months']} tháng"),
        ("Tiền trợ cấp tai nạn", f"{res['indemnity_amount_vnd']:,.0f} VND"), ("Chi phí y tế chi trả", f"{res['medical_costs_covered_vnd']:,.0f} VND"),
        ("Tổng số tiền chủ tàu phải trả", f"{res['total_statutory_payout_vnd']:,.0f} VND"),
    ])


@portwaste_app.command("verify")
def verify_port_waste(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu ghé cảng"),
    port: str = typer.Option(..., "--port", "-p", help="Tên cảng biển tiếp nhận"),
    notice_hours: float = typer.Option(24.0, "--notice-hours", help="Số giờ gửi thông báo trước khi cập cảng (Chuẩn >= 24h)"),
    category: str = typer.Option("ANNEX_I_OILY_BILGE_SLUDGE", "--category", "-c", help="Loại chất thải MARPOL: ANNEX_I_OILY_BILGE_SLUDGE, ANNEX_IV_SEWAGE_BLACKWATER, ANNEX_V_GARBAGE_PLASTICS, ANNEX_V_FOOD_DOMESTIC_WASTE, ANNEX_VI_OZONE_EXHAUST_RESIDUE"),
    volume: float = typer.Option(5.0, "--volume", help="Khối lượng chất thải đề nghị giao nộp (m3)"),
    capacity: float = typer.Option(20.0, "--capacity", help="Dung tích chứa còn lại trên tàu (m3)"),
    estimated_gen: float = typer.Option(10.0, "--estimated-gen", help="Dự kiến chất thải phát sinh đến cảng tiếp theo (m3)"),
    exemption: bool = typer.Option(False, "--exemption/--delivery", help="Đề nghị miễn nộp để chuyển sang cảng tiếp theo"),
) -> None:
    """Thẩm định thủ tục giao nộp chất thải tàu biển tại cảng theo TT 41/2020/TT-BGTVT."""
    waste_cat = MarpolWasteCategory.__members__.get(category.upper(), MarpolWasteCategory.ANNEX_I_OILY_BILGE_SLUDGE)
    res = PortWasteReceptionEngine.verify_waste_delivery(vessel, port, notice_hours, waste_cat, volume, capacity, estimated_gen, exemption)
    _print_kv_table(f"THẨM ĐỊNH THỦ TỤC CHẤT THẢI CẢNG BIỂN: {port.upper()} (TÀU {vessel.upper()})", "Thông số", "Kết quả", [
        ("Loại chất thải MARPOL", waste_cat.value), ("Thời gian thông báo trước (>= 24h)", f"{notice_hours:.1f} giờ ({'ĐẠT' if res.advance_notice_compliant else 'TRỄ'})"),
        ("Khối lượng đề nghị giao nộp", f"{volume:.1f} m3"), ("Dung tích chứa lưu trữ còn lại", f"{capacity:.1f} m3"),
        ("Dự kiến phát sinh đến cảng sau", f"{estimated_gen:.1f} m3"),
        ("Chấp thuận miễn trừ lưu giữ", "ĐƯỢC MIỄN TRỪ" if res.exemption_granted_for_next_port else "BẮT BUỘC GIAO NỘP TẠI CẢNG"),
        ("Phí thu gom chất thải luật định", f"{res.statutory_port_waste_fee_vnd:,.0f} VND"),
        ("Biên nhận chuyển giao chất thải (WTN)", "CẤP PHIẾU WTN" if res.reception_facility_transfer_note_issued else "KHÔNG CẤP"),
    ])
    if res.deficiencies:
        console.print(Panel("\n".join(f"- {d}" for d in res.deficiencies), title="Khiếm khuyết / Từ chối miễn trừ", border_style="red"))


@remediationescrow_app.command("calculate")
def calculate_remediation_escrow(
    incident: str = typer.Option(..., "--incident", "-i", help="Mã hồ sơ sự cố ô nhiễm"),
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu tràn dầu"),
    volume: float = typer.Option(..., "--volume", help="Khối lượng dầu tràn ước tính (m3)"),
    persistence: str = typer.Option("PERSISTENT_CRUDE_HEAVY_FUEL", "--persistence", help="Loại dầu: PERSISTENT_CRUDE_HEAVY_FUEL (1.8x), MEDIUM_DISTILLATE_DIESEL (1.4x), NON_PERSISTENT_GASOLINE_MGO (1.0x)"),
    esi: int = typer.Option(5, "--esi", help="Chỉ số nhạy cảm môi trường đường bờ ESI (1 đến 10)"),
) -> None:
    """Tính toán ký quỹ phục hồi môi trường & bảo lãnh ngân hàng theo Luật BVMT 2020."""
    oil_type = OilPersistenceClass.__members__.get(persistence.upper(), OilPersistenceClass.PERSISTENT_CRUDE_HEAVY_FUEL)
    res = MaritimeRemediationEscrowEngine.calculate_escrow(incident, vessel, volume, oil_type, esi)
    _print_kv_table(f"KÝ QUỸ PHỤC HỒI MÔI TRƯỜNG BIỂN: {incident.upper()} (TÀU {vessel.upper()})", "Tham số ký quỹ", "Giá trị", [
        ("Khối lượng dầu tràn", f"{volume:,.2f} m3"), ("Loại dầu & Hệ số bền vững", f"{oil_type.value} ({res.persistence_factor:.1f}x)"),
        ("Chỉ số nhạy cảm môi trường ESI", f"ESI {res.esi_sensitivity_index} ({res.esi_factor:.1f}x)"),
        ("Chi phí khắc phục cơ sở", f"{res.base_cleanup_cost_per_m3_vnd:,.0f} VND/m3"), ("Kinh phí xử lý sự cố trực tiếp", f"{res.subtotal_remediation_cost_vnd:,.0f} VND"),
        ("Dự phòng phục hồi sinh thái (20%)", f"{res.ecological_restoration_contingency_vnd:,.0f} VND"),
        ("TỔNG TIỀN KÝ QUỸ / BẢO LÃNH NGÂN HÀNG", f"{res.total_statutory_escrow_deposit_vnd:,.0f} VND"),
        ("Đơn vị thụ hưởng ký quỹ", res.escrow_account_beneficiary), ("Điều kiện giải tỏa bảo lãnh", res.liquidation_release_condition),
    ])
    if res.notes:
        console.print(Panel("\n".join(f"- {n}" for n in res.notes), title="Căn cứ tính toán & Điều kiện pháp lý", border_style="blue"))
