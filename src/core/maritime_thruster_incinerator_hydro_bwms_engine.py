"""Master Integration Facade for Maritime Phases 439-442.

Integrates Bow Thruster, Marine Incinerator, Hydrophore, and BWMS Neutralization.
Strictly < 100 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Optional

from src.core.maritime.phase_439_bow_thruster_hydraulic_interlocks import (
    BowThrusterEngine,
    BowThrusterTelemetry,
    BowThrusterAssessment,
)
from src.core.maritime.phase_440_marine_incinerator_safety import (
    IncineratorEngine,
    IncineratorTelemetry,
    IncineratorAssessment,
)
from src.core.maritime.phase_441_hydrophore_fresh_water_control import (
    HydrophoreEngine,
    HydrophoreTelemetry,
    HydrophoreAssessment,
)
from src.core.maritime.phase_442_bwms_tro_neutralization import (
    BwmsNeutralizationEngine,
    BwmsNeutralizationTelemetry,
    BwmsNeutralizationAssessment,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryMultiSystemAssessment:
    bow_thruster: Optional[BowThrusterAssessment]
    incinerator: Optional[IncineratorAssessment]
    hydrophore: Optional[HydrophoreAssessment]
    bwms_neutralization: Optional[BwmsNeutralizationAssessment]
    all_systems_healthy: bool


class MaritimeThrusterIncineratorHydroBwmsMasterEngine:
    def __init__(self) -> None:
        self.thruster_engine = BowThrusterEngine()
        self.incinerator_engine = IncineratorEngine()
        self.hydrophore_engine = HydrophoreEngine()
        self.bwms_engine = BwmsNeutralizationEngine()

    def evaluate_all(
        self,
        thruster: Optional[BowThrusterTelemetry] = None,
        incinerator: Optional[IncineratorTelemetry] = None,
        hydrophore: Optional[HydrophoreTelemetry] = None,
        hydrophore_pump_running: bool = False,
        bwms: Optional[BwmsNeutralizationTelemetry] = None,
    ) -> MaritimeAuxiliaryMultiSystemAssessment:
        t_res = self.thruster_engine.evaluate(thruster) if thruster else None
        i_res = self.incinerator_engine.evaluate(incinerator) if incinerator else None
        h_res = (
            self.hydrophore_engine.evaluate(hydrophore, hydrophore_pump_running)
            if hydrophore
            else None
        )
        b_res = self.bwms_engine.evaluate(bwms) if bwms else None

        healthy = True
        if t_res and not t_res.is_operational:
            healthy = False
        if i_res and len(i_res.trips) > 0:
            healthy = False
        if h_res and len(h_res.trips) > 0:
            healthy = False
        if b_res and not b_res.is_overboard_discharge_permitted:
            healthy = False

        return MaritimeAuxiliaryMultiSystemAssessment(
            bow_thruster=t_res,
            incinerator=i_res,
            hydrophore=h_res,
            bwms_neutralization=b_res,
            all_systems_healthy=healthy,
        )
