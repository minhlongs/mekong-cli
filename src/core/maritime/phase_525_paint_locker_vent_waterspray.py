"""Phase 525: Paint & Flammable Liquid Locker Explosion-Proof Vent & Water-Spray Interlock.
Complies with SOLAS II-2 Reg 10.6.3 and IEC 60092 Hazardous Area Electrical Interlocks.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class PaintLockerSafetyState(str, Enum):
    SAFE_VENTILATED_LOCKER = "SAFE_VENTILATED_LOCKER"
    VENTILATION_FAILURE_LIGHTING_INTERLOCK = "VENTILATION_FAILURE_LIGHTING_INTERLOCK"
    HIGH_LEL_IGNITION_ISOLATION_LOCKOUT = "HIGH_LEL_IGNITION_ISOLATION_LOCKOUT"
    FIRE_WATERSPRAY_DELUGE_RELEASE = "FIRE_WATERSPRAY_DELUGE_RELEASE"


@dataclass(frozen=True)
class PaintLockerTelemetry:
    air_changes_per_hour: float
    flammable_vapor_lel_pct: float
    ex_exhaust_fan_running: bool = True
    fire_detected_in_locker: bool = False


@dataclass(frozen=True)
class PaintLockerAssessment:
    safety_state: PaintLockerSafetyState
    waterspray_deluge_open: bool
    ex_lighting_energized: bool
    vent_damper_closed: bool
    alarm_active: bool
    alarm_code: str


class PaintLockerVentWatersprayEngine:
    """Enforces SOLAS II-2 Reg 10.6.3 paint locker deluge, >=6 ACH vent & LEL power cutoff."""

    MIN_ACH: float = 6.0
    MAX_SAFE_LEL_PCT: float = 20.0

    @classmethod
    def evaluate(cls, t: PaintLockerTelemetry) -> PaintLockerAssessment:
        if t.fire_detected_in_locker:
            return PaintLockerAssessment(
                PaintLockerSafetyState.FIRE_WATERSPRAY_DELUGE_RELEASE,
                True,
                False,
                True,
                True,
                "SOLAS_PAINT_LOCKER_FIRE_DELUGE_RELEASED",
            )
        if t.flammable_vapor_lel_pct >= cls.MAX_SAFE_LEL_PCT:
            return PaintLockerAssessment(
                PaintLockerSafetyState.HIGH_LEL_IGNITION_ISOLATION_LOCKOUT,
                False,
                False,
                False,
                True,
                "PAINT_LOCKER_VAPOR_LEL_CRITICAL_ISOLATION",
            )
        if not t.ex_exhaust_fan_running or t.air_changes_per_hour < cls.MIN_ACH:
            return PaintLockerAssessment(
                PaintLockerSafetyState.VENTILATION_FAILURE_LIGHTING_INTERLOCK,
                False,
                False,
                False,
                True,
                "PAINT_LOCKER_VENT_LOSS_EX_POWER_CUTOFF",
            )
        return PaintLockerAssessment(
            PaintLockerSafetyState.SAFE_VENTILATED_LOCKER,
            False,
            True,
            False,
            False,
            "NONE",
        )
