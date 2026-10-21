"""Master Unified Maritime Auxiliary & Safety Engine (Phases 419-422).

Combines:
- Phase 419: Marine Auxiliary Boiler Drum Level & Blowdown (IACS M53, SOLAS II-1/32)
- Phase 420: STP Electrolytic Chlorination & Dechlorination (MEPC.227(64), MARPOL IV)
- Phase 421: Ballast Tank ICCP & Sacrificial Zinc Anode Depletion (DNV-RP-B401)
- Phase 422: Hyper-Mist Local Water-Based Machinery Fire Extinguishing (SOLAS II-2/10)

Strictly < 150 LOC, zero mocks.
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from src.core.maritime.phase_419_boiler_drum_blowdown import (
    BoilerDrumBlowdownEngine,
    BoilerDrumTelemetry,
    BoilerDrumAssessment,
)
from src.core.maritime.phase_420_stp_electrolytic_chlorination import (
    StpChlorinationEngine,
    StpChlorinationTelemetry,
    StpChlorinationAssessment,
)
from src.core.maritime.phase_421_ballast_anodic_protection import (
    BallastAnodicProtectionEngine,
    BallastAnodicTelemetry,
    BallastAnodicAssessment,
)
from src.core.maritime.phase_422_hypermist_water_fire import (
    HyperMistFireExtinguishingEngine,
    HyperMistTelemetry,
    HyperMistAssessment,
)


@dataclass(frozen=True)
class MaritimePhases419to422Telemetry:
    """Consolidated telemetry for maritime auxiliary machinery and safety systems."""
    boiler: BoilerDrumTelemetry = field(default_factory=BoilerDrumTelemetry)
    stp: StpChlorinationTelemetry = field(default_factory=StpChlorinationTelemetry)
    ballast: BallastAnodicTelemetry = field(default_factory=BallastAnodicTelemetry)
    hypermist: HyperMistTelemetry = field(default_factory=HyperMistTelemetry)


@dataclass(frozen=True)
class MaritimePhases419to422Assessment:
    """Consolidated safety and operational assessment for Phases 419-422."""
    boiler: BoilerDrumAssessment
    stp: StpChlorinationAssessment
    ballast: BallastAnodicAssessment
    hypermist: HyperMistAssessment
    overall_status: str
    all_systems_operational: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boiler_status": self.boiler.status,
            "boiler_tripped": self.boiler.burner_tripped,
            "stp_status": self.stp.status,
            "stp_overboard_permitted": self.stp.overboard_discharge_permitted,
            "ballast_status": self.ballast.status,
            "ballast_depletion_pct": self.ballast.remaining_anode_life_pct,
            "hypermist_status": self.hypermist.status,
            "hypermist_fire_confirmed": self.hypermist.fire_confirmed,
            "overall_status": self.overall_status,
            "all_systems_operational": self.all_systems_operational,
        }


class MaritimeAuxiliarySafetyEngine:
    """Unified controller orchestrating phases 419 through 422."""

    def __init__(self) -> None:
        self.boiler_engine = BoilerDrumBlowdownEngine()
        self.stp_engine = StpChlorinationEngine()
        self.ballast_engine = BallastAnodicProtectionEngine()
        self.hypermist_engine = HyperMistFireExtinguishingEngine()

    def evaluate_all(self, telemetry: MaritimePhases419to422Telemetry) -> MaritimePhases419to422Assessment:
        boiler_res = self.boiler_engine.evaluate(telemetry.boiler)
        stp_res = self.stp_engine.evaluate(telemetry.stp)
        ballast_res = self.ballast_engine.evaluate(telemetry.ballast)
        hypermist_res = self.hypermist_engine.evaluate(telemetry.hypermist)

        critical_alert = (
            boiler_res.burner_tripped or
            hypermist_res.fire_confirmed or
            ballast_res.over_protection_embrittlement_risk
        )
        has_warnings = bool(
            boiler_res.warnings or
            stp_res.warnings or
            ballast_res.warnings or
            hypermist_res.warnings
        )

        overall_status = "CRITICAL" if critical_alert else ("WARNING" if has_warnings else "NORMAL")
        all_systems_operational = not boiler_res.burner_tripped and stp_res.overboard_discharge_permitted and not hypermist_res.fire_confirmed

        return MaritimePhases419to422Assessment(
            boiler=boiler_res,
            stp=stp_res,
            ballast=ballast_res,
            hypermist=hypermist_res,
            overall_status=overall_status,
            all_systems_operational=all_systems_operational,
        )
