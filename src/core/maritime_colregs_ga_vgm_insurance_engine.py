"""Core Engines for Maritime COLREGs, General Average, Container VGM & Marine Insurance.

Phases 319-322 Simplest Viable Maritime Operational Suite.
- Phase 319: COLREGs 1972 Collision Prevention & CPA/TCPA Assessment Engine (Rules 7, 8, 13-17).
- Phase 320: York-Antwerp Rules 2016 General Average Adjustment & Contribution Engine (YAR 2016).
- Phase 321: SOLAS VI/2 Container Verified Gross Mass (VGM) Safety Engine (TT 41/2016/TT-BGTVT).
- Phase 322: Institute Time Clauses - Hulls (ITC-Hulls 1/10/83) Marine Insurance Settlement Engine.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
import math
from typing import Any, Dict, List


# ==============================================================================
# Phase 319: COLREGs 1972 Collision Prevention & Risk of Collision Engine
# ==============================================================================

class EncounterSituation(str, Enum):
    HEAD_ON = "HEAD_ON"                    # Rule 14: Đối đầu trực diện
    CROSSING_GIVE_WAY = "CROSSING_GIVE_WAY"# Rule 15: Cắt hướng - Tàu phải nhường đường (Mục tiêu bên mạn phải)
    CROSSING_STAND_ON = "CROSSING_STAND_ON"# Rule 15/17: Cắt hướng - Tàu giữ hướng (Mục tiêu bên mạn trái)
    OVERTAKING_GIVE_WAY = "OVERTAKING_GIVE_WAY" # Rule 13: Đang vượt tàu khác - Phải tránh đường
    OVERTAKEN_STAND_ON = "OVERTAKEN_STAND_ON"   # Rule 13: Bị tàu khác vượt - Giữ hướng & tốc độ
    SAFE_PASSING = "SAFE_PASSING"          # An toàn, không có nguy cơ đâm va


class ColregsActionObligation(str, Enum):
    GIVE_WAY = "GIVE_WAY"                  # Rule 16: Chủ động đổi hướng/tốc độ sớm và rõ ràng
    STAND_ON = "STAND_ON"                  # Rule 17: Giữ nguyên hướng đi và tốc độ
    MUTUAL_STARBOARD = "MUTUAL_STARBOARD"  # Rule 14: Cả 2 tàu cùng đổi hướng sang phải (Starboard)
    NONE_REQUIRED = "NONE_REQUIRED"        # Không cần điều động khẩn cấp


@dataclass
class ColregsTargetInput:
    own_vessel_name: str
    own_course_deg: float      # Hướng đi tàu mình (0-359 độ)
    own_speed_knots: float     # Tốc độ tàu mình (hải lý/giờ)
    target_vessel_name: str
    target_bearing_deg: float  # Phương vị thật tới tàu mục tiêu (0-359 độ)
    target_range_nm: float     # Khoảng cách tới tàu mục tiêu (hải lý)
    target_course_deg: float   # Hướng đi tàu mục tiêu (0-359 độ)
    target_speed_knots: float  # Tốc độ tàu mục tiêu (hải lý/giờ)
    safe_cpa_distance_nm: float = 1.5  # Khoảng cách an toàn tối thiểu (NM)
    safe_tcpa_time_min: float = 20.0   # Thời gian cảnh báo va chạm tối thiểu (phút)


@dataclass
class ColregsAssessmentResult:
    own_vessel_name: str
    target_vessel_name: str
    relative_bearing_deg: float
    cpa_distance_nm: float
    tcpa_minutes: float
    risk_of_collision: bool
    situation: EncounterSituation
    action_obligation: ColregsActionObligation
    recommended_maneuver: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "own_vessel_name": self.own_vessel_name,
            "target_vessel_name": self.target_vessel_name,
            "relative_bearing_deg": round(self.relative_bearing_deg, 1),
            "cpa_distance_nm": round(self.cpa_distance_nm, 2),
            "tcpa_minutes": round(self.tcpa_minutes, 1),
            "risk_of_collision": self.risk_of_collision,
            "situation": self.situation.value,
            "action_obligation": self.action_obligation.value,
            "recommended_maneuver": self.recommended_maneuver,
            "audit_hash": self.audit_hash,
        }


class ColregsNavigationEngine:
    """COLREGs 1972 Rules 7, 8, 13, 14, 15, 16, 17 Real-time Collision Risk Evaluator."""

    @classmethod
    def evaluate_encounter(cls, inp: ColregsTargetInput) -> ColregsAssessmentResult:
        # 1. Tính relative bearing từ tàu mình tới mục tiêu
        rel_bearing = (inp.target_bearing_deg - inp.own_course_deg) % 360.0
        if rel_bearing > 180.0:
            rel_bearing_signed = rel_bearing - 360.0  # -180 đến +180
        else:
            rel_bearing_signed = rel_bearing

        # 2. Véc tơ vận tốc riêng và tương đối trong hệ tọa độ cực Cartesien (X=East, Y=North)
        rad_own_course = math.radians(inp.own_course_deg)
        rad_tgt_course = math.radians(inp.target_course_deg)
        rad_bearing = math.radians(inp.target_bearing_deg)

        vox = inp.own_speed_knots * math.sin(rad_own_course)
        voy = inp.own_speed_knots * math.cos(rad_own_course)

        vtx = inp.target_speed_knots * math.sin(rad_tgt_course)
        vty = inp.target_speed_knots * math.cos(rad_tgt_course)

        # Vận tốc tương đối của mục tiêu đối với tàu mình: Vr = Vt - Vo
        vrx = vtx - vox
        vry = vty - voy
        relative_speed = math.sqrt(vrx**2 + vry**2)

        # Tọa độ tương đối của mục tiêu ban đầu
        px = inp.target_range_nm * math.sin(rad_bearing)
        py = inp.target_range_nm * math.cos(rad_bearing)

        # 3. Tính CPA và TCPA
        if relative_speed < 0.05:
            # Hai tàu giữ cùng vận tốc và hướng song song
            cpa_nm = inp.target_range_nm
            tcpa_min = 0.0
        else:
            # Thời gian đến CPA (giờ) = -(P . Vr) / |Vr|^2
            dot_p_vr = px * vrx + py * vry
            tcpa_hours = -dot_p_vr / (relative_speed**2)
            tcpa_min = tcpa_hours * 60.0

            if tcpa_hours > 0:
                # Vị trí tại thời điểm CPA
                cpa_x = px + vrx * tcpa_hours
                cpa_y = py + vry * tcpa_hours
                cpa_nm = math.sqrt(cpa_x**2 + cpa_y**2)
            else:
                # Đang xa dần nhau (opening)
                cpa_nm = inp.target_range_nm

        # 4. Xác định nguy cơ va chạm (Rule 7)
        risk = (
            tcpa_min > 0.0
            and tcpa_min <= inp.safe_tcpa_time_min
            and cpa_nm < inp.safe_cpa_distance_nm
            and inp.target_range_nm <= 12.0
        )

        # 5. Phân loại tình huống (Rules 13, 14, 15)
        # Góc nhìn hướng đi tương đối (difference of courses)
        course_diff = abs(inp.own_course_deg - inp.target_course_deg)
        if course_diff > 180.0:
            course_diff = 360.0 - course_diff

        # Xác định góc mạn đối với tàu mục tiêu để xét quy tắc vượt (Rule 13)
        # Góc từ đuôi tàu mục tiêu: phương vị ngược là (inp.target_bearing_deg + 180) % 360
        back_bearing = (inp.target_bearing_deg + 180.0) % 360.0
        aspect_on_target = (back_bearing - inp.target_course_deg) % 360.0
        if aspect_on_target > 180.0:
            aspect_on_target -= 360.0

        situation = EncounterSituation.SAFE_PASSING
        obligation = ColregsActionObligation.NONE_REQUIRED
        recommendation = "Không có nguy cơ va chạm. Duy trì cảnh giới thường xuyên."

        if not risk and cpa_nm >= inp.safe_cpa_distance_nm:
            situation = EncounterSituation.SAFE_PASSING
            obligation = ColregsActionObligation.NONE_REQUIRED
            recommendation = f"CPA an toàn ({cpa_nm:.2f} NM). Tiếp tục hành trình và giữ cảnh giới thị giác, radar."
        else:
            # Có nguy cơ đâm va, kiểm tra các tình huống
            # Tình huống 1: Tàu mình đang vượt mục tiêu (Rule 13: own ship overtaking)
            if abs(aspect_on_target) > 112.5 and inp.own_speed_knots > inp.target_speed_knots:
                situation = EncounterSituation.OVERTAKING_GIVE_WAY
                obligation = ColregsActionObligation.GIVE_WAY
                recommendation = "Rule 13: Tàu mình là tàu vượt, phải chủ động giữ khoảng cách xa và nhường đường hoàn toàn cho tàu bị vượt."

            # Tình huống 2: Mục tiêu đang vượt tàu mình (Rule 13: target overtaking own ship)
            elif abs(rel_bearing_signed) > 112.5 and inp.target_speed_knots > inp.own_speed_knots:
                situation = EncounterSituation.OVERTAKEN_STAND_ON
                obligation = ColregsActionObligation.STAND_ON
                recommendation = "Rule 13/17: Tàu mình đang bị vượt. Giữ nguyên hướng và tốc độ, theo dõi sát hành động của tàu vượt."

            # Tình huống 3: Tình huống đối đầu trực diện (Rule 14: Head-on situation)
            elif abs(rel_bearing_signed) <= 6.0 and course_diff >= 170.0:
                situation = EncounterSituation.HEAD_ON
                obligation = ColregsActionObligation.MUTUAL_STARBOARD
                recommendation = "Rule 14: Đối đầu trực diện! CẢ HAI TÀU PHẢI ĐỔI HƯỚNG SANG PHẢI (Alter course to starboard) để mạn trái đi qua nhau."

            # Tình huống 4: Cắt hướng - Tàu mình nhường đường (Rule 15: Crossing - Give-way, mục tiêu bên mạn phải)
            elif 0.0 < rel_bearing < 112.5:
                situation = EncounterSituation.CROSSING_GIVE_WAY
                obligation = ColregsActionObligation.GIVE_WAY
                recommendation = "Rule 15/16: Tàu mục tiêu nằm bên MẠN PHẢI! Tàu mình là GIVE-WAY, phải chủ động chuyển hướng sang phải rõ ràng và sớm, tránh cắt mũi tàu kia."

            # Tình huống 5: Cắt hướng - Tàu mình giữ hướng (Rule 15/17: Crossing - Stand-on, mục tiêu bên mạn trái)
            elif 247.5 <= rel_bearing < 360.0 or -112.5 < rel_bearing_signed < 0.0:
                situation = EncounterSituation.CROSSING_STAND_ON
                obligation = ColregsActionObligation.STAND_ON
                recommendation = "Rule 15/17: Tàu mục tiêu nằm bên MẠN TRÁI! Tàu mình là STAND-ON, giữ nguyên hướng và tốc độ. Sẵn sàng điều động tự tránh nếu tàu kia không nhường."

            else:
                situation = EncounterSituation.CROSSING_GIVE_WAY
                obligation = ColregsActionObligation.GIVE_WAY
                recommendation = "Quy tắc an toàn hàng hải: Chủ động điều động tránh xa mục tiêu sớm và quyết đoán."

        payload = f"{inp.own_vessel_name}:{inp.target_vessel_name}:{cpa_nm:.3f}:{tcpa_min:.1f}:{situation.value}:{obligation.value}"
        audit_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        return ColregsAssessmentResult(
            own_vessel_name=inp.own_vessel_name,
            target_vessel_name=inp.target_vessel_name,
            relative_bearing_deg=rel_bearing,
            cpa_distance_nm=cpa_nm,
            tcpa_minutes=tcpa_min,
            risk_of_collision=risk,
            situation=situation,
            action_obligation=obligation,
            recommended_maneuver=recommendation,
            audit_hash=audit_hash
        )


# ==============================================================================
# Phase 320: York-Antwerp Rules 2016 General Average Adjustment Engine
# ==============================================================================

class GaInterestParty(str, Enum):
    SHIPOWNER = "SHIPOWNER"          # Chủ tàu
    CARGO_OWNER = "CARGO_OWNER"      # Chủ hàng
    CHARTERER = "CHARTERER"          # Người thuê tàu / Cước phí


@dataclass
class GaContributoryItem:
    item_id: str
    party: GaInterestParty
    name: str
    sound_value_usd: float          # Giá trị nguyên vẹn ban đầu
    non_ga_damage_deduction_usd: float # Tổn thất riêng trừ ra
    ga_sacrifice_amount_usd: float   # Thiệt hại hy sinh vì tổn thất chung (được tính gộp vào giá trị chịu phân bổ)
    ga_direct_expenditure_usd: float # Chi phí trực tiếp đã chi cho tổn thất chung

    @property
    def net_contributory_value(self) -> float:
        # Giá trị chịu phân bổ = Giá trị nguyên vẹn - Tổn thất riêng + Hy sinh tổn thất chung
        val = self.sound_value_usd - self.non_ga_damage_deduction_usd + self.ga_sacrifice_amount_usd
        return max(0.0, val)

    @property
    def total_ga_allowance(self) -> float:
        # Tổng số tiền được bồi hoàn trong GA = Hy sinh + Chi phí bỏ ra
        return self.ga_sacrifice_amount_usd + self.ga_direct_expenditure_usd


@dataclass
class GaSettlementItem:
    item_id: str
    party: str
    name: str
    contributory_value_usd: float
    contribution_payable_usd: float  # Số tiền phải đóng góp vào quỹ GA
    ga_allowance_receivable_usd: float # Số tiền được bù đắp từ quỹ GA
    net_balance_usd: float           # Dương (+): Được nhận tiền; Âm (-): Phải trả thêm tiền


@dataclass
class GaAdjustmentResult:
    incident_ref: str
    total_contributory_value_usd: float
    total_ga_loss_usd: float
    ga_contribution_rate_pct: float
    settlements: List[GaSettlementItem]
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_ref": self.incident_ref,
            "total_contributory_value_usd": round(self.total_contributory_value_usd, 2),
            "total_ga_loss_usd": round(self.total_ga_loss_usd, 2),
            "ga_contribution_rate_pct": round(self.ga_contribution_rate_pct, 4),
            "settlements": [
                {
                    "item_id": s.item_id,
                    "party": s.party,
                    "name": s.name,
                    "contributory_value_usd": round(s.contributory_value_usd, 2),
                    "contribution_payable_usd": round(s.contribution_payable_usd, 2),
                    "ga_allowance_receivable_usd": round(s.ga_allowance_receivable_usd, 2),
                    "net_balance_usd": round(s.net_balance_usd, 2),
                }
                for s in self.settlements
            ],
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class GeneralAverageAdjustmentEngine:
    """York-Antwerp Rules 2016 & Vietnam Maritime Code Arts 292-297 General Average Engine."""

    @classmethod
    def calculate_adjustment(
        cls,
        incident_ref: str,
        items: List[GaContributoryItem]
    ) -> GaAdjustmentResult:
        if not items:
            raise ValueError("Danh sách tài sản phân bổ tổn thất chung không được để trống.")

        # 1. Tổng giá trị chịu phân bổ (Total Contributory Value)
        total_contributory_val = sum(it.net_contributory_value for it in items)
        if total_contributory_val <= 0:
            raise ValueError("Tổng giá trị tài sản chịu phân bổ tổn thất chung phải lớn hơn 0.")

        # 2. Tổng thiệt hại và chi phí tổn thất chung (Total GA Losses)
        total_ga_losses = sum(it.total_ga_allowance for it in items)

        # 3. Tỷ lệ đóng góp tổn thất chung (GA Contribution Rate)
        ga_rate = total_ga_losses / total_contributory_val

        # 4. Tính toán phân bổ và bù trừ công nợ cho từng bên
        settlements: List[GaSettlementItem] = []
        for it in items:
            cv = it.net_contributory_value
            payable = cv * ga_rate
            receivable = it.total_ga_allowance
            net_bal = receivable - payable

            settlements.append(
                GaSettlementItem(
                    item_id=it.item_id,
                    party=it.party.value,
                    name=it.name,
                    contributory_value_usd=cv,
                    contribution_payable_usd=payable,
                    ga_allowance_receivable_usd=receivable,
                    net_balance_usd=net_bal
                )
            )

        remarks = (
            f"Tuyên bố Tổn thất chung {incident_ref} theo York-Antwerp Rules 2016. "
            f"Tổng quỹ tổn thất: ${total_ga_losses:,.2f} USD | "
            f"Tỷ lệ phân bổ đóng góp: {ga_rate * 100:.3f}%"
        )
        payload = f"{incident_ref}:{total_contributory_val:.2f}:{total_ga_losses:.2f}:{ga_rate:.6f}"
        audit_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        return GaAdjustmentResult(
            incident_ref=incident_ref,
            total_contributory_value_usd=total_contributory_val,
            total_ga_loss_usd=total_ga_losses,
            ga_contribution_rate_pct=ga_rate * 100.0,
            settlements=settlements,
            remarks=remarks,
            audit_hash=audit_hash
        )


# ==============================================================================
# Phase 321: SOLAS VI/2 Container Verified Gross Mass (VGM) Safety Engine
# ==============================================================================

class VgmMethod(str, Enum):
    METHOD_1 = "METHOD_1"  # Cân toàn bộ container đã đóng hàng & bấm chì
    METHOD_2 = "METHOD_2"  # Cân từng kiện hàng + chèn lót bao bì + vỏ cont (Tare)


@dataclass
class ContainerVgmInput:
    container_no: str
    booking_no: str
    vgm_method: VgmMethod
    tare_weight_kg: float         # Trọng lượng vỏ container rỗng (Tare)
    max_gross_weight_kg: float    # Trọng lượng tối đa cho phép của cont (MGW)
    declared_vgm_kg: float        # Trọng lượng VGM được khai báo trong chứng từ
    terminal_scale_weight_kg: float # Trọng lượng thực cân tại cổng cảng (Gate-in)
    weighing_cert_verified: bool = True
    dunnage_packaging_kg: float = 0.0


@dataclass
class ContainerVgmResult:
    container_no: str
    booking_no: str
    vgm_method: VgmMethod
    declared_vgm_kg: float
    terminal_scale_weight_kg: float
    tare_weight_kg: float
    max_payload_kg: float
    actual_net_cargo_kg: float
    weight_variance_kg: float
    weight_variance_pct: float
    within_tolerance: bool
    is_overweight: bool
    is_loading_permitted: bool
    rejection_reasons: List[str]
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_no": self.container_no,
            "booking_no": self.booking_no,
            "vgm_method": self.vgm_method.value,
            "declared_vgm_kg": round(self.declared_vgm_kg, 1),
            "terminal_scale_weight_kg": round(self.terminal_scale_weight_kg, 1),
            "tare_weight_kg": round(self.tare_weight_kg, 1),
            "max_payload_kg": round(self.max_payload_kg, 1),
            "actual_net_cargo_kg": round(self.actual_net_cargo_kg, 1),
            "weight_variance_kg": round(self.weight_variance_kg, 1),
            "weight_variance_pct": round(self.weight_variance_pct, 2),
            "within_tolerance": self.within_tolerance,
            "is_overweight": self.is_overweight,
            "is_loading_permitted": self.is_loading_permitted,
            "rejection_reasons": self.rejection_reasons,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class ContainerVgmComplianceEngine:
    """SOLAS Chapter VI Reg 2 & Circular 41/2016/TT-BGTVT Container VGM Compliance Engine."""

    # Dung sai tối đa theo quy định hàng hải quốc tế & Bộ GTVT
    TOLERANCE_PCT_LIMIT = 5.0     # Sai số tối đa cho phép là 5%
    MAX_ABSOLUTE_VARIANCE_KG = 1000.0 # Hoặc tối đa 1000 kg

    @classmethod
    def verify_vgm(cls, inp: ContainerVgmInput) -> ContainerVgmResult:
        rejections: List[str] = []

        max_payload = inp.max_gross_weight_kg - inp.tare_weight_kg
        actual_net_cargo = inp.declared_vgm_kg - inp.tare_weight_kg

        # 1. Kiểm tra tính hợp lệ của chứng nhận cân
        if not inp.weighing_cert_verified:
            rejections.append("Không có chứng chỉ/phiếu cân điện tử hợp lệ (Missing certified scale certificate).")

        # 2. Kiểm tra vượt tải trọng tối đa (Overweight)
        is_overweight = False
        if inp.declared_vgm_kg > inp.max_gross_weight_kg:
            is_overweight = True
            rejections.append(
                f"VGM khai báo ({inp.declared_vgm_kg:,.0f} kg) vượt quá tải trọng thiết kế MGW ({inp.max_gross_weight_kg:,.0f} kg)."
            )

        if inp.terminal_scale_weight_kg > inp.max_gross_weight_kg:
            is_overweight = True
            rejections.append(
                f"Trọng lượng cân tại cổng cảng ({inp.terminal_scale_weight_kg:,.0f} kg) vượt quá MGW ({inp.max_gross_weight_kg:,.0f} kg)."
            )

        # 3. Kiểm tra độ lệch trọng lượng giữa VGM khai báo và Cân thực tế tại cảng
        variance_kg = inp.terminal_scale_weight_kg - inp.declared_vgm_kg
        abs_variance = abs(variance_kg)
        variance_pct = (abs_variance / inp.declared_vgm_kg) * 100.0 if inp.declared_vgm_kg > 0 else 100.0

        within_tolerance = True
        if variance_pct > cls.TOLERANCE_PCT_LIMIT or abs_variance > cls.MAX_ABSOLUTE_VARIANCE_KG:
            within_tolerance = False
            rejections.append(
                f"Độ lệch trọng lượng thực cân ({abs_variance:,.1f} kg, {variance_pct:.1f}%) vượt ngưỡng dung sai cho phép (5% hoặc 1,000 kg)."
            )

        # 4. Kiểm tra điều kiện xếp hàng lên tàu ("NO VGM, NO LOAD")
        permitted = (len(rejections) == 0) and within_tolerance and not is_overweight

        if permitted:
            remarks = (
                f"Container {inp.container_no} ĐẠT CHUẨN VGM SOLAS VI/2. "
                f"Dung sai {variance_pct:.2f}% trong ngưỡng hợp lệ. Đủ điều kiện xếp hàng lên tàu."
            )
        else:
            remarks = (
                f"CẤM XẾP HÀNG LÊN TÀU (NO VGM, NO LOAD) đối với container {inp.container_no}. "
                f"Lý do vi phạm: {'; '.join(rejections)}"
            )

        payload = f"{inp.container_no}:{inp.booking_no}:{inp.declared_vgm_kg}:{inp.terminal_scale_weight_kg}:{permitted}"
        audit_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        return ContainerVgmResult(
            container_no=inp.container_no,
            booking_no=inp.booking_no,
            vgm_method=inp.vgm_method,
            declared_vgm_kg=inp.declared_vgm_kg,
            terminal_scale_weight_kg=inp.terminal_scale_weight_kg,
            tare_weight_kg=inp.tare_weight_kg,
            max_payload_kg=max_payload,
            actual_net_cargo_kg=actual_net_cargo,
            weight_variance_kg=variance_kg,
            weight_variance_pct=variance_pct,
            within_tolerance=within_tolerance,
            is_overweight=is_overweight,
            is_loading_permitted=permitted,
            rejection_reasons=rejections,
            remarks=remarks,
            audit_hash=audit_hash
        )


# ==============================================================================
# Phase 322: Institute Time Clauses - Hulls (ITC-Hulls 1/10/83) Claim Engine
# ==============================================================================

class HullLossType(str, Enum):
    ACTUAL_TOTAL_LOSS = "ACTUAL_TOTAL_LOSS"            # Tổn thất toàn bộ thực tế (ATL)
    CONSTRUCTIVE_TOTAL_LOSS = "CONSTRUCTIVE_TOTAL_LOSS"# Tổn thất toàn bộ ước tính (CTL)
    PARTICULAR_AVERAGE = "PARTICULAR_AVERAGE"          # Tổn thất bộ phận thân tàu
    COLLISION_LIABILITY_3_4 = "COLLISION_LIABILITY_3_4"# Trách nhiệm đâm va 3/4 RDC (Clause 8)


@dataclass
class ItcHullsClaimInput:
    claim_id: str
    vessel_name: str
    agreed_insured_value_usd: float    # Giá trị bảo hiểm thỏa thuận trong đơn
    repair_costs_usd: float            # Chi phí sửa chữa dự kiến/thực tế
    salvage_recovery_costs_usd: float  # Chi phí trục vớt, cứu nạn kéo tàu về xưởng
    third_party_collision_damage_usd: float = 0.0 # Thiệt hại gây ra cho tàu khác trong vụ đâm va
    policy_deductible_usd: float = 25000.0        # Mức khấu trừ theo Hợp đồng (Clause 12)
    sue_and_labour_costs_usd: float = 0.0         # Chi phí đề phòng & hạn chế tổn thất (Clause 13)
    is_actual_total_loss: bool = False             # Tàu chìm đắm hoàn toàn không thể cứu vãn


@dataclass
class ItcHullsClaimResult:
    claim_id: str
    vessel_name: str
    loss_classification: HullLossType
    agreed_insured_value_usd: float
    total_physical_repair_usd: float
    hull_insurer_payout_usd: float       # Số tiền Bảo hiểm Thân tàu bồi thường
    deductible_applied_usd: float        # Mức khấu trừ đã áp dụng
    rdc_hull_3_4_payout_usd: float       # Bồi thường 3/4 RDC từ bảo hiểm thân tàu
    rdc_pni_1_4_liability_usd: float     # Trách nhiệm 1/4 RDC chuyển giao cho P&I Club
    sue_and_labour_payout_usd: float     # Bồi thường chi phí hạn chế tổn thất
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "vessel_name": self.vessel_name,
            "loss_classification": self.loss_classification.value,
            "agreed_insured_value_usd": round(self.agreed_insured_value_usd, 2),
            "total_physical_repair_usd": round(self.total_physical_repair_usd, 2),
            "hull_insurer_payout_usd": round(self.hull_insurer_payout_usd, 2),
            "deductible_applied_usd": round(self.deductible_applied_usd, 2),
            "rdc_hull_3_4_payout_usd": round(self.rdc_hull_3_4_payout_usd, 2),
            "rdc_pni_1_4_liability_usd": round(self.rdc_pni_1_4_liability_usd, 2),
            "sue_and_labour_payout_usd": round(self.sue_and_labour_payout_usd, 2),
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class ItcHullsClaimEngine:
    """ITC-Hulls 1/10/83 & Vietnam Maritime Code Arts 304-315 Marine Insurance Claim Engine."""

    @classmethod
    def calculate_claim_settlement(cls, inp: ItcHullsClaimInput) -> ItcHullsClaimResult:
        # 1. Kiểm tra điều kiện Tổn thất toàn bộ thực tế (ATL)
        if inp.is_actual_total_loss:
            loss_type = HullLossType.ACTUAL_TOTAL_LOSS
            hull_payout = inp.agreed_insured_value_usd
            deductible = 0.0  # Không áp dụng deductible cho tổn thất toàn bộ
            rdc_hull = 0.0
            rdc_pni = 0.0
            sue_labour = min(inp.sue_and_labour_costs_usd, inp.agreed_insured_value_usd)
            remarks = (
                f"Tổn thất toàn bộ thực tế (Actual Total Loss). "
                f"Bồi thường 100% Giá trị bảo hiểm (${inp.agreed_insured_value_usd:,.0f} USD). Miễn khấu trừ."
            )

        else:
            # 2. Kiểm tra điều kiện Tổn thất toàn bộ ước tính (CTL - Constructive Total Loss)
            # Theo Clause 19 ITC-Hulls 1/10/83: Chi phí trục vớt + sửa chữa >= Giá trị bảo hiểm
            total_recovery_and_repair = inp.repair_costs_usd + inp.salvage_recovery_costs_usd

            if total_recovery_and_repair >= inp.agreed_insured_value_usd:
                loss_type = HullLossType.CONSTRUCTIVE_TOTAL_LOSS
                hull_payout = inp.agreed_insured_value_usd
                deductible = 0.0  # Không áp dụng deductible cho CTL
                rdc_hull = 0.0
                rdc_pni = 0.0
                sue_labour = min(inp.sue_and_labour_costs_usd, inp.agreed_insured_value_usd)
                remarks = (
                    f"Tuyên bố Tổn thất toàn bộ ước tính (Constructive Total Loss - CTL). "
                    f"Chi phí cứu vớt + sửa chữa (${total_recovery_and_repair:,.0f} USD) >= Giá trị bảo hiểm. Miễn khấu trừ."
                )

            else:
                # 3. Tổn thất bộ phận (Particular Average) & Trách nhiệm đâm va 3/4 RDC (Clause 8)
                # Bồi thường thiệt hại thân tàu: Chi phí sửa chữa - Mức khấu trừ
                net_repair = max(0.0, inp.repair_costs_usd - inp.policy_deductible_usd)
                deductible = min(inp.policy_deductible_usd, inp.repair_costs_usd)

                # Phân bổ trách nhiệm đâm va bên thứ ba 3/4 RDC (Clause 8)
                # 3/4 do bảo hiểm thân tàu bồi thường (tối đa bằng 3/4 Giá trị bảo hiểm)
                max_rdc_hull_cap = 0.75 * inp.agreed_insured_value_usd
                rdc_hull = min(0.75 * inp.third_party_collision_damage_usd, max_rdc_hull_cap)
                # 1/4 còn lại thuộc P&I Club
                rdc_pni = 0.25 * inp.third_party_collision_damage_usd

                # Sue and Labour (Clause 13)
                sue_labour = min(inp.sue_and_labour_costs_usd, inp.agreed_insured_value_usd)

                hull_payout = net_repair + rdc_hull + sue_labour

                if inp.third_party_collision_damage_usd > 0:
                    loss_type = HullLossType.COLLISION_LIABILITY_3_4
                    remarks = (
                        f"Tổn thất bộ phận có trách nhiệm đâm va (3/4 RDC). "
                        f"Thân tàu bồi thường sửa chữa (trừ khấu trừ ${deductible:,.0f}) + 3/4 trách nhiệm đâm va (${rdc_hull:,.0f}). "
                        f"Phần 1/4 (${rdc_pni:,.0f} USD) chuyển giao Hội P&I."
                    )
                else:
                    loss_type = HullLossType.PARTICULAR_AVERAGE
                    remarks = (
                        f"Bồi thường tổn thất bộ phận thân tàu (Particular Average). "
                        f"Chi phí sửa chữa hợp lý ${inp.repair_costs_usd:,.0f} USD - Khấu trừ ${deductible:,.0f} USD."
                    )

        payload = f"{inp.claim_id}:{inp.vessel_name}:{loss_type.value}:{hull_payout:.2f}:{rdc_hull:.2f}:{rdc_pni:.2f}"
        audit_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        return ItcHullsClaimResult(
            claim_id=inp.claim_id,
            vessel_name=inp.vessel_name,
            loss_classification=loss_type,
            agreed_insured_value_usd=inp.agreed_insured_value_usd,
            total_physical_repair_usd=inp.repair_costs_usd,
            hull_insurer_payout_usd=hull_payout,
            deductible_applied_usd=deductible,
            rdc_hull_3_4_payout_usd=rdc_hull,
            rdc_pni_1_4_liability_usd=rdc_pni,
            sue_and_labour_payout_usd=sue_labour,
            remarks=remarks,
            audit_hash=audit_hash
        )
