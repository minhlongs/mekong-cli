"""Maritime Safety Auxiliary Batch 13 Coordinator Engine (Phases 511-514).
Aggregates Scavenge Condensate, Medical O2 Manifold, Mooring Winch Brake, and Water-Mist.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_511_scavenge_air_condensate_drain import (
    ScavengeAirCondensateDrainEngine, ScavengeCondensateAssessment, ScavengeCondensateTelemetry,
)
from src.core.maritime.phase_512_medical_oxygen_manifold_safety import (
    MedicalOxygenAssessment, MedicalOxygenManifoldSafetyEngine, MedicalOxygenTelemetry,
)
from src.core.maritime.phase_513_mooring_winch_brake_render import (
    MooringWinchAssessment, MooringWinchBrakeRenderEngine, MooringWinchTelemetry,
)
from src.core.maritime.phase_514_water_mist_local_application import (
    WaterMistAssessment, WaterMistLocalApplicationEngine, WaterMistTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch13Assessment:
    scavenge_assessment: ScavengeCondensateAssessment
    med_o2_assessment: MedicalOxygenAssessment
    mooring_assessment: MooringWinchAssessment
    water_mist_assessment: WaterMistAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch13Engine:
    @classmethod
    def evaluate_batch13(
        cls,
        scav: ScavengeCondensateTelemetry,
        med: MedicalOxygenTelemetry,
        mooring: MooringWinchTelemetry,
        mist: WaterMistTelemetry,
    ) -> MaritimeAuxiliaryBatch13Assessment:
        res_scav = ScavengeAirCondensateDrainEngine.evaluate(scav)
        res_med = MedicalOxygenManifoldSafetyEngine.evaluate(med)
        res_mooring = MooringWinchBrakeRenderEngine.evaluate(mooring)
        res_mist = WaterMistLocalApplicationEngine.evaluate(mist)

        alarms: List[str] = []
        if res_scav.alarm_active:
            alarms.append(f"SCAV: {res_scav.alarm_code}")
        if res_med.alarm_active:
            alarms.append(f"MED_O2: {res_med.alarm_code}")
        if res_mooring.alarm_active:
            alarms.append(f"MOORING: {res_mooring.alarm_code}")
        if res_mist.alarm_active:
            alarms.append(f"WATER_MIST: {res_mist.alarm_code}")

        overall_safe = (
            not res_scav.alarm_active
            and not res_med.alarm_active
            and not res_mooring.alarm_active
            and not res_mist.alarm_active
        )

        return MaritimeAuxiliaryBatch13Assessment(
            scavenge_assessment=res_scav,
            med_o2_assessment=res_med,
            mooring_assessment=res_mooring,
            water_mist_assessment=res_mist,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
