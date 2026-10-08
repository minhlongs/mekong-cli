# -*- coding: utf-8 -*-
"""Typer CLI Subcommands for Phases 259-262.

Commands:
- bareboat: Bareboat Charter Registry & Flag Suspension Under VMC 2015 & Decree 171/2016
- collision: Collision Cross-Liabilities & Both-to-Blame Settlement Under VMC 2015 & Brussels 1910
- tokyomou: Tokyo MOU Port State Control (PSC) Ship Risk Profile & CIC Inspection Engine
- reeferport: Seaport Reefer Container Power Tariff & Temperature Monitoring Under Circular 39/2023
"""

from __future__ import annotations

import json
import typer

from src.core.maritime_flag_collision_psc_reefer_engine import (
    BareboatRegistryType,
    BareboatRegistrationApplication,
    BareboatRegistrationEngine,
    CollisionDamageProfile,
    CollisionLiabilityBothToBlameEngine,
    FlagPerformanceTier,
    ROPerformanceTier,
    CompanyPerformanceTier,
    PSCHistoryData,
    TokyoMOUPSCInspectionEngine,
    CargoThermalClass,
    PortReeferMonitoringEngine,
)

bareboat_app = typer.Typer(
    name="bareboat",
    help="Phase 259: Bareboat Charter Registry & Temporary Flag Suspension Under VMC 2015",
    no_args_is_help=True,
)

collision_app = typer.Typer(
    name="collision",
    help="Phase 260: Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015",
    no_args_is_help=True,
)

tokyomou_app = typer.Typer(
    name="tokyomou",
    help="Phase 261: Tokyo MOU PSC Ship Risk Profile (SRP) & CIC Inspection Calculator",
    no_args_is_help=True,
)

reeferport_app = typer.Typer(
    name="reeferport",
    help="Phase 262: Seaport Reefer Container Electricity Tariff & Temperature Monitoring",
    no_args_is_help=True,
)


# ==============================================================================
# PHASE 259: BAREBOAT CHARTER REGISTRY
# ==============================================================================

@bareboat_app.command(name="evaluate")
def cmd_bareboat_evaluate(
    vessel: str = typer.Option("MV_PACIFIC_CHARTERER", "--vessel", "-v", help="Tên tàu"),
    imo: str = typer.Option("9283741", "--imo", help="Số IMO của tàu"),
    reg_type: str = typer.Option("bareboat_in", "--reg-type", help="Loại đăng ký: bareboat_in hoặc bareboat_out"),
    start_date: str = typer.Option("2026-01-01", "--start-date", help="Ngày bắt đầu thuê tàu (YYYY-MM-DD)"),
    end_date: str = typer.Option("2028-12-31", "--end-date", help="Ngày kết thúc thuê tàu (YYYY-MM-DD)"),
    charterer: str = typer.Option("VINASHIP CORP", "--charterer", help="Doanh nghiệp thuê tàu trần"),
    owner_country: str = typer.Option("PANAMA", "--owner-country", help="Quốc gia chủ tàu gốc"),
    original_flag: str = typer.Option("PANAMA", "--original-flag", help="Cờ quốc tịch gốc"),
    has_flag_suspension: bool = typer.Option(True, "--has-flag-suspension", help="Có giấy tạm đình chỉ cờ gốc"),
    total_crew: int = typer.Option(20, "--total-crew", help="Tổng định biên thuyền viên"),
    vn_officers: int = typer.Option(8, "--vn-officers", help="Số sĩ quan mang quốc tịch Việt Nam"),
    vn_ratings: int = typer.Option(10, "--vn-ratings", help="Số thủy thủ/thợ máy mang quốc tịch Việt Nam"),
    gt: float = typer.Option(28000.0, "--gt", help="Dung tích toàn phần (Gross Tonnage)"),
    built_year: int = typer.Option(2015, "--built-year", help="Năm đóng tàu"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Thẩm định điều kiện đăng ký tàu thuê trần mang cờ Việt Nam theo Nghị định 171/2016."""
    app = BareboatRegistrationApplication(
        vessel_name=vessel,
        imo_number=imo,
        registry_type=BareboatRegistryType(reg_type),
        charter_start_date=start_date,
        charter_end_date=end_date,
        charterer_entity_name=charterer,
        disponent_owner_country=owner_country,
        original_flag_state=original_flag,
        has_temporary_flag_suspension_cert=has_flag_suspension,
        total_crew_members=total_crew,
        vietnamese_officers_count=vn_officers,
        vietnamese_ratings_count=vn_ratings,
        gross_tonnage=gt,
        built_year=built_year,
    )

    report = BareboatRegistrationEngine.evaluate_registration(app)

    if json_output:
        typer.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"THẨM ĐỊNH ĐĂNG KÝ TÀU THUÊ TRẦN (BAREBOAT) — {report.vessel_name}")
    typer.echo("=" * 70)
    typer.echo(f"Số IMO:                     {report.imo_number}")
    typer.echo(f"Hình thức đăng ký:          {report.registry_type}")
    typer.echo(f"Đủ điều kiện đăng ký:       {'ĐẠT' if report.eligible_for_registry else 'KHÔNG ĐẠT'}")
    typer.echo(f"Thời hạn đăng ký tối đa:    {report.max_registration_duration_days} ngày")
    typer.echo(f"Tỷ lệ thuyền viên VN:       {report.vietnamese_crew_ratio_pct:.1f}%")
    typer.echo(f"Tỷ lệ sĩ quan VN:           {report.vietnamese_officers_ratio_pct:.1f}%")
    typer.echo(f"Lệ phí đăng ký luật định:   {report.registration_fee_vnd:,.0f} VND")
    typer.echo(f"Trạng thái tuân thủ:        {report.statutory_compliance_status}")
    typer.echo(f"Ghi chú:                    {report.remarks}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 260: COLLISION CROSS-LIABILITIES & BOTH-TO-BLAME
# ==============================================================================

@collision_app.command(name="settle")
def cmd_collision_settle(
    vessel_a: str = typer.Option("MV_VIET_SUN", "--vessel-a", help="Tên Tàu A"),
    vessel_b: str = typer.Option("MV_OCEAN_PRIDE", "--vessel-b", help="Tên Tàu B"),
    fault_a: float = typer.Option(60.0, "--fault-a", help="Tỷ lệ lỗi của Tàu A (%)"),
    hull_a: float = typer.Option(1200000.0, "--hull-a", help="Chi phí sửa chữa hư hại thân tàu A (USD)"),
    demurrage_a: float = typer.Option(300000.0, "--demurrage-a", help="Tổn thất kinh doanh/mất tiền thuê tàu A (USD)"),
    cargo_a: float = typer.Option(800000.0, "--cargo-a", help="Tổn thất hàng hóa trên tàu A (USD)"),
    hull_b: float = typer.Option(600000.0, "--hull-b", help="Chi phí sửa chữa hư hại thân tàu B (USD)"),
    demurrage_b: float = typer.Option(150000.0, "--demurrage-b", help="Tổn thất kinh doanh tàu B (USD)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán quyết toán thanh toán chéo đâm va và điều khoản Both-to-Blame."""
    damage_a = CollisionDamageProfile(
        hull_repair_damage_usd=hull_a,
        loss_of_hire_demurrage_usd=demurrage_a,
        cargo_loss_onboard_usd=cargo_a,
        crew_personal_injury_claims_usd=0.0,
    )
    damage_b = CollisionDamageProfile(
        hull_repair_damage_usd=hull_b,
        loss_of_hire_demurrage_usd=demurrage_b,
        cargo_loss_onboard_usd=0.0,
        crew_personal_injury_claims_usd=0.0,
    )

    res = CollisionLiabilityBothToBlameEngine.calculate_collision_settlement(
        vessel_a_name=vessel_a,
        vessel_b_name=vessel_b,
        fault_percentage_a=fault_a,
        damage_a=damage_a,
        damage_b=damage_b,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo("QUYẾT TOÁN TAI NẠN ĐÂM VA & ĐIỀU KHOẢN BOTH-TO-BLAME")
    typer.echo("=" * 70)
    typer.echo(f"Tỷ lệ lỗi đâm va:             {res.vessel_a_name} ({res.vessel_a_fault_ratio*100:.1f}%) vs {res.vessel_b_name} ({res.vessel_b_fault_ratio*100:.1f}%)")
    typer.echo(f"Tổng tổn thất tàu A:          {res.vessel_a_total_direct_loss_usd:,.2f} USD")
    typer.echo(f"Tổng tổn thất tàu B:          {res.vessel_b_total_direct_loss_usd:,.2f} USD")
    typer.echo(f"Trách nhiệm tàu A bồi thường B:{res.vessel_a_liability_to_vessel_b_usd:,.2f} USD")
    typer.echo(f"Trách nhiệm tàu B bồi thường A:{res.vessel_b_liability_to_vessel_a_usd:,.2f} USD")
    typer.echo(f"Số dư thanh toán ròng:        {res.single_liability_net_balance_usd:,.2f} USD ({res.paying_vessel} phải trả)")
    typer.echo(f"Bồi thường hàng Tàu A từ Tàu B:{res.cargo_claims_against_other_vessel_usd:,.2f} USD")
    typer.echo(f"Thu hồi theo Both-to-Blame:   {res.both_to_blame_indemnity_recovery_usd:,.2f} USD")
    typer.echo(f"Phân tích:                    {res.settlement_analysis}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 261: TOKYO MOU PSC INSPECTION
# ==============================================================================

@tokyomou_app.command(name="profile")
def cmd_tokyomou_profile(
    vessel: str = typer.Option("MV_STAR_CARRIER", "--vessel", help="Tên tàu"),
    imo: str = typer.Option("9418291", "--imo", help="Số IMO của tàu"),
    ship_type: str = typer.Option("bulk_carrier", "--type", help="Loại tàu (bulk_carrier, oil_tanker, container, general_cargo)"),
    age: int = typer.Option(14, "--age", help="Tuổi tàu (năm)"),
    flag: str = typer.Option("white_list", "--flag", help="Hiệu suất cờ: white_list, grey_list, black_list"),
    ro: str = typer.Option("high", "--ro", help="Hiệu suất Đăng kiểm RO: high, medium, low, very_low"),
    company: str = typer.Option("medium", "--company", help="Hiệu suất công ty quản lý: high, medium, low, very_low"),
    inspections: int = typer.Option(6, "--inspections", help="Số lần kiểm tra trong 36 tháng qua"),
    deficiencies: int = typer.Option(18, "--deficiencies", help="Số khiếm khuyết trong 36 tháng qua"),
    detentions: int = typer.Option(0, "--detentions", help="Số lần bị lưu giữ (detentions) trong 36 tháng qua"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán hồ sơ rủi ro tàu biển (SRP) và cửa sổ kiểm tra theo Tokyo MOU."""
    psc_hist = PSCHistoryData(
        inspections_last_36_months=inspections,
        deficiencies_last_36_months=deficiencies,
        detentions_last_36_months=detentions,
    )

    res = TokyoMOUPSCInspectionEngine.calculate_ship_risk_profile(
        vessel_name=vessel,
        imo_number=imo,
        ship_type=ship_type,
        vessel_age=age,
        flag_status=FlagPerformanceTier(flag),
        ro_performance=ROPerformanceTier(ro),
        company_performance=CompanyPerformanceTier(company),
        psc_history=psc_hist,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"HỒ SƠ RỦI RO TÀU BIỂN TOKYO MOU (SRP) — {res.vessel_name}")
    typer.echo("=" * 70)
    typer.echo(f"Số IMO:                       {res.imo_number}")
    typer.echo(f"Phân loại rủi ro (Grade):     {res.risk_profile_grade.value}")
    typer.echo(f"Điểm số rủi ro tích lũy:      {res.total_risk_weighting_points} điểm")
    typer.echo(f"Cửa sổ kiểm tra ưu tiên:      {res.inspection_priority_window_months}")
    typer.echo(f"Mức độ rủi ro chiến dịch CIC: {res.cic_target_risk_level}")
    typer.echo(f"Kiểm tra mở rộng (Expanded):  {'CÓ (BẮT BUỘC)' if res.is_subject_to_expanded_inspection else 'KHÔNG'}")
    typer.echo("Trọng tâm kiểm tra đề xuất:")
    for fa in res.recommended_psco_focus_areas:
        typer.echo(f"  - {fa}")
    typer.echo(f"Tổng kết:                     {res.compliance_summary}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 262: REEFER CONTAINER MONITORING & POWER TARIFF
# ==============================================================================

@reeferport_app.command(name="monitor")
def cmd_reeferport_monitor(
    container_id: str = typer.Option("SEGU-8492014", "--container-id", help="Số hiệu container"),
    thermal: str = typer.Option("frozen", "--thermal", help="Loại nhiệt độ: chilled, frozen, deep_frozen, ultra_low"),
    setpoint: float = typer.Option(-20.0, "--setpoint", help="Nhiệt độ cài đặt (°C)"),
    actual_temp: float = typer.Option(-19.2, "--actual-temp", help="Nhiệt độ thực tế bình quân (°C)"),
    hours: float = typer.Option(48.0, "--hours", help="Số giờ cắm điện tại bãi cảng"),
    ambient: float = typer.Option(34.5, "--ambient", help="Nhiệt độ môi trường bình quân (°C)"),
    tariff: float = typer.Option(3850.0, "--tariff", help="Đơn giá điện cảng biển (VND/kWh)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán chi phí điện năng và kiểm soát nhiệt độ container lạnh tại cảng."""
    res = PortReeferMonitoringEngine.calculate_reefer_service(
        container_id=container_id,
        thermal_class=CargoThermalClass(thermal),
        setpoint_celsius=setpoint,
        actual_avg_temp_celsius=actual_temp,
        plugged_hours=hours,
        ambient_temp_celsius=ambient,
        electricity_tariff_vnd_kwh=tariff,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"GIÁM SÁT CONTAINER LẠNH & PHÍ ĐIỆN NĂNG — {res.container_id}")
    typer.echo("=" * 70)
    typer.echo(f"Chủng loại bảo quản:          {res.thermal_class.upper()}")
    typer.echo(f"Thời gian cắm điện bãi:       {res.dwell_plugged_hours:.1f} giờ")
    typer.echo(f"Điện năng tiêu thụ thực tế:   {res.total_power_consumed_kwh:,.2f} kWh")
    typer.echo(f"Chi phí tiền điện:            {res.power_electricity_cost_vnd:,.0f} VND")
    typer.echo(f"Phí cắm/rút phích cắm:        {res.plug_unplug_service_fee_vnd:,.0f} VND")
    typer.echo(f"Phí giám sát đo ghi nhiệt độ: {res.monitoring_and_log_fee_vnd:,.0f} VND")
    typer.echo(f"TỔNG CHI PHÍ CONTAINER LẠNH:  {res.total_reefer_charges_vnd:,.0f} VND")
    typer.echo(f"Đánh giá rủi ro nhiệt độ:     {res.temperature_excursion_risk}")
    typer.echo(f"Chỉ số bảo toàn chất lượng:   {res.cargo_quality_retention_index_pct:.1f}%")
    typer.echo(f"Đánh giá:                     {res.remarks}")
    typer.echo("=" * 70)
