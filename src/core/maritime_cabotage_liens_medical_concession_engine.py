"""Maritime Domestic Cabotage, Liens Waterfall, Seafarer Medical & Seaport PPP Concession Engine.

Statutory Frameworks:
- Phase 251: Vietnam Maritime Code 2015 Arts. 7, 21 & Decree 58/2017/NĐ-CP Arts. 18-24 (Cabotage Waiver).
- Phase 252: Vietnam Maritime Code 2015 Arts. 37-43 & MLC 1993 (Maritime Liens & Judicial Auction Waterfall).
- Phase 253: STCW 1978/2010 Reg. I/9, MLC 2006 Standard A1.2 & Circular 22/2017/TT-BYT (Seafarer Medical Fitness).
- Phase 254: Law on PPP 2020 (Law No. 64/2020/QH14) & Decree 35/2021/NĐ-CP Art. 82 (Seaport Concessions & Revenue Sharing).

Pure Python standard library implementation - Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# PHASE 251: MARITIME DOMESTIC CABOTAGE WAIVER ENGINE
# ==============================================================================

class CabotageWaiverReason(str, Enum):
    """Statutory justifications for granting domestic cabotage waiver to foreign vessels."""
    SPECIALIZED_CARGO = "specialized_cargo"          # Hàng hóa chuyên dụng (LNG/LPG, hóa chất độc hại)
    DOMESTIC_FLEET_DEFICIT = "fleet_deficit"         # Đội tàu trong nước không đủ năng lực/phương tiện
    INTERNATIONAL_CRUISE = "international_cruise"    # Tàu khách quốc tế du lịch giữa các cảng VN
    OFFSHORE_PROJECT = "offshore_project"            # Dự án công trình biển / siêu trường siêu trọng


class CabotagePermitType(str, Enum):
    """Types of domestic cabotage waiver licenses."""
    SINGLE_VOYAGE = "single_voyage"                  # Cấp theo từng chuyến
    TIME_CHARTER_3_MONTHS = "time_charter_3m"        # Thuê định hạn đến 3 tháng
    TIME_CHARTER_6_MONTHS = "time_charter_6m"        # Thuê định hạn đến 6 tháng
    ANNUAL_12_MONTHS = "annual_12m"                  # Thời hạn tối đa 1 năm (12 tháng)


@dataclass
class CabotageWaiverEvaluation:
    """Evaluation result for domestic cabotage waiver application."""
    application_id: str
    vessel_name: str
    flag_state: str
    gross_tonnage: float
    reason: CabotageWaiverReason
    permit_type: CabotagePermitType
    cargo_or_passenger_desc: str
    is_approved: bool
    processing_time_days: int
    statutory_permit_fee_vnd: float
    permit_duration_days: int
    operational_conditions: str
    remarks: str


class MaritimeCabotageEngine:
    """Calculates domestic maritime cabotage waiver permits and statutory conditions."""

    @staticmethod
    def evaluate_cabotage_permit(
        application_id: str,
        vessel_name: str,
        flag_state: str,
        gross_tonnage: float,
        reason: CabotageWaiverReason,
        permit_type: CabotagePermitType,
        cargo_or_passenger_desc: str = "Hàng hóa tổng hợp",
        domestic_fleet_available: bool = False,
        vessel_age_years: int = 10,
    ) -> CabotageWaiverEvaluation:
        """Evaluate statutory criteria for foreign vessel domestic transport permit."""
        # Vessel age restriction: Passenger vessels max 15 years, cargo max 20-25 years
        max_allowed_age = 15 if reason == CabotageWaiverReason.INTERNATIONAL_CRUISE else 25
        if vessel_age_years > max_allowed_age:
            return CabotageWaiverEvaluation(
                application_id=application_id,
                vessel_name=vessel_name,
                flag_state=flag_state,
                gross_tonnage=gross_tonnage,
                reason=reason,
                permit_type=permit_type,
                cargo_or_passenger_desc=cargo_or_passenger_desc,
                is_approved=False,
                processing_time_days=7,
                statutory_permit_fee_vnd=0.0,
                permit_duration_days=0,
                operational_conditions="TỪ CHỐI CẤP PHÉP",
                remarks=f"Tuổi tàu ({vessel_age_years} năm) vượt quá quy định tối đa ({max_allowed_age} năm) theo NĐ 58/2017.",
            )

        # Flag State check: Vietnamese flag does not need cabotage waiver
        if flag_state.upper() in ["VN", "VIETNAM", "VIỆT NAM"]:
            return CabotageWaiverEvaluation(
                application_id=application_id,
                vessel_name=vessel_name,
                flag_state=flag_state,
                gross_tonnage=gross_tonnage,
                reason=reason,
                permit_type=permit_type,
                cargo_or_passenger_desc=cargo_or_passenger_desc,
                is_approved=True,
                processing_time_days=0,
                statutory_permit_fee_vnd=0.0,
                permit_duration_days=365,
                operational_conditions="TÀU MANG CỜ QUỐC TỊCH VIỆT NAM",
                remarks="Tàu mang cờ Việt Nam được quyền đương nhiên vận tải nội địa theo Điều 7 Bộ luật Hàng hải 2015.",
            )

        # If domestic fleet can handle the cargo and it is not a specialized waiver ground -> Reject
        if domestic_fleet_available and reason == CabotageWaiverReason.DOMESTIC_FLEET_DEFICIT:
            return CabotageWaiverEvaluation(
                application_id=application_id,
                vessel_name=vessel_name,
                flag_state=flag_state,
                gross_tonnage=gross_tonnage,
                reason=reason,
                permit_type=permit_type,
                cargo_or_passenger_desc=cargo_or_passenger_desc,
                is_approved=False,
                processing_time_days=7,
                statutory_permit_fee_vnd=0.0,
                permit_duration_days=0,
                operational_conditions="TỪ CHỐI CẤP PHÉP",
                remarks="Đội tàu quốc gia Việt Nam đáp ứng đủ năng lực vận chuyển theo lịch trình yêu cầu.",
            )

        # Approved: Determine duration and statutory permit fees
        duration_map = {
            CabotagePermitType.SINGLE_VOYAGE: 15,
            CabotagePermitType.TIME_CHARTER_3_MONTHS: 90,
            CabotagePermitType.TIME_CHARTER_6_MONTHS: 180,
            CabotagePermitType.ANNUAL_12_MONTHS: 365,
        }
        duration_days = duration_map[permit_type]

        # Statutory fee under Circular 39/2023/TT-BGTVT
        base_fee = 5_000_000.0 if permit_type == CabotagePermitType.SINGLE_VOYAGE else 20_000_000.0
        tonnage_surcharge = min(50_000_000.0, gross_tonnage * 200.0)
        total_fee = round(base_fee + tonnage_surcharge, 0)

        conditions = (
            f"Chỉ được phép vận chuyển '{cargo_or_passenger_desc}' giữa các cảng biển chỉ định tại Việt Nam; "
            f"Tuân thủ kiểm tra an ninh cảng biển ISPS và quy định kiểm dịch y tế trước khi rời cảng."
        )

        return CabotageWaiverEvaluation(
            application_id=application_id,
            vessel_name=vessel_name,
            flag_state=flag_state,
            gross_tonnage=gross_tonnage,
            reason=reason,
            permit_type=permit_type,
            cargo_or_passenger_desc=cargo_or_passenger_desc,
            is_approved=True,
            processing_time_days=7,
            statutory_permit_fee_vnd=total_fee,
            permit_duration_days=duration_days,
            operational_conditions=conditions,
            remarks=f"Chấp thuận cấp giấy phép vận tải nội địa có thời hạn {duration_days} ngày theo Điều 21 Bộ luật Hàng hải 2015.",
        )


# ==============================================================================
# PHASE 252: MARITIME LIENS & JUDICIAL AUCTION WATERFALL ENGINE
# ==============================================================================

class MaritimeClaimTier(str, Enum):
    """Statutory priority tiers for maritime claims under VMC 2015 Arts. 37-38."""
    TIER_0_COURT_CUSTODY = "tier_0_court_custody"       # Chi phí giữ tàu, bán đấu giá & tư pháp
    TIER_1_CREW_WAGES = "tier_1_crew_wages"             # Tiền lương, hồi hương, BHXH thuyền viên
    TIER_2_PERSONAL_INJURY = "tier_2_personal_injury"   # Tổn thất tính mạng, thương tật do hoạt động tàu
    TIER_3_SALVAGE_GA = "tier_3_salvage_ga"             # Tiền thưởng cứu hộ & đóng góp tổn thất chung
    TIER_4_PORT_DUES = "tier_4_port_dues"               # Phí cảng biển, an toàn hàng hải, hoa tiêu
    TIER_5_PROPERTY_DAMAGE = "tier_5_property_damage"   # Tổn thất tài sản do đâm va, sự cố tàu
    TIER_6_SHIP_MORTGAGE = "tier_6_ship_mortgage"       # Thế chấp tàu biển đã đăng ký hợp pháp
    TIER_7_GENERAL_CREDITORS = "tier_7_general"         # Chủ nợ thông thường (nhiên liệu, sửa chữa)


@dataclass
class MaritimeClaimItem:
    """Individual maritime creditor claim."""
    claim_id: str
    creditor_name: str
    tier: MaritimeClaimTier
    claim_amount_usd: float
    claim_date_str: str
    is_time_barred: bool = False


@dataclass
class ClaimDistributionResult:
    """Distribution result for an individual claim."""
    claim_id: str
    creditor_name: str
    tier: MaritimeClaimTier
    original_claim_usd: float
    allocated_payout_usd: float
    unpaid_balance_usd: float
    recovery_rate_pct: float
    status: str


@dataclass
class AuctionProceedsDistributionReport:
    """Comprehensive judicial ship auction distribution summary."""
    vessel_name: str
    gross_auction_proceeds_usd: float
    court_custody_costs_usd: float
    net_distributable_funds_usd: float
    total_claims_demanded_usd: float
    total_claims_paid_usd: float
    surplus_to_shipowner_usd: float
    claims_distributions: List[ClaimDistributionResult]
    waterfall_summary: str


class MaritimeLiensAuctionEngine:
    """Distributes judicial auction proceeds according to Vietnamese statutory priority."""

    TIER_ORDER = [
        MaritimeClaimTier.TIER_0_COURT_CUSTODY,
        MaritimeClaimTier.TIER_1_CREW_WAGES,
        MaritimeClaimTier.TIER_2_PERSONAL_INJURY,
        MaritimeClaimTier.TIER_3_SALVAGE_GA,
        MaritimeClaimTier.TIER_4_PORT_DUES,
        MaritimeClaimTier.TIER_5_PROPERTY_DAMAGE,
        MaritimeClaimTier.TIER_6_SHIP_MORTGAGE,
        MaritimeClaimTier.TIER_7_GENERAL_CREDITORS,
    ]

    @staticmethod
    def distribute_auction_proceeds(
        vessel_name: str,
        gross_auction_proceeds_usd: float,
        claims: List[MaritimeClaimItem],
        court_custody_costs_usd: float = 0.0,
    ) -> AuctionProceedsDistributionReport:
        """Executes statutory priority waterfall on ship sale proceeds."""
        # Tier 0 deduction
        net_distributable = max(0.0, gross_auction_proceeds_usd - court_custody_costs_usd)
        remaining_funds = net_distributable
        total_claims_demanded = sum(c.claim_amount_usd for c in claims)
        distributions: List[ClaimDistributionResult] = []

        # Group valid claims by tier
        tier_claims_map: Dict[MaritimeClaimTier, List[MaritimeClaimItem]] = {t: [] for t in MaritimeLiensAuctionEngine.TIER_ORDER}
        for c in claims:
            if c.is_time_barred:
                distributions.append(ClaimDistributionResult(
                    claim_id=c.claim_id,
                    creditor_name=c.creditor_name,
                    tier=c.tier,
                    original_claim_usd=c.claim_amount_usd,
                    allocated_payout_usd=0.0,
                    unpaid_balance_usd=c.claim_amount_usd,
                    recovery_rate_pct=0.0,
                    status="HẾT HIỆU LỰC (Thời hiệu quyền cầm giữ hàng hải 1 năm đã chấm dứt)",
                ))
            else:
                tier_claims_map[c.tier].append(c)

        # Distribute tier by tier
        for tier in MaritimeLiensAuctionEngine.TIER_ORDER:
            tier_list = tier_claims_map[tier]
            if not tier_list:
                continue

            tier_total = sum(item.claim_amount_usd for item in tier_list)
            if remaining_funds >= tier_total:
                # Fully satisfied
                for item in tier_list:
                    distributions.append(ClaimDistributionResult(
                        claim_id=item.claim_id,
                        creditor_name=item.creditor_name,
                        tier=item.tier,
                        original_claim_usd=item.claim_amount_usd,
                        allocated_payout_usd=item.claim_amount_usd,
                        unpaid_balance_usd=0.0,
                        recovery_rate_pct=100.0,
                        status="THANH TOÁN ĐỦ 100%",
                    ))
                remaining_funds -= tier_total
            elif remaining_funds > 0.0:
                # Pro-rata distribution within this tier
                ratio = remaining_funds / tier_total
                for item in tier_list:
                    payout = round(item.claim_amount_usd * ratio, 2)
                    unpaid = round(item.claim_amount_usd - payout, 2)
                    rate = round((payout / item.claim_amount_usd) * 100.0, 2)
                    distributions.append(ClaimDistributionResult(
                        claim_id=item.claim_id,
                        creditor_name=item.creditor_name,
                        tier=item.tier,
                        original_claim_usd=item.claim_amount_usd,
                        allocated_payout_usd=payout,
                        unpaid_balance_usd=unpaid,
                        recovery_rate_pct=rate,
                        status=f"THANH TOÁN MỘT PHẦN ({rate}%) THEO TỶ LỆ PRO-RATA",
                    ))
                remaining_funds = 0.0
            else:
                # Funds exhausted
                for item in tier_list:
                    distributions.append(ClaimDistributionResult(
                        claim_id=item.claim_id,
                        creditor_name=item.creditor_name,
                        tier=item.tier,
                        original_claim_usd=item.claim_amount_usd,
                        allocated_payout_usd=0.0,
                        unpaid_balance_usd=item.claim_amount_usd,
                        recovery_rate_pct=0.0,
                        status="HẾT TIỀN PHÂN BỔ (0%)",
                    ))

        total_paid = sum(d.allocated_payout_usd for d in distributions)
        surplus = round(remaining_funds, 2)

        summary = (
            f"Phân bổ tiền đấu giá tàu {vessel_name}: Tổng thu ${gross_auction_proceeds_usd:,.2f}. "
            f"Chi phí tố tụng/bảo quản: ${court_custody_costs_usd:,.2f}. "
            f"Tổng thanh toán chủ nợ: ${total_paid:,.2f}. "
            f"Thặng dư hoàn trả chủ tàu: ${surplus:,.2f}."
        )

        return AuctionProceedsDistributionReport(
            vessel_name=vessel_name,
            gross_auction_proceeds_usd=gross_auction_proceeds_usd,
            court_custody_costs_usd=court_custody_costs_usd,
            net_distributable_funds_usd=net_distributable,
            total_claims_demanded_usd=total_claims_demanded,
            total_claims_paid_usd=total_paid,
            surplus_to_shipowner_usd=surplus,
            claims_distributions=distributions,
            waterfall_summary=summary,
        )


# ==============================================================================
# PHASE 253: SEAFARER MEDICAL FITNESS (STCW REG. I/9) ENGINE
# ==============================================================================

class SeafarerDepartment(str, Enum):
    """Department role aboard merchant vessel."""
    DECK_OFFICER = "deck_officer"        # Sĩ quan boong / Thuyền trưởng (Yêu cầu thị lực cao nhất)
    ENGINE_OFFICER = "engine_officer"    # Sĩ quan máy
    DECK_RATING = "deck_rating"          # Thủy thủ boong
    ENGINE_RATING = "engine_rating"      # Thợ máy
    CATERING_SERVICE = "catering"        # Phục vụ / Bếp


class MedicalFitnessVerdict(str, Enum):
    """STCW & Circular 22/2017 medical fitness certificate conclusion."""
    FIT_UNRESTRICTED = "fit_unrestricted"          # Đủ điều kiện sức khỏe không hạn chế
    FIT_WITH_RESTRICTIONS = "fit_restricted"       # Đủ điều kiện kèm hạn chế (kính, vùng biển)
    TEMPORARILY_UNFIT = "temporarily_unfit"        # Tạm thời chưa đủ điều kiện
    PERMANENTLY_UNFIT = "permanently_unfit"        # Vĩnh viễn không đủ điều kiện


@dataclass
class SeafarerMedicalCertificate:
    """Official STCW seafarer medical fitness assessment."""
    certificate_id: str
    seafarer_name: str
    date_of_birth: str
    department: SeafarerDepartment
    visual_acuity_right: float
    visual_acuity_left: float
    color_vision_pass: bool
    hearing_threshold_db: float
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    bmi: float
    verdict: MedicalFitnessVerdict
    validity_months: int
    restriction_notes: str
    statutory_remarks: str


class SeafarerMedicalEngine:
    """Evaluates seafarer health against STCW Reg. I/9 and Circular 22/2017/TT-BYT."""

    @staticmethod
    def evaluate_fitness(
        certificate_id: str,
        seafarer_name: str,
        date_of_birth: str,
        department: SeafarerDepartment,
        visual_acuity_right: float,
        visual_acuity_left: float,
        color_vision_pass: bool,
        hearing_threshold_db: float = 20.0,
        blood_pressure_systolic: int = 120,
        blood_pressure_diastolic: int = 80,
        bmi: float = 23.5,
        age_years: int = 30,
        requires_corrective_lenses: bool = False,
    ) -> SeafarerMedicalCertificate:
        """Determines STCW fitness verdict, restrictions, and certificate validity."""
        restrictions: List[str] = []

        # 1. Color vision check
        if not color_vision_pass:
            if department in [SeafarerDepartment.DECK_OFFICER, SeafarerDepartment.DECK_RATING]:
                return SeafarerMedicalCertificate(
                    certificate_id=certificate_id,
                    seafarer_name=seafarer_name,
                    date_of_birth=date_of_birth,
                    department=department,
                    visual_acuity_right=visual_acuity_right,
                    visual_acuity_left=visual_acuity_left,
                    color_vision_pass=False,
                    hearing_threshold_db=hearing_threshold_db,
                    blood_pressure_systolic=blood_pressure_systolic,
                    blood_pressure_diastolic=blood_pressure_diastolic,
                    bmi=bmi,
                    verdict=MedicalFitnessVerdict.PERMANENTLY_UNFIT,
                    validity_months=0,
                    restriction_notes="MÙ MÀU ĐỎ/XANH LỤC",
                    statutory_remarks="Không đạt chuẩn thị giác màu sắc STCW Bảng A-I/9 cho thuyền viên ngành boong.",
                )
            restrictions.append("Không bố trí ca trực cảnh giới ban đêm (Daylight service only)")

        # 2. Visual Acuity
        min_deck_va = 0.8
        min_engine_va = 0.5
        required_va = min_deck_va if department in [SeafarerDepartment.DECK_OFFICER, SeafarerDepartment.DECK_RATING] else min_engine_va
        if visual_acuity_right < required_va or visual_acuity_left < required_va:
            if not requires_corrective_lenses:
                return SeafarerMedicalCertificate(
                    certificate_id=certificate_id,
                    seafarer_name=seafarer_name,
                    date_of_birth=date_of_birth,
                    department=department,
                    visual_acuity_right=visual_acuity_right,
                    visual_acuity_left=visual_acuity_left,
                    color_vision_pass=color_vision_pass,
                    hearing_threshold_db=hearing_threshold_db,
                    blood_pressure_systolic=blood_pressure_systolic,
                    blood_pressure_diastolic=blood_pressure_diastolic,
                    bmi=bmi,
                    verdict=MedicalFitnessVerdict.TEMPORARILY_UNFIT,
                    validity_months=0,
                    restriction_notes="Thị lực chưa chỉnh kính không đạt chuẩn tối thiểu",
                    statutory_remarks="Cần khám đo khúc xạ và trang bị kính thị lực phù hợp.",
                )
            restrictions.append("Bắt buộc đeo kính thị lực phù hợp và mang theo một kính dự phòng khi làm việc")

        # 3. Hearing threshold (Pure tone audiometry <= 30 dB)
        if hearing_threshold_db > 35.0:
            restrictions.append("Hạn chế khu vực tiếng ồn cao / Cần thiết bị trợ thính")

        # 4. Blood pressure & Cardiovascular
        if blood_pressure_systolic >= 160 or blood_pressure_diastolic >= 100:
            return SeafarerMedicalCertificate(
                certificate_id=certificate_id,
                seafarer_name=seafarer_name,
                date_of_birth=date_of_birth,
                department=department,
                visual_acuity_right=visual_acuity_right,
                visual_acuity_left=visual_acuity_left,
                color_vision_pass=color_vision_pass,
                hearing_threshold_db=hearing_threshold_db,
                blood_pressure_systolic=blood_pressure_systolic,
                blood_pressure_diastolic=blood_pressure_diastolic,
                bmi=bmi,
                verdict=MedicalFitnessVerdict.TEMPORARILY_UNFIT,
                validity_months=0,
                restriction_notes="TĂNG HUYẾT ÁP ĐỘ 2",
                statutory_remarks="Tạm hoãn cấp chứng chỉ; yêu cầu điều trị ổn định huyết áp.",
            )

        # 5. BMI check
        if bmi >= 35.0:
            restrictions.append("Béo phì độ 2 - Cần theo dõi tim mạch định kỳ 6 tháng")

        # Validity: 12 months for minor seafarers (< 18), 24 months for adults
        validity = 12 if age_years < 18 else 24

        if restrictions:
            verdict = MedicalFitnessVerdict.FIT_WITH_RESTRICTIONS
            res_str = "; ".join(restrictions)
            remarks = "Đủ điều kiện sức khỏe làm việc trên biển kèm điều kiện hạn chế STCW Section A-I/9."
        else:
            verdict = MedicalFitnessVerdict.FIT_UNRESTRICTED
            res_str = "Không hạn chế"
            remarks = "Đủ điều kiện sức khỏe làm việc trên biển toàn cầu không hạn chế."

        return SeafarerMedicalCertificate(
            certificate_id=certificate_id,
            seafarer_name=seafarer_name,
            date_of_birth=date_of_birth,
            department=department,
            visual_acuity_right=visual_acuity_right,
            visual_acuity_left=visual_acuity_left,
            color_vision_pass=color_vision_pass,
            hearing_threshold_db=hearing_threshold_db,
            blood_pressure_systolic=blood_pressure_systolic,
            blood_pressure_diastolic=blood_pressure_diastolic,
            bmi=bmi,
            verdict=verdict,
            validity_months=validity,
            restriction_notes=res_str,
            statutory_remarks=remarks,
        )


# ==============================================================================
# PHASE 254: SEAPORT PPP CONCESSION & REVENUE SHARING ENGINE
# ==============================================================================

class PppConcessionModel(str, Enum):
    """Public-Private Partnership seaport concession contract models."""
    BOT = "bot"  # Build - Operate - Transfer (Xây dựng - Kinh doanh - Chuyển giao)
    BTO = "bto"  # Build - Transfer - Operate (Xây dựng - Chuyển giao - Kinh doanh)
    BOO = "boo"  # Build - Own - Operate (Xây dựng - Sở hữu - Kinh doanh)
    OM = "om"    # Operate - Maintain (Kinh doanh - Quản lý)


@dataclass
class PppFinancialMetrics:
    """Financial feasibility metrics of seaport PPP project."""
    total_capex_vnd: float
    equity_ratio_pct: float
    debt_ratio_pct: float
    meets_equity_statutory_threshold: bool
    annual_debt_service_vnd: float
    average_dscr: float
    project_irr_pct: float
    financial_feasibility: bool
    remarks: str


@dataclass
class RevenueSharingSettlement:
    """Annual Decree 35/2021/NĐ-CP Art. 82 revenue risk-sharing calculation."""
    year: int
    planned_revenue_vnd: float
    actual_revenue_vnd: float
    revenue_ratio_pct: float
    lower_threshold_75_vnd: float
    upper_threshold_125_vnd: float
    state_share_payout_to_investor_vnd: float
    investor_share_payout_to_state_vnd: float
    mechanism_triggered: str


class SeaportConcessionEngine:
    """Calculates financial parameters and Decree 35 revenue-sharing waterfalls for seaport PPPs."""

    @staticmethod
    def evaluate_ppp_financials(
        total_capex_vnd: float,
        equity_capital_vnd: float,
        debt_interest_rate_pct: float = 9.0,
        loan_tenor_years: int = 15,
        expected_annual_ebitda_vnd: float = 200_000_000_000.0,
    ) -> PppFinancialMetrics:
        """Evaluates minimum statutory equity (15% per Law on PPP) and debt sustainability."""
        equity_ratio = (equity_capital_vnd / total_capex_vnd) * 100.0 if total_capex_vnd > 0 else 0.0
        debt_ratio = 100.0 - equity_ratio
        meets_equity = equity_ratio >= 15.0

        debt_principal = max(0.0, total_capex_vnd - equity_capital_vnd)
        r = debt_interest_rate_pct / 100.0
        n = loan_tenor_years

        # Equal annual annuity payment: PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
        if debt_principal > 0 and r > 0 and n > 0:
            annuity_factor = (r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)
            annual_debt_service = debt_principal * annuity_factor
        else:
            annual_debt_service = 0.0

        dscr = (expected_annual_ebitda_vnd / annual_debt_service) if annual_debt_service > 0 else 999.0
        irr_estimate = round((expected_annual_ebitda_vnd / total_capex_vnd) * 100.0 * 1.15, 2)
        is_feasible = meets_equity and (dscr >= 1.20)

        remarks = "ĐẠT CHUẨN KHẢ THI TÀI CHÍNH" if is_feasible else "KHÔNG ĐẠT: Vốn chủ sở hữu <15% hoặc DSCR <1.20"

        return PppFinancialMetrics(
            total_capex_vnd=total_capex_vnd,
            equity_ratio_pct=round(equity_ratio, 2),
            debt_ratio_pct=round(debt_ratio, 2),
            meets_equity_statutory_threshold=meets_equity,
            annual_debt_service_vnd=round(annual_debt_service, 0),
            average_dscr=round(dscr, 2),
            project_irr_pct=irr_estimate,
            financial_feasibility=is_feasible,
            remarks=remarks,
        )

    @staticmethod
    def calculate_decree35_revenue_sharing(
        year: int,
        planned_revenue_vnd: float,
        actual_revenue_vnd: float,
    ) -> RevenueSharingSettlement:
        """Calculates Decree 35/2021/NĐ-CP Art. 82 revenue risk-sharing mechanism."""
        ratio_pct = round((actual_revenue_vnd / planned_revenue_vnd) * 100.0, 2)
        lower_75 = planned_revenue_vnd * 0.75
        upper_125 = planned_revenue_vnd * 1.25

        state_payout = 0.0
        investor_payout = 0.0
        trigger = "VÙNG TRUNG HÒA (75% - 125%): Không áp dụng cơ chế chia sẻ"

        if actual_revenue_vnd < lower_75:
            # Downside sharing: State shares 50% of the deficit below 75%
            deficit = lower_75 - actual_revenue_vnd
            state_payout = round(deficit * 0.50, 0)
            trigger = f"KÍCH HOẠT CHIA SẺ GIẢM DOANH THU: Nhà nước bù 50% chênh lệch hụt thu ({state_payout:,.0f} VND)"
        elif actual_revenue_vnd > upper_125:
            # Upside sharing: Investor shares 50% of the excess above 125%
            surplus = actual_revenue_vnd - upper_125
            investor_payout = round(surplus * 0.50, 0)
            trigger = f"KÍCH HOẠT CHIA SẺ TĂNG DOANH THU: Nhà đầu tư nộp ngân sách 50% phần doanh thu vượt ({investor_payout:,.0f} VND)"

        return RevenueSharingSettlement(
            year=year,
            planned_revenue_vnd=planned_revenue_vnd,
            actual_revenue_vnd=actual_revenue_vnd,
            revenue_ratio_pct=ratio_pct,
            lower_threshold_75_vnd=lower_75,
            upper_threshold_125_vnd=upper_125,
            state_share_payout_to_investor_vnd=state_payout,
            investor_share_payout_to_state_vnd=investor_payout,
            mechanism_triggered=trigger,
        )
