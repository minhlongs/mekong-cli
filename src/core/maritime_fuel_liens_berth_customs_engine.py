"""
Maritime Fuel Switchover, Lien Waterfall, Berth Planning & Customs VASSCM Engine.
Covers:
- Phase 275: MARPOL Annex VI Fuel Sulfur Cap & Port/ECA Fuel Switchover (MEPC.1/Circ.864)
- Phase 276: Maritime Lien Priority Waterfall & Auction Distribution (VMC 2015 Arts. 37-43)
- Phase 277: Seaport Berth Allocation Planning, Tidal UKC & BOR Engine (Decree 58/2017 & PIANC 158)
- Phase 278: Customs Risk Channeling & Seaport VASSCM Clearance Engine (Decision 1399 & 2185/QĐ-TCHQ)

Zero external dependencies - Python standard library only.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import math
from typing import Any, Dict, List, Optional


# ==============================================================================
# PHASE 275: MARPOL ANNEX VI FUEL SWITCHOVER ENGINE
# ==============================================================================

class FuelComplianceStatus(str, Enum):
    """MARPOL Annex VI fuel sulfur compliance status."""
    ALREADY_COMPLIANT = "already_compliant"
    SWITCHOVER_FEASIBLE = "switchover_feasible"
    DISTANCE_DEFICIT_WARNING = "distance_deficit_warning"
    VISCOSITY_SAFETY_VIOLATION = "viscosity_safety_violation"
    TARGET_UNATTAINABLE_ERROR = "target_unattainable_error"


@dataclass
class FuelSwitchoverInput:
    """Input parameters for fuel oil switchover procedure."""
    vessel_name: str
    imo_number: str
    system_volume_m3: float
    fuel_consumption_m3_h: float
    initial_sulfur_pct: float
    low_sulfur_bunker_pct: float
    target_sulfur_pct: float
    initial_temp_c: float
    target_temp_c: float
    vessel_speed_knots: float
    distance_to_boundary_nm: float
    mgo_kinematic_viscosity_cst: float


@dataclass
class FuelSwitchoverResult:
    """Result of fuel switchover calculation."""
    vessel_name: str
    status: FuelComplianceStatus
    dilution_duration_hours: float
    thermal_ramp_duration_hours: float
    critical_duration_hours: float
    required_switchover_distance_nm: float
    remaining_distance_buffer_nm: float
    cooling_rate_c_per_min: float
    inlet_viscosity_cst: float
    is_safe_to_execute: bool
    summary_vi: str
    summary_en: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "status": self.status.value,
            "dilution_duration_hours": round(self.dilution_duration_hours, 2),
            "thermal_ramp_duration_hours": round(self.thermal_ramp_duration_hours, 2),
            "critical_duration_hours": round(self.critical_duration_hours, 2),
            "required_switchover_distance_nm": round(self.required_switchover_distance_nm, 2),
            "remaining_distance_buffer_nm": round(self.remaining_distance_buffer_nm, 2),
            "cooling_rate_c_per_min": round(self.cooling_rate_c_per_min, 2),
            "inlet_viscosity_cst": round(self.inlet_viscosity_cst, 2),
            "is_safe_to_execute": self.is_safe_to_execute,
            "summary_vi": self.summary_vi,
            "summary_en": self.summary_en,
        }


class FuelSwitchoverEngine:
    """MARPOL Annex VI fuel oil changeover calculator."""

    @staticmethod
    def calculate_switchover(data: FuelSwitchoverInput) -> FuelSwitchoverResult:
        if data.system_volume_m3 <= 0 or data.fuel_consumption_m3_h <= 0 or data.vessel_speed_knots <= 0:
            raise ValueError("System volume, fuel consumption, and vessel speed must be strictly positive.")

        # Check if already compliant
        if data.initial_sulfur_pct <= data.target_sulfur_pct:
            return FuelSwitchoverResult(
                vessel_name=data.vessel_name,
                status=FuelComplianceStatus.ALREADY_COMPLIANT,
                dilution_duration_hours=0.0,
                thermal_ramp_duration_hours=0.0,
                critical_duration_hours=0.0,
                required_switchover_distance_nm=0.0,
                remaining_distance_buffer_nm=data.distance_to_boundary_nm,
                cooling_rate_c_per_min=0.0,
                inlet_viscosity_cst=data.mgo_kinematic_viscosity_cst,
                is_safe_to_execute=True,
                summary_vi=f"Nhiên liệu hiện tại ({data.initial_sulfur_pct}% S) đã đạt chuẩn giới hạn ({data.target_sulfur_pct}% S).",
                summary_en=f"Current fuel ({data.initial_sulfur_pct}% S) already complies with boundary limit ({data.target_sulfur_pct}% S).",
            )

        # Check if low-sulfur bunker sulfur is higher than target limit
        if data.low_sulfur_bunker_pct >= data.target_sulfur_pct:
            return FuelSwitchoverResult(
                vessel_name=data.vessel_name,
                status=FuelComplianceStatus.TARGET_UNATTAINABLE_ERROR,
                dilution_duration_hours=0.0,
                thermal_ramp_duration_hours=0.0,
                critical_duration_hours=0.0,
                required_switchover_distance_nm=0.0,
                remaining_distance_buffer_nm=0.0,
                cooling_rate_c_per_min=0.0,
                inlet_viscosity_cst=data.mgo_kinematic_viscosity_cst,
                is_safe_to_execute=False,
                summary_vi=f"Nhiên liệu cấp ({data.low_sulfur_bunker_pct}% S) không đạt ngưỡng mục tiêu ({data.target_sulfur_pct}% S).",
                summary_en=f"Bunker fuel sulfur ({data.low_sulfur_bunker_pct}% S) cannot meet target limit ({data.target_sulfur_pct}% S).",
            )

        # Exponential mixing dilution model: t = (V / Q) * ln((C0 - C_low) / (C_target - C_low))
        ratio = (data.initial_sulfur_pct - data.low_sulfur_bunker_pct) / (data.target_sulfur_pct - data.low_sulfur_bunker_pct)
        t_dilution = (data.system_volume_m3 / data.fuel_consumption_m3_h) * math.log(ratio)

        # Thermal ramp: max 2.0 deg C/min = 120.0 deg C/h
        temp_diff = abs(data.initial_temp_c - data.target_temp_c)
        t_thermal = temp_diff / 120.0  # hours
        cooling_rate_per_min = min(2.0, temp_diff / (max(t_dilution, t_thermal) * 60.0))

        # Critical duration is governed by the slower process (mixing or thermal shock limit)
        t_critical = max(t_dilution, t_thermal)
        d_required = t_critical * data.vessel_speed_knots
        distance_buffer = data.distance_to_boundary_nm - d_required

        # Viscosity constraint per ISO 8217: min 2.0 cSt
        if data.mgo_kinematic_viscosity_cst < 2.0:
            status = FuelComplianceStatus.VISCOSITY_SAFETY_VIOLATION
            is_safe = False
            summary_vi = f"CẢNH BÁO NGUY HIỂM: Độ nhớt {data.mgo_kinematic_viscosity_cst:.2f} cSt dưới ngưỡng an toàn 2.0 cSt (nguy cơ bó kẹt bơm cao áp)."
            summary_en = f"CRITICAL HAZARD: Viscosity {data.mgo_kinematic_viscosity_cst:.2f} cSt below safety threshold 2.0 cSt (booster pump seizure risk)."
        elif distance_buffer < 0:
            status = FuelComplianceStatus.DISTANCE_DEFICIT_WARNING
            is_safe = False
            summary_vi = f"CẢNH BÁO: Khoảng cách hiện tại ({data.distance_to_boundary_nm:.1f} NM) không đủ cho thời gian chuyển đổi ({d_required:.1f} NM cần thiết)."
            summary_en = f"WARNING: Remaining distance ({data.distance_to_boundary_nm:.1f} NM) insufficient for switchover ({d_required:.1f} NM needed)."
        else:
            status = FuelComplianceStatus.SWITCHOVER_FEASIBLE
            is_safe = True
            summary_vi = f"ĐỦ ĐIỀU KIỆN CHUYỂN ĐỔI: Cần {t_critical:.2f} giờ ({d_required:.1f} NM), còn dư {distance_buffer:.1f} NM an toàn."
            summary_en = f"SWITCHOVER FEASIBLE: Requires {t_critical:.2f} hrs ({d_required:.1f} NM), safety margin {distance_buffer:.1f} NM."

        return FuelSwitchoverResult(
            vessel_name=data.vessel_name,
            status=status,
            dilution_duration_hours=t_dilution,
            thermal_ramp_duration_hours=t_thermal,
            critical_duration_hours=t_critical,
            required_switchover_distance_nm=d_required,
            remaining_distance_buffer_nm=distance_buffer,
            cooling_rate_c_per_min=cooling_rate_per_min,
            inlet_viscosity_cst=data.mgo_kinematic_viscosity_cst,
            is_safe_to_execute=is_safe,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )


# ==============================================================================
# PHASE 276: MARITIME LIEN WATERFALL & AUCTION DISTRIBUTION ENGINE
# ==============================================================================

class LienTier(int, Enum):
    """5 Statutory Tiers under Vietnam Maritime Code 2015 Art. 37."""
    TIER_1_CREW_WAGES = 1
    TIER_2_PERSONAL_INJURY = 2
    TIER_3_SALVAGE_GENERAL_AVERAGE = 3
    TIER_4_PORT_SAFETY_DUES = 4
    TIER_5_TORT_COLLISION = 5


class ClaimType(str, Enum):
    """Type of creditor claim."""
    STATUTORY_LIEN = "statutory_lien"
    SHIP_MORTGAGE = "ship_mortgage"
    UNSECURED_MARITIME_CLAIM = "unsecured_claim"


@dataclass
class MaritimeClaimItem:
    """Individual creditor claim against the vessel."""
    claim_id: str
    claimant_name: str
    claim_type: ClaimType
    lien_tier: Optional[LienTier]
    claim_amount_vnd: float
    claim_date_iso: str
    arrest_prior_to_expiry: bool = False
    salvage_timestamp_iso: Optional[str] = None
    mortgage_registration_iso: Optional[str] = None


@dataclass
class ClaimDistributionResult:
    """Individual payout distribution result."""
    claim_id: str
    claimant_name: str
    claim_type: str
    tier: Optional[int]
    claimed_amount_vnd: float
    paid_amount_vnd: float
    deficit_amount_vnd: float
    recovery_rate_pct: float
    is_time_barred: bool
    status_note: str


@dataclass
class AuctionWaterfallReport:
    """Comprehensive judicial auction waterfall distribution report."""
    vessel_name: str
    gross_proceeds_vnd: float
    auction_enforcement_costs_vnd: float
    net_distributable_funds_vnd: float
    total_statutory_liens_paid_vnd: float
    total_mortgages_paid_vnd: float
    total_unsecured_paid_vnd: float
    unallocated_surplus_vnd: float
    claims_payout: List[ClaimDistributionResult] = field(default_factory=list)
    summary_vi: str = ""
    summary_en: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "gross_proceeds_vnd": round(self.gross_proceeds_vnd, 2),
            "auction_enforcement_costs_vnd": round(self.auction_enforcement_costs_vnd, 2),
            "net_distributable_funds_vnd": round(self.net_distributable_funds_vnd, 2),
            "total_statutory_liens_paid_vnd": round(self.total_statutory_liens_paid_vnd, 2),
            "total_mortgages_paid_vnd": round(self.total_mortgages_paid_vnd, 2),
            "total_unsecured_paid_vnd": round(self.total_unsecured_paid_vnd, 2),
            "unallocated_surplus_vnd": round(self.unallocated_surplus_vnd, 2),
            "claims_payout": [
                {
                    "claim_id": c.claim_id,
                    "claimant_name": c.claimant_name,
                    "claim_type": c.claim_type,
                    "tier": c.tier,
                    "claimed_amount_vnd": round(c.claimed_amount_vnd, 2),
                    "paid_amount_vnd": round(c.paid_amount_vnd, 2),
                    "deficit_amount_vnd": round(c.deficit_amount_vnd, 2),
                    "recovery_rate_pct": round(c.recovery_rate_pct, 2),
                    "is_time_barred": c.is_time_barred,
                    "status_note": c.status_note,
                }
                for c in self.claims_payout
            ],
            "summary_vi": self.summary_vi,
            "summary_en": self.summary_en,
        }


class MaritimeLienWaterfallEngine:
    """Judicial auction proceeds distributor following VMC 2015 Arts. 37-43."""

    @staticmethod
    def distribute_auction_proceeds(
        vessel_name: str,
        gross_proceeds_vnd: float,
        auction_costs_vnd: float,
        auction_date_iso: str,
        claims: List[MaritimeClaimItem],
    ) -> AuctionWaterfallReport:
        if gross_proceeds_vnd < 0 or auction_costs_vnd < 0:
            raise ValueError("Gross proceeds and auction costs must be non-negative.")

        auction_dt = datetime.fromisoformat(auction_date_iso.replace("Z", "+00:00"))
        net_distributable = max(0.0, gross_proceeds_vnd - auction_costs_vnd)
        current_funds = net_distributable

        payout_map: Dict[str, ClaimDistributionResult] = {}
        active_liens: List[MaritimeClaimItem] = []
        mortgages: List[MaritimeClaimItem] = []
        unsecured: List[MaritimeClaimItem] = []

        # Step 1: Filter active vs expired claims (Art. 39 - 1-year timebar)
        for c in claims:
            c_dt = datetime.fromisoformat(c.claim_date_iso.replace("Z", "+00:00"))
            days_elapsed = (auction_dt - c_dt).total_seconds() / 86400.0

            if c.claim_type == ClaimType.STATUTORY_LIEN and days_elapsed > 365.25 and not c.arrest_prior_to_expiry:
                payout_map[c.claim_id] = ClaimDistributionResult(
                    claim_id=c.claim_id,
                    claimant_name=c.claimant_name,
                    claim_type=c.claim_type.value,
                    tier=c.lien_tier.value if c.lien_tier else None,
                    claimed_amount_vnd=c.claim_amount_vnd,
                    paid_amount_vnd=0.0,
                    deficit_amount_vnd=c.claim_amount_vnd,
                    recovery_rate_pct=0.0,
                    is_time_barred=True,
                    status_note="Hết thời hiệu cầm giữ hàng hải (> 1 năm theo Điều 39)",
                )
            elif c.claim_type == ClaimType.STATUTORY_LIEN:
                active_liens.append(c)
            elif c.claim_type == ClaimType.SHIP_MORTGAGE:
                mortgages.append(c)
            else:
                unsecured.append(c)

        total_liens_paid = 0.0

        # Step 2: Waterfall across Tiers 1 through 5
        for tier_idx in range(1, 6):
            tier_enum = LienTier(tier_idx)
            tier_claims = [c for c in active_liens if c.lien_tier == tier_enum]
            if not tier_claims:
                continue

            if tier_enum == LienTier.TIER_3_SALVAGE_GENERAL_AVERAGE:
                # Reverse chronological order for salvage (Art. 38)
                tier_claims.sort(
                    key=lambda x: x.salvage_timestamp_iso or x.claim_date_iso,
                    reverse=True,
                )
                for sc in tier_claims:
                    if current_funds >= sc.claim_amount_vnd:
                        paid = sc.claim_amount_vnd
                    else:
                        paid = current_funds
                    current_funds -= paid
                    total_liens_paid += paid
                    payout_map[sc.claim_id] = ClaimDistributionResult(
                        claim_id=sc.claim_id,
                        claimant_name=sc.claimant_name,
                        claim_type=sc.claim_type.value,
                        tier=3,
                        claimed_amount_vnd=sc.claim_amount_vnd,
                        paid_amount_vnd=paid,
                        deficit_amount_vnd=sc.claim_amount_vnd - paid,
                        recovery_rate_pct=(paid / sc.claim_amount_vnd * 100.0) if sc.claim_amount_vnd > 0 else 0.0,
                        is_time_barred=False,
                        status_note="Thanh toán Cấp 3 (Cứu hộ sau ưu tiên trước - Điều 38)",
                    )
            else:
                total_tier_demand = sum(c.claim_amount_vnd for c in tier_claims)
                if current_funds >= total_tier_demand:
                    for c in tier_claims:
                        paid = c.claim_amount_vnd
                        current_funds -= paid
                        total_liens_paid += paid
                        payout_map[c.claim_id] = ClaimDistributionResult(
                            claim_id=c.claim_id,
                            claimant_name=c.claimant_name,
                            claim_type=c.claim_type.value,
                            tier=tier_idx,
                            claimed_amount_vnd=c.claim_amount_vnd,
                            paid_amount_vnd=paid,
                            deficit_amount_vnd=0.0,
                            recovery_rate_pct=100.0,
                            is_time_barred=False,
                            status_note=f"Thanh toán đủ 100% Cấp {tier_idx}",
                        )
                elif current_funds > 0:
                    pro_rata_factor = current_funds / total_tier_demand
                    for c in tier_claims:
                        paid = c.claim_amount_vnd * pro_rata_factor
                        total_liens_paid += paid
                        payout_map[c.claim_id] = ClaimDistributionResult(
                            claim_id=c.claim_id,
                            claimant_name=c.claimant_name,
                            claim_type=c.claim_type.value,
                            tier=tier_idx,
                            claimed_amount_vnd=c.claim_amount_vnd,
                            paid_amount_vnd=paid,
                            deficit_amount_vnd=c.claim_amount_vnd - paid,
                            recovery_rate_pct=pro_rata_factor * 100.0,
                            is_time_barred=False,
                            status_note=f"Phân bổ tỷ lệ Cấp {tier_idx} ({pro_rata_factor*100:.1f}%)",
                        )
                    current_funds = 0.0
                else:
                    for c in tier_claims:
                        payout_map[c.claim_id] = ClaimDistributionResult(
                            claim_id=c.claim_id,
                            claimant_name=c.claimant_name,
                            claim_type=c.claim_type.value,
                            tier=tier_idx,
                            claimed_amount_vnd=c.claim_amount_vnd,
                            paid_amount_vnd=0.0,
                            deficit_amount_vnd=c.claim_amount_vnd,
                            recovery_rate_pct=0.0,
                            is_time_barred=False,
                            status_note=f"Hết ngân quỹ tại Cấp {tier_idx}",
                        )

        # Step 3: Mortgages (sorted by registration time)
        total_mortgages_paid = 0.0
        mortgages.sort(key=lambda m: m.mortgage_registration_iso or m.claim_date_iso)
        for m in mortgages:
            if current_funds >= m.claim_amount_vnd:
                paid = m.claim_amount_vnd
            else:
                paid = current_funds
            current_funds -= paid
            total_mortgages_paid += paid
            payout_map[m.claim_id] = ClaimDistributionResult(
                claim_id=m.claim_id,
                claimant_name=m.claimant_name,
                claim_type=m.claim_type.value,
                tier=None,
                claimed_amount_vnd=m.claim_amount_vnd,
                paid_amount_vnd=paid,
                deficit_amount_vnd=m.claim_amount_vnd - paid,
                recovery_rate_pct=(paid / m.claim_amount_vnd * 100.0) if m.claim_amount_vnd > 0 else 0.0,
                is_time_barred=False,
                status_note="Thanh toán thế chấp tàu biển theo thứ tự đăng ký",
            )

        # Step 4: Unsecured Claims (pro-rata distribution)
        total_unsecured_paid = 0.0
        total_unsecured_demand = sum(u.claim_amount_vnd for u in unsecured)
        if total_unsecured_demand > 0 and current_funds > 0:
            factor = min(1.0, current_funds / total_unsecured_demand)
            for u in unsecured:
                paid = u.claim_amount_vnd * factor
                current_funds -= paid
                total_unsecured_paid += paid
                payout_map[u.claim_id] = ClaimDistributionResult(
                    claim_id=u.claim_id,
                    claimant_name=u.claimant_name,
                    claim_type=u.claim_type.value,
                    tier=None,
                    claimed_amount_vnd=u.claim_amount_vnd,
                    paid_amount_vnd=paid,
                    deficit_amount_vnd=u.claim_amount_vnd - paid,
                    recovery_rate_pct=factor * 100.0,
                    is_time_barred=False,
                    status_note=f"Phân bổ tỷ lệ nợ không bảo đảm ({factor*100:.1f}%)",
                )
        else:
            for u in unsecured:
                payout_map[u.claim_id] = ClaimDistributionResult(
                    claim_id=u.claim_id,
                    claimant_name=u.claimant_name,
                    claim_type=u.claim_type.value,
                    tier=None,
                    claimed_amount_vnd=u.claim_amount_vnd,
                    paid_amount_vnd=0.0,
                    deficit_amount_vnd=u.claim_amount_vnd,
                    recovery_rate_pct=0.0,
                    is_time_barred=False,
                    status_note="Không còn ngân quỹ thanh toán nợ không bảo đảm",
                )

        ordered_payouts = [payout_map[c.claim_id] for c in claims if c.claim_id in payout_map]

        summary_vi = (
            f"Bán đấu giá tàu {vessel_name}: Tổng thu {gross_proceeds_vnd:,.0f} VND. "
            f"Trừ chi phí {auction_costs_vnd:,.0f} VND -> Thực chi {net_distributable:,.0f} VND. "
            f"Cầm giữ hàng hải: {total_liens_paid:,.0f} VND, Thế chấp: {total_mortgages_paid:,.0f} VND, "
            f"Nợ thường: {total_unsecured_paid:,.0f} VND, Dư: {current_funds:,.0f} VND."
        )
        summary_en = (
            f"Auction {vessel_name}: Gross {gross_proceeds_vnd:,.0f} VND. "
            f"Costs {auction_costs_vnd:,.0f} VND -> Net {net_distributable:,.0f} VND. "
            f"Liens: {total_liens_paid:,.0f} VND, Mortgages: {total_mortgages_paid:,.0f} VND, "
            f"Unsecured: {total_unsecured_paid:,.0f} VND, Surplus: {current_funds:,.0f} VND."
        )

        return AuctionWaterfallReport(
            vessel_name=vessel_name,
            gross_proceeds_vnd=gross_proceeds_vnd,
            auction_enforcement_costs_vnd=auction_costs_vnd,
            net_distributable_funds_vnd=net_distributable,
            total_statutory_liens_paid_vnd=total_liens_paid,
            total_mortgages_paid_vnd=total_mortgages_paid,
            total_unsecured_paid_vnd=total_unsecured_paid,
            unallocated_surplus_vnd=current_funds,
            claims_payout=ordered_payouts,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )


# ==============================================================================
# PHASE 277: SEAPORT BERTH ALLOCATION, TIDAL UKC & BOR ENGINE
# ==============================================================================

@dataclass
class BerthAllocationInput:
    """Input for berth allocation and dynamic UKC calculation."""
    berth_id: str
    berth_length_m: float
    charted_depth_m: float
    vessel_name: str
    loa_m: float
    beam_m: float
    static_draft_m: float
    block_coefficient: float
    transit_speed_knots: float
    channel_width_m: float
    is_confined_channel: bool
    water_density_kg_l: float
    wave_response_m: float
    tide_high_water_m: float
    tide_low_water_m: float
    tide_cycle_hours: float
    hour_of_transit: float
    high_water_hour: float
    total_service_hours_period: float
    period_hours: float
    active_berths_count: int


@dataclass
class BerthUkcEvaluationResult:
    """Evaluation result for berth allocation, tidal UKC, and BOR."""
    berth_id: str
    vessel_name: str
    is_slot_length_adequate: bool
    required_slot_length_m: float
    tide_height_at_transit_m: float
    dynamic_squat_m: float
    salinity_sinkage_m: float
    total_dynamic_water_depth_m: float
    total_dynamic_draft_m: float
    calculated_ukc_m: float
    minimum_required_ukc_m: float
    is_ukc_safe: bool
    berth_occupancy_rate_pct: float
    is_bor_congested: bool
    safe_transit_window_hours: float
    summary_vi: str
    summary_en: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "berth_id": self.berth_id,
            "vessel_name": self.vessel_name,
            "is_slot_length_adequate": self.is_slot_length_adequate,
            "required_slot_length_m": round(self.required_slot_length_m, 2),
            "tide_height_at_transit_m": round(self.tide_height_at_transit_m, 2),
            "dynamic_squat_m": round(self.dynamic_squat_m, 2),
            "salinity_sinkage_m": round(self.salinity_sinkage_m, 2),
            "total_dynamic_water_depth_m": round(self.total_dynamic_water_depth_m, 2),
            "total_dynamic_draft_m": round(self.total_dynamic_draft_m, 2),
            "calculated_ukc_m": round(self.calculated_ukc_m, 2),
            "minimum_required_ukc_m": round(self.minimum_required_ukc_m, 2),
            "is_ukc_safe": self.is_ukc_safe,
            "berth_occupancy_rate_pct": round(self.berth_occupancy_rate_pct, 2),
            "is_bor_congested": self.is_bor_congested,
            "safe_transit_window_hours": round(self.safe_transit_window_hours, 2),
            "summary_vi": self.summary_vi,
            "summary_en": self.summary_en,
        }


class BerthPlanningUkcEngine:
    """Berth allocation spatiotemporal & tidal UKC optimization engine."""

    @staticmethod
    def evaluate_berth_plan(data: BerthAllocationInput) -> BerthUkcEvaluationResult:
        if data.berth_length_m <= 0 or data.loa_m <= 0 or data.static_draft_m <= 0:
            raise ValueError("Berth length, LOA, and draft must be positive.")

        # Spatial slot length constraint: LOA + max(15m, 10% LOA)
        req_slot = data.loa_m + max(15.0, 0.10 * data.loa_m)
        is_length_ok = data.berth_length_m >= req_slot

        # Harmonic tide calculation at transit hour
        omega = (2.0 * math.pi) / max(1.0, data.tide_cycle_hours)
        mid_level = (data.tide_high_water_m + data.tide_low_water_m) / 2.0
        amplitude = (data.tide_high_water_m - data.tide_low_water_m) / 2.0
        tide_h = mid_level + amplitude * math.cos(omega * (data.hour_of_transit - data.high_water_hour))

        # Dynamic Water Depth
        total_depth = data.charted_depth_m + tide_h

        # Barass Squat Model:
        # S_squat = (C_b * B_ratio * V_k^2) / (30 * K)
        # where B_ratio = (B_ship * Draft) / (W_channel * Depth)
        b_ratio = (data.beam_m * data.static_draft_m) / max(1.0, data.channel_width_m * total_depth)
        k_factor = 2.0 if data.is_confined_channel else 1.0
        squat_m = (data.block_coefficient * b_ratio * (data.transit_speed_knots ** 2)) / (30.0 * k_factor)

        # Salinity sinkage (freshwater correction): Draft * max(0, (1.025 - rho) / rho)
        rho = max(0.990, data.water_density_kg_l)
        salinity_sinkage = data.static_draft_m * max(0.0, (1.025 - rho) / rho)

        # Dynamic Draft & UKC
        total_dyn_draft = data.static_draft_m + squat_m + salinity_sinkage + data.wave_response_m
        dyn_ukc = total_depth - total_dyn_draft
        min_ukc = max(0.10 * data.static_draft_m, 0.60)
        is_ukc_ok = dyn_ukc >= min_ukc

        # Safe transit window estimation (duration where tide h(t) yields UKC >= min_ukc)
        # Required water depth: req_depth = total_dyn_draft + min_ukc
        # req_tide = req_depth - charted_depth
        req_tide = total_dyn_draft + min_ukc - data.charted_depth_m
        if req_tide <= data.tide_low_water_m:
            safe_window_hours = data.tide_cycle_hours
        elif req_tide >= data.tide_high_water_m:
            safe_window_hours = 0.0
        else:
            # cos(theta) = (req_tide - mid_level) / amplitude
            cos_val = max(-1.0, min(1.0, (req_tide - mid_level) / max(0.01, amplitude)))
            half_angle = math.acos(cos_val)
            safe_window_hours = (2.0 * half_angle / (2.0 * math.pi)) * data.tide_cycle_hours

        # Berth Occupancy Rate (BOR)
        bor_denom = max(1.0, data.active_berths_count * data.period_hours)
        bor_pct = (data.total_service_hours_period / bor_denom) * 100.0
        is_congested = bor_pct > 65.0  # PIANC container congestion ceiling

        summary_vi = (
            f"Cầu bến {data.berth_id} cho tàu {data.vessel_name}: "
            f"Chiều dài {'ĐẠT' if is_length_ok else 'THIẾU'} ({data.berth_length_m:.1f}m / {req_slot:.1f}m cần). "
            f"UKC tại giờ hành hải: {dyn_ukc:.2f}m (Yêu cầu: >= {min_ukc:.2f}m -> {'AN TOÀN' if is_ukc_ok else 'NGUY CƠ MẮC CẠN'}). "
            f"Hệ số sử dụng cầu (BOR): {bor_pct:.1f}% ({'ÙN TẮC' if is_congested else 'BÌNH THƯỜNG'})."
        )
        summary_en = (
            f"Berth {data.berth_id} for {data.vessel_name}: "
            f"Length {'ADEQUATE' if is_length_ok else 'DEFICIENT'} ({data.berth_length_m:.1f}m / {req_slot:.1f}m required). "
            f"Dynamic UKC: {dyn_ukc:.2f}m (Min: >= {min_ukc:.2f}m -> {'SAFE' if is_ukc_ok else 'GROUNDING HAZARD'}). "
            f"BOR: {bor_pct:.1f}% ({'CONGESTED' if is_congested else 'OPTIMAL'})."
        )

        return BerthUkcEvaluationResult(
            berth_id=data.berth_id,
            vessel_name=data.vessel_name,
            is_slot_length_adequate=is_length_ok,
            required_slot_length_m=req_slot,
            tide_height_at_transit_m=tide_h,
            dynamic_squat_m=squat_m,
            salinity_sinkage_m=salinity_sinkage,
            total_dynamic_water_depth_m=total_depth,
            total_dynamic_draft_m=total_dyn_draft,
            calculated_ukc_m=dyn_ukc,
            minimum_required_ukc_m=min_ukc,
            is_ukc_safe=is_ukc_ok,
            berth_occupancy_rate_pct=bor_pct,
            is_bor_congested=is_congested,
            safe_transit_window_hours=safe_window_hours,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )


# ==============================================================================
# PHASE 278: CUSTOMS RISK CHANNELING & VASSCM CLEARANCE ENGINE
# ==============================================================================

class CustomsChannel(int, Enum):
    """Customs risk channel classification (Decisions 1399 & 2185/QĐ-TCHQ)."""
    GREEN_CHANNEL = 1   # Luồng Xanh: Exempt doc & physical check
    YELLOW_CHANNEL = 2  # Luồng Vàng: Detailed documentary audit
    RED_CHANNEL = 3     # Luồng Đỏ: Physical inspection


class EnterpriseComplianceLevel(int, Enum):
    """Enterprise risk compliance rating (1 to 5)."""
    LEVEL_1_AEO_PRIORITY = 1
    LEVEL_2_HIGH_COMPLIANCE = 2
    LEVEL_3_MEDIUM_COMPLIANCE = 3
    LEVEL_4_LOW_COMPLIANCE = 4
    LEVEL_5_NON_COMPLIANT = 5


@dataclass
class CustomsRiskInput:
    """Input for automated customs risk channeling."""
    declaration_number: str
    enterprise_tax_id: str
    enterprise_level: EnterpriseComplianceLevel
    hs_code: str
    hs_risk_tier: float          # 0.0 to 1.0
    origin_risk_tier: float      # 0.0 to 1.0
    has_intelligence_alert: bool
    declared_value_usd: float


@dataclass
class CustomsRiskChannelResult:
    """Result of automated risk channeling."""
    declaration_number: str
    channel: CustomsChannel
    channel_name_vi: str
    channel_name_en: str
    risk_score: float
    target_sla_hours: float
    exempt_document_check: bool
    exempt_physical_inspection: bool
    release_token: str
    summary_vi: str
    summary_en: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "declaration_number": self.declaration_number,
            "channel": self.channel.value,
            "channel_name_vi": self.channel_name_vi,
            "channel_name_en": self.channel_name_en,
            "risk_score": round(self.risk_score, 4),
            "target_sla_hours": self.target_sla_hours,
            "exempt_document_check": self.exempt_document_check,
            "exempt_physical_inspection": self.exempt_physical_inspection,
            "release_token": self.release_token,
            "summary_vi": self.summary_vi,
            "summary_en": self.summary_en,
        }


@dataclass
class VasscmGateCheckInput:
    """Gate-out 3-way match input parameters."""
    declaration_number: str
    declaration_status: str       # e.g. "RELEASED" or "CUSTOMS_CLEARED"
    edo_number: str
    edo_is_valid: bool
    container_number: str
    manifest_seal_number: str
    gate_scanned_seal_number: str


@dataclass
class VasscmGateCheckResult:
    """Gate-out clearance result with cryptographic barcode."""
    declaration_number: str
    container_number: str
    is_gate_pass_approved: bool
    match_status: str
    discrepancy_reasons: List[str]
    vasscm_auth_hash: str
    summary_vi: str
    summary_en: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "declaration_number": self.declaration_number,
            "container_number": self.container_number,
            "is_gate_pass_approved": self.is_gate_pass_approved,
            "match_status": self.match_status,
            "discrepancy_reasons": self.discrepancy_reasons,
            "vasscm_auth_hash": self.vasscm_auth_hash,
            "summary_vi": self.summary_vi,
            "summary_en": self.summary_en,
        }


class CustomsRiskVasscmEngine:
    """Automated customs channeling & VASSCM 3-way match engine."""

    @staticmethod
    def evaluate_risk_channel(data: CustomsRiskInput) -> CustomsRiskChannelResult:
        if not data.declaration_number or not data.enterprise_tax_id:
            raise ValueError("Declaration number and enterprise tax ID must be non-empty.")

        # Map enterprise compliance to numeric scale: Level 1=0.1, Level 2=0.3, Level 3=0.6, Level 4=0.8, Level 5=1.0
        ent_weights = {
            EnterpriseComplianceLevel.LEVEL_1_AEO_PRIORITY: 0.1,
            EnterpriseComplianceLevel.LEVEL_2_HIGH_COMPLIANCE: 0.3,
            EnterpriseComplianceLevel.LEVEL_3_MEDIUM_COMPLIANCE: 0.6,
            EnterpriseComplianceLevel.LEVEL_4_LOW_COMPLIANCE: 0.8,
            EnterpriseComplianceLevel.LEVEL_5_NON_COMPLIANT: 1.0,
        }
        e_weight = ent_weights.get(data.enterprise_level, 0.6)

        # R = 0.40 * E + 0.35 * H + 0.25 * O
        hs_clamped = max(0.0, min(1.0, data.hs_risk_tier))
        org_clamped = max(0.0, min(1.0, data.origin_risk_tier))
        score = 0.40 * e_weight + 0.35 * hs_clamped + 0.25 * org_clamped

        # Channeling threshold
        if data.has_intelligence_alert or score >= 0.70:
            channel = CustomsChannel.RED_CHANNEL
            c_name_vi = "Luồng Đỏ (Kiểm tra thực tế hàng hóa)"
            c_name_en = "Red Channel (Physical Inspection Required)"
            sla = 8.0
            exempt_doc = False
            exempt_phy = False
        elif score >= 0.35:
            channel = CustomsChannel.YELLOW_CHANNEL
            c_name_vi = "Luồng Vàng (Kiểm tra chi tiết hồ sơ)"
            c_name_en = "Yellow Channel (Detailed Documentary Audit)"
            sla = 2.0
            exempt_doc = False
            exempt_phy = True
        else:
            channel = CustomsChannel.GREEN_CHANNEL
            c_name_vi = "Luồng Xanh (Thông quan tự động)"
            c_name_en = "Green Channel (Automated Clearance)"
            sla = 0.0014  # ~5 seconds
            exempt_doc = True
            exempt_phy = True

        token_raw = f"{data.declaration_number}:{channel.value}:{score:.4f}:{data.enterprise_tax_id}"
        release_token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        summary_vi = (
            f"Tờ khai {data.declaration_number}: Phân luồng {c_name_vi}. "
            f"Điểm rủi ro: {score:.3f}. SLA xử lý: {sla}h. Mã xác thực: {release_token}"
        )
        summary_en = (
            f"Declaration {data.declaration_number}: Routed to {c_name_en}. "
            f"Risk score: {score:.3f}. Target SLA: {sla}h. Token: {release_token}"
        )

        return CustomsRiskChannelResult(
            declaration_number=data.declaration_number,
            channel=channel,
            channel_name_vi=c_name_vi,
            channel_name_en=c_name_en,
            risk_score=score,
            target_sla_hours=sla,
            exempt_document_check=exempt_doc,
            exempt_physical_inspection=exempt_phy,
            release_token=release_token,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )

    @staticmethod
    def verify_vasscm_gate_out(check: VasscmGateCheckInput) -> VasscmGateCheckResult:
        discrepancies: List[str] = []

        # 1. Customs declaration status check
        valid_decl_states = {"RELEASED", "CUSTOMS_CLEARED", "THONG_QUAN", "GIAI_PHONG_HANG"}
        if check.declaration_status.strip().upper() not in valid_decl_states:
            discrepancies.append(f"Tờ khai chưa thông quan (Trạng thái: {check.declaration_status})")

        # 2. Electronic Delivery Order (e-D/O) status
        if not check.edo_is_valid:
            discrepancies.append(f"Lệnh giao hàng điện tử (e-D/O: {check.edo_number}) không hợp lệ hoặc đã hết hạn")

        # 3. Seal number match
        if check.manifest_seal_number.strip().upper() != check.gate_scanned_seal_number.strip().upper():
            discrepancies.append(
                f"Sai lệch số chì container: Khai báo '{check.manifest_seal_number}' != Thực tế cổng '{check.gate_scanned_seal_number}'"
            )

        is_approved = len(discrepancies) == 0
        match_status = "MATCH_SUCCESS" if is_approved else "GATE_HOLD"

        token_raw = f"VASSCM:{check.declaration_number}:{check.container_number}:{check.gate_scanned_seal_number}:{match_status}"
        auth_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()

        if is_approved:
            summary_vi = f"VASSCM XÁC THỰC THÀNH CÔNG: Container {check.container_number} đủ điều kiện qua cổng ra cảng."
            summary_en = f"VASSCM VERIFICATION APPROVED: Container {check.container_number} cleared for gate-out."
        else:
            summary_vi = f"VASSCM TẠM GIỮ CỔNG (GATE HOLD): Phát hiện {len(discrepancies)} điểm sai lệch cho {check.container_number}."
            summary_en = f"VASSCM GATE HOLD: Detected {len(discrepancies)} discrepancies for container {check.container_number}."

        return VasscmGateCheckResult(
            declaration_number=check.declaration_number,
            container_number=check.container_number,
            is_gate_pass_approved=is_approved,
            match_status=match_status,
            discrepancy_reasons=discrepancies,
            vasscm_auth_hash=auth_hash,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )
