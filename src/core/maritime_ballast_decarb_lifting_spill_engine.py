"""Facade for Maritime Ballast, Decarb, Lifting & Spill Engines (Phases 327-330).

Provides backward-compatible direct imports and unified surface for all
Phase 327-330 compliance modules.
"""

from src.core.maritime.phase_327_ballast_water_uscg import (
    BallastWaterComplianceEngine,
    BallastWaterQualityInput,
    BallastWaterQualityResult,
)
from src.core.maritime.phase_328_decarb_fueleu_fuels import (
    DecarbEvaluationResult,
    DualFuelBunkeringInput,
    EuEtsFuelEuInput,
    MaritimeDecarbFuelEngine,
)
from src.core.maritime.phase_329_lifting_appliances import (
    LiftingApplianceInput,
    LiftingApplianceResult,
    PortLiftingComplianceEngine,
)
from src.core.maritime.phase_330_oil_spill_oprc_neba import (
    MarineOilSpillResponseEngine,
    OilSpillIncidentInput,
    OilSpillResponseResult,
)

__all__ = [
    "BallastWaterComplianceEngine",
    "BallastWaterQualityInput",
    "BallastWaterQualityResult",
    "DecarbEvaluationResult",
    "DualFuelBunkeringInput",
    "EuEtsFuelEuInput",
    "MaritimeDecarbFuelEngine",
    "LiftingApplianceInput",
    "LiftingApplianceResult",
    "PortLiftingComplianceEngine",
    "MarineOilSpillResponseEngine",
    "OilSpillIncidentInput",
    "OilSpillResponseResult",
]
