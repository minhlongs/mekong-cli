"""
Typer CLI Commands for Maritime Bunker Oil Pollution, MLC Living/Medical, SOPEP Response, and Environmental Sanctions.
Phases 223-226:
- Phase 223: mekong bunkerclaim assess
- Phase 224: mekong mlcliving audit
- Phase 225: mekong sopep verify
- Phase 226: mekong maritimesanction penalize
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_bunker_mlc_sopep_sanctions_engine import (
    BunkerOilPollutionEngine,
    BunkerPollutionDefense,
    MlcLivingMedicalEngine,
    MlcMedicineChestCategory,
    SopepEmergencyPlanEngine,
    MaritimeEnvironmentalSanctionsEngine,
    EnvironmentalInfractionType,
)

console = Console()

# Typer sub-applications
bunkerclaim_app = typer.Typer(
    name="bunkerclaim",
    help="Phân tích bồi thường ô nhiễm dầu nhiên liệu & Công ước Bunker 2001 (Phase 223).",
)
mlcliving_app = typer.Typer(
    name="mlcliving",
    help="Kiểm toán điều kiện sinh hoạt, ăn uống & chăm sóc y tế thuyền viên theo MLC 2006 (Phase 224).",
)
sopep_app = typer.Typer(
    name="sopep",
    help="Thẩm định Kế hoạch khẩn cấp ứng phó ô nhiễm dầu trên tàu SOPEP / SMPEP MARPOL Reg. 37 (Phase 225).",
)
maritimesanction_app = typer.Typer(
    name="maritimesanction",
    help="Xử phạt vi phạm hành chính môi trường biển & Lưu giữ tàu PSC theo NĐ 142/2017 & NĐ 45/2022 (Phase 226).",
)


# ==============================================================================
# PHASE 223: BUNKER OIL POLLUTION COMMAND
# ==============================================================================

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
    try:
        defense_enum = BunkerPollutionDefense[defense.strip().upper()]
    except KeyError:
        defense_enum = BunkerPollutionDefense.NONE

    assessment = BunkerOilPollutionEngine.assess_bunker_pollution_claim(
        vessel_name=vessel,
        gross_tonnage=gt,
        claim_clean_up_sdr=clean_up,
        claim_property_damage_sdr=property_damage,
        claim_economic_loss_sdr=economic_loss,
        claim_environmental_sdr=environmental,
        has_bunker_blue_card=blue_card,
        defense=defense_enum,
        years_since_damage=years_damage,
        years_since_incident=years_incident,
        is_intentional_misconduct=misconduct,
    )

    table = Table(title=f"ĐÁNH GIÁ TRÁCH NHIỆM BỒI THƯỜNG DẦU BUNKER - {assessment.vessel_name.upper()}")
    table.add_column("Chỉ số / Tiêu chí", style="cyan")
    table.add_column("Kết quả thẩm định", style="bold green")

    table.add_row("Tổng dung tích (GT)", f"{assessment.gross_tonnage:,.0f} GT")
    table.add_row("Bắt buộc chứng chỉ Bunker Blue Card", "CÓ (Tàu > 1,000 GT)" if assessment.compulsory_insurance_required else "KHÔNG (Tàu <= 1,000 GT)")
    table.add_row("Tình trạng Bunker Blue Card", "[green]HỢP LỆ[/green]" if assessment.has_valid_bunker_blue_card else "[red]THIẾU / KHÔNG HỢP LỆ[/red]")
    table.add_row("Quyền kiện trực tiếp P&I Club", "ĐƯỢC PHÉP" if assessment.direct_action_against_insurer_allowed else "KHÔNG")
    table.add_row("Tổng giá trị khiếu nại yêu cầu", f"{assessment.total_claim_amount_sdr:,.2f} SDR")
    table.add_row("Trần giới hạn trách nhiệm LLMC 1996", f"{assessment.applicable_llmc_limit_sdr:,.2f} SDR" if assessment.limitation_of_liability_applies else "KHÔNG GIỚI HẠN (MẤT QUYỀN)")
    table.add_row("Chủ tàu / P&I phải bồi thường", f"[yellow]{assessment.owner_statutory_payout_sdr:,.2f} SDR[/yellow]")
    table.add_row("Thâm hụt chưa được đền bù", f"[red]{assessment.uncompensated_shortfall_sdr:,.2f} SDR[/red]" if assessment.uncompensated_shortfall_sdr > 0 else "0.00 SDR")
    table.add_row("Miễn trừ trách nhiệm", "[green]ĐƯỢC MIỄN TRỪ[/green]" if assessment.defense_exoneration_granted else "KHÔNG")
    table.add_row("Thời hiệu khởi kiện", "[red]HẾT THỜI HIỆU[/red]" if assessment.claim_prescribed else "[green]CÒN THỜI HIỆU[/green]")

    console.print(table)

    findings_text = "\n".join(f"• {f}" for f in assessment.findings)
    console.print(Panel(findings_text, title="KẾT LUẬN & CĂN CỨ PHÁP LÝ BUNKER CONVENTION 2001", border_style="blue"))


# ==============================================================================
# PHASE 224: MLC 2006 LIVING & MEDICAL COMMAND
# ==============================================================================

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
    try:
        cat_enum = MlcMedicineChestCategory[chest_cat.strip().upper()]
    except KeyError:
        cat_enum = MlcMedicineChestCategory.CATEGORY_A_OCEAN_GOING

    report = MlcLivingMedicalEngine.audit_living_and_medical(
        vessel_name=vessel,
        crew_count=crew,
        passenger_count=passengers,
        voyage_duration_days=days,
        potable_water_liters_per_person_day=water,
        has_certified_cook=cook,
        has_dedicated_hospital_berth=hospital,
        has_qualified_doctor=doctor,
        has_valid_medical_guide_and_chest=medical_chest,
        chest_category=cat_enum,
    )

    table = Table(title=f"KIỂM TOÁN ĐIỀU KIỆN SINH HOẠT & Y TẾ MLC 2006 - {report.vessel_name.upper()}")
    table.add_column("Hạng mục kiểm tra", style="cyan")
    table.add_column("Tình trạng ghi nhận", style="bold white")
    table.add_column("Đánh giá hợp chuẩn MLC", style="bold green")

    status_color = "[green]TUÂN THỦ HOÀN TOÀN[/green]" if report.is_compliant else "[red]KHÔNG ĐẠT (CÓ THIẾU SÓT)[/red]"
    table.add_row("Kết luận chung", status_color, status_color)
    table.add_row("Số lượng thuyền viên / Thời gian", f"{report.crew_count} người / {report.voyage_duration_days:.1f} ngày", "Định biên an toàn")
    table.add_row("Nước ngọt sinh hoạt", f"{report.potable_water_liters_per_person_day:.1f} L/người/ngày", "[green]ĐẠT[/green]" if report.potable_water_liters_per_person_day >= 2.5 else "[red]THIẾU[/red]")
    table.add_row("Bếp trưởng chứng chỉ hàng hải", "CÓ" if report.has_certified_cook else "KHÔNG", "[green]ĐẠT[/green]" if (report.crew_count < 10 or report.has_certified_cook) else "[red]KHÔNG ĐẠT[/red]")
    table.add_row("Buồng bệnh xá riêng biệt", "CÓ" if report.has_dedicated_hospital_berth else "KHÔNG", "[green]ĐẠT[/green]" if (report.crew_count < 15 or report.voyage_duration_days <= 3.0 or report.has_dedicated_hospital_berth) else "[red]KHÔNG ĐẠT[/red]")
    table.add_row("Bác sĩ y khoa trên tàu", "CÓ" if report.has_qualified_doctor else ("BẮT BUỘC" if report.requires_qualified_doctor else "KHÔNG YÊU CẦU"), "[green]ĐẠT[/green]" if (not report.requires_qualified_doctor or report.has_qualified_doctor) else "[red]THIẾU BÁC SĨ[/red]")
    table.add_row("Tủ thuốc & Sổ tay y tế WHO", "HỢP LỆ" if report.medicine_chest_valid else "HẾT HẠN / THIẾU", "[green]ĐẠT[/green]" if report.medicine_chest_valid else "[red]KHÔNG ĐẠT[/red]")

    console.print(table)

    if report.deficiencies:
        def_text = "\n".join(f"• [red]VI PHẠM:[/red] {d}" for d in report.deficiencies)
        console.print(Panel(def_text, title="DANH SÁCH THIẾU SÓT CẦN KHẮC PHỤC TRƯỚC KHI RỜI CẢNG", border_style="red"))

    if report.recommendations:
        rec_text = "\n".join(f"• {r}" for r in report.recommendations)
        console.print(Panel(rec_text, title="KHUYẾN NGHỊ & HƯỚNG DẪN BẢO ĐẢM PHÚC LỢI THUYỀN VIÊN", border_style="green"))


# ==============================================================================
# PHASE 225: MARPOL SOPEP / SMPEP VERIFICATION COMMAND
# ==============================================================================

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
    report = SopepEmergencyPlanEngine.verify_sopep_compliance(
        vessel_name=vessel,
        vessel_type=vessel_type,
        gross_tonnage=gt,
        is_administration_approved=approved,
        has_coastal_state_contacts=contacts,
        has_operational_spill_steps=operational,
        has_casualty_mitigation_steps=casualty,
        has_national_local_liaison=liaison,
        months_since_last_oil_spill_drill=drill_months,
    )

    table = Table(title=f"THẨM ĐỊNH KẾ HOẠCH ỨNG CỨU Ô NHIỄM DẦU SOPEP / SMPEP - {report.vessel_name.upper()}")
    table.add_column("Tiêu chuẩn MARPOL", style="cyan")
    table.add_column("Kết quả thẩm tra", style="bold green")

    table.add_row("Loại kế hoạch áp dụng", report.plan_type.value)
    table.add_row("Bắt buộc trang bị trên tàu", "CÓ (BẮT BUỘC)" if report.is_mandatory else "KHÔNG (MIỄN TRỪ)")
    table.add_row("Phê duyệt của Chính quyền Hàng hải", "[green]ĐÃ PHÊ DUYỆT[/green]" if report.is_approved_by_administration else "[red]CHƯA PHÊ DUYỆT[/red]")
    table.add_row("Đầu mối liên lạc khẩn cấp IMO Res. A.851(20)", "[green]ĐẦY ĐỦ[/green]" if report.has_coastal_state_contacts else "[red]THIẾU[/red]")
    table.add_row("Quy trình ứng phó tràn dầu vận hành", "[green]CÓ[/green]" if report.has_operational_spill_steps else "[red]THIẾU[/red]")
    table.add_row("Hướng dẫn giảm thiểu sự cố tai nạn", "[green]CÓ[/green]" if report.has_casualty_mitigation_steps else "[red]THIẾU[/red]")
    table.add_row("Cơ chế phối hợp ven biển sở tại", "[green]CÓ[/green]" if report.has_national_local_liaison else "[red]THIẾU[/red]")
    table.add_row("Thực tập ứng phó sự cố (Diễn tập)", f"{report.last_drill_months_ago:.1f} tháng trước", "[green]ĐẠT (<= 3 tháng)[/green]" if report.drill_compliant else "[red]QUÁ HẠN[/red]")
    table.add_row("TRẠNG THÁI TỔNG THỂ", f"[bold]{report.overall_status}[/bold]")

    console.print(table)

    if report.deficiencies:
        def_text = "\n".join(f"• [red]KHIẾM KHUYẾT:[/red] {d}" for d in report.deficiencies)
        console.print(Panel(def_text, title="KHIẾM KHUYẾT SOPEP YÊU CẦU ĐÌNH CHỈ RỜI CẢNG THEO PSC TOKYO MOU", border_style="red"))
    else:
        console.print(Panel("[green]Tàu đủ điều kiện an toàn môi trường biển và sẵn sàng ứng phó sự cố tràn dầu.[/green]", title="KẾT LUẬN THẨM ĐỊNH", border_style="green"))


# ==============================================================================
# PHASE 226: MARITIME ENVIRONMENTAL SANCTIONS COMMAND
# ==============================================================================

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

    result = MaritimeEnvironmentalSanctionsEngine.calculate_sanctions(
        vessel_name=vessel,
        infraction=infraction_enum,
        is_repeat_offense=repeat,
        caused_measurable_pollution=pollution,
        refused_cooperation=uncooperative,
    )

    table = Table(title=f"QUYẾT ĐỊNH XỬ PHẠT VI PHẠM MÔI TRƯỜNG BIỂN - {result.vessel_name.upper()}")
    table.add_column("Nội dung quyết định", style="cyan")
    table.add_column("Giá trị áp dụng", style="bold yellow")

    table.add_row("Hành vi vi phạm", result.infraction.value)
    table.add_row("Căn cứ pháp lý", result.statutory_legal_basis)
    table.add_row("Mức phạt tiền khung cơ sở", f"{result.base_fine_vnd:,.0f} VNĐ")
    table.add_row("Hệ số tình tiết tăng nặng", f"{result.aggravating_multiplier:.2f}x")
    table.add_row("TỔNG MỨC PHẠT CHÍNH THỨC", f"[bold red]{result.total_statutory_fine_vnd:,.0f} VNĐ[/bold red]")
    table.add_row("LỆNH LƯU GIỮ TÀU BIỂN (PSC DETENTION)", "[bold red]LƯU GIỮ BẮT BUỘC TẠI CẢNG[/bold red]" if result.psc_detention_ordered else "[green]KHÔNG ÁP DỤNG[/green]")
    table.add_row("Tiền đặt cọc bảo lãnh phong tỏa", f"{result.mandatory_escrow_deposit_vnd:,.0f} VNĐ" if result.mandatory_escrow_deposit_vnd > 0 else "0 VNĐ")

    console.print(table)

    rect_text = f"• [bold yellow]Biện pháp khắc phục hậu quả:[/bold yellow] {result.rectification_order}\n• [bold red]Yêu cầu:[/bold red] Nộp phạt kho bạc nhà nước và hoàn tất biện pháp khắc phục trước khi Cảng vụ cấp phép rời cảng."
    console.print(Panel(rect_text, title="BIỆN PHÁP KHẮC PHỤC HẬU QUẢ BẮT BUỘC", border_style="red" if result.psc_detention_ordered else "yellow"))
