"""Master Orchestrator Engine for Maritime Phases 463-466.

Aggregates:
- Phase 463: Stern Tube Gravity Tank (IACS UR M56)
- Phase 464: Deck Water Seal (SOLAS II-2 Reg 4.5.5)
- Phase 465: Scavenge Air Fire (SOLAS II-2 Reg 10.5)
- Phase 466: Fresh Water Generator Salinometer (MARPOL & DNV)
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_463_stern_tube_gravity_tank import (
    SternTubeGravityTankEngine,
    SternTubeGravityTelemetry,
    SternTubeGravityAssessment,
)
from src.core.maritime.phase_464_deck_water_seal_inert_gas import (
    DeckWaterSealEngine,
    DeckWaterSealTelemetry,
    DeckWaterSealAssessment,
)
from src.core.maritime.phase_465_main_engine_scavenge_air_fire import (
    ScavengeAirFireEngine,
    ScavengeFireTelemetry,
    ScavengeFireAssessment,
)
from src.core.maritime.phase_466_fresh_water_generator_salinometer import (
    FreshWaterGeneratorEngine,
    FwgSalinometerTelemetry,
    FwgSalinometerAssessment,
)


@dataclass(frozen=True)
class MarineSafetyAuxiliaryAssessment:
    stern_tube: SternTubeGravityAssessment
    deck_seal: DeckWaterSealAssessment
    scavenge_fire: ScavengeFireAssessment
    fresh_water_gen: FwgSalinometerAssessment
    overall_safety_interlock_ok: bool
    engine_slowdown_tripped: bool


class MaritimeSafetyAuxiliaryMasterEngine:
    """Master facade coordinating phases 463-466 maritime auxiliary safety."""

    @classmethod
    def evaluate_all(
        cls,
        stern_tube_telem: SternTubeGravityTelemetry,
        deck_seal_telem: DeckWaterSealTelemetry,
        scavenge_telem: ScavengeFireTelemetry,
        fwg_telem: FwgSalinometerTelemetry,
    ) -> MarineSafetyAuxiliaryAssessment:
        stern = SternTubeGravityTankEngine.evaluate(stern_tube_telem)
        seal = DeckWaterSealEngine.evaluate(deck_seal_telem)
        scavenge = ScavengeAirFireEngine.evaluate(scavenge_telem)
        fwg = FreshWaterGeneratorEngine.evaluate(fwg_telem)

        interlock_ok = not (
            stern.water_ingress_detected
            or seal.backflow_risk
            or scavenge.fire_detected
            or not fwg.vacuum_satisfactory
        )

        slowdown_tripped = scavenge.engine_slowdown_required

        return MarineSafetyAuxiliaryAssessment(
            stern_tube=stern,
            deck_seal=seal,
            scavenge_fire=scavenge,
            fresh_water_gen=fwg,
            overall_safety_interlock_ok=interlock_ok,
            engine_slowdown_tripped=slowdown_tripped,
        )
