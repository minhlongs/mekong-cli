# -*- coding: utf-8 -*-
"""Typer CLI Subcommands for Phases 255-258.

Commands:
- shipagency: Maritime Ship Agency & Husbandry Disbursements (PDA/FDA)
- salvage: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement
- abandonment: Seafarer Repatriation & Abandonment Financial Security Guarantee
- greentug: Seaport Green Tug & Clean Energy Harbor Craft Transition
"""

from __future__ import annotations

import json
import typer

from src.core.maritime_agency_salvage_abandonment_cleanport_engine import (
    AbandonmentTrigger,
    DisbursementCategory,
    DisbursementItem,
    HarborCraftPropulsion,
    SalvedPropertyValues,
    SalvageContractRegime,
    SCOPICExpenseItem,
    SeafarerAbandonmentClaim,
    ShipAgencyDisbursementEngine,
    MaritimeSalvageEngine,
    SeafarerAbandonmentEngine,
    GreenHarborCraftEngine,
)

shipagency_app = typer.Typer(
    name="shipagency",
    help="Phase 255: Maritime Ship Agency & Disbursements (PDA/FDA) Accounting",
    no_args_is_help=True,
)

salvage_app = typer.Typer(
    name="salvage",
    help="Phase 256: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement",
    no_args_is_help=True,
)

abandonment_app = typer.Typer(
    name="abandonment",
    help="Phase 257: Seafarer Repatriation & Abandonment Financial Security Guarantee",
    no_args_is_help=True,
)

greentug_app = typer.Typer(
    name="greentug",
    help="Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives",
    no_args_is_help=True,
)


# ==============================================================================
# PHASE 255: SHIP AGENCY PDA/FDA
# ==============================================================================

@shipagency_app.command(name="reconcile")
def cmd_shipagency_reconcile(
    vessel: str = typer.Option("MV_PACIFIC_VOYAGER", "--vessel", "-v", help="Tên tàu"),
    call_id: str = typer.Option("CALL-VN-2026-001", "--call-id", help="Mã chuyến cập cảng"),
    port: str = typer.Option("CẢNG CÁI MÉP", "--port", help="Tên cảng biển"),
    gt: float = typer.Option(25000.0, "--gt", help="Dung tích toàn phần (Gross Tonnage)"),
    advance: float = typer.Option(50000.0, "--advance", help="Tiền tạm ứng chủ tàu đã chuyển (USD)"),
    port_dues: float = typer.Option(18000.0, "--port-dues", help="Phí cảng biển thực tế (USD)"),
    pilotage: float = typer.Option(7500.0, "--pilotage", help="Phí hoa tiêu thực tế (USD)"),
    tugboat: float = typer.Option(12000.0, "--tugboat", help="Phí tàu lai dắt thực tế (USD)"),
    stay_days: int = typer.Option(3, "--stay-days", help="Số ngày tàu lưu tại cảng"),
    is_tanker: bool = typer.Option(False, "--tanker", help="Tàu chở dầu/hàng nguy hiểm"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Quyết toán giải ngân chi phí tàu biển (PDA vs FDA) theo Nghị định 160/2016."""
    items = [
        DisbursementItem("ITEM-01", DisbursementCategory.PORT_DUES, "Cảng phí luồng hàng hải", port_dues * 0.95, port_dues),
        DisbursementItem("ITEM-02", DisbursementCategory.PILOTAGE, "Phí dẫn tàu hoa tiêu", pilotage * 0.95, pilotage),
        DisbursementItem("ITEM-03", DisbursementCategory.TUGBOAT_SERVICES, "Tàu lai hỗ trợ cập/rời cầu", tugboat * 0.95, tugboat),
    ]

    report = ShipAgencyDisbursementEngine.reconcile_pda_fda(
        vessel_name=vessel,
        call_id=call_id,
        port_name=port,
        gross_tonnage=gt,
        advance_deposit_received_usd=advance,
        items=items,
        port_stay_days=stay_days,
        is_tanker_or_dangerous=is_tanker,
    )

    if json_output:
        typer.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"QUYẾT TOÁN TÀI KHOẢN GIẢI NGÂN ĐẠI LÝ (FDA) — {report.vessel_name}")
    typer.echo("=" * 70)
    typer.echo(f"Cảng thực hiện:               {report.port_name} (Call: {report.call_id})")
    typer.echo(f"Dung tích toàn phần (GT):     {report.gross_tonnage:,.0f} GT")
    typer.echo(f"Tiền tạm ứng đã nhận (PDA):   {report.advance_deposit_received_usd:,.2f} USD")
    typer.echo(f"Tổng chi phí cảng thực tế:    {report.total_actual_fda_usd:,.2f} USD")
    typer.echo(f"Phí đại lý luật định:         {report.statutory_agency_fee_usd:,.2f} USD")
    typer.echo(f"Tổng giải ngân ròng (FDA):    {report.net_disbursement_total_usd:,.2f} USD")
    typer.echo(f"Số dư quyết toán:             {report.balance_settlement_usd:,.2f} USD")
    typer.echo(f"Trạng thái:                   {report.settlement_status}")
    typer.echo(f"Ghi chú:                      {report.remarks}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 256: MARITIME SALVAGE & SCOPIC
# ==============================================================================

@salvage_app.command(name="settle")
def cmd_salvage_settle(
    sound_value: float = typer.Option(15000000.0, "--sound-val", help="Giá trị nguyên vẹn của tàu (USD)"),
    repairs: float = typer.Option(3000000.0, "--repairs", help="Chi phí sửa chữa hư hại (USD)"),
    cargo: float = typer.Option(8000000.0, "--cargo", help="Giá trị hàng hóa CIF (USD)"),
    freight: float = typer.Option(500000.0, "--freight", help="Cước vận chuyển rủi ro (USD)"),
    award_pct: float = typer.Option(12.0, "--award-pct", help="Tỷ lệ thù lao Điều 13 LOF (%)"),
    scopic_daily: float = typer.Option(25000.0, "--scopic-daily", help="Chi phí định mức ngày cứu hộ (USD)"),
    days: float = typer.Option(10.0, "--days", help="Số ngày thực hiện cứu hộ"),
    regime: str = typer.Option("scopic_invoked", "--regime", help="Chế độ cứu hộ: lof_article_13, scopic_invoked, article_14_special_compensation"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán phân bổ thù lao cứu hộ hàng hải theo LOF 2024 và điều khoản SCOPIC 2020."""
    regime_enum = SalvageContractRegime(regime)
    props = SalvedPropertyValues(
        sound_ship_value_usd=sound_value,
        damage_repair_costs_usd=repairs,
        cargo_cif_value_usd=cargo,
        unpaid_freight_at_risk_usd=freight,
    )
    items = [SCOPICExpenseItem("Tàu kéo cứu hộ 150T BP", scopic_daily, days)]

    res = MaritimeSalvageEngine.calculate_salvage_settlement(
        property_values=props,
        assessed_art13_award_percentage=award_pct,
        regime=regime_enum,
        scopic_items=items,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo("QUYẾT TOÁN THÙ LAO CỨU HỘ BIỂN & ĐIỀU KHOẢN SCOPIC")
    typer.echo("=" * 70)
    typer.echo(f"Quỹ tài sản cứu được (Net Fund): {res.net_salved_fund_usd:,.2f} USD")
    typer.echo(f"Thù lao Điều 13 đánh giá:        {res.article_13_assessed_award_usd:,.2f} USD")
    typer.echo(f"Chi phí định mức SCOPIC (gốc):   {res.scopic_costs_usd:,.2f} USD")
    typer.echo(f"Thưởng SCOPIC (+25%):            {res.scopic_bonus_uplift_usd:,.2f} USD")
    typer.echo(f"Tổng định mức SCOPIC:            {res.total_scopic_remuneration_usd:,.2f} USD")
    typer.echo(f"Khấu trừ giảm thưởng (25% penalty): {res.article_13_discount_penalty_usd:,.2f} USD")
    typer.echo(f"THÙ LAO BÊN CỨU HỘ ĐƯỢC NHẬN:    {res.final_salvor_remuneration_usd:,.2f} USD")
    typer.echo(f"- Bảo hiểm tài sản (H&M/Cargo):  {res.property_underwriters_liability_usd:,.2f} USD")
    typer.echo(f"- Trách nhiệm Hội P&I:           {res.pni_club_liability_usd:,.2f} USD")
    typer.echo(f"Kết luận:                        {res.settlement_summary}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 257: SEAFARER ABANDONMENT FINANCIAL GUARANTEE
# ==============================================================================

@abandonment_app.command(name="adjudicate")
def cmd_abandonment_adjudicate(
    vessel: str = typer.Option("MV_ABANDONED_STAR", "--vessel", help="Tên tàu"),
    imo: str = typer.Option("9348123", "--imo", help="Số IMO của tàu"),
    insurer: str = typer.Option("GARD P&I CLUB", "--insurer", help="Tổ chức bảo lãnh tài chính"),
    trigger: str = typer.Option("unpaid_wages_2_months", "--trigger", help="Nguyên nhân kích hoạt: unpaid_wages_2_months, failure_to_repatriate, lack_of_provisions_support, severed_shipowner_ties"),
    crew_count: int = typer.Option(18, "--crew-count", help="Số lượng thuyền viên bị bỏ rơi"),
    avg_wage: float = typer.Option(2200.0, "--avg-wage", help="Lương cơ bản bình quân hàng tháng (USD)"),
    unpaid_months: float = typer.Option(5.0, "--unpaid-months", help="Số tháng bị nợ lương"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Thẩm định chi trả bảo đảm tài chính hồi hương thuyền viên theo MLC 2006 Standard A2.5.2."""
    trig_enum = AbandonmentTrigger(trigger)
    claims = []
    for i in range(1, crew_count + 1):
        actual_debt = avg_wage * unpaid_months
        claims.append(
            SeafarerAbandonmentClaim(
                seafarer_name=f"Thuyền viên #{i}",
                rank_or_role="Thủy thủ / Sĩ quan",
                nationality="Việt Nam",
                monthly_basic_wage_usd=avg_wage,
                months_unpaid=unpaid_months,
                actual_outstanding_wages_usd=actual_debt,
                repatriation_home_country="Việt Nam",
                estimated_travel_cost_usd=1200.0,
                stranding_days_onboard=20,
            )
        )

    res = SeafarerAbandonmentEngine.adjudicate_abandonment(
        vessel_name=vessel,
        imo_number=imo,
        guarantor_pni_insurer=insurer,
        trigger=trig_enum,
        claims=claims,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"THẨM ĐỊNH BẢO ĐẢM TÀI CHÍNH THUYỀN VIÊN (MLC 2006) — {res.vessel_name}")
    typer.echo("=" * 70)
    typer.echo(f"Số IMO:                       {res.imo_number}")
    typer.echo(f"Tổ chức cấp bảo lãnh:         {res.guarantor_pni_insurer}")
    typer.echo(f"Số thuyền viên bảo hộ:        {res.total_seafarers_stranded} người")
    typer.echo(f"Tổng lương nợ yêu cầu:        {res.total_gross_wages_claimed_usd:,.2f} USD")
    typer.echo(f"Lương chốt trần (tối đa 4m):  {res.total_statutory_capped_wages_usd:,.2f} USD")
    typer.echo(f"Chi phí vé máy bay hồi hương: {res.total_repatriation_transit_costs_usd:,.2f} USD")
    typer.echo(f"Trợ cấp sinh hoạt phí khẩn cấp:{res.total_subsistence_allowance_usd:,.2f} USD")
    typer.echo(f"TỔNG CHI TRẢ BẢO ĐÃM:         {res.total_guarantee_payout_usd:,.2f} USD")
    typer.echo(f"Quyền truy đòi chủ tàu:       {res.shipowner_recourse_claim_usd:,.2f} USD")
    typer.echo(f"Phán quyết:                   {res.adjudication_verdict}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 258: GREEN TUG & CLEAN HARBOR CRAFT
# ==============================================================================

@greentug_app.command(name="evaluate")
def cmd_greentug_evaluate(
    craft: str = typer.Option("TÀU LAI XANH SÀI GÒN 01", "--craft", help="Tên phương tiện thủy"),
    bp: float = typer.Option(60.0, "--bp", help="Sức kéo cột bích (Bollard Pull tonnes)"),
    tech: str = typer.Option("pure_battery_electric", "--tech", help="Công nghệ: conventional_diesel, hybrid_diesel_electric, pure_battery_electric, green_hydrogen_fc, green_e_methanol"),
    hours: float = typer.Option(2500.0, "--hours", help="Số giờ hoạt động hàng năm"),
    capex_premium: float = typer.Option(1800000.0, "--capex-premium", help="Phí chênh lệch vốn đầu tư xanh (USD)"),
    port_dues: float = typer.Option(90000.0, "--port-dues", help="Cảng phí luồng tuyến nộp hàng năm (USD)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Đánh giá chuyển đổi xanh tàu lai và ưu đãi phí cảng theo Quyết định 876/QĐ-TTg."""
    prop_enum = HarborCraftPropulsion(tech)
    res = GreenHarborCraftEngine.evaluate_transition(
        craft_name=craft,
        bollard_pull_tonnes=bp,
        propulsion=prop_enum,
        annual_operating_hours=hours,
        capex_green_premium_usd=capex_premium,
        annual_port_dues_paid_usd=port_dues,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"ĐÁNH GIÁ CHUYỂN ĐỔI XANH PHƯƠNG TIỆN CẢNG BIỂN — {res.craft_name}")
    typer.echo("=" * 70)
    typer.echo(f"Công nghệ động lực:           {res.propulsion}")
    typer.echo(f"Sức kéo cột bích (Bollard Pull): {res.bollard_pull_tonnes:.1f} T")
    typer.echo(f"Phát thải cơ sở MGO:          {res.baseline_mgo_co2_tonnes_per_year:,.1f} tấn CO2/năm")
    typer.echo(f"Lượng CO2 cắt giảm:           {res.abated_co2_tonnes_per_year:,.1f} tấn ({res.abatement_ratio_pct:.1f}%)")
    typer.echo(f"Tiết kiệm chi phí nhiên liệu: {res.annual_fuel_cost_savings_usd:,.2f} USD/năm")
    typer.echo(f"Ưu đãi giảm phí cảng biển:    {res.annual_green_tariff_rebate_usd:,.2f} USD/năm")
    typer.echo(f"Tổng lợi ích kinh tế hàng năm:{res.annual_total_economic_benefit_usd:,.2f} USD/năm")
    typer.echo(f"Chi phí đầu tư xanh (CAPEX):  {res.capex_green_premium_usd:,.2f} USD")
    typer.echo(f"Thời gian hoàn vốn (PBP):     {res.simple_payback_years:.1f} năm")
    typer.echo(f"Phù hợp Quyết định 876:       {'ĐẠT' if res.statutory_incentive_compliance else 'CHƯA ĐẠT'}")
    typer.echo(f"Đánh giá:                     {res.remarks}")
    typer.echo("=" * 70)
