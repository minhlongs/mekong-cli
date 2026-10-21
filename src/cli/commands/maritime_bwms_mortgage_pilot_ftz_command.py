"""CLI Commands for BWMS D-2 Compliance, Ship Mortgage, Pilotage & Seaport FTZ Suite (Phases 279-282)."""

import typer
from src.core.maritime_bwms_mortgage_pilot_ftz_engine import (
    BwmsComplianceEngine, BwmSampleInput, ShipMortgageEnforcementEngine, ShipMortgageClaim,
    MortgageClaimCategory, MaritimePilotageDuesEngine, PilotageZone,
    SeaportFtzTransshipmentEngine, TransshipmentCargoInput, GeoCoordinate,
)

bwms_app = typer.Typer(help="Ballast Water Management (BWMS) D-2 & D-1 Standards Calculator (Phase 279)")
mortgage_app = typer.Typer(help="Ship Mortgage Enforcement & Escrow Proceeds Distributor (Phase 280)")
pilotage_app = typer.Typer(help="Maritime Pilotage Service Allocation & Tariff Engine (Phase 281)")
ftz_app = typer.Typer(help="Seaport FTZ / Transshipment Cargo E-Seal Supervision Engine (Phase 282)")

_SEP = "=" * 80
_SUB = "-" * 80


@bwms_app.command("evaluate")
def evaluate_bwms_compliance(
    vessel: str = typer.Option("MV MEKONG DISCOVERY", "--vessel", "-v", help="Vessel name"),
    imo: str = typer.Option("9876543", "--imo", help="IMO number"),
    org_ge_50um: float = typer.Option(2.0, "--org-50", help="Viable organisms >= 50 um per m3"),
    org_10_50um: float = typer.Option(4.0, "--org-10", help="Viable organisms 10 to 50 um per mL"),
    vibrio: float = typer.Option(0.0, "--vibrio", help="Vibrio cholerae cfu per 100 mL"),
    e_coli: float = typer.Option(45.0, "--ecoli", help="E. coli cfu per 100 mL"),
    enterococci: float = typer.Option(12.0, "--enterococci", help="Intestinal enterococci cfu per 100 mL"),
    raw_tro: float = typer.Option(3.50, "--raw-tro", help="Raw Total Residual Oxidant (TRO) in mg/L"),
    neutral_tro: float = typer.Option(0.04, "--neutral-tro", help="Neutralized TRO at discharge in mg/L"),
    flow_rate: float = typer.Option(1200.0, "--flow", help="Discharge flow rate in m3/h"),
    distance_nm: float = typer.Option(250.0, "--dist", help="Distance from land in nautical miles"),
    water_depth: float = typer.Option(300.0, "--depth", help="Water depth in meters"),
):
    """Evaluate Ballast Water Management System (BWMS) D-2 biological limits & TRO neutralization."""
    sample = BwmSampleInput(org_ge_50um, org_10_50um, vibrio, e_coli, enterococci, raw_tro, neutral_tro, flow_rate, distance_nm, water_depth)
    result = BwmsComplianceEngine.evaluate_compliance(vessel, imo, sample)
    lines = [
        _SEP, "ĐÁNH GIÁ XẢ NƯỚC DẰN TÀU (BWMS) & CHUẨN D-2 / D-1 (IMO BWM CONVENTION)", _SEP,
        f"Tàu: {vessel} | IMO: {imo}",
        f"Trạng thái tuân thủ: {result.compliance_status.value}",
        f"- Đạt chuẩn sinh học D-2: {'CÓ' if result.d2_biological_pass else 'KHÔNG'}",
        f"- Đạt nồng độ TRO xả thải (<= 0.10 mg/L): {'CÓ' if result.tro_discharge_compliant else 'KHÔNG'}",
        f"- Suất hóa chất trung hòa NaHSO3: {result.required_neutralizer_rate_kg_h:.2f} kg/h",
    ]
    if result.contingency_action:
        lines.append(f"- Biện pháp dự phòng / Cảnh báo: {result.contingency_action}")
    lines.extend([f"Mã chứng chỉ điện tử: {result.verification_hash}", _SEP])
    typer.echo("\n".join(lines))


@mortgage_app.command("enforce")
def enforce_ship_mortgage(
    vessel: str = typer.Option("MV MEKONG VOYAGER", "--vessel", "-v", help="Vessel name"),
    registry: str = typer.Option("VN-1092-HP", "--reg", help="Vessel registration number"),
    proceeds: float = typer.Option(80_000_000_000.0, "--proceeds", help="Gross sale proceeds in VND"),
    notice_days: int = typer.Option(20, "--notice", help="Days elapsed since statutory notice under Art. 34"),
    costs: float = typer.Option(3_000_000_000.0, "--costs", help="Judicial and enforcement costs in VND"),
    liens: float = typer.Option(12_000_000_000.0, "--liens", help="Statutory maritime liens under Art. 37"),
    mortgage1_principal: float = typer.Option(50_000_000_000.0, "--m1-pr", help="1st mortgage principal in VND"),
    mortgage1_interest: float = typer.Option(4_000_000_000.0, "--m1-int", help="1st mortgage interest in VND"),
    mortgage2_principal: float = typer.Option(15_000_000_000.0, "--m2-pr", help="2nd mortgage principal in VND"),
    mortgage2_interest: float = typer.Option(1_000_000_000.0, "--m2-int", help="2nd mortgage interest in VND"),
):
    """Enforce ship mortgage disposal and calculate escrow proceeds waterfall distribution."""
    claims = [
        ShipMortgageClaim("COSTS-01", "Tòa án / Tổ chức đấu giá tài sản", MortgageClaimCategory.ENFORCEMENT_COSTS, 0, costs),
        ShipMortgageClaim("LIEN-01", "Thuyền viên & Cảng vụ (Quyền cầm giữ Đ.37)", MortgageClaimCategory.MARITIME_LIEN, 0, liens),
        ShipMortgageClaim("MORT-01", "Ngân hàng Ngoại thương (Thế chấp hạng 1)", MortgageClaimCategory.REGISTERED_MORTGAGE, 1, mortgage1_principal, mortgage1_interest, 11.5),
        ShipMortgageClaim("MORT-02", "Ngân hàng Công thương (Thế chấp hạng 2)", MortgageClaimCategory.REGISTERED_MORTGAGE, 2, mortgage2_principal, mortgage2_interest, 13.0),
    ]
    report = ShipMortgageEnforcementEngine.process_enforcement_waterfall(vessel, registry, proceeds, notice_days, claims)
    lines = [
        _SEP, "XỬ LÝ THẾ CHẤP TÀU BIỂN & PHÂN BỔ THÁC NƯỚC (BỘ LUẬT HÀNG HẢI VIỆT NAM 2015)", _SEP,
        f"Tàu: {vessel} (Số ĐK: {registry})",
        f"Tổng tiền thu hồi: {report.gross_proceeds_vnd:,.0f} VND",
        f"Hợp lệ thời hạn thông báo (>= 15 ngày): {'HỢP LỆ' if report.statutory_notice_valid else 'VI PHẠM'}",
        _SUB,
    ]
    for alloc in report.allocations:
        lines.append(f"[{alloc.category}] {alloc.creditor_name}:")
        lines.append(f"  Yêu cầu: {alloc.claimed_amount_vnd:,.0f} VND | Phân bổ: {alloc.allocated_amount_vnd:,.0f} VND | Còn lại: {alloc.unpaid_balance_vnd:,.0f} VND")
    lines.extend([
        _SUB, f"Tổng đã thanh toán: {report.total_claims_satisfied_vnd:,.0f} VND",
        f"Số dư hoàn trả chủ tàu: {report.shipowner_residual_vnd:,.0f} VND",
        f"Mã ủy thác thi hành: {report.auth_token}", _SEP,
    ])
    typer.echo("\n".join(lines))


@pilotage_app.command("dues")
def calculate_pilotage_dues(
    vessel: str = typer.Option("MV MEKONG NAVIGATOR", "--vessel", "-v", help="Vessel name"),
    gt: float = typer.Option(18500.0, "--gt", help="Vessel Gross Tonnage (GT)"),
    dist_nm: float = typer.Option(22.5, "--dist", help="Pilotage distance in nautical miles"),
    zone_str: str = typer.Option("ZONE_I", "--zone", help="Pilotage Zone (ZONE_I, ZONE_II, ZONE_III)"),
    freeboard: float = typer.Option(10.2, "--freeboard", help="Actual freeboard in meters"),
    climbing_height: float = typer.Option(6.5, "--climb", help="Climbing height on pilot ladder in meters"),
    ladder_angle: float = typer.Option(40.0, "--angle", help="Accommodation ladder angle in degrees"),
    night: bool = typer.Option(True, "--night", help="Is night navigation (18:00 - 06:00)?"),
    weather_hours: float = typer.Option(2.0, "--weather-wait", help="Weather standby hours"),
    is_exempt: bool = typer.Option(False, "--exempt", help="Statutory exemption applied"),
):
    """Calculate maritime pilotage service tariffs, surcharges & SOLAS V/23 ladder safety."""
    calc = MaritimePilotageDuesEngine.calculate_pilotage_dues(
        vessel, gt, dist_nm, PilotageZone[zone_str.upper()], freeboard, climbing_height, ladder_angle, night, weather_hours, is_exempt
    )
    lines = [
        _SEP, "ĐIỀU ĐỘ HOA TIÊU HÀNG HẢI & TÍNH CƯỚC HOA TIÊU (THÔNG TƯ 39/2023/TT-BGTVT)", _SEP,
        f"Tàu: {vessel} | GT: {gt:,.0f} | Cự ly: {dist_nm} NM | Vùng: {calc.zone.value}",
        "KIỂM TRA AN TOÀN THANG HOA TIÊU (SOLAS REG. V/23):",
        f"- Bố trí: {calc.ladder_safety.required_arrangement.value}",
        f"- An toàn bố trí thang: {'ĐẠT' if calc.ladder_safety.is_safe else 'KHÔNG ĐẠT'}",
        *[f"  * Cảnh báo: {v}" for v in calc.ladder_safety.violations],
        _SUB,
    ]
    if calc.is_exempt:
        lines.append(f"MIỄN HOA TIÊU LUẬT ĐỊNH: {calc.exemption_reason}")
    else:
        lines.extend([
            f"Cước cơ bản:          ${calc.base_charge_usd:,.2f} USD",
            f"Phụ thu ban đêm (+40%):+${calc.night_surcharge_usd:,.2f} USD",
            f"Phí chờ đợi thời tiết: +${calc.weather_standby_charge_usd:,.2f} USD",
            f"TỔNG CƯỚC HOA TIÊU:   ${calc.total_dues_usd:,.2f} USD ({calc.total_dues_vnd:,.0f} VND)",
        ])
    lines.extend([f"Biên lai thu cước:    {calc.receipt_code}", _SEP])
    typer.echo("\n".join(lines))


@ftz_app.command("supervise")
def supervise_ftz_cargo(
    declaration: str = typer.Option("OTL-2026-TC98124", "--dec", help="Transshipment customs declaration number"),
    container: str = typer.Option("CMDU9128471", "--cont", help="Container number"),
    discharge_date: str = typer.Option("2026-09-18", "--discharge", help="Discharge date (YYYY-MM-DD)"),
    current_date: str = typer.Option("2026-10-08", "--current", help="Current date (YYYY-MM-DD)"),
    extension: bool = typer.Option(False, "--extension", help="Extension approved"),
    lat: float = typer.Option(10.6420, "--lat", help="Current latitude"),
    lon: float = typer.Option(106.8427, "--lon", help="Current longitude"),
    cable_intact: bool = typer.Option(True, "--cable", help="Is e-seal cable intact?"),
    tamper_switch: bool = typer.Option(False, "--tamper", help="Tamper switch triggered?"),
    battery: float = typer.Option(85.0, "--battery", help="Battery percentage"),
):
    """Supervise international transshipment cargo dwell limit & smart E-seal GPS corridor."""
    cargo_input = TransshipmentCargoInput(
        declaration_no=declaration, container_no=container, discharge_date=discharge_date, current_date=current_date,
        extension_approved=extension, current_coordinate=GeoCoordinate(lat, lon),
        e_seal_cable_intact=cable_intact, e_seal_tamper_switch=tamper_switch, battery_level_pct=battery,
    )
    result = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo_input)
    typer.echo("\n".join([
        _SEP, "GIÁM SÁT HÀNG TRUNG CHUYỂN QUỐC TẾ & NIÊM PHONG E-SEAL (LUẬT HẢI QUAN 2014)", _SEP,
        f"Tờ khai: {declaration} | Container: {container}",
        f"Thời gian lưu bãi: {result.dwell_days} ngày | Tình trạng: {result.dwell_status.value}",
        f"Trạng thái E-seal: {result.e_seal_status.value}",
        f"Độ lệch hành lang: {result.corridor_deviation_meters:.1f} m",
        f"Thông quan hợp lệ: {'ĐẠT CHUẨN' if result.statutory_clearance_granted else 'TẠM GIỮ / CẢNH BÁO'}",
        f"Chỉ đạo nghiệp vụ: {result.action_required}",
        f"Mã định danh SHA-256: {result.integrity_token}", _SEP,
    ]))
