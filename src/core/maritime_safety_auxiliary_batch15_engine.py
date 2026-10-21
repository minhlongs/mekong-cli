"""Maritime Safety Auxiliary Batch 15 Coordinator Engine (Phases 519-522).
Aggregates Turning Gear Interlock, Grey Water Tank, Deck Crane Limiter, and Escape Trunk.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_519_turning_gear_start_interlock import (
    TurningGearAssessment, TurningGearStartInterlockEngine, TurningGearTelemetry,
)
from src.core.maritime.phase_520_grey_water_tank_ventilation import (
    GreyWaterAssessment, GreyWaterTankVentilationEngine, GreyWaterTelemetry,
)
from src.core.maritime.phase_521_deck_crane_overload_limiter import (
    DeckCraneAssessment, DeckCraneOverloadLimiterEngine, DeckCraneTelemetry,
)
from src.core.maritime.phase_522_escape_trunk_pressurization import (
    EscapeTrunkAssessment, EscapeTrunkPressurizationEngine, EscapeTrunkTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch15Assessment:
    turning_gear_assessment: TurningGearAssessment
    grey_water_assessment: GreyWaterAssessment
    crane_assessment: DeckCraneAssessment
    escape_trunk_assessment: EscapeTrunkAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch15Engine:
    @classmethod
    def evaluate_batch15(
        cls,
        turning_gear: TurningGearTelemetry,
        grey_water: GreyWaterTelemetry,
        crane: DeckCraneTelemetry,
        escape_trunk: EscapeTrunkTelemetry,
    ) -> MaritimeAuxiliaryBatch15Assessment:
        res_tg = TurningGearStartInterlockEngine.evaluate(turning_gear)
        res_gw = GreyWaterTankVentilationEngine.evaluate(grey_water)
        res_crane = DeckCraneOverloadLimiterEngine.evaluate(crane)
        res_trunk = EscapeTrunkPressurizationEngine.evaluate(escape_trunk)

        alarms: List[str] = []
        if res_tg.alarm_active:
            alarms.append(f"TURNING_GEAR: {res_tg.alarm_code}")
        if res_gw.alarm_active:
            alarms.append(f"GREYWATER: {res_gw.alarm_code}")
        if res_crane.alarm_active:
            alarms.append(f"CRANE: {res_crane.alarm_code}")
        if res_trunk.alarm_active:
            alarms.append(f"ESCAPE_TRUNK: {res_trunk.alarm_code}")

        overall_safe = (
            not res_tg.alarm_active
            and not res_gw.alarm_active
            and not res_crane.alarm_active
            and not res_trunk.alarm_active
        )

        return MaritimeAuxiliaryBatch15Assessment(
            turning_gear_assessment=res_tg,
            grey_water_assessment=res_gw,
            crane_assessment=res_crane,
            escape_trunk_assessment=res_trunk,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
