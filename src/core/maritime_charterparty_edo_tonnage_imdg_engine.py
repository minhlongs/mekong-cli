"""
Maritime Charterparty Performance, Electronic D/O, Port Tonnage & IMDG Engine
Phases 267-270 Maritime Compliance & Operations Suite for Mekong CLI v6.0.

Statutory and International Maritime References:
- Phase 267: Vietnam Maritime Code (VMC) 2015 Arts. 215-230, BIMCO NYPE 93/2015,
  The Didymi [1988] 2 Lloyd's Rep. 108 & The Gas Enterprise [1993] 2 Lloyd's Rep. 352
- Phase 268: VMC 2015 Arts. 160 & 168, Circular 38/2015/TT-BTC, Circular 39/2018/TT-BTC,
  Decree 58/2017/NĐ-CP (e-D/O and Container Deposit Settlement)
- Phase 269: Circular 39/2023/TT-BGTVT, Circular 12/2024/TT-BGTVT, VMC 2015 Arts. 104, 107-112
  (Seaport Tonnage Dues & Maritime Safety Tariffs)
- Phase 270: IMO IMDG Code Amendment 41-22, Decree 58/2017/NĐ-CP Arts. 73-77, Decree 34/2024/NĐ-CP
  (Dangerous Goods Handling, Segregation Matrix & Emergency Schedules)

CRITICAL QUALITY REQUIREMENT:
- Strict zero-dependency rule: Python standard library ONLY.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# Phase 267: Time Charterparty Speed & Consumption Warranty Assessment
# ============================================================================

class WeatherCondition(str, Enum):
    GOOD_WEATHER = "GOOD_WEATHER"          # Wind <= BF 4, Sea <= Douglas 3 (Wave <= 1.25m), no neg swell
    ADVERSE_WEATHER = "ADVERSE_WEATHER"    # Wind > BF 4 or Sea > Douglas 3


class LiabilityParty(str, Enum):
    OWNERS_LIABLE = "OWNERS_LIABLE"
    CHARTERERS_OFFSET = "CHARTERERS_OFFSET"
    BALANCED_NO_CLAIM = "BALANCED_NO_CLAIM"


@dataclass
class WarrantedTerms:
    warranted_speed_knots: float
    warranted_fuel_tonnes_day: float
    about_speed_allowance_knots: float = 0.5  # Standard "about" clause gives 0.5 kts leeway
    about_fuel_allowance_percent: float = 0.05  # Standard 5% leeway on fuel
    daily_hire_rate_usd: float = 18000.0
    vlsfo_price_per_tonne_usd: float = 620.0


@dataclass
class PassageLegData:
    leg_name: str
    total_distance_nm: float
    steaming_hours_total: float
    good_weather_hours: float
    good_weather_distance_nm: float
    actual_fuel_consumed_tonnes: float
    current_factor_knots: float = 0.0  # Positive = favorable current, negative = adverse


@dataclass
class CharterpartyClaimResult:
    warranted_net_speed_knots: float
    warranted_effective_fuel_t_day: float
    actual_good_weather_speed_knots: float
    speed_deficiency_good_weather_knots: float
    is_underperforming_in_good_weather: bool
    allowed_steaming_hours: float
    net_time_lost_hours: float
    net_time_lost_days: float
    allowed_fuel_tonnes: float
    fuel_variance_tonnes: float  # Positive = overconsumption, Negative = saving
    time_loss_financial_claim_usd: float
    fuel_variance_financial_claim_usd: float
    net_total_claim_usd: float
    liability_determination: LiabilityParty
    legal_doctrine_applied: str
    recommendation_vi: str
    recommendation_en: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CharterpartyPerformanceEngine:
    """
    Evaluates vessel speed and fuel oil consumption performance against time charter warranties.
    Applies 'The Didymi' (extrapolation from good weather) and 'The Gas Enterprise' (financial netting).
    """

    @staticmethod
    def evaluate_passage(
        warranties: WarrantedTerms,
        passage: PassageLegData,
    ) -> CharterpartyClaimResult:
        if passage.steaming_hours_total <= 0 or passage.total_distance_nm <= 0:
            raise ValueError("Steaming hours and distance must be greater than zero.")

        # 1. Effective Warranties incorporating "About" allowances (English Commercial Law)
        # "About" on speed protects Owner by reducing minimum warranted speed
        effective_warranted_speed = warranties.warranted_speed_knots - warranties.about_speed_allowance_knots
        # "About" on fuel increases maximum warranted consumption
        effective_warranted_fuel_rate = warranties.warranted_fuel_tonnes_day * (1.0 + warranties.about_fuel_allowance_percent)

        # 2. Analyze Good Weather Sample
        if passage.good_weather_hours > 0 and passage.good_weather_distance_nm > 0:
            actual_gw_speed = passage.good_weather_distance_nm / passage.good_weather_hours
            actual_gw_speed_adjusted = actual_gw_speed - passage.current_factor_knots
            speed_deficiency = effective_warranted_speed - actual_gw_speed_adjusted
            is_underperforming = speed_deficiency > 0.05
        else:
            # Fallback to total passage if no good weather recorded (or bad weather entire route)
            actual_gw_speed = passage.total_distance_nm / passage.steaming_hours_total
            actual_gw_speed_adjusted = actual_gw_speed - passage.current_factor_knots
            speed_deficiency = max(0.0, effective_warranted_speed - actual_gw_speed_adjusted)
            is_underperforming = speed_deficiency > 0.05

        # 3. Calculate Allowed Steaming Time using effective speed warranty
        # Under The Didymi [1988], if underperformance is proven in good weather,
        # apply it to derive time lost.
        allowed_steaming_hours = passage.total_distance_nm / effective_warranted_speed
        net_time_lost_hours = max(0.0, passage.steaming_hours_total - allowed_steaming_hours) if is_underperforming else 0.0
        net_time_lost_days = net_time_lost_hours / 24.0

        # 4. Fuel Consumption & Netting (The Gas Enterprise [1993])
        # Allowed fuel is based on allowed steaming time at the effective fuel rate
        allowed_fuel_tonnes = (allowed_steaming_hours / 24.0) * effective_warranted_fuel_rate
        fuel_variance_tonnes = passage.actual_fuel_consumed_tonnes - allowed_fuel_tonnes

        # 5. Financial Quantification
        time_claim_usd = net_time_lost_days * warranties.daily_hire_rate_usd
        fuel_claim_usd = fuel_variance_tonnes * warranties.vlsfo_price_per_tonne_usd
        net_claim_usd = time_claim_usd + fuel_claim_usd

        if net_claim_usd > 100.0:
            liability = LiabilityParty.OWNERS_LIABLE
            rec_vi = f"Chủ tàu vi phạm cam kết tốc độ/tiêu hao. Người thuê tàu được khấu trừ {net_claim_usd:,.2f} USD vào kỳ thanh toán tiền thuê tiếp theo."
            rec_en = f"Owners in breach of speed/consumption warranty. Charterers entitled to deduct ${net_claim_usd:,.2f} from hire."
        elif net_claim_usd < -100.0:
            liability = LiabilityParty.CHARTERERS_OFFSET
            rec_vi = f"Tàu tiết kiệm nhiên liệu vượt trội ({abs(fuel_variance_tonnes):.2f} tấn). Bù trừ hoàn toàn chênh lệch thời gian theo phán quyết The Gas Enterprise."
            rec_en = f"Bunker savings of {abs(fuel_variance_tonnes):.2f} MT fully offset any time deficiency per The Gas Enterprise doctrine."
        else:
            liability = LiabilityParty.BALANCED_NO_CLAIM
            rec_vi = "Tàu vận hành trong giới hạn dung sai cho phép (about allowance). Không phát sinh khiếu nại tài chính."
            rec_en = "Vessel operated within contractual tolerances. No financial claim arises."

        return CharterpartyClaimResult(
            warranted_net_speed_knots=effective_warranted_speed,
            warranted_effective_fuel_t_day=effective_warranted_fuel_rate,
            actual_good_weather_speed_knots=round(actual_gw_speed, 2),
            speed_deficiency_good_weather_knots=round(max(0.0, speed_deficiency), 2),
            is_underperforming_in_good_weather=is_underperforming,
            allowed_steaming_hours=round(allowed_steaming_hours, 2),
            net_time_lost_hours=round(net_time_lost_hours, 2),
            net_time_lost_days=round(net_time_lost_days, 3),
            allowed_fuel_tonnes=round(allowed_fuel_tonnes, 2),
            fuel_variance_tonnes=round(fuel_variance_tonnes, 2),
            time_loss_financial_claim_usd=round(time_claim_usd, 2),
            fuel_variance_financial_claim_usd=round(fuel_claim_usd, 2),
            net_total_claim_usd=round(net_claim_usd, 2),
            liability_determination=liability,
            legal_doctrine_applied="The Didymi [1988] 2 Lloyd's Rep 108 & The Gas Enterprise [1993] 2 Lloyd's Rep 352",
            recommendation_vi=rec_vi,
            recommendation_en=rec_en,
        )


# ============================================================================
# Phase 268: Seaport Electronic Delivery Order (e-D/O) & Container Deposit
# ============================================================================

class ContainerCategory(str, Enum):
    DRY_20FT = "DRY_20FT"
    DRY_40FT = "DRY_40FT"
    REEFER_20FT = "REEFER_20FT"
    REEFER_40FT = "REEFER_40FT"
    SPECIAL_OT_FR = "SPECIAL_OT_FR"


class EDOStatus(str, Enum):
    ISSUED_VALID = "ISSUED_VALID"
    CARGO_RELEASED = "CARGO_RELEASED"
    CONTAINER_RETURNED = "CONTAINER_RETURNED"
    DEPOSIT_REFUNDED = "DEPOSIT_REFUNDED"
    DISPUTED_OVERDUE = "DISPUTED_OVERDUE"


@dataclass
class ContainerDepositParams:
    category: ContainerCategory
    unit_count: int
    deposit_per_unit_vnd: float
    free_days_allowed: int
    actual_days_to_return: int
    daily_detention_rate_vnd: float
    iicl_damage_repair_vnd: float = 0.0
    container_cleaning_fee_vnd: float = 0.0


@dataclass
class EDODepositSettlementResult:
    bl_number: str
    edo_reference: str
    status: EDOStatus
    total_deposit_held_vnd: float
    overdue_days: int
    detention_charge_total_vnd: float
    repair_deduction_total_vnd: float
    cleaning_deduction_total_vnd: float
    total_deductions_vnd: float
    net_refund_payable_vnd: float
    additional_balance_due_vnd: float
    statutory_refund_deadline_days: int
    compliance_verdict_vi: str
    compliance_verdict_en: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ElectronicDeliveryOrderEngine:
    """
    Manages e-D/O issuance validation and Container Deposit (Cược vỏ cont) settlement.
    Enforces VMC 2015 Arts. 160, 168 and Vietnamese customs digital release requirements.
    """

    @staticmethod
    def calculate_deposit_settlement(
        bl_number: str,
        edo_reference: str,
        params: ContainerDepositParams,
    ) -> EDODepositSettlementResult:
        if params.unit_count <= 0 or params.deposit_per_unit_vnd < 0:
            raise ValueError("Unit count must be positive and deposit cannot be negative.")

        total_deposit_held = params.unit_count * params.deposit_per_unit_vnd
        overdue_days = max(0, params.actual_days_to_return - params.free_days_allowed)

        detention_charge_total = overdue_days * params.daily_detention_rate_vnd * params.unit_count
        repair_deduction_total = params.iicl_damage_repair_vnd
        cleaning_deduction_total = params.container_cleaning_fee_vnd

        total_deductions = detention_charge_total + repair_deduction_total + cleaning_deduction_total

        if total_deposit_held >= total_deductions:
            net_refund_payable = total_deposit_held - total_deductions
            additional_balance_due = 0.0
            status = EDOStatus.DEPOSIT_REFUNDED if overdue_days == 0 else EDOStatus.CONTAINER_RETURNED
            verdict_vi = f"Đủ điều kiện hoàn cược. Hãng tàu/đại lý có trách nhiệm hoàn trả {net_refund_payable:,.0f} VND trong vòng 3 ngày làm việc."
            verdict_en = f"Eligible for deposit refund. Carrier must refund {net_refund_payable:,.0f} VND within 3 banking days."
        else:
            net_refund_payable = 0.0
            additional_balance_due = total_deductions - total_deposit_held
            status = EDOStatus.DISPUTED_OVERDUE
            verdict_vi = f"Khấu trừ hết tiền cược. Chủ hàng còn nợ hãng tàu thêm {additional_balance_due:,.0f} VND tiền lưu bãi/sửa chữa."
            verdict_en = f"Deposit depleted. Consignee owes additional {additional_balance_due:,.0f} VND for detention/damages."

        return EDODepositSettlementResult(
            bl_number=bl_number,
            edo_reference=edo_reference,
            status=status,
            total_deposit_held_vnd=total_deposit_held,
            overdue_days=overdue_days,
            detention_charge_total_vnd=detention_charge_total,
            repair_deduction_total_vnd=repair_deduction_total,
            cleaning_deduction_total_vnd=cleaning_deduction_total,
            total_deductions_vnd=total_deductions,
            net_refund_payable_vnd=net_refund_payable,
            additional_balance_due_vnd=additional_balance_due,
            statutory_refund_deadline_days=3,
            compliance_verdict_vi=verdict_vi,
            compliance_verdict_en=verdict_en,
        )


# ============================================================================
# Phase 269: Seaport Tonnage Dues & Maritime Safety Tariffs
# ============================================================================

class VoyageType(str, Enum):
    INTERNATIONAL = "INTERNATIONAL"
    DOMESTIC = "DOMESTIC"


class PortMaritimeZone(str, Enum):
    ZONE_I_NORTH = "ZONE_I_NORTH"      # Hải Phòng, Quảng Ninh, Nghi Sơn
    ZONE_II_CENTRAL = "ZONE_II_CENTRAL"# Đà Nẵng, Quy Nhơn, Dung Quất
    ZONE_III_SOUTH = "ZONE_III_SOUTH"  # TP.HCM, Cái Mép - Thị Vải, Cần Thơ


@dataclass
class VesselPortCallData:
    vessel_gross_tonnage_gt: float
    voyage_type: VoyageType
    port_zone: PortMaritimeZone
    number_of_port_calls: int = 1
    anchorage_hours: float = 24.0
    has_green_award_certificate: bool = False
    is_transshipment_cargo_only: bool = False


@dataclass
class SeaportTariffBreakdownResult:
    tonnage_dues_entry_exit_total: float
    maritime_safety_dues_total: float
    anchorage_fairway_dues_total: float
    green_discount_amount: float
    grand_total_port_dues: float
    currency: str
    statutory_legal_basis: str
    statutory_summary_vi: str
    statutory_summary_en: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SeaportTonnageTariffEngine:
    """
    Computes statutory Seaport Tonnage Dues, Maritime Safety Dues & Anchorage Tariffs
    under Circular 39/2023/TT-BGTVT and Circular 12/2024/TT-BGTVT.
    """

    # Statutory Rates (Circular 39/2023/TT-BGTVT)
    # International voyages (in USD per GT)
    INTL_TONNAGE_DUE_PER_GT_CALL = 0.034     # Art. 6: 0.034 USD/GT/lượt vào hoặc rời
    INTL_SAFETY_DUE_PER_GT_CALL = 0.076      # Art. 7: 0.076 USD/GT/lượt vào hoặc rời
    INTL_ANCHORAGE_PER_GT_HOUR = 0.0005      # Art. 8: 0.0005 USD/GT/giờ neo đậu

    # Domestic voyages (in VND per GT)
    DOM_TONNAGE_DUE_PER_GT_CALL = 350.0      # Avg 250 - 450 VND/GT
    DOM_SAFETY_DUE_PER_GT_CALL = 1000.0      # Avg 700 - 1,400 VND/GT
    DOM_ANCHORAGE_PER_GT_HOUR = 20.0         # 15 - 30 VND/GT/giờ neo đậu

    @classmethod
    def calculate_dues(cls, call_data: VesselPortCallData) -> SeaportTariffBreakdownResult:
        if call_data.vessel_gross_tonnage_gt <= 0:
            raise ValueError("Vessel Gross Tonnage (GT) must be greater than zero.")

        gt = call_data.vessel_gross_tonnage_gt
        calls = max(1, call_data.number_of_port_calls)
        anchorage_hrs = max(0.0, call_data.anchorage_hours)

        if call_data.voyage_type == VoyageType.INTERNATIONAL:
            currency = "USD"
            # 2 calls per voyage entry + exit
            tonnage_rate = cls.INTL_TONNAGE_DUE_PER_GT_CALL * 2 * calls
            safety_rate = cls.INTL_SAFETY_DUE_PER_GT_CALL * 2 * calls

            # Transshipment incentive: 50% reduction on maritime safety dues
            if call_data.is_transshipment_cargo_only:
                safety_rate *= 0.50

            tonnage_dues = gt * tonnage_rate
            safety_dues = gt * safety_rate

            # Anchorage: standard rate, +50% after 720 hours (30 days)
            if anchorage_hrs <= 720.0:
                anchorage_dues = gt * cls.INTL_ANCHORAGE_PER_GT_HOUR * anchorage_hrs
            else:
                base_anchorage = gt * cls.INTL_ANCHORAGE_PER_GT_HOUR * 720.0
                extended_anchorage = gt * (cls.INTL_ANCHORAGE_PER_GT_HOUR * 1.5) * (anchorage_hrs - 720.0)
                anchorage_dues = base_anchorage + extended_anchorage

            subtotal = tonnage_dues + safety_dues + anchorage_dues
            # Green Award discount: 10% on tonnage & safety dues
            green_discount = (tonnage_dues + safety_dues) * 0.10 if call_data.has_green_award_certificate else 0.0
            grand_total = subtotal - green_discount

            summary_vi = (
                f"Tàu quốc tế {gt:,.0f} GT: Phí trọng tải {tonnage_dues:,.2f} USD, "
                f"Phí bảo đảm hàng hải {safety_dues:,.2f} USD, Phí neo đậu {anchorage_dues:,.2f} USD. "
                f"Tổng nộp: {grand_total:,.2f} USD."
            )
            summary_en = (
                f"International vessel {gt:,.0f} GT: Tonnage dues ${tonnage_dues:,.2f}, "
                f"Maritime safety dues ${safety_dues:,.2f}, Anchorage dues ${anchorage_dues:,.2f}. "
                f"Net payable: ${grand_total:,.2f}."
            )
        else:
            currency = "VND"
            tonnage_rate = cls.DOM_TONNAGE_DUE_PER_GT_CALL * 2 * calls
            safety_rate = cls.DOM_SAFETY_DUE_PER_GT_CALL * 2 * calls

            if call_data.is_transshipment_cargo_only:
                safety_rate *= 0.50

            tonnage_dues = gt * tonnage_rate
            safety_dues = gt * safety_rate

            if anchorage_hrs <= 720.0:
                anchorage_dues = gt * cls.DOM_ANCHORAGE_PER_GT_HOUR * anchorage_hrs
            else:
                base_anchorage = gt * cls.DOM_ANCHORAGE_PER_GT_HOUR * 720.0
                extended_anchorage = gt * (cls.DOM_ANCHORAGE_PER_GT_HOUR * 1.5) * (anchorage_hrs - 720.0)
                anchorage_dues = base_anchorage + extended_anchorage

            subtotal = tonnage_dues + safety_dues + anchorage_dues
            green_discount = (tonnage_dues + safety_dues) * 0.10 if call_data.has_green_award_certificate else 0.0
            grand_total = subtotal - green_discount

            summary_vi = (
                f"Tàu nội địa {gt:,.0f} GT: Phí trọng tải {tonnage_dues:,.0f} VND, "
                f"Phí bảo đảm hàng hải {safety_dues:,.0f} VND, Phí neo đậu {anchorage_dues:,.0f} VND. "
                f"Tổng nộp: {grand_total:,.0f} VND."
            )
            summary_en = (
                f"Domestic vessel {gt:,.0f} GT: Tonnage dues {tonnage_dues:,.0f} VND, "
                f"Maritime safety dues {safety_dues:,.0f} VND, Anchorage dues {anchorage_dues:,.0f} VND. "
                f"Net payable: {grand_total:,.0f} VND."
            )

        return SeaportTariffBreakdownResult(
            tonnage_dues_entry_exit_total=round(tonnage_dues, 2),
            maritime_safety_dues_total=round(safety_dues, 2),
            anchorage_fairway_dues_total=round(anchorage_dues, 2),
            green_discount_amount=round(green_discount, 2),
            grand_total_port_dues=round(grand_total, 2),
            currency=currency,
            statutory_legal_basis="Circular 39/2023/TT-BGTVT & Circular 12/2024/TT-BGTVT",
            statutory_summary_vi=summary_vi,
            statutory_summary_en=summary_en,
        )


# ============================================================================
# Phase 270: IMDG Dangerous Goods Handling & Segregation Safety Matrix
# ============================================================================

class IMDGClass(str, Enum):
    CLASS_1_EXPLOSIVES = "CLASS_1_EXPLOSIVES"
    CLASS_2_1_FLAMMABLE_GAS = "CLASS_2_1_FLAMMABLE_GAS"
    CLASS_2_2_NON_FLAMMABLE_GAS = "CLASS_2_2_NON_FLAMMABLE_GAS"
    CLASS_2_3_TOXIC_GAS = "CLASS_2_3_TOXIC_GAS"
    CLASS_3_FLAMMABLE_LIQUID = "CLASS_3_FLAMMABLE_LIQUID"
    CLASS_4_1_FLAMMABLE_SOLID = "CLASS_4_1_FLAMMABLE_SOLID"
    CLASS_4_2_SPONTANEOUS_COMBUSTIBLE = "CLASS_4_2_SPONTANEOUS_COMBUSTIBLE"
    CLASS_4_3_DANGEROUS_WHEN_WET = "CLASS_4_3_DANGEROUS_WHEN_WET"
    CLASS_5_1_OXIDIZING = "CLASS_5_1_OXIDIZING"
    CLASS_5_2_ORGANIC_PEROXIDE = "CLASS_5_2_ORGANIC_PEROXIDE"
    CLASS_6_1_TOXIC = "CLASS_6_1_TOXIC"
    CLASS_6_2_INFECTIOUS = "CLASS_6_2_INFECTIOUS"
    CLASS_7_RADIOACTIVE = "CLASS_7_RADIOACTIVE"
    CLASS_8_CORROSIVE = "CLASS_8_CORROSIVE"
    CLASS_9_MISCELLANEOUS = "CLASS_9_MISCELLANEOUS"


class SegregationRequirement(str, Enum):
    NO_RESTRICTION = "NO_RESTRICTION"                        # 0 / X: Không yêu cầu cách ly
    AWAY_FROM = "AWAY_FROM"                                  # 1: Cách xa (min 3m)
    SEPARATED_FROM = "SEPARATED_FROM"                        # 2: Tách biệt (min 6m hoặc 1 hàng cont)
    SEPARATED_BY_COMPARTMENT = "SEPARATED_BY_COMPARTMENT"    # 3: Tách biệt qua vách ngăn/hầm hàng (12m)
    SEPARATED_LONGITUDINALLY = "SEPARATED_LONGITUDINALLY"    # 4: Cách ly theo chiều dọc toàn bộ hầm


class PortHandlingMode(str, Enum):
    DIRECT_DELIVERY_MANDATORY = "DIRECT_DELIVERY_MANDATORY"  # Giao thẳng, cấm lưu bãi quá 2h
    DEDICATED_HAZMAT_YARD = "DEDICATED_HAZMAT_YARD"          # Bãi riêng, tường chống cháy, đê bao
    RESTRICTED_STANDARD_YARD = "RESTRICTED_STANDARD_YARD"    # Bãi container tiêu chuẩn có khoảng đệm


@dataclass
class IMDGHandlingEvaluationResult:
    primary_class: IMDGClass
    secondary_class: Optional[IMDGClass]
    segregation_code: int
    segregation_requirement: SegregationRequirement
    minimum_buffer_distance_meters: float
    port_handling_mode: PortHandlingMode
    max_dockside_dwell_hours: float
    port_handling_surcharge_percent: float
    fire_safety_ems_schedule: str
    statutory_warning_vi: str
    statutory_warning_en: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IMDGSafetyHandlingEngine:
    """
    Enforces IMDG Code Amendment 41-22 Segregation Matrix & Vietnamese Seaport Handling Rules
    (Decree 58/2017/NĐ-CP Arts. 73-77 and Decree 34/2024/NĐ-CP).
    """

    # IMDG Code Table 7.2.4 Segregation Matrix (simplified numerical mapping between major classes)
    # Key: (ClassA, ClassB) -> Segregation Level (0: None, 1: Away, 2: Separated, 3: Compartment, 4: Longitudinal)
    SEGREGATION_RULES: Dict[Tuple[IMDGClass, IMDGClass], int] = {
        # Class 1 (Explosives) requires highest separation against flammables and oxidizers
        (IMDGClass.CLASS_1_EXPLOSIVES, IMDGClass.CLASS_3_FLAMMABLE_LIQUID): 4,
        (IMDGClass.CLASS_1_EXPLOSIVES, IMDGClass.CLASS_5_1_OXIDIZING): 4,
        (IMDGClass.CLASS_1_EXPLOSIVES, IMDGClass.CLASS_5_2_ORGANIC_PEROXIDE): 4,
        (IMDGClass.CLASS_1_EXPLOSIVES, IMDGClass.CLASS_2_1_FLAMMABLE_GAS): 4,
        (IMDGClass.CLASS_1_EXPLOSIVES, IMDGClass.CLASS_8_CORROSIVE): 2,
        # Class 3 (Flammable Liquids) vs Class 5.1/5.2 (Oxidizers)
        (IMDGClass.CLASS_3_FLAMMABLE_LIQUID, IMDGClass.CLASS_5_1_OXIDIZING): 2,
        (IMDGClass.CLASS_3_FLAMMABLE_LIQUID, IMDGClass.CLASS_5_2_ORGANIC_PEROXIDE): 2,
        (IMDGClass.CLASS_3_FLAMMABLE_LIQUID, IMDGClass.CLASS_2_1_FLAMMABLE_GAS): 0,  # Compatible in storage zone
        (IMDGClass.CLASS_3_FLAMMABLE_LIQUID, IMDGClass.CLASS_8_CORROSIVE): 1,
        # Class 5.1 (Oxidizers) vs Class 8 (Corrosives)
        (IMDGClass.CLASS_5_1_OXIDIZING, IMDGClass.CLASS_8_CORROSIVE): 2,
        # Class 7 (Radioactive) vs Class 1 (Explosives)
        (IMDGClass.CLASS_7_RADIOACTIVE, IMDGClass.CLASS_1_EXPLOSIVES): 4,
        (IMDGClass.CLASS_7_RADIOACTIVE, IMDGClass.CLASS_3_FLAMMABLE_LIQUID): 2,
    }

    @classmethod
    def evaluate_cargo_handling(
        cls,
        primary_class: IMDGClass,
        secondary_class: Optional[IMDGClass] = None,
        tonnage_weight: float = 20.0,
    ) -> IMDGHandlingEvaluationResult:
        # Determine Segregation
        if secondary_class is None or secondary_class == primary_class:
            seg_code = 0
        else:
            pair1 = (primary_class, secondary_class)
            pair2 = (secondary_class, primary_class)
            seg_code = cls.SEGREGATION_RULES.get(pair1, cls.SEGREGATION_RULES.get(pair2, 1))

        if seg_code == 0:
            seg_req = SegregationRequirement.NO_RESTRICTION
            buffer_dist = 0.0
        elif seg_code == 1:
            seg_req = SegregationRequirement.AWAY_FROM
            buffer_dist = 3.0
        elif seg_code == 2:
            seg_req = SegregationRequirement.SEPARATED_FROM
            buffer_dist = 6.0
        elif seg_code == 3:
            seg_req = SegregationRequirement.SEPARATED_BY_COMPARTMENT
            buffer_dist = 12.0
        else:
            seg_req = SegregationRequirement.SEPARATED_LONGITUDINALLY
            buffer_dist = 24.0

        # Port handling mode & dwell restrictions (Decree 58/2017 Art. 74)
        if primary_class in (IMDGClass.CLASS_1_EXPLOSIVES, IMDGClass.CLASS_7_RADIOACTIVE):
            handling_mode = PortHandlingMode.DIRECT_DELIVERY_MANDATORY
            max_dwell = 2.0  # Max 2 hours at dockside
            surcharge = 200.0  # +200% handling surcharge
            ems = "F-B, S-Y (Emergency Schedule for Explosives/Radioactive)"
            warn_vi = "BẮT BUỘC GIAO THẲNG (Direct Delivery). Cấm hạ bãi container cảng. Thời gian lưu cầu tàu tối đa 2 giờ."
            warn_en = "MANDATORY DIRECT DELIVERY. Prohibited in port container yards. Wharf dwell time limited to 2 hours."
        elif primary_class in (
            IMDGClass.CLASS_2_1_FLAMMABLE_GAS,
            IMDGClass.CLASS_2_3_TOXIC_GAS,
            IMDGClass.CLASS_3_FLAMMABLE_LIQUID,
            IMDGClass.CLASS_5_1_OXIDIZING,
            IMDGClass.CLASS_5_2_ORGANIC_PEROXIDE,
        ):
            handling_mode = PortHandlingMode.DEDICATED_HAZMAT_YARD
            max_dwell = 48.0
            surcharge = 100.0  # +100% handling surcharge
            ems = "F-E, S-D (Fire Schedule Flammables & Peroxides)"
            warn_vi = "Lưu tại bãi hàng nguy hiểm chuyên dụng. Yêu cầu tường ngăn cháy, đê quây thu gom và khoảng đệm 50m."
            warn_en = "Store in dedicated hazmat yard. Requires fire walls, chemical sumps, and 50m safety perimeter."
        else:
            handling_mode = PortHandlingMode.RESTRICTED_STANDARD_YARD
            max_dwell = 72.0
            surcharge = 50.0  # +50% handling surcharge
            ems = "F-A, S-B (General Spillage & Fire Schedule)"
            warn_vi = "Được phép lưu tại khu vực chỉ định trong bãi cảng. Tuân thủ khoảng cách ly IMDG."
            warn_en = "Permitted in designated port yard sector. Comply with IMDG segregation buffer."

        return IMDGHandlingEvaluationResult(
            primary_class=primary_class,
            secondary_class=secondary_class,
            segregation_code=seg_code,
            segregation_requirement=seg_req,
            minimum_buffer_distance_meters=buffer_dist,
            port_handling_mode=handling_mode,
            max_dockside_dwell_hours=max_dwell,
            port_handling_surcharge_percent=surcharge,
            fire_safety_ems_schedule=ems,
            statutory_warning_vi=warn_vi,
            statutory_warning_en=warn_en,
        )
