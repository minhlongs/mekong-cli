"""Inland Waterway Navigation, Container Feeder Barging, Maritime SAR & ISPS Security Engines.

Phases 187-190:
- Phase 187: Vietnam Inland Waterway Navigation & Bridge Clearance (Luật ĐTNĐ 2004/2014 & TT 46/2016/TT-BGTVT)
- Phase 188: Container Feeder Barging & Mekong Transit Freight (TT 39/2023/TT-BGTVT & TT 248/2016/TT-BTC)
- Phase 189: Maritime Search & Rescue (SAR) & Wreck Removal (NĐ 05/2017/NĐ-CP & IAMSAR Manual)
- Phase 190: Port Facility & Ship Security (ISPS Code & NĐ 159/2018/NĐ-CP)

100% Python standard library implementation with zero external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WaterwayClass(str, Enum):
    """Inland Waterway Classification under Circular 46/2016/TT-BGTVT."""
    SPECIAL = "SPECIAL"  # Cấp Đặc biệt (Depth >= 4.0m, Bridge Air Draft >= 11.0m)
    CLASS_I = "CLASS_I"  # Cấp I (Depth >= 3.0m, Bridge Air Draft >= 9.0m)
    CLASS_II = "CLASS_II"  # Cấp II (Depth >= 2.5m, Bridge Air Draft >= 7.0m)
    CLASS_III = "CLASS_III"  # Cấp III (Depth >= 2.0m, Bridge Air Draft >= 6.0m)
    CLASS_IV = "CLASS_IV"  # Cấp IV (Depth >= 1.5m, Bridge Air Draft >= 5.0m)
    CLASS_V = "CLASS_V"  # Cấp V (Depth >= 1.2m, Bridge Air Draft >= 4.0m)
    CLASS_VI = "CLASS_VI"  # Cấp VI (Depth >= 1.0m, Bridge Air Draft >= 3.5m)


class FeederBargeRoute(str, Enum):
    """Feeder container barging routes in Vietnam."""
    HCM_CAI_MEP = "HCM_CAI_MEP"  # TP.HCM - Cái Mép (approx 45 NM)
    MEKONG_DELTA_CAI_MEP = "MEKONG_DELTA_CAI_MEP"  # Cần Thơ / Mỹ Thới - Cái Mép (approx 120 NM)
    HCM_PHNOM_PENH = "HCM_PHNOM_PENH"  # Cross-border Mekong Transit (approx 190 NM)
    HAI_PHONG_BAC_NINH = "HAI_PHONG_BAC_NINH"  # Hải Phòng - Bắc Ninh ICD (approx 65 NM)


class SARRegion(str, Enum):
    """Vietnam Maritime Search and Rescue Coordination Center (VMRCC) Regions."""
    REGION_I = "REGION_I"  # Hải Phòng (Northern Gulf of Tonkin)
    REGION_II = "REGION_II"  # Đà Nẵng (Central Coast & Paracel)
    REGION_III = "REGION_III"  # Vũng Tàu (Southern East Sea & Mekong Estuary)
    REGION_IV = "REGION_IV"  # Nha Trang (South-Central & Spratly)


class ISPSLevel(str, Enum):
    """ISPS Code Security Levels (SOLAS Ch. XI-2)."""
    LEVEL_1 = "LEVEL_1"  # Normal / Standard operating security measures
    LEVEL_2 = "LEVEL_2"  # Medium / Heightened risk of security incident
    LEVEL_3 = "LEVEL_3"  # High / Exceptional risk or imminent security incident


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class WaterwayClearanceAssessment:
    """Clearance assessment for inland waterway navigation."""
    vessel_name: str
    waterway_class: WaterwayClass
    bridge_name: str
    bridge_air_draft_m: float
    vessel_air_draft_m: float
    net_air_clearance_m: float
    is_air_draft_safe: bool
    channel_depth_m: float
    vessel_draft_m: float
    under_keel_clearance_m: float
    is_ukc_safe: bool
    can_transit: bool
    restriction_notes: List[str] = field(default_factory=list)


@dataclass
class FeederBargingFreightResult:
    """Feeder container barging freight and port charges."""
    route: FeederBargeRoute
    teu_count: int
    feu_count: int
    dg_containers_count: int
    base_freight_vnd: float
    dg_surcharge_vnd: float
    waterway_port_dues_vnd: float
    cross_border_mekong_fee_vnd: float
    total_barging_cost_vnd: float
    total_barging_cost_usd: float
    transit_hours_estimated: float
    details: Dict[str, float] = field(default_factory=dict)


@dataclass
class SARSearchDatumBox:
    """Maritime Search and Rescue Datum and Search Box Result."""
    incident_id: str
    sar_region: SARRegion
    initial_lat: float
    initial_lon: float
    drift_hours: float
    water_current_speed_knots: float
    water_current_direction_deg: float
    wind_speed_knots: float
    wind_direction_deg: float
    datum_lat: float
    datum_lon: float
    search_radius_nm: float
    search_box_area_sq_nm: float
    primary_sar_base: str
    recommended_air_surface_units: List[str] = field(default_factory=list)


@dataclass
class WreckRemovalAssessment:
    """Wreck removal statutory deadline and maritime lien evaluation."""
    vessel_name: str
    sinking_date_iso: str
    assessment_date_iso: str
    days_elapsed: int
    statutory_plan_deadline_days: int
    days_remaining_for_plan: int
    is_deadline_breached: bool
    port_authority_forced_removal: bool
    maritime_lien_enforceable: bool
    action_order: str


@dataclass
class ISPSComplianceEvaluation:
    """ISPS Code Port Facility and Ship Security Compliance."""
    facility_name: str
    port_isps_level: ISPSLevel
    vessel_name: str
    ship_isps_level: ISPSLevel
    effective_operational_level: ISPSLevel
    is_declaration_of_security_required: bool
    mandatory_security_measures: List[str] = field(default_factory=list)
    access_control_rule: str = ""
    cargo_handling_supervision: str = ""


# ---------------------------------------------------------------------------
# Domain Engines (Pure Python Standard Library)
# ---------------------------------------------------------------------------


class InlandWaterwayNavEngine:
    """Engine for Vietnam Inland Waterway Navigation & Bridge Clearance (Phase 187)."""

    MIN_AIR_CLEARANCE_MARGIN_M = 0.50  # 50cm mandatory buffer under bridges
    MIN_UKC_MARGIN_M = 0.30  # 30cm mandatory Under Keel Clearance

    @classmethod
    def evaluate_clearance(
        cls,
        vessel_name: str,
        waterway_class: WaterwayClass,
        bridge_name: str,
        bridge_air_draft_m: float,
        vessel_air_draft_m: float,
        channel_depth_m: float,
        vessel_draft_m: float,
    ) -> WaterwayClearanceAssessment:
        """Evaluate air draft and channel depth clearance for safe transit."""
        net_air_clearance = round(bridge_air_draft_m - vessel_air_draft_m, 2)
        is_air_safe = net_air_clearance >= cls.MIN_AIR_CLEARANCE_MARGIN_M

        ukc = round(channel_depth_m - vessel_draft_m, 2)
        is_ukc_safe = ukc >= cls.MIN_UKC_MARGIN_M

        can_transit = is_air_safe and is_ukc_safe
        notes: List[str] = []

        if not is_air_safe:
            notes.append(
                f"Air clearance {net_air_clearance}m is below safety margin ({cls.MIN_AIR_CLEARANCE_MARGIN_M}m) for bridge '{bridge_name}'."
            )
        if not is_ukc_safe:
            notes.append(
                f"Under Keel Clearance {ukc}m is below minimum required UKC ({cls.MIN_UKC_MARGIN_M}m) in {waterway_class.value} channel."
            )
        if can_transit:
            notes.append("Clearance verified safe for inland waterway passage under Circular 46/2016/TT-BGTVT.")

        return WaterwayClearanceAssessment(
            vessel_name=vessel_name,
            waterway_class=waterway_class,
            bridge_name=bridge_name,
            bridge_air_draft_m=bridge_air_draft_m,
            vessel_air_draft_m=vessel_air_draft_m,
            net_air_clearance_m=net_air_clearance,
            is_air_draft_safe=is_air_safe,
            channel_depth_m=channel_depth_m,
            vessel_draft_m=vessel_draft_m,
            under_keel_clearance_m=ukc,
            is_ukc_safe=is_ukc_safe,
            can_transit=can_transit,
            restriction_notes=notes,
        )


class FeederBargingFreightEngine:
    """Engine for Container Feeder Barging & Mekong Transit Freight (Phase 188)."""

    # Baseline Freight Rates (VND / container)
    ROUTE_RATES = {
        FeederBargeRoute.HCM_CAI_MEP: {"TEU": 1_800_000.0, "FEU": 3_200_000.0, "hours": 4.5},
        FeederBargeRoute.MEKONG_DELTA_CAI_MEP: {"TEU": 3_500_000.0, "FEU": 6_200_000.0, "hours": 14.0},
        FeederBargeRoute.HCM_PHNOM_PENH: {"TEU": 8_500_000.0, "FEU": 15_000_000.0, "hours": 32.0},
        FeederBargeRoute.HAI_PHONG_BAC_NINH: {"TEU": 2_200_000.0, "FEU": 3_900_000.0, "hours": 7.0},
    }

    DG_SURCHARGE_PERCENT = 10.0  # +10% surcharge for Dangerous Goods (DG) containers
    VND_USD_RATE = 25_000.0  # Reference exchange rate

    @classmethod
    def calculate_freight(
        cls,
        route: FeederBargeRoute,
        teu_count: int,
        feu_count: int = 0,
        dg_containers_count: int = 0,
        barge_dwt_tonnage: float = 2000.0,
    ) -> FeederBargingFreightResult:
        """Calculate feeder barging freight, DG surcharges, and TT 248 port dues."""
        rate_info = cls.ROUTE_RATES[route]
        base_freight = (teu_count * rate_info["TEU"]) + (feu_count * rate_info["FEU"])

        # DG surcharge applied per dangerous goods box
        total_boxes = teu_count + feu_count
        avg_rate_per_box = base_freight / total_boxes if total_boxes > 0 else 0.0
        dg_surcharge = dg_containers_count * avg_rate_per_box * (cls.DG_SURCHARGE_PERCENT / 100.0)

        # TT 248/2016/TT-BTC Waterway port dues: 150 VND/DWT + 50,000 VND clearance fee
        waterway_port_dues = (barge_dwt_tonnage * 150.0) + 50_000.0

        # Cross-border treaty surcharge for Vietnam-Cambodia route
        cross_border_fee = 2_500_000.0 if route == FeederBargeRoute.HCM_PHNOM_PENH else 0.0

        total_cost_vnd = base_freight + dg_surcharge + waterway_port_dues + cross_border_fee
        total_cost_usd = round(total_cost_vnd / cls.VND_USD_RATE, 2)

        return FeederBargingFreightResult(
            route=route,
            teu_count=teu_count,
            feu_count=feu_count,
            dg_containers_count=dg_containers_count,
            base_freight_vnd=round(base_freight, 2),
            dg_surcharge_vnd=round(dg_surcharge, 2),
            waterway_port_dues_vnd=round(waterway_port_dues, 2),
            cross_border_mekong_fee_vnd=round(cross_border_fee, 2),
            total_barging_cost_vnd=round(total_cost_vnd, 2),
            total_barging_cost_usd=total_cost_usd,
            transit_hours_estimated=rate_info["hours"],
            details={
                "base_freight_vnd": round(base_freight, 2),
                "dg_surcharge_vnd": round(dg_surcharge, 2),
                "port_dues_vnd": round(waterway_port_dues, 2),
                "cross_border_vnd": round(cross_border_fee, 2),
            },
        )


class MaritimeSARWreckEngine:
    """Engine for Maritime Search & Rescue (SAR) & Wreck Removal (Phase 189)."""

    SAR_BASES = {
        SARRegion.REGION_I: "Hai Phong SAR Base (SAR 411 / SAR 273)",
        SARRegion.REGION_II: "Da Nang SAR Base (SAR 412 / SAR 274)",
        SARRegion.REGION_III: "Vung Tau SAR Base (SAR 413 / SAR 272)",
        SARRegion.REGION_IV: "Nha Trang SAR Base (SAR 27-01)",
    }

    STATUTORY_WRECK_PLAN_DAYS = 30  # 30-day statutory limit under Decree 05/2017/NĐ-CP

    @classmethod
    def calculate_sar_datum(
        cls,
        incident_id: str,
        sar_region: SARRegion,
        initial_lat: float,
        initial_lon: float,
        drift_hours: float,
        water_current_speed_knots: float,
        water_current_direction_deg: float,
        wind_speed_knots: float,
        wind_direction_deg: float,
    ) -> SARSearchDatumBox:
        """Calculate IAMSAR search datum position and rectangular search box."""
        # Total Water Current Drift Vector
        current_distance_nm = water_current_speed_knots * drift_hours
        rad_current = math.radians(water_current_direction_deg)
        dx_current = current_distance_nm * math.sin(rad_current)
        dy_current = current_distance_nm * math.cos(rad_current)

        # Leeway Wind Drift Vector (approx 3% wind speed, downwind: direction + 180 deg)
        leeway_speed_knots = wind_speed_knots * 0.03
        leeway_distance_nm = leeway_speed_knots * drift_hours
        rad_wind_leeway = math.radians((wind_direction_deg + 180.0) % 360.0)
        dx_wind = leeway_distance_nm * math.sin(rad_wind_leeway)
        dy_wind = leeway_distance_nm * math.cos(rad_wind_leeway)

        # Combined displacement in NM
        total_dx_nm = dx_current + dx_wind
        total_dy_nm = dy_current + dy_wind

        # Coordinate shift (1 deg lat approx 60 NM; 1 deg lon approx 60 * cos(lat) NM)
        d_lat = total_dy_nm / 60.0
        avg_lat = initial_lat + (d_lat / 2.0)
        cos_factor = math.cos(math.radians(avg_lat)) if math.cos(math.radians(avg_lat)) > 0.01 else 1.0
        d_lon = total_dx_nm / (60.0 * cos_factor)

        datum_lat = round(initial_lat + d_lat, 4)
        datum_lon = round(initial_lon + d_lon, 4)

        # Search radius based on navigational error (5 NM) and drift uncertainty
        drift_uncertainty_nm = (total_dx_nm**2 + total_dy_nm**2)**0.5 * 0.25
        search_radius_nm = round(max(5.0, 5.0 + drift_uncertainty_nm), 2)
        search_box_area = round((2 * search_radius_nm) ** 2, 2)

        units = [
            cls.SAR_BASES[sar_region],
            "Maritime Patrol Aircraft (VHC-SAR)",
            "Coast Guard Cutter / Rescue Tug",
        ]

        return SARSearchDatumBox(
            incident_id=incident_id,
            sar_region=sar_region,
            initial_lat=initial_lat,
            initial_lon=initial_lon,
            drift_hours=drift_hours,
            water_current_speed_knots=water_current_speed_knots,
            water_current_direction_deg=water_current_direction_deg,
            wind_speed_knots=wind_speed_knots,
            wind_direction_deg=wind_direction_deg,
            datum_lat=datum_lat,
            datum_lon=datum_lon,
            search_radius_nm=search_radius_nm,
            search_box_area_sq_nm=search_box_area,
            primary_sar_base=cls.SAR_BASES[sar_region],
            recommended_air_surface_units=units,
        )

    @classmethod
    def assess_wreck_removal(
        cls,
        vessel_name: str,
        sinking_date_iso: str,
        assessment_date_iso: Optional[str] = None,
    ) -> WreckRemovalAssessment:
        """Assess 30-day wreck removal plan deadline under Decree 05/2017/NĐ-CP."""
        d_sinking = datetime.strptime(sinking_date_iso, "%Y-%m-%d")
        d_assessment = (
            datetime.strptime(assessment_date_iso, "%Y-%m-%d")
            if assessment_date_iso
            else datetime.utcnow()
        )

        days_elapsed = (d_assessment - d_sinking).days
        days_remaining = max(0, cls.STATUTORY_WRECK_PLAN_DAYS - days_elapsed)
        is_breached = days_elapsed > cls.STATUTORY_WRECK_PLAN_DAYS

        if is_breached:
            action = "PORT_AUTHORITY_MANDATORY_FORCED_REMOVAL"
            forced = True
            lien = True
        else:
            action = "SHIPOWNER_SUBMIT_SALVAGE_PLAN"
            forced = False
            lien = False

        return WreckRemovalAssessment(
            vessel_name=vessel_name,
            sinking_date_iso=sinking_date_iso,
            assessment_date_iso=d_assessment.strftime("%Y-%m-%d"),
            days_elapsed=days_elapsed,
            statutory_plan_deadline_days=cls.STATUTORY_WRECK_PLAN_DAYS,
            days_remaining_for_plan=days_remaining,
            is_deadline_breached=is_breached,
            port_authority_forced_removal=forced,
            maritime_lien_enforceable=lien,
            action_order=action,
        )


class PortFacilitySecurityISPSEngine:
    """Engine for Port Facility & Ship Security (ISPS Code) (Phase 190)."""

    LEVEL_ORDER = {
        ISPSLevel.LEVEL_1: 1,
        ISPSLevel.LEVEL_2: 2,
        ISPSLevel.LEVEL_3: 3,
    }

    @classmethod
    def evaluate_security_compliance(
        cls,
        facility_name: str,
        port_isps_level: ISPSLevel,
        vessel_name: str,
        ship_isps_level: ISPSLevel,
    ) -> ISPSComplianceEvaluation:
        """Evaluate operational security level and Declaration of Security (DoS) requirements."""
        # Operational security level is max(Port, Ship)
        port_num = cls.LEVEL_ORDER[port_isps_level]
        ship_num = cls.LEVEL_ORDER[ship_isps_level]

        effective_num = max(port_num, ship_num)
        effective_level = [k for k, v in cls.LEVEL_ORDER.items() if v == effective_num][0]

        # DoS is mandatory whenever ship and port security levels differ, or either is Level 3
        is_dos_required = (port_isps_level != ship_isps_level) or (effective_level == ISPSLevel.LEVEL_3)

        measures: List[str] = []
        if effective_level == ISPSLevel.LEVEL_1:
            access_rule = "Standard ID check at gate; 20% random vehicle inspection."
            cargo_rule = "Periodic cargo seal verification and routine perimeter patrol."
            measures.append("Level 1 baseline surveillance active.")
        elif effective_level == ISPSLevel.LEVEL_2:
            access_rule = "100% photo ID inspection, vehicle search, and restricted visitor passes."
            cargo_rule = "100% container seal matching, continuous lighting, water-side boat patrol."
            measures.append("Heightened security state: Double patrol frequency.")
            measures.append("Water-side security escort required for berthing.")
        else:  # LEVEL_3
            access_rule = "Total perimeter lockdown. No unauthorized personnel or vehicles permitted."
            cargo_rule = "All cargo loading/unloading operations SUSPENDED immediately."
            measures.append("Exceptional security crisis: Transfer tactical control to National Security / Coast Guard.")
            measures.append("Evacuation readiness protocols activated.")

        return ISPSComplianceEvaluation(
            facility_name=facility_name,
            port_isps_level=port_isps_level,
            vessel_name=vessel_name,
            ship_isps_level=ship_isps_level,
            effective_operational_level=effective_level,
            is_declaration_of_security_required=is_dos_required,
            mandatory_security_measures=measures,
            access_control_rule=access_rule,
            cargo_handling_supervision=cargo_rule,
        )
