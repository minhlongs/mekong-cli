"""CLI Commands for Maritime Casualty Inquiry, Electronic C/O, Tugboat Tariffs & SOLAS VGM."""

from typing import Optional
import typer

from src.core.maritime_casualty_co_tug_vgm_engine import (
    CasualtyType, ContainerVgmInput, ElectronicCOEngine, MarineCasualtyData,
    MarineCasualtyInquiryEngine, ProductOriginInput, SeaportTugTariffEngine,
    SolasVgmEngine, TradeAgreement, TugboatJobData, TugMaritimeZone, TugVoyageType,
)

casualty_app = typer.Typer(help="Marine casualty formal inquiry, classification & safety investigation board")
co_app = typer.Typer(help="Electronic Certificate of Origin (e-C/O) & Preferential Rules of Origin (ROO)")
tug_app = typer.Typer(help="Seaport tugboat towage tariffs & assisted berthing service charges")
vgm_app = typer.Typer(help="SOLAS Verified Gross Mass (VGM) container weighing & tolerance compliance")


@casualty_app.command("inquire")
def inquire_casualty(
    vessel: str = typer.Option("MV MEKONG PIONEER", "--vessel", "-v", help="Vessel name"),
    imo: str = typer.Option("9876543", "--imo", help="IMO number"),
    casualty_type: str = typer.Option("COLLISION", "--type", "-t", help="Casualty type (COLLISION, GROUNDING, FIRE_EXPLOSION)"),
    total_loss: bool = typer.Option(False, "--total-loss", help="Ship suffered constructive or actual total loss"),
    fatalities: int = typer.Option(0, "--fatalities", help="Number of fatalities"),
    severe_injuries: int = typer.Option(0, "--injuries", help="Number of severe injuries"),
    pollution: bool = typer.Option(False, "--pollution", help="Severe environmental pollution occurred"),
    immobilized: bool = typer.Option(False, "--immobilized", help="Vessel lost propulsion or is immobilized"),
    structural_damage: bool = typer.Option(False, "--damage", help="Major structural hull cracking or flooding"),
    hours: float = typer.Option(12.0, "--hours", help="Hours elapsed since accident occurred"),
):
    """Classify marine casualty severity and evaluate statutory reporting deadlines under Circular 34/2015."""
    c_type = CasualtyType[casualty_type] if casualty_type in CasualtyType.__members__ else CasualtyType.COLLISION
    report = MarineCasualtyInquiryEngine.evaluate_casualty(MarineCasualtyData(
        vessel_name=vessel, imo_number=imo, casualty_type=c_type, has_total_loss=total_loss,
        fatalities_count=fatalities, severe_injuries_count=severe_injuries, is_severe_pollution=pollution,
        is_immobilized=immobilized, has_major_structural_damage=structural_damage, hours_since_occurrence=hours,
    ))
    typer.echo(
        "=== BÁO CÁO PHÂN LOẠI & ĐIỀU TRA TAI NẠN HÀNG HẢI (THÔNG TƯ 34/2015) ===\n"
        f"Tàu / Số IMO:                  {vessel} / {imo}\n"
        f"Phân cấp mức độ tai nạn:       {report.severity_level.value}\n"
        f"Yêu cầu điều tra chính thức:   {'BẮT BUỘC' if report.is_mandatory_formal_inquiry else 'KHÔNG BẮT BUỘC'}\n"
        f"Thành lập Hội đồng điều tra:   {'CÓ' if report.casualty_board_required else 'KHÔNG'}\n"
        f"Thời hạn báo cáo khẩn cấp:     {report.emergency_report_deadline_hours:.0f} giờ ({'QUÁ HẠN' if report.is_emergency_report_overdue else 'ĐÚNG HẠN'})\n"
        f"Thời hạn nộp Bản khai tai nạn: {report.formal_declaration_deadline_hours:.0f} giờ sau khi cập cảng\n"
        f"Thời hạn hoàn thành điều tra:  Tối đa {report.statutory_investigation_max_days} ngày\n"
        "--------------------------------------------------------------------------------\n"
        f"Căn cứ pháp lý:                {report.legal_statute_reference}\n"
        f"Kết luận:                      {report.summary_vi}"
    )


@co_app.command("evaluate")
def evaluate_co(
    hs_code: str = typer.Option("8471.30", "--hs", help="Product 6-digit HS Code"),
    fta: str = typer.Option("EVFTA", "--fta", help="Trade Agreement (EVFTA, CPTPP, RCEP, ATIGA, VKFTA)"),
    fob: float = typer.Option(1000.0, "--fob", help="FOB price in USD"),
    vom: float = typer.Option(550.0, "--vom", help="Value of Originating Materials (VOM) in USD"),
    vnm: float = typer.Option(450.0, "--vnm", help="Value of Non-Originating Materials (VNM) in USD"),
    direct_cost: float = typer.Option(150.0, "--direct-cost", help="Direct labor and factory overhead in USD"),
    wholly_obtained: bool = typer.Option(False, "--wo", help="Is wholly obtained (WO)"),
):
    """Evaluate Rules of Origin (ROO) and electronic Certificate of Origin (e-C/O) eligibility."""
    fta_enum = TradeAgreement[fta] if fta in TradeAgreement.__members__ else TradeAgreement.EVFTA
    result = ElectronicCOEngine.evaluate_origin(ProductOriginInput(
        product_hs_code=hs_code, fob_price_usd=fob, originating_materials_value_usd=vom,
        non_originating_materials_value_usd=vnm, direct_labor_and_overhead_usd=direct_cost,
        trade_agreement=fta_enum, is_wholly_obtained=wholly_obtained,
    ))
    typer.echo(
        "=== THẨM ĐỊNH XUẤT XỨ HÀNG HÓA & CẤP e-C/O (NGHỊ ĐỊNH 31/2018) ===\n"
        f"Hiệp định thương mại:          {result.trade_agreement.value}\n"
        f"Mã HS thành phẩm:              {result.product_hs_code}\n"
        f"Tiêu chí xuất xứ:              {result.qualifying_criterion.value}\n"
        f"Tỷ lệ RVC (Build-Down):        {result.rvc_build_down_percent:.2f}%\n"
        f"Tỷ lệ RVC (Build-Up):          {result.rvc_build_up_percent:.2f}%\n"
        f"Tỷ lệ De Minimis:              {result.de_minimis_tolerance_percent:.2f}% ({'ĐẠT' if result.is_de_minimis_compliant else 'VƯỢT NGƯỠNG'})\n"
        "------------------------------------------------------------------\n"
        f"ĐỦ ĐIỀU KIỆN CẤP e-C/O:        {'ĐẠT (HỢP LỆ)' if result.is_originating else 'KHÔNG ĐẠT'}\n"
        f"Hưởng thuế ưu đãi FTA:         {'ĐƯỢC ÁP DỤNG' if result.preferential_duty_eligible else 'KHÔNG ÁP DỤNG'}\n"
        f"Kết luận:                      {result.statutory_verdict_vi}"
    )


@tug_app.command("calculate")
def calculate_tug_charges(
    voyage_type: str = typer.Option("INTERNATIONAL", "--voyage", help="Voyage type (INTERNATIONAL / DOMESTIC)"),
    zone: str = typer.Option("ZONE_III_SOUTH", "--zone", help="Maritime Port Zone"),
    horsepower: float = typer.Option(4000.0, "--hp", help="Tugboat engine horsepower (HP)"),
    tugs: int = typer.Option(2, "--tugs", "-t", help="Number of tugboats assisting"),
    hours: float = typer.Option(2.0, "--hours", "-h", help="Assistance duration in hours"),
    night: bool = typer.Option(False, "--night", help="Night operation (+30%)"),
    tanker: bool = typer.Option(False, "--tanker", help="Hazardous cargo / oil tanker escort (+30%)"),
    weather: bool = typer.Option(False, "--weather", help="Adverse weather / strong current (+50%)"),
    standby: bool = typer.Option(False, "--standby", help="Standby only (50% base rate)"),
):
    """Calculate statutory tugboat towage charges under Circular 39/2023/TT-BGTVT."""
    v_type = TugVoyageType[voyage_type] if voyage_type in TugVoyageType.__members__ else TugVoyageType.INTERNATIONAL
    p_zone = TugMaritimeZone[zone] if zone in TugMaritimeZone.__members__ else TugMaritimeZone.ZONE_III_SOUTH
    res = SeaportTugTariffEngine.calculate_towage(TugboatJobData(
        voyage_type=v_type, port_zone=p_zone, tugboat_horsepower_hp=horsepower, number_of_tugs=tugs,
        duration_hours=hours, is_night_operation=night, is_hazardous_cargo_tanker=tanker,
        is_adverse_weather=weather, is_standby_only=standby,
    ))
    typer.echo(
        "=== TÍNH CƯỚC DỊCH VỤ LAI DẮT CẢNG BIỂN (THÔNG TƯ 39/2023) ===\n"
        f"Đơn vị tính:                   {res.currency} ({zone})\n"
        f"Đơn giá giờ / tàu:             {res.base_hourly_rate:,.2f} {res.currency}/h\n"
        f"Cước cơ sở lai dắt:            {res.base_towage_charge:,.2f} {res.currency}"
    )
    if res.night_surcharge > 0:
        typer.echo(f"Phụ phí ban đêm (+30%):        +{res.night_surcharge:,.2f} {res.currency}")
    if res.hazmat_surcharge > 0:
        typer.echo(f"Phụ phí hàng nguy hiểm (+30%): +{res.hazmat_surcharge:,.2f} {res.currency}")
    if res.adverse_weather_surcharge > 0:
        typer.echo(f"Phụ phí sóng to/gió lớn (+50%):+{res.adverse_weather_surcharge:,.2f} {res.currency}")
    typer.echo(f"--------------------------------------------------------------\nTỔNG CƯỚC LAI DẮT PHẢI THU:    {res.total_tugboat_charge:,.2f} {res.currency}\nChi tiết:                      {res.breakdown_vi}")


@vgm_app.command("verify")
def verify_vgm(
    container: str = typer.Option("MSKU9081234", "--cntr", "-c", help="Container ISO number"),
    size: int = typer.Option(40, "--size", help="Container size in feet (20 or 40)"),
    tare: float = typer.Option(3850.0, "--tare", help="Tare weight in kg"),
    csc_max: float = typer.Option(32500.0, "--csc", help="CSC plate maximum operating gross mass in kg"),
    declared_vgm: Optional[float] = typer.Option(28000.0, "--declared", help="Declared VGM in kg (None if missing)"),
    measured_weight: float = typer.Option(28200.0, "--measured", "-m", help="Terminal weighbridge measured weight in kg"),
):
    """Verify SOLAS Verified Gross Mass (VGM) and gate tolerance compliance."""
    res = SolasVgmEngine.verify_vgm(ContainerVgmInput(
        container_number=container, container_size_ft=size, tare_weight_kg=tare,
        csc_max_gross_weight_kg=csc_max, declared_vgm_kg=declared_vgm, weighbridge_measured_gross_kg=measured_weight,
    ))
    typer.echo(
        "=== KIỂM TRA XÁC NHẬN KHỐI LƯỢNG CONTAINER (SOLAS VGM QUY ĐỊNH VI/2) ===\n"
        f"Số hiệu Container:             {res.container_number}\n"
        f"Trạng thái VGM:                {res.vgm_status.value}\n"
        f"Khối lượng khai báo:           {res.declared_vgm_kg:,.0f} kg\n"
        f"Khối lượng cân tại trạm:       {res.measured_gross_kg:,.0f} kg\n"
        f"Sai lệch khối lượng:           {res.variance_kg:+,.0f} kg ({res.variance_percentage:.2f}%)\n"
        f"Dung sai cho phép:             ±{res.allowed_tolerance_kg:,.0f} kg\n"
        f"Kiểm tra quá tải CSC:          {'QUÁ TẢI (CSC OVERLOAD)' if res.is_csc_overload else 'AN TOÀN'}\n"
        f"Phí dịch vụ cân tại cảng:      {res.terminal_weighing_fee_vnd:,.0f} VND\n"
        "------------------------------------------------------------------------\n"
        f"Quyết định xếp tàu:            {res.statutory_verdict_vi}"
    )
