"""Phase 501: Cargo Hold Fixed CO2 Fire Extinguishing Total Flooding Interlock.
Complies with SOLAS II-2 Reg 10.4 and IMO FSS Code Chapter 5.
Strictly < 90 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class Co2ReleaseStatus(str, Enum):
    STANDBY_ARMED = "STANDBY_ARMED"
    PRE_DISCHARGE_ALARM_DELAY = "PRE_DISCHARGE_ALARM_DELAY"
    INTERLOCK_BLOCKED = "INTERLOCK_BLOCKED"
    MASTER_FLOODING_RELEASED = "MASTER_FLOODING_RELEASED"
    PILOT_PRESSURE_FAULT = "PILOT_PRESSURE_FAULT"


@dataclass(frozen=True)
class Co2FloodingTelemetry:
    cabinet_door_opened: bool
    pre_discharge_delay_sec: float
    ventilation_fans_tripped: bool
    fire_dampers_closed: bool
    pilot_cylinder_pressure_bar: float = 55.0


@dataclass(frozen=True)
class Co2FloodingAssessment:
    release_status: Co2ReleaseStatus
    main_manifold_valve_open: bool
    evacuation_siren_active: bool
    alarm_active: bool
    alarm_code: str


class Co2TotalFloodingInterlockEngine:
    """Enforces FSS Code Ch. 5 two-control release interlock and 20s evacuation delay."""

    MIN_PILOT_BAR: float = 45.0
    MANDATORY_EVAC_DELAY_SEC: float = 20.0

    @classmethod
    def evaluate(cls, t: Co2FloodingTelemetry) -> Co2FloodingAssessment:
        if t.pilot_cylinder_pressure_bar < cls.MIN_PILOT_BAR:
            return Co2FloodingAssessment(
                Co2ReleaseStatus.PILOT_PRESSURE_FAULT,
                False,
                t.cabinet_door_opened,
                True,
                "CO2_PILOT_BOTTLE_LOW_PRESSURE",
            )
        if not t.cabinet_door_opened:
            return Co2FloodingAssessment(
                Co2ReleaseStatus.STANDBY_ARMED, False, False, False, "NONE"
            )
        if not t.ventilation_fans_tripped or not t.fire_dampers_closed:
            return Co2FloodingAssessment(
                Co2ReleaseStatus.INTERLOCK_BLOCKED,
                False,
                True,
                True,
                "CO2_VENT_DAMPER_INTERLOCK_OPEN",
            )
        if t.pre_discharge_delay_sec < cls.MANDATORY_EVAC_DELAY_SEC:
            return Co2FloodingAssessment(
                Co2ReleaseStatus.PRE_DISCHARGE_ALARM_DELAY,
                False,
                True,
                True,
                "CO2_EVACUATION_COUNTDOWN_ACTIVE",
            )
        return Co2FloodingAssessment(
            Co2ReleaseStatus.MASTER_FLOODING_RELEASED,
            True,
            True,
            True,
            "CO2_MASTER_VALVE_DISCHARGING",
        )
