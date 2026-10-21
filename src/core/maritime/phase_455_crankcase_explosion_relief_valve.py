"""Phase 455: Engine Crankcase Explosion Relief Valve & Flame Quenching Mesh.

Compliant with IACS UR M9 & SOLAS II-1 Reg 31.
Monitors crankcase overpressure relief discharge, spring re-seating against
air ingress, flame arrester wire gauze thermal absorption, and fouling.
"""

from dataclasses import dataclass
from enum import Enum


class CrankcaseValveStatus(str, Enum):
    NORMAL = "NORMAL"
    RELIEF_ACTIVE = "RELIEF_ACTIVE"
    AIR_INGRESS_HAZARD = "AIR_INGRESS_HAZARD"
    MESH_FOULING_ALARM = "MESH_FOULING_ALARM"
    CRITICAL_EXPLOSION = "CRITICAL_EXPLOSION"


@dataclass(frozen=True)
class CrankcaseValveTelemetry:
    crankcase_pressure_bar: float
    valve_lift_mm: float
    relief_reseated: bool
    flame_mesh_clear_pct: float
    flame_mesh_temp_celsius: float


@dataclass(frozen=True)
class CrankcaseValveAssessment:
    status: CrankcaseValveStatus
    explosion_relief_active: bool
    air_ingress_hazard: bool
    mesh_fouling_alarm: bool
    flame_quenched: bool
    safety_alarm: bool
    remarks: str


class CrankcaseExplosionReliefEngine:
    RELIEF_CRACKING_PRESSURE_BAR: float = 0.20
    CRITICAL_EXPLOSION_BAR: float = 0.50
    MIN_FLAME_MESH_CLEAR_PCT: float = 85.0
    MAX_MESH_EXIT_TEMP_CELSIUS: float = 150.0

    @classmethod
    def evaluate(cls, telemetry: CrankcaseValveTelemetry) -> CrankcaseValveAssessment:
        mesh_fouled = telemetry.flame_mesh_clear_pct < cls.MIN_FLAME_MESH_CLEAR_PCT
        if telemetry.crankcase_pressure_bar >= cls.CRITICAL_EXPLOSION_BAR:
            return CrankcaseValveAssessment(
                status=CrankcaseValveStatus.CRITICAL_EXPLOSION,
                explosion_relief_active=True,
                air_ingress_hazard=not telemetry.relief_reseated,
                mesh_fouling_alarm=mesh_fouled,
                flame_quenched=telemetry.flame_mesh_temp_celsius <= cls.MAX_MESH_EXIT_TEMP_CELSIUS,
                safety_alarm=True,
                remarks="Severe crankcase detonation: Emergency engine stop initiated",
            )

        if mesh_fouled:
            return CrankcaseValveAssessment(
                status=CrankcaseValveStatus.MESH_FOULING_ALARM,
                explosion_relief_active=False,
                air_ingress_hazard=False,
                mesh_fouling_alarm=True,
                flame_quenched=False,
                safety_alarm=True,
                remarks="Flame arrester mesh fouled with carbon deposits below 85%",
            )

        if telemetry.crankcase_pressure_bar >= cls.RELIEF_CRACKING_PRESSURE_BAR:
            air_ingress = not telemetry.relief_reseated
            status = (
                CrankcaseValveStatus.AIR_INGRESS_HAZARD
                if air_ingress
                else CrankcaseValveStatus.RELIEF_ACTIVE
            )
            quenched = telemetry.flame_mesh_temp_celsius <= cls.MAX_MESH_EXIT_TEMP_CELSIUS
            return CrankcaseValveAssessment(
                status=status,
                explosion_relief_active=True,
                air_ingress_hazard=air_ingress,
                mesh_fouling_alarm=False,
                flame_quenched=quenched,
                safety_alarm=air_ingress or not quenched,
                remarks="Overpressure venting active; checking spring closure and quenching",
            )

        return CrankcaseValveAssessment(
            status=CrankcaseValveStatus.NORMAL,
            explosion_relief_active=False,
            air_ingress_hazard=False,
            mesh_fouling_alarm=False,
            flame_quenched=True,
            safety_alarm=False,
            remarks="Crankcase relief valve seated and flame mesh clear",
        )
