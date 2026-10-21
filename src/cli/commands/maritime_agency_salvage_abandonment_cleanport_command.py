# -*- coding: utf-8 -*-
"""Typer CLI Subcommands for Phases 255-258."""

from __future__ import annotations

import json
import typer

from src.core.maritime_agency_salvage_abandonment_cleanport_engine import (
    AbandonmentTrigger, DisbursementCategory, DisbursementItem,
    HarborCraftPropulsion, SalvedPropertyValues, SalvageContractRegime,
    SCOPICExpenseItem, SeafarerAbandonmentClaim, ShipAgencyDisbursementEngine,
    MaritimeSalvageEngine, SeafarerAbandonmentEngine, GreenHarborCraftEngine,
)

shipagency_app = typer.Typer(name="shipagency", help="Phase 255: Maritime Ship Agency & Disbursements (PDA/FDA) Accounting", no_args_is_help=True)
salvage_app = typer.Typer(name="salvage", help="Phase 256: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement", no_args_is_help=True)
abandonment_app = typer.Typer(name="abandonment", help="Phase 257: Seafarer Repatriation & Abandonment Financial Security Guarantee", no_args_is_help=True)
greentug_app = typer.Typer(name="greentug", help="Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives", no_args_is_help=True)


def _echo_box(title: str, lines: list[str]) -> None:
    typer.echo("\n".join(["=" * 70, title, "=" * 70, *lines, "=" * 70]))


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
    report = ShipAgencyDisbursementEngine.reconcile_pda_fda(vessel, call_id, port, gt, advance, items, stay_days, is_tanker)
    if json_output:
        typer.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    _echo_box(f"QUYẾT TOÁN TÀI KHOẢN GIẢI NGÂN ĐẠI LÝ (FDA) — {report.vessel_name}", [
        f"Cảng thực hiện:               {report.port_name} (Call: {report.call_id})",
        f"Dung tích toàn phần (GT):     {report.gross_tonnage:,.0f} GT",
        f"Tiền tạm ứng đã nhận (PDA):   {report.advance_deposit_received_usd:,.2f} USD",
        f"Tổng chi phí cảng thực tế:    {report.total_actual_fda_usd:,.2f} USD",
        f"Phí đại lý luật định:         {report.statutory_agency_fee_usd:,.2f} USD",
        f"Tổng giải ngân ròng (FDA):    {report.net_disbursement_total_usd:,.2f} USD",
        f"Số dư quyết toán:             {report.balance_settlement_usd:,.2f} USD",
        f"Trạng thái:                   {report.settlement_status}",
        f"Ghi chú:                      {report.remarks}",
    ])


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
    res = MaritimeSalvageEngine.calculate_salvage_settlement(
        SalvedPropertyValues(sound_value, repairs, cargo, freight), award_pct,
        SalvageContractRegime(regime), [SCOPICExpenseItem("Tàu kéo cứu hộ 150T BP", scopic_daily, days)],
    )
    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return
    _echo_box("QUYẾT TOÁN THÙ LAO CỨU HỘ BIỂN & ĐIỀU KHOẢN SCOPIC", [
        f"Quỹ tài sản cứu được (Net Fund): {res.net_salved_fund_usd:,.2f} USD",
        f"Thù lao Điều 13 đánh giá:        {res.article_13_assessed_award_usd:,.2f} USD",
        f"Chi phí định mức SCOPIC (gốc):   {res.scopic_costs_usd:,.2f} USD",
        f"Thưởng SCOPIC (+25%):            {res.scopic_bonus_uplift_usd:,.2f} USD",
        f"Tổng định mức SCOPIC:            {res.total_scopic_remuneration_usd:,.2f} USD",
        f"Khấu trừ giảm thưởng (25% penalty): {res.article_13_discount_penalty_usd:,.2f} USD",
        f"THÙ LAO BÊN CỨU HỘ ĐƯỢC NHẬN:    {res.final_salvor_remuneration_usd:,.2f} USD",
        f"- Bảo hiểm tài sản (H&M/Cargo):  {res.property_underwriters_liability_usd:,.2f} USD",
        f"- Trách nhiệm Hội P&I:           {res.pni_club_liability_usd:,.2f} USD",
        f"Kết luận:                        {res.settlement_summary}",
    ])


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
    claims = [
        SeafarerAbandonmentClaim(f"Thuyền viên #{i}", "Thủy thủ / Sĩ quan", "Việt Nam", avg_wage, unpaid_months, avg_wage * unpaid_months, "Việt Nam", 1200.0, 20)
        for i in range(1, crew_count + 1)
    ]
    res = SeafarerAbandonmentEngine.adjudicate_abandonment(vessel, imo, insurer, AbandonmentTrigger(trigger), claims)
    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return
    _echo_box(f"THẨM ĐỊNH BẢO ĐẢM TÀI CHÍNH THUYỀN VIÊN (MLC 2006) — {res.vessel_name}", [
        f"Số IMO:                       {res.imo_number}",
        f"Tổ chức cấp bảo lãnh:         {res.guarantor_pni_insurer}",
        f"Số thuyền viên bảo hộ:        {res.total_seafarers_stranded} người",
        f"Tổng lương nợ yêu cầu:        {res.total_gross_wages_claimed_usd:,.2f} USD",
        f"Lương chốt trần (tối đa 4m):  {res.total_statutory_capped_wages_usd:,.2f} USD",
        f"Chi phí vé máy bay hồi hương: {res.total_repatriation_transit_costs_usd:,.2f} USD",
        f"Trợ cấp sinh hoạt phí khẩn cấp:{res.total_subsistence_allowance_usd:,.2f} USD",
        f"TỔNG CHI TRẢ BẢO ĐÃM:         {res.total_guarantee_payout_usd:,.2f} USD",
        f"Quyền truy đòi chủ tàu:       {res.shipowner_recourse_claim_usd:,.2f} USD",
        f"Phán quyết:                   {res.adjudication_verdict}",
    ])


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
    res = GreenHarborCraftEngine.evaluate_transition(craft, bp, HarborCraftPropulsion(tech), hours, capex_premium, port_dues)
    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return
    _echo_box(f"ĐÁNH GIÁ CHUYỂN ĐỔI XANH PHƯƠNG TIỆN CẢNG BIỂN — {res.craft_name}", [
        f"Công nghệ động lực:           {res.propulsion}",
        f"Sức kéo cột bích (Bollard Pull): {res.bollard_pull_tonnes:.1f} T",
        f"Phát thải cơ sở MGO:          {res.baseline_mgo_co2_tonnes_per_year:,.1f} tấn CO2/năm",
        f"Lượng CO2 cắt giảm:           {res.abated_co2_tonnes_per_year:,.1f} tấn ({res.abatement_ratio_pct:.1f}%)",
        f"Tiết kiệm chi phí nhiên liệu: {res.annual_fuel_cost_savings_usd:,.2f} USD/năm",
        f"Ưu đãi giảm phí cảng biển:    {res.annual_green_tariff_rebate_usd:,.2f} USD/năm",
        f"Tổng lợi ích kinh tế hàng năm:{res.annual_total_economic_benefit_usd:,.2f} USD/năm",
        f"Chi phí đầu tư xanh (CAPEX):  {res.capex_green_premium_usd:,.2f} USD",
        f"Thời gian hoàn vốn (PBP):     {res.simple_payback_years:.1f} năm",
        f"Phù hợp Quyết định 876:       {'ĐẠT' if res.statutory_incentive_compliance else 'CHƯA ĐẠT'}",
        f"Đánh giá:                     {res.remarks}",
    ])
