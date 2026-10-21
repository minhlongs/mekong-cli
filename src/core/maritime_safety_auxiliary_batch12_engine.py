"""Maritime Safety Auxiliary Batch 12 Coordinator Engine (Phases 507-510).
Aggregates Shaft Grounding, Emergency Bilge Suction, Watertight Doors, and Helideck Foam.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_507_shaft_grounding_slip_ring import (
    ShaftGroundingAssessment, ShaftGroundingSlipRingEngine, ShaftGroundingTelemetry,
)
from src.core.maritime.phase_508_emergency_bilge_direct_suction import (
    EmergencyBilgeAssessment, EmergencyBilgeDirectSuctionEngine, EmergencyBilgeTelemetry,
)
from src.core.maritime.phase_509_watertight_sliding_door_safety import (
    WatertightDoorAssessment, WatertightDoorTelemetry, WatertightSlidingDoorSafetyEngine,
)
from src.core.maritime.phase_510_helideck_foam_monitor_system import (
    HelideckFoamAssessment, HelideckFoamMonitorSystemEngine, HelideckFoamTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch12Assessment:
    shaft_assessment: ShaftGroundingAssessment
    bilge_assessment: EmergencyBilgeAssessment
    door_assessment: WatertightDoorAssessment
    helideck_assessment: HelideckFoamAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch12Engine:
    @classmethod
    def evaluate_batch12(
        cls,
        shaft: ShaftGroundingTelemetry,
        bilge: EmergencyBilgeTelemetry,
        door: WatertightDoorTelemetry,
        heli: HelideckFoamTelemetry,
    ) -> MaritimeAuxiliaryBatch12Assessment:
        res_shaft = ShaftGroundingSlipRingEngine.evaluate(shaft)
        res_bilge = EmergencyBilgeDirectSuctionEngine.evaluate(bilge)
        res_door = WatertightSlidingDoorSafetyEngine.evaluate(door)
        res_heli = HelideckFoamMonitorSystemEngine.evaluate(heli)

        alarms: List[str] = []
        if res_shaft.alarm_active:
            alarms.append(f"SHAFT: {res_shaft.alarm_code}")
        if res_bilge.alarm_active:
            alarms.append(f"BILGE: {res_bilge.alarm_code}")
        if res_door.alarm_active:
            alarms.append(f"WTD: {res_door.alarm_code}")
        if res_heli.alarm_active:
            alarms.append(f"HELIDECK: {res_heli.alarm_code}")

        overall_safe = (
            not res_shaft.alarm_active
            and not res_bilge.alarm_active
            and not res_door.alarm_active
            and not res_heli.alarm_active
        )

        return MaritimeAuxiliaryBatch12Assessment(
            shaft_assessment=res_shaft,
            bilge_assessment=res_bilge,
            door_assessment=res_door,
            helideck_assessment=res_heli,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
