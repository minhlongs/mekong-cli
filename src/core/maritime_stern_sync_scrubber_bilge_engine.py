"""Master Integration Facade for Maritime Automation Phases 431-434.

Coordinates:
- Phase 431: Stern Tube Lube Gravity Tank, Differential Pressure & Seal Heat.
- Phase 432: Auxiliary Diesel Generator Auto-Sync & Load Sharing.
- Phase 433: EGCS Scrubber Washwater Effluent Quality Monitoring.
- Phase 434: Machinery Space Emergency Bilge Suction Valve Interlock.
Strictly < 120 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List

from src.core.maritime.phase_431_stern_tube_lube_gravity import (
    SternTubeLubeEngine,
    SternTubeLubeTelemetry,
    SternTubeLubeAssessment,
)
from src.core.maritime.phase_432_diesel_gen_sync_loadshare import (
    DieselGenSyncEngine,
    GeneratorSyncTelemetry,
    GeneratorSyncAssessment,
)
from src.core.maritime.phase_433_scrubber_washwater_monitoring import (
    ScrubberWashwaterEngine,
    ScrubberWashwaterTelemetry,
    ScrubberWashwaterAssessment,
)
from src.core.maritime.phase_434_emergency_bilge_suction import (
    EmergencyBilgeSuctionEngine,
    EmergencyBilgeTelemetry,
    EmergencyBilgeAssessment,
)


@dataclass(frozen=True)
class MaritimePhases431to434Telemetry:
    """Consolidated telemetry for Phases 431 through 434."""
    stern_tube: SternTubeLubeTelemetry = SternTubeLubeTelemetry()
    gen_sync: GeneratorSyncTelemetry = GeneratorSyncTelemetry()
    scrubber: ScrubberWashwaterTelemetry = ScrubberWashwaterTelemetry()
    emergency_bilge: EmergencyBilgeTelemetry = EmergencyBilgeTelemetry()


@dataclass(frozen=True)
class MaritimePhases431to434Assessment:
    """Master assessment across machinery safety, power sync, emissions, and flooding."""
    stern_tube: SternTubeLubeAssessment
    gen_sync: GeneratorSyncAssessment
    scrubber: ScrubberWashwaterAssessment
    emergency_bilge: EmergencyBilgeAssessment
    overall_status: str
    action_required: bool
    summary_warnings: List[str]
    compliance_matrix: Dict[str, bool]


class MaritimeSternSyncScrubberBilgeEngine:
    """Facade orchestrating Phases 431-434."""

    def __init__(self) -> None:
        self.stern_engine = SternTubeLubeEngine()
        self.sync_engine = DieselGenSyncEngine()
        self.scrubber_engine = ScrubberWashwaterEngine()
        self.bilge_engine = EmergencyBilgeSuctionEngine()

    def evaluate(self, telemetry: MaritimePhases431to434Telemetry) -> MaritimePhases431to434Assessment:
        stern_res = self.stern_engine.evaluate(telemetry.stern_tube)
        sync_res = self.sync_engine.evaluate(telemetry.gen_sync)
        scrub_res = self.scrubber_engine.evaluate(telemetry.scrubber)
        bilge_res = self.bilge_engine.evaluate(telemetry.emergency_bilge)

        all_warnings = stern_res.warnings + sync_res.warnings + scrub_res.warnings + bilge_res.warnings
        action_required = (
            stern_res.seal_overheat
            or sync_res.reverse_power_trip
            or scrub_res.divert_to_holding_tank
            or bilge_res.bilge_alarm_state == "CRITICAL_FLOODING_TRIP"
        )

        overall_status = "CRITICAL_ACTION_REQUIRED" if action_required else "ALL_SYSTEMS_NOMINAL"

        matrix: Dict[str, bool] = {
            **stern_res.compliance_flags,
            **sync_res.compliance_flags,
            **scrub_res.compliance_flags,
            **bilge_res.compliance_flags,
        }

        return MaritimePhases431to434Assessment(
            stern_tube=stern_res,
            gen_sync=sync_res,
            scrubber=scrub_res,
            emergency_bilge=bilge_res,
            overall_status=overall_status,
            action_required=action_required,
            summary_warnings=all_warnings,
            compliance_matrix=matrix,
        )
