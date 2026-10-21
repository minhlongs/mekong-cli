"""Master Cross-System Unified Assessment Engine for Phases 447-450:
- Phase 447: Crude Oil Washing (COW) Operation (IMO A.446(XI))
- Phase 448: Fixed Deck Foam Fire-Extinguishing (SOLAS II-2 Reg 10.8)
- Phase 449: Boiler Flue Gas Desulfurization (MARPOL Annex VI)
- Phase 450: Vapor Emission Control System (VECS) (USCG 46 CFR 39)
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_447_crude_oil_washing_machine import (
    CrudeOilWashingEngine,
    CowTelemetry,
    CowAssessment,
)
from src.core.maritime.phase_448_fixed_deck_foam_extinguishing import (
    DeckFoamFireSystemEngine,
    DeckFoamTelemetry,
    DeckFoamAssessment,
)
from src.core.maritime.phase_449_boiler_flue_gas_desulfurization import (
    BoilerFlueGasScrubberEngine,
    ScrubberTelemetry,
    ScrubberAssessment,
)
from src.core.maritime.phase_450_vapor_emission_control_vecs import (
    VaporEmissionControlEngine,
    VecsTelemetry,
    VecsAssessment,
)


@dataclass(frozen=True)
class TankerSafetyIntegratedTelemetry:
    cow: CowTelemetry
    foam: DeckFoamTelemetry
    scrubber: ScrubberTelemetry
    vecs: VecsTelemetry


@dataclass(frozen=True)
class TankerSafetyIntegratedAssessment:
    overall_safe: bool
    cow_assessment: CowAssessment
    foam_assessment: DeckFoamAssessment
    scrubber_assessment: ScrubberAssessment
    vecs_assessment: VecsAssessment
    critical_trips: list[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_safe": self.overall_safe,
            "cow_status": self.cow_assessment.status.value,
            "foam_status": self.foam_assessment.status.value,
            "scrubber_status": self.scrubber_assessment.status.value,
            "vecs_status": self.vecs_assessment.status.value,
            "critical_trips": self.critical_trips,
        }


class TankerSafetyIntegratedEngine:
    def __init__(self) -> None:
        self.cow_engine = CrudeOilWashingEngine()
        self.foam_engine = DeckFoamFireSystemEngine()
        self.scrubber_engine = BoilerFlueGasScrubberEngine()
        self.vecs_engine = VaporEmissionControlEngine()

    def evaluate_all(self, telem: TankerSafetyIntegratedTelemetry) -> TankerSafetyIntegratedAssessment:
        cow_res = self.cow_engine.evaluate(telem.cow)
        foam_res = self.foam_engine.evaluate(telem.foam)
        scrubber_res = self.scrubber_engine.evaluate(telem.scrubber)
        vecs_res = self.vecs_engine.evaluate(telem.vecs)

        trips: list[str] = []
        if not cow_res.is_wash_permitted:
            trips.append(f"COW: {cow_res.action_summary}")
        if not foam_res.is_ready_or_effective:
            trips.append(f"FOAM: {foam_res.action_summary}")
        if not scrubber_res.is_scrubber_compliant:
            trips.append(f"SCRUBBER: {scrubber_res.action_summary}")
        if not vecs_res.is_transfer_permitted:
            trips.append(f"VECS: {vecs_res.action_summary}")

        overall_safe = len(trips) == 0

        return TankerSafetyIntegratedAssessment(
            overall_safe=overall_safe,
            cow_assessment=cow_res,
            foam_assessment=foam_res,
            scrubber_assessment=scrubber_res,
            vecs_assessment=vecs_res,
            critical_trips=trips,
        )
