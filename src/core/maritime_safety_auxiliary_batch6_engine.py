"""Master Coordinator Engine for Maritime Automation Phases 483-486.

Coordinates:
- Phase 483: STP Aeration & Sludge Return
- Phase 484: Main Engine Bearing Mist & Slowdown
- Phase 485: EGB Circulation & Dry-Run Interlock
- Phase 486: Emergency Diesel Generator Blackout Auto-Start

Strictly < 95 LOC.
"""

from dataclasses import dataclass

from src.core.maritime.phase_483_stp_aeration_sludge_return import (
    StpAerationAssessment,
    StpAerationSludgeReturnEngine,
    StpAerationStatus,
    StpAerationTelemetry,
)
from src.core.maritime.phase_484_bearing_mist_slowdown import (
    BearingMistSlowdownAssessment,
    BearingMistSlowdownEngine,
    BearingMistSlowdownTelemetry,
    BearingMistStatus,
)
from src.core.maritime.phase_485_egb_circulation_dryrun import (
    EgbCirculationAssessment,
    EgbCirculationDryRunEngine,
    EgbCirculationStatus,
    EgbCirculationTelemetry,
)
from src.core.maritime.phase_486_emergency_gen_blackout import (
    EmergencyGenAssessment,
    EmergencyGenBlackoutEngine,
    EmergencyGenStatus,
    EmergencyGenTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch6Telemetry:
    stp: StpAerationTelemetry
    bearing: BearingMistSlowdownTelemetry
    egb: EgbCirculationTelemetry
    edg: EmergencyGenTelemetry


@dataclass(frozen=True)
class MaritimePhases483to486Assessment:
    stp_eval: StpAerationAssessment
    bearing_eval: BearingMistSlowdownAssessment
    egb_eval: EgbCirculationAssessment
    edg_eval: EmergencyGenAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: str


class MaritimeSafetyAuxiliaryBatch6Engine:
    @classmethod
    def evaluate(cls, telem: MaritimeAuxiliaryBatch6Telemetry) -> MaritimePhases483to486Assessment:
        stp = StpAerationSludgeReturnEngine.evaluate(telem.stp)
        brg = BearingMistSlowdownEngine.evaluate(telem.bearing)
        egb = EgbCirculationDryRunEngine.evaluate(telem.egb)
        edg = EmergencyGenBlackoutEngine.evaluate(telem.edg)

        alarms = sum([
            stp.status not in (StpAerationStatus.NORMAL, StpAerationStatus.LOW_DO_WARNING),
            brg.status != BearingMistStatus.NORMAL,
            egb.status not in (EgbCirculationStatus.NORMAL, EgbCirculationStatus.PUMP_CAVITATION_WARNING),
            edg.status not in (EmergencyGenStatus.NORMAL, EmergencyGenStatus.EMERGENCY_POWER_CONNECTED),
        ])

        overall_safe = (
            stp.aerobic_treatment_healthy
            and not brg.slowdown_command
            and egb.circulation_adequate
            and edg.fuel_endurance_ok
            and alarms == 0
        )

        return MaritimePhases483to486Assessment(
            stp_eval=stp,
            bearing_eval=brg,
            egb_eval=egb,
            edg_eval=edg,
            overall_safe=overall_safe,
            active_alarms_count=alarms,
            system_health_summary=f"Batch 6 Evaluated. Active Alarms: {alarms}. Safe: {overall_safe}.",
        )
