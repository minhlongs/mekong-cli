# -*- coding: utf-8 -*-
"""Typer CLI Subcommands for Phases 263-266.

Commands:
- loi: Letter of Indemnity (LOI) & Switch B/L Risk Management Under VMC 2015 & IG P&I
- ga: General Average (GA) Adjustment Under VMC 2015 & York-Antwerp Rules 2016
- bunker: Bunker Delivery Note (BDN) & MARPOL Annex VI Fuel Sulfur Compliance
- demurrage: Seaport Container Demurrage & Detention Progressive Tariff Engine
"""

from __future__ import annotations

import json
import typer

from src.core.maritime_loi_ga_bunker_demurrage_engine import (
    LOIType,
    BankGuaranteeStatus,
    LOIEvaluationInput,
    LOIRiskEngine,
    GASacrificeExpenditure,
    ContributoryValues,
    GeneralAverageEngine,
    FuelGrade,
    EmissionControlArea,
    BunkerDeliveryData,
    BunkerMARPOLComplianceEngine,
    ContainerType,
    FreeTimePolicy,
    DemurrageDetentionEngine,
)

loi_app = typer.Typer(
    name="loi",
    help="Phase 263: Letter of Indemnity (LOI) & Switch B/L Risk Evaluation Under VMC 2015",
    no_args_is_help=True,
)

ga_app = typer.Typer(
    name="ga",
    help="Phase 264: General Average (GA) Adjustment Calculator Under York-Antwerp Rules 2016",
    no_args_is_help=True,
)

bunker_app = typer.Typer(
    name="bunker",
    help="Phase 265: Bunker Delivery Note (BDN) & MARPOL Annex VI Fuel Sulfur Compliance",
    no_args_is_help=True,
)

demurrage_app = typer.Typer(
    name="demurrage",
    help="Phase 266: Seaport Container Demurrage & Detention (D&D) Progressive Tariff Engine",
    no_args_is_help=True,
)


# ==============================================================================
# PHASE 263: LETTER OF INDEMNITY (LOI)
# ==============================================================================

@loi_app.command(name="evaluate")
def cmd_loi_evaluate(
    vessel: str = typer.Option("MV_PACIFIC_VOYAGER", "--vessel", "-v", help="Tên tàu"),
    voyage: str = typer.Option("VOY-2026-01", "--voyage", help="Số chuyến hành trình"),
    loi_type: str = typer.Option("delivery_without_original_bl", "--type", help="Loại LOI (delivery_without_original_bl, change_of_discharge_port, split_bl, clean_bl_against_defects)"),
    cif_value: float = typer.Option(1500000.0, "--cif", help="Giá trị CIF hàng hóa (USD)"),
    multiplier: float = typer.Option(2.0, "--multiplier", help="Hệ số bảo lãnh yêu cầu (Chuẩn 200% = 2.0)"),
    bank_status: str = typer.Option("first_class_international_bank", "--bank", help="Phân hạng ngân hàng (first_class_international_bank, local_commercial_bank, unsecured_corporate_only, no_bank_join)"),
    charterer: str = typer.Option("GLOBAL_TRADING_LTD", "--charterer", help="Tên người thuê tàu/người phát hành"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Thẩm định an toàn pháp lý của Thư cam kết bồi thường (LOI) và rủi ro P&I."""
    inp = LOIEvaluationInput(
        vessel_name=vessel,
        voyage_number=voyage,
        loi_type=LOIType(loi_type),
        cargo_cif_value_usd=cif_value,
        requested_indemnity_multiplier=multiplier,
        bank_status=BankGuaranteeStatus(bank_status),
        charterer_name=charterer,
    )

    res = LOIRiskEngine.evaluate_loi(inp)

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"THẨM ĐỊNH RỦI RO THƯ CAM KẾT BỒI THƯỜNG (LOI) — {res.vessel_name}")
    typer.echo("=" * 70)
    typer.echo(f"Loại nghiệp vụ:               {res.loi_type}")
    typer.echo(f"Giá trị CIF hàng hóa:         ${res.cargo_cif_value_usd:,.2f} USD")
    typer.echo(f"Mức bảo lãnh khuyến nghị:     ${res.recommended_guarantee_amount_usd:,.2f} USD")
    typer.echo(f"Mức bảo đảm thực tế:          ${res.provided_guarantee_amount_usd:,.2f} USD")
    typer.echo(f"Tỷ lệ bảo đảm:                {res.guarantee_adequacy_ratio*100:.1f}%")
    typer.echo(f"Rủi ro mất bảo hiểm P&I:      {'CÓ (BỊ LOẠI TRỪ BẢO HIỂM)' if res.is_pi_club_cover_prejudiced else 'KHÔNG'}")
    typer.echo(f"Cấp độ rủi ro:                {res.risk_level}")
    typer.echo(f"Tính khả thi pháp lý:         {res.enforceability_status}")
    typer.echo(f"Đánh giá thời hiệu:           {res.validity_period_assessment}")
    typer.echo("Khuyến nghị an toàn:")
    for rec in res.recommendations:
        typer.echo(f"  - {rec}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 264: GENERAL AVERAGE (GA) ADJUSTMENT
# ==============================================================================

@ga_app.command(name="adjust")
def cmd_ga_adjust(
    ship_sacrifice: float = typer.Option(250000.0, "--ship-sacrifice", help="Tổn thất thân máy hy sinh cho GA (USD)"),
    cargo_sacrifice: float = typer.Option(400000.0, "--cargo-sacrifice", help="Hàng hóa vứt bỏ hy sinh GA (USD)"),
    salvage_award: float = typer.Option(180000.0, "--salvage", help="Tiền công cứu nạn tính vào GA (USD)"),
    port_refuge: float = typer.Option(120000.0, "--port-refuge", help="Chi phí ghé cảng lánh nạn (USD)"),
    adjuster_fee: float = typer.Option(50000.0, "--adjuster-fee", help="Phí giám định tính toán GA (USD)"),
    ship_sound: float = typer.Option(8000000.0, "--ship-sound", help="Giá trị nguyên vẹn của tàu (USD)"),
    ship_deductions: float = typer.Option(150000.0, "--ship-deduct", help="Chi phí sửa chữa tổn thất riêng của tàu (USD)"),
    cargo_cif: float = typer.Option(12000000.0, "--cargo-cif", help="Tổng giá trị CIF hàng hóa (USD)"),
    cargo_deductions: float = typer.Option(300000.0, "--cargo-deduct", help="Tổn thất riêng của hàng hóa (USD)"),
    freight_at_risk: float = typer.Option(600000.0, "--freight", help="Cước phí chưa thu gặp rủi ro (USD)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán phân bổ tổn thất chung (GA Adjustment) theo York-Antwerp Rules 2016."""
    exp = GASacrificeExpenditure(
        ship_damage_sacrifice_usd=ship_sacrifice,
        cargo_jettison_sacrifice_usd=cargo_sacrifice,
        salvage_award_allowable_usd=salvage_award,
        port_of_refuge_expenses_usd=port_refuge,
        adjuster_fee_and_legal_usd=adjuster_fee,
    )
    cont = ContributoryValues(
        ship_sound_value_usd=ship_sound,
        ship_deductions_usd=ship_deductions,
        cargo_cif_value_usd=cargo_cif,
        cargo_deductions_usd=cargo_deductions,
        freight_at_risk_gross_usd=freight_at_risk,
    )

    res = GeneralAverageEngine.calculate_adjustment(exp, cont)

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo("BẢN PHÂN BỔ TỔN THẤT CHUNG (GA ADJUSTMENT) — YORK-ANTWERP RULES 2016")
    typer.echo("=" * 70)
    typer.echo(f"Tổng chi phí & hy sinh TTC:   ${res.total_ga_allowances_usd:,.2f} USD")
    typer.echo(f"Tổng giá trị chịu phân bổ:    ${res.total_contributory_value_usd:,.2f} USD")
    typer.echo(f"Tỷ lệ đóng góp TTC:           {res.ga_contribution_rate_percentage:.4f}%")
    typer.echo("-" * 70)
    typer.echo(f"Tàu biển (Ship):              Đóng góp ${res.ship_ga_contribution_usd:,.2f} | Số dư ròng: ${res.ship_net_balance_usd:,.2f}")
    typer.echo(f"Hàng hóa (Cargo):             Đóng góp ${res.cargo_ga_contribution_usd:,.2f} | Số dư ròng: ${res.cargo_net_balance_usd:,.2f}")
    typer.echo(f"Cước phí (Freight):           Đóng góp ${res.freight_ga_contribution_usd:,.2f} | Số dư ròng: ${res.freight_net_balance_usd:,.2f}")
    typer.echo("-" * 70)
    typer.echo(f"Tỷ lệ ký quỹ (Cash Deposit):  {res.recommended_cash_deposit_pct:.2f}% CIF")
    typer.echo(f"Căn cứ pháp lý:               {res.legal_statute_reference}")
    typer.echo(f"Ghi chú:                      {res.remarks}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 265: BUNKER DELIVERY NOTE (BDN) & SULFUR COMPLIANCE
# ==============================================================================

@bunker_app.command(name="check")
def cmd_bunker_check(
    bdn_no: str = typer.Option("BDN-2026-8899", "--bdn-no", help="Số chứng từ BDN"),
    fuel: str = typer.Option("vlsfo", "--fuel", help="Loại dầu (vlsfo, ulsfo, hsfo, mgo, biofuel)"),
    qty: float = typer.Option(500.0, "--qty", help="Khối lượng nhận (Tấn - MT)"),
    sulfur: float = typer.Option(0.48, "--sulfur", help="Hàm lượng lưu huỳnh kiểm nghiệm (% m/m)"),
    flash_point: float = typer.Option(68.0, "--flash-point", help="Điểm chớp cháy (°C)"),
    density: float = typer.Option(985.0, "--density", help="Tỷ trọng ở 15°C (kg/m3)"),
    viscosity: float = typer.Option(380.0, "--viscosity", help="Độ nhớt ở 50°C (cSt)"),
    area: str = typer.Option("global_open_sea", "--area", help="Vùng biển hoạt động: global_open_sea, imo_eca_zone, port_internal_waters"),
    has_scrubber: bool = typer.Option(False, "--has-scrubber", help="Có lắp hệ thống Scrubber EGCS"),
    scrubber_ratio: float = typer.Option(0.0, "--scrubber-ratio", help="Tỷ lệ phát thải SO2/CO2 của Scrubber"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Kiểm tra hợp chuẩn lưu huỳnh MARPOL Annex VI trên chứng từ giao nhận BDN."""
    bunker_data = BunkerDeliveryData(
        bdn_number=bdn_no,
        bunkering_date="2026-10-08",
        port_name="HAI_PHONG_PORT",
        fuel_grade=FuelGrade(fuel),
        supplied_quantity_mt=qty,
        density_at_15c_kg_m3=density,
        viscosity_cst=viscosity,
        flash_point_celsius=flash_point,
        tested_sulfur_content_pct=sulfur,
        has_scrubber_installed=has_scrubber,
        scrubber_so2_co2_ratio=scrubber_ratio,
    )

    res = BunkerMARPOLComplianceEngine.evaluate_bunker_sample(
        bunker=bunker_data,
        operational_area=EmissionControlArea(area),
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"KIỂM ĐỊNH HỢP CHUẨN NHIÊN LIỆU MARPOL ANNEX VI — BDN #{res.bdn_number}")
    typer.echo("=" * 70)
    typer.echo(f"Hàm lượng lưu huỳnh đo được: {res.tested_sulfur_content_pct:.2f}% (Giới hạn: {res.applicable_sulfur_limit_pct:.2f}%)")
    typer.echo(f"Tuân thủ lưu huỳnh MARPOL:    {'ĐẠT TIÊU CHUẨN' if res.is_sulfur_compliant else 'VI PHẠM QUY ĐỊNH'}")
    typer.echo(f"An toàn điểm chớp cháy:      {'ĐẠT (>= 60°C)' if res.is_flash_point_safe else 'NGUY HIỂM HỎA HOẠN (< 60°C)'}")
    typer.echo(f"Tính pháp lý chứng từ BDN:    {'HỢP LỆ' if res.is_bdn_legally_valid else 'KHÔNG HỢP LỆ'}")
    typer.echo(f"Rủi ro xử phạt pháp lý:       {res.statutory_sanction_risk}")
    if res.estimated_debunkering_cost_usd > 0:
        typer.echo(f"Chi phí hút bỏ nhiên liệu:   ${res.estimated_debunkering_cost_usd:,.2f} USD")
    typer.echo(f"Thời gian lưu trữ chứng từ:   Lưu BDN tối thiểu {res.marpol_record_retention_years} năm; mẫu niêm phong {res.sample_retention_months} tháng")
    typer.echo(f"Tổng kết:                     {res.compliance_summary}")
    typer.echo("=" * 70)


# ==============================================================================
# PHASE 266: CONTAINER DEMURRAGE & DETENTION (D&D)
# ==============================================================================

@demurrage_app.command(name="calculate")
def cmd_demurrage_calculate(
    container_id: str = typer.Option("TEMU-8821941", "--container-id", help="Số hiệu container"),
    cntr_type: str = typer.Option("dry_20ft", "--type", help="Chủng loại (dry_20ft, dry_40ft, reefer_20ft, reefer_40ft, special_ot_fr)"),
    dwell_days: int = typer.Option(14, "--dwell-days", help="Tổng số ngày lưu bãi và giữ vỏ"),
    free_terminal: int = typer.Option(5, "--free-terminal", help="Số ngày miễn phí bãi cảng (Demurrage free time)"),
    free_equipment: int = typer.Option(7, "--free-equipment", help="Số ngày miễn phí vỏ hãng tàu (Detention free time)"),
    cargo_value: float = typer.Option(180000000.0, "--cargo-value", help="Trị giá lô hàng (VND)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
):
    """Tính toán cước phạt lưu bãi cảng (Demurrage) và lưu vỏ hãng tàu (Detention) lũy tiến."""
    policy = FreeTimePolicy(
        terminal_free_days=free_terminal,
        carrier_equipment_free_days=free_equipment,
    )

    res = DemurrageDetentionEngine.calculate_charges(
        container_id=container_id,
        container_type=ContainerType(cntr_type),
        total_dwell_days=dwell_days,
        policy=policy,
        cargo_value_vnd=cargo_value,
    )

    if json_output:
        typer.echo(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        return

    typer.echo("=" * 70)
    typer.echo(f"QUYẾT TOÁN CƯỚC LƯU BÃI & LƯU VỎ CONTAINER — {res.container_id}")
    typer.echo("=" * 70)
    typer.echo(f"Chủng loại container:         {res.container_type.upper()}")
    typer.echo(f"Tổng số ngày lưu bãi:         {res.total_dwell_days} ngày")
    typer.echo(f"Số ngày quá hạn bãi cảng:     {res.terminal_demurrage_days} ngày")
    typer.echo(f"Tiền phạt lưu bãi (Demurrage):{res.terminal_demurrage_fee_vnd:,.0f} VND")
    typer.echo(f"Số ngày quá hạn vỏ hãng tàu:  {res.carrier_detention_days} ngày")
    typer.echo(f"Tiền phạt lưu vỏ (Detention): {res.carrier_detention_fee_vnd:,.0f} VND")
    typer.echo(f"TỔNG CƯỚC PHẠT D&D:           {res.total_dd_charges_vnd:,.0f} VND")
    typer.echo(f"Trị giá hàng hóa:             {res.cargo_value_vnd:,.0f} VND")
    typer.echo(f"Cảnh báo cầm giữ hàng (Lien): {'CẢNH BÁO: PHÍ VƯỢT QUÁ 70% GIÁ TRỊ HÀNG (ĐIỀU 168 BỘ LUẬT HÀNG HẢI)' if res.is_maritime_lien_warning else 'BÌNH THƯỜNG'}")
    typer.echo(f"Tổng kết:                     {res.cost_status_summary}")
    typer.echo("=" * 70)
