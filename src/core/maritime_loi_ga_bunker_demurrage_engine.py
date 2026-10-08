# -*- coding: utf-8 -*-
"""Maritime Commercial & Operational Risk Engine (Phases 263-266).

Statutory & Convention Bases:
- Phase 263: Letter of Indemnity (LOI) & Switch B/L Risk Management (VMC 2015 Arts. 154, 160, 163; IG P&I Club Standards)
- Phase 264: General Average (GA) Adjustment & York-Antwerp Rules 2016 (VMC 2015 Arts. 290-302; YAR 2016 Rules A-G, VI, X, XI, XX, XXI)
- Phase 265: Bunker Delivery Note (BDN) & MARPOL Annex VI Fuel Sulfur Compliance (MARPOL Regs. 14, 18; Circular 41/2020; Circular 39/2023)
- Phase 266: Seaport Container Demurrage & Detention (D&D) progressive tariffs (VMC 2015 Arts. 168, 172; Decree 160/2016; Circular 39/2023)

Zero-Dependency Architecture: Uses ONLY Python standard library modules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import math
from typing import Any, Dict, List, Optional


# ==============================================================================
# PHASE 263: LETTER OF INDEMNITY (LOI) & SWITCH B/L RISK ENGINE
# ==============================================================================

class LOIType(str, Enum):
    """Phân loại nghiệp vụ Thư cam kết bồi thường (LOI)."""
    DELIVERY_WITHOUT_ORIGINAL_BL = "delivery_without_original_bl"
    CHANGE_OF_DISCHARGE_PORT = "change_of_discharge_port"
    SPLIT_BL = "split_bl"
    CLEAN_BL_AGAINST_DEFECTS = "clean_bl_against_defects"


class BankGuaranteeStatus(str, Enum):
    """Mức độ bảo lãnh thanh toán của Ngân hàng thương mại."""
    FIRST_CLASS_INTERNATIONAL_BANK = "first_class_international_bank"  # Hạng 1 thế giới
    LOCAL_COMMERCIAL_BANK = "local_commercial_bank"                    # Ngân hàng TM trong nước
    UNSECURED_CORPORATE_ONLY = "unsecured_corporate_only"              # Chỉ có cam kết của Charterer/Trader
    NO_BANK_JOIN = "no_bank_join"                                      # Không có ngân hàng cùng ký


@dataclass
class LOIEvaluationInput:
    """Tham số đầu vào thẩm định rủi ro phát hành/chấp nhận LOI."""
    vessel_name: str
    voyage_number: str
    loi_type: LOIType
    cargo_cif_value_usd: float
    requested_indemnity_multiplier: float = 2.0  # Chuẩn thông lệ P&I: 200% giá trị CIF
    bank_status: BankGuaranteeStatus = BankGuaranteeStatus.FIRST_CLASS_INTERNATIONAL_BANK
    charterer_name: str = "CHARTERER_CORP"
    receiver_name: str = "NOTIFIED_RECEIVER"
    is_charterer_investment_grade: bool = True
    days_since_discharge: int = 0
    statute_of_limitations_years: int = 6  # Chuẩn luật Anh 6 năm (hợp đồng thông thường)


@dataclass
class LOIRiskAssessment:
    """Kết quả thẩm định an toàn pháp lý của Thư bảo lãnh LOI."""
    vessel_name: str
    loi_type: str
    cargo_cif_value_usd: float
    recommended_guarantee_amount_usd: float
    provided_guarantee_amount_usd: float
    guarantee_adequacy_ratio: float
    is_pi_club_cover_prejudiced: bool
    risk_level: str
    validity_period_assessment: str
    enforceability_status: str
    recommendations: List[str]
    compliance_remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LOIRiskEngine:
    """Động cơ phân tích rủi ro chấp nhận Thư bồi thường LOI và Switch B/L."""

    @staticmethod
    def evaluate_loi(input_data: LOIEvaluationInput) -> LOIRiskAssessment:
        req_mult = max(1.0, input_data.requested_indemnity_multiplier)
        rec_guarantee = input_data.cargo_cif_value_usd * req_mult

        # Mức bảo lãnh thực tế dựa trên cấp độ ngân hàng
        if input_data.bank_status == BankGuaranteeStatus.FIRST_CLASS_INTERNATIONAL_BANK:
            bank_discount = 1.0
        elif input_data.bank_status == BankGuaranteeStatus.LOCAL_COMMERCIAL_BANK:
            bank_discount = 0.85
        elif input_data.bank_status == BankGuaranteeStatus.UNSECURED_CORPORATE_ONLY:
            bank_discount = 0.40 if input_data.is_charterer_investment_grade else 0.15
        else:
            bank_discount = 0.0

        effective_coverage = rec_guarantee * bank_discount
        adequacy_ratio = round(effective_coverage / rec_guarantee, 4) if rec_guarantee > 0 else 0.0

        # Rủi ro P&I Club: Giao hàng không xuất trình Vận đơn gốc (B/L) làm mất bảo hiểm P&I tự động
        is_pi_prejudiced = input_data.loi_type in [
            LOIType.DELIVERY_WITHOUT_ORIGINAL_BL,
            LOIType.CLEAN_BL_AGAINST_DEFECTS
        ]

        recommendations = []
        if is_pi_prejudiced:
            recommendations.append(
                "CẢNH BÁO: Rủi ro loại trừ bảo hiểm P&I tự động. Bắt buộc Ngân hàng Hạng 1 cùng ký bảo lãnh vô điều kiện."
            )

        if input_data.bank_status in [BankGuaranteeStatus.UNSECURED_CORPORATE_ONLY, BankGuaranteeStatus.NO_BANK_JOIN]:
            recommendations.append(
                "TỪ CHỐI THỰC HIỆN: LOI không có Ngân hàng đồng ký tạo rủi ro tài chính trực tiếp cho Chủ tàu khi có tranh chấp giao nhầm hàng."
            )

        if input_data.loi_type == LOIType.CLEAN_BL_AGAINST_DEFECTS:
            recommendations.append(
                "VI PHẠM BẤT HỢP PHÁP: Phát hành vận đơn sạch trái với tình trạng hàng thực tế bị coi là hành vi gian lận (The Brown Jenkinson) và vô hiệu tại tòa án."
            )

        if input_data.statute_of_limitations_years >= 6:
            validity_eval = "Thời hiệu yêu cầu bồi thường theo luật Anh là 6 năm; cần duy trì bảo lãnh ngân hàng vô thời hạn cho đến khi thu hồi đủ bộ B/L gốc."
        else:
            validity_eval = f"Thời hiệu cam kết {input_data.statute_of_limitations_years} năm; rủi ro bên thứ ba xuất trình B/L gốc trễ hạn."

        # Phân loại mức rủi ro tổng thể
        if input_data.loi_type == LOIType.CLEAN_BL_AGAINST_DEFECTS:
            risk_level = "CRITICAL_FRAUDULENT"
            enforceability = "VÔ HIỆU DO GIAN LẬN THƯƠNG MẠI"
        elif adequacy_ratio >= 0.95 and not is_pi_prejudiced:
            risk_level = "LOW_SAFE"
            enforceability = "HIỆU LỰC TOÀN PHẦN — BẢO ĐẢM NGÂN HÀNG HẠNG 1"
        elif adequacy_ratio >= 0.80:
            risk_level = "MEDIUM_ACCEPTABLE"
            enforceability = "HIỆU LỰC CÓ ĐIỀU KIỆN KÈM BẢO LÃNH NGÂN HÀNG"
        elif adequacy_ratio >= 0.40:
            risk_level = "HIGH_UNSECURED"
            enforceability = "RỦI RO CAO — THIẾU BẢO ĐẢM TÀI CHÍNH ĐỘC LẬP"
        else:
            risk_level = "CRITICAL_UNACCEPTABLE"
            enforceability = "BẤT KHẢ THI / RỦI RO PHÁ SẢN CAO"

        remarks = (
            f"Thẩm định LOI {input_data.loi_type.value}: Mức bảo lãnh yêu cầu ${rec_guarantee:,.2f} USD "
            f"({req_mult*100:.0f}% CIF). Tỷ lệ bảo đảm: {adequacy_ratio*100:.1f}%. "
            f"Tình trạng P&I: {'MẤT BẢO HIỂM P&I' if is_pi_prejudiced else 'ĐƯỢC BẢO LƯU'}."
        )

        return LOIRiskAssessment(
            vessel_name=input_data.vessel_name,
            loi_type=input_data.loi_type.value,
            cargo_cif_value_usd=input_data.cargo_cif_value_usd,
            recommended_guarantee_amount_usd=round(rec_guarantee, 2),
            provided_guarantee_amount_usd=round(effective_coverage, 2),
            guarantee_adequacy_ratio=adequacy_ratio,
            is_pi_club_cover_prejudiced=is_pi_prejudiced,
            risk_level=risk_level,
            validity_period_assessment=validity_eval,
            enforceability_status=enforceability,
            recommendations=recommendations,
            compliance_remarks=remarks,
        )


# ==============================================================================
# PHASE 264: GENERAL AVERAGE (GA) & YORK-ANTWERP RULES 2016 ENGINE
# ==============================================================================

@dataclass
class GASacrificeExpenditure:
    """Chi phí hy sinh và tổn thất thuộc phạm vi tổn thất chung (Rule A, C, VI, X, XI)."""
    ship_damage_sacrifice_usd: float = 0.0      # Hư hại thân máy do cố ý cứu nạn (Rule VII, XIV)
    cargo_jettison_sacrifice_usd: float = 0.0   # Hàng hóa vứt xuống biển (Rule I, II)
    salvage_award_allowable_usd: float = 0.0    # Tiền công cứu nạn được tính vào GA (Rule VI)
    port_of_refuge_expenses_usd: float = 0.0    # Chi phí ghé cảng lánh nạn (Rule X, XI)
    fuel_stores_consumed_usd: float = 0.0       # Nhiên liệu, vật tư tiêu hao trong cứu nạn
    adjuster_fee_and_legal_usd: float = 0.0     # Chi phí giám định và phân bổ GA
    commission_2pct_allowable_usd: float = 0.0  # Hoa hồng chi tiền 2% (Rule XX)
    interest_allowable_usd: float = 0.0         # Tiền lãi phát sinh (Rule XXI)


@dataclass
class ContributoryValues:
    """Giá trị chịu phân bổ tổn thất chung (Contributory Values - Rule XVII)."""
    ship_sound_value_usd: float
    ship_deductions_usd: float = 0.0                  # Chi phí sửa chữa không thuộc GA
    cargo_cif_value_usd: float = 0.0
    cargo_deductions_usd: float = 0.0                 # Tổn thất riêng của hàng
    freight_at_risk_gross_usd: float = 0.0            # Cước phí chưa thu phụ thuộc chuyến đi
    freight_contingent_expenses_usd: float = 0.0      # Chi phí để thu cước


@dataclass
class GeneralAverageAdjustmentResult:
    """Bản phân bổ tổn thất chung chính thức theo York-Antwerp Rules 2016."""
    total_ga_allowances_usd: float
    net_ship_contributory_value_usd: float
    net_cargo_contributory_value_usd: float
    net_freight_contributory_value_usd: float
    total_contributory_value_usd: float
    ga_contribution_rate_percentage: float
    ship_ga_contribution_usd: float
    cargo_ga_contribution_usd: float
    freight_ga_contribution_usd: float
    ship_net_balance_usd: float                  # Dương: được nhận về; Âm: phải nộp thêm
    cargo_net_balance_usd: float
    freight_net_balance_usd: float
    recommended_cash_deposit_pct: float
    legal_statute_reference: str
    remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GeneralAverageEngine:
    """Động cơ tính toán phân bổ Tổn thất chung (GA Adjustment)."""

    @staticmethod
    def calculate_adjustment(
        expenditure: GASacrificeExpenditure,
        contributory: ContributoryValues,
        include_rule_xx_commission: bool = True,
        interest_rate_p_a: float = 0.07,  # Chuẩn YAR 2016: SOFR/LIBOR + 4% ~ 7%
        duration_years: float = 1.0,
    ) -> GeneralAverageAdjustmentResult:
        # 1. Tính tổng chi phí và hy sinh tổn thất chung
        base_expenditures = (
            expenditure.ship_damage_sacrifice_usd +
            expenditure.cargo_jettison_sacrifice_usd +
            expenditure.salvage_award_allowable_usd +
            expenditure.port_of_refuge_expenses_usd +
            expenditure.fuel_stores_consumed_usd +
            expenditure.adjuster_fee_and_legal_usd
        )

        commission = (base_expenditures * 0.02) if include_rule_xx_commission else 0.0
        interest = (base_expenditures + commission) * interest_rate_p_a * duration_years

        total_ga_allowances = base_expenditures + commission + interest

        # 2. Tính giá trị chịu phân bổ ròng (Net Contributory Values)
        net_ship = max(0.0, contributory.ship_sound_value_usd - contributory.ship_deductions_usd + expenditure.ship_damage_sacrifice_usd)
        net_cargo = max(0.0, contributory.cargo_cif_value_usd - contributory.cargo_deductions_usd + expenditure.cargo_jettison_sacrifice_usd)
        net_freight = max(0.0, contributory.freight_at_risk_gross_usd - contributory.freight_contingent_expenses_usd)

        total_contributory = net_ship + net_cargo + net_freight
        if total_contributory <= 0.0:
            raise ValueError("Tổng giá trị chịu phân bổ (Total contributory value) phải lớn hơn 0")

        # 3. Tỷ lệ đóng góp tổn thất chung (GA Rate)
        ga_rate = total_ga_allowances / total_contributory

        ship_contribution = net_ship * ga_rate
        cargo_contribution = net_cargo * ga_rate
        freight_contribution = net_freight * ga_rate

        # 4. Quyết toán số dư ròng (Net Balance: Đã hy sinh trừ đi Trách nhiệm đóng góp)
        ship_sacrifice = expenditure.ship_damage_sacrifice_usd + expenditure.fuel_stores_consumed_usd + expenditure.port_of_refuge_expenses_usd
        cargo_sacrifice = expenditure.cargo_jettison_sacrifice_usd
        freight_sacrifice = 0.0

        ship_net_balance = round(ship_sacrifice - ship_contribution, 2)
        cargo_net_balance = round(cargo_sacrifice - cargo_contribution, 2)
        freight_net_balance = round(freight_sacrifice - freight_contribution, 2)

        # Đề xuất tỷ lệ ký quỹ tiền mặt (Cash Deposit) kèm biên an toàn 20%
        rec_cash_deposit_pct = round(min(100.0, (ga_rate * 1.20) * 100), 2)

        remarks = (
            f"Tổng giá trị TTC: ${total_ga_allowances:,.2f} USD. "
            f"Tổng giá trị chịu phân bổ: ${total_contributory:,.2f} USD. "
            f"Tỷ lệ đóng góp TTC: {ga_rate*100:.3f}%. "
            f"Tỷ lệ ký quỹ (Cash Deposit) khuyến nghị: {rec_cash_deposit_pct}% CIF."
        )

        return GeneralAverageAdjustmentResult(
            total_ga_allowances_usd=round(total_ga_allowances, 2),
            net_ship_contributory_value_usd=round(net_ship, 2),
            net_cargo_contributory_value_usd=round(net_cargo, 2),
            net_freight_contributory_value_usd=round(net_freight, 2),
            total_contributory_value_usd=round(total_contributory, 2),
            ga_contribution_rate_percentage=round(ga_rate * 100, 4),
            ship_ga_contribution_usd=round(ship_contribution, 2),
            cargo_ga_contribution_usd=round(cargo_contribution, 2),
            freight_ga_contribution_usd=round(freight_contribution, 2),
            ship_net_balance_usd=ship_net_balance,
            cargo_net_balance_usd=cargo_net_balance,
            freight_net_balance_usd=freight_net_balance,
            recommended_cash_deposit_pct=rec_cash_deposit_pct,
            legal_statute_reference="Bộ luật Hàng hải VN 2015 Điều 290-302 & York-Antwerp Rules 2016",
            remarks=remarks,
        )


# ==============================================================================
# PHASE 265: BUNKER DELIVERY NOTE (BDN) & MARPOL ANNEX VI FUEL SULFUR ENGINE
# ==============================================================================

class FuelGrade(str, Enum):
    """Phân loại cấp độ nhiên liệu hàng hải theo hàm lượng lưu huỳnh."""
    VLSFO = "vlsfo"      # Very Low Sulfur Fuel Oil (<= 0.50% m/m)
    ULSFO = "ulsfo"      # Ultra Low Sulfur Fuel Oil (<= 0.10% m/m)
    HSFO = "hsfo"        # High Sulfur Fuel Oil (> 0.50% m/m, yêu cầu Scrubber EGCS)
    MGO = "mgo"          # Marine Gas Oil (<= 0.10% m/m)
    BIOFUEL = "biofuel"  # B30/B100 Bio-marine Fuel (<= 0.05% m/m)


class EmissionControlArea(str, Enum):
    """Khu vực kiểm soát khí thải hàng hải (ECA)."""
    GLOBAL_OPEN_SEA = "global_open_sea"          # Biển quốc tế: tối đa 0.50% S
    IMO_ECA_ZONE = "imo_eca_zone"                # Vùng ECA (Bắc Hải, Baltic, Bắc Mỹ): tối đa 0.10% S
    PORT_INTERNAL_WATERS = "port_internal_waters"  # Vùng nước cảng biển Việt Nam: tối đa 0.10% S


@dataclass
class BunkerDeliveryData:
    """Dữ liệu trên Chứng từ giao nhận nhiên liệu (Bunker Delivery Note - BDN)."""
    bdn_number: str
    bunkering_date: str
    port_name: str
    fuel_grade: FuelGrade
    supplied_quantity_mt: float
    density_at_15c_kg_m3: float
    viscosity_cst: float
    flash_point_celsius: float
    tested_sulfur_content_pct: float
    has_marpol_sample_sealed: bool = True
    has_scrubber_installed: bool = False
    scrubber_so2_co2_ratio: float = 0.0          # Tiêu chuẩn: <= 21.7 (0.50% S) hoặc <= 4.3 (0.10% S)


@dataclass
class BunkerComplianceAssessment:
    """Kết quả kiểm định hợp chuẩn nhiên liệu hàng hải và phát thải MARPOL."""
    bdn_number: str
    is_sulfur_compliant: bool
    is_flash_point_safe: bool
    is_bdn_legally_valid: bool
    applicable_sulfur_limit_pct: float
    tested_sulfur_content_pct: float
    scrubber_equivalence_accepted: bool
    statutory_sanction_risk: str
    estimated_debunkering_cost_usd: float
    fonar_defense_eligible: bool
    marpol_record_retention_years: int
    sample_retention_months: int
    compliance_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BunkerMARPOLComplianceEngine:
    """Động cơ kiểm định tuân thủ MARPOL Annex VI và hồ sơ tiếp nhận nhiên liệu."""

    @staticmethod
    def evaluate_bunker_sample(
        bunker: BunkerDeliveryData,
        operational_area: EmissionControlArea = EmissionControlArea.GLOBAL_OPEN_SEA,
        reference_mgo_price_mt_usd: float = 850.0,
    ) -> BunkerComplianceAssessment:
        # Xác định trần lưu huỳnh theo vùng biển
        if operational_area == EmissionControlArea.GLOBAL_OPEN_SEA:
            sulfur_limit = 0.50
            scrubber_ratio_cap = 21.7
        else:
            sulfur_limit = 0.10
            scrubber_ratio_cap = 4.3

        # Kiểm tra tính an toàn điểm chớp cháy (SOLAS Ch. II-2: tối thiểu 60°C)
        is_flash_safe = bunker.flash_point_celsius >= 60.0

        # Kiểm tra lưu huỳnh trực tiếp hoặc qua thiết bị làm sạch khí thải (Scrubber EGCS)
        direct_compliant = bunker.tested_sulfur_content_pct <= sulfur_limit
        scrubber_accepted = False

        if not direct_compliant and bunker.has_scrubber_installed:
            if bunker.scrubber_so2_co2_ratio <= scrubber_ratio_cap:
                scrubber_accepted = True

        is_sulfur_compliant = direct_compliant or scrubber_accepted

        # Tính toán chi phí hút bỏ nhiên liệu (De-bunkering) nếu vi phạm
        if not is_flash_safe:
            est_debunker_cost = bunker.supplied_quantity_mt * 250.0
            sanction_risk = "NGUY CƠ HỎA HOẠN — VI PHẠM SOLAS VỀ ĐIỂM CHỚP CHÁY NHIÊN LIỆU (< 60°C)"
            fonar_eligible = False
        elif not is_sulfur_compliant:
            # Chi phí hút dầu, xử lý chất thải độc hại và cấp lại dầu mới
            debunkering_fee_per_mt = 250.0
            replacement_loss = max(0.0, reference_mgo_price_mt_usd - 500.0)
            est_debunker_cost = bunker.supplied_quantity_mt * (debunkering_fee_per_mt + replacement_loss)
            sanction_risk = "NGHIÊM TRỌNG — NGUY CƠ BỊ CẢNG VỤ LƯU GIỮ TÀU VÀ XỬ PHẠT HÀNH CHÍNH THEO NGHỊ ĐỊNH 142/2017"
            fonar_eligible = False  # Nếu đã nhận dầu tại cảng có sẵn MGO thì không được nại cớ FONAR
        else:
            est_debunker_cost = 0.0
            sanction_risk = "AN TOÀN — HỢP CHUẨN ĐẦY ĐỦ"
            fonar_eligible = False

        is_bdn_valid = (
            bunker.has_marpol_sample_sealed and
            is_flash_safe and
            bunker.supplied_quantity_mt > 0.0 and
            bunker.density_at_15c_kg_m3 > 0.0
        )

        summary = (
            f"BDN #{bunker.bdn_number} ({bunker.fuel_grade.value.upper()}): "
            f"Lưu huỳnh đo được: {bunker.tested_sulfur_content_pct:.2f}% (Trần: {sulfur_limit:.2f}%). "
            f"Hợp chuẩn: {'ĐẠT' if is_sulfur_compliant else 'KHÔNG ĐẠT'}. "
            f"Điểm chớp cháy: {bunker.flash_point_celsius:.1f}°C ({'ĐẠT' if is_flash_safe else 'NGUY HIỂM'})."
        )

        return BunkerComplianceAssessment(
            bdn_number=bunker.bdn_number,
            is_sulfur_compliant=is_sulfur_compliant,
            is_flash_point_safe=is_flash_safe,
            is_bdn_legally_valid=is_bdn_valid,
            applicable_sulfur_limit_pct=sulfur_limit,
            tested_sulfur_content_pct=bunker.tested_sulfur_content_pct,
            scrubber_equivalence_accepted=scrubber_accepted,
            statutory_sanction_risk=sanction_risk,
            estimated_debunkering_cost_usd=round(est_debunker_cost, 2),
            fonar_defense_eligible=fonar_eligible,
            marpol_record_retention_years=3,  # MARPOL Reg. 18.6: Lưu BDN tối thiểu 3 năm
            sample_retention_months=12,       # MARPOL Reg. 18.8: Mẫu đại diện lưu tối thiểu 12 tháng
            compliance_summary=summary,
        )


# ==============================================================================
# PHASE 266: SEAPORT CONTAINER DEMURRAGE & DETENTION PROGRESSIVE TARIFF ENGINE
# ==============================================================================

class ContainerType(str, Enum):
    """Chủng loại vỏ container và tính chất lưu bãi/thiết bị."""
    DRY_20FT = "dry_20ft"
    DRY_40FT = "dry_40ft"
    REEFER_20FT = "reefer_20ft"
    REEFER_40FT = "reefer_40ft"
    SPECIAL_OT_FR = "special_ot_fr"  # Open Top / Flat Rack


@dataclass
class FreeTimePolicy:
    """Chính sách thời gian miễn phí lưu bãi cảng và lưu vỏ container (Free Time)."""
    terminal_free_days: int = 5       # Miễn phí lưu bãi cảng (Demurrage)
    carrier_equipment_free_days: int = 7  # Miễn phí lưu vỏ hãng tàu (Detention)
    combined_free_days: Optional[int] = None


@dataclass
class DailyProgressiveTariff:
    """Biểu cước lũy tiến theo số ngày lưu vượt hạn (Tiered Progressive)."""
    tier1_rate_vnd: float             # Ngày 1 - 5 vượt hạn
    tier2_rate_vnd: float             # Ngày 6 - 10 vượt hạn (thường tăng 150%)
    tier3_rate_vnd: float             # Từ ngày 11 trở đi (thường tăng 200%)


@dataclass
class DemurrageDetentionResult:
    """Quyết toán tiền phạt lưu bãi cảng (Demurrage) và lưu vỏ thiết bị (Detention)."""
    container_id: str
    container_type: str
    total_dwell_days: int
    terminal_demurrage_days: int
    terminal_demurrage_fee_vnd: float
    carrier_detention_days: int
    carrier_detention_fee_vnd: float
    total_dd_charges_vnd: float
    cargo_value_vnd: float
    is_maritime_lien_warning: bool    # Cảnh báo thực hiện quyền lưu giữ hàng (VMC Điều 168)
    cost_status_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DemurrageDetentionEngine:
    """Động cơ tính toán cước lưu bãi (Demurrage) và lưu vỏ (Detention) lũy tiến."""

    # Biểu phí lưu bãi tham chiếu chuẩn cảng biển VN (Thông tư 39/2023)
    DEMURRAGE_RATES = {
        ContainerType.DRY_20FT: DailyProgressiveTariff(45000.0, 75000.0, 110000.0),
        ContainerType.DRY_40FT: DailyProgressiveTariff(75000.0, 125000.0, 190000.0),
        ContainerType.REEFER_20FT: DailyProgressiveTariff(95000.0, 160000.0, 240000.0),
        ContainerType.REEFER_40FT: DailyProgressiveTariff(155000.0, 260000.0, 390000.0),
        ContainerType.SPECIAL_OT_FR: DailyProgressiveTariff(120000.0, 200000.0, 300000.0),
    }

    # Biểu phí lưu vỏ tham chiếu hãng tàu quốc tế (VND quy đổi)
    DETENTION_RATES = {
        ContainerType.DRY_20FT: DailyProgressiveTariff(250000.0, 380000.0, 550000.0),
        ContainerType.DRY_40FT: DailyProgressiveTariff(450000.0, 680000.0, 990000.0),
        ContainerType.REEFER_20FT: DailyProgressiveTariff(750000.0, 1150000.0, 1650000.0),
        ContainerType.REEFER_40FT: DailyProgressiveTariff(1250000.0, 1850000.0, 2650000.0),
        ContainerType.SPECIAL_OT_FR: DailyProgressiveTariff(650000.0, 950000.0, 1400000.0),
    }

    @classmethod
    def _compute_progressive(cls, overdue_days: int, tariff: DailyProgressiveTariff) -> float:
        if overdue_days <= 0:
            return 0.0

        tier1_days = min(overdue_days, 5)
        tier2_days = min(max(0, overdue_days - 5), 5)
        tier3_days = max(0, overdue_days - 10)

        total = (
            tier1_days * tariff.tier1_rate_vnd +
            tier2_days * tariff.tier2_rate_vnd +
            tier3_days * tariff.tier3_rate_vnd
        )
        return total

    @classmethod
    def calculate_charges(
        cls,
        container_id: str,
        container_type: ContainerType,
        total_dwell_days: int,
        policy: Optional[FreeTimePolicy] = None,
        cargo_value_vnd: float = 200000000.0,
    ) -> DemurrageDetentionResult:
        if policy is None:
            policy = FreeTimePolicy()

        # 1. Tính số ngày lưu vượt hạn lưu bãi cảng (Demurrage)
        demurrage_days = max(0, total_dwell_days - policy.terminal_free_days)
        demurrage_tariff = cls.DEMURRAGE_RATES.get(container_type, cls.DEMURRAGE_RATES[ContainerType.DRY_20FT])
        demurrage_fee = cls._compute_progressive(demurrage_days, demurrage_tariff)

        # 2. Tính số ngày lưu vượt hạn vỏ container (Detention)
        detention_days = max(0, total_dwell_days - policy.carrier_equipment_free_days)
        detention_tariff = cls.DETENTION_RATES.get(container_type, cls.DETENTION_RATES[ContainerType.DRY_20FT])
        detention_fee = cls._compute_progressive(detention_days, detention_tariff)

        total_charges = demurrage_fee + detention_fee

        # 3. Cảnh báo quyền cầm giữ hàng (Lien) theo Điều 168 Bộ luật Hàng hải VN 2015
        # Nếu chi phí lưu bãi + lưu vỏ vượt quá 70% giá trị hàng, kích hoạt cảnh báo phát mãi
        lien_warning = total_charges >= (cargo_value_vnd * 0.70)

        summary = (
            f"Container {container_id} ({container_type.value}): Lưu kho bãi {total_dwell_days} ngày. "
            f"Vượt bãi (Demurrage): {demurrage_days} ngày = {demurrage_fee:,.0f} VND. "
            f"Vượt vỏ (Detention): {detention_days} ngày = {detention_fee:,.0f} VND. "
            f"Tổng phạt: {total_charges:,.0f} VND."
        )

        return DemurrageDetentionResult(
            container_id=container_id,
            container_type=container_type.value,
            total_dwell_days=total_dwell_days,
            terminal_demurrage_days=demurrage_days,
            terminal_demurrage_fee_vnd=round(demurrage_fee, 2),
            carrier_detention_days=detention_days,
            carrier_detention_fee_vnd=round(detention_fee, 2),
            total_dd_charges_vnd=round(total_charges, 2),
            cargo_value_vnd=cargo_value_vnd,
            is_maritime_lien_warning=lien_warning,
            cost_status_summary=summary,
        )
