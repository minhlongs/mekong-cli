"""
CLI Commands for MARPOL Fuel Switchover, Maritime Liens Waterfall, Berth Planning & Customs VASSCM
Phases 275-278 Maritime De-carbonization, Port Operations & Customs Automation Suite.
"""

from typing import List, Optional
import typer

from src.core.maritime_fuel_liens_berth_customs_engine import (
    FuelSwitchoverEngine,
    FuelSwitchoverInput,
    MaritimeLienWaterfallEngine,
    MaritimeClaimItem,
    ClaimType,
    LienTier,
    BerthPlanningUkcEngine,
    BerthAllocationInput,
    CustomsRiskVasscmEngine,
    CustomsRiskInput,
    EnterpriseComplianceLevel,
    VasscmGateCheckInput,
)

# Typer Command Groups
fuelswitch_app = typer.Typer(help="MARPOL Annex VI Fuel Oil Changeover & Sulfur Compliance Calculator (Phase 275)")
lienswaterfall_app = typer.Typer(help="Maritime Liens Priority Waterfall & Judicial Auction Proceeds Distributor (Phase 276)")
berthplan_app = typer.Typer(help="Seaport Berth Allocation, Dynamic UKC & PIANC BOR Engine (Phase 277)")
vasscm_app = typer.Typer(help="Automated Customs Risk Channeling & Seaport VASSCM Clearance Engine (Phase 278)")


# ------------------------------------------------------------------------------
# Phase 275: MARPOL Fuel Switchover Command
# ------------------------------------------------------------------------------

@fuelswitch_app.command("calculate")
def calculate_fuel_switchover(
    vessel: str = typer.Option("MV MEKONG CHALLENGER", "--vessel", "-v", help="Vessel name"),
    imo: str = typer.Option("9912345", "--imo", help="IMO number"),
    vol: float = typer.Option(4.2, "--vol", help="Fuel piping system volume in m3"),
    rate: float = typer.Option(1.4, "--rate", help="Fuel consumption rate in m3/h"),
    c0: float = typer.Option(0.50, "--c0", help="Initial fuel sulfur content (% m/m)"),
    c_low: float = typer.Option(0.08, "--c-low", help="Bunker changeover fuel sulfur content (% m/m)"),
    target: float = typer.Option(0.10, "--target", help="Statutory target sulfur limit (% m/m)"),
    t0: float = typer.Option(125.0, "--t0", help="Initial fuel temperature in deg C"),
    t_target: float = typer.Option(35.0, "--t-target", help="Target fuel temperature in deg C"),
    speed: float = typer.Option(14.5, "--speed", help="Vessel transit speed in knots"),
    dist: float = typer.Option(48.0, "--dist", help="Distance to ECA/Port boundary in nautical miles"),
    visc: float = typer.Option(2.45, "--visc", help="Kinematic viscosity of MGO at inlet in cSt"),
):
    """
    Calculate fuel changeover mixing duration, thermal ramping & ECA approach distance.
    """
    data = FuelSwitchoverInput(
        vessel_name=vessel,
        imo_number=imo,
        system_volume_m3=vol,
        fuel_consumption_m3_h=rate,
        initial_sulfur_pct=c0,
        low_sulfur_bunker_pct=c_low,
        target_sulfur_pct=target,
        initial_temp_c=t0,
        target_temp_c=t_target,
        vessel_speed_knots=speed,
        distance_to_boundary_nm=dist,
        mgo_kinematic_viscosity_cst=visc,
    )
    result = FuelSwitchoverEngine.calculate_switchover(data)

    typer.echo("================================================================================")
    typer.echo("TÍNH TOÁN CHUYỂN ĐỔI NHIÊN LIỆU MARPOL ANNEX VI (MEPC.1/CIRC.864)")
    typer.echo("================================================================================")
    typer.echo(f"Tên tàu / IMO:                 {vessel} / {imo}")
    typer.echo(f"Nhiên liệu ban đầu:            {c0:.2f}% S (Nhiệt độ: {t0:.1f}°C)")
    typer.echo(f"Nhiên liệu thay thế:           {c_low:.2f}% S (Nhiệt độ: {t_target:.1f}°C, Độ nhớt: {visc:.2f} cSt)")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"Thời gian hòa trộn pha loãng:  {result.dilution_duration_hours:.2f} giờ")
    typer.echo(f"Thời gian ổn định nhiệt độ:    {result.thermal_ramp_duration_hours:.2f} giờ (Tốc độ: {result.cooling_rate_c_per_min:.2f} °C/phút)")
    typer.echo(f"Thời gian chuyển đổi tới hạn:  {result.critical_duration_hours:.2f} giờ")
    typer.echo(f"Khoảng cách cần chuyển đổi:    {result.required_switchover_distance_nm:.1f} hải lý")
    typer.echo(f"Khoảng cách dự phòng:          {result.remaining_distance_buffer_nm:+.1f} hải lý")
    typer.echo(f"Trạng thái an toàn:            {'ĐẠT AN TOÀN' if result.is_safe_to_execute else 'CẢNH BÁO KHÔNG AN TOÀN'}")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"Kết luận: {result.summary_vi}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 276: Maritime Lien Priority Waterfall Command
# ------------------------------------------------------------------------------

@lienswaterfall_app.command("distribute")
def distribute_liens_proceeds(
    vessel: str = typer.Option("MV MEKONG FREIGHTER", "--vessel", "-v", help="Vessel name"),
    gross: float = typer.Option(50000000000.0, "--gross", help="Gross auction proceeds in VND"),
    costs: float = typer.Option(2000000000.0, "--costs", help="Auction & enforcement costs in VND"),
    date: str = typer.Option("2026-10-08T00:00:00", "--date", help="Auction date in ISO format"),
):
    """
    Simulate statutory maritime lien waterfall & auction proceeds distribution (VMC 2015 Arts. 37-43).
    """
    # Sample realistic claim docket for demonstration
    sample_claims = [
        MaritimeClaimItem(
            claim_id="CLM-01",
            claimant_name="Crew Union (Thuyền viên)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_1_CREW_WAGES,
            claim_amount_vnd=8000000000.0,
            claim_date_iso="2026-05-01T00:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-02",
            claimant_name="Personal Injury (Người lao động)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_2_PERSONAL_INJURY,
            claim_amount_vnd=3000000000.0,
            claim_date_iso="2026-04-15T00:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-03",
            claimant_name="Salvage Co 2 (Cứu hộ đợt 2 - Mới nhất)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_3_SALVAGE_GENERAL_AVERAGE,
            claim_amount_vnd=6000000000.0,
            claim_date_iso="2026-08-15T00:00:00",
            salvage_timestamp_iso="2026-08-15T10:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-04",
            claimant_name="Salvage Co 1 (Cứu hộ đợt 1 - Cũ hơn)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_3_SALVAGE_GENERAL_AVERAGE,
            claim_amount_vnd=4000000000.0,
            claim_date_iso="2026-05-02T00:00:00",
            salvage_timestamp_iso="2026-05-02T08:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-05",
            claimant_name="Port Authority (Cảng vụ Hải Phòng)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_4_PORT_SAFETY_DUES,
            claim_amount_vnd=5000000000.0,
            claim_date_iso="2026-03-20T00:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-06",
            claimant_name="Collision Damage (Tàu bị va chạm)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_5_TORT_COLLISION,
            claim_amount_vnd=8000000000.0,
            claim_date_iso="2026-02-10T00:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-07",
            claimant_name="Maritime Commercial Bank (Thế chấp)",
            claim_type=ClaimType.SHIP_MORTGAGE,
            lien_tier=None,
            claim_amount_vnd=14000000000.0,
            claim_date_iso="2025-01-10T00:00:00",
            mortgage_registration_iso="2025-01-10T00:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-08",
            claimant_name="Old Bunkering Supplier (Quá hạn 1 năm)",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_4_PORT_SAFETY_DUES,
            claim_amount_vnd=3500000000.0,
            claim_date_iso="2024-05-01T00:00:00",
            arrest_prior_to_expiry=False,
        ),
    ]

    report = MaritimeLienWaterfallEngine.distribute_auction_proceeds(
        vessel_name=vessel,
        gross_proceeds_vnd=gross,
        auction_costs_vnd=costs,
        auction_date_iso=date,
        claims=sample_claims,
    )

    typer.echo("================================================================================")
    typer.echo("PHÂN BỔ TIỀN BÁN ĐẤU GIÁ TÀU THEO QUYỀN CẦM GIỮ HÀNG HẢI (BỘ LUẬT HHVN 2015)")
    typer.echo("================================================================================")
    typer.echo(f"Tên tàu bán đấu giá:           {report.vessel_name}")
    typer.echo(f"Tổng số tiền bán đấu giá:      {report.gross_proceeds_vnd:,.0f} VND")
    typer.echo(f"Chi phí cưỡng chế & bán ĐG:    {report.auction_enforcement_costs_vnd:,.0f} VND (Khấu trừ số 1)")
    typer.echo(f"Số tiền thực tế phân bổ:       {report.net_distributable_funds_vnd:,.0f} VND")
    typer.echo("--------------------------------------------------------------------------------")
    for cp in report.claims_payout:
        tier_label = f"[Cấp {cp.tier}]" if cp.tier else f"[{cp.claim_type}]"
        typer.echo(f"{tier_label:<16} {cp.claimant_name:<30}: Đã trả {cp.paid_amount_vnd:,.0f} VND / {cp.claimed_amount_vnd:,.0f} VND ({cp.recovery_rate_pct:.1f}%) - {cp.status_note}")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"Tổng chi Cầm giữ (Điều 37):    {report.total_statutory_liens_paid_vnd:,.0f} VND")
    typer.echo(f"Tổng chi Thế chấp tàu biển:    {report.total_mortgages_paid_vnd:,.0f} VND")
    typer.echo(f"Tổng chi Nợ thường:            {report.total_unsecured_paid_vnd:,.0f} VND")
    typer.echo(f"Số dư thặng dư còn lại:        {report.unallocated_surplus_vnd:,.0f} VND")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 277: Seaport Berth Allocation Planning & Tidal UKC Command
# ------------------------------------------------------------------------------

@berthplan_app.command("evaluate")
def evaluate_berth_plan(
    berth_id: str = typer.Option("CMIT-03", "--berth", help="Berth identifier"),
    length: float = typer.Option(400.0, "--length", help="Berth usable length in meters"),
    depth: float = typer.Option(14.0, "--depth", help="Charted water depth at berth/channel in meters"),
    vessel: str = typer.Option("MV MEKONG TITAN", "--vessel", "-v", help="Vessel name"),
    loa: float = typer.Option(366.0, "--loa", help="Length overall (LOA) in meters"),
    beam: float = typer.Option(51.2, "--beam", help="Vessel beam in meters"),
    draft: float = typer.Option(15.2, "--draft", help="Static vessel draft in meters"),
    cb: float = typer.Option(0.70, "--cb", help="Block coefficient Cb"),
    speed: float = typer.Option(7.0, "--speed", help="Channel transit speed in knots"),
    chan_width: float = typer.Option(310.0, "--width", help="Channel width in meters"),
    confined: bool = typer.Option(True, "--confined", help="Confined channel (canal/dredged trench)"),
    density: float = typer.Option(1.020, "--density", help="Water density in kg/l"),
    wave: float = typer.Option(0.30, "--wave", help="Wave motion response allowance in meters"),
    hw: float = typer.Option(3.40, "--hw", help="High water tide level in meters"),
    lw: float = typer.Option(0.80, "--lw", help="Low water tide level in meters"),
    tide_cycle: float = typer.Option(12.4, "--cycle", help="Tidal cycle duration in hours"),
    transit_hr: float = typer.Option(15.0, "--transit-hr", help="Transit hour (relative)"),
    hw_hr: float = typer.Option(15.5, "--hw-hr", help="High water peak hour"),
    serv_hours: float = typer.Option(147.6, "--serv-hrs", help="Total berth service hours in period"),
    period_hrs: float = typer.Option(240.0, "--period-hrs", help="Evaluation period in hours"),
    berths_cnt: int = typer.Option(1, "--berths", help="Total active berths in terminal"),
):
    """
    Evaluate berth spatial allocation, harmonic dynamic UKC and PIANC BOR.
    """
    inp = BerthAllocationInput(
        berth_id=berth_id,
        berth_length_m=length,
        charted_depth_m=depth,
        vessel_name=vessel,
        loa_m=loa,
        beam_m=beam,
        static_draft_m=draft,
        block_coefficient=cb,
        transit_speed_knots=speed,
        channel_width_m=chan_width,
        is_confined_channel=confined,
        water_density_kg_l=density,
        wave_response_m=wave,
        tide_high_water_m=hw,
        tide_low_water_m=lw,
        tide_cycle_hours=tide_cycle,
        hour_of_transit=transit_hr,
        high_water_hour=hw_hr,
        total_service_hours_period=serv_hours,
        period_hours=period_hrs,
        active_berths_count=berths_cnt,
    )
    res = BerthPlanningUkcEngine.evaluate_berth_plan(inp)

    typer.echo("================================================================================")
    typer.echo("KẾ HOẠCH ĐIỀU ĐỘ CẦU BẾN & TÍNH TOÁN D-UKC THEO THỦY TRIỀU (NGHỊ ĐỊNH 58/2017)")
    typer.echo("================================================================================")
    typer.echo(f"Cầu cảng chỉ định:             {berth_id} (Chiều dài khả dụng: {length:.1f} m)")
    typer.echo(f"Tàu cập cầu:                   {vessel} (LOA: {loa:.1f} m, Mớn nước: {draft:.2f} m)")
    typer.echo(f"Chiều dài slot an toàn:        {res.required_slot_length_m:.1f} m -> {'ĐẠT' if res.is_slot_length_adequate else 'THIẾU'}")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"Độ sâu luồng chuẩn hải đồ:     {depth:.2f} m")
    typer.echo(f"Độ cao triều tại giờ hành hải: +{res.tide_height_at_transit_m:.2f} m (Tổng độ sâu nước: {res.total_dynamic_water_depth_m:.2f} m)")
    typer.echo(f"Độ chìm do tốc độ (Squat):     -{res.dynamic_squat_m:.2f} m")
    typer.echo(f"Độ chìm do nước ngọt:          -{res.salinity_sinkage_m:.2f} m")
    typer.echo(f"Tổng mớn nước động:            {res.total_dynamic_draft_m:.2f} m")
    typer.echo(f"Dynamic UKC thực tế:           {res.calculated_ukc_m:.2f} m (Ngưỡng an toàn tối thiểu: {res.minimum_required_ukc_m:.2f} m)")
    typer.echo(f"Đánh giá tĩnh không dưới lườn: {'AN TOÀN' if res.is_ukc_safe else 'NGUY CƠ MẮC CẠN'}")
    typer.echo(f"Cửa sổ triều an toàn:          {res.safe_transit_window_hours:.2f} giờ")
    typer.echo(f"Hệ số sử dụng cầu bến (BOR):   {res.berth_occupancy_rate_pct:.1f}% ({'ÙN TẮC' if res.is_bor_congested else 'AN TOÀN'})")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"Kết luận: {res.summary_vi}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 278: Customs Risk Channeling & Seaport VASSCM Clearance Command
# ------------------------------------------------------------------------------

@vasscm_app.command("channel")
def channel_customs_risk(
    declaration: str = typer.Option("104567891234", "--decl", "-d", help="Customs declaration number"),
    tax_id: str = typer.Option("0109988776", "--mst", help="Enterprise tax registration ID"),
    level: int = typer.Option(1, "--level", help="Enterprise compliance level (1 to 5)"),
    hs: str = typer.Option("8542.31", "--hs", help="6-digit HS Code"),
    hs_risk: float = typer.Option(0.20, "--hs-risk", help="HS code risk tier (0.0 to 1.0)"),
    org_risk: float = typer.Option(0.15, "--org-risk", help="Origin route risk tier (0.0 to 1.0)"),
    alert: bool = typer.Option(False, "--alert", help="Targeted intelligence alert flag"),
    val: float = typer.Option(150000.0, "--val", help="Declared customs value in USD"),
):
    """
    Evaluate automated customs risk score & channeling (Luồng Xanh / Vàng / Đỏ).
    """
    e_lvl = EnterpriseComplianceLevel(level) if level in {1, 2, 3, 4, 5} else EnterpriseComplianceLevel.LEVEL_3_MEDIUM_COMPLIANCE
    inp = CustomsRiskInput(
        declaration_number=declaration,
        enterprise_tax_id=tax_id,
        enterprise_level=e_lvl,
        hs_code=hs,
        hs_risk_tier=hs_risk,
        origin_risk_tier=org_risk,
        has_intelligence_alert=alert,
        declared_value_usd=val,
    )
    res = CustomsRiskVasscmEngine.evaluate_risk_channel(inp)

    typer.echo("================================================================================")
    typer.echo("PHÂN LUỒNG RỦI RO HẢI QUAN TỰ ĐỘNG (QUYẾT ĐỊNH 1399/QĐ-TCHQ)")
    typer.echo("================================================================================")
    typer.echo(f"Số tờ khai hải quan:           {declaration}")
    typer.echo(f"Mã số thuế doanh nghiệp:       {tax_id} (Xếp hạng tuân thủ: Cấp {level})")
    typer.echo(f"Mã HS mặt hàng:                {hs} (Trị giá: ${val:,.2f} USD)")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"KẾT QUẢ PHÂN LUỒNG:            {res.channel_name_vi}")
    typer.echo(f"Điểm rủi ro (R-score):         {res.risk_score:.3f}")
    typer.echo(f"Miễn kiểm tra hồ sơ giấy:      {'ĐẠT' if res.exempt_document_check else 'KHÔNG (PHẢI NỘP HỒ SƠ)'}")
    typer.echo(f"Miễn kiểm tra thực tế hàng:    {'ĐẠT' if res.exempt_physical_inspection else 'KHÔNG (PHẢI SOI CHIẾU/MỞ HÀNG)'}")
    typer.echo(f"Thời gian thông quan cam kết:  {res.target_sla_hours:.2f} giờ")
    typer.echo(f"Mã băm thông quan:             {res.release_token}")
    typer.echo("================================================================================")


@vasscm_app.command("gate-out")
def verify_vasscm_gate(
    declaration: str = typer.Option("104567891234", "--decl", "-d", help="Customs declaration number"),
    status: str = typer.Option("RELEASED", "--status", help="Declaration clearance status (RELEASED, CUSTOMS_CLEARED)"),
    edo: str = typer.Option("EDO-MSK-202610-8899", "--edo", help="e-D/O tracking number"),
    edo_valid: bool = typer.Option(True, "--edo-valid", help="Is e-D/O verified and valid"),
    container: str = typer.Option("MSKU9876543", "--cntr", "-c", help="Container number"),
    manifest_seal: str = typer.Option("MSK-889977", "--m-seal", help="Manifest declared seal number"),
    gate_seal: str = typer.Option("MSK-889977", "--g-seal", help="Physical OCR scanned seal number"),
):
    """
    Perform seaport VASSCM 3-way match gate-out verification (Decision 2185/QĐ-TCHQ).
    """
    inp = VasscmGateCheckInput(
        declaration_number=declaration,
        declaration_status=status,
        edo_number=edo,
        edo_is_valid=edo_valid,
        container_number=container,
        manifest_seal_number=manifest_seal,
        gate_scanned_seal_number=gate_seal,
    )
    res = CustomsRiskVasscmEngine.verify_vasscm_gate_out(inp)

    typer.echo("================================================================================")
    typer.echo("ĐỐI SOÁT 3 BÊN TẠI CỔNG RA CẢNG BIỂN - VASSCM (QUYẾT ĐỊNH 2185/QĐ-TCHQ)")
    typer.echo("================================================================================")
    typer.echo(f"Số tờ khai:                    {declaration} (Trạng thái: {status})")
    typer.echo(f"Lệnh giao hàng điện tử:        {edo} ({'HỢP LỆ' if edo_valid else 'KHÔNG HỢP LỆ'})")
    typer.echo(f"Container / Số chì:            {container} / {gate_seal}")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"KẾT QUẢ ĐỐI SOÁT:              {'CHO PHÉP XUẤT CẢNG (PASS)' if res.is_gate_pass_approved else 'TẠM GIỮ TẠI CỔNG (HOLD)'}")
    if res.discrepancy_reasons:
        typer.echo("Lý do sai lệch:")
        for r in res.discrepancy_reasons:
            typer.echo(f" - {r}")
    typer.echo(f"Mã băm giao dịch VASSCM:       {res.vasscm_auth_hash}")
    typer.echo("================================================================================")
