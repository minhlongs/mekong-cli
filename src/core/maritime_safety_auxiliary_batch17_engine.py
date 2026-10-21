"""Maritime Safety Auxiliary Batch 17 Coordinator Engine (Phases 527-530).
Aggregates Cylinder Lubricator ACC, Bilge Holding Tank, Cargo Smoke Extraction, and Free-Fall Lifeboat.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_527_cylinder_lubricator_alpha_dosage import (
    CylinderLubricatorAlphaDosageEngine, CylinderLubricatorAssessment, CylinderLubricatorTelemetry,
)
from src.core.maritime.phase_528_bilge_holding_tank_interface import (
    BilgeHoldingTankAssessment, BilgeHoldingTankInterfaceEngine, BilgeHoldingTankTelemetry,
)
from src.core.maritime.phase_529_cargo_smoke_extraction_fan_supervision import (
    CargoSmokeExtractionAssessment, CargoSmokeExtractionFanSupervisionEngine, CargoSmokeExtractionTelemetry,
)
from src.core.maritime.phase_530_freefall_lifeboat_release_interlock import (
    FreefallLifeboatAssessment, FreefallLifeboatReleaseInterlockEngine, FreefallLifeboatTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch17Assessment:
    cylinder_lubricator_assessment: CylinderLubricatorAssessment
    bilge_holding_tank_assessment: BilgeHoldingTankAssessment
    cargo_smoke_extraction_assessment: CargoSmokeExtractionAssessment
    freefall_lifeboat_assessment: FreefallLifeboatAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch17Engine:
    @classmethod
    def evaluate_batch17(
        cls,
        cylinder_lubricator: CylinderLubricatorTelemetry,
        bilge_holding_tank: BilgeHoldingTankTelemetry,
        cargo_smoke_extraction: CargoSmokeExtractionTelemetry,
        freefall_lifeboat: FreefallLifeboatTelemetry,
    ) -> MaritimeAuxiliaryBatch17Assessment:
        res_lub = CylinderLubricatorAlphaDosageEngine.evaluate(cylinder_lubricator)
        res_bilge = BilgeHoldingTankInterfaceEngine.evaluate(bilge_holding_tank)
        res_smoke = CargoSmokeExtractionFanSupervisionEngine.evaluate(cargo_smoke_extraction)
        res_boat = FreefallLifeboatReleaseInterlockEngine.evaluate(freefall_lifeboat)

        alarms: List[str] = []
        if res_lub.alarm_active:
            alarms.append(f"CYL_LUBRICATOR: {res_lub.alarm_code}")
        if res_bilge.alarm_active:
            alarms.append(f"BILGE_HOLDING: {res_bilge.alarm_code}")
        if res_smoke.alarm_active:
            alarms.append(f"CARGO_SMOKE: {res_smoke.alarm_code}")
        if res_boat.alarm_active:
            alarms.append(f"FREEFALL_BOAT: {res_boat.alarm_code}")

        overall_safe = (
            not res_lub.alarm_active
            and not res_bilge.alarm_active
            and not res_smoke.alarm_active
            and not res_boat.alarm_active
        )

        return MaritimeAuxiliaryBatch17Assessment(
            cylinder_lubricator_assessment=res_lub,
            bilge_holding_tank_assessment=res_bilge,
            cargo_smoke_extraction_assessment=res_smoke,
            freefall_lifeboat_assessment=res_boat,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
