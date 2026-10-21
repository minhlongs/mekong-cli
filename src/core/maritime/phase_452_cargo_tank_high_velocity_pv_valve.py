"""Phase 452: Cargo Tank High-Velocity P/V Valve & Deflagration Arrestor.

Compliant with IMO MSC/Circ.677 & ISO 15364.
Ensures overpressure (+14 kPa) and vacuum (-3.5 kPa) venting with high-velocity
efflux gas ejection (>= 30 m/s) and magnetic check-lift verification.
"""

from dataclasses import dataclass
from enum import Enum


class PvValveStatus(str, Enum):
    NORMAL_CLOSED = "NORMAL_CLOSED"
    ACTIVE_VENTING = "ACTIVE_VENTING"
    ACTIVE_VACUUM_RELIEF = "ACTIVE_VACUUM_RELIEF"
    VALVE_STUCK_ALARM = "VALVE_STUCK_ALARM"
    DEFLAGRATION_SCREEN_FOULED = "DEFLAGRATION_SCREEN_FOULED"


@dataclass(frozen=True)
class PvValveTelemetry:
    tank_pressure_kpa: float
    efflux_velocity_m_s: float
    flame_screen_mesh_clear_pct: float
    magnetic_lift_verified: bool
    disc_lift_percentage: float


@dataclass(frozen=True)
class PvValveAssessment:
    status: PvValveStatus
    efflux_compliant: bool
    atmospheric_venting_open: bool
    vacuum_relief_open: bool
    safety_alarm: bool
    remarks: str


class CargoPvValveEngine:
    OVERPRESSURE_OPEN_KPA: float = 14.0
    VACUUM_OPEN_KPA: float = -3.5
    MIN_EFFLUX_VELOCITY_M_S: float = 30.0
    MIN_FLAME_SCREEN_CLEAR_PCT: float = 80.0

    @classmethod
    def evaluate(cls, telemetry: PvValveTelemetry) -> PvValveAssessment:
        if not telemetry.magnetic_lift_verified:
            return PvValveAssessment(
                status=PvValveStatus.VALVE_STUCK_ALARM,
                efflux_compliant=False,
                atmospheric_venting_open=False,
                vacuum_relief_open=False,
                safety_alarm=True,
                remarks="Magnetic check-lift failed: Disc sticking or crystallization detected",
            )

        if telemetry.flame_screen_mesh_clear_pct < cls.MIN_FLAME_SCREEN_CLEAR_PCT:
            return PvValveAssessment(
                status=PvValveStatus.DEFLAGRATION_SCREEN_FOULED,
                efflux_compliant=False,
                atmospheric_venting_open=False,
                vacuum_relief_open=False,
                safety_alarm=True,
                remarks="Deflagration flame screen aperture fouled below 80% effective area",
            )

        if telemetry.tank_pressure_kpa >= cls.OVERPRESSURE_OPEN_KPA:
            efflux_ok = telemetry.efflux_velocity_m_s >= cls.MIN_EFFLUX_VELOCITY_M_S
            return PvValveAssessment(
                status=PvValveStatus.ACTIVE_VENTING,
                efflux_compliant=efflux_ok,
                atmospheric_venting_open=True,
                vacuum_relief_open=False,
                safety_alarm=not efflux_ok,
                remarks="High-velocity overpressure discharge active" if efflux_ok else "Sub-critical efflux velocity",
            )

        if telemetry.tank_pressure_kpa <= cls.VACUUM_OPEN_KPA:
            return PvValveAssessment(
                status=PvValveStatus.ACTIVE_VACUUM_RELIEF,
                efflux_compliant=True,
                atmospheric_venting_open=False,
                vacuum_relief_open=True,
                safety_alarm=False,
                remarks="Vacuum relief disc lifted: Ingesting ambient air to protect tank structure",
            )

        return PvValveAssessment(
            status=PvValveStatus.NORMAL_CLOSED,
            efflux_compliant=True,
            atmospheric_venting_open=False,
            vacuum_relief_open=False,
            safety_alarm=False,
            remarks="Cargo tank pressure balanced within safe envelope",
        )
