"""CLI Commands for Bunkering MFM Dispute, Tidal Pilotage, Draft Survey & Reefer Claim (Phases 311-314)."""

from typing import List  # noqa: F401
import typer

from src.core.maritime_bunker_pilot_draft_reefer_engine import (
    BunkerDisputeInput,
    BunkerMfmDisputeEngine,
    DraftMarks,
    DraftSurveyEngine,
    DraftSurveyInput,
    HourlyTide,
    PilotageTidalWindowEngine,
    PilotageWindowInput,
    ReeferCargoType,
    ReeferClaimEngine,
    ReeferClaimInput,
    ReeferTempLog,
)

mfm_app = typer.Typer(help="Bunkering MFM Discrepancy & Dispute Resolver (Phase 311)")
pilot_app = typer.Typer(help="Seaport Pilotage Booking & Tidal Window Clearance (Phase 312)")
draft_app = typer.Typer(help="Draft Survey Cargo Displacement & Constant Calculator (Phase 313)")
reefer_claim_app = typer.Typer(help="Reefer Container Temperature Excursion & Claim Analyzer (Phase 314)")


@mfm_app.command("dispute-check")
def check_bunker_dispute(
    bdn: str = typer.Option("BDN-2026-HCM-88", "--bdn", help="Số chứng từ giao nhận dầu (BDN No)"),
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", "-v", help="Tên tàu nhận dầu"),
    barge: str = typer.Option("SAIGON BARGE 01", "--barge", help="Tên sà lan cấp dầu"),
    fuel: str = typer.Option("VLSFO 0.5%", "--fuel", help="Loại nhiên liệu cấp"),
    mfm_mt: float = typer.Option(500.0, "--mfm", help="Khối lượng đo bằng MFM trên sà lan (MT)"),
    ship_mt: float = typer.Option(491.0, "--ship", help="Khối lượng đo bằng Sounding trên tàu (MT)"),
    bdn_density: float = typer.Option(985.0, "--bdn-rho", help="Tỷ trọng ghi trên BDN tại 15°C (kg/m³)"),
    ship_density: float = typer.Option(980.5, "--ship-rho", help="Tỷ trọng mẫu thử thực tế trên tàu (kg/m³)"),
):
    """Kiểm tra độ lệch số liệu cấp dầu SS 600/648 & phát hiện bọt khí Cappuccino."""
    inp = BunkerDisputeInput(
        bunker_delivery_note_no=bdn, vessel_name=vessel, barge_name=barge, fuel_grade=fuel,
        mfm_delivered_mt=mfm_mt, vessel_received_mt=ship_mt,
        bdn_density_kg_m3=bdn_density, ship_measured_density_kg_m3=ship_density,
    )
    res = BunkerMfmDisputeEngine.evaluate_discrepancy(inp)
    typer.echo("=" * 80)
    typer.echo("GIÁM SÁT CHÊNH LỆCH CẤP DẦU MFM & TRANH CHẤP (SS 600 / SS 648)")
    typer.echo("=" * 80)
    typer.echo(f"Chứng từ: {res.bdn_no} | Tàu nhận: {res.vessel_name} | Sà lan: {barge}")
    typer.echo(f"Số đo MFM sà lan: {res.mfm_delivered_mt:,.2f} MT | Số đo tàu nhận: {res.vessel_received_mt:,.2f} MT")
    typer.echo(f"Độ lệch khối lượng: {res.discrepancy_mt:+,.2f} MT (Tỷ lệ: {res.discrepancy_pct:.2f}%)")
    typer.echo("-" * 80)
    typer.echo(f"Cấp độ phân xử: {res.dispute_level} | Nghi vấn bọt khí Cappuccino: {'CÓ (NGUY HIỂM)' if res.cappuccino_suspected else 'KHÔNG'}")
    typer.echo(f"Yêu cầu Thư kháng nghị (NoP): {'BẮT BUỘC KÝ NOP' if res.notice_of_protest_required else 'KHÔNG'}")
    typer.echo(f"Kết luận: {res.remarks}\nMã tra cứu xác thực: {res.audit_hash}\n" + "=" * 80)


@pilot_app.command("clearance")
def evaluate_tidal_clearance(
    vessel: str = typer.Option("MV MEKONG PHOENIX", "--vessel", "-v", help="Tên tàu hành hải"),
    grt: float = typer.Option(35000.0, "--grt", help="Dung tích toàn phần GRT"),
    draft: float = typer.Option(10.5, "--draft", "-d", help="Mớn nước tĩnh của tàu (m)"),
    datum: float = typer.Option(8.5, "--datum", help="Độ sâu chuẩn tắc luồng hải đồ (m)"),
    distance: float = typer.Option(22.0, "--distance", help="Chiều dài đoạn luồng hoa tiêu (hải lý)"),
    speed: float = typer.Option(10.0, "--speed", help="Tốc độ chạy tàu dự kiến trong luồng (hải lý/h)"),
):
    """Tính mớn nước an toàn UKC theo đỉnh triều & dự toán cước hoa tiêu TT 39/2023."""
    hourly_tides = [HourlyTide(h, 3.2 if 9 <= h <= 15 else (2.8 if 21 <= h <= 23 else 1.1)) for h in range(24)]
    inp = PilotageWindowInput(
        vessel_name=vessel, grt=grt, static_draft_m=draft, channel_depth_datum_m=datum,
        speed_knots=speed, transit_duration_hours=2, channel_distance_nm=distance, hourly_tides=hourly_tides,
    )
    res = PilotageTidalWindowEngine.evaluate_clearance_and_booking(inp)
    typer.echo("=" * 80)
    typer.echo("KIỂM TRA CỬA SỔ TRIỀU & ĐẶT HOA TIÊU HÀNG HẢI (TT 39/2023/TT-BGTVT)")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {res.vessel_name} (GRT {grt:,.0f}) | Mớn nước: {res.static_draft_m:.2f}m")
    typer.echo(f"Yêu cầu luồng: Mớn {res.static_draft_m}m + Squat {res.squat_allowance_m:.2f}m + UKC {res.required_ukc_m:.2f}m = {res.min_water_depth_needed_m:.2f}m")
    typer.echo("-" * 80)
    typer.echo(f"Cấp phép qua luồng: {'ĐỦ ĐIỀU KIỆN (CLEARED)' if res.is_clearance_granted else 'TỪ CHỐI (REJECTED)'}")
    if res.eligible_transit_hours:
        typer.echo(f"Khung giờ xuất phát an toàn: {', '.join(f'{h:02d}:00' for h in res.eligible_transit_hours)}")
    typer.echo(f"Dự toán cước hoa tiêu dẫn luồng: {res.estimated_pilot_dues_vnd:,.0f} VND\nGhi chú Cảng vụ: {res.remarks}\n" + "=" * 80)


@draft_app.command("calc")
def calculate_draft_survey(
    vessel: str = typer.Option("MV BULK PHOENIX", "--vessel", "-v", help="Tên tàu giám định"),
    survey_id: str = typer.Option("DS-2026-SG-01", "--id", help="Mã biên bản giám định"),
    fp: float = typer.Option(8.10, "--fp", help="Mớn mũi mạn trái Fwd Port (m)"),
    fs: float = typer.Option(8.14, "--fs", help="Mớn mũi mạn phải Fwd Stbd (m)"),
    mp: float = typer.Option(8.50, "--mp", help="Mớn giữa mạn trái Mid Port (m)"),
    ms: float = typer.Option(8.52, "--ms", help="Mớn giữa mạn phải Mid Stbd (m)"),
    ap: float = typer.Option(8.90, "--ap", help="Mớn lái mạn trái Aft Port (m)"),
    as_: float = typer.Option(8.94, "--as", help="Mớn lái mạn phải Aft Stbd (m)"),
    disp_table: float = typer.Option(30000.0, "--disp", help="Lượng dãn nước tra bảng thủy tĩnh (MT)"),
    tpc: float = typer.Option(45.0, "--tpc", help="Tấn trên 1 cm mớn nước (TPC)"),
    lcf: float = typer.Option(2.5, "--lcf", help="Khoảng cách LCF (m)"),
    lbp: float = typer.Option(180.0, "--lbp", help="Chiều dài LBP (m)"),
    density: float = typer.Option(1.020, "--density", help="Tỷ trọng nước thực tế (t/m³)"),
    deductibles: float = typer.Option(4500.0, "--deduct", help="Tổng trọng lượng trừ bì ballast/fuel (MT)"),
):
    """Tính lượng dãn nước và khối lượng hàng rời theo UN ECE Draft Survey Code."""
    marks = DraftMarks(fwd_port=fp, fwd_stbd=fs, mid_port=mp, mid_stbd=ms, aft_port=ap, aft_stbd=as_)
    inp = DraftSurveyInput(
        survey_id=survey_id, vessel_name=vessel, draft_marks=marks, table_displacement_mt=disp_table,
        tpc=tpc, lcf_m=lcf, lbp_m=lbp, measured_water_density=density, deductible_weights_mt=deductibles,
    )
    res = DraftSurveyEngine.calculate_draft_survey(inp)
    typer.echo("=" * 80)
    typer.echo("GIÁM ĐỊNH MỚN NƯỚC HÀNG RỜI (UN ECE CODE DRAFT SURVEY)")
    typer.echo("=" * 80)
    typer.echo(f"Biên bản: {res.survey_id} | Tàu: {res.vessel_name}")
    typer.echo(f"Mớn nước trung bình hiệu chỉnh (D_QM): {res.quarter_mean_draft_m:.3f} m | Trim thực tế: {res.apparent_trim_m:+.3f} m")
    typer.echo("-" * 80)
    typer.echo(f"Hiệu chỉnh Trim 1st: {res.first_trim_correction_mt:+.2f} MT | Giãn nước hiệu chỉnh ({density:.3f} t/m³): {res.density_corrected_disp_mt:,.2f} MT")
    typer.echo(f"KHỐI LƯỢNG HÀNG TỊNH (NET CARGO LOADED): {res.net_displacement_mt:,.2f} MT\nMã Hash chứng thư: {res.survey_hash}\n" + "=" * 80)


@reefer_claim_app.command("claim-analyze")
def analyze_reefer_claim(
    container: str = typer.Option("TEMU8899001", "--cont", "-c", help="Số container lạnh"),
    cargo: str = typer.Option("FROZEN_SEAFOOD", "--cargo", help="Loại hàng (FROZEN_SEAFOOD, FROZEN_MEAT, FRESH_FRUIT)"),
    set_point: float = typer.Option(-20.0, "--setpoint", "-s", help="Nhiệt độ cài đặt (°C)"),
    invoice_val: float = typer.Option(75000.0, "--value", help="Trị giá hóa đơn lô hàng (USD)"),
):
    """Phân tích vi phạm dải nhiệt độ container lạnh & phân xử trách nhiệm tổn thất."""
    try:
        c_type = ReeferCargoType(cargo.upper())
    except ValueError:
        c_type = ReeferCargoType.FROZEN_SEAFOOD

    logs = [
        ReeferTempLog(0, -20.0, "GATE_IN"),
        *[ReeferTempLog(h, -13.0, "YARD_STACK") for h in range(1, 5)],
        ReeferTempLog(5, -19.0, "VESSEL_VOYAGE"),
    ]
    inp = ReeferClaimInput(
        container_no=container, cargo_type=c_type, set_point_c=set_point,
        tolerance_c=2.0, temp_logs=logs, cargo_invoice_value_usd=invoice_val,
    )
    res = ReeferClaimEngine.analyze_claim(inp)
    typer.echo("=" * 80)
    typer.echo("GIÁM ĐỊNH TỔN THẤT CONTAINER LẠNH & PHÂN XỬ TRÁCH NHIỆM (REEFER CLAIM)")
    typer.echo("=" * 80)
    typer.echo(f"Container: {res.container_no} | Loại hàng: {res.cargo_type} | Nhiệt độ chuẩn: {res.set_point_c}°C | Cao nhất: {res.max_recorded_temp_c}°C")
    typer.echo(f"Thời gian vi phạm quá nhiệt: {res.excursion_hours} giờ | Tích lũy tổn hại: {res.accumulated_degree_hours:.1f} Degree-Hours")
    typer.echo("-" * 80)
    typer.echo(f"Hiệu lực khiếu nại: {'HỢP LỆ (VALID CLAIM)' if res.is_claim_valid else 'TỪ CHỐI (INVALID)'} | Bên chịu TN: {res.liable_party}")
    typer.echo(f"Mức bồi thường đề xuất: ${res.recommended_compensation_usd:,.2f} USD\nChi tiết phân xử: {res.remarks}\nMã tra cứu biên bản: {res.claim_hash}\n" + "=" * 80)
