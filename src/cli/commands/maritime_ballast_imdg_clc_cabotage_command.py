"""CLI commands for Maritime Bio-Security, IMDG Dangerous Goods, CLC Oil Pollution & Cabotage (Phases 219-222)."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.maritime_ballast_imdg_clc_cabotage_engine import (
    BallastWaterManagementEngine, BallastWaterAuditReport, BallastDischargeSample, BwmStandardApplied,
    ImdgCargoSegregationEngine, ImdgStowageAuditReport, DangerousCargoEntry,
    ClcOilPollutionLiabilityEngine, ClcLiabilityAssessment, OilPollutionClaimSummary,
    MaritimeCabotageLicensingEngine, CabotageLicenseAssessment, CabotageCargoType,
)

console = Console()

ballast_app = typer.Typer(name="ballast", help="Quản lý nước dằn tàu & an toàn sinh học (BWM Convention 2004 & D-2 Standards).")
imdg_app = typer.Typer(name="imdg", help="Phân cách & xếp dỡ hàng hóa nguy hiểm đường biển (IMDG Code Amdt 41-22).")
clc_app = typer.Typer(name="clc", help="Giới hạn trách nhiệm dân sự ô nhiễm dầu tràn (CLC 1992 & IOPC Fund 1992).")
cabotage_app = typer.Typer(name="cabotage", help="Giấy phép vận tải nội địa & miễn trừ tàu biển nước ngoài (VMC Art. 7 & NĐ 58/2017).")


def _render_audit(title: str, h_style: str, cols: list[tuple[str, str]], rows: list[tuple[str, str, str]], verdict: str, ok: bool, p_title: str) -> None:
    table = Table(title=title, header_style=h_style)
    for c_name, c_style in cols:
        table.add_column(c_name, style=c_style)
    for r in rows:
        table.add_row(*r)
    console.print(table)
    color = "green" if ok else "red"
    console.print(Panel(f"[{color} bold]{verdict}[/{color} bold]", title=p_title))


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
    applied_enum = BwmStandardApplied.D1_BALLAST_EXCHANGE if standard.upper() == "D1" else BwmStandardApplied.D2_TREATMENT_SYSTEM
    sample = BallastDischargeSample("DB_TANK_3P", org_50um, org_10_50um, vibrio, ecoli, enterococci)
    report: BallastWaterAuditReport = BallastWaterManagementEngine.audit_ballast_compliance(
        vessel_name=vessel, imo_number=imo, standard_applied=applied_enum,
        bwms_type_approved=bwms_approved, bwms_active_and_calibrated=True,
        exchange_distance_nm=distance_nm, exchange_depth_meters=depth_m,
        volumetric_exchange_percent=volumetric_pct, bwrb_years_retained_onboard=bwrb_years, sample=sample,
    )
    _render_audit(
        f"ĐÁNH GIÁ AN TOÀN SINH HỌC NƯỚC DẰN - {vessel} (IMO: {imo})", "bold cyan",
        [("Chỉ số kiểm định", "white"), ("Giá trị ghi nhận", "yellow"), ("Trạng thái", "green")],
        [
            ("Tiêu chuẩn áp dụng", report.standard_applied.value, "Hoạt động"),
            ("Phê duyệt BWMS", str(report.bwms_type_approved), "Hợp lệ" if report.bwms_type_approved else "Cảnh báo"),
            ("Nhật ký BWRB (>=2 năm)", f"{bwrb_years} năm", "Đạt" if report.bwrb_log_compliant else "Không đạt"),
            ("Trao đổi D-1 (Cách bờ / Độ sâu)", f"{report.exchange_distance_nm} nm / {report.exchange_depth_meters} m", "Hợp lệ"),
            ("Quyết định xả nước dằn", "ĐƯỢC PHÉP" if report.discharge_permitted else "BỊ CẤM", "GREEN" if report.discharge_permitted else "RED"),
        ],
        report.verdict, report.discharge_permitted, "Kết luận Cảng vụ",
    )


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
    c_a = DangerousCargoEntry(container_a, "UN1993", "FLAMMABLE LIQUID, N.O.S.", ImdgCargoSegregationEngine.parse_imdg_class(class_a_str), "II", "02-04-82")
    c_b = DangerousCargoEntry(container_b, "UN1479", "OXIDIZING SOLID, N.O.S.", ImdgCargoSegregationEngine.parse_imdg_class(class_b_str), "II", "02-06-82")
    report: ImdgStowageAuditReport = ImdgCargoSegregationEngine.audit_stowage_pair(c_a, c_b, distance_m, bulkheads, has_dgd, has_cpc)
    _render_audit(
        f"KIỂM ĐỊNH PHÂN CÁCH IMDG CODE ({container_a} vs {container_b})", "bold magenta",
        [("Hạng mục kiểm định", "white"), ("Thông số", "yellow"), ("Kết quả", "green")],
        [
            ("Phân loại A / B", f"{c_a.imdg_class.value} / {c_b.imdg_class.value}", "Xác thực"),
            ("Yêu cầu phân cách (Bảng 7.2.4)", report.required_segregation.value, "Quy định"),
            ("Khoảng cách thực tế", f"{report.physical_distance_meters} m ({bulkheads} vách ngăn)", "Kiểm đo"),
            ("Chứng từ DGD & CPC", f"DGD: {report.dgd_valid} | CPC: {report.cpc_valid}", "Hợp lệ" if (report.dgd_valid and report.cpc_valid) else "Thiếu"),
            ("Đánh giá phân cách", "ĐẠT CHUẨN" if report.segregation_compliant else "VI PHẠM", "GREEN" if report.segregation_compliant else "RED"),
        ],
        report.verdict, report.segregation_compliant, "Phê duyệt Xếp dỡ Cảng",
    )


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
    claims = OilPollutionClaimSummary(cleanup_usd, fisheries_usd, property_usd, environment_usd)
    a: ClcLiabilityAssessment = ClcOilPollutionLiabilityEngine.evaluate_oil_pollution_claims(
        incident_ref, tanker, gt, claims, blue_card, years_incident, years_damage, intentional_fault,
    )
    _render_audit(
        "ĐÁNH GIÁ TRÁCH NHIỆM DÂN SỰ Ô NHIỄM DẦU TRÀN (CLC 1992 & IOPC FUND)", "bold blue",
        [("Hạng mục bồi thường", "white"), ("Giá trị (SDR / USD)", "yellow"), ("Cơ chế phân bổ", "cyan")],
        [
            ("Tổng dung tích tàu", f"{gt:,.0f} GT", "Cơ sở tính hạn mức CLC"),
            ("Hạn mức CLC Chủ tàu", f"{a.clc_shipowner_limit_sdr:,.2f} SDR (${a.clc_shipowner_limit_usd:,.2f})", "Trách nhiệm nghiêm ngặt"),
            ("Hạn mức tối đa Quỹ IOPC", f"{a.iopc_fund_ceiling_sdr:,.2f} SDR (${a.iopc_fund_ceiling_usd:,.2f})", "Trần đền bù bậc 2"),
            ("Tổng khiếu nại thực tế", f"${a.total_claims_usd:,.2f} USD", "Thiệt hại kiểm toán"),
            ("Chủ tàu / Bảo hiểm P&I trả", f"${a.shipowner_liability_usd:,.2f} USD", "Bảo lãnh qua Blue Card"),
            ("Quỹ IOPC Fund chi trả", f"${a.iopc_fund_contribution_usd:,.2f} USD", "Bù đắp phần vượt CLC"),
            ("Thiệt hại chưa bồi thường", f"${a.uncompensated_shortfall_usd:,.2f} USD", "Vượt trần 203M SDR"),
        ],
        a.verdict, not a.timebar_prescribed, "Quyết định Tòa án Hàng hải",
    )


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
    cargo_type_enum = next((m for m in CabotageCargoType if cargo.upper() in m.value), CabotageCargoType.SPECIALIZED_HEAVY_LIFT_PROJECT)
    a: CabotageLicenseAssessment = MaritimeCabotageLicensingEngine.evaluate_cabotage_licensing(
        ref, vessel, flag, gt, cargo_type_enum, months, domestic_available, defense_clearance, vessel_age,
    )
    _render_audit(
        f"THẨM ĐỊNH CẤP PHÉP VẬN TẢI BIỂN NỘI ĐỊA (CABOTAGE) - {vessel}", "bold green",
        [("Tiêu chí xem xét", "white"), ("Hiện trạng hồ sơ", "yellow"), ("Kết quả thẩm định", "cyan")],
        [
            ("Quốc tịch tàu", flag, "Ưu tiên cờ VN" if flag.lower() in ("vietnam", "vn") else "Tàu nước ngoài"),
            ("Loại hình vận tải", a.operation_type.value, "Đặc thù" if a.domestic_fleet_deficit_verified else "Thông thường"),
            ("Đội tàu trong nước thiếu hụt", "ĐÃ XÁC THỰC" if a.domestic_fleet_deficit_verified else "CÓ SẴN ĐỘI TÀU VN", "Căn cứ cấp phép"),
            ("An ninh - Quốc phòng", "CHẤP THUẬN" if a.national_defense_clearance_granted else "TỪ CHỐI", "Bắt buộc"),
            ("Thời hạn cấp phép", f"{a.permit_duration_months} tháng", "Hợp lệ (<= 6 tháng)"),
            ("Phí phụ thu nhà nước", f"${a.statutory_cabotage_surcharge_usd:,.2f} USD", "Nộp ngân sách"),
            ("Kết luận cấp phép", "ĐƯỢC CẤP PHÉP" if a.license_granted else "TỪ CHỐI", "GREEN" if a.license_granted else "RED"),
        ],
        a.verdict, a.license_granted, "Quyết định Cục Hàng hải Việt Nam",
    )
