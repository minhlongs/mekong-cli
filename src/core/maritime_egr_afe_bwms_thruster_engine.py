"""Unified Facade Engine for Maritime Phases 419-422.

Integrates:
- Phase 419: EGR Bleed-off Water Treatment System (MEPC.307(73))
- Phase 420: Shaft Generator Active Front End (AFE) Harmonics (IACS UR E24 / IEEE 519)
- Phase 421: BWMS Electro-Chlorination & Neutralization (IMO BWM D-2)
- Phase 422: Stern Thruster Tunnel Grate & CPP Pitch Cavitation (DNV Pt.4 Ch.5)

Strictly zero mocks, < 200 LOC.
"""

from dataclasses import dataclass, field
from typing import List

from src.core.maritime.phase_419_egr_bleedoff_water_treatment import (
    EgrBleedoffAssessment,
    EgrBleedoffTelemetry,
    EgrBleedoffWaterTreatmentEngine,
)
from src.core.maritime.phase_420_shaft_generator_afe_harmonics import (
    ShaftGeneratorAfeAssessment,
    ShaftGeneratorAfeHarmonicsEngine,
    ShaftGeneratorAfeTelemetry,
)
from src.core.maritime.phase_421_bwms_chlorination_neutralization import (
    BwmsChlorinationAssessment,
    BwmsChlorinationNeutralizationEngine,
    BwmsChlorinationTelemetry,
)
from src.core.maritime.phase_422_stern_thruster_cavitation_pitch import (
    SternThrusterCavitationAssessment,
    SternThrusterCavitationEngine,
    SternThrusterCavitationTelemetry,
)


@dataclass(frozen=True)
class MaritimeEgrAfeBwmsThrusterTelemetry:
    """Aggregated telemetry inputs for Phases 419-422."""
    egr: EgrBleedoffTelemetry = field(default_factory=EgrBleedoffTelemetry)
    shaft_gen: ShaftGeneratorAfeTelemetry = field(default_factory=ShaftGeneratorAfeTelemetry)
    bwms: BwmsChlorinationTelemetry = field(default_factory=BwmsChlorinationTelemetry)
    stern_thruster: SternThrusterCavitationTelemetry = field(
        default_factory=SternThrusterCavitationTelemetry
    )


@dataclass
class MaritimeEgrAfeBwmsThrusterResult:
    """Consolidated assessment outcome for Phases 419-422."""
    egr: EgrBleedoffAssessment
    shaft_gen: ShaftGeneratorAfeAssessment
    bwms: BwmsChlorinationAssessment
    stern_thruster: SternThrusterCavitationAssessment
    all_compliant: bool
    summary_status: str
    active_alarms: List[str]


class MaritimeEgrAfeBwmsThrusterEngine:
    """Unified Orchestrator across EGR WTS, Shaft Gen AFE, BWMS, and Stern Thruster."""

    def __init__(self) -> None:
        self.egr_engine = EgrBleedoffWaterTreatmentEngine()
        self.shaft_gen_engine = ShaftGeneratorAfeHarmonicsEngine()
        self.bwms_engine = BwmsChlorinationNeutralizationEngine()
        self.stern_thruster_engine = SternThrusterCavitationEngine()

    def evaluate(
        self, telemetry: MaritimeEgrAfeBwmsThrusterTelemetry
    ) -> MaritimeEgrAfeBwmsThrusterResult:
        egr_res = self.egr_engine.evaluate(telemetry.egr)
        shaft_res = self.shaft_gen_engine.evaluate(telemetry.shaft_gen)
        bwms_res = self.bwms_engine.evaluate(telemetry.bwms)
        thruster_res = self.stern_thruster_engine.evaluate(telemetry.stern_thruster)

        alarms: List[str] = []
        alarms.extend([f"[EGR] {w}" for w in egr_res.warnings])
        alarms.extend([f"[SHAFT_GEN] {w}" for w in shaft_res.warnings])
        alarms.extend([f"[BWMS] {w}" for w in bwms_res.warnings])
        alarms.extend([f"[STERN_THRUSTER] {w}" for w in thruster_res.warnings])

        all_ok = (
            egr_res.status == "COMPLIANT"
            and shaft_res.status in ("AFE_STABLE", "GFRT_RIDING_THROUGH")
            and bwms_res.status == "COMPLIANT_ACTIVE"
            and thruster_res.status == "SUB_CAVITATING_OPTIMAL"
        )

        summary = "FULLY_COMPLIANT_AND_OPTIMAL" if all_ok else "ALERTS_ACTIVE"

        return MaritimeEgrAfeBwmsThrusterResult(
            egr=egr_res,
            shaft_gen=shaft_res,
            bwms=bwms_res,
            stern_thruster=thruster_res,
            all_compliant=all_ok,
            summary_status=summary,
            active_alarms=alarms,
        )
