"""Phase 453: Marine Sewage Vacuum Collection System & Ejector Interlock.

Compliant with ISO 15749 & MARPOL Annex IV Regulation 11.
Monitors vacuum piping network pressure (-60 to -40 kPa), collection tank level,
seawater ejector motive pressure, and coastal distance discharge restrictions.
"""

from dataclasses import dataclass
from enum import Enum


class SewageVacuumStatus(str, Enum):
    NORMAL = "NORMAL"
    VACUUM_BUILDING = "VACUUM_BUILDING"
    LOSS_OF_VACUUM = "LOSS_OF_VACUUM"
    TANK_HIGH_LEVEL_LOCKOUT = "TANK_HIGH_LEVEL_LOCKOUT"
    SHORE_PROXIMITY_LOCK = "SHORE_PROXIMITY_LOCK"


@dataclass(frozen=True)
class SewageVacuumTelemetry:
    vacuum_pressure_kpa: float  # Negative, e.g. -50.0 kPa
    buffer_tank_level_pct: float
    ejector_motive_pressure_bar: float
    distance_to_shore_nm: float


@dataclass(frozen=True)
class SewageVacuumAssessment:
    status: SewageVacuumStatus
    vacuum_pump_call: bool
    discharge_valve_open: bool
    alarm_active: bool
    remarks: str


class SewageVacuumSystemEngine:
    VACUUM_STOP_KPA: float = -60.0
    VACUUM_START_KPA: float = -40.0
    VACUUM_LOSS_ALARM_KPA: float = -30.0
    MAX_BUFFER_TANK_LEVEL_PCT: float = 80.0
    MIN_MOTIVE_PRESSURE_BAR: float = 2.5
    MIN_SHORE_DISTANCE_NM: float = 12.0

    @classmethod
    def evaluate(cls, telemetry: SewageVacuumTelemetry) -> SewageVacuumAssessment:
        if telemetry.buffer_tank_level_pct >= cls.MAX_BUFFER_TANK_LEVEL_PCT:
            return SewageVacuumAssessment(
                status=SewageVacuumStatus.TANK_HIGH_LEVEL_LOCKOUT,
                vacuum_pump_call=False,
                discharge_valve_open=False,
                alarm_active=True,
                remarks="Vacuum collection tank high level >= 80%: Lockout toilet interface",
            )

        if telemetry.vacuum_pressure_kpa > cls.VACUUM_LOSS_ALARM_KPA:
            return SewageVacuumAssessment(
                status=SewageVacuumStatus.LOSS_OF_VACUUM,
                vacuum_pump_call=True,
                discharge_valve_open=False,
                alarm_active=True,
                remarks="Vacuum loss alarm: Pressure above -30 kPa, check piping seal integrity",
            )

        pump_call = telemetry.vacuum_pressure_kpa >= cls.VACUUM_START_KPA
        shore_lock = telemetry.distance_to_shore_nm < cls.MIN_SHORE_DISTANCE_NM

        if shore_lock:
            status = SewageVacuumStatus.SHORE_PROXIMITY_LOCK
            discharge = False
            remarks = "MARPOL Annex IV coastal proximity: Overboard discharge prohibited < 12 nm"
        else:
            status = SewageVacuumStatus.VACUUM_BUILDING if pump_call else SewageVacuumStatus.NORMAL
            discharge = telemetry.ejector_motive_pressure_bar >= cls.MIN_MOTIVE_PRESSURE_BAR
            remarks = "Sewage vacuum collection operational; overboard transfer permitted"

        return SewageVacuumAssessment(
            status=status,
            vacuum_pump_call=pump_call,
            discharge_valve_open=discharge,
            alarm_active=False,
            remarks=remarks,
        )
