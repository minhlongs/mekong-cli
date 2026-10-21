"""Phase 477: Main Engine Scavenge Air Manifold Relief & Fire Snuffing Engine.

Complies with:
- SOLAS II-2 Reg. 4.2.5.2 & IACS UR M9 (Scavenge Fire & Explosion Protection):
  - Scavenge air manifold temperature: normal <= 55.0 C, fire warning >= 80.0 C, fire alarm/trip >= 120.0 C.
  - Manifold overpressure relief: mechanical relief valve lifts at P >= 1.5 bar gauge.
  - Fixed fire extinguishing: Steam/CO2 snuffing injection permissive activates at fire alarm.
  - Auto-action: Fuel pump rack cutoff, auxiliary scavenging blower emergency stop.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class ScavengeFireStatus(str, Enum):
    NORMAL = "NORMAL"
    SCAVENGE_AIR_TEMP_WARNING = "SCAVENGE_AIR_TEMP_WARNING"
    SCAVENGE_FIRE_ALARM_SNUFFING_TRIP = "SCAVENGE_FIRE_ALARM_SNUFFING_TRIP"
    MANIFOLD_EXPLOSION_RELIEF_OPEN = "MANIFOLD_EXPLOSION_RELIEF_OPEN"


@dataclass(frozen=True)
class ScavengeFireTelemetry:
    manifold_temp_c: float
    manifold_pressure_bar: float
    differential_cyl_temp_c: float
    aux_blower_running: bool
    engine_fuel_rack_pct: float


@dataclass(frozen=True)
class ScavengeFireAssessment:
    status: ScavengeFireStatus
    fuel_rack_cutoff_command: bool
    aux_blower_trip_command: bool
    snuffing_medium_permissive: bool
    explosion_relief_open: bool
    remarks: str


class ScavengeFireSafetyEngine:
    TEMP_WARNING_C: float = 80.0
    FIRE_ALARM_TRIP_C: float = 120.0
    MAX_MANIFOLD_PRESSURE_BAR: float = 1.5
    MAX_CYLINDER_DIFF_TEMP_C: float = 35.0

    @classmethod
    def evaluate(cls, telemetry: ScavengeFireTelemetry) -> ScavengeFireAssessment:
        if telemetry.manifold_pressure_bar >= cls.MAX_MANIFOLD_PRESSURE_BAR:
            return ScavengeFireAssessment(
                status=ScavengeFireStatus.MANIFOLD_EXPLOSION_RELIEF_OPEN,
                fuel_rack_cutoff_command=True,
                aux_blower_trip_command=True,
                snuffing_medium_permissive=True,
                explosion_relief_open=True,
                remarks=f"CRITICAL: Scavenge manifold overpressure {telemetry.manifold_pressure_bar} bar >= {cls.MAX_MANIFOLD_PRESSURE_BAR} bar. Relief vented.",
            )

        if telemetry.manifold_temp_c >= cls.FIRE_ALARM_TRIP_C:
            return ScavengeFireAssessment(
                status=ScavengeFireStatus.SCAVENGE_FIRE_ALARM_SNUFFING_TRIP,
                fuel_rack_cutoff_command=True,
                aux_blower_trip_command=True,
                snuffing_medium_permissive=True,
                explosion_relief_open=False,
                remarks=f"SOLAS FIRE TRIP: Scavenge temp {telemetry.manifold_temp_c}C >= {cls.FIRE_ALARM_TRIP_C}C. Fuel cut, blowers off, CO2/steam snuffing armed.",
            )

        if telemetry.manifold_temp_c >= cls.TEMP_WARNING_C or telemetry.differential_cyl_temp_c >= cls.MAX_CYLINDER_DIFF_TEMP_C:
            return ScavengeFireAssessment(
                status=ScavengeFireStatus.SCAVENGE_AIR_TEMP_WARNING,
                fuel_rack_cutoff_command=False,
                aux_blower_trip_command=False,
                snuffing_medium_permissive=False,
                explosion_relief_open=False,
                remarks=f"WARNING: Elevated scavenge temp {telemetry.manifold_temp_c}C or cylinder diff {telemetry.differential_cyl_temp_c}C. Soot accumulation check.",
            )

        return ScavengeFireAssessment(
            status=ScavengeFireStatus.NORMAL,
            fuel_rack_cutoff_command=False,
            aux_blower_trip_command=False,
            snuffing_medium_permissive=False,
            explosion_relief_open=False,
            remarks="Scavenge air manifold temperatures and pressures nominal.",
        )
