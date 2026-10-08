"""Maritime Air Emission (MARPOL VI / CII), Charter Party Financials, Towage & Drydock Tariffs, and Customs STS Manifest Suite.

Phases 295-298 Simplest Viable Maritime Operational Suite.
- Phase 295: MARPOL Annex VI Air Emissions, CII Rating Tracker & SEEMP Alert, ECA Bunker Sulphur Log
- Phase 296: Charter Party Financials: Time Charter Off-Hire Deductions & Voyage Charter Demurrage/Despatch
- Phase 297: Circular 39/2023/TT-BGTVT Towage Dues & Drydock Repair Budget Variance
- Phase 298: Customs Ship-to-Ship (STS) Transfer Permit & Mother-to-Lighter Split Manifest Engine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional


# ==============================================================================
# Phase 295: MARPOL Annex VI Air Emissions & CII Engine
# ==============================================================================

class CiiRating(str, Enum):
    """CII Operational Carbon Intensity Rating (IMO MEPC.336(76))."""
    RATING_A = "A"  # Major superior
    RATING_B = "B"  # Minor superior
    RATING_C = "C"  # Moderate
    RATING_D = "D"  # Minor inferior
    RATING_E = "E"  # Inferior


class FuelType(str, Enum):
    """Marine Fuel Types and their Carbon Conversion Factors (Cf)."""
    VLSFO = "VLSFO"  # Very Low Sulphur Fuel Oil (Cf = 3.151)
    ULSFO = "ULSFO"  # Ultra Low Sulphur Fuel Oil (Cf = 3.151)
    LSMGO = "LSMGO"  # Low Sulphur Marine Gas Oil (Cf = 3.206)
    MGO = "MGO"      # Marine Gas Oil (Cf = 3.206)
    HFO = "HFO"      # Heavy Fuel Oil (Cf = 3.114)
    LNG = "LNG"      # Liquefied Natural Gas (Cf = 2.750)
    LPG = "LPG"      # Liquefied Petroleum Gas (Cf = 3.000)
    BIOFUEL = "BIOFUEL"  # Biofuel Blend (Cf = 2.800)


@dataclass
class BunkerSulphurLog:
    """Bunker Delivery Note (BDN) & Fuel Sulphur Verification Log."""
    bunker_id: str
    fuel_type: FuelType
    sulphur_content_pct: float  # % m/m
    is_in_eca: bool  # Emission Control Area (ECA/SECA)
    bunker_date: str
    port_name: str
    supplier_name: str

    def is_compliant(self) -> bool:
        """Check compliance: <= 0.10% m/m in ECA; <= 0.50% m/m globally (IMO 2020)."""
        limit = 0.10 if self.is_in_eca else 0.50
        return self.sulphur_content_pct <= limit

    def max_allowed_sulphur(self) -> float:
        return 0.10 if self.is_in_eca else 0.50


@dataclass
class VesselCiiAssessmentInput:
    """Input for CII evaluation and multi-year rating tracking."""
    vessel_name: str
    imo_number: str
    dwt: float  # Deadweight tonnage
    distance_traveled_nm: float
    fuel_consumption_mt: Dict[FuelType, float]  # Metric tons consumed per fuel
    historical_ratings: List[CiiRating] = field(default_factory=list)  # Prior years (up to 3 years)
    year: int = 2026


@dataclass
class CiiAssessmentResult:
    """Result of CII calculation and SEEMP compliance check."""
    vessel_name: str
    imo_number: str
    year: int
    total_co2_emissions_mt: float
    attained_cii: float  # gCO2 / (dwt * nm)
    rating: CiiRating
    requires_seemp_corrective_action_plan: bool
    seemp_reason: str
    is_compliant: bool
    remarks: str
    verification_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "imo_number": self.imo_number,
            "year": self.year,
            "total_co2_emissions_mt": round(self.total_co2_emissions_mt, 2),
            "attained_cii": round(self.attained_cii, 4),
            "rating": self.rating.value,
            "requires_seemp_corrective_action_plan": self.requires_seemp_corrective_action_plan,
            "seemp_reason": self.seemp_reason,
            "is_compliant": self.is_compliant,
            "remarks": self.remarks,
            "verification_hash": self.verification_hash,
        }


class MarpolAirCiiEngine:
    """MARPOL Annex VI Air Pollution & CII Rating Engine."""

    CF_FACTORS: Dict[FuelType, float] = {
        FuelType.VLSFO: 3.151,
        FuelType.ULSFO: 3.151,
        FuelType.LSMGO: 3.206,
        FuelType.MGO: 3.206,
        FuelType.HFO: 3.114,
        FuelType.LNG: 2.750,
        FuelType.LPG: 3.000,
        FuelType.BIOFUEL: 2.800,
    }

    @classmethod
    def evaluate(cls, sample: VesselCiiAssessmentInput) -> CiiAssessmentResult:
        # 1. Total CO2 emissions
        total_co2_mt = 0.0
        for fuel, mt in sample.fuel_consumption_mt.items():
            cf = cls.CF_FACTORS.get(fuel, 3.151)
            total_co2_mt += mt * cf

        # 2. Attained CII = (Total CO2 in grams) / (DWT * Distance in NM)
        transport_work = sample.dwt * max(sample.distance_traveled_nm, 1.0)
        attained_cii = (total_co2_mt * 1_000_000.0) / transport_work

        # 3. Reference CII benchmark baseline for bulk/general cargo proxy
        # Baseline reference proxy: CII_ref = 4.5 * (dwt^-0.15) * 10
        ref_cii = 4.5 * (max(sample.dwt, 1000.0) ** -0.15) * 10.0
        ratio = attained_cii / max(ref_cii, 0.01)

        # 4. Rating derivation
        if ratio <= 0.82:
            rating = CiiRating.RATING_A
        elif ratio <= 0.94:
            rating = CiiRating.RATING_B
        elif ratio <= 1.06:
            rating = CiiRating.RATING_C
        elif ratio <= 1.18:
            rating = CiiRating.RATING_D
        else:
            rating = CiiRating.RATING_E

        # 5. SEEMP Part III Corrective Action Plan Rule:
        # Required if: Single year rated 'E' OR three consecutive years rated 'D'
        recent_ratings = sample.historical_ratings[-2:] + [rating] if len(sample.historical_ratings) >= 2 else sample.historical_ratings + [rating]
        requires_seemp = False
        seemp_reason = "Không cần kế hoạch hiệu chỉnh SEEMP (Xếp hạng đạt yêu cầu)."

        if rating == CiiRating.RATING_E:
            requires_seemp = True
            seemp_reason = "Bắt buộc lập Kế hoạch Hiệu chỉnh SEEMP Part III: Tàu xếp hạng E trong năm đánh giá."
        elif len(recent_ratings) >= 3 and all(r == CiiRating.RATING_D for r in recent_ratings[-3:]):
            requires_seemp = True
            seemp_reason = "Bắt buộc lập Kế hoạch Hiệu chỉnh SEEMP Part III: Tàu xếp hạng D trong 3 năm liên tiếp."

        is_compliant = not requires_seemp
        remarks = (
            f"Chỉ số CII đạt được: {attained_cii:.2f} gCO2/dwt.nm (Hạng {rating.value}). "
            f"Tổng lượng phát thải CO2: {total_co2_mt:,.1f} tấn."
        )

        # Verification hash
        raw_token = f"{sample.vessel_name}|{sample.imo_number}|{sample.year}|{attained_cii:.4f}|{rating.value}|{requires_seemp}"
        token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        return CiiAssessmentResult(
            vessel_name=sample.vessel_name,
            imo_number=sample.imo_number,
            year=sample.year,
            total_co2_emissions_mt=total_co2_mt,
            attained_cii=attained_cii,
            rating=rating,
            requires_seemp_corrective_action_plan=requires_seemp,
            seemp_reason=seemp_reason,
            is_compliant=is_compliant,
            remarks=remarks,
            verification_hash=token,
        )


# ==============================================================================
# Phase 296: Charter Party (CP) Financials Engine
# ==============================================================================

class CharterType(str, Enum):
    TIME_CHARTER = "TIME_CHARTER"
    VOYAGE_CHARTER = "VOYAGE_CHARTER"


class OffHireReason(str, Enum):
    ENGINE_BREAKDOWN = "ENGINE_BREAKDOWN"
    CREW_STRIKE_DEFICIENCY = "CREW_STRIKE_DEFICIENCY"
    DRYDOCK_REPAIR = "DRYDOCK_REPAIR"
    PORT_STATE_CONTROL_DETENTION = "PORT_STATE_CONTROL_DETENTION"
    DEVIATION_FOR_CREW_TREATMENT = "DEVIATION_FOR_CREW_TREATMENT"
    WEATHER_PIRACY_DAMAGE = "WEATHER_PIRACY_DAMAGE"


@dataclass
class TimeCharterOffHireInput:
    """Input for Time Charter Off-Hire & Bunker Compensation calculation."""
    charter_id: str
    vessel_name: str
    daily_hire_rate_usd: float
    off_hire_hours: float
    reason: OffHireReason
    bunker_consumed_mt: float  # Dầu tiêu hao trong thời gian off-hire
    bunker_price_usd_per_mt: float
    auxiliary_diesel_consumed_mt: float = 0.0
    diesel_price_usd_per_mt: float = 0.0


@dataclass
class TimeCharterOffHireResult:
    """Financial statement of Time Charter Off-Hire deduction."""
    charter_id: str
    vessel_name: str
    off_hire_days: float
    hire_deduction_usd: float
    bunker_deduction_usd: float
    total_deduction_usd: float
    reason: OffHireReason
    remarks: str
    settlement_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "charter_id": self.charter_id,
            "vessel_name": self.vessel_name,
            "off_hire_days": round(self.off_hire_days, 4),
            "hire_deduction_usd": round(self.hire_deduction_usd, 2),
            "bunker_deduction_usd": round(self.bunker_deduction_usd, 2),
            "total_deduction_usd": round(self.total_deduction_usd, 2),
            "reason": self.reason.value,
            "remarks": self.remarks,
            "settlement_token": self.settlement_token,
        }


@dataclass
class VoyageLaytimeStatement:
    """Statement of Facts (SOF) Laytime Calculation for Voyage Charter."""
    charter_id: str
    vessel_name: str
    allowed_laytime_hours: float
    actual_time_used_hours: float
    demurrage_rate_per_day_usd: float
    despatch_rate_ratio: float = 0.50  # Typically half of demurrage rate (DHD)


@dataclass
class VoyageDemurrageResult:
    """Outcome of Voyage Demurrage or Despatch."""
    charter_id: str
    vessel_name: str
    time_difference_hours: float
    is_demurrage: bool
    is_despatch: bool
    demurrage_amount_usd: float
    despatch_amount_usd: float
    net_financial_impact_usd: float  # Positive = Charterer owes Owner; Negative = Owner pays Charterer
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "charter_id": self.charter_id,
            "vessel_name": self.vessel_name,
            "time_difference_hours": round(self.time_difference_hours, 2),
            "is_demurrage": self.is_demurrage,
            "is_despatch": self.is_despatch,
            "demurrage_amount_usd": round(self.demurrage_amount_usd, 2),
            "despatch_amount_usd": round(self.despatch_amount_usd, 2),
            "net_financial_impact_usd": round(self.net_financial_impact_usd, 2),
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class CharterPartyFinancialEngine:
    """Charter Party Off-Hire & Laytime/Demurrage Financial Engine."""

    @classmethod
    def calculate_off_hire(cls, req: TimeCharterOffHireInput) -> TimeCharterOffHireResult:
        off_hire_days = req.off_hire_hours / 24.0
        hire_deduction = off_hire_days * req.daily_hire_rate_usd

        bunker_deduction = (
            (req.bunker_consumed_mt * req.bunker_price_usd_per_mt) +
            (req.auxiliary_diesel_consumed_mt * req.diesel_price_usd_per_mt)
        )
        total_deduction = hire_deduction + bunker_deduction

        remarks = (
            f"Khấu trừ thuê tàu ({req.off_hire_hours:.1f}h = {off_hire_days:.2f} ngày): "
            f"${hire_deduction:,.2f} + Bồi hoàn nhiên liệu: ${bunker_deduction:,.2f}."
        )

        raw = f"{req.charter_id}|{req.vessel_name}|{req.off_hire_hours}|{total_deduction:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return TimeCharterOffHireResult(
            charter_id=req.charter_id,
            vessel_name=req.vessel_name,
            off_hire_days=off_hire_days,
            hire_deduction_usd=hire_deduction,
            bunker_deduction_usd=bunker_deduction,
            total_deduction_usd=total_deduction,
            reason=req.reason,
            remarks=remarks,
            settlement_token=token,
        )

    @classmethod
    def calculate_demurrage(cls, req: VoyageLaytimeStatement) -> VoyageDemurrageResult:
        diff_hours = req.actual_time_used_hours - req.allowed_laytime_hours
        demurrage_amount = 0.0
        despatch_amount = 0.0
        is_demurrage = False
        is_despatch = False

        hourly_demurrage = req.demurrage_rate_per_day_usd / 24.0
        hourly_despatch = (req.demurrage_rate_per_day_usd * req.despatch_rate_ratio) / 24.0

        if diff_hours > 0:
            is_demurrage = True
            demurrage_amount = diff_hours * hourly_demurrage
            net_impact = demurrage_amount
            remarks = f"Phạt dôi nhật (Demurrage) do vượt {diff_hours:.2f} giờ làm hàng."
        elif diff_hours < 0:
            is_despatch = True
            saved_hours = abs(diff_hours)
            despatch_amount = saved_hours * hourly_despatch
            net_impact = -despatch_amount
            remarks = f"Thưởng giải phóng tàu sớm (Despatch) do tiết kiệm {saved_hours:.2f} giờ làm hàng."
        else:
            net_impact = 0.0
            remarks = "Thời gian làm hàng chính xác bằng thời gian cho phép (Laytime exact)."

        raw = f"{req.charter_id}|{req.vessel_name}|{diff_hours:.2f}|{net_impact:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return VoyageDemurrageResult(
            charter_id=req.charter_id,
            vessel_name=req.vessel_name,
            time_difference_hours=diff_hours,
            is_demurrage=is_demurrage,
            is_despatch=is_despatch,
            demurrage_amount_usd=demurrage_amount,
            despatch_amount_usd=despatch_amount,
            net_financial_impact_usd=net_impact,
            remarks=remarks,
            audit_hash=token,
        )


# ==============================================================================
# Phase 297: Towage Dues (TT 39/2023) & Drydock Budget Variance Engine
# ==============================================================================

class TowageTugPower(str, Enum):
    UNDER_1000_HP = "UNDER_1000_HP"
    HP_1000_TO_1999 = "HP_1000_TO_1999"
    HP_2000_TO_2999 = "HP_2000_TO_2999"
    HP_3000_TO_3999 = "HP_3000_TO_3999"
    HP_4000_AND_ABOVE = "HP_4000_AND_ABOVE"


class PortZoneArea(str, Enum):
    ZONE_I_NORTH = "ZONE_I_NORTH"
    ZONE_II_CENTRAL = "ZONE_II_CENTRAL"
    ZONE_III_SOUTH = "ZONE_III_SOUTH"


@dataclass
class TowageServiceInput:
    """Input for Seaport Tugboat Towage Service (Circular 39/2023/TT-BGTVT)."""
    vessel_name: str
    vessel_gt: float
    tug_power: TowageTugPower
    tug_quantity: int
    operation_hours: float
    zone: PortZoneArea = PortZoneArea.ZONE_III_SOUTH
    is_international: bool = True
    is_holiday_or_night: bool = False  # Phụ thu 30% ngoài giờ/lễ


@dataclass
class TowageServiceResult:
    """Tariff result for seaport towage service."""
    vessel_name: str
    vessel_gt: float
    tug_quantity: int
    operation_hours: float
    base_rate_per_tug_hour: float
    surcharge_rate: float
    total_towage_charge: float
    currency: str
    remarks: str
    receipt_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "vessel_gt": self.vessel_gt,
            "tug_quantity": self.tug_quantity,
            "operation_hours": round(self.operation_hours, 2),
            "base_rate_per_tug_hour": round(self.base_rate_per_tug_hour, 2),
            "surcharge_rate": self.surcharge_rate,
            "total_towage_charge": round(self.total_towage_charge, 2),
            "currency": self.currency,
            "remarks": self.remarks,
            "receipt_hash": self.receipt_hash,
        }


@dataclass
class DrydockRepairItem:
    """Single repair work package in shipyard drydocking."""
    category: str  # e.g., "Hull Blasting & Painting", "Tailshaft & Propeller", "Main Engine Overhaul"
    budgeted_cost_usd: float
    actual_cost_usd: float


@dataclass
class DrydockVarianceReport:
    """Drydocking Budget vs. Actual Variance Report."""
    vessel_name: str
    shipyard_name: str
    total_budgeted_usd: float
    total_actual_usd: float
    variance_amount_usd: float
    variance_percentage: float
    is_over_budget: bool
    items_breakdown: List[Dict[str, Any]]
    recommendation: str
    audit_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "shipyard_name": self.shipyard_name,
            "total_budgeted_usd": round(self.total_budgeted_usd, 2),
            "total_actual_usd": round(self.total_actual_usd, 2),
            "variance_amount_usd": round(self.variance_amount_usd, 2),
            "variance_percentage": round(self.variance_percentage, 2),
            "is_over_budget": self.is_over_budget,
            "items_breakdown": self.items_breakdown,
            "recommendation": self.recommendation,
            "audit_token": self.audit_token,
        }


class TowageDrydockTariffEngine:
    """Towage Rates (Circular 39/2023) and Drydock Variance Engine."""

    # Base hourly rates per tugboat based on power (USD for Intl, VND for Domestic)
    HOURLY_RATES_USD: Dict[TowageTugPower, float] = {
        TowageTugPower.UNDER_1000_HP: 110.0,
        TowageTugPower.HP_1000_TO_1999: 180.0,
        TowageTugPower.HP_2000_TO_2999: 290.0,
        TowageTugPower.HP_3000_TO_3999: 420.0,
        TowageTugPower.HP_4000_AND_ABOVE: 580.0,
    }

    HOURLY_RATES_VND: Dict[TowageTugPower, float] = {
        TowageTugPower.UNDER_1000_HP: 2_600_000.0,
        TowageTugPower.HP_1000_TO_1999: 4_300_000.0,
        TowageTugPower.HP_2000_TO_2999: 7_000_000.0,
        TowageTugPower.HP_3000_TO_3999: 10_000_000.0,
        TowageTugPower.HP_4000_AND_ABOVE: 14_000_000.0,
    }

    @classmethod
    def calculate_towage(cls, req: TowageServiceInput) -> TowageServiceResult:
        currency = "USD" if req.is_international else "VND"
        rates_dict = cls.HOURLY_RATES_USD if req.is_international else cls.HOURLY_RATES_VND
        base_rate = rates_dict.get(req.tug_power, 290.0 if req.is_international else 7_000_000.0)

        surcharge = 0.30 if req.is_holiday_or_night else 0.0
        effective_rate = base_rate * (1.0 + surcharge)
        total_charge = effective_rate * req.tug_quantity * max(req.operation_hours, 1.0)

        remarks = (
            f"Dịch vụ {req.tug_quantity} tàu kéo ({req.tug_power.value}) trong {req.operation_hours:.1f}h. "
            f"Phụ thu: {surcharge * 100:.0f}%."
        )

        raw = f"{req.vessel_name}|{req.vessel_gt}|{req.tug_power.value}|{total_charge:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return TowageServiceResult(
            vessel_name=req.vessel_name,
            vessel_gt=req.vessel_gt,
            tug_quantity=req.tug_quantity,
            operation_hours=req.operation_hours,
            base_rate_per_tug_hour=base_rate,
            surcharge_rate=surcharge,
            total_towage_charge=total_charge,
            currency=currency,
            remarks=remarks,
            receipt_hash=token,
        )

    @classmethod
    def evaluate_drydock_variance(
        cls,
        vessel_name: str,
        shipyard_name: str,
        repair_items: List[DrydockRepairItem],
    ) -> DrydockVarianceReport:
        total_budget = sum(item.budgeted_cost_usd for item in repair_items)
        total_actual = sum(item.actual_cost_usd for item in repair_items)
        variance = total_actual - total_budget
        variance_pct = (variance / total_budget * 100.0) if total_budget > 0 else 0.0
        is_over = variance > 0

        breakdown = []
        for item in repair_items:
            item_var = item.actual_cost_usd - item.budgeted_cost_usd
            item_pct = (item_var / item.budgeted_cost_usd * 100.0) if item.budgeted_cost_usd > 0 else 0.0
            breakdown.append({
                "category": item.category,
                "budgeted_usd": item.budgeted_cost_usd,
                "actual_usd": item.actual_cost_usd,
                "variance_usd": item_var,
                "variance_pct": round(item_pct, 2),
            })

        if is_over:
            recommendation = f"Vượt dự toán ${variance:,.2f} ({variance_pct:+.1f}%). Cần rà soát các hạng mục phát sinh thêm (Unforeseen works) và đàm phán giảm giá."
        else:
            recommendation = f"Kiểm soát ngân sách tốt, tiết kiệm ${abs(variance):,.2f} ({variance_pct:.1f}%)."

        raw = f"{vessel_name}|{shipyard_name}|{total_actual:.2f}|{variance:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return DrydockVarianceReport(
            vessel_name=vessel_name,
            shipyard_name=shipyard_name,
            total_budgeted_usd=total_budget,
            total_actual_usd=total_actual,
            variance_amount_usd=variance,
            variance_percentage=variance_pct,
            is_over_budget=is_over,
            items_breakdown=breakdown,
            recommendation=recommendation,
            audit_token=token,
        )


# ==============================================================================
# Phase 298: Customs STS (Ship-to-Ship) Permit & Split Manifest Engine
# ==============================================================================

class StsOperationType(str, Enum):
    LIGHTERAGE_DISCHARGE = "LIGHTERAGE_DISCHARGE"  # Sang mạn hạ tải
    BUNKER_TRANSFER = "BUNKER_TRANSFER"            # Cung ứng dầu chuyển tải
    TRANSSHIPMENT = "TRANSSHIPMENT"                # Chuyển tải xuất nhập khẩu


@dataclass
class LighterVesselAllocation:
    """Manifest sub-allocation to a lighter / barge vessel."""
    lighter_vessel_name: str
    lighter_call_sign: str
    allocated_weight_mt: float
    package_count: int
    destination_customs_sub_department: str  # Chi cục Hải quan tiếp nhận


@dataclass
class StsPermitRecord:
    """Customs Ship-to-Ship Transfer Permit record."""
    permit_number: str
    mother_vessel_name: str
    mother_imo: str
    operation_type: StsOperationType
    anchor_location_zone: str  # Vị trí neo chuyển tải (e.g. Vũng Tàu, Hòn Gai)
    total_cargo_weight_mt: float
    total_packages: int
    valid_from: str
    valid_until: str
    is_approved: bool = True


@dataclass
class SplitManifestResult:
    """Result of splitting a mother vessel master manifest to lighters."""
    permit_number: str
    mother_vessel_name: str
    total_mother_weight_mt: float
    total_transferred_weight_mt: float
    remaining_weight_on_mother_mt: float
    is_balanced: bool
    sub_manifests: List[Dict[str, Any]]
    discrepancy_remarks: str
    customs_manifest_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permit_number": self.permit_number,
            "mother_vessel_name": self.mother_vessel_name,
            "total_mother_weight_mt": round(self.total_mother_weight_mt, 2),
            "total_transferred_weight_mt": round(self.total_transferred_weight_mt, 2),
            "remaining_weight_on_mother_mt": round(self.remaining_weight_on_mother_mt, 2),
            "is_balanced": self.is_balanced,
            "sub_manifests": self.sub_manifests,
            "discrepancy_remarks": self.discrepancy_remarks,
            "customs_manifest_hash": self.customs_manifest_hash,
        }


class CustomsStsManifestEngine:
    """Customs Ship-to-Ship Permit & Split Manifest Engine."""

    @classmethod
    def split_manifest(
        cls,
        permit: StsPermitRecord,
        allocations: List[LighterVesselAllocation],
    ) -> SplitManifestResult:
        total_transferred_mt = sum(a.allocated_weight_mt for a in allocations)
        remaining_mt = permit.total_cargo_weight_mt - total_transferred_mt
        is_balanced = remaining_mt >= -0.001  # Cannot allocate more than total cargo

        sub_manifests = []
        for idx, alloc in enumerate(allocations, 1):
            sub_id = f"{permit.permit_number}-SUB{idx:02d}"
            sub_manifests.append({
                "sub_manifest_id": sub_id,
                "lighter_vessel": alloc.lighter_vessel_name,
                "call_sign": alloc.lighter_call_sign,
                "weight_mt": alloc.allocated_weight_mt,
                "packages": alloc.package_count,
                "destination_customs": alloc.destination_customs_sub_department,
            })

        if remaining_mt < -0.001:
            remarks = f"CẢNH BÁO HẢI QUAN: Khối lượng phân bổ cho tàu con ({total_transferred_mt:.2f} MT) vượt quá bản khai tàu mẹ ({permit.total_cargo_weight_mt:.2f} MT)!"
        elif remaining_mt == 0:
            remarks = "Toàn bộ hàng hóa trên tàu mẹ đã được chuyển tải hoàn tất sang các tàu con/xà lan."
        else:
            remarks = f"Chuyển tải một phần: Còn lại {remaining_mt:,.2f} MT trên tàu mẹ {permit.mother_vessel_name}."

        raw = f"{permit.permit_number}|{permit.mother_vessel_name}|{total_transferred_mt:.2f}|{remaining_mt:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return SplitManifestResult(
            permit_number=permit.permit_number,
            mother_vessel_name=permit.mother_vessel_name,
            total_mother_weight_mt=permit.total_cargo_weight_mt,
            total_transferred_weight_mt=total_transferred_mt,
            remaining_weight_on_mother_mt=remaining_mt,
            is_balanced=is_balanced,
            sub_manifests=sub_manifests,
            discrepancy_remarks=remarks,
            customs_manifest_hash=token,
        )
