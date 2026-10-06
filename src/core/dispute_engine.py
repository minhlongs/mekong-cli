"""
Mekong Dispute Resolution Suite Engine (Phases 159 - 161).
Provides comprehensive engines for:
1. Commercial Arbitration & VIAC (Luật Trọng tài thương mại 2010 & Quy tắc VIAC 2024)
2. Civil Judgment Enforcement (Luật Thi hành án dân sự 2008/2014 & Nghị định 62/2015)
3. Court Litigation & Civil Procedure (Bộ luật Tố tụng Dân sự 2015 & Nghị quyết 326/2016)

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


# ============================================================================
# 1. COMMERCIAL ARBITRATION & VIAC ENGINE (Luật TTTM 2010 & VIAC 2024)
# ============================================================================

class ArbitrationTribunalType(str, Enum):
    THREE_ARBITRATORS = "three_arbitrators"  # Hội đồng 3 trọng tài viên
    SOLE_ARBITRATOR = "sole_arbitrator"      # Trọng tài viên duy nhất


@dataclass
class ArbitrationClauseCheck:
    clause_text: str
    is_valid: bool
    arbitration_institution: str
    risk_factors: List[str] = field(default_factory=list)
    statutory_basis: str = ""
    advice_vn: str = ""


@dataclass
class ViacFeeResult:
    claim_amount_vnd: float
    tribunal_type: ArbitrationTribunalType
    is_international: bool
    arbitration_fee_vnd: float
    sole_discount_applied: bool
    legal_basis: str


@dataclass
class ArbitrationLimitationStatus:
    infringement_date: str
    filing_date: str
    days_passed: int
    is_within_limitation: bool
    remaining_days: int
    advice_vn: str


class CommercialArbitrationEngine:
    """Vietnam Commercial Arbitration & VIAC Evaluation Engine."""

    # Luật TTTM 2010 Điều 33: Thời hiệu khởi kiện là 02 năm (730 ngày)
    LIMITATION_PERIOD_DAYS = 730

    @classmethod
    def validate_arbitration_clause(
        cls,
        clause_text: str,
        dispute_type: str = "commercial",
        parties_have_capacity: bool = True
    ) -> ArbitrationClauseCheck:
        """Thẩm tra tính hợp pháp và hiệu lực của thỏa thuận trọng tài (Điều 16, Điều 18 Luật TTTM 2010)."""
        risks: List[str] = []
        is_valid = True
        institution = "VIAC (Trung tâm Trọng tài Quốc tế Việt Nam)"

        text_lower = clause_text.lower()

        if not parties_have_capacity:
            is_valid = False
            risks.append("Người xác lập thỏa thuận trọng tài không có thẩm quyền hoặc năng lực hành vi dân sự (Khoản 2 Điều 18).")

        if dispute_type not in ("commercial", "trade", "investment", "goods", "services"):
            is_valid = False
            risks.append("Tranh chấp không phát sinh từ hoạt động thương mại theo Điều 2 Luật TTTM 2010.")

        # Thỏa thuận không rõ cơ quan trọng tài hoặc mơ hồ
        if "tòa án" in text_lower and ("trọng tài" in text_lower):
            if "hoặc" in text_lower or "either" in text_lower:
                risks.append("Cảnh báo: Thỏa thuận chọn cả Tòa án hoặc Trọng tài chưa xác định rõ cơ quan giải quyết (Nghị quyết 01/2014/NQ-HĐTP).")

        if "viac" not in text_lower and "trọng tài" not in text_lower and "arbitration" not in text_lower:
            is_valid = False
            risks.append("Không thể hiện rõ ý chí lựa chọn trọng tài theo quy định tại Điều 16 Luật TTTM 2010.")

        if "ad hoc" in text_lower or "vụ việc" in text_lower:
            institution = "Trọng tài vụ việc (Ad-hoc Arbitration)"

        advice = "Thỏa thuận trọng tài có hiệu lực thi hành." if is_valid else "Thỏa thuận trọng tài có nguy cơ bị Tòa án tuyên vô hiệu."
        if risks:
            advice += " Cần làm rõ: " + "; ".join(risks)

        return ArbitrationClauseCheck(
            clause_text=clause_text,
            is_valid=is_valid,
            arbitration_institution=institution,
            risk_factors=risks,
            statutory_basis="Điều 16 & Điều 18 Luật Trọng tài thương mại 2010",
            advice_vn=advice
        )

    @classmethod
    def calculate_viac_fee(
        cls,
        claim_amount_vnd: float,
        tribunal_type: ArbitrationTribunalType = ArbitrationTribunalType.THREE_ARBITRATORS,
        is_international: bool = False
    ) -> ViacFeeResult:
        """
        Tính phí trọng tài VIAC theo Biểu phí Quy tắc VIAC 2024.
        Đối với Hội đồng gồm 1 Trọng tài viên: Phí bằng 70% mức phí của HĐ 3 Trọng tài viên.
        """
        claim = max(0.0, claim_amount_vnd)

        # Bậc phí HĐ 3 Trọng tài viên vụ tranh chấp có giá trị xác định (VNĐ)
        if claim <= 500_000_000:
            fee_3 = 38_000_000.0
        elif claim <= 1_000_000_000:
            fee_3 = 38_000_000.0 + 0.04 * (claim - 500_000_000)
        elif claim <= 5_000_000_000:
            fee_3 = 58_000_000.0 + 0.03 * (claim - 1_000_000_000)
        elif claim <= 10_000_000_000:
            fee_3 = 178_000_000.0 + 0.02 * (claim - 5_000_000_000)
        elif claim <= 50_000_000_000:
            fee_3 = 278_000_000.0 + 0.005 * (claim - 10_000_000_000)
        else:
            fee_3 = 478_000_000.0 + 0.001 * (claim - 50_000_000_000)

        is_sole = tribunal_type == ArbitrationTribunalType.SOLE_ARBITRATOR
        final_fee = (fee_3 * 0.7) if is_sole else fee_3

        legal = "Biểu phí trọng tài VIAC 2024 (Hội đồng " + ("1 TTV giảm 30%" if is_sole else "3 TTV") + ")"
        return ViacFeeResult(
            claim_amount_vnd=claim,
            tribunal_type=tribunal_type,
            is_international=is_international,
            arbitration_fee_vnd=round(final_fee, 2),
            sole_discount_applied=is_sole,
            legal_basis=legal
        )

    @classmethod
    def check_limitation_period(
        cls,
        infringement_date_str: str,
        filing_date_str: Optional[str] = None
    ) -> ArbitrationLimitationStatus:
        """Kiểm tra thời hiệu khởi kiện trọng tài (02 năm theo Điều 33 Luật TTTM 2010)."""
        inf_date = datetime.strptime(infringement_date_str, "%Y-%m-%d").date()
        today = datetime.strptime(filing_date_str, "%Y-%m-%d").date() if filing_date_str else date.today()

        days_passed = max(0, (today - inf_date).days)
        is_within = days_passed <= cls.LIMITATION_PERIOD_DAYS
        rem_days = max(0, cls.LIMITATION_PERIOD_DAYS - days_passed)

        if is_within:
            advice = f"Còn trong thời hiệu khởi kiện trọng tài ({rem_days} ngày còn lại)."
        else:
            advice = f"HẾT THỜI HIỆU KHỞI KIỆN! Quá hạn {days_passed - cls.LIMITATION_PERIOD_DAYS} ngày theo Điều 33 Luật TTTM 2010."

        return ArbitrationLimitationStatus(
            infringement_date=infringement_date_str,
            filing_date=today.strftime("%Y-%m-%d"),
            days_passed=days_passed,
            is_within_limitation=is_within,
            remaining_days=rem_days,
            advice_vn=advice
        )


# ============================================================================
# 2. CIVIL JUDGMENT ENFORCEMENT ENGINE (Luật THADS 2008/2014)
# ============================================================================

@dataclass
class EnforcementLimitationStatus:
    effective_date: str
    request_date: str
    days_passed: int
    is_within_5_years: bool
    remaining_days: int
    statutory_notice: str


@dataclass
class EnforcementFeeResult:
    recovered_amount_vnd: float
    statutory_fee_rate_pct: float
    calculated_fee_vnd: float
    actual_fee_payable_vnd: float
    is_capped_at_200m: bool
    circular_basis: str


@dataclass
class PaymentPriorityDistribution:
    total_recovered_amount: float
    alimony_paid: float
    labor_paid: float
    court_fee_paid: float
    other_claims_paid: float
    remaining_surplus: float
    is_fully_satisfied: bool


class CivilEnforcementEngine:
    """Civil Judgment Enforcement & Asset Recovery Engine (Luật THADS 2014)."""

    # Thời hiệu yêu cầu thi hành án là 05 năm (1825 ngày) theo Điều 30
    ENFORCEMENT_LIMITATION_DAYS = 1825
    # Mức thu tối đa phí THADS theo Thông tư 216/2016/TT-BTC là 200.000.000 VNĐ
    MAX_ENFORCEMENT_FEE = 200_000_000.0

    @classmethod
    def check_enforcement_limitation(
        cls,
        effective_date_str: str,
        request_date_str: Optional[str] = None
    ) -> EnforcementLimitationStatus:
        """Kiểm tra thời hiệu 05 năm yêu cầu thi hành án dân sự (Điều 30 Luật THADS 2014)."""
        eff_date = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
        req_date = datetime.strptime(request_date_str, "%Y-%m-%d").date() if request_date_str else date.today()

        days_passed = max(0, (req_date - eff_date).days)
        is_within = days_passed <= cls.ENFORCEMENT_LIMITATION_DAYS
        rem_days = max(0, cls.ENFORCEMENT_LIMITATION_DAYS - days_passed)

        if is_within:
            notice = f"Trong thời hiệu 05 năm yêu cầu THADS (còn {rem_days} ngày)."
        else:
            notice = "QUÁ THỜI HIỆU 05 NĂM! Hết quyền yêu cầu THADS theo Điều 30 Luật THADS (trừ trường hợp bất khả kháng)."

        return EnforcementLimitationStatus(
            effective_date=effective_date_str,
            request_date=req_date.strftime("%Y-%m-%d"),
            days_passed=days_passed,
            is_within_5_years=is_within,
            remaining_days=rem_days,
            statutory_notice=notice
        )

    @classmethod
    def calculate_enforcement_fee(
        cls,
        recovered_amount_vnd: float
    ) -> EnforcementFeeResult:
        """
        Tính phí thi hành án dân sự theo Thông tư 216/2016/TT-BTC.
        Mức thu: 3% số tiền thực nhận, tối đa không quá 200.000.000 VNĐ.
        """
        recovered = max(0.0, recovered_amount_vnd)
        calc_fee = recovered * 0.03
        actual_fee = min(calc_fee, cls.MAX_ENFORCEMENT_FEE)
        is_capped = calc_fee >= cls.MAX_ENFORCEMENT_FEE

        return EnforcementFeeResult(
            recovered_amount_vnd=recovered,
            statutory_fee_rate_pct=3.0,
            calculated_fee_vnd=round(calc_fee, 2),
            actual_fee_payable_vnd=round(actual_fee, 2),
            is_capped_at_200m=is_capped,
            circular_basis="Thông tư 216/2016/TT-BTC (3%, trần tối đa 200 triệu VNĐ)"
        )

    @classmethod
    def distribute_payment_priority(
        cls,
        total_recovered_amount: float,
        alimony_due: float = 0.0,
        labor_salary_due: float = 0.0,
        court_fees_due: float = 0.0,
        other_claims_due: float = 0.0
    ) -> PaymentPriorityDistribution:
        """
        Thứ tự thanh toán tiền thi hành án theo Điều 47 Luật THADS 2014:
        1. Tiền cấp dưỡng
        2. Tiền lương, trợ cấp thôi việc
        3. Án phí, lệ phí Tòa án
        4. Các khoản nghĩa vụ thi hành án khác
        """
        available = max(0.0, total_recovered_amount)

        # 1. Cấp dưỡng
        paid_alimony = min(available, alimony_due)
        available -= paid_alimony

        # 2. Lương & trợ cấp
        paid_labor = min(available, labor_salary_due)
        available -= paid_labor

        # 3. Án phí
        paid_court = min(available, court_fees_due)
        available -= paid_court

        # 4. Các khoản khác
        paid_other = min(available, other_claims_due)
        available -= paid_other

        total_due = alimony_due + labor_salary_due + court_fees_due + other_claims_due
        total_paid = paid_alimony + paid_labor + paid_court + paid_other
        is_fully = total_paid >= total_due

        return PaymentPriorityDistribution(
            total_recovered_amount=total_recovered_amount,
            alimony_paid=round(paid_alimony, 2),
            labor_paid=round(paid_labor, 2),
            court_fee_paid=round(paid_court, 2),
            other_claims_paid=round(paid_other, 2),
            remaining_surplus=round(available, 2),
            is_fully_satisfied=is_fully
        )


# ============================================================================
# 3. COURT LITIGATION & CIVIL PROCEDURE (BLTTDS 2015 & NGHỊ QUYẾT 326/2016)
# ============================================================================

class CourtLevel(str, Enum):
    DISTRICT = "district"      # TAND cấp huyện
    PROVINCIAL = "provincial"  # TAND cấp tỉnh


@dataclass
class CourtJurisdictionResult:
    court_level: CourtLevel
    has_foreign_element: bool
    is_intellectual_property: bool
    is_maritime: bool
    competent_forum_vn: str
    legal_basis: str


@dataclass
class CourtFeeResult:
    claim_amount_vnd: float
    first_instance_fee_vnd: float
    advance_payment_vnd: float  # Tạm ứng 50%
    statutory_bracket_desc: str
    legal_basis: str


class CourtLitigationEngine:
    """Civil Procedure & Court Fee Calculation Engine (BLTTDS 2015 & NQ 326/2016)."""

    @classmethod
    def resolve_jurisdiction(
        cls,
        has_foreign_element: bool = False,
        is_intellectual_property: bool = False,
        is_maritime: bool = False,
        province: str = "TP. Hồ Chí Minh"
    ) -> CourtJurisdictionResult:
        """
        Phân định thẩm quyền Tòa án theo cấp (Điều 35 & Điều 37 BLTTDS 2015):
        - TAND cấp Tỉnh giải quyết sơ thẩm nếu có: đương sự/tài sản ở nước ngoài, tranh chấp SHTT, hoặc hàng hải.
        - TAND cấp Huyện giải quyết các tranh chấp còn lại.
        """
        if has_foreign_element or is_intellectual_property or is_maritime:
            level = CourtLevel.PROVINCIAL
            forum = f"Tòa án nhân dân {province} (Cấp Tỉnh)"
            reason = "Vụ án có yếu tố nước ngoài / SHTT / Hàng hải thuộc thẩm quyền sơ thẩm TAND cấp tỉnh (Điều 37 BLTTDS)."
        else:
            level = CourtLevel.DISTRICT
            forum = f"Tòa án nhân dân Quận/Huyện thuộc {province} (Cấp Huyện)"
            reason = "Tranh chấp dân sự/thương mại trong nước thuộc thẩm quyền sơ thẩm TAND cấp huyện (Điều 35 BLTTDS)."

        return CourtJurisdictionResult(
            court_level=level,
            has_foreign_element=has_foreign_element,
            is_intellectual_property=is_intellectual_property,
            is_maritime=is_maritime,
            competent_forum_vn=forum,
            legal_basis=reason
        )

    @classmethod
    def calculate_court_fee(
        cls,
        claim_amount_vnd: float
    ) -> CourtFeeResult:
        """
        Tính án phí sơ thẩm dân sự / kinh doanh thương mại có giá ngạch và tạm ứng án phí 50%
        theo Danh mục án phí ban hành kèm theo Nghị quyết số 326/2016/UBTVQH14.
        """
        claim = max(0.0, claim_amount_vnd)

        if claim <= 6_000_000:
            fee = 300_000.0
            desc = "Từ 6.000.000 VNĐ trở xuống: 300.000 VNĐ"
        elif claim <= 400_000_000:
            fee = 0.05 * claim
            desc = "Từ trên 6.000.000 đến 400.000.000 VNĐ: 5% giá trị tranh chấp"
        elif claim <= 800_000_000:
            fee = 20_000_000.0 + 0.04 * (claim - 400_000_000)
            desc = "Từ trên 400.000.000 đến 800.000.000 VNĐ: 20 triệu + 4% phần vượt 400 triệu"
        elif claim <= 2_000_000_000:
            fee = 36_000_000.0 + 0.03 * (claim - 800_000_000)
            desc = "Từ trên 800.000.000 đến 2 tỷ VNĐ: 36 triệu + 3% phần vượt 800 triệu"
        elif claim <= 4_000_000_000:
            fee = 72_000_000.0 + 0.02 * (claim - 2_000_000_000)
            desc = "Từ trên 2 tỷ đến 4 tỷ VNĐ: 72 triệu + 2% phần vượt 2 tỷ"
        else:
            fee = 112_000_000.0 + 0.001 * (claim - 4_000_000_000)
            desc = "Từ trên 4 tỷ VNĐ: 112 triệu + 0.1% phần vượt 4 tỷ"

        advance = fee * 0.5  # Tạm ứng án phí sơ thẩm 50% (Điều 7 Nghị quyết 326)

        return CourtFeeResult(
            claim_amount_vnd=claim,
            first_instance_fee_vnd=round(fee, 2),
            advance_payment_vnd=round(advance, 2),
            statutory_bracket_desc=desc,
            legal_basis="Nghị quyết số 326/2016/UBTVQH14 & Điều 144 BLTTDS 2015"
        )
