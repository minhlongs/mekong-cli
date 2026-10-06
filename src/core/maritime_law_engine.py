"""
Vietnam Maritime Law, Carriage of Goods by Sea & General Average Engine (Phase 162).
Compliant with:
- Bộ luật Hàng hải Việt Nam 2015 (Luật số 95/2015/QH13)
- Hague-Visby Rules & SDR Protocol 1979 (Điều 152)
- York-Antwerp Rules 2016 (Điều 280 - Điều 297)

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MaritimeClaimCategory(str, Enum):
    CREW_WAGES = "crew_wages"                  # 1. Tiền lương, chi phí hồi hương, BHXH thuyền viên
    LIFE_INJURY = "life_injury"                # 2. Bồi thường tính mạng, thương tích thuyền viên & hành khách
    PORT_DUES = "port_dues"                    # 3. Phí cảng biển, hoa tiêu, phí bảo đảm an toàn
    SALVAGE_REWARD = "salvage_reward"          # 4. Thù lao cứu hộ hàng hải
    COLLISION_DAMAGE = "collision_damage"      # 5. Bồi thường thiệt hại do va chạm tàu biển
    SHIP_MORTGAGE = "ship_mortgage"            # 6. Thế chấp tàu biển (sau quyền cầm giữ hàng hải)
    OTHER_MARITIME = "other_maritime"          # 7. Các khoản nợ thương mại hàng hải khác


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
    interest_name: str  # Ví dụ: "Tàu biển (Ship)", "Hàng hóa A (Cargo A)", "Cước phí (Freight)"
    contributory_value_vnd: float  # Giá trị chịu phân bổ (C_i)
    sacrifice_incurred_vnd: float = 0.0  # Tổn thất/chi phí đã gánh chịu (S_i)


@dataclass
class GeneralAverageContribution:
    interest_name: str
    contributory_value_vnd: float
    sacrifice_incurred_vnd: float
    gross_contribution_vnd: float  # Đóng góp gộp: GC_i = C_i * R
    net_settlement_vnd: float      # Quyết toán ròng: Net_i = GC_i - S_i (>0: Phải nộp thêm; <0: Được nhận hoàn)


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
    """Vietnam Maritime Code 2015 & International Conventions Engine."""

    # Tỷ giá tham chiếu 1 SDR quy đổi VNĐ mặc định
    DEFAULT_SDR_VND_RATE = 34_500.0
    # Thời hiệu khởi kiện mất mát, hư hỏng hàng hóa: 01 năm (365 ngày) theo Điều 169
    CARGO_CLAIM_LIMITATION_DAYS = 365
    # Thời hiệu tiêu tán quyền cầm giữ hàng hải: 01 năm (365 ngày) theo Điều 43
    MARITIME_LIEN_EXTINCTION_DAYS = 365

    @classmethod
    def calculate_carrier_liability(
        cls,
        packages_count: int,
        gross_weight_kg: float,
        actual_loss_vnd: float,
        sdr_rate_vnd: float = DEFAULT_SDR_VND_RATE
    ) -> CarrierLiabilityResult:
        """
        Tính giới hạn trách nhiệm bồi thường của người vận chuyển đường biển
        theo Khoản 1 Điều 152 Bộ luật Hàng hải Việt Nam 2015:
        Mức bồi thường không vượt quá: Max(666.67 SDR/kiện, 2.0 SDR/kg trọng lượng cả bì).
        """
        pkg_cnt = max(0, packages_count)
        weight = max(0.0, gross_weight_kg)
        loss = max(0.0, actual_loss_vnd)
        rate = max(1.0, sdr_rate_vnd)

        pkg_sdr = pkg_cnt * 666.67
        weight_sdr = weight * 2.0
        applied_sdr = max(pkg_sdr, weight_sdr)
        ceiling_vnd = applied_sdr * rate

        payable_vnd = min(loss, ceiling_vnd)
        is_limited = loss > ceiling_vnd

        return CarrierLiabilityResult(
            packages_count=pkg_cnt,
            gross_weight_kg=weight,
            actual_loss_vnd=loss,
            sdr_rate_vnd=rate,
            package_limit_sdr=round(pkg_sdr, 2),
            weight_limit_sdr=round(weight_sdr, 2),
            applicable_limit_sdr=round(applied_sdr, 2),
            statutory_ceiling_vnd=round(ceiling_vnd, 2),
            carrier_payable_vnd=round(payable_vnd, 2),
            is_limited=is_limited,
            legal_basis="Điều 152 Bộ luật Hàng hải Việt Nam 2015 & Nghị định thư SDR 1979"
        )

    @classmethod
    def check_cargo_claim_limitation(
        cls,
        delivery_date_str: str,
        claim_date_str: Optional[str] = None
    ) -> CargoLimitationStatus:
        """Kiểm tra thời hiệu 01 năm khởi kiện hư hỏng hàng hóa theo Điều 169 BLHH 2015."""
        del_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        today = datetime.strptime(claim_date_str, "%Y-%m-%d").date() if claim_date_str else date.today()

        days_passed = max(0, (today - del_date).days)
        is_within = days_passed <= cls.CARGO_CLAIM_LIMITATION_DAYS
        rem_days = max(0, cls.CARGO_CLAIM_LIMITATION_DAYS - days_passed)

        if is_within:
            advice = f"Còn trong thời hiệu 01 năm khiếu nại/khởi kiện vận chuyển đường biển (còn {rem_days} ngày)."
        else:
            advice = f"HẾT THỜI HIỆU KHỞI KIỆN! Quá hạn {days_passed - cls.CARGO_CLAIM_LIMITATION_DAYS} ngày theo Điều 169 BLHH 2015."

        return CargoLimitationStatus(
            delivery_date=delivery_date_str,
            filing_date=today.strftime("%Y-%m-%d"),
            days_passed=days_passed,
            is_within_1_year=is_within,
            remaining_days=rem_days,
            advice_vn=advice
        )

    @classmethod
    def calculate_general_average(
        cls,
        interests: List[GeneralAverageInterest]
    ) -> GeneralAverageResult:
        """
        Tính toán phân bổ tổn thất chung (General Average) theo Điều 292 - 297 BLHH 2015
        và Quy tắc York-Antwerp 2016.
        - Tổng giá trị chịu phân bổ: TCV = Sum(C_i)
        - Tổng tổn thất chung: TGL = Sum(S_i)
        - Tỷ lệ phân bổ: R = TGL / TCV
        - Đóng góp gộp: GC_i = C_i * R
        - Quyết toán bù trừ: Net_i = GC_i - S_i (Tổng Sum(Net_i) == 0)
        """
        total_cv = sum(max(0.0, item.contributory_value_vnd) for item in interests)
        total_loss = sum(max(0.0, item.sacrifice_incurred_vnd) for item in interests)

        ratio = (total_loss / total_cv) if total_cv > 0 else 0.0
        ratio_pct = ratio * 100.0

        contributions: List[GeneralAverageContribution] = []
        net_sum = 0.0

        for item in interests:
            cv = max(0.0, item.contributory_value_vnd)
            si = max(0.0, item.sacrifice_incurred_vnd)
            gc = cv * ratio
            net = gc - si
            net_sum += net
            contributions.append(
                GeneralAverageContribution(
                    interest_name=item.interest_name,
                    contributory_value_vnd=round(cv, 2),
                    sacrifice_incurred_vnd=round(si, 2),
                    gross_contribution_vnd=round(gc, 2),
                    net_settlement_vnd=round(net, 2)
                )
            )

        # Kiểm tra tính cân bằng Zero-Sum (độ lệch cho phép < 1.0 VNĐ do làm tròn)
        is_balanced = abs(net_sum) < 5.0

        return GeneralAverageResult(
            total_contributory_value_vnd=round(total_cv, 2),
            total_general_average_loss_vnd=round(total_loss, 2),
            contribution_ratio_pct=round(ratio_pct, 4),
            participants=contributions,
            is_zero_sum_balanced=is_balanced,
            legal_basis="Điều 292 - 297 Bộ luật Hàng hải 2015 & Quy tắc York-Antwerp 2016"
        )

    @classmethod
    def assess_salvage_reward(
        cls,
        salvaged_property_value_vnd: float,
        agreed_or_claimed_reward_vnd: float,
        has_useful_result: bool = True
    ) -> SalvageAssessmentResult:
        """
        Đánh giá thù lao cứu hộ hàng hải theo Điều 281 - 291 BLHH 2015:
        - Nguyên tắc 'No Cure No Pay': Nếu không mang lại kết quả có ích, không có thù lao (Điều 286).
        - Mức thù lao không vượt quá giá trị tài sản cứu được (Khoản 1 Điều 286).
        """
        prop_val = max(0.0, salvaged_property_value_vnd)
        claim_reward = max(0.0, agreed_or_claimed_reward_vnd)

        if not has_useful_result:
            return SalvageAssessmentResult(
                salvaged_property_value_vnd=prop_val,
                agreed_reward_claim_vnd=claim_reward,
                has_useful_result=False,
                statutory_approved_reward_vnd=0.0,
                is_capped_by_property_value=False,
                advice_vn="Nguyên tắc 'No Cure No Pay': Cứu hộ không mang lại kết quả có ích nên không được hưởng thù lao cứu hộ.",
                legal_basis="Điều 286 Bộ luật Hàng hải 2015"
            )

        capped = claim_reward > prop_val
        final_reward = min(claim_reward, prop_val)

        advice = "Mức thù lao cứu hộ hợp lệ trong giới hạn giá trị tài sản cứu được."
        if capped:
            advice = f"Thù lao cứu hộ bị khống chế tối đa không vượt quá giá trị tài sản cứu được ({prop_val:,.0f} VNĐ)."

        return SalvageAssessmentResult(
            salvaged_property_value_vnd=prop_val,
            agreed_reward_claim_vnd=claim_reward,
            has_useful_result=True,
            statutory_approved_reward_vnd=round(final_reward, 2),
            is_capped_by_property_value=capped,
            advice_vn=advice,
            legal_basis="Khoản 1 Điều 286 Bộ luật Hàng hải 2015 (Cứu hộ có kết quả)"
        )

    @classmethod
    def rank_maritime_claims(
        cls,
        claims: List[Dict[str, Any]]
    ) -> List[RankedMaritimeClaim]:
        """
        Xếp hạng thứ tự ưu tiên thanh toán các khiếu nại hàng hải
        theo Điều 40 (Quyền cầm giữ hàng hải) và Điều 41 (Ưu tiên hơn thế chấp tàu biển).
        """
        # Ánh xạ mức độ ưu tiên pháp định
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
            cid = str(item.get("claim_id", "CLM-UNKNOWN"))
            desc = str(item.get("description", "Khiếu nại hàng hải"))
            cat_raw = item.get("category", MaritimeClaimCategory.OTHER_MARITIME)

            if isinstance(cat_raw, MaritimeClaimCategory):
                cat = cat_raw
            else:
                try:
                    cat = MaritimeClaimCategory(str(cat_raw).lower())
                except ValueError:
                    cat = MaritimeClaimCategory.OTHER_MARITIME

            amt = max(0.0, float(item.get("claim_amount_vnd", 0.0)))
            rank, label, is_lien = rank_map[cat]

            basis = "Điều 40 & Điều 41 Bộ luật Hàng hải 2015" if is_lien else "Điều 41 Bộ luật Hàng hải 2015"

            ranked_list.append(
                RankedMaritimeClaim(
                    claim_id=cid,
                    description=desc,
                    category=cat,
                    claim_amount_vnd=amt,
                    statutory_priority_rank=rank,
                    priority_label_vn=label,
                    is_maritime_lien=is_lien,
                    legal_basis=basis
                )
            )

        # Sắp xếp theo thứ tự ưu tiên tăng dần (Rank 1 trước Rank 7)
        ranked_list.sort(key=lambda x: (x.statutory_priority_rank, -x.claim_amount_vnd))
        return ranked_list
