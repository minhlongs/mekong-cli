"""Central Facade for Maritime Phases 379-382.

Unifies:
- Phase 379: Marine Starting Air & Air Reservoir Compressor Automation Engine
- Phase 380: Seachest & Main Seawater Cooling Ingress Protection Engine
- Phase 381: Automatic Draft & Tank Sounding Gauging Radar/Bubbler Engine
- Phase 382: Port Pilotage Navigational Safety & ARPA Collision Avoidance Engine
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_379_marine_starting_air_compressor import (
    EngineReversibility,
    MarineStartingAirCompressorEngine,
    StartingAirInput,
    StartingAirReport,
)
from src.core.maritime.phase_380_seachest_cooling_ingress import (
    SeachestCoolingIngressEngine,
    SeachestCoolingInput,
    SeachestCoolingReport,
    SeachestSuctionType,
)
from src.core.maritime.phase_381_draft_tank_sounding_gauging import (
    DraftTankGaugingInput,
    DraftTankGaugingReport,
    DraftTankSoundingGaugingEngine,
)
from src.core.maritime.phase_382_port_pilotage_arpa_collision import (
    PilotageArpaInput,
    PilotageArpaReport,
    PortPilotageArpaCollisionEngine,
    TargetAssessment,
    TargetTrack,
)

__all__ = [
    "EngineReversibility",
    "StartingAirInput",
    "StartingAirReport",
    "MarineStartingAirCompressorEngine",
    "SeachestSuctionType",
    "SeachestCoolingInput",
    "SeachestCoolingReport",
    "SeachestCoolingIngressEngine",
    "DraftTankGaugingInput",
    "DraftTankGaugingReport",
    "DraftTankSoundingGaugingEngine",
    "TargetTrack",
    "PilotageArpaInput",
    "TargetAssessment",
    "PilotageArpaReport",
    "PortPilotageArpaCollisionEngine",
    "MaritimeMultiDomain379To382Report",
    "MaritimeAirSeachestDraftPilotEngine",
]


@dataclass
class MaritimeMultiDomain379To382Report:
    overall_status: str
    starting_air_report: StartingAirReport
    seachest_report: SeachestCoolingReport
    draft_sounding_report: DraftTankGaugingReport
    pilotage_arpa_report: PilotageArpaReport
    critical_alerts: List[str] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class MaritimeAirSeachestDraftPilotEngine:
    """Unified Facade for Maritime Phases 379-382."""

    @classmethod
    def evaluate_starting_air(
        cls, inp: StartingAirInput
    ) -> StartingAirReport:
        return MarineStartingAirCompressorEngine().evaluate(inp)

    @classmethod
    def evaluate_seachest(
        cls, inp: SeachestCoolingInput
    ) -> SeachestCoolingReport:
        return SeachestCoolingIngressEngine().evaluate(inp)

    @classmethod
    def evaluate_draft_sounding(
        cls, inp: DraftTankGaugingInput
    ) -> DraftTankGaugingReport:
        return DraftTankSoundingGaugingEngine().evaluate(inp)

    @classmethod
    def evaluate_pilotage_arpa(
        cls, inp: PilotageArpaInput
    ) -> PilotageArpaReport:
        return PortPilotageArpaCollisionEngine().evaluate(inp)

    @classmethod
    def run_all(
        cls,
        air_inp: StartingAirInput,
        seachest_inp: SeachestCoolingInput,
        draft_inp: DraftTankGaugingInput,
        pilot_inp: PilotageArpaInput,
    ) -> MaritimeMultiDomain379To382Report:
        air_res = cls.evaluate_starting_air(air_inp)
        seachest_res = cls.evaluate_seachest(seachest_inp)
        draft_res = cls.evaluate_draft_sounding(draft_inp)
        pilot_res = cls.evaluate_pilotage_arpa(pilot_inp)

        alerts: List[str] = []
        alerts.extend(air_res.warnings)
        alerts.extend(seachest_res.warnings)
        alerts.extend(draft_res.warnings)
        alerts.extend(pilot_res.warnings)

        is_critical = (
            air_res.system_status == "CRITICAL_ALARM"
            or seachest_res.system_status == "CRITICAL_CLOGGED"
            or draft_res.system_status == "CRITICAL_ALARM"
            or pilot_res.system_status == "CRITICAL_COLLISION_ALARM"
        )

        overall_status = "CRITICAL_ACTION_REQUIRED" if is_critical else "OPTIMAL_OPERATIONAL"

        summary = {
            "air_available_starts": air_res.available_starts,
            "air_pressure_bar": air_res.current_pressure_bar,
            "seachest_diff_p_bar": seachest_res.differential_pressure_bar,
            "seachest_mgps_target_a": seachest_res.target_mgps_current_a,
            "draft_quarter_mean_m": draft_res.quarter_mean_draft_m,
            "draft_trim_m": draft_res.trim_m,
            "tank_filling_pct": draft_res.tank_filling_pct,
            "pilot_min_cpa_nm": pilot_res.min_cpa_nm,
            "pilot_critical_target": pilot_res.critical_cpa_target_id,
        }

        return MaritimeMultiDomain379To382Report(
            overall_status=overall_status,
            starting_air_report=air_res,
            seachest_report=seachest_res,
            draft_sounding_report=draft_res,
            pilotage_arpa_report=pilot_res,
            critical_alerts=alerts,
            summary_metrics=summary,
        )
