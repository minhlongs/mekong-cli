"""
CLI Commands for Maritime Charterparty Performance, e-D/O, Tonnage Dues & IMDG Handling
Phases 267-270 Maritime Compliance & Operations Suite.
"""

from typing import Optional
import typer

from src.core.maritime_charterparty_edo_tonnage_imdg_engine import (
    CharterpartyPerformanceEngine,
    WarrantedTerms,
    PassageLegData,
    ElectronicDeliveryOrderEngine,
    ContainerDepositParams,
    ContainerCategory,
    SeaportTonnageTariffEngine,
    VesselPortCallData,
    VoyageType,
    PortMaritimeZone,
    IMDGSafetyHandlingEngine,
    IMDGClass,
)

# Typer Command Groups
charterparty_app = typer.Typer(help="Time charterparty speed & fuel warranty performance claim assessment")
edo_app = typer.Typer(help="Electronic Delivery Order (e-D/O) & Container Deposit settlement")
tonnage_app = typer.Typer(help="Seaport tonnage dues, maritime safety tariffs & anchorage dues")
imdg_app = typer.Typer(help="IMDG dangerous goods seaport handling, segregation matrix & safety rules")


@charterparty_app.command("evaluate")
def evaluate_charterparty(
    warranted_speed: float = typer.Option(13.5, "--speed", "-s", help="Warranted speed in knots (e.g. 13.5)"),
    warranted_fuel: float = typer.Option(28.0, "--fuel", "-f", help="Warranted fuel consumption t/day (e.g. 28.0)"),
    distance: float = typer.Option(3200.0, "--distance", "-d", help="Total passage distance in nautical miles"),
    steaming_hours: float = typer.Option(250.0, "--hours", "-h", help="Total steaming hours on passage"),
    gw_hours: float = typer.Option(90.0, "--gw-hours", help="Good weather steaming hours"),
    gw_distance: float = typer.Option(1125.0, "--gw-dist", help="Good weather distance in nautical miles"),
    actual_fuel: float = typer.Option(315.0, "--act-fuel", help="Actual fuel consumed in metric tons"),
    hire_rate: float = typer.Option(18000.0, "--hire", help="Daily hire rate in USD"),
    fuel_price: float = typer.Option(620.0, "--fuel-price", help="VLSFO bunker price in USD/tonne"),
):
    """
    Evaluate vessel performance under BIMCO NYPE 93/2015 and The Didymi / The Gas Enterprise doctrines.
    """
    warranties = WarrantedTerms(
        warranted_speed_knots=warranted_speed,
        warranted_fuel_tonnes_day=warranted_fuel,
        daily_hire_rate_usd=hire_rate,
        vlsfo_price_per_tonne_usd=fuel_price,
    )
    passage = PassageLegData(
        leg_name="Main Voyage",
        total_distance_nm=distance,
        steaming_hours_total=steaming_hours,
        good_weather_hours=gw_hours,
        good_weather_distance_nm=gw_distance,
        actual_fuel_consumed_tonnes=actual_fuel,
    )

    result = CharterpartyPerformanceEngine.evaluate_passage(warranties, passage)

    typer.echo("=== BÁO CÁO ĐÁNH GIÁ THỰC HIỆN HỢP ĐỒNG THUÊ TÀU ĐỊNH HẠN (NYPE 93/2015) ===")
    typer.echo(f"Tốc độ cam kết (sau trừ allowance): {result.warranted_net_speed_knots:.2f} kts")
    typer.echo(f"Tốc độ thời tiết tốt thực tế:       {result.actual_good_weather_speed_knots:.2f} kts")
    typer.echo(f"Suy giảm tốc độ (Deficiency):       {result.speed_deficiency_good_weather_knots:.2f} kts")
    typer.echo(f"Thời gian chậm trễ:                 {result.net_time_lost_hours:.1f} giờ ({result.net_time_lost_days:.2f} ngày)")
    typer.echo(f"Chênh lệch tiêu hao nhiên liệu:     {result.fuel_variance_tonnes:+.2f} tấn")
    typer.echo(f"Khiếu nại mất thời gian:            ${result.time_loss_financial_claim_usd:,.2f}")
    typer.echo(f"Khiếu nại vượt tiêu hao dầu:        ${result.fuel_variance_financial_claim_usd:,.2f}")
    typer.echo("--------------------------------------------------------------------------------")
    typer.echo(f"TỔNG KHIẾU NẠI RÒNG (NET CLAIM):    ${result.net_total_claim_usd:,.2f} USD")
    typer.echo(f"Trách nhiệm pháp lý:                {result.liability_determination.value}")
    typer.echo(f"Án lệ áp dụng:                      {result.legal_doctrine_applied}")
    typer.echo(f"Khuyến nghị:                        {result.recommendation_vi}")


@edo_app.command("settle")
def settle_edo_deposit(
    bl_number: str = typer.Option("SGN2026100801", "--bl", help="Bill of Lading number"),
    edo_ref: str = typer.Option("EDO-998877", "--edo", help="Electronic D/O Reference"),
    category: str = typer.Option("DRY_20FT", "--cat", help="Container category (DRY_20FT, DRY_40FT, REEFER_40FT)"),
    units: int = typer.Option(2, "--units", "-u", help="Container units"),
    deposit_per_unit: float = typer.Option(2000000.0, "--deposit", help="Deposit per unit in VND"),
    free_days: int = typer.Option(5, "--free-days", help="Free detention days allowed"),
    actual_days: int = typer.Option(8, "--actual-days", help="Actual days until empty return"),
    daily_rate: float = typer.Option(250000.0, "--rate", help="Daily detention rate per unit in VND"),
    repair_cost: float = typer.Option(500000.0, "--repair", help="IICL repair deduction in VND"),
    cleaning_cost: float = typer.Option(200000.0, "--cleaning", help="Container cleaning fee in VND"),
):
    """
    Settle electronic D/O container deposit with demurrage/detention and IICL damages.
    """
    cat_enum = ContainerCategory[category] if category in ContainerCategory.__members__ else ContainerCategory.DRY_20FT
    params = ContainerDepositParams(
        category=cat_enum,
        unit_count=units,
        deposit_per_unit_vnd=deposit_per_unit,
        free_days_allowed=free_days,
        actual_days_to_return=actual_days,
        daily_detention_rate_vnd=daily_rate,
        iicl_damage_repair_vnd=repair_cost,
        container_cleaning_fee_vnd=cleaning_cost,
    )

    result = ElectronicDeliveryOrderEngine.calculate_deposit_settlement(bl_number, edo_ref, params)

    typer.echo("=== QUYẾT TOÁN CƯỢC VỎ CONTAINER & LỆNH GIAO HÀNG ĐIỆN TỬ (e-D/O) ===")
    typer.echo(f"Vận đơn / Mã e-D/O:            {result.bl_number} / {result.edo_reference}")
    typer.echo(f"Tổng tiền cược đã thu:         {result.total_deposit_held_vnd:,.0f} VND")
    typer.echo(f"Số ngày quá hạn:               {result.overdue_days} ngày")
    typer.echo(f"Phí lưu container (Detention): {result.detention_charge_total_vnd:,.0f} VND")
    typer.echo(f"Chi phí sửa chữa (IICL):       {result.repair_deduction_total_vnd:,.0f} VND")
    typer.echo(f"Phí vệ sinh container:         {result.cleaning_deduction_total_vnd:,.0f} VND")
    typer.echo(f"Tổng các khoản khấu trừ:       {result.total_deductions_vnd:,.0f} VND")
    typer.echo("--------------------------------------------------------------------")
    typer.echo(f"SỐ TIỀN HOÀN TRẢ KHÁCH HÀNG:   {result.net_refund_payable_vnd:,.0f} VND")
    if result.additional_balance_due_vnd > 0:
        typer.echo(f"Số tiền khách phải nộp thêm:   {result.additional_balance_due_vnd:,.0f} VND")
    typer.echo(f"Thời hạn hoàn cược quy định:   {result.statutory_refund_deadline_days} ngày làm việc")
    typer.echo(f"Kết luận:                      {result.compliance_verdict_vi}")


@tonnage_app.command("calculate")
def calculate_tonnage_dues(
    gross_tonnage: float = typer.Option(25000.0, "--gt", help="Vessel Gross Tonnage (GT)"),
    voyage_type: str = typer.Option("INTERNATIONAL", "--voyage", help="Voyage type (INTERNATIONAL / DOMESTIC)"),
    port_zone: str = typer.Option("ZONE_III_SOUTH", "--zone", help="Maritime Port Zone"),
    calls: int = typer.Option(1, "--calls", help="Number of port calls"),
    anchorage_hours: float = typer.Option(36.0, "--anchorage", help="Anchorage hours"),
    green_award: bool = typer.Option(False, "--green", help="Vessel has Green Award certificate (10% discount)"),
    transshipment: bool = typer.Option(False, "--transshipment", help="Transshipment cargo only (50% safety dues discount)"),
):
    """
    Calculate statutory Seaport Tonnage Dues, Maritime Safety Dues & Anchorage Tariffs.
    """
    v_type = VoyageType[voyage_type] if voyage_type in VoyageType.__members__ else VoyageType.INTERNATIONAL
    p_zone = PortMaritimeZone[port_zone] if port_zone in PortMaritimeZone.__members__ else PortMaritimeZone.ZONE_III_SOUTH

    call_data = VesselPortCallData(
        vessel_gross_tonnage_gt=gross_tonnage,
        voyage_type=v_type,
        port_zone=p_zone,
        number_of_port_calls=calls,
        anchorage_hours=anchorage_hours,
        has_green_award_certificate=green_award,
        is_transshipment_cargo_only=transshipment,
    )

    result = SeaportTonnageTariffEngine.calculate_dues(call_data)

    typer.echo("=== BIỂU PHÍ TRỌNG TẢI & BẢO ĐẢM HÀNG HẢI CẢNG BIỂN (THÔNG TƯ 39/2023) ===")
    typer.echo(f"Dung tích tàu (GT):           {gross_tonnage:,.0f} GT ({voyage_type})")
    typer.echo(f"Phí trọng tải luồng vào/ra:   {result.tonnage_dues_entry_exit_total:,.2f} {result.currency}")
    typer.echo(f"Phí bảo đảm hàng hải:         {result.maritime_safety_dues_total:,.2f} {result.currency}")
    typer.echo(f"Phí neo đậu vùng nước cảng:   {result.anchorage_fairway_dues_total:,.2f} {result.currency}")
    if result.green_discount_amount > 0:
        typer.echo(f"Ưu đãi tàu xanh Green Award:  -{result.green_discount_amount:,.2f} {result.currency}")
    typer.echo("--------------------------------------------------------------------------")
    typer.echo(f"TỔNG CỘNG PHÍ NHÀ NƯỚC:       {result.grand_total_port_dues:,.2f} {result.currency}")
    typer.echo(f"Tóm tắt:                      {result.statutory_summary_vi}")


@imdg_app.command("evaluate")
def evaluate_imdg_cargo(
    primary_class: str = typer.Option("CLASS_3_FLAMMABLE_LIQUID", "--class", "-c", help="Primary IMDG Class"),
    secondary_class: Optional[str] = typer.Option("CLASS_5_1_OXIDIZING", "--sec-class", help="Secondary IMDG Class for segregation check"),
    tonnage: float = typer.Option(24.0, "--tonnage", help="Cargo gross weight in tons"),
):
    """
    Evaluate dangerous goods seaport handling, segregation code (Table 7.2.4) and safety perimeters.
    """
    p_cls = IMDGClass[primary_class] if primary_class in IMDGClass.__members__ else IMDGClass.CLASS_3_FLAMMABLE_LIQUID
    s_cls = IMDGClass[secondary_class] if secondary_class and secondary_class in IMDGClass.__members__ else None

    result = IMDGSafetyHandlingEngine.evaluate_cargo_handling(p_cls, s_cls, tonnage)

    typer.echo("=== ĐÁNH GIÁ AN TOÀN & CÁCH LY HÀNG NGUY HIỂM IMDG TẠI CẢNG BIỂN ===")
    typer.echo(f"Nhóm hàng IMDG:               {result.primary_class.value}")
    if result.secondary_class:
        typer.echo(f"Nhóm hàng kế cận:             {result.secondary_class.value}")
    typer.echo(f"Mã cách ly IMDG Table 7.2.4:  Cấp {result.segregation_code} ({result.segregation_requirement.value})")
    typer.echo(f"Khoảng cách đệm an toàn:      {result.minimum_buffer_distance_meters:.1f} mét")
    typer.echo(f"Quy trình khai thác cảng:     {result.port_handling_mode.value}")
    typer.echo(f"Thời gian lưu cầu tàu tối đa: {result.max_dockside_dwell_hours:.1f} giờ")
    typer.echo(f"Phụ phí xếp dỡ hàng nguy hiểm:{result.port_handling_surcharge_percent:+.0f}%")
    typer.echo(f"Quy trình cứu hỏa khẩn cấp:   {result.fire_safety_ems_schedule}")
    typer.echo("--------------------------------------------------------------------")
    typer.echo(f"Cảnh báo luật định:           {result.statutory_warning_vi}")
