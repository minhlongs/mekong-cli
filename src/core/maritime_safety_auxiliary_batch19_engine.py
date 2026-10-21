"""Maritime Safety Auxiliary Batch 19 Coordinator Engine (Phases 535-538).
Aggregates Exhaust Valve Actuator, Cargo Pumproom, Hull Stress Slamming, and Helideck JP-5 Refueling.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_535_exhaust_valve_actuator_supervision import (
    ExhaustValveActuatorAssessment, ExhaustValveActuatorSupervisionEngine, ExhaustValveActuatorTelemetry,
)
from src.core.maritime.phase_536_cargo_pumproom_vent_gas_interlock import (
    CargoPumproomAssessment, CargoPumproomTelemetry, CargoPumproomVentGasInterlockEngine,
)
from src.core.maritime.phase_537_hull_stress_slamming_monitor import (
    HullStressSlammingAssessment, HullStressSlammingMonitorEngine, HullStressSlammingTelemetry,
)
from src.core.maritime.phase_538_helideck_jp5_refueling_interlock import (
    HelideckJp5RefuelingInterlockEngine, HelideckRefuelingAssessment, HelideckRefuelingTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch19Assessment:
    exhaust_valve_assessment: ExhaustValveActuatorAssessment
    cargo_pumproom_assessment: CargoPumproomAssessment
    hull_stress_assessment: HullStressSlammingAssessment
    helideck_refueling_assessment: HelideckRefuelingAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch19Engine:
    @classmethod
    def evaluate_batch19(
        cls,
        exhaust_valve: ExhaustValveActuatorTelemetry,
        cargo_pumproom: CargoPumproomTelemetry,
        hull_stress: HullStressSlammingTelemetry,
        helideck_refueling: HelideckRefuelingTelemetry,
    ) -> MaritimeAuxiliaryBatch19Assessment:
        res_exh = ExhaustValveActuatorSupervisionEngine.evaluate(exhaust_valve)
        res_pump = CargoPumproomVentGasInterlockEngine.evaluate(cargo_pumproom)
        res_hull = HullStressSlammingMonitorEngine.evaluate(hull_stress)
        res_jp5 = HelideckJp5RefuelingInterlockEngine.evaluate(helideck_refueling)

        alarms: List[str] = []
        if res_exh.interlock_code != "NONE":
            alarms.append(f"EXH_VALVE: {res_exh.interlock_code}")
        if res_pump.interlock_code != "NONE":
            alarms.append(f"CARGO_PUMPROOM: {res_pump.interlock_code}")
        if res_hull.interlock_code != "NONE":
            alarms.append(f"HULL_STRESS: {res_hull.interlock_code}")
        if res_jp5.interlock_code != "NONE":
            alarms.append(f"HELIDECK_JP5: {res_jp5.interlock_code}")

        return MaritimeAuxiliaryBatch19Assessment(
            exhaust_valve_assessment=res_exh,
            cargo_pumproom_assessment=res_pump,
            hull_stress_assessment=res_hull,
            helideck_refueling_assessment=res_jp5,
            overall_safe=len(alarms) == 0,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
