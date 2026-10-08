"""
Mekong Maritime Garbage, STCW Rest, Port Wharfage & CFS E-Seal Engine (Phases 287-290).

Statutory Frameworks:
- Phase 287: MARPOL Annex V Regs. 3-6, MEPC.201(62), MEPC.277(70), MEPC.295(71),
  VMC 2015 Arts. 107-111 & Circular 41/2020/TT-BGTVT (Garbage Record Book & Placards).
- Phase 288: STCW 2010 Manila Amendments Table A-VIII/1, MLC 2006 Standard A2.3,
  Vietnam Maritime Code 2015 Art. 60 & Labor Code 2019 (Seafarer Hours of Rest).
- Phase 289: Circular 39/2023/TT-BGTVT & Circular 12/2024/TT-BGTVT on Seaport Wharfage,
  Berth Occupancy, Buoyage & Overstay Penalties.
- Phase 290: Law on Customs 2014 Arts. 61-63, Decree 08/2015/ND-CP, Circular 38/2015/TT-BTC,
  Circular 39/2018/TT-BTC & General Department of Customs E-Seal RFID/GPS Regulations.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Dict, List, Any


# ============================================================================
# Phase 287: MARPOL Annex V Garbage Discharge & GRB Engine
# ============================================================================

class GarbageCategory(str, Enum):
    PLASTICS = "PLASTICS"
    FOOD_WASTE_COMMINUTED = "FOOD_WASTE_COMMINUTED"
    FOOD_WASTE_UNCOMMINUTED = "FOOD_WASTE_UNCOMMINUTED"
    DOMESTIC_WASTE = "DOMESTIC_WASTE"
    COOKING_OIL = "COOKING_OIL"
    INCINERATOR_ASHES = "INCINERATOR_ASHES"
    CARGO_RESIDUES_NON_HME = "CARGO_RESIDUES_NON_HME"
    CARGO_RESIDUES_HME = "CARGO_RESIDUES_HME"
    ANIMAL_CARCASSES = "ANIMAL_CARCASSES"


class SeaAreaZone(str, Enum):
    OUTSIDE_SPECIAL_AREA = "OUTSIDE_SPECIAL_AREA"
    SPECIAL_AREA = "SPECIAL_AREA"
    PORT_LIMITS = "PORT_LIMITS"


class GarbageDischargeVerdict(str, Enum):
    PERMITTED_OVERBOARD = "PERMITTED_OVERBOARD"
    PROHIBITED_MUST_RETAIN = "PROHIBITED_MUST_RETAIN"
    PROHIBITED_SPECIAL_AREA = "PROHIBITED_SPECIAL_AREA"
    PROHIBITED_DISTANCE_INSUFFICIENT = "PROHIBITED_DISTANCE_INSUFFICIENT"
    PROHIBITED_VESSEL_NOT_EN_ROUTE = "PROHIBITED_VESSEL_NOT_EN_ROUTE"
    PROHIBITED_PORT_WATERS = "PROHIBITED_PORT_WATERS"


@dataclass
class GarbageDischargeInput:
    vessel_name: str
    imo_number: str
    garbage_category: GarbageCategory
    zone: SeaAreaZone
    distance_from_land_nm: float
    vessel_speed_knots: float
    estimated_volume_m3: float
    is_special_area_port_available: bool = True
    water_depth_meters: float = 50.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "imo_number": self.imo_number,
            "garbage_category": self.garbage_category.value,
            "zone": self.zone.value,
            "distance_from_land_nm": round(self.distance_from_land_nm, 2),
            "vessel_speed_knots": round(self.vessel_speed_knots, 2),
            "estimated_volume_m3": round(self.estimated_volume_m3, 3),
            "is_special_area_port_available": self.is_special_area_port_available,
            "water_depth_meters": round(self.water_depth_meters, 1),
        }


@dataclass
class GarbageDischargeResult:
    verdict: GarbageDischargeVerdict
    is_discharge_permitted: bool
    required_min_distance_nm: float
    grb_log_code: str
    verification_token: str
    remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "is_discharge_permitted": self.is_discharge_permitted,
            "required_min_distance_nm": self.required_min_distance_nm,
            "grb_log_code": self.grb_log_code,
            "verification_token": self.verification_token,
            "remarks": self.remarks,
        }


class GarbageDischargeEngine:
    """Evaluates shipboard garbage discharge legality under MARPOL Annex V."""

    MIN_EN_ROUTE_SPEED_KNOTS: float = 0.5

    @classmethod
    def evaluate(cls, sample: GarbageDischargeInput) -> GarbageDischargeResult:
        cat = sample.garbage_category
        zone = sample.zone
        dist = sample.distance_from_land_nm
        speed = sample.vessel_speed_knots
        depth = sample.water_depth_meters

        token_raw = f"{sample.imo_number}-{cat.value}-{dist}-{speed}-{sample.estimated_volume_m3}"
        verification_token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        if zone == SeaAreaZone.PORT_LIMITS:
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PROHIBITED_PORT_WATERS,
                is_discharge_permitted=False,
                required_min_distance_nm=3.0,
                grb_log_code="GRB-PRF-PORT",
                verification_token=verification_token,
                remarks="Discharge prohibited in port waters. Deliver to Port Reception Facility (PRF).",
            )

        # Non-dischargeable categories anywhere at sea
        if cat in (
            GarbageCategory.PLASTICS,
            GarbageCategory.DOMESTIC_WASTE,
            GarbageCategory.COOKING_OIL,
            GarbageCategory.INCINERATOR_ASHES,
            GarbageCategory.CARGO_RESIDUES_HME,
        ):
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PROHIBITED_MUST_RETAIN,
                is_discharge_permitted=False,
                required_min_distance_nm=999.0,
                grb_log_code="GRB-HOLD-RETAIN",
                verification_token=verification_token,
                remarks=f"MARPOL Annex V strictly prohibits overboard discharge of {cat.value}. Retain on board.",
            )

        # En route requirement for allowable overboard discharges
        if speed < cls.MIN_EN_ROUTE_SPEED_KNOTS:
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PROHIBITED_VESSEL_NOT_EN_ROUTE,
                is_discharge_permitted=False,
                required_min_distance_nm=3.0,
                grb_log_code="GRB-EN-ROUTE-FAIL",
                verification_token=verification_token,
                remarks=f"Vessel speed {speed} kts < 0.5 kts minimum required en-route condition.",
            )

        if cat == GarbageCategory.FOOD_WASTE_COMMINUTED:
            if zone == SeaAreaZone.SPECIAL_AREA:
                min_dist = 12.0
                if dist < min_dist:
                    return GarbageDischargeResult(
                        verdict=GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT,
                        is_discharge_permitted=False,
                        required_min_distance_nm=min_dist,
                        grb_log_code="GRB-SA-FOOD-12NM",
                        verification_token=verification_token,
                        remarks=f"Food waste in Special Area requires distance >= 12 NM (actual: {dist} NM).",
                    )
            else:
                min_dist = 3.0
                if dist < min_dist:
                    return GarbageDischargeResult(
                        verdict=GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT,
                        is_discharge_permitted=False,
                        required_min_distance_nm=min_dist,
                        grb_log_code="GRB-OSA-FOOD-3NM",
                        verification_token=verification_token,
                        remarks=f"Comminuted food waste outside Special Area requires distance >= 3 NM (actual: {dist} NM).",
                    )
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PERMITTED_OVERBOARD,
                is_discharge_permitted=True,
                required_min_distance_nm=min_dist,
                grb_log_code="GRB-PART-I-CAT-B",
                verification_token=verification_token,
                remarks="Comminuted food waste (<=25mm screen) discharge compliant with MARPOL Annex V.",
            )

        elif cat == GarbageCategory.FOOD_WASTE_UNCOMMINUTED:
            if zone == SeaAreaZone.SPECIAL_AREA:
                return GarbageDischargeResult(
                    verdict=GarbageDischargeVerdict.PROHIBITED_SPECIAL_AREA,
                    is_discharge_permitted=False,
                    required_min_distance_nm=999.0,
                    grb_log_code="GRB-SA-FOOD-UNCOMM-PROHIBITED",
                    verification_token=verification_token,
                    remarks="Uncomminuted food waste is strictly prohibited in MARPOL Special Areas.",
                )
            min_dist = 12.0
            if dist < min_dist:
                return GarbageDischargeResult(
                    verdict=GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT,
                    is_discharge_permitted=False,
                    required_min_distance_nm=min_dist,
                    grb_log_code="GRB-OSA-FOOD-12NM",
                    verification_token=verification_token,
                    remarks=f"Uncomminuted food waste outside Special Area requires >= 12 NM from land (actual: {dist} NM).",
                )
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PERMITTED_OVERBOARD,
                is_discharge_permitted=True,
                required_min_distance_nm=min_dist,
                grb_log_code="GRB-PART-I-CAT-B",
                verification_token=verification_token,
                remarks="Uncomminuted food waste discharge >= 12 NM compliant with MARPOL Annex V.",
            )

        elif cat == GarbageCategory.CARGO_RESIDUES_NON_HME:
            min_dist = 12.0
            if dist < min_dist:
                return GarbageDischargeResult(
                    verdict=GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT,
                    is_discharge_permitted=False,
                    required_min_distance_nm=min_dist,
                    grb_log_code="GRB-PART-II-DIST-FAIL",
                    verification_token=verification_token,
                    remarks=f"Non-HME cargo residues require >= 12 NM from land (actual: {dist} NM).",
                )
            if zone == SeaAreaZone.SPECIAL_AREA and sample.is_special_area_port_available:
                return GarbageDischargeResult(
                    verdict=GarbageDischargeVerdict.PROHIBITED_SPECIAL_AREA,
                    is_discharge_permitted=False,
                    required_min_distance_nm=min_dist,
                    grb_log_code="GRB-SA-RESIDUES-PROHIBITED",
                    verification_token=verification_token,
                    remarks="Cargo residues discharge in Special Area prohibited when port PRF facilities are available.",
                )
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PERMITTED_OVERBOARD,
                is_discharge_permitted=True,
                required_min_distance_nm=min_dist,
                grb_log_code="GRB-PART-II-CAT-J",
                verification_token=verification_token,
                remarks="Non-HME cargo hold washwater discharge compliant with MARPOL Annex V Part II.",
            )

        elif cat == GarbageCategory.ANIMAL_CARCASSES:
            if zone == SeaAreaZone.SPECIAL_AREA:
                return GarbageDischargeResult(
                    verdict=GarbageDischargeVerdict.PROHIBITED_SPECIAL_AREA,
                    is_discharge_permitted=False,
                    required_min_distance_nm=100.0,
                    grb_log_code="GRB-SA-CARCASSES-PROHIBITED",
                    verification_token=verification_token,
                    remarks="Animal carcasses discharge strictly prohibited in MARPOL Special Areas.",
                )
            min_dist = 100.0
            if dist < min_dist or depth < 100.0:
                return GarbageDischargeResult(
                    verdict=GarbageDischargeVerdict.PROHIBITED_DISTANCE_INSUFFICIENT,
                    is_discharge_permitted=False,
                    required_min_distance_nm=min_dist,
                    grb_log_code="GRB-CARCASSES-DEPTH-FAIL",
                    verification_token=verification_token,
                    remarks=f"Animal carcasses require distance >= 100 NM (actual: {dist} NM) and depth >= 100 m (actual: {depth} m).",
                )
            return GarbageDischargeResult(
                verdict=GarbageDischargeVerdict.PERMITTED_OVERBOARD,
                is_discharge_permitted=True,
                required_min_distance_nm=min_dist,
                grb_log_code="GRB-PART-I-CAT-K",
                verification_token=verification_token,
                remarks="Animal carcass discharge meets IMO MEPC.295(71) 100 NM / 100 m depth statutory criteria.",
            )

        return GarbageDischargeResult(
            verdict=GarbageDischargeVerdict.PROHIBITED_MUST_RETAIN,
            is_discharge_permitted=False,
            required_min_distance_nm=999.0,
            grb_log_code="GRB-UNKNOWN-FAIL",
            verification_token=verification_token,
            remarks="Unrecognized or unapproved discharge configuration.",
        )


# ============================================================================
# Phase 288: STCW 2010 Manila & MLC 2006 Seafarer Rest Hours Engine
# ============================================================================

class RestComplianceStatus(str, Enum):
    FULLY_COMPLIANT = "FULLY_COMPLIANT"
    VIOLATION_24H_TOTAL = "VIOLATION_24H_TOTAL"
    VIOLATION_24H_PERIODS = "VIOLATION_24H_PERIODS"
    VIOLATION_24H_CONTINUOUS = "VIOLATION_24H_CONTINUOUS"
    VIOLATION_INTERVAL_EXCEEDED = "VIOLATION_INTERVAL_EXCEEDED"
    VIOLATION_7D_TOTAL = "VIOLATION_7D_TOTAL"
    EMERGENCY_OVERRIDE_COMPENSATED = "EMERGENCY_OVERRIDE_COMPENSATED"


@dataclass
class RestPeriod:
    start_hour: float
    duration_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_hour": round(self.start_hour, 1),
            "duration_hours": round(self.duration_hours, 1),
        }


@dataclass
class SeafarerRestInput:
    seafarer_name: str
    rank: str
    rest_periods_24h: List[RestPeriod]
    total_rest_hours_past_6d: float
    interval_between_rests_hours: float
    is_emergency_drill_or_sar: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seafarer_name": self.seafarer_name,
            "rank": self.rank,
            "rest_periods_24h": [p.to_dict() for p in self.rest_periods_24h],
            "total_rest_hours_past_6d": round(self.total_rest_hours_past_6d, 1),
            "interval_between_rests_hours": round(self.interval_between_rests_hours, 1),
            "is_emergency_drill_or_sar": self.is_emergency_drill_or_sar,
        }


@dataclass
class SeafarerRestResult:
    compliance_status: RestComplianceStatus
    is_compliant: bool
    total_rest_24h: float
    total_rest_7d: float
    longest_continuous_rest: float
    period_count_24h: int
    compensation_rest_due_hours: float
    audit_remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compliance_status": self.compliance_status.value,
            "is_compliant": self.is_compliant,
            "total_rest_24h": round(self.total_rest_24h, 1),
            "total_rest_7d": round(self.total_rest_7d, 1),
            "longest_continuous_rest": round(self.longest_continuous_rest, 1),
            "period_count_24h": self.period_count_24h,
            "compensation_rest_due_hours": round(self.compensation_rest_due_hours, 1),
            "audit_remarks": self.audit_remarks,
        }


class SeafarerRestEngine:
    """Verifies Seafarer Hours of Rest under STCW A-VIII/1 & MLC Standard A2.3."""

    MIN_REST_24H: float = 10.0
    MIN_REST_7D: float = 77.0
    MIN_CONTINUOUS_PERIOD: float = 6.0
    MAX_PERIOD_COUNT: int = 2
    MAX_INTERVAL_HOURS: float = 14.0

    @classmethod
    def evaluate(cls, sample: SeafarerRestInput) -> SeafarerRestResult:
        periods = sample.rest_periods_24h
        total_24h = sum(p.duration_hours for p in periods)
        total_7d = sample.total_rest_hours_past_6d + total_24h
        longest_p = max((p.duration_hours for p in periods), default=0.0)
        p_count = len(periods)
        interval = sample.interval_between_rests_hours

        if sample.is_emergency_drill_or_sar:
            comp_due = max(0.0, cls.MIN_REST_24H - total_24h)
            return SeafarerRestResult(
                compliance_status=RestComplianceStatus.EMERGENCY_OVERRIDE_COMPENSATED,
                is_compliant=True,
                total_rest_24h=total_24h,
                total_rest_7d=total_7d,
                longest_continuous_rest=longest_p,
                period_count_24h=p_count,
                compensation_rest_due_hours=comp_due,
                audit_remarks=f"Emergency/Drill exception invoked. Mandatory compensatory rest {comp_due} hrs required immediately.",
            )

        if total_24h < cls.MIN_REST_24H:
            return SeafarerRestResult(
                compliance_status=RestComplianceStatus.VIOLATION_24H_TOTAL,
                is_compliant=False,
                total_rest_24h=total_24h,
                total_rest_7d=total_7d,
                longest_continuous_rest=longest_p,
                period_count_24h=p_count,
                compensation_rest_due_hours=cls.MIN_REST_24H - total_24h,
                audit_remarks=f"Total 24h rest {total_24h} hrs < statutory minimum {cls.MIN_REST_24H} hrs.",
            )

        if p_count > cls.MAX_PERIOD_COUNT:
            return SeafarerRestResult(
                compliance_status=RestComplianceStatus.VIOLATION_24H_PERIODS,
                is_compliant=False,
                total_rest_24h=total_24h,
                total_rest_7d=total_7d,
                longest_continuous_rest=longest_p,
                period_count_24h=p_count,
                compensation_rest_due_hours=0.0,
                audit_remarks=f"Rest divided into {p_count} periods, exceeding maximum allowable 2 periods.",
            )

        if longest_p < cls.MIN_CONTINUOUS_PERIOD:
            return SeafarerRestResult(
                compliance_status=RestComplianceStatus.VIOLATION_24H_CONTINUOUS,
                is_compliant=False,
                total_rest_24h=total_24h,
                total_rest_7d=total_7d,
                longest_continuous_rest=longest_p,
                period_count_24h=p_count,
                compensation_rest_due_hours=0.0,
                audit_remarks=f"Longest continuous rest {longest_p} hrs < mandatory minimum {cls.MIN_CONTINUOUS_PERIOD} hrs.",
            )

        if interval > cls.MAX_INTERVAL_HOURS:
            return SeafarerRestResult(
                compliance_status=RestComplianceStatus.VIOLATION_INTERVAL_EXCEEDED,
                is_compliant=False,
                total_rest_24h=total_24h,
                total_rest_7d=total_7d,
                longest_continuous_rest=longest_p,
                period_count_24h=p_count,
                compensation_rest_due_hours=0.0,
                audit_remarks=f"Interval between consecutive rest periods {interval} hrs > statutory limit {cls.MAX_INTERVAL_HOURS} hrs.",
            )

        if total_7d < cls.MIN_REST_7D:
            return SeafarerRestResult(
                compliance_status=RestComplianceStatus.VIOLATION_7D_TOTAL,
                is_compliant=False,
                total_rest_24h=total_24h,
                total_rest_7d=total_7d,
                longest_continuous_rest=longest_p,
                period_count_24h=p_count,
                compensation_rest_due_hours=cls.MIN_REST_7D - total_7d,
                audit_remarks=f"Total 7-day rolling rest {total_7d} hrs < statutory minimum {cls.MIN_REST_7D} hrs.",
            )

        return SeafarerRestResult(
            compliance_status=RestComplianceStatus.FULLY_COMPLIANT,
            is_compliant=True,
            total_rest_24h=total_24h,
            total_rest_7d=total_7d,
            longest_continuous_rest=longest_p,
            period_count_24h=p_count,
            compensation_rest_due_hours=0.0,
            audit_remarks="All STCW 2010 Manila & MLC 2006 Standard A2.3 rest requirements verified compliant.",
        )


# ============================================================================
# Phase 289: Seaport Wharfage & Berth Occupancy Tariffs Engine
# ============================================================================

class PortWharfArea(str, Enum):
    AREA_I_NORTH = "AREA_I_NORTH"
    AREA_II_CENTRAL = "AREA_II_CENTRAL"
    AREA_III_SOUTH = "AREA_III_SOUTH"


class BerthType(str, Enum):
    CONTAINER_BERTH = "CONTAINER_BERTH"
    GENERAL_CARGO_BERTH = "GENERAL_CARGO_BERTH"
    BUOY_ANCHORAGE = "BUOY_ANCHORAGE"
    LIQUID_BULK_JETTY = "LIQUID_BULK_JETTY"


class VesselTradeType(str, Enum):
    INTERNATIONAL = "INTERNATIONAL"
    DOMESTIC = "DOMESTIC"


@dataclass
class WharfageCalculationInput:
    gross_tonnage: float
    trade_type: VesselTradeType
    port_area: PortWharfArea
    berth_type: BerthType
    scheduled_hours: float
    actual_hours: float
    is_holiday: bool = False
    vnd_exchange_rate: float = 25000.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gross_tonnage": round(self.gross_tonnage, 1),
            "trade_type": self.trade_type.value,
            "port_area": self.port_area.value,
            "berth_type": self.berth_type.value,
            "scheduled_hours": round(self.scheduled_hours, 1),
            "actual_hours": round(self.actual_hours, 1),
            "is_holiday": self.is_holiday,
            "vnd_exchange_rate": round(self.vnd_exchange_rate, 2),
        }


@dataclass
class WharfageCalculationResult:
    base_rate_per_gt_hour: float
    base_berthage_fee_usd: float
    base_berthage_fee_vnd: float
    overstay_hours: float
    overstay_surcharge_usd: float
    holiday_surcharge_usd: float
    total_wharfage_fee_usd: float
    total_wharfage_fee_vnd: float
    invoice_description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_rate_per_gt_hour": round(self.base_rate_per_gt_hour, 6),
            "base_berthage_fee_usd": round(self.base_berthage_fee_usd, 2),
            "base_berthage_fee_vnd": round(self.base_berthage_fee_vnd, 0),
            "overstay_hours": round(self.overstay_hours, 1),
            "overstay_surcharge_usd": round(self.overstay_surcharge_usd, 2),
            "holiday_surcharge_usd": round(self.holiday_surcharge_usd, 2),
            "total_wharfage_fee_usd": round(self.total_wharfage_fee_usd, 2),
            "total_wharfage_fee_vnd": round(self.total_wharfage_fee_vnd, 0),
            "invoice_description": self.invoice_description,
        }


class PortWharfageEngine:
    """Calculates Seaport Wharfage & Berth Occupancy under Circular 39/2023/TT-BGTVT."""

    # Base rates in USD per GT per hour for International trade
    INTERNATIONAL_RATES: Dict[BerthType, float] = {
        BerthType.CONTAINER_BERTH: 0.0035,
        BerthType.GENERAL_CARGO_BERTH: 0.0031,
        BerthType.BUOY_ANCHORAGE: 0.00175,
        BerthType.LIQUID_BULK_JETTY: 0.0042,
    }

    # Base rates in VND per GT per hour for Domestic trade
    DOMESTIC_RATES_VND: Dict[BerthType, float] = {
        BerthType.CONTAINER_BERTH: 28.0,
        BerthType.GENERAL_CARGO_BERTH: 22.0,
        BerthType.BUOY_ANCHORAGE: 12.0,
        BerthType.LIQUID_BULK_JETTY: 35.0,
    }

    @classmethod
    def calculate(cls, sample: WharfageCalculationInput) -> WharfageCalculationResult:
        gt = sample.gross_tonnage
        actual_h = max(0.5, sample.actual_hours)
        scheduled_h = sample.scheduled_hours
        fx = sample.vnd_exchange_rate

        if sample.trade_type == VesselTradeType.INTERNATIONAL:
            base_unit_rate = cls.INTERNATIONAL_RATES.get(sample.berth_type, 0.0035)
            # Area adjustment
            if sample.port_area == PortWharfArea.AREA_I_NORTH:
                base_unit_rate *= 0.95
            elif sample.port_area == PortWharfArea.AREA_II_CENTRAL:
                base_unit_rate *= 0.90
            base_fee_usd = gt * actual_h * base_unit_rate
            base_fee_vnd = base_fee_usd * fx
        else:
            base_unit_rate_vnd = cls.DOMESTIC_RATES_VND.get(sample.berth_type, 25.0)
            if sample.port_area == PortWharfArea.AREA_I_NORTH:
                base_unit_rate_vnd *= 0.95
            elif sample.port_area == PortWharfArea.AREA_II_CENTRAL:
                base_unit_rate_vnd *= 0.90
            base_fee_vnd = gt * actual_h * base_unit_rate_vnd
            base_fee_usd = base_fee_vnd / fx
            base_unit_rate = base_unit_rate_vnd / fx

        # Overstay calculation: overstay hours charged with +50% penalty
        overstay_h = max(0.0, actual_h - scheduled_h)
        overstay_surcharge_usd = 0.0
        if overstay_h > 0.0:
            overstay_surcharge_usd = (gt * overstay_h * base_unit_rate) * 0.50

        # Holiday surcharge: +30% on base fee
        holiday_surcharge_usd = 0.0
        if sample.is_holiday:
            holiday_surcharge_usd = base_fee_usd * 0.30

        total_usd = base_fee_usd + overstay_surcharge_usd + holiday_surcharge_usd
        total_vnd = total_usd * fx

        desc = (
            f"Wharfage fee for {gt:.0f} GT, berth={sample.berth_type.value}, duration={actual_h:.1f}h "
            f"(overstay={overstay_h:.1f}h). Circular 39/2023/TT-BGTVT."
        )

        return WharfageCalculationResult(
            base_rate_per_gt_hour=base_unit_rate,
            base_berthage_fee_usd=base_fee_usd,
            base_berthage_fee_vnd=base_fee_vnd,
            overstay_hours=overstay_h,
            overstay_surcharge_usd=overstay_surcharge_usd,
            holiday_surcharge_usd=holiday_surcharge_usd,
            total_wharfage_fee_usd=total_usd,
            total_wharfage_fee_vnd=total_vnd,
            invoice_description=desc,
        )


# ============================================================================
# Phase 290: Customs CFS Deconsolidation & E-Seal Tracking Engine
# ============================================================================

class CfsCustomsStatus(str, Enum):
    COMPLIANT_ACTIVE = "COMPLIANT_ACTIVE"
    WARNING_EXPIRING_SOON = "WARNING_EXPIRING_SOON"
    OVERDUE_ABANDONED_SUSPECT = "OVERDUE_ABANDONED_SUSPECT"
    TAMPER_ALERT_CABLE_CUT = "TAMPER_ALERT_CABLE_CUT"
    ROUTE_DEVIATION_ALERT = "ROUTE_DEVIATION_ALERT"
    GPS_SIGNAL_LOST = "GPS_SIGNAL_LOST"


class CfsCargoOperation(str, Enum):
    LCL_DECONSOLIDATION = "LCL_DECONSOLIDATION"
    LCL_CONSOLIDATION = "LCL_CONSOLIDATION"
    STORAGE_ONLY = "STORAGE_ONLY"


@dataclass
class CfsEsealSupervisionInput:
    container_no: str
    eseal_id: str
    operation: CfsCargoOperation
    storage_days: int
    is_extension_approved: bool = False
    is_cable_intact: bool = True
    is_tamper_detected: bool = False
    route_deviation_meters: float = 0.0
    gps_lost_minutes: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_no": self.container_no,
            "eseal_id": self.eseal_id,
            "operation": self.operation.value,
            "storage_days": self.storage_days,
            "is_extension_approved": self.is_extension_approved,
            "is_cable_intact": self.is_cable_intact,
            "is_tamper_detected": self.is_tamper_detected,
            "route_deviation_meters": round(self.route_deviation_meters, 1),
            "gps_lost_minutes": round(self.gps_lost_minutes, 1),
        }


@dataclass
class CfsEsealSupervisionResult:
    customs_status: CfsCustomsStatus
    is_cleared_for_release: bool
    remaining_storage_days: int
    max_permitted_storage_days: int
    supervision_token: str
    status_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customs_status": self.customs_status.value,
            "is_cleared_for_release": self.is_cleared_for_release,
            "remaining_storage_days": self.remaining_storage_days,
            "max_permitted_storage_days": self.max_permitted_storage_days,
            "supervision_token": self.supervision_token,
            "status_summary": self.status_summary,
        }


class CfsEsealEngine:
    """Supervises CFS LCL bonded operations & Customs RFID/GPS E-Seal integrity."""

    MAX_INITIAL_STORAGE_DAYS: int = 90
    MAX_EXTENSION_DAYS: int = 90
    MAX_PERMITTED_ROUTE_DEVIATION_METERS: float = 500.0
    MAX_GPS_SIGNAL_LOST_MINUTES: float = 30.0

    @classmethod
    def evaluate(cls, sample: CfsEsealSupervisionInput) -> CfsEsealSupervisionResult:
        max_days = cls.MAX_INITIAL_STORAGE_DAYS
        if sample.is_extension_approved:
            max_days += cls.MAX_EXTENSION_DAYS

        remaining_days = max(0, max_days - sample.storage_days)

        token_raw = (
            f"{sample.container_no}-{sample.eseal_id}-{sample.storage_days}-"
            f"{sample.is_cable_intact}-{sample.is_tamper_detected}"
        )
        supervision_token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        # E-Seal integrity checks
        if not sample.is_cable_intact or sample.is_tamper_detected:
            return CfsEsealSupervisionResult(
                customs_status=CfsCustomsStatus.TAMPER_ALERT_CABLE_CUT,
                is_cleared_for_release=False,
                remaining_storage_days=remaining_days,
                max_permitted_storage_days=max_days,
                supervision_token=supervision_token,
                status_summary="CRITICAL: E-Seal wire severed or unauthorized opening detected. Immediate physical customs inspection triggered.",
            )

        if sample.route_deviation_meters > cls.MAX_PERMITTED_ROUTE_DEVIATION_METERS:
            return CfsEsealSupervisionResult(
                customs_status=CfsCustomsStatus.ROUTE_DEVIATION_ALERT,
                is_cleared_for_release=False,
                remaining_storage_days=remaining_days,
                max_permitted_storage_days=max_days,
                supervision_token=supervision_token,
                status_summary=f"WARNING: Vehicle route deviation {sample.route_deviation_meters} m > 500 m limit from designated customs corridor.",
            )

        if sample.gps_lost_minutes > cls.MAX_GPS_SIGNAL_LOST_MINUTES:
            return CfsEsealSupervisionResult(
                customs_status=CfsCustomsStatus.GPS_SIGNAL_LOST,
                is_cleared_for_release=False,
                remaining_storage_days=remaining_days,
                max_permitted_storage_days=max_days,
                supervision_token=supervision_token,
                status_summary=f"WARNING: GPS telemetry lost for {sample.gps_lost_minutes} mins > 30 mins tolerance window.",
            )

        # CFS Storage time-bar checks
        if sample.storage_days > max_days:
            return CfsEsealSupervisionResult(
                customs_status=CfsCustomsStatus.OVERDUE_ABANDONED_SUSPECT,
                is_cleared_for_release=False,
                remaining_storage_days=0,
                max_permitted_storage_days=max_days,
                supervision_token=supervision_token,
                status_summary=f"ALERT: CFS dwell time {sample.storage_days} days exceeds statutory cap {max_days} days. Flagged for abandoned cargo auction.",
            )

        if remaining_days <= 15:
            return CfsEsealSupervisionResult(
                customs_status=CfsCustomsStatus.WARNING_EXPIRING_SOON,
                is_cleared_for_release=True,
                remaining_storage_days=remaining_days,
                max_permitted_storage_days=max_days,
                supervision_token=supervision_token,
                status_summary=f"CAUTION: CFS storage expiring in {remaining_days} days. Expedite customs clearance or file extension request.",
            )

        return CfsEsealSupervisionResult(
            customs_status=CfsCustomsStatus.COMPLIANT_ACTIVE,
            is_cleared_for_release=True,
            remaining_storage_days=remaining_days,
            max_permitted_storage_days=max_days,
            supervision_token=supervision_token,
            status_summary="CFS dwell time and E-Seal telemetry fully compliant under Customs Law 2014 & Decree 08/2015/ND-CP.",
        )
