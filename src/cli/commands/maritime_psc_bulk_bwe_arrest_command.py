"""CLI Commands for Maritime PSC Targeting, Bulk Cargo Safety, BWE & Vessel Arrest (Phases 315-318)."""

import typer

from src.core.maritime_psc_bulk_bwe_arrest_engine import (
    BallastWaterComplianceEngine,
    BallastWaterInput,
    BulkCargoInput,
    BulkCargoLiquefactionEngine,
    BwmStandard,
    FlagPerformance,
    ImsbcCargoGroup,
    MaritimeClaimItem,
    MaritimeClaimRank,
    PscTargetingEngine,
    PscTargetingInput,
    RoPerformance,
    VesselArrestWaterfallEngine,
)

psc_app = typer.Typer(help="Tokyo MoU Port State Control (PSC) Targeting & Risk Matrix (Phase 315)")
bulk_app = typer.Typer(help="IMSBC Solid Bulk Cargo Liquefaction & TML/FMP Safety (Phase 316)")
bwe_app = typer.Typer(help="Ballast Water Management D-1 Exchange vs D-2 Treatment (Phase 317)")
arrest_app = typer.Typer(help="Maritime Lien & Vessel Arrest Proceeds Waterfall (Phase 318)")


@psc_app.command("check")
def check_psc_targeting(
    imo: str = typer.Option("IMO9876543", "--imo", help="Số định danh IMO tàu biển"),
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", "-v", help="Tên tàu biển"),
    flag: str = typer.Option("Panama", "--flag", "-f", help="Quốc gia mang cờ"),
    flag_perf: str = typer.Option("WHITE", "--flag-perf", help="Hiệu suất cờ (WHITE, GREY, BLACK)"),
    ro_perf: str = typer.Option("HIGH", "--ro-perf", help="Hiệu suất tổ chức Đăng kiểm RO (HIGH, MEDIUM, LOW, VERY_LOW)"),
    age: int = typer.Option(8, "--age", "-a", help="Tuổi tàu (năm)"),
    high_risk_type: bool = typer.Option(False, "--high-risk-type", help="Loại tàu rủi ro cao (Tanker, Bulker, Passenger)"),
    deficiencies: int = typer.Option(3, "--deficiencies", "-d", help="Số lỗi PSC ghi nhận trong 36 tháng qua"),
    detentions: int = typer.Option(0, "--detentions", help="Số lần bị lưu giữ tàu PSC trong 36 tháng qua"),
    months_psc: int = typer.Option(5, "--months-psc", "-m", help="Số tháng kể từ lần kiểm tra PSC gần nhất"),
    critical_def: bool = typer.Option(False, "--code30", help="Có khiếm khuyết nghiêm trọng Code 30 tại chỗ hay không"),
):
    """Tính toán hồ sơ rủi ro tàu (Ship Risk Profile) & mức ưu tiên kiểm tra Tokyo MoU."""
    try:
        f_perf = FlagPerformance(flag_perf.upper())
    except ValueError:
        f_perf = FlagPerformance.WHITE
    try:
        r_perf = RoPerformance(ro_perf.upper())
    except ValueError:
        r_perf = RoPerformance.HIGH
    inp = PscTargetingInput(
        imo_number=imo, vessel_name=vessel, flag=flag, flag_performance=f_perf,
        recognized_org_performance=r_perf, vessel_age_years=age, is_high_risk_ship_type=high_risk_type,
        deficiencies_last_36m=deficiencies, detentions_last_36m=detentions,
        months_since_last_psc=months_psc, critical_deficiency_present=critical_def,
    )
    res = PscTargetingEngine.evaluate_targeting(inp)
    typer.echo("=" * 80)
    typer.echo("ĐÁNH GIÁ HỒ SƠ RỦI RO & MỨC ĐỘ ƯU TIÊN KIỂM TRA TOKYO MOU PSC")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {res.vessel_name} (IMO: {res.imo_number}) | Quốc tịch: {flag}")
    typer.echo(f"Hồ sơ rủi ro tàu: {res.ship_risk_profile.value} (Tổng điểm rủi ro: {res.risk_score_points})")
    typer.echo(f"Khung cửa sổ kiểm tra định kỳ: {res.eligible_inspection_window} | Mức độ ưu tiên: {res.priority_level.value}")
    typer.echo("-" * 80)
    typer.echo(f"Nguy cơ lưu giữ tàu (Detention Ground): {'CÓ (RẤT NGUY HIỂM)' if res.grounds_for_detention else 'KHÔNG'}")
    typer.echo(f"Chi tiết đánh giá: {res.remarks}\nMã tra cứu xác thực: {res.audit_hash}\n" + "=" * 80)


@bulk_app.command("safety-check")
def evaluate_bulk_cargo_safety(
    cargo: str = typer.Option("Nickel Ore", "--cargo", "-c", help="Tên mặt hàng rời"),
    group: str = typer.Option("GROUP_A", "--group", "-g", help="Nhóm hàng IMSBC (GROUP_A, GROUP_B, GROUP_C)"),
    tonnage: float = typer.Option(50000.0, "--tonnage", "-t", help="Tổng khối lượng hàng dự kiến xếp (MT)"),
    fmp: float = typer.Option(34.0, "--fmp", help="Điểm độ ẩm dòng chảy FMP (%)"),
    mc: float = typer.Option(29.0, "--mc", help="Độ ẩm thực tế đo tại bãi MC (%)"),
    cert_days: int = typer.Option(3, "--cert-days", help="Số ngày kể từ khi cấp chứng thư độ ẩm"),
):
    """Kiểm tra giới hạn độ ẩm vận chuyển an toàn TML & rủi ro hóa lỏng hàng rời IMSBC."""
    try:
        c_group = ImsbcCargoGroup(group.upper())
    except ValueError:
        c_group = ImsbcCargoGroup.GROUP_A
    inp = BulkCargoInput(
        cargo_name=cargo, cargo_group=c_group, total_metric_tons=tonnage,
        flow_moisture_point_pct=fmp, actual_moisture_content_pct=mc, certificate_age_days=cert_days,
    )
    res = BulkCargoLiquefactionEngine.evaluate_cargo_safety(inp)
    typer.echo("=" * 80)
    typer.echo("KIỂM TRA GIỚI HẠN ĐỘ ẨM TML & AN TOÀN HÓA LỎNG HÀNG RỜI (IMSBC CODE)")
    typer.echo("=" * 80)
    typer.echo(f"Mặt hàng: {res.cargo_name} | Phân nhóm IMSBC: {res.cargo_group.value} | Khối lượng: {tonnage:,.0f} MT")
    if res.cargo_group == ImsbcCargoGroup.GROUP_A:
        typer.echo(f"Điểm dòng chảy FMP: {res.fmp_pct:.1f}% | Giới hạn độ ẩm vận chuyển TML (90% FMP): {res.tml_pct:.1f}%")
        typer.echo(f"Độ ẩm thực tế đo được (MC): {res.actual_mc_pct:.1f}% | Độ lệch vượt ngưỡng: {res.moisture_excess_pct:+.1f}%")
    typer.echo("-" * 80)
    typer.echo(f"Đủ điều kiện xếp hàng lên tàu: {'ĐỦ ĐIỀU KIỆN (SAFE TO LOAD)' if res.is_safe_to_load else 'CẤM XẾP HÀNG (PROHIBITED)'}")
    typer.echo(f"Yêu cầu thử nghiệm Canister tại hiện trường: {'CÓ' if res.canister_test_required else 'KHÔNG'}")
    typer.echo(f"Kết luận & Khuyến cáo: {res.remarks}\nMã chứng chỉ an toàn: {res.audit_hash}\n" + "=" * 80)


@bwe_app.command("verify")
def verify_ballast_water(
    vessel: str = typer.Option("MV MEKONG CHALLENGER", "--vessel", "-v", help="Tên tàu xả nước dằn"),
    standard: str = typer.Option("D1_EXCHANGE", "--standard", "-s", help="Tiêu chuẩn áp dụng (D1_EXCHANGE, D2_TREATMENT)"),
    capacity: float = typer.Option(6000.0, "--capacity", help="Tổng dung tích két nước dằn (m³)"),
    pumped: float = typer.Option(18000.0, "--pumped", help="Thể tích nước đã bơm trao đổi (m³)"),
    distance: float = typer.Option(220.0, "--distance", "-d", help="Khoảng cách tính từ bờ gần nhất (hải lý)"),
    depth: float = typer.Option(500.0, "--depth", help="Độ sâu đáy biển tại vị trí thao tác (m)"),
    bwms_ok: bool = typer.Option(True, "--bwms-ok", help="Hệ thống BWMS hoạt động bình thường (đối với chuẩn D-2)"),
    tro: float = typer.Option(0.5, "--tro", help="Dư lượng chất khử oxy hóa TRO (ppm)"),
):
    """Kiểm tra tuân thủ Công ước Quản lý Nước dằn BWM (Tiêu chuẩn D-1 vs D-2)."""
    try:
        std = BwmStandard(standard.upper())
    except ValueError:
        std = BwmStandard.D1_EXCHANGE
    inp = BallastWaterInput(
        vessel_name=vessel, standard_applied=std, tank_capacity_m3=capacity, pumped_volume_m3=pumped,
        distance_from_land_nm=distance, water_depth_m=depth, bwms_operational=bwms_ok, active_substance_tro_ppm=tro,
    )
    res = BallastWaterComplianceEngine.evaluate_compliance(inp)
    typer.echo("=" * 80)
    typer.echo("THẨM TRA TUÂN THỦ CÔNG ƯỚC NƯỚC DẰN BWM CONVENTION (TIÊU CHUẨN D-1 / D-2)")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {res.vessel_name} | Tiêu chuẩn khai báo: {res.standard_applied.value}")
    if res.standard_applied == BwmStandard.D1_EXCHANGE:
        typer.echo(f"Hiệu suất trao đổi thể tích: {res.exchange_efficiency_pct:.1f}% (Bơm {pumped:,.0f} m³ / Két {capacity:,.0f} m³)")
        typer.echo(f"Khoảng cách cách bờ: {distance:.0f} NM (Hợp lệ: {res.distance_compliant}) | Độ sâu nước: {depth:.0f}m (Hợp lệ: {res.depth_compliant})")
    typer.echo("-" * 80)
    typer.echo(f"Cấp phép xả nước dằn: {'CHO PHÉP XẢ (PERMITTED)' if res.is_discharge_permitted else 'CẤM XẢ (PROHIBITED)'}")
    typer.echo(f"Ghi chú kiểm tra: {res.remarks}\nMã tra cứu nhật ký nước dằn: {res.audit_hash}\n" + "=" * 80)


@arrest_app.command("waterfall")
def calculate_arrest_waterfall(
    vessel: str = typer.Option("MV OCEAN PHOENIX", "--vessel", "-v", help="Tên tàu bị bắt giữ & bán đấu giá"),
    proceeds: float = typer.Option(40000000000.0, "--proceeds", "-p", help="Số tiền thu được từ bán đấu giá tàu (VND)"),
):
    """Tính toán thứ tự ưu tiên thanh toán khiếu nại & bán đấu giá tàu (Điều 37 Bộ luật HHVN)."""
    claims = [
        MaritimeClaimItem("CLM-01", "Chi phí bảo quản & Tòa án thụ lý", MaritimeClaimRank.RANK_0_COURT_CUSTODY, 1_500_000_000.0),
        MaritimeClaimItem("CLM-02", "Lương nợ 15 Thuyền viên & Hồi hương", MaritimeClaimRank.RANK_1_CREW_WAGES, 4_200_000_000.0),
        MaritimeClaimItem("CLM-03", "Phí hoa tiêu & Cảng phí Cảng vụ", MaritimeClaimRank.RANK_4_PORT_DUES, 2_800_000_000.0),
        MaritimeClaimItem("CLM-04", "Thế chấp Tàu biển (Ngân hàng Hàng hải)", MaritimeClaimRank.RANK_6_MORTGAGE, 45_000_000_000.0),
        MaritimeClaimItem("CLM-05", "Nợ tiền cấp dầu FO (Nhà cung cấp)", MaritimeClaimRank.RANK_7_UNSECURED, 8_000_000_000.0),
    ]
    res = VesselArrestWaterfallEngine.calculate_waterfall(vessel, proceeds, claims)
    typer.echo("=" * 80)
    typer.echo("PHÂN BỔ NGUỒN TIỀN BÁN ĐẤU GIÁ TÀU THEO QUYỀN CẦM GIỮ (ĐIỀU 37 BỘ LUẬT HHVN)")
    typer.echo("=" * 80)
    typer.echo(f"Tàu bán đấu giá: {res.vessel_name} | Tổng tiền đấu giá: {res.total_auction_proceeds_vnd:,.0f} VND")
    typer.echo(f"Tổng khiếu nại: {res.total_claims_vnd:,.0f} VND | Đã giải ngân: {res.total_payout_vnd:,.0f} VND | Số dư: {res.remaining_balance_vnd:,.0f} VND")
    typer.echo("-" * 80)
    typer.echo(f"{'Mã khiếu nại':<10} | {'Bên khiếu nại':<32} | {'Hạng':<5} | {'Số tiền đòi (VND)':<18} | {'Được trả (VND)':<18} | {'Tỷ lệ'}")
    typer.echo("-" * 80)
    for s in res.settlements:
        typer.echo(f"{s.claim_id:<10} | {s.claimant_name:<32} | {s.rank:<5} | {s.claimed_amount_vnd:>18,.0f} | {s.paid_amount_vnd:>18,.0f} | {s.recovery_rate_pct:>6.1f}%")
    typer.echo("=" * 80 + f"\nMã Hash phân bổ thi hành án: {res.audit_hash}\n" + "=" * 80)
