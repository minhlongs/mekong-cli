"""Typer CLI Commands for Maritime Bunker Oil Pollution, MLC Living/Medical, SOPEP Response, and Environmental Sanctions (Phases 223-226)."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_bunker_mlc_sopep_sanctions_engine import (
    BunkerOilPollutionEngine, BunkerPollutionDefense, MlcLivingMedicalEngine,
    MlcMedicineChestCategory, SopepEmergencyPlanEngine,
    MaritimeEnvironmentalSanctionsEngine, EnvironmentalInfractionType,
)

console = Console()

bunkerclaim_app = typer.Typer(name="bunkerclaim", help="Phân tích bồi thường ô nhiễm dầu nhiên liệu & Công ước Bunker 2001 (Phase 223).")
mlcliving_app = typer.Typer(name="mlcliving", help="Kiểm toán điều kiện sinh hoạt, ăn uống & chăm sóc y tế thuyền viên theo MLC 2006 (Phase 224).")
sopep_app = typer.Typer(name="sopep", help="Thẩm định Kế hoạch khẩn cấp ứng phó ô nhiễm dầu trên tàu SOPEP / SMPEP MARPOL Reg. 37 (Phase 225).")
maritimesanction_app = typer.Typer(name="maritimesanction", help="Xử phạt vi phạm hành chính môi trường biển & Lưu giữ tàu PSC theo NĐ 142/2017 & NĐ 45/2022 (Phase 226).")


def _render_table(title: str, cols: list[tuple[str, str]], rows: list[tuple[str, ...]]) -> None:
    table = Table(title=title)
    for name, style in cols:
        table.add_column(name, style=style)
    for row in rows:
        table.add_row(*row)
    console.print(table)


@bunkerclaim_app.command("assess")
def assess_bunker_claim(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu gây sự cố"),
    gt: float = typer.Option(..., "--gt", help="Tổng dung tích tàu (Gross Tonnage)"),
    clean_up: float = typer.Option(0.0, "--clean-up", help="Chi phí dọn dẹp, quây hút dầu (SDR)"),
    property_damage: float = typer.Option(0.0, "--property-damage", help="Thiệt hại tài sản, cầu cảng, lồng bè (SDR)"),
    economic_loss: float = typer.Option(0.0, "--economic-loss", help="Thiệt hại kinh tế, gián đoạn nuôi trồng (SDR)"),
    environmental: float = typer.Option(0.0, "--environmental", help="Chi phí phục hồi môi trường sinh thái (SDR)"),
    blue_card: bool = typer.Option(True, "--blue-card/--no-blue-card", help="Có Chứng chỉ bảo hiểm Bunker Blue Card"),
    defense: str = typer.Option("NONE", "--defense", help="Lý do miễn trừ: NONE, WAR_HOSTILITIES, EXCEPTIONAL_NATURAL_DISASTER, THIRD_PARTY_INTENTIONAL_ACT, NEGLIGENT_NAV_AID_MAINTENANCE"),
    years_damage: float = typer.Option(1.0, "--years-damage", help="Số năm kể từ khi xảy ra thiệt hại"),
    years_incident: float = typer.Option(1.0, "--years-incident", help="Số năm kể từ sự cố phát sinh"),
    misconduct: bool = typer.Option(False, "--misconduct/--no-misconduct", help="Lỗi cố ý hoặc liều lĩnh biết trước hậu quả"),
):
    """Đánh giá trách nhiệm dân sự bồi thường ô nhiễm dầu nhiên liệu Bunker 2001 & LLMC 1996."""
    defense_enum = BunkerPollutionDefense.__members__.get(defense.strip().upper(), BunkerPollutionDefense.NONE)
    a = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel, gt, clean_up, property_damage, economic_loss, environmental, blue_card, defense_enum, years_damage, years_incident, misconduct
    )
    _render_table(f"ĐÁNH GIÁ TRÁCH NHIỆM BỒI THƯỜNG DẦU BUNKER - {a.vessel_name.upper()}", [("Chỉ số / Tiêu chí", "cyan"), ("Kết quả thẩm định", "bold green")], [
        ("Tổng dung tích (GT)", f"{a.gross_tonnage:,.0f} GT"),
        ("Bắt buộc chứng chỉ Bunker Blue Card", "CÓ (Tàu > 1,000 GT)" if a.compulsory_insurance_required else "KHÔNG (Tàu <= 1,000 GT)"),
        ("Tình trạng Bunker Blue Card", "[green]HỢP LỆ[/green]" if a.has_valid_bunker_blue_card else "[red]THIẾU / KHÔNG HỢP LỆ[/red]"),
        ("Quyền kiện trực tiếp P&I Club", "ĐƯỢC PHÉP" if a.direct_action_against_insurer_allowed else "KHÔNG"),
        ("Tổng giá trị khiếu nại yêu cầu", f"{a.total_claim_amount_sdr:,.2f} SDR"),
        ("Trần giới hạn trách nhiệm LLMC 1996", f"{a.applicable_llmc_limit_sdr:,.2f} SDR" if a.limitation_of_liability_applies else "KHÔNG GIỚI HẠN (MẤT QUYỀN)"),
        ("Chủ tàu / P&I phải bồi thường", f"[yellow]{a.owner_statutory_payout_sdr:,.2f} SDR[/yellow]"),
        ("Thâm hụt chưa được đền bù", f"[red]{a.uncompensated_shortfall_sdr:,.2f} SDR[/red]" if a.uncompensated_shortfall_sdr > 0 else "0.00 SDR"),
        ("Miễn trừ trách nhiệm", "[green]ĐƯỢC MIỄN TRỪ[/green]" if a.defense_exoneration_granted else "KHÔNG"),
        ("Thời hiệu khởi kiện", "[red]HẾT THỜI HIỆU[/red]" if a.claim_prescribed else "[green]CÒN THỜI HIỆU[/green]"),
    ])
    console.print(Panel("\n".join(f"• {f}" for f in a.findings), title="KẾT LUẬN & CĂN CỨ PHÁP LÝ BUNKER CONVENTION 2001", border_style="blue"))


@mlcliving_app.command("audit")
def audit_mlc_living(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu kiểm toán"),
    crew: int = typer.Option(..., "--crew", "-c", help="Số lượng thuyền viên trên tàu"),
    passengers: int = typer.Option(0, "--passengers", "-p", help="Số lượng hành khách đi cùng"),
    days: float = typer.Option(..., "--days", "-d", help="Thời gian chuyến đi biển (ngày)"),
    water: float = typer.Option(3.0, "--water", "-w", help="Định mức nước ngọt sinh hoạt/uống (lít/người/ngày)"),
    cook: bool = typer.Option(True, "--cook/--no-cook", help="Có bếp trưởng chứng chỉ hàng hải hợp lệ"),
    hospital: bool = typer.Option(True, "--hospital/--no-hospital", help="Có buồng bệnh xá riêng biệt trên tàu"),
    doctor: bool = typer.Option(False, "--doctor/--no-doctor", help="Có Bác sĩ y khoa đủ chứng chỉ chuyên môn"),
    medical_chest: bool = typer.Option(True, "--chest/--no-chest", help="Tủ thuốc y tế và Sổ tay Y tế đạt chuẩn"),
    chest_cat: str = typer.Option("CATEGORY_A_OCEAN_GOING", "--chest-cat", help="Hạng tủ thuốc: CATEGORY_A_OCEAN_GOING, CATEGORY_B_COASTAL_NEAR, CATEGORY_C_HARBOUR_TUG"),
):
    """Kiểm toán điều kiện làm việc, sinh hoạt, thực phẩm & y tế thuyền viên theo MLC 2006."""
    cat_enum = MlcMedicineChestCategory.__members__.get(chest_cat.strip().upper(), MlcMedicineChestCategory.CATEGORY_A_OCEAN_GOING)
    r = MlcLivingMedicalEngine.audit_living_and_medical(vessel, crew, passengers, days, water, cook, hospital, doctor, medical_chest, cat_enum)
    sc = "[green]TUÂN THỦ HOÀN TOÀN[/green]" if r.is_compliant else "[red]KHÔNG ĐẠT (CÓ THIẾU SÓT)[/red]"
    _render_table(f"KIỂM TOÁN ĐIỀU KIỆN SINH HOẠT & Y TẾ MLC 2006 - {r.vessel_name.upper()}", [("Hạng mục kiểm tra", "cyan"), ("Tình trạng ghi nhận", "bold white"), ("Đánh giá hợp chuẩn MLC", "bold green")], [
        ("Kết luận chung", sc, sc),
        ("Số lượng thuyền viên / Thời gian", f"{r.crew_count} người / {r.voyage_duration_days:.1f} ngày", "Định biên an toàn"),
        ("Nước ngọt sinh hoạt", f"{r.potable_water_liters_per_person_day:.1f} L/người/ngày", "[green]ĐẠT[/green]" if r.potable_water_liters_per_person_day >= 2.5 else "[red]THIẾU[/red]"),
        ("Bếp trưởng chứng chỉ hàng hải", "CÓ" if r.has_certified_cook else "KHÔNG", "[green]ĐẠT[/green]" if (r.crew_count < 10 or r.has_certified_cook) else "[red]KHÔNG ĐẠT[/red]"),
        ("Buồng bệnh xá riêng biệt", "CÓ" if r.has_dedicated_hospital_berth else "KHÔNG", "[green]ĐẠT[/green]" if (r.crew_count < 15 or r.voyage_duration_days <= 3.0 or r.has_dedicated_hospital_berth) else "[red]KHÔNG ĐẠT[/red]"),
        ("Bác sĩ y khoa trên tàu", "CÓ" if r.has_qualified_doctor else ("BẮT BUỘC" if r.requires_qualified_doctor else "KHÔNG YÊU CẦU"), "[green]ĐẠT[/green]" if (not r.requires_qualified_doctor or r.has_qualified_doctor) else "[red]THIẾU BÁC SĨ[/red]"),
        ("Tủ thuốc & Sổ tay y tế WHO", "HỢP LỆ" if r.medicine_chest_valid else "HẾT HẠN / THIẾU", "[green]ĐẠT[/green]" if r.medicine_chest_valid else "[red]KHÔNG ĐẠT[/red]"),
    ])
    if r.deficiencies:
        console.print(Panel("\n".join(f"• [red]VI PHẠM:[/red] {d}" for d in r.deficiencies), title="DANH SÁCH THIẾU SÓT CẦN KHẮC PHỤC TRƯỚC KHI RỜI CẢNG", border_style="red"))
    if r.recommendations:
        console.print(Panel("\n".join(f"• {rec}" for rec in r.recommendations), title="KHUYẾN NGHỊ & HƯỚNG DẪN BẢO ĐẢM PHÚC LỢI THUYỀN VIÊN", border_style="green"))


@sopep_app.command("verify")
def verify_sopep(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu"),
    vessel_type: str = typer.Option(..., "--type", "-t", help="Loại tàu: OIL_TANKER, CHEMICAL_TANKER, BULK_CARRIER, CONTAINER"),
    gt: float = typer.Option(..., "--gt", help="Tổng dung tích tàu (Gross Tonnage)"),
    approved: bool = typer.Option(True, "--approved/--not-approved", help="Đã được Đăng kiểm / Cục Hàng hải phê duyệt"),
    contacts: bool = typer.Option(True, "--contacts/--no-contacts", help="Có danh mục đầu mối liên lạc khẩn cấp IMO Res. A.851(20)"),
    operational: bool = typer.Option(True, "--operational/--no-operational", help="Có quy trình ứng phó tràn dầu khi thao tác bơm rót"),
    casualty: bool = typer.Option(True, "--casualty/--no-casualty", help="Có hướng dẫn giảm thiểu tổn thất do mắc cạn, va chạm"),
    liaison: bool = typer.Option(True, "--liaison/--no-liaison", help="Có cơ chế phối hợp tác chiến với cơ quan quản lý ven biển"),
    drill_months: float = typer.Option(1.5, "--drill-months", help="Số tháng kể từ lần thực tập sự cố tràn dầu gần nhất"),
):
    """Thẩm định kế hoạch ứng cứu ô nhiễm dầu SOPEP / SMPEP theo MARPOL Reg. 37."""
    r = SopepEmergencyPlanEngine.verify_sopep_compliance(vessel, vessel_type, gt, approved, contacts, operational, casualty, liaison, drill_months)
    _render_table(f"THẨM ĐỊNH KẾ HOẠCH ỨNG CỨU Ô NHIỄM DẦU SOPEP / SMPEP - {r.vessel_name.upper()}", [("Tiêu chuẩn MARPOL", "cyan"), ("Kết quả thẩm tra", "bold green")], [
        ("Loại kế hoạch áp dụng", r.plan_type.value),
        ("Bắt buộc trang bị trên tàu", "CÓ (BẮT BUỘC)" if r.is_mandatory else "KHÔNG (MIỄN TRỪ)"),
        ("Phê duyệt của Chính quyền Hàng hải", "[green]ĐÃ PHÊ DUYỆT[/green]" if r.is_approved_by_administration else "[red]CHƯA PHÊ DUYỆT[/red]"),
        ("Đầu mối liên lạc khẩn cấp IMO Res. A.851(20)", "[green]ĐẦY ĐỦ[/green]" if r.has_coastal_state_contacts else "[red]THIẾU[/red]"),
        ("Quy trình ứng phó tràn dầu vận hành", "[green]CÓ[/green]" if r.has_operational_spill_steps else "[red]THIẾU[/red]"),
        ("Hướng dẫn giảm thiểu sự cố tai nạn", "[green]CÓ[/green]" if r.has_casualty_mitigation_steps else "[red]THIẾU[/red]"),
        ("Cơ chế phối hợp ven biển sở tại", "[green]CÓ[/green]" if r.has_national_local_liaison else "[red]THIẾU[/red]"),
        ("Thực tập ứng phó sự cố (Diễn tập)", f"{r.last_drill_months_ago:.1f} tháng trước", "[green]ĐẠT (<= 3 tháng)[/green]" if r.drill_compliant else "[red]QUÁ HẠN[/red]"),
        ("TRẠNG THÁI TỔNG THỂ", f"[bold]{r.overall_status}[/bold]"),
    ])
    if r.deficiencies:
        console.print(Panel("\n".join(f"• [red]KHIẾM KHUYẾT:[/red] {d}" for d in r.deficiencies), title="KHIẾM KHUYẾT SOPEP YÊU CẦU ĐÌNH CHỈ RỜI CẢNG THEO PSC TOKYO MOU", border_style="red"))
    else:
        console.print(Panel("[green]Tàu đủ điều kiện an toàn môi trường biển và sẵn sàng ứng phó sự cố tràn dầu.[/green]", title="KẾT LUẬN THẨM ĐỊNH", border_style="green"))


@maritimesanction_app.command("penalize")
def penalize_environmental_infraction(
    vessel: str = typer.Option(..., "--vessel", "-v", help="Tên tàu vi phạm"),
    infraction: str = typer.Option(..., "--infraction", "-i", help="Loại hành vi vi phạm: OILY_BILGE_OVERBOARD_DISCHARGE, MARPOL_V_PLASTICS_GARBAGE_DUMP, BALLAST_WATER_UNAPPROVED_RELEASE, SOPEP_DRILL_AND_EQUIPMENT_ABSENT, SMOKE_EXCESSIVE_OPACITY_RINGELMANN"),
    repeat: bool = typer.Option(False, "--repeat/--first-time", help="Vi phạm tái phạm nhiều lần"),
    pollution: bool = typer.Option(False, "--pollution/--no-pollution", help="Gây ô nhiễm thực tế đo đạc được trên mặt nước biển"),
    uncooperative: bool = typer.Option(False, "--uncooperative/--cooperative", help="Có hành vi trốn tránh, chống đối kiểm tra"),
):
    """Quyết định xử phạt vi phạm hành chính môi trường biển & Lệnh lưu giữ tàu PSC."""
    try:
        infraction_enum = EnvironmentalInfractionType[infraction.strip().upper()]
    except KeyError:
        console.print(f"[red]Lỗi: Không tìm thấy hành vi vi phạm '{infraction}'[/red]")
        raise typer.Exit(code=1)

    res = MaritimeEnvironmentalSanctionsEngine.calculate_sanctions(vessel, infraction_enum, repeat, pollution, uncooperative)
    _render_table(f"QUYẾT ĐỊNH XỬ PHẠT VI PHẠM MÔI TRƯỜNG BIỂN - {res.vessel_name.upper()}", [("Nội dung quyết định", "cyan"), ("Giá trị áp dụng", "bold yellow")], [
        ("Hành vi vi phạm", res.infraction.value),
        ("Căn cứ pháp lý", res.statutory_legal_basis),
        ("Mức phạt tiền khung cơ sở", f"{res.base_fine_vnd:,.0f} VNĐ"),
        ("Hệ số tình tiết tăng nặng", f"{res.aggravating_multiplier:.2f}x"),
        ("TỔNG MỨC PHẠT CHÍNH THỨC", f"[bold red]{res.total_statutory_fine_vnd:,.0f} VNĐ[/bold red]"),
        ("LỆNH LƯU GIỮ TÀU BIỂN (PSC DETENTION)", "[bold red]LƯU GIỮ BẮT BUỘC TẠI CẢNG[/bold red]" if res.psc_detention_ordered else "[green]KHÔNG ÁP DỤNG[/green]"),
        ("Tiền đặt cọc bảo lãnh phong tỏa", f"{res.mandatory_escrow_deposit_vnd:,.0f} VNĐ" if res.mandatory_escrow_deposit_vnd > 0 else "0 VNĐ"),
    ])
    rect_text = f"• [bold yellow]Biện pháp khắc phục hậu quả:[/bold yellow] {res.rectification_order}\n• [bold red]Yêu cầu:[/bold red] Nộp phạt kho bạc nhà nước và hoàn tất biện pháp khắc phục trước khi Cảng vụ cấp phép rời cảng."
    console.print(Panel(rect_text, title="BIỆN PHÁP KHẮC PHỤC HẬU QUẢ BẮT BUỘC", border_style="red" if res.psc_detention_ordered else "yellow"))
