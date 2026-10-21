"""Phase 495: ME Cylinder Liner Thermal Stress & Scavenge Drain Protection.

Complies with IACS UR M10 & M38 for two-stroke marine diesel engines.
Evaluates liner wall temperature, thermal shock rate, orifice differential pressure,
and scavenge air box drain sludge temperature to prevent scavenge fires.
Strictly <= 95 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class CylinderLinerStatus(str, Enum):
    NORMAL = "normal"
    THERMAL_SHOCK_WARNING = "thermal_shock_warning"
    HIGH_STRESS_ALARM = "high_stress_alarm"
    SCAVENGE_DRAIN_CLOGGED = "scavenge_drain_clogged"
    SCAVENGE_FIRE_TRIP = "scavenge_fire_trip"
    CRITICAL_OVERHEAT_SLOWDOWN = "critical_overheat_slowdown"


@dataclass(frozen=True)
class CylinderLinerTelemetry:
    liner_wall_temp_c: float
    temp_rate_c_per_min: float
    drain_orifice_dp_bar: float
    scavenge_drain_temp_c: float
    cylinder_lube_feed_active: bool = True


@dataclass(frozen=True)
class CylinderLinerAssessment:
    status: CylinderLinerStatus
    liner_safe: bool
    slowdown_trip_command: bool
    aux_blower_inhibit: bool
    increased_cylinder_lube_command: bool
    description: str


class CylinderLinerStressScavengeDrainEngine:
    """Evaluates cylinder liner low-cycle thermal stress and scavenge box safety."""

    @staticmethod
    def evaluate(t: CylinderLinerTelemetry) -> CylinderLinerAssessment:
        if t.scavenge_drain_temp_c >= 120.0:
            return CylinderLinerAssessment(
                CylinderLinerStatus.SCAVENGE_FIRE_TRIP, False, True, True, True,
                "Scavenge box fire detected: drain temp >= 120.0 C. Auto slowdown & blower trip.",
            )
        if t.liner_wall_temp_c >= 280.0:
            return CylinderLinerAssessment(
                CylinderLinerStatus.CRITICAL_OVERHEAT_SLOWDOWN, False, True, False, True,
                "Critical liner wall temp >= 280.0 C: automated engine slowdown tripped.",
            )
        if t.drain_orifice_dp_bar < 0.05:
            return CylinderLinerAssessment(
                CylinderLinerStatus.SCAVENGE_DRAIN_CLOGGED, True, False, False, False,
                "Scavenge drain orifice differential pressure < 0.05 bar: clogging alarm.",
            )
        if t.liner_wall_temp_c >= 260.0:
            return CylinderLinerAssessment(
                CylinderLinerStatus.HIGH_STRESS_ALARM, True, False, False, True,
                "Liner wall temperature >= 260.0 C: high thermal stress alarm.",
            )
        if abs(t.temp_rate_c_per_min) > 5.0:
            return CylinderLinerAssessment(
                CylinderLinerStatus.THERMAL_SHOCK_WARNING, True, False, False, True,
                "Liner thermal rate of change |dT/dt| > 5.0 C/min: thermal shock warning.",
            )
        return CylinderLinerAssessment(
            CylinderLinerStatus.NORMAL, True, False, False, False,
            "Cylinder liner thermal conditions and scavenge drain flow normal.",
        )
