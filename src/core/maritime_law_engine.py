"""Vietnam Maritime Law, Carriage of Goods by Sea & General Average Engine (Phase 162)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MaritimeClaimCategory(str, Enum):
    CREW_WAGES = "crew_wages"
    LIFE_INJURY = "life_injury"
    PORT_DUES = "port_dues"
    SALVAGE_REWARD = "salvage_reward"
    COLLISION_DAMAGE = "collision_damage"
    SHIP_MORTGAGE = "ship_mortgage"
    OTHER_MARITIME = "other_maritime"


@dataclass
class CarrierLiabilityResult:
    packages_count: int
    gross_weight_kg: float
    actual_loss_vnd: float
    sdr_rate_vnd: float
    package_limit_sdr: float
    weight_limit_sdr: float
    applicable_limit_sdr: float
    statutory_ceiling_vnd: float
    carrier_payable_vnd: float
    is_limited: bool
    legal_basis: str


@dataclass
class CargoLimitationStatus:
    delivery_date: str
    filing_date: str
    days_passed: int
    is_within_1_year: bool
    remaining_days: int
    advice_vn: str


@dataclass
class GeneralAverageInterest:
    interest_name: str
    contributory_value_vnd: float
    sacrifice_incurred_vnd: float = 0.0


@dataclass
class GeneralAverageContribution:
    interest_name: str
    contributory_value_vnd: float
    sacrifice_incurred_vnd: float
    gross_contribution_vnd: float
    net_settlement_vnd: float


@dataclass
class GeneralAverageResult:
    total_contributory_value_vnd: float
    total_general_average_loss_vnd: float
    contribution_ratio_pct: float
    participants: List[GeneralAverageContribution]
    is_zero_sum_balanced: bool
    legal_basis: str


@dataclass
class SalvageAssessmentResult:
    salvaged_property_value_vnd: float
    agreed_reward_claim_vnd: float
    has_useful_result: bool
    statutory_approved_reward_vnd: float
    is_capped_by_property_value: bool
    advice_vn: str
    legal_basis: str


@dataclass
class RankedMaritimeClaim:
    claim_id: str
    description: str
    category: MaritimeClaimCategory
    claim_amount_vnd: float
    statutory_priority_rank: int
    priority_label_vn: str
    is_maritime_lien: bool
    legal_basis: str


class MaritimeLawEngine:
    DEFAULT_SDR_VND_RATE = 34_500.0
    CARGO_CLAIM_LIMITATION_DAYS = 365
    MARITIME_LIEN_EXTINCTION_DAYS = 365

    @classmethod
    def calculate_carrier_liability(cls, packages_count: int, gross_weight_kg: float, actual_loss_vnd: float, sdr_rate_vnd: float = DEFAULT_SDR_VND_RATE) -> CarrierLiabilityResult:
        pkg_cnt, weight, loss, rate = max(0, packages_count), max(0.0, gross_weight_kg), max(0.0, actual_loss_vnd), max(1.0, sdr_rate_vnd)
        pkg_sdr, weight_sdr = pkg_cnt * 666.67, weight * 2.0
        applied_sdr = max(pkg_sdr, weight_sdr)
        ceiling_vnd = applied_sdr * rate
        return CarrierLiabilityResult(
            pkg_cnt, weight, loss, rate, round(pkg_sdr, 2), round(weight_sdr, 2), round(applied_sdr, 2),
            round(ceiling_vnd, 2), round(min(loss, ceiling_vnd), 2), loss > ceiling_vnd,
            "Điều 152 Bộ luật Hàng hải Việt Nam 2015 & Nghị định thư SDR 1979",
        )

    @classmethod
    def check_cargo_claim_limitation(cls, delivery_date_str: str, claim_date_str: Optional[str] = None) -> CargoLimitationStatus:
        del_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        today = datetime.strptime(claim_date_str, "%Y-%m-%d").date() if claim_date_str else date.today()
        days_passed = max(0, (today - del_date).days)
        is_within, rem_days = days_passed <= cls.CARGO_CLAIM_LIMITATION_DAYS, max(0, cls.CARGO_CLAIM_LIMITATION_DAYS - days_passed)
        advice = f"Còn trong thời hiệu 01 năm khiếu nại/khởi kiện vận chuyển đường biển (còn {rem_days} ngày)." if is_within else f"HẾT THỜI HIỆU KHỞI KIỆN! Quá hạn {days_passed - cls.CARGO_CLAIM_LIMITATION_DAYS} ngày theo Điều 169 BLHH 2015."
        return CargoLimitationStatus(delivery_date_str, today.strftime("%Y-%m-%d"), days_passed, is_within, rem_days, advice)

    @classmethod
    def calculate_general_average(cls, interests: List[GeneralAverageInterest]) -> GeneralAverageResult:
        total_cv = sum(max(0.0, item.contributory_value_vnd) for item in interests)
        total_loss = sum(max(0.0, item.sacrifice_incurred_vnd) for item in interests)
        ratio = (total_loss / total_cv) if total_cv > 0 else 0.0
        contributions, net_sum = [], 0.0
        for item in interests:
            cv, si = max(0.0, item.contributory_value_vnd), max(0.0, item.sacrifice_incurred_vnd)
            gc, net = cv * ratio, (cv * ratio) - si
            net_sum += net
            contributions.append(GeneralAverageContribution(item.interest_name, round(cv, 2), round(si, 2), round(gc, 2), round(net, 2)))
        return GeneralAverageResult(round(total_cv, 2), round(total_loss, 2), round(ratio * 100.0, 4), contributions, abs(net_sum) < 5.0, "Điều 292 - 297 Bộ luật Hàng hải 2015 & Quy tắc York-Antwerp 2016")

    @classmethod
    def assess_salvage_reward(cls, salvaged_property_value_vnd: float, agreed_or_claimed_reward_vnd: float, has_useful_result: bool = True) -> SalvageAssessmentResult:
        prop_val, claim_reward = max(0.0, salvaged_property_value_vnd), max(0.0, agreed_or_claimed_reward_vnd)
        if not has_useful_result:
            return SalvageAssessmentResult(prop_val, claim_reward, False, 0.0, False, "Nguyên tắc 'No Cure No Pay': Cứu hộ không mang lại kết quả có ích nên không được hưởng thù lao cứu hộ.", "Điều 286 Bộ luật Hàng hải 2015")
        capped = claim_reward > prop_val
        advice = f"Thù lao cứu hộ bị khống chế tối đa không vượt quá giá trị tài sản cứu được ({prop_val:,.0f} VNĐ)." if capped else "Mức thù lao cứu hộ hợp lệ trong giới hạn giá trị tài sản cứu được."
        return SalvageAssessmentResult(prop_val, claim_reward, True, round(min(claim_reward, prop_val), 2), capped, advice, "Khoản 1 Điều 286 Bộ luật Hàng hải 2015 (Cứu hộ có kết quả)")

    @classmethod
    def rank_maritime_claims(cls, claims: List[Dict[str, Any]]) -> List[RankedMaritimeClaim]:
        rank_map = {
            MaritimeClaimCategory.CREW_WAGES: (1, "Ưu tiên Hạng 1: Tiền lương, chi phí hồi hương, BHXH thuyền viên", True),
            MaritimeClaimCategory.LIFE_INJURY: (2, "Ưu tiên Hạng 2: Bồi thường tính mạng, thương tích", True),
            MaritimeClaimCategory.PORT_DUES: (3, "Ưu tiên Hạng 3: Phí cảng biển, hoa tiêu, phí bảo đảm an toàn", True),
            MaritimeClaimCategory.SALVAGE_REWARD: (4, "Ưu tiên Hạng 4: Thù lao cứu hộ hàng hải", True),
            MaritimeClaimCategory.COLLISION_DAMAGE: (5, "Ưu tiên Hạng 5: Bồi thường thiệt hại va chạm tàu biển", True),
            MaritimeClaimCategory.SHIP_MORTGAGE: (6, "Ưu tiên Hạng 6: Thế chấp tàu biển (sau quyền cầm giữ)", False),
            MaritimeClaimCategory.OTHER_MARITIME: (7, "Ưu tiên Hạng 7: Nghĩa vụ thương mại hàng hải thông thường khác", False),
        }
        ranked_list: List[RankedMaritimeClaim] = []
        for item in claims:
            cat_raw = item.get("category", MaritimeClaimCategory.OTHER_MARITIME)
            try:
                cat = cat_raw if isinstance(cat_raw, MaritimeClaimCategory) else MaritimeClaimCategory(str(cat_raw).lower())
            except ValueError:
                cat = MaritimeClaimCategory.OTHER_MARITIME
            amt = max(0.0, float(item.get("claim_amount_vnd", 0.0)))
            rank, label, is_lien = rank_map[cat]
            basis = "Điều 40 & Điều 41 Bộ luật Hàng hải 2015" if is_lien else "Điều 41 Bộ luật Hàng hải 2015"
            ranked_list.append(RankedMaritimeClaim(str(item.get("claim_id", "CLM-UNKNOWN")), str(item.get("description", "Khiếu nại hàng hải")), cat, amt, rank, label, is_lien, basis))
        ranked_list.sort(key=lambda x: (x.statutory_priority_rank, -x.claim_amount_vnd))
        return ranked_list
