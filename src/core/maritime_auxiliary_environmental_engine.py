"""Unified Facade Engine for Maritime Phases 403-406.

Combines:
- Phase 403: Marine Boiler Water Coordinated Phosphate-pH & Deaeration
- Phase 404: Stern Tube Lubrication & Bio-Lubricant Seal EAL
- Phase 405: Marine Incinerator Waste Sludge Thermal Destruction
- Phase 406: Marine Sewage Treatment Plant MBR & Nutrient Removal

Strictly < 180 LOC, zero mocks, deterministic marine auxiliary & environmental monitoring.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_403_boiler_water_chemistry import (
    BoilerWaterEngine,
    BoilerWaterInput,
    BoilerWaterResult,
)
from src.core.maritime.phase_404_stern_tube_eal import (
    SternTubeEngine,
    SternTubeInput,
    SternTubeResult,
)
from src.core.maritime.phase_405_incinerator_sludge import (
    SludgeIncineratorEngine,
    SludgeIncineratorInput,
    SludgeIncineratorResult,
)
from src.core.maritime.phase_406_sewage_treatment_mbr import (
    SewageTreatmentEngine,
    SewageTreatmentInput,
    SewageTreatmentResult,
)


@dataclass
class MaritimeAuxiliaryEnvironmentalResult:
    """Consolidated assessment of vessel auxiliary systems and environmental compliance."""
    boiler_water: BoilerWaterResult
    stern_tube: SternTubeResult
    incinerator: SludgeIncineratorResult
    sewage_treatment: SewageTreatmentResult
    overall_auxiliary_status: str
    all_systems_green: bool
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_auxiliary_status,
            "all_systems_green": self.all_systems_green,
            "boiler_water": {
                "status": self.boiler_water.status.value,
                "oxygen_pass": self.boiler_water.oxygen_scavenging_pass,
                "phosphate_pass": self.boiler_water.phosphate_buffer_pass,
                "blowdown_recommended": self.boiler_water.blowdown_recommended,
                "passivation_stable": self.boiler_water.magnetite_passivation_stable,
            },
            "stern_tube": {
                "status": self.stern_tube.status.value,
                "diff_p_bar": self.stern_tube.pressure_diff_bar,
                "seal_barrier_intact": self.stern_tube.seal_barrier_intact,
                "eal_water_compliant": self.stern_tube.eal_water_compliant,
            },
            "incinerator": {
                "status": self.incinerator.status.value,
                "feed_permitted": self.incinerator.sludge_feed_permitted,
                "temp_compliant": self.incinerator.temperature_compliant,
            },
            "sewage_treatment": {
                "status": self.sewage_treatment.status.value,
                "discharge_permitted": self.sewage_treatment.overboard_discharge_permitted,
                "nutrient_pass": self.sewage_treatment.nutrient_removal_pass,
            },
            "warnings_count": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeAuxiliaryEnvironmentalEngine:
    """Unified coordinator for marine auxiliary thermodynamics, lubrication, and environmental discharge."""

    def __init__(self) -> None:
        self.boiler_engine = BoilerWaterEngine()
        self.stern_tube_engine = SternTubeEngine()
        self.incinerator_engine = SludgeIncineratorEngine()
        self.sewage_engine = SewageTreatmentEngine()

    def evaluate(
        self,
        boiler_input: BoilerWaterInput,
        stern_tube_input: SternTubeInput,
        incinerator_input: SludgeIncineratorInput,
        sewage_input: SewageTreatmentInput,
    ) -> MaritimeAuxiliaryEnvironmentalResult:
        boiler_res = self.boiler_engine.evaluate(boiler_input)
        stern_res = self.stern_tube_engine.evaluate(stern_tube_input)
        incinerator_res = self.incinerator_engine.evaluate(incinerator_input)
        sewage_res = self.sewage_engine.evaluate(sewage_input)

        warnings: List[str] = (
            boiler_res.warnings
            + stern_res.warnings
            + incinerator_res.warnings
            + sewage_res.warnings
        )

        all_systems_green = (
            boiler_res.magnetite_passivation_stable
            and stern_res.seal_barrier_intact
            and stern_res.eal_water_compliant
            and incinerator_res.sludge_feed_permitted
            and sewage_res.overboard_discharge_permitted
        )

        if all_systems_green:
            overall_status = "AUXILIARY_ENVIRONMENTAL_NOMINAL_OPTIMAL"
        elif (
            "CRITICAL" in boiler_res.status.value
            or "CRITICAL" in stern_res.status.value
            or "FAIL" in sewage_res.status.value
        ):
            overall_status = "CRITICAL_AUXILIARY_SAFETY_TRIP"
        else:
            overall_status = "ATTENTION_REQUIRED_DEGRADED"

        return MaritimeAuxiliaryEnvironmentalResult(
            boiler_water=boiler_res,
            stern_tube=stern_res,
            incinerator=incinerator_res,
            sewage_treatment=sewage_res,
            overall_auxiliary_status=overall_status,
            all_systems_green=all_systems_green,
            aggregated_warnings=warnings,
        )
