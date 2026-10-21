"""Maritime Safety Auxiliary Batch 14 Coordinator Engine (Phases 515-518).
Aggregates Anchor Windlass, Switchboard Insulation, Bow Visor Cleat, and Marine Elevator.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_515_anchor_windlass_payout_brake import (
    AnchorWindlassAssessment, AnchorWindlassPayoutBrakeEngine, AnchorWindlassTelemetry,
)
from src.core.maritime.phase_516_switchboard_insulation_load_shed import (
    SwitchboardAssessment, SwitchboardInsulationLoadShedEngine, SwitchboardTelemetry,
)
from src.core.maritime.phase_517_bow_visor_stern_ramp_cleat import (
    BowVisorRampAssessment, BowVisorRampTelemetry, BowVisorSternRampCleatEngine,
)
from src.core.maritime.phase_518_marine_elevator_roll_governor import (
    MarineElevatorAssessment, MarineElevatorRollGovernorEngine, MarineElevatorTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch14Assessment:
    windlass_assessment: AnchorWindlassAssessment
    switchboard_assessment: SwitchboardAssessment
    visor_assessment: BowVisorRampAssessment
    elevator_assessment: MarineElevatorAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch14Engine:
    @classmethod
    def evaluate_batch14(
        cls,
        windlass: AnchorWindlassTelemetry,
        msb: SwitchboardTelemetry,
        visor: BowVisorRampTelemetry,
        elevator: MarineElevatorTelemetry,
    ) -> MaritimeAuxiliaryBatch14Assessment:
        res_windlass = AnchorWindlassPayoutBrakeEngine.evaluate(windlass)
        res_msb = SwitchboardInsulationLoadShedEngine.evaluate(msb)
        res_visor = BowVisorSternRampCleatEngine.evaluate(visor)
        res_elev = MarineElevatorRollGovernorEngine.evaluate(elevator)

        alarms: List[str] = []
        if res_windlass.alarm_active:
            alarms.append(f"WINDLASS: {res_windlass.alarm_code}")
        if res_msb.alarm_active:
            alarms.append(f"MSB: {res_msb.alarm_code}")
        if res_visor.alarm_active:
            alarms.append(f"VISOR: {res_visor.alarm_code}")
        if res_elev.alarm_active:
            alarms.append(f"ELEVATOR: {res_elev.alarm_code}")

        overall_safe = (
            not res_windlass.alarm_active
            and not res_msb.alarm_active
            and not res_visor.alarm_active
            and not res_elev.alarm_active
        )

        return MaritimeAuxiliaryBatch14Assessment(
            windlass_assessment=res_windlass,
            switchboard_assessment=res_msb,
            visor_assessment=res_visor,
            elevator_assessment=res_elev,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
