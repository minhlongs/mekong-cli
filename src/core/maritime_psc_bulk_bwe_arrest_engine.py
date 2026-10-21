"""Core calculation engines for Maritime PSC, Bulk Cargo, BWE & Vessel Arrest.

Phases 315-318 Simplest Viable Maritime Operational Suite.
- Phase 315: Tokyo MoU Port State Control (PSC) Inspection Targeting & Deficiency Risk Engine.
- Phase 316: IMSBC Solid Bulk Cargo Liquefaction & TML/FMP Safety Engine.
- Phase 317: BWM Convention Ballast Water Exchange (D-1) vs Treatment (D-2) Compliance Engine.
- Phase 318: Maritime Lien Enforcement & Vessel Arrest Waterfall Engine (VN Maritime Code 2015).
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any, Dict, List


# ==============================================================================
# Phase 315: Tokyo MoU PSC Inspection Targeting & Deficiency Risk Engine
# ==============================================================================

class FlagPerformance(str, Enum):
    WHITE = "WHITE"
    GREY = "GREY"
    BLACK = "BLACK"


class RoPerformance(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class ShipRiskProfile(str, Enum):
    HRS = "HRS"  # High Risk Ship
    SRS = "SRS"  # Standard Risk Ship
    LRS = "LRS"  # Low Risk Ship


class PscPriority(str, Enum):
    PRIORITY_I = "PRIORITY_I"      # Inspection mandatory (Overdue)
    PRIORITY_II = "PRIORITY_II"    # Inspection discretionary
    PRIORITY_III = "PRIORITY_III"  # Low priority (Not in window)


@dataclass
class PscTargetingInput:
    imo_number: str
    vessel_name: str
    flag: str
    flag_performance: FlagPerformance
    recognized_org_performance: RoPerformance
    vessel_age_years: int
    is_high_risk_ship_type: bool  # Oil/Chemical tanker, Gas carrier, Bulk carrier, Passenger ship
    deficiencies_last_36m: int
    detentions_last_36m: int
    months_since_last_psc: int
    critical_deficiency_present: bool = False  # e.g., OWS inop, emergency fire pump failure (Code 30)


@dataclass
class PscTargetingResult:
    imo_number: str
    vessel_name: str
    ship_risk_profile: ShipRiskProfile
    risk_score_points: int
    priority_level: PscPriority
    eligible_inspection_window: str
    grounds_for_detention: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "imo_number": self.imo_number,
            "vessel_name": self.vessel_name,
            "ship_risk_profile": self.ship_risk_profile.value,
            "risk_score_points": self.risk_score_points,
            "priority_level": self.priority_level.value,
            "eligible_inspection_window": self.eligible_inspection_window,
            "grounds_for_detention": self.grounds_for_detention,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class PscTargetingEngine:
    """Tokyo MoU Ship Risk Profile & PSC Targeting Calculator."""

    @classmethod
    def evaluate_targeting(cls, inp: PscTargetingInput) -> PscTargetingResult:
        points = 0

        # 1. Flag points
        if inp.flag_performance == FlagPerformance.BLACK:
            points += 5
        elif inp.flag_performance == FlagPerformance.GREY:
            points += 2

        # 2. RO points
        if inp.recognized_org_performance in (RoPerformance.LOW, RoPerformance.VERY_LOW):
            points += 3
        elif inp.recognized_org_performance == RoPerformance.MEDIUM:
            points += 1

        # 3. Ship Type & Age
        if inp.is_high_risk_ship_type:
            points += 2
            if inp.vessel_age_years > 12:
                points += 2
        elif inp.vessel_age_years > 20:
            points += 1

        # 4. Historical Record in last 36 months
        points += min(inp.deficiencies_last_36m // 5, 4)
        points += inp.detentions_last_36m * 4

        # Risk Profile classification
        if points >= 6 or inp.detentions_last_36m >= 2:
            profile = ShipRiskProfile.HRS
            window_min, window_max = 2, 4
        elif points <= 1 and inp.flag_performance == FlagPerformance.WHITE and inp.detentions_last_36m == 0:
            profile = ShipRiskProfile.LRS
            window_min, window_max = 9, 18
        else:
            profile = ShipRiskProfile.SRS
            window_min, window_max = 5, 8

        # Inspection Priority determination
        if inp.months_since_last_psc > window_max:
            priority = PscPriority.PRIORITY_I
        elif inp.months_since_last_psc >= window_min:
            priority = PscPriority.PRIORITY_II
        else:
            priority = PscPriority.PRIORITY_III

        # Grounds for detention (Code 30)
        grounds_detention = inp.critical_deficiency_present or (inp.detentions_last_36m > 0 and inp.deficiencies_last_36m > 15)

        remarks_list = [f"Hồ sơ rủi ro Tokyo MoU: {profile.value} ({points} điểm)"]
        if priority == PscPriority.PRIORITY_I:
            remarks_list.append(f"Quá hạn kiểm tra ({inp.months_since_last_psc} tháng > {window_max} tháng) - Bắt buộc kiểm tra Priority I")
        elif priority == PscPriority.PRIORITY_II:
            remarks_list.append(f"Trong khung kiểm tra ({window_min}-{window_max} tháng) - Ưu tiên Priority II")
        else:
            remarks_list.append(f"Chưa đến hạn kiểm tra định kỳ (khung {window_min}-{window_max} tháng)")

        if grounds_detention:
            remarks_list.append("CẢNH BÁO: Phát hiện lỗi nghiêm trọng (Code 30) có nguy cơ bị lưu giữ tàu (Detention)!")

        hash_payload = f"{inp.imo_number}:{profile.value}:{points}:{priority.value}:{grounds_detention}"
        audit_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

        return PscTargetingResult(
            imo_number=inp.imo_number,
            vessel_name=inp.vessel_name,
            ship_risk_profile=profile,
            risk_score_points=points,
            priority_level=priority,
            eligible_inspection_window=f"{window_min}-{window_max} months",
            grounds_for_detention=grounds_detention,
            remarks=" | ".join(remarks_list),
            audit_hash=audit_hash
        )


# ==============================================================================
# Phase 316: IMSBC Solid Bulk Cargo Liquefaction & TML/FMP Safety Engine
# ==============================================================================

class ImsbcCargoGroup(str, Enum):
    GROUP_A = "GROUP_A"  # Cargoes which may liquefy (Nickel ore, Iron ore fines, Bauxite)
    GROUP_B = "GROUP_B"  # Chemical hazard cargoes (Coal, Direct Reduced Iron)
    GROUP_C = "GROUP_C"  # Non-combustible, neither liquefy nor chemical hazard


@dataclass
class BulkCargoInput:
    cargo_name: str
    cargo_group: ImsbcCargoGroup
    total_metric_tons: float
    flow_moisture_point_pct: float     # FMP (%)
    actual_moisture_content_pct: float  # MC (%)
    certificate_age_days: int = 3       # IMSBC rule: moisture test within 7 days of loading


@dataclass
class BulkCargoSafetyResult:
    cargo_name: str
    cargo_group: ImsbcCargoGroup
    fmp_pct: float
    tml_pct: float
    actual_mc_pct: float
    moisture_excess_pct: float
    is_safe_to_load: bool
    canister_test_required: bool
    carriage_prohibited: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cargo_name": self.cargo_name,
            "cargo_group": self.cargo_group.value,
            "fmp_pct": round(self.fmp_pct, 2),
            "tml_pct": round(self.tml_pct, 2),
            "actual_mc_pct": round(self.actual_mc_pct, 2),
            "moisture_excess_pct": round(self.moisture_excess_pct, 2),
            "is_safe_to_load": self.is_safe_to_load,
            "canister_test_required": self.canister_test_required,
            "carriage_prohibited": self.carriage_prohibited,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class BulkCargoLiquefactionEngine:
    """IMSBC Code Solid Bulk Cargo Transportable Moisture Limit (TML) Engine."""

    TML_RATIO_OF_FMP = 0.90  # TML is statutorily 90% of FMP under IMSBC Code
    CERT_VALIDITY_DAYS = 7   # Moisture sampling max 7 days before loading

    @classmethod
    def evaluate_cargo_safety(cls, inp: BulkCargoInput) -> BulkCargoSafetyResult:
        # Non-Group A cargoes are not subject to liquefaction
        if inp.cargo_group != ImsbcCargoGroup.GROUP_A:
            hash_val = hashlib.sha256(f"{inp.cargo_name}:{inp.cargo_group.value}".encode()).hexdigest()[:16]
            return BulkCargoSafetyResult(
                cargo_name=inp.cargo_name,
                cargo_group=inp.cargo_group,
                fmp_pct=0.0,
                tml_pct=0.0,
                actual_mc_pct=inp.actual_moisture_content_pct,
                moisture_excess_pct=0.0,
                is_safe_to_load=True,
                canister_test_required=False,
                carriage_prohibited=False,
                remarks=f"Hàng thuộc nhóm {inp.cargo_group.value}: Không có rủi ro hóa lỏng (Liquefaction).",
                audit_hash=hash_val
            )

        tml = inp.flow_moisture_point_pct * cls.TML_RATIO_OF_FMP
        excess = inp.actual_moisture_content_pct - tml
        cert_expired = inp.certificate_age_days > cls.CERT_VALIDITY_DAYS

        # Carriage prohibited if actual moisture content exceeds TML
        carriage_prohibited = excess > 0 or cert_expired
        is_safe = not carriage_prohibited
        canister_required = excess > -1.0 or cert_expired  # Onboard spot-check if within 1% of TML

        remarks = []
        if excess > 0:
            remarks.append(f"NGUY HIỂM: Độ ẩm thực tế ({inp.actual_moisture_content_pct:.1f}%) vượt quá TML ({tml:.1f}%) - CẤM XẾP HÀNG LÊN TÀU")
        else:
            remarks.append(f"Độ ẩm thực tế ({inp.actual_moisture_content_pct:.1f}%) nằm trong ngưỡng an toàn TML ({tml:.1f}%)")

        if cert_expired:
            remarks.append(f"Chứng thư độ ẩm quá hạn {inp.certificate_age_days} ngày (> {cls.CERT_VALIDITY_DAYS} ngày)")
        if canister_required and is_safe:
            remarks.append("Yêu cầu Thuyền trưởng thực hiện Canister Test tại hiện trường trước khi nhận hàng")

        hash_payload = f"{inp.cargo_name}:{tml:.2f}:{inp.actual_moisture_content_pct:.2f}:{is_safe}"
        audit_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

        return BulkCargoSafetyResult(
            cargo_name=inp.cargo_name,
            cargo_group=inp.cargo_group,
            fmp_pct=inp.flow_moisture_point_pct,
            tml_pct=tml,
            actual_mc_pct=inp.actual_moisture_content_pct,
            moisture_excess_pct=max(0.0, excess),
            is_safe_to_load=is_safe,
            canister_test_required=canister_required,
            carriage_prohibited=carriage_prohibited,
            remarks=" | ".join(remarks),
            audit_hash=audit_hash
        )


# ==============================================================================
# Phase 317: BWM Convention Ballast Water Exchange (D-1) vs Treatment (D-2)
# ==============================================================================

class BwmStandard(str, Enum):
    D1_EXCHANGE = "D1_EXCHANGE"    # Ballast Water Exchange standard
    D2_TREATMENT = "D2_TREATMENT"  # Ballast Water Performance / BWMS standard


@dataclass
class BallastWaterInput:
    vessel_name: str
    standard_applied: BwmStandard
    tank_capacity_m3: float
    pumped_volume_m3: float
    distance_from_land_nm: float
    water_depth_m: float
    bwms_operational: bool = True
    active_substance_tro_ppm: float = 0.8  # Residual oxidants for D-2 systems (typically <= 1.0 ppm)


@dataclass
class BallastWaterResult:
    vessel_name: str
    standard_applied: BwmStandard
    exchange_efficiency_pct: float
    distance_compliant: bool
    depth_compliant: bool
    is_discharge_permitted: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "standard_applied": self.standard_applied.value,
            "exchange_efficiency_pct": round(self.exchange_efficiency_pct, 1),
            "distance_compliant": self.distance_compliant,
            "depth_compliant": self.depth_compliant,
            "is_discharge_permitted": self.is_discharge_permitted,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class BallastWaterComplianceEngine:
    """IMO Ballast Water Management Convention (BWM) Reg D-1 vs D-2 Engine."""

    # Reg D-1 criteria
    MIN_DISTANCE_LAND_NM = 200.0  # Or at least 50 NM if 200 NM impossible
    MIN_WATER_DEPTH_M = 200.0
    MIN_VOLUMETRIC_EFFICIENCY_PCT = 95.0

    @classmethod
    def evaluate_compliance(cls, req: BallastWaterInput) -> BallastWaterResult:
        remarks = []

        if req.standard_applied == BwmStandard.D1_EXCHANGE:
            # 3 times tank volume pumps >= 95% volumetric exchange efficiency
            vol_ratio = req.pumped_volume_m3 / req.tank_capacity_m3 if req.tank_capacity_m3 > 0 else 0.0
            efficiency_pct = min(100.0, vol_ratio * 33.33) if vol_ratio < 3.0 else 100.0

            dist_ok = req.distance_from_land_nm >= 50.0  # Absolute minimum 50 NM
            is_full_distance = req.distance_from_land_nm >= cls.MIN_DISTANCE_LAND_NM
            depth_ok = req.water_depth_m >= cls.MIN_WATER_DEPTH_M
            eff_ok = efficiency_pct >= cls.MIN_VOLUMETRIC_EFFICIENCY_PCT

            permitted = dist_ok and depth_ok and eff_ok

            if not is_full_distance and dist_ok:
                remarks.append(f"Khoảng cách {req.distance_from_land_nm:.0f} NM (vùng biển giới hạn 50-200 NM)")
            elif not dist_ok:
                remarks.append(f"VI PHẠM: Khoảng cách cách bờ {req.distance_from_land_nm:.0f} NM (< 50 NM)")

            if not depth_ok:
                remarks.append(f"VI PHẠM: Độ sâu luồng {req.water_depth_m:.0f}m (< 200m)")
            if not eff_ok:
                remarks.append(f"VI PHẠM: Hiệu suất trao đổi nước dằn {efficiency_pct:.1f}% (< 95%)")

            if permitted:
                remarks.append("ĐẠT CHUẨN D-1: Cho phép xả nước dằn sau khi trao đổi")
            else:
                remarks.append("CẤM XẢ NƯỚC DẰN (D-1 Violation) - Yêu cầu giữ lại trong két hoặc bơm ra trạm tiếp nhận bờ")

        else:  # D2_TREATMENT
            efficiency_pct = 100.0 if req.bwms_operational else 0.0
            dist_ok = True   # D-2 BWMS permitted inside coastal / port waters if treated
            depth_ok = True
            tro_ok = req.active_substance_tro_ppm <= 1.0  # Residual neutralizer check

            permitted = req.bwms_operational and tro_ok
            if req.bwms_operational and tro_ok:
                remarks.append("ĐẠT CHUẨN D-2: Hệ thống xử lý nước dằn (BWMS) hoạt động bình thường, TRO an toàn")
            elif not req.bwms_operational:
                remarks.append("VI PHẠM: Hệ thống BWMS bị lỗi/không vận hành - Không được xả nước dằn chưa xử lý")
            elif not tro_ok:
                remarks.append(f"CẢNH BÁO DƯ LƯỢNG HÓA CHẤT TRO: {req.active_substance_tro_ppm} ppm vượt chuẩn 1.0 ppm")

        hash_payload = f"{req.vessel_name}:{req.standard_applied.value}:{permitted}:{efficiency_pct:.1f}"
        audit_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

        return BallastWaterResult(
            vessel_name=req.vessel_name,
            standard_applied=req.standard_applied,
            exchange_efficiency_pct=efficiency_pct,
            distance_compliant=dist_ok,
            depth_compliant=depth_ok,
            is_discharge_permitted=permitted,
            remarks=" | ".join(remarks),
            audit_hash=audit_hash
        )


# ==============================================================================
# Phase 318: Maritime Lien Enforcement & Vessel Arrest Waterfall Engine
# ==============================================================================

class MaritimeClaimRank(int, Enum):
    RANK_0_COURT_CUSTODY = 0   # Chi phí bảo quản tàu, đấu giá tại Tòa án
    RANK_1_CREW_WAGES = 1      # Lương và hồi hương thuyền viên (Maritime Lien)
    RANK_2_INJURY_LIFE = 2     # Bồi thường tính mạng, thương tật (Maritime Lien)
    RANK_3_SALVAGE = 3         # Tiền công cứu nạn (Maritime Lien)
    RANK_4_PORT_DUES = 4       # Phí cảng biển, hoa tiêu (Maritime Lien)
    RANK_5_COLLISION_DAMAGE = 5 # Đâm va, hư hỏng tài sản phi hợp đồng (Maritime Lien)
    RANK_6_MORTGAGE = 6        # Thế chấp tàu biển đã đăng ký (Ship Mortgage)
    RANK_7_UNSECURED = 7       # Khiếu nại thương mại thông thường (Bunkers, Repairs, Charter)


@dataclass
class MaritimeClaimItem:
    claim_id: str
    claimant_name: str
    rank: MaritimeClaimRank
    amount_vnd: float


@dataclass
class ClaimSettlement:
    claim_id: str
    claimant_name: str
    rank: int
    claimed_amount_vnd: float
    paid_amount_vnd: float
    recovery_rate_pct: float


@dataclass
class ArrestWaterfallResult:
    vessel_name: str
    total_auction_proceeds_vnd: float
    total_claims_vnd: float
    total_payout_vnd: float
    remaining_balance_vnd: float
    settlements: List[ClaimSettlement]
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "total_auction_proceeds_vnd": round(self.total_auction_proceeds_vnd, 2),
            "total_claims_vnd": round(self.total_claims_vnd, 2),
            "total_payout_vnd": round(self.total_payout_vnd, 2),
            "remaining_balance_vnd": round(self.remaining_balance_vnd, 2),
            "settlements": [
                {
                    "claim_id": s.claim_id,
                    "claimant_name": s.claimant_name,
                    "rank": s.rank,
                    "claimed_amount_vnd": s.claimed_amount_vnd,
                    "paid_amount_vnd": round(s.paid_amount_vnd, 2),
                    "recovery_rate_pct": round(s.recovery_rate_pct, 2),
                }
                for s in self.settlements
            ],
            "audit_hash": self.audit_hash,
        }


class VesselArrestWaterfallEngine:
    """Article 37 Vietnam Maritime Code 2015 Priority of Claims on Vessel Auction."""

    @classmethod
    def calculate_waterfall(
        cls,
        vessel_name: str,
        auction_proceeds_vnd: float,
        claims: List[MaritimeClaimItem]
    ) -> ArrestWaterfallResult:
        remaining_fund = auction_proceeds_vnd
        settlements: List[ClaimSettlement] = []

        # Group claims by statutory rank (0 to 7)
        ranked_groups: Dict[int, List[MaritimeClaimItem]] = {}
        for c in sorted(claims, key=lambda x: x.rank.value):
            r = c.rank.value
            ranked_groups.setdefault(r, []).append(c)

        total_claims = sum(c.amount_vnd for c in claims)
        total_payout = 0.0

        for r in sorted(ranked_groups.keys()):
            group = ranked_groups[r]
            group_total = sum(c.amount_vnd for c in group)

            if remaining_fund >= group_total:
                # Full payment for this tier
                for c in group:
                    settlements.append(ClaimSettlement(
                        claim_id=c.claim_id,
                        claimant_name=c.claimant_name,
                        rank=r,
                        claimed_amount_vnd=c.amount_vnd,
                        paid_amount_vnd=c.amount_vnd,
                        recovery_rate_pct=100.0
                    ))
                remaining_fund -= group_total
                total_payout += group_total
            elif remaining_fund > 0:
                # Pro-rata distribution among claimants in this tier
                ratio = remaining_fund / group_total
                for c in group:
                    paid = c.amount_vnd * ratio
                    settlements.append(ClaimSettlement(
                        claim_id=c.claim_id,
                        claimant_name=c.claimant_name,
                        rank=r,
                        claimed_amount_vnd=c.amount_vnd,
                        paid_amount_vnd=paid,
                        recovery_rate_pct=ratio * 100.0
                    ))
                total_payout += remaining_fund
                remaining_fund = 0.0
            else:
                # Exhausted funds
                for c in group:
                    settlements.append(ClaimSettlement(
                        claim_id=c.claim_id,
                        claimant_name=c.claimant_name,
                        rank=r,
                        claimed_amount_vnd=c.amount_vnd,
                        paid_amount_vnd=0.0,
                        recovery_rate_pct=0.0
                    ))

        hash_payload = f"{vessel_name}:{auction_proceeds_vnd:.0f}:{total_payout:.0f}"
        audit_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

        return ArrestWaterfallResult(
            vessel_name=vessel_name,
            total_auction_proceeds_vnd=auction_proceeds_vnd,
            total_claims_vnd=total_claims,
            total_payout_vnd=total_payout,
            remaining_balance_vnd=remaining_fund,
            settlements=settlements,
            audit_hash=audit_hash
        )
