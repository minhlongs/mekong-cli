"""CLI commands for Maritime Bio-Security, IMDG Dangerous Goods, CLC Oil Pollution & Cabotage (Phases 219-222).

Commands:
- mekong ballast / nuocdanthuyen (Phase 219 - BWM 2004 Ballast Water Management)
- mekong imdg / hangnguyhiem (Phase 220 - IMDG Code Dangerous Goods Stowage)
- mekong clc / trachnhiemoil (Phase 221 - CLC 1992 & IOPC Fund Oil Pollution Liability)
- mekong cabotage / vantainoidia (Phase 222 - Coastal Cabotage & Foreign Waiver Licensing)
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.maritime_ballast_imdg_clc_cabotage_engine import (
    BallastWaterManagementEngine,
    BallastWaterAuditReport,
    BallastDischargeSample,
    BwmStandardApplied,
    ImdgCargoSegregationEngine,
    ImdgStowageAuditReport,
    DangerousCargoEntry,
    ClcOilPollutionLiabilityEngine,
    ClcLiabilityAssessment,
    OilPollutionClaimSummary,
    MaritimeCabotageLicensingEngine,
    CabotageLicenseAssessment,
    CabotageCargoType,
)

console = Console()

ballast_app = typer.Typer(
    name="ballast",
    help="Quản lý nước dằn tàu & an toàn sinh học (BWM Convention 2004 & D-2 Standards).",
)
imdg_app = typer.Typer(
    name="imdg",
    help="Phân cách & xếp dỡ hàng hóa nguy hiểm đường biển (IMDG Code Amdt 41-22).",
)
clc_app = typer.Typer(
    name="clc",
    help="Giới hạn trách nhiệm dân sự ô nhiễm dầu tràn (CLC 1992 & IOPC Fund 1992).",
)
cabotage_app = typer.Typer(
    name="cabotage",
    help="Giấy phép vận tải nội địa & miễn trừ tàu biển nước ngoài (VMC Art. 7 & NĐ 58/2017).",
)


# ===========================================================================
# 1. Phase 219: Ballast Water Management Command
# ===========================================================================
@ballast_app.command("audit")
def audit_ballast(
    vessel: str = typer.Option("MV PACIFIC DAWN", help="Tên tàu biển"),
    imo: str = typer.Option("9876543", help="Số IMO tàu"),
    standard: str = typer.Option("D2", help="Tiêu chuẩn áp dụng (D1: Trao đổi nước dằn, D2: Hệ thống xử lý BWMS)"),
    distance_nm: float = typer.Option(250.0, help="Khoảng cách trao đổi cách bờ gần nhất (hải lý)"),
    depth_m: float = typer.Option(500.0, help="Độ sâu vùng biển trao đổi (mét)"),
    volumetric_pct: float = typer.Option(95.0, help="Tỷ lệ trao đổi thể tích (%)"),
    bwms_approved: bool = typer.Option(True, help="Hệ thống BWMS được phê duyệt kiểu dáng Type Approval"),
    bwrb_years: float = typer.Option(2.0, help="Thời gian lưu sổ nhật ký nước dằn trên tàu (năm)"),
    org_50um: float = typer.Option(5.0, help="Số sinh vật sống >= 50um (giới hạn < 10/m3)"),
    org_10_50um: float = typer.Option(4.0, help="Số sinh vật sống 10-50um (giới hạn < 10/mL)"),
    vibrio: float = typer.Option(0.0, help="Toxicogenic Vibrio cholerae (giới hạn < 1 cfu/100mL)"),
    ecoli: float = typer.Option(120.0, help="E. coli (giới hạn < 250 cfu/100mL)"),
    enterococci: float = typer.Option(40.0, help="Intestinal Enterococci (giới hạn < 100 cfu/100mL)"),
):
    """Kiểm tra tuân thủ xả nước dằn theo Công ước BWM 2004 và Thông tư 40/2020/TT-BGTVT."""
    applied_enum = (
        BwmStandardApplied.D1_BALLAST_EXCHANGE
        if standard.upper() == "D1"
        else BwmStandardApplied.D2_TREATMENT_SYSTEM
    )

    sample = BallastDischargeSample(
        tank_identifier="DB_TANK_3P",
        organisms_50um_plus_per_m3=org_50um,
        organisms_10_to_50um_per_ml=org_10_50um,
        vibrio_cholerae_cfu_per_100ml=vibrio,
        escherichia_coli_cfu_per_100ml=ecoli,
        intestinal_enterococci_cfu_per_100ml=enterococci,
    )

    report: BallastWaterAuditReport = BallastWaterManagementEngine.audit_ballast_compliance(
        vessel_name=vessel,
        imo_number=imo,
        standard_applied=applied_enum,
        bwms_type_approved=bwms_approved,
        bwms_active_and_calibrated=True,
        exchange_distance_nm=distance_nm,
        exchange_depth_meters=depth_m,
        volumetric_exchange_percent=volumetric_pct,
        bwrb_years_retained_onboard=bwrb_years,
        sample=sample,
    )

    table = Table(title=f"ĐÁNH GIÁ AN TOÀN SINH HỌC NƯỚC DẰN - {vessel} (IMO: {imo})", header_style="bold cyan")
    table.add_column("Chỉ số kiểm định", style="white")
    table.add_column("Giá trị ghi nhận", style="yellow")
    table.add_column("Trạng thái", style="green")

    table.add_row("Tiêu chuẩn áp dụng", report.standard_applied.value, "Hoạt động")
    table.add_row("Phê duyệt BWMS", str(report.bwms_type_approved), "Hợp lệ" if report.bwms_type_approved else "Cảnh báo")
    table.add_row("Nhật ký BWRB (>=2 năm)", f"{bwrb_years} năm", "Đạt" if report.bwrb_log_compliant else "Không đạt")
    table.add_row("Trao đổi D-1 (Cách bờ / Độ sâu)", f"{report.exchange_distance_nm} nm / {report.exchange_depth_meters} m", "Hợp lệ")
    table.add_row("Quyết định xả nước dằn", "ĐƯỢC PHÉP" if report.discharge_permitted else "BỊ CẤM", "GREEN" if report.discharge_permitted else "RED")

    console.print(table)
    color = "green" if report.discharge_permitted else "red"
    console.print(Panel(f"[{color} bold]{report.verdict}[/{color} bold]", title="Kết luận Cảng vụ"))


# ===========================================================================
# 2. Phase 220: IMDG Code Dangerous Goods Command
# ===========================================================================
@imdg_app.command("segregate")
def segregate_imdg(
    container_a: str = typer.Option("MSKU1234567", help="Mã container kiện hàng A"),
    class_a_str: str = typer.Option("3", help="Nhóm nguy hiểm A (vd: 3, 5.1, 8, 1)"),
    container_b: str = typer.Option("TCLU7654321", help="Mã container kiện hàng B"),
    class_b_str: str = typer.Option("5.1", help="Nhóm nguy hiểm B (vd: 3, 5.1, 8, 1)"),
    distance_m: float = typer.Option(4.0, help="Khoảng cách vật lý giữa 2 container (mét)"),
    bulkheads: int = typer.Option(0, help="Số vách ngăn thép kín cách ly giữa 2 hầm hàng"),
    has_dgd: bool = typer.Option(True, help="Có Bản khai Hàng nguy hiểm (DGD)"),
    has_cpc: bool = typer.Option(True, help="Có Chứng nhận đóng gói Container (CPC)"),
):
    """Kiểm tra phân cách hàng nguy hiểm theo Bảng 7.2.4 IMDG Code và TT 46/2016/TT-BGTVT."""
    c_a = DangerousCargoEntry(
        container_id=container_a,
        un_number="UN1993",
        proper_shipping_name="FLAMMABLE LIQUID, N.O.S.",
        imdg_class=ImdgCargoSegregationEngine.parse_imdg_class(class_a_str),
        packing_group="II",
        bay_row_tier="02-04-82",
    )
    c_b = DangerousCargoEntry(
        container_id=container_b,
        un_number="UN1479",
        proper_shipping_name="OXIDIZING SOLID, N.O.S.",
        imdg_class=ImdgCargoSegregationEngine.parse_imdg_class(class_b_str),
        packing_group="II",
        bay_row_tier="02-06-82",
    )

    report: ImdgStowageAuditReport = ImdgCargoSegregationEngine.audit_stowage_pair(
        cargo_a=c_a,
        cargo_b=c_b,
        physical_distance_meters=distance_m,
        intervening_bulkheads_count=bulkheads,
        has_dangerous_goods_declaration=has_dgd,
        has_container_packing_certificate=has_cpc,
    )

    table = Table(title=f"KIỂM ĐỊNH PHÂN CÁCH IMDG CODE ({container_a} vs {container_b})", header_style="bold magenta")
    table.add_column("Hạng mục kiểm định", style="white")
    table.add_column("Thông số", style="yellow")
    table.add_column("Kết quả", style="green")

    table.add_row("Phân loại A / B", f"{c_a.imdg_class.value} / {c_b.imdg_class.value}", "Xác thực")
    table.add_row("Yêu cầu phân cách (Bảng 7.2.4)", report.required_segregation.value, "Quy định")
    table.add_row("Khoảng cách thực tế", f"{report.physical_distance_meters} m ({bulkheads} vách ngăn)", "Kiểm đo")
    table.add_row("Chứng từ DGD & CPC", f"DGD: {report.dgd_valid} | CPC: {report.cpc_valid}", "Hợp lệ" if (report.dgd_valid and report.cpc_valid) else "Thiếu")
    table.add_row("Đánh giá phân cách", "ĐẠT CHUẨN" if report.segregation_compliant else "VI PHẠM", "GREEN" if report.segregation_compliant else "RED")

    console.print(table)
    color = "green" if report.segregation_compliant else "red"
    console.print(Panel(f"[{color} bold]{report.verdict}[/{color} bold]", title="Phê duyệt Xếp dỡ Cảng"))


# ===========================================================================
# 3. Phase 221: CLC 1992 & IOPC Fund Oil Pollution Command
# ===========================================================================
@clc_app.command("assess")
def assess_oil_pollution(
    incident_ref: str = typer.Option("INC-2026-VUNGTAU-01", help="Mã hồ sơ sự cố ô nhiễm tràn dầu"),
    tanker: str = typer.Option("MT MEKONG PIONEER", help="Tên tàu chở dầu"),
    gt: float = typer.Option(50_000.0, help="Tổng dung tích tàu (Gross Tonnage)"),
    cleanup_usd: float = typer.Option(25_000_000.0, help="Chi phí ứng phó & làm sạch dầu tràn (USD)"),
    fisheries_usd: float = typer.Option(15_000_000.0, help="Thiệt hại kinh tế ngư dân & nuôi trồng thủy sản (USD)"),
    property_usd: float = typer.Option(5_000_000.0, help="Thiệt hại tài sản ven biển & cầu cảng (USD)"),
    environment_usd: float = typer.Option(10_000_000.0, help="Chi phí phục hồi môi trường sinh thái biển (USD)"),
    blue_card: bool = typer.Option(True, help="Giấy chứng nhận bảo hiểm bắt buộc Blue Card hợp lệ"),
    years_damage: float = typer.Option(1.0, help="Số năm kể từ ngày phát sinh thiệt hại (thời hiệu 3 năm)"),
    years_incident: float = typer.Option(1.5, help="Số năm kể từ ngày xảy ra sự cố (thời hiệu 6 năm)"),
    intentional_fault: bool = typer.Option(False, help="Chủ tàu có lỗi cố ý hoặc liều lĩnh với nhận thức hậu quả"),
):
    """Tính toán bồi thường ô nhiễm dầu tràn theo CLC 1992, Quỹ IOPC 1992 và BLLHH 2015."""
    claims = OilPollutionClaimSummary(
        cleanup_and_preventive_costs_usd=cleanup_usd,
        fisheries_economic_loss_usd=fisheries_usd,
        property_damage_usd=property_usd,
        environmental_reinstatement_usd=environment_usd,
    )

    assessment: ClcLiabilityAssessment = ClcOilPollutionLiabilityEngine.evaluate_oil_pollution_claims(
        incident_ref=incident_ref,
        tanker_name=tanker,
        gross_tonnage=gt,
        claims=claims,
        compulsory_blue_card_valid=blue_card,
        years_since_incident=years_incident,
        years_since_damage=years_damage,
        shipowner_intentional_fault=intentional_fault,
    )

    table = Table(title="ĐÁNH GIÁ TRÁCH NHIỆM DÂN SỰ Ô NHIỄM DẦU TRÀN (CLC 1992 & IOPC FUND)", header_style="bold blue")
    table.add_column("Hạng mục bồi thường", style="white")
    table.add_column("Giá trị (SDR / USD)", style="yellow")
    table.add_column("Cơ chế phân bổ", style="cyan")

    table.add_row("Tổng dung tích tàu", f"{gt:,.0f} GT", "Cơ sở tính hạn mức CLC")
    table.add_row("Hạn mức CLC Chủ tàu", f"{assessment.clc_shipowner_limit_sdr:,.2f} SDR (${assessment.clc_shipowner_limit_usd:,.2f})", "Trách nhiệm nghiêm ngặt")
    table.add_row("Hạn mức tối đa Quỹ IOPC", f"{assessment.iopc_fund_ceiling_sdr:,.2f} SDR (${assessment.iopc_fund_ceiling_usd:,.2f})", "Trần đền bù bậc 2")
    table.add_row("Tổng khiếu nại thực tế", f"${assessment.total_claims_usd:,.2f} USD", "Thiệt hại kiểm toán")
    table.add_row("Chủ tàu / Bảo hiểm P&I trả", f"${assessment.shipowner_liability_usd:,.2f} USD", "Bảo lãnh qua Blue Card")
    table.add_row("Quỹ IOPC Fund chi trả", f"${assessment.iopc_fund_contribution_usd:,.2f} USD", "Bù đắp phần vượt CLC")
    table.add_row("Thiệt hại chưa bồi thường", f"${assessment.uncompensated_shortfall_usd:,.2f} USD", "Vượt trần 203M SDR")

    console.print(table)
    color = "red" if assessment.timebar_prescribed else "green"
    console.print(Panel(f"[{color} bold]{assessment.verdict}[/{color} bold]", title="Quyết định Tòa án Hàng hải"))


# ===========================================================================
# 4. Phase 222: Coastal Cabotage & Foreign Waiver Licensing Command
# ===========================================================================
@cabotage_app.command("evaluate")
def evaluate_cabotage(
    ref: str = typer.Option("CAB-2026-DK-09", help="Mã hồ sơ xin cấp phép vận tải nội địa"),
    vessel: str = typer.Option("MV HEAVY CRANE 1", help="Tên tàu xin cấp phép"),
    flag: str = typer.Option("Panama", help="Quốc tịch treo cờ (vd: Vietnam, Panama, Liberia)"),
    gt: float = typer.Option(18_000.0, help="Tổng dung tích tàu (GT)"),
    cargo: str = typer.Option("SPECIALIZED_HEAVY_LIFT_PROJECT", help="Loại hàng vận chuyển nội địa"),
    months: int = typer.Option(6, help="Thời gian xin cấp phép hoạt động nội địa (tháng)"),
    domestic_available: bool = typer.Option(False, help="Đội tàu mang cờ Việt Nam có khả năng đảm nhận"),
    defense_clearance: bool = typer.Option(True, help="Ý kiến đồng thuận của Bộ Quốc phòng / Bộ Công an"),
    vessel_age: float = typer.Option(11.0, help="Tuổi tàu (năm)"),
):
    """Đánh giá cấp phép vận tải nội địa và miễn trừ tàu nước ngoài theo NĐ 58/2017/NĐ-CP."""
    cargo_type_enum = CabotageCargoType.SPECIALIZED_HEAVY_LIFT_PROJECT
    for member in CabotageCargoType:
        if cargo.upper() in member.value:
            cargo_type_enum = member
            break

    assessment: CabotageLicenseAssessment = MaritimeCabotageLicensingEngine.evaluate_cabotage_licensing(
        application_ref=ref,
        vessel_name=vessel,
        flag_state=flag,
        gross_tonnage=gt,
        cargo_type=cargo_type_enum,
        requested_duration_months=months,
        domestic_vietnamese_vessel_available=domestic_available,
        national_defense_clearance=defense_clearance,
        vessel_age_years=vessel_age,
    )

    table = Table(title=f"THẨM ĐỊNH CẤP PHÉP VẬN TẢI BIỂN NỘI ĐỊA (CABOTAGE) - {vessel}", header_style="bold green")
    table.add_column("Tiêu chí xem xét", style="white")
    table.add_column("Hiện trạng hồ sơ", style="yellow")
    table.add_column("Kết quả thẩm định", style="cyan")

    table.add_row("Quốc tịch tàu", flag, "Ưu tiên cờ VN" if flag.lower() in ("vietnam", "vn") else "Tàu nước ngoài")
    table.add_row("Loại hình vận tải", assessment.operation_type.value, "Đặc thù" if assessment.domestic_fleet_deficit_verified else "Thông thường")
    table.add_row("Đội tàu trong nước thiếu hụt", "ĐÃ XÁC THỰC" if assessment.domestic_fleet_deficit_verified else "CÓ SẴN ĐỘI TÀU VN", "Căn cứ cấp phép")
    table.add_row("An ninh - Quốc phòng", "CHẤP THUẬN" if assessment.national_defense_clearance_granted else "TỪ CHỐI", "Bắt buộc")
    table.add_row("Thời hạn cấp phép", f"{assessment.permit_duration_months} tháng", "Hợp lệ (<= 6 tháng)")
    table.add_row("Phí phụ thu nhà nước", f"${assessment.statutory_cabotage_surcharge_usd:,.2f} USD", "Nộp ngân sách")
    table.add_row("Kết luận cấp phép", "ĐƯỢC CẤP PHÉP" if assessment.license_granted else "TỪ CHỐI", "GREEN" if assessment.license_granted else "RED")

    console.print(table)
    color = "green" if assessment.license_granted else "red"
    console.print(Panel(f"[{color} bold]{assessment.verdict}[/{color} bold]", title="Quyết định Cục Hàng hải Việt Nam"))
