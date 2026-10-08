"""Typer CLI Commands for Maritime Cabotage Waiver, Liens Waterfall,

Seafarer Medical & Seaport PPP Concession Suite (Phases 251-254).

Statutory Frameworks:
- Phase 251: Vietnam Maritime Code 2015 Arts. 7, 21; Decree 58/2017/NĐ-CP (Cabotage Waiver)
- Phase 252: Vietnam Maritime Code 2015 Arts. 37-43; MLC 1993 (Maritime Liens Waterfall)
- Phase 253: STCW 1978/2010 Reg. I/9; Circular 22/2017/TT-BYT (Seafarer Medical Fitness)
- Phase 254: Law on PPP 2020; Decree 35/2021/NĐ-CP Art. 82 (Seaport PPP Revenue Sharing)
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_cabotage_liens_medical_concession_engine import (
    CabotagePermitType,
    CabotageWaiverReason,
    ClaimDistributionResult,
    MaritimeCabotageEngine,
    MaritimeClaimItem,
    MaritimeClaimTier,
    MaritimeLiensAuctionEngine,
    MedicalFitnessVerdict,
    PppConcessionModel,
    SeafarerDepartment,
    SeafarerMedicalEngine,
    SeaportConcessionEngine,
)

console = Console()

cabotage_app = typer.Typer(
    name="cabotage",
    help="Miễn trừ Vận tải Nội địa & Cấp phép Tàu Ngoại VMC 2015 / NĐ 58/2017 (Phase 251)",
    no_args_is_help=True,
)

liens_app = typer.Typer(
    name="liens",
    help="Thứ tự Ưu tiên Quyền Cầm giữ Hàng hải & Phân bổ Tiền Đấu giá Tàu VMC Art. 37 (Phase 252)",
    no_args_is_help=True,
)

seafarer_med_app = typer.Typer(
    name="seafarer-med",
    help="Chứng chỉ Sức khỏe Thuyền viên STCW Quy tắc I/9 & Thông tư 22/2017/TT-BYT (Phase 253)",
    no_args_is_help=True,
)

seaport_ppp_app = typer.Typer(
    name="seaport-ppp",
    help="Dự án PPP Cảng biển & Cơ chế Chia sẻ Rủi ro Doanh thu NĐ 35/2021 (Phase 254)",
    no_args_is_help=True,
)


# ==============================================================================
# PHASE 251: CABOTAGE WAIVER COMMANDS
# ==============================================================================

@cabotage_app.command(name="evaluate")
def cabotage_evaluate_cmd(
    app_id: str = typer.Option("VN-CAB-2026-001", "--id", "-i", help="Mã hồ sơ xin cấp phép"),
    vessel: str = typer.Option("PACIFIC_PIONEER", "--vessel", "-v", help="Tên tàu nước ngoài"),
    flag: str = typer.Option("PANAMA", "--flag", "-f", help="Quốc tịch / Cờ tàu"),
    gt: float = typer.Option(15000.0, "--gt", help="Dung tích tổng bộ (Gross Tonnage)"),
    reason: str = typer.Option("specialized_cargo", "--reason", "-r", help="Lý do: specialized_cargo, fleet_deficit, international_cruise, offshore_project"),
    permit: str = typer.Option("single_voyage", "--permit", "-p", help="Loại giấy phép: single_voyage, time_charter_3m, time_charter_6m, annual_12m"),
    cargo: str = typer.Option("Hóa chất lỏng chuyên dụng Chloroform", "--cargo", "-c", help="Mô tả hàng hóa / hành khách"),
    vn_available: bool = typer.Option(False, "--vn-avail", help="Đội tàu VN có phương tiện đáp ứng không"),
    age: int = typer.Option(8, "--age", help="Tuổi tàu (năm)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Đánh giá điều kiện cấp phép vận tải nội địa cho tàu biển mang cờ quốc tịch nước ngoài."""
    reason_enum = CabotageWaiverReason(reason)
    permit_enum = CabotagePermitType(permit)

    result = MaritimeCabotageEngine.evaluate_cabotage_permit(
        application_id=app_id,
        vessel_name=vessel,
        flag_state=flag,
        gross_tonnage=gt,
        reason=reason_enum,
        permit_type=permit_enum,
        cargo_or_passenger_desc=cargo,
        domestic_fleet_available=vn_available,
        vessel_age_years=age,
    )

    if as_json:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="KẾT QUẢ ĐÁNH GIÁ CẤP PHÉP VẬN TẢI NỘI ĐỊA (CABOTAGE)", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="yellow")

    table.add_row("Mã hồ sơ", result.application_id)
    table.add_row("Tên tàu / Cờ", f"{result.vessel_name} ({result.flag_state})")
    table.add_row("Dung tích (GT)", f"{result.gross_tonnage:,.0f} GT")
    table.add_row("Căn cứ xin phép", result.reason.value)
    table.add_row("Loại giấy phép", result.permit_type.value)
    table.add_row("Trạng thái phê duyệt", "[green]CHẤP THUẬN[/green]" if result.is_approved else "[red]TỪ CHỐI[/red]")
    table.add_row("Thời hạn cấp phép", f"{result.permit_duration_days} ngày")
    table.add_row("Lệ phí cấp phép", f"{result.statutory_permit_fee_vnd:,.0f} VND")
    table.add_row("Thời gian xử lý", f"{result.processing_time_days} ngày làm việc")

    console.print(table)
    console.print(Panel(f"[bold]Điều kiện khai thác:[/bold]\n{result.operational_conditions}\n\n[bold]Ghi chú:[/bold] {result.remarks}", title="Kết luận Cục Hàng hải VN"))


# ==============================================================================
# PHASE 252: MARITIME LIENS WATERFALL COMMANDS
# ==============================================================================

@liens_app.command(name="distribute")
def liens_distribute_cmd(
    vessel: str = typer.Option("MV_OCEAN_PROVIDENCE", "--vessel", "-v", help="Tên tàu bán đấu giá"),
    proceeds: float = typer.Option(2_500_000.0, "--proceeds", "-p", help="Tổng tiền thu được từ bán đấu giá tàu (USD)"),
    court_costs: float = typer.Option(150_000.0, "--court-costs", help="Chi phí tố tụng, giữ tàu, giám định (Tier 0) (USD)"),
    wages: float = typer.Option(400_000.0, "--wages", help="Yêu cầu lương & hồi hương thuyền viên (Tier 1) (USD)"),
    injury: float = typer.Option(200_000.0, "--injury", help="Yêu cầu bồi thường tai nạn tính mạng (Tier 2) (USD)"),
    salvage: float = typer.Option(300_000.0, "--salvage", help="Tiền cứu hộ & tổn thất chung (Tier 3) (USD)"),
    port_dues: float = typer.Option(100_000.0, "--port-dues", help="Phí cảng biển & luồng hàng hải (Tier 4) (USD)"),
    property_dmg: float = typer.Option(250_000.0, "--prop-dmg", help="Thiệt hại đâm va va xô cầu cảng (Tier 5) (USD)"),
    mortgage: float = typer.Option(1_200_000.0, "--mortgage", "-m", help="Thế chấp ngân hàng đã đăng ký (Tier 6) (USD)"),
    general_debts: float = typer.Option(300_000.0, "--debts", help="Chủ nợ cung cấp dầu, đại lý (Tier 7) (USD)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Phân bổ số tiền bán đấu giá tàu biển theo thứ tự ưu tiên quyền cầm giữ hàng hải VMC 2015."""
    claims = [
        MaritimeClaimItem(claim_id="CLM-01", creditor_name="Thuyền viên tàu (Wages & Repatriation)", tier=MaritimeClaimTier.TIER_1_CREW_WAGES, claim_amount_usd=wages, claim_date_str="2026-01-10"),
        MaritimeClaimItem(claim_id="CLM-02", creditor_name="Gia đình thuyền viên tử nạn (Personal Injury)", tier=MaritimeClaimTier.TIER_2_PERSONAL_INJURY, claim_amount_usd=injury, claim_date_str="2026-02-15"),
        MaritimeClaimItem(claim_id="CLM-03", creditor_name="Đơn vị cứu hộ hàng hải (Salvage / GA)", tier=MaritimeClaimTier.TIER_3_SALVAGE_GA, claim_amount_usd=salvage, claim_date_str="2026-03-01"),
        MaritimeClaimItem(claim_id="CLM-04", creditor_name="Cảng vụ Hàng hải (Port & Safety Dues)", tier=MaritimeClaimTier.TIER_4_PORT_DUES, claim_amount_usd=port_dues, claim_date_str="2026-03-20"),
        MaritimeClaimItem(claim_id="CLM-05", creditor_name="Chủ cầu cảng bị đâm va (Allision Damage)", tier=MaritimeClaimTier.TIER_5_PROPERTY_DAMAGE, claim_amount_usd=property_dmg, claim_date_str="2026-04-05"),
        MaritimeClaimItem(claim_id="CLM-06", creditor_name="Ngân hàng Ngoại thương (Registered Mortgage)", tier=MaritimeClaimTier.TIER_6_SHIP_MORTGAGE, claim_amount_usd=mortgage, claim_date_str="2025-06-15"),
        MaritimeClaimItem(claim_id="CLM-07", creditor_name="Đại lý nhiên liệu & Sửa chữa (Bunker Supplier)", tier=MaritimeClaimTier.TIER_7_GENERAL_CREDITORS, claim_amount_usd=general_debts, claim_date_str="2026-05-10"),
    ]

    report = MaritimeLiensAuctionEngine.distribute_auction_proceeds(
        vessel_name=vessel,
        gross_auction_proceeds_usd=proceeds,
        claims=claims,
        court_custody_costs_usd=court_costs,
    )

    if as_json:
        data = {
            "vessel_name": report.vessel_name,
            "gross_auction_proceeds_usd": report.gross_auction_proceeds_usd,
            "court_custody_costs_usd": report.court_custody_costs_usd,
            "net_distributable_funds_usd": report.net_distributable_funds_usd,
            "total_claims_demanded_usd": report.total_claims_demanded_usd,
            "total_claims_paid_usd": report.total_claims_paid_usd,
            "surplus_to_shipowner_usd": report.surplus_to_shipowner_usd,
            "waterfall_summary": report.waterfall_summary,
            "distributions": [d.__dict__ for d in report.claims_distributions],
        }
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"THỨ TỰ PHÂN BỔ TIỀN BÁN ĐẤU GIÁ TÀU {vessel} (VMC 2015)", box=box.ROUNDED)
    table.add_column("Mã", style="dim")
    table.add_column("Chủ nợ", style="cyan")
    table.add_column("Cấp ưu tiên (Tier)", style="magenta")
    table.add_column("Đòi nợ (USD)", justify="right")
    table.add_column("Được trả (USD)", justify="right", style="green")
    table.add_column("Tỷ lệ %", justify="right", style="yellow")
    table.add_column("Trạng thái", style="white")

    for d in report.claims_distributions:
        table.add_row(
            d.claim_id,
            d.creditor_name,
            d.tier.value,
            f"${d.original_claim_usd:,.2f}",
            f"${d.allocated_payout_usd:,.2f}",
            f"{d.recovery_rate_pct:.1f}%",
            d.status,
        )

    console.print(table)
    console.print(Panel(
        f"[bold]Tổng thu bán đấu giá:[/bold] ${report.gross_auction_proceeds_usd:,.2f}\n"
        f"[bold]Trừ chi phí tố tụng (Tier 0):[/bold] ${report.court_custody_costs_usd:,.2f}\n"
        f"[bold]Tiền thanh toán chủ nợ:[/bold] ${report.total_claims_paid_usd:,.2f}\n"
        f"[bold]Thặng dư trả chủ tàu:[/bold] ${report.surplus_to_shipowner_usd:,.2f}\n\n"
        f"{report.waterfall_summary}",
        title="Báo cáo Phân phối Tiền Thi hành án Dân sự",
    ))


# ==============================================================================
# PHASE 253: SEAFARER MEDICAL COMMANDS
# ==============================================================================

@seafarer_med_app.command(name="evaluate")
def seafarer_med_evaluate_cmd(
    cert_id: str = typer.Option("MED-VN-2026-901", "--id", "-i", help="Mã chứng chỉ y tế"),
    name: str = typer.Option("Nguyễn Văn An", "--name", "-n", help="Họ và tên thuyền viên"),
    dob: str = typer.Option("1992-05-14", "--dob", help="Ngày tháng năm sinh"),
    dept: str = typer.Option("deck_officer", "--dept", "-d", help="Bộ phận: deck_officer, engine_officer, deck_rating, engine_rating, catering"),
    va_r: float = typer.Option(1.0, "--var", help="Thị lực mắt phải (hệ 10/10)"),
    va_l: float = typer.Option(1.0, "--val", help="Thị lực mắt trái (hệ 10/10)"),
    color_pass: bool = typer.Option(True, "--color/--no-color", help="Thị giác màu sắc Ishihara"),
    hearing_db: float = typer.Option(20.0, "--hearing", help="Thính lực bình quân (dB)"),
    bp_sys: int = typer.Option(120, "--sys", help="Huyết áp tâm thu (mmHg)"),
    bp_dia: int = typer.Option(80, "--dia", help="Huyết áp tâm trương (mmHg)"),
    bmi: float = typer.Option(23.5, "--bmi", help="Chỉ số khối cơ thể (BMI)"),
    age: int = typer.Option(34, "--age", help="Tuổi hiện tại"),
    glasses: bool = typer.Option(False, "--glasses/--no-glasses", help="Có đeo kính thuốc điều chỉnh không"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Kiểm tra và đánh giá cấp chứng chỉ sức khỏe thuyền viên STCW Reg. I/9 & TT 22/2017/TT-BYT."""
    dept_enum = SeafarerDepartment(dept)

    cert = SeafarerMedicalEngine.evaluate_fitness(
        certificate_id=cert_id,
        seafarer_name=name,
        date_of_birth=dob,
        department=dept_enum,
        visual_acuity_right=va_r,
        visual_acuity_left=va_l,
        color_vision_pass=color_pass,
        hearing_threshold_db=hearing_db,
        blood_pressure_systolic=bp_sys,
        blood_pressure_diastolic=bp_dia,
        bmi=bmi,
        age_years=age,
        requires_corrective_lenses=glasses,
    )

    if as_json:
        typer.echo(json.dumps(cert.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="KẾT QUẢ KHÁM SỨC KHỎE THUYỀN VIÊN STCW REG. I/9", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="yellow")

    table.add_row("Mã chứng chỉ", cert.certificate_id)
    table.add_row("Họ và tên / NS", f"{cert.seafarer_name} ({cert.date_of_birth})")
    table.add_row("Chức danh / Ban", cert.department.value)
    table.add_row("Thị lực (MP / MT)", f"{cert.visual_acuity_right} / {cert.visual_acuity_left}")
    table.add_row("Thị giác màu sắc", "ĐẠT (Pass)" if cert.color_vision_pass else "KHÔNG ĐẠT (Fail)")
    table.add_row("Thính lực (Audiometry)", f"{cert.hearing_threshold_db} dB")
    table.add_row("Huyết áp (Sys/Dia)", f"{cert.blood_pressure_systolic}/{cert.blood_pressure_diastolic} mmHg")
    table.add_row("Chỉ số BMI", f"{cert.bmi:.1f}")
    table.add_row("Kết luận sức khỏe", f"[bold green]{cert.verdict.value}[/bold green]" if cert.verdict == MedicalFitnessVerdict.FIT_UNRESTRICTED else f"[bold red]{cert.verdict.value}[/bold red]")
    table.add_row("Thời hạn hiệu lực", f"{cert.validity_months} tháng")

    console.print(table)
    console.print(Panel(
        f"[bold]Điều kiện hạn chế:[/bold] {cert.restriction_notes}\n"
        f"[bold]Nhận xét y bạ:[/bold] {cert.statutory_remarks}",
        title="Chứng chỉ Y tế Thuyền viên Quốc tế",
    ))


# ==============================================================================
# PHASE 254: SEAPORT PPP CONCESSION COMMANDS
# ==============================================================================

@seaport_ppp_app.command(name="financials")
def seaport_ppp_financials_cmd(
    capex: float = typer.Option(5_000_000_000_000.0, "--capex", "-c", help="Tổng mức đầu tư CAPEX (VND)"),
    equity: float = typer.Option(1_000_000_000_000.0, "--equity", "-e", help="Vốn chủ sở hữu của nhà đầu tư (VND)"),
    interest: float = typer.Option(9.5, "--interest", "-i", help="Lãi suất vay thương mại (%/năm)"),
    tenor: int = typer.Option(15, "--tenor", "-t", help="Thời hạn vay vốn (năm)"),
    ebitda: float = typer.Option(600_000_000_000.0, "--ebitda", help="EBITDA bình quân năm dự kiến (VND)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Đánh giá tính khả thi tài chính và tỷ lệ vốn chủ sở hữu dự án PPP cảng biển."""
    metrics = SeaportConcessionEngine.evaluate_ppp_financials(
        total_capex_vnd=capex,
        equity_capital_vnd=equity,
        debt_interest_rate_pct=interest,
        loan_tenor_years=tenor,
        expected_annual_ebitda_vnd=ebitda,
    )

    if as_json:
        typer.echo(json.dumps(metrics.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="ĐÁNH GIÁ CHỈ SỐ TÀI CHÍNH DỰ ÁN PPP CẢNG BIỂN (LUẬT PPP 2020)", box=box.ROUNDED)
    table.add_column("Chỉ tiêu", style="cyan")
    table.add_column("Giá trị", style="yellow")

    table.add_row("Tổng mức đầu tư (CAPEX)", f"{metrics.total_capex_vnd:,.0f} VND")
    table.add_row("Tỷ lệ Vốn chủ sở hữu (Equity)", f"{metrics.equity_ratio_pct:.2f}% (Tối thiểu 15%)")
    table.add_row("Tỷ lệ Vốn vay (Debt)", f"{metrics.debt_ratio_pct:.2f}%")
    table.add_row("Đạt ngưỡng vốn chủ sở hữu", "[green]ĐẠT[/green]" if metrics.meets_equity_statutory_threshold else "[red]KHÔNG ĐẠT[/red]")
    table.add_row("Nghĩa vụ trả nợ năm (Debt Service)", f"{metrics.annual_debt_service_vnd:,.0f} VND")
    table.add_row("Hệ số DSCR bình quân", f"{metrics.average_dscr:.2f}x (Yêu cầu >= 1.20x)")
    table.add_row("Dự phóng IRR dự án", f"{metrics.project_irr_pct:.2f}%")
    table.add_row("Kết luận tính khả thi", "[bold green]KHẢ THI[/bold green]" if metrics.financial_feasibility else "[bold red]KHÔNG KHẢ THI[/bold red]")

    console.print(table)
    console.print(Panel(metrics.remarks, title="Kết luận Hội đồng Thẩm định Dự án PPP"))


@seaport_ppp_app.command(name="sharing")
def seaport_ppp_sharing_cmd(
    year: int = typer.Option(2026, "--year", "-y", help="Năm tài chính khai thác cảng"),
    plan_rev: float = typer.Option(1_000_000_000_000.0, "--plan", "-p", help="Doanh thu theo phương án tài chính hợp đồng (VND)"),
    act_rev: float = typer.Option(680_000_000_000.0, "--act", "-a", help="Doanh thu thực tế kiểm toán xác nhận (VND)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán cơ chế chia sẻ rủi ro tăng/giảm doanh thu Nghị định 35/2021/NĐ-CP Điều 82."""
    settlement = SeaportConcessionEngine.calculate_decree35_revenue_sharing(
        year=year,
        planned_revenue_vnd=plan_rev,
        actual_revenue_vnd=act_rev,
    )

    if as_json:
        typer.echo(json.dumps(settlement.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"QUYẾT TOÁN CƠ CHẾ CHIA SẺ DOANH THU PPP NĂM {year} (NĐ 35/2021)", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="yellow")

    table.add_row("Doanh thu quy định hợp đồng", f"{settlement.planned_revenue_vnd:,.0f} VND")
    table.add_row("Doanh thu thực tế đạt được", f"{settlement.actual_revenue_vnd:,.0f} VND")
    table.add_row("Tỷ lệ đạt doanh thu kế hoạch", f"{settlement.revenue_ratio_pct:.2f}%")
    table.add_row("Ngưỡng sàn chia sẻ (75%)", f"{settlement.lower_threshold_75_vnd:,.0f} VND")
    table.add_row("Ngưỡng trần chia sẻ (125%)", f"{settlement.upper_threshold_125_vnd:,.0f} VND")
    table.add_row("Nhà nước bù cho Nhà đầu tư", f"[bold green]{settlement.state_share_payout_to_investor_vnd:,.0f} VND[/bold green]")
    table.add_row("Nhà đầu tư nộp lại Ngân sách", f"[bold red]{settlement.investor_share_payout_to_state_vnd:,.0f} VND[/bold red]")

    console.print(table)
    console.print(Panel(settlement.mechanism_triggered, title="Thông báo Cơ quan Nhà nước có Thẩm quyền"))
