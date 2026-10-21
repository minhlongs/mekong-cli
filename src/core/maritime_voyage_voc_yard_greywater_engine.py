"""Central Facade for Maritime Phases 375-378.

Unifies:
- Phase 375: Voyage Weather Routing & Operational CII Engine
- Phase 376: Oil Tanker VOC Emission Recovery & Vapor Balancing Engine
- Phase 377: Port Container Yard Stacking & RTG Crane Dispatch Engine
- Phase 378: Shipboard HVAC Condensate & Greywater Circular Reclamation Engine
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_375_voyage_weather_routing_cii import (
    CiiRating,
    VoyageRoutingInput,
    VoyageWeatherCiiReport,
    VoyageWeatherRoutingCiiEngine,
)
from src.core.maritime.phase_376_voc_vapor_recovery_balancing import (
    VocRecoveryInput,
    VocRecoveryReport,
    VocVaporRecoveryBalancingEngine,
)
from src.core.maritime.phase_377_container_yard_rtg_dispatch import (
    ContainerItem,
    ContainerYardRtgDispatchEngine,
    YardBlockInput,
    YardStackRtgReport,
)
from src.core.maritime.phase_378_hvac_condensate_greywater_reuse import (
    HvacCondensateGreywaterEngine,
    WaterReclamationInput,
    WaterReclamationReport,
)

__all__ = [
    "CiiRating",
    "VoyageRoutingInput",
    "VoyageWeatherCiiReport",
    "VoyageWeatherRoutingCiiEngine",
    "VocRecoveryInput",
    "VocRecoveryReport",
    "VocVaporRecoveryBalancingEngine",
    "ContainerItem",
    "YardBlockInput",
    "YardStackRtgReport",
    "ContainerYardRtgDispatchEngine",
    "WaterReclamationInput",
    "WaterReclamationReport",
    "HvacCondensateGreywaterEngine",
    "MaritimeMultiDomain375To378Report",
    "MaritimeVoyageVocYardGreywaterEngine",
]


@dataclass
class MaritimeMultiDomain375To378Report:
    """Aggregated assessment report across maritime phases 375 to 378."""

    overall_status: str
    weather_cii_report: VoyageWeatherCiiReport
    voc_recovery_report: VocRecoveryReport
    yard_rtg_report: YardStackRtgReport
    greywater_report: WaterReclamationReport
    critical_alerts: List[str] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class MaritimeVoyageVocYardGreywaterEngine:
    """Central orchestrator facade for Maritime Phases 375 through 378."""

    def __init__(self) -> None:
        self.weather_engine = VoyageWeatherRoutingCiiEngine()
        self.voc_engine = VocVaporRecoveryBalancingEngine()
        self.yard_engine = ContainerYardRtgDispatchEngine()
        self.greywater_engine = HvacCondensateGreywaterEngine()

    def run_all(
        self,
        weather_inp: VoyageRoutingInput,
        voc_inp: VocRecoveryInput,
        yard_inp: YardBlockInput,
        water_inp: WaterReclamationInput,
    ) -> MaritimeMultiDomain375To378Report:
        weather_rep = self.weather_engine.evaluate(weather_inp)
        voc_rep = self.voc_engine.evaluate(voc_inp)
        yard_rep = self.yard_engine.evaluate(yard_inp)
        water_rep = self.greywater_engine.evaluate(water_inp)

        alerts: List[str] = []
        if weather_rep.seemp_action_required:
            alerts.append(f"CII Critical: Vessel {weather_rep.vessel_id} Rating {weather_rep.cii_rating.value}")
        if not voc_rep.is_safe_to_load:
            alerts.append(f"VOC Safety Trip: Tanker {voc_rep.tanker_id} not safe to load")
        if not yard_rep.imdg_segregation_compliant:
            alerts.append(f"Yard Segregation Hazard: Block {yard_rep.block_id} IMDG separation violated")
        if not yard_rep.is_crane_capacity_sufficient:
            alerts.append(f"Yard Crane Deficit: Block {yard_rep.block_id} RTG/QC ratio below UNCTAD standard")
        if not water_rep.is_qcvn14_compliant:
            alerts.append(f"Water Quality Alert: Vessel {water_rep.vessel_id} greywater non-compliant with QCVN 14")
        if water_rep.is_zero_discharge_enforced:
            alerts.append(f"Environmental Protection: Vessel {water_rep.vessel_id} in MPA zero discharge area")

        total_issues = len(alerts)
        if total_issues == 0:
            overall_status = "OPTIMAL"
        elif total_issues <= 2:
            overall_status = "CAUTION"
        else:
            overall_status = "CRITICAL_ACTION_REQUIRED"

        summary = {
            "overall_status": overall_status,
            "cii_rating": weather_rep.cii_rating.value,
            "optimal_speed_knots": weather_rep.optimal_speed_knots,
            "voc_co2_offset_kg_h": voc_rep.co2_eq_offset_kg_h,
            "is_voc_safe_to_load": voc_rep.is_safe_to_load,
            "yard_total_reshuffles": yard_rep.total_reshuffles_required,
            "yard_cost_to_go": yard_rep.cost_to_go_score,
            "freshwater_saved_m3_day": water_rep.total_freshwater_saved_m3_day,
            "water_cost_savings_usd_day": water_rep.cost_savings_usd_day,
        }

        return MaritimeMultiDomain375To378Report(
            overall_status=overall_status,
            weather_cii_report=weather_rep,
            voc_recovery_report=voc_rep,
            yard_rtg_report=yard_rep,
            greywater_report=water_rep,
            critical_alerts=alerts,
            summary_metrics=summary,
        )
