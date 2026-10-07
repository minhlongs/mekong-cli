"""
Autonomous Vietnamese International Trade, Multimodal Transport, Aviation & Trade Remedies Engine (Phases 163 - 166).

Compliant with:
- Phase 163: Multimodal Transport Operator (MTO) Liability under Nghị định 87/2009/NĐ-CP & NĐ 144/2018/NĐ-CP
- Phase 164: Civil Aviation Carrier Liability under Luật Hàng không dân dụng Việt Nam 2006/2014 & Montreal Convention 1999
- Phase 165: UN Convention on Contracts for the International Sale of Goods (CISG 1980) & Incoterms 2020 Rules
- Phase 166: Vietnamese Trade Remedies, Anti-Dumping & Countervailing Measures under Luật Quản lý ngoại thương 2017 & NĐ 10/2018/NĐ-CP

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, Optional


# ============================================================================
# Phase 163: Multimodal Transport (MTO) Dataclasses & Engine
# ============================================================================


@dataclass
class MTOLiabilityResult:
    packages_count: int
    gross_weight_kg: float
    actual_loss_vnd: float
    has_sea_or_waterway_leg: bool
    sdr_rate_vnd: float
    statutory_ceiling_sdr: float
    statutory_ceiling_vnd: float
    operator_payable_vnd: float
    is_limited: bool
    legal_basis: str


@dataclass
class MTODelayResult:
    freight_charge_vnd: float
    delay_loss_claimed_vnd: float
    statutory_ceiling_vnd: float
    payable_compensation_vnd: float
    is_capped_at_double_freight: bool
    legal_basis: str


@dataclass
class MTOLimitationStatus:
    delivery_date: str
    filing_date: str
    days_passed: int
    is_within_9_months: bool
    remaining_days: int
    advice_vn: str


class MultimodalTransportEngine:
    """Multimodal Transport Operator Liability Engine (Nghị định 87/2009/NĐ-CP)."""

    DEFAULT_SDR_VND_RATE = 34_500.0
    MTO_LIMITATION_DAYS = 270  # 09 tháng (Điều 29 NĐ 87/2009)

    @classmethod
    def calculate_unlocalized_loss_liability(
        cls,
        packages_count: int,
        gross_weight_kg: float,
        actual_loss_vnd: float,
        has_sea_or_waterway_leg: bool = True,
        sdr_rate_vnd: float = DEFAULT_SDR_VND_RATE,
    ) -> MTOLiabilityResult:
        """
        Tính giới hạn trách nhiệm bồi thường tổn thất không xác định được chặng
        theo Điều 24 Nghị định số 87/2009/NĐ-CP:
        - Nếu có chặng đường biển/đường thủy nội địa: Max(666.67 SDR/kiện, 2.0 SDR/kg).
        - Nếu không có chặng đường biển/đường thủy: 8.33 SDR/kg.
        """
        pkg = max(0, packages_count)
        weight = max(0.0, gross_weight_kg)
        loss = max(0.0, actual_loss_vnd)
        rate = max(1.0, sdr_rate_vnd)

        if has_sea_or_waterway_leg:
            pkg_sdr = pkg * 666.67
            weight_sdr = weight * 2.0
            applied_sdr = max(pkg_sdr, weight_sdr)
            basis = "Khoản 1 Điều 24 Nghị định 87/2009/NĐ-CP (Có chặng đường biển/thủy: Max 666.67 SDR/kiện hoặc 2.0 SDR/kg)"
        else:
            applied_sdr = weight * 8.33
            basis = "Khoản 2 Điều 24 Nghị định 87/2009/NĐ-CP (Không có chặng đường biển/thủy: 8.33 SDR/kg)"

        ceiling_vnd = applied_sdr * rate
        payable_vnd = min(loss, ceiling_vnd)
        is_limited = loss > ceiling_vnd

        return MTOLiabilityResult(
            packages_count=pkg,
            gross_weight_kg=weight,
            actual_loss_vnd=loss,
            has_sea_or_waterway_leg=has_sea_or_waterway_leg,
            sdr_rate_vnd=rate,
            statutory_ceiling_sdr=round(applied_sdr, 2),
            statutory_ceiling_vnd=round(ceiling_vnd, 2),
            operator_payable_vnd=round(payable_vnd, 2),
            is_limited=is_limited,
            legal_basis=basis,
        )

    @classmethod
    def calculate_delay_liability(
        cls,
        freight_charge_vnd: float,
        delay_loss_claimed_vnd: float,
    ) -> MTODelayResult:
        """
        Trách nhiệm bồi thường do chậm giao hàng theo Khoản 3 Điều 24 NĐ 87/2009:
        Giới hạn ở mức không vượt quá 2 lần tiền cước của số hàng giao chậm.
        """
        freight = max(0.0, freight_charge_vnd)
        loss = max(0.0, delay_loss_claimed_vnd)
        ceiling = freight * 2.0
        payable = min(loss, ceiling)
        is_capped = loss > ceiling

        return MTODelayResult(
            freight_charge_vnd=freight,
            delay_loss_claimed_vnd=loss,
            statutory_ceiling_vnd=round(ceiling, 2),
            payable_compensation_vnd=round(payable, 2),
            is_capped_at_double_freight=is_capped,
            legal_basis="Khoản 3 Điều 24 Nghị định 87/2009/NĐ-CP (Trần tối đa 2 lần tiền cước vận chuyển)",
        )

    @classmethod
    def check_claim_limitation(
        cls,
        delivery_date_str: str,
        filing_date_str: Optional[str] = None,
    ) -> MTOLimitationStatus:
        """Kiểm tra thời hiệu khởi kiện 09 tháng theo Điều 29 NĐ 87/2009/NĐ-CP."""
        deliv = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        today = datetime.strptime(filing_date_str, "%Y-%m-%d").date() if filing_date_str else date.today()

        days_passed = max(0, (today - deliv).days)
        is_within = days_passed <= cls.MTO_LIMITATION_DAYS
        rem_days = max(0, cls.MTO_LIMITATION_DAYS - days_passed)

        if is_within:
            advice = f"Còn trong thời hiệu 09 tháng khởi kiện vận tải đa phương thức (còn {rem_days} ngày)."
        else:
            advice = f"HẾT THỜI HIỆU KHỞI KIỆN! Quá hạn {days_passed - cls.MTO_LIMITATION_DAYS} ngày theo Điều 29 NĐ 87/2009/NĐ-CP."

        return MTOLimitationStatus(
            delivery_date=delivery_date_str,
            filing_date=today.strftime("%Y-%m-%d"),
            days_passed=days_passed,
            is_within_9_months=is_within,
            remaining_days=rem_days,
            advice_vn=advice,
        )


# ============================================================================
# Phase 164: Civil Aviation Carrier Liability Dataclasses & Engine
# ============================================================================


@dataclass
class AirPassengerInjuryResult:
    actual_damage_claimed_vnd: float
    sdr_rate_vnd: float
    tier1_strict_ceiling_sdr: float
    tier1_strict_ceiling_vnd: float
    carrier_payable_strict_vnd: float
    requires_carrier_fault_for_excess: bool
    advice_vn: str
    legal_basis: str


@dataclass
class AirCargoLiabilityResult:
    gross_weight_kg: float
    actual_loss_vnd: float
    sdr_rate_vnd: float
    cargo_limit_sdr: float
    statutory_ceiling_vnd: float
    carrier_payable_vnd: float
    is_limited: bool
    legal_basis: str


@dataclass
class AirBaggageDelayResult:
    claim_type: str  # "baggage" | "delay"
    passengers_count: int
    actual_loss_vnd: float
    sdr_rate_vnd: float
    statutory_limit_sdr: float
    statutory_ceiling_vnd: float
    carrier_payable_vnd: float
    is_limited: bool
    legal_basis: str


@dataclass
class AviationLimitationStatus:
    arrival_date: str
    action_date: str
    days_passed: int
    is_within_2_years: bool
    remaining_days: int
    advice_vn: str


class AirCarrierLiabilityEngine:
    """Vietnam Civil Aviation Code 2006/2014 & Montreal Convention 1999 Engine."""

    DEFAULT_SDR_VND_RATE = 34_500.0
    # Montreal Convention revised SDR limits (ICAO 2019 revision)
    PASSENGER_STRICT_INJURY_SDR = 128_821.0
    PASSENGER_DELAY_SDR = 5_346.0
    BAGGAGE_LIMIT_SDR = 1_288.0
    CARGO_PER_KG_SDR = 22.0
    AVIATION_LIMITATION_DAYS = 730  # 02 năm theo Điều 173 Luật HKDD 2006

    @classmethod
    def calculate_passenger_injury_liability(
        cls,
        actual_damage_claimed_vnd: float,
        sdr_rate_vnd: float = DEFAULT_SDR_VND_RATE,
    ) -> AirPassengerInjuryResult:
        """
        Tính bồi thường thiệt hại tính mạng, sức khỏe hành khách theo Điều 160 Luật HKDD:
        - Tầng 1: Trách nhiệm nghiêm ngặt đến 128,821 SDR (không phụ thuộc vào lỗi).
        - Tầng 2: Vượt quá 128,821 SDR nếu hãng không chứng minh được mình không có lỗi.
        """
        loss = max(0.0, actual_damage_claimed_vnd)
        rate = max(1.0, sdr_rate_vnd)
        tier1_vnd = cls.PASSENGER_STRICT_INJURY_SDR * rate

        strict_payable = min(loss, tier1_vnd)
        requires_fault = loss > tier1_vnd

        if requires_fault:
            advice = (
                f"Thiệt hại vượt hạn mức trách nhiệm nghiêm ngặt ({tier1_vnd:,.0f} VNĐ). "
                f"Hãng hàng không phải bồi thường toàn bộ {loss:,.0f} VNĐ trừ khi chứng minh được mình không có lỗi."
            )
        else:
            advice = "Thiệt hại nằm trong hạn mức trách nhiệm nghiêm ngặt (hãng bay chịu trách nhiệm vô điều kiện)."

        return AirPassengerInjuryResult(
            actual_damage_claimed_vnd=loss,
            sdr_rate_vnd=rate,
            tier1_strict_ceiling_sdr=cls.PASSENGER_STRICT_INJURY_SDR,
            tier1_strict_ceiling_vnd=round(tier1_vnd, 2),
            carrier_payable_strict_vnd=round(strict_payable, 2),
            requires_carrier_fault_for_excess=requires_fault,
            advice_vn=advice,
            legal_basis="Điều 160 Luật Hàng không dân dụng Việt Nam & Công ước Montreal 1999",
        )

    @classmethod
    def calculate_cargo_liability(
        cls,
        gross_weight_kg: float,
        actual_loss_vnd: float,
        sdr_rate_vnd: float = DEFAULT_SDR_VND_RATE,
    ) -> AirCargoLiabilityResult:
        """
        Tính bồi thường mất mát, hư hỏng hàng hóa vận chuyển đường hàng không
        theo Điều 166 Luật HKDD: Tối đa 22 SDR/kg trọng lượng cả bì.
        """
        weight = max(0.0, gross_weight_kg)
        loss = max(0.0, actual_loss_vnd)
        rate = max(1.0, sdr_rate_vnd)

        limit_sdr = weight * cls.CARGO_PER_KG_SDR
        ceiling_vnd = limit_sdr * rate
        payable = min(loss, ceiling_vnd)
        is_limited = loss > ceiling_vnd

        return AirCargoLiabilityResult(
            gross_weight_kg=weight,
            actual_loss_vnd=loss,
            sdr_rate_vnd=rate,
            cargo_limit_sdr=round(limit_sdr, 2),
            statutory_ceiling_vnd=round(ceiling_vnd, 2),
            carrier_payable_vnd=round(payable, 2),
            is_limited=is_limited,
            legal_basis="Điều 166 Luật Hàng không dân dụng Việt Nam & Công ước Montreal 1999 (22 SDR/kg)",
        )

    @classmethod
    def calculate_baggage_or_delay_liability(
        cls,
        claim_type: str,  # "baggage" | "delay"
        passengers_count: int,
        actual_loss_vnd: float,
        sdr_rate_vnd: float = DEFAULT_SDR_VND_RATE,
    ) -> AirBaggageDelayResult:
        """Tính bồi thường hành lý (1,288 SDR/khách) hoặc chậm chuyến (5,346 SDR/khách)."""
        count = max(1, passengers_count)
        loss = max(0.0, actual_loss_vnd)
        rate = max(1.0, sdr_rate_vnd)

        if claim_type.lower() == "delay":
            limit_sdr = count * cls.PASSENGER_DELAY_SDR
            basis = "Điều 162 Luật HKDD & Montreal 1999 (Chậm chuyến: 5,346 SDR/hành khách)"
        else:
            limit_sdr = count * cls.BAGGAGE_LIMIT_SDR
            basis = "Điều 166 Luật HKDD & Montreal 1999 (Hành lý: 1,288 SDR/hành khách)"

        ceiling_vnd = limit_sdr * rate
        payable = min(loss, ceiling_vnd)
        is_limited = loss > ceiling_vnd

        return AirBaggageDelayResult(
            claim_type=claim_type,
            passengers_count=count,
            actual_loss_vnd=loss,
            sdr_rate_vnd=rate,
            statutory_limit_sdr=round(limit_sdr, 2),
            statutory_ceiling_vnd=round(ceiling_vnd, 2),
            carrier_payable_vnd=round(payable, 2),
            is_limited=is_limited,
            legal_basis=basis,
        )

    @classmethod
    def check_aviation_claim_limitation(
        cls,
        arrival_date_str: str,
        action_date_str: Optional[str] = None,
    ) -> AviationLimitationStatus:
        """Kiểm tra thời hiệu khởi kiện 02 năm theo Điều 173 Luật HKDD 2006."""
        arr_date = datetime.strptime(arrival_date_str, "%Y-%m-%d").date()
        today = datetime.strptime(action_date_str, "%Y-%m-%d").date() if action_date_str else date.today()

        days = max(0, (today - arr_date).days)
        is_within = days <= cls.AVIATION_LIMITATION_DAYS
        rem = max(0, cls.AVIATION_LIMITATION_DAYS - days)

        if is_within:
            advice = f"Còn trong thời hiệu 02 năm khởi kiện hàng không dân dụng (còn {rem} ngày)."
        else:
            advice = f"HẾT THỜI HIỆU KHỞI KIỆN! Quá hạn {days - cls.AVIATION_LIMITATION_DAYS} ngày theo Điều 173 Luật HKDD."

        return AviationLimitationStatus(
            arrival_date=arrival_date_str,
            action_date=today.strftime("%Y-%m-%d"),
            days_passed=days,
            is_within_2_years=is_within,
            remaining_days=rem,
            advice_vn=advice,
        )


# ============================================================================
# Phase 165: CISG 1980 & Incoterms 2020 Dataclasses & Engine
# ============================================================================


class IncotermsGroup(str, Enum):
    ANY_MODE = "any_mode"        # EXW, FCA, CPT, CIP, DAP, DPU, DDP
    SEA_INLAND = "sea_inland"    # FAS, FOB, CFR, CIF


@dataclass
class FundamentalBreachResult:
    is_fundamental_breach: bool
    substantially_deprives_expectation: bool
    was_foreseeable_by_breaching_party: bool
    entitled_to_avoid_contract: bool
    advice_vn: str
    legal_basis: str


@dataclass
class CISGPriceReductionResult:
    agreed_contract_price_vnd: float
    value_of_delivered_goods_vnd: float
    value_if_conforming_vnd: float
    reduction_ratio_pct: float
    reduced_price_payable_vnd: float
    price_abatement_amount_vnd: float
    legal_basis: str


@dataclass
class IncotermsRuleDetail:
    code: str
    name_vn: str
    group: IncotermsGroup
    risk_transfer_point_vn: str
    mandatory_insurance: str
    carriage_contract_party: str
    advice_vn: str


class InternationalSalesIncotermsEngine:
    """CISG 1980 & ICC Incoterms 2020 Engine."""

    INCOTERMS_RULES: Dict[str, IncotermsRuleDetail] = {
        "EXW": IncotermsRuleDetail(
            code="EXW",
            name_vn="Giao tại xưởng (Ex Works)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Tại cơ sở của người bán khi hàng được đặt dưới quyền định đoạt của người mua",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người mua",
            advice_vn="Nghĩa vụ tối thiểu cho người bán. Người mua chịu mọi chi phí và rủi ro từ xưởng.",
        ),
        "FCA": IncotermsRuleDetail(
            code="FCA",
            name_vn="Giao cho người chuyên chở (Free Carrier)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Khi hàng được giao cho người chuyên chở do người mua chỉ định tại địa điểm chỉ định",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người mua",
            advice_vn="Phù hợp vận tải đa phương thức & container. Người bán làm thủ tục thông quan xuất khẩu.",
        ),
        "CPT": IncotermsRuleDetail(
            code="CPT",
            name_vn="Cước phí trả tới (Carriage Paid To)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Khi hàng được giao cho người chuyên chở đầu tiên",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người bán",
            advice_vn="Người bán trả cước vận tải đến điểm đến nhưng rủi ro chuyển giao ngay khi giao hàng cho người chuyên chở đầu tiên.",
        ),
        "CIP": IncotermsRuleDetail(
            code="CIP",
            name_vn="Cước phí và bảo hiểm trả tới (Carriage and Insurance Paid To)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Khi hàng được giao cho người chuyên chở đầu tiên",
            mandatory_insurance="BẮT BUỘC: Bảo hiểm Loại A (ICC A - All Risks) tối thiểu 110% giá trị hợp đồng",
            carriage_contract_party="Người bán",
            advice_vn="Người bán có nghĩa vụ mua bảo hiểm phạm vi tối đa (Loại A) theo Incoterms 2020.",
        ),
        "DAP": IncotermsRuleDetail(
            code="DAP",
            name_vn="Giao tại nơi đến (Delivered at Place)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Trên phương tiện vận tải sẵn sàng dỡ tại nơi đến chỉ định",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người bán",
            advice_vn="Người bán chịu rủi ro cho đến điểm đến. Người mua làm thủ tục nhập khẩu.",
        ),
        "DPU": IncotermsRuleDetail(
            code="DPU",
            name_vn="Giao tại địa điểm đã dỡ xuống (Delivered at Place Unloaded)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Sau khi hàng đã dỡ khỏi phương tiện vận tải tại nơi đến chỉ định",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người bán",
            advice_vn="Quy tắc duy nhất người bán có nghĩa vụ dỡ hàng khỏi phương tiện vận tải tại nơi đến.",
        ),
        "DDP": IncotermsRuleDetail(
            code="DDP",
            name_vn="Giao đã nộp thuế (Delivered Duty Paid)",
            group=IncotermsGroup.ANY_MODE,
            risk_transfer_point_vn="Tại nơi đến chỉ định, sẵn sàng dỡ và đã thông quan nhập khẩu",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người bán",
            advice_vn="Nghĩa vụ tối đa cho người bán. Người bán chịu thuế nhập khẩu và mọi thủ tục hải quan nước đến.",
        ),
        "FAS": IncotermsRuleDetail(
            code="FAS",
            name_vn="Giao dọc mạn tàu (Free Alongside Ship)",
            group=IncotermsGroup.SEA_INLAND,
            risk_transfer_point_vn="Khi hàng được đặt dọc mạn tàu tại cảng bốc hàng chỉ định",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người mua",
            advice_vn="Chỉ dùng cho vận tải đường biển/đường thủy nội địa. Phù hợp hàng rời, hàng xơ nang.",
        ),
        "FOB": IncotermsRuleDetail(
            code="FOB",
            name_vn="Giao trên tàu (Free On Board)",
            group=IncotermsGroup.SEA_INLAND,
            risk_transfer_point_vn="Khi hàng đã được xếp an toàn trên tàu tại cảng bốc hàng chỉ định",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người mua",
            advice_vn="Rủi ro chuyển giao khi hàng nằm trên tàu. Phù hợp xuất khẩu nông sản, khoáng sản đường biển.",
        ),
        "CFR": IncotermsRuleDetail(
            code="CFR",
            name_vn="Tiền hàng và cước phí (Cost and Freight)",
            group=IncotermsGroup.SEA_INLAND,
            risk_transfer_point_vn="Khi hàng đã xếp trên tàu tại cảng bốc",
            mandatory_insurance="Không bắt buộc",
            carriage_contract_party="Người bán",
            advice_vn="Người bán trả cước đường biển đến cảng đến nhưng rủi ro chuyển giao ngay khi hàng qua lan can tàu tại cảng bốc.",
        ),
        "CIF": IncotermsRuleDetail(
            code="CIF",
            name_vn="Tiền hàng, bảo hiểm và cước phí (Cost, Insurance and Freight)",
            group=IncotermsGroup.SEA_INLAND,
            risk_transfer_point_vn="Khi hàng đã xếp trên tàu tại cảng bốc",
            mandatory_insurance="BẮT BUỘC: Bảo hiểm Loại C (ICC C - Rủi ro tối thiểu) tối thiểu 110% giá trị hợp đồng",
            carriage_contract_party="Người bán",
            advice_vn="Người bán mua bảo hiểm tối thiểu (Loại C) trừ khi các bên có thỏa thuận mua bảo hiểm cao hơn.",
        ),
    }

    @classmethod
    def evaluate_fundamental_breach(
        cls,
        substantially_deprives_expectation: bool,
        was_foreseeable: bool = True,
    ) -> FundamentalBreachResult:
        """
        Đánh giá vi phạm cơ bản hợp đồng theo Điều 25 Công ước CISG 1980:
        Hành vi vi phạm tước bỏ đáng kể lợi ích kỳ vọng của bên bị vi phạm,
        trừ khi bên vi phạm không lường trước được hậu quả đó.
        """
        is_fundamental = substantially_deprives_expectation and was_foreseeable

        if is_fundamental:
            advice = "Xác định vi phạm cơ bản (Fundamental Breach). Bên bị vi phạm có quyền tuyên bố HỦY HỢP ĐỒNG (Avoidance) theo Điều 49 hoặc 64 CISG."
        elif substantially_deprives_expectation and not was_foreseeable:
            advice = "Thiệt hại tước bỏ lợi ích kỳ vọng nhưng bên vi phạm KHÔNG THỂ LƯỜNG TRƯỚC: Không cấu thành vi phạm cơ bản."
        else:
            advice = "Vi phạm thông thường, không tước bỏ đáng kể lợi ích kỳ vọng: Chỉ được quyền yêu cầu bồi thường thiệt hại, không được hủy hợp đồng."

        return FundamentalBreachResult(
            is_fundamental_breach=is_fundamental,
            substantially_deprives_expectation=substantially_deprives_expectation,
            was_foreseeable_by_breaching_party=was_foreseeable,
            entitled_to_avoid_contract=is_fundamental,
            advice_vn=advice,
            legal_basis="Điều 25 Công ước Viên 1980 (CISG) về Vi phạm cơ bản",
        )

    @classmethod
    def calculate_cisg_price_reduction(
        cls,
        agreed_contract_price_vnd: float,
        value_of_delivered_goods_vnd: float,
        value_if_conforming_vnd: float,
    ) -> CISGPriceReductionResult:
        """
        Tính giảm giá hàng hóa khi hàng không phù hợp hợp đồng theo Điều 50 CISG:
        P_thực_trả = P_thỏa_thuận * (Giá trị thực tế / Giá trị chuẩn).
        """
        price = max(0.0, agreed_contract_price_vnd)
        v_deliv = max(0.0, value_of_delivered_goods_vnd)
        v_conf = max(1.0, value_if_conforming_vnd)

        ratio = min(1.0, v_deliv / v_conf)
        reduced_price = price * ratio
        abatement = price - reduced_price

        return CISGPriceReductionResult(
            agreed_contract_price_vnd=price,
            value_of_delivered_goods_vnd=v_deliv,
            value_if_conforming_vnd=v_conf,
            reduction_ratio_pct=round(ratio * 100.0, 4),
            reduced_price_payable_vnd=round(reduced_price, 2),
            price_abatement_amount_vnd=round(abatement, 2),
            legal_basis="Điều 50 Công ước Viên 1980 (CISG) về Giảm giá hàng",
        )

    @classmethod
    def lookup_incoterms_rule(cls, term: str) -> Optional[IncotermsRuleDetail]:
        """Tra cứu chi tiết điều kiện Incoterms 2020."""
        return cls.INCOTERMS_RULES.get(term.upper().strip())


# ============================================================================
# Phase 166: Vietnamese Trade Remedies Dataclasses & Engine
# ============================================================================


@dataclass
class DumpingMarginResult:
    normal_value_vnd: float
    export_price_vnd: float
    dumping_margin_pct: float
    is_de_minimis: bool
    is_subject_to_anti_dumping: bool
    advice_vn: str
    legal_basis: str


@dataclass
class TradeRemedyApplicationAssessment:
    exporting_country: str
    dumping_margin_pct: float
    import_volume_share_pct: float
    is_volume_negligible: bool
    can_impose_duty: bool
    maximum_duty_rate_pct: float
    max_duration_years: int
    advice_vn: str
    legal_basis: str


@dataclass
class SafeguardSurgeResult:
    base_import_quantity: float
    current_import_quantity: float
    surge_rate_pct: float
    is_substantial_increase: bool
    advice_vn: str
    legal_basis: str


class TradeRemediesEngine:
    """Vietnamese Foreign Trade Management Law 2017 & Trade Remedies Engine."""

    # Ngưỡng biên độ bán phá giá tối thiểu (De Minimis) theo Điều 78 Luật QLNT: 2.0%
    DE_MINIMIS_DUMPING_MARGIN_PCT = 2.0
    # Ngưỡng khối lượng nhập khẩu không đáng kể từ 1 nước theo Điều 78: 3.0%
    NEGLIGIBLE_IMPORT_VOLUME_SHARE_PCT = 3.0
    # Thời hạn áp dụng thuế chống bán phá giá tối đa: 5 năm (Điều 82)
    MAX_DUTY_DURATION_YEARS = 5

    @classmethod
    def calculate_dumping_margin(
        cls,
        normal_value_vnd: float,
        export_price_vnd: float,
    ) -> DumpingMarginResult:
        """
        Tính biên độ bán phá giá (Dumping Margin) theo Điều 77 Luật QLNT 2017:
        DM = ((NV - EP) / EP) * 100%.
        """
        nv = max(0.0, normal_value_vnd)
        ep = max(1.0, export_price_vnd)

        margin = max(0.0, (nv - ep) / ep * 100.0)
        is_de_minimis = margin < cls.DE_MINIMIS_DUMPING_MARGIN_PCT
        subject_to_ad = not is_de_minimis

        if is_de_minimis:
            advice = (
                f"Biên độ bán phá giá ({margin:.2f}%) dưới ngưỡng tối thiểu 2.0% (De Minimis). "
                "Không áp dụng biện pháp chống bán phá giá theo Điều 78 Luật QLNT 2017."
            )
        else:
            advice = (
                f"Biên độ bán phá giá đạt {margin:.2f}% (>= 2.0%). Đủ điều kiện xem xét áp thuế "
                "chống bán phá giá theo Điều 77, 78 Luật QLNT 2017."
            )

        return DumpingMarginResult(
            normal_value_vnd=nv,
            export_price_vnd=ep,
            dumping_margin_pct=round(margin, 2),
            is_de_minimis=is_de_minimis,
            is_subject_to_anti_dumping=subject_to_ad,
            advice_vn=advice,
            legal_basis="Điều 77 & 78 Luật Quản lý ngoại thương 2017",
        )

    @classmethod
    def assess_anti_dumping_application(
        cls,
        exporting_country: str,
        dumping_margin_pct: float,
        import_volume_share_pct: float,
    ) -> TradeRemedyApplicationAssessment:
        """
        Đánh giá điều kiện áp dụng thuế chống bán phá giá đối với hàng hóa nhập khẩu
        theo Điều 78 & 82 Luật QLNT 2017.
        """
        dm = max(0.0, dumping_margin_pct)
        vol_share = max(0.0, import_volume_share_pct)

        is_de_minimis = dm < cls.DE_MINIMIS_DUMPING_MARGIN_PCT
        is_negligible_vol = vol_share < cls.NEGLIGIBLE_IMPORT_VOLUME_SHARE_PCT

        can_impose = (not is_de_minimis) and (not is_negligible_vol)
        max_rate = dm if can_impose else 0.0

        if not can_impose:
            reasons = []
            if is_de_minimis:
                reasons.append("Biên độ phá giá < 2.0%")
            if is_negligible_vol:
                reasons.append("Khối lượng nhập khẩu < 3.0% tổng nhập khẩu")
            advice = f"KHÔNG ĐƯỢC ÁP THUẾ CHỐNG BÁN PHÁ GIÁ: {', '.join(reasons)}."
        else:
            advice = (
                f"ĐỦ ĐIỀU KIỆN ÁP THUẾ CHỐNG BÁN PHÁ GIÁ: Mức thuế không vượt quá biên độ phá giá "
                f"({dm:.2f}%), thời hạn áp dụng tối đa 05 năm."
            )

        return TradeRemedyApplicationAssessment(
            exporting_country=exporting_country,
            dumping_margin_pct=dm,
            import_volume_share_pct=vol_share,
            is_volume_negligible=is_negligible_vol,
            can_impose_duty=can_impose,
            maximum_duty_rate_pct=round(max_rate, 2),
            max_duration_years=cls.MAX_DUTY_DURATION_YEARS,
            advice_vn=advice,
            legal_basis="Điều 78, 81 & 82 Luật Quản lý ngoại thương 2017 & Nghị định 10/2018/NĐ-CP",
        )

    @classmethod
    def assess_safeguard_surge(
        cls,
        base_import_quantity: float,
        current_import_quantity: float,
        threshold_surge_rate_pct: float = 30.0,
    ) -> SafeguardSurgeResult:
        """
        Đánh giá mức độ gia tăng hàng hóa nhập khẩu phục vụ điều tra tự vệ (Safeguards)
        theo Điều 88 Luật QLNT 2017.
        """
        base = max(1.0, base_import_quantity)
        curr = max(0.0, current_import_quantity)

        surge_rate = ((curr - base) / base) * 100.0
        is_substantial = surge_rate >= threshold_surge_rate_pct

        if is_substantial:
            advice = f"Hàng hóa nhập khẩu gia tăng đột biến (+{surge_rate:.2f}% >= {threshold_surge_rate_pct}%). Đủ căn cứ xem xét áp dụng biện pháp tự vệ (Điều 88)."
        else:
            advice = f"Mức gia tăng nhập khẩu (+{surge_rate:.2f}%) chưa đủ điều kiện cấu thành gia tăng đột biến gây thiệt hại nghiêm trọng."

        return SafeguardSurgeResult(
            base_import_quantity=base,
            current_import_quantity=curr,
            surge_rate_pct=round(surge_rate, 2),
            is_substantial_increase=is_substantial,
            advice_vn=advice,
            legal_basis="Điều 88 & 91 Luật Quản lý ngoại thương 2017 về Biện pháp Tự vệ",
        )
