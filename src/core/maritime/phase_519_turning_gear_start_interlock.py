"""Phase 519: Main Engine Turning Gear Engagement & Starting Air Safety Interlock.
Complies with SOLAS II-1 Reg 27 and IACS UR M10 Machinery Safety Standards.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class TurningGearInterlockState(str, Enum):
    READY_FOR_MAIN_START = "READY_FOR_MAIN_START"
    TURNING_GEAR_ENGAGED_START_BLOCKED = "TURNING_GEAR_ENGAGED_START_BLOCKED"
    INDICATOR_COCKS_OPEN_BLOWTHROUGH = "INDICATOR_COCKS_OPEN_BLOWTHROUGH"
    MAIN_AIR_STOP_VALVE_CLOSED_LOCK = "MAIN_AIR_STOP_VALVE_CLOSED_LOCK"


@dataclass(frozen=True)
class TurningGearTelemetry:
    turning_gear_disengaged: bool
    main_air_shutoff_valve_open: bool
    indicator_cocks_closed: bool = True


@dataclass(frozen=True)
class TurningGearAssessment:
    interlock_state: TurningGearInterlockState
    starting_air_permitted: bool
    bridge_start_ready_lamp: bool
    alarm_active: bool
    alarm_code: str


class TurningGearStartInterlockEngine:
    """Enforces SOLAS II-1 Reg 27 turning gear starting air lockout and indicator cock checks."""

    @classmethod
    def evaluate(cls, t: TurningGearTelemetry) -> TurningGearAssessment:
        if not t.turning_gear_disengaged:
            return TurningGearAssessment(
                TurningGearInterlockState.TURNING_GEAR_ENGAGED_START_BLOCKED,
                False,
                False,
                True,
                "SOLAS_TURNING_GEAR_ENGAGED_AIR_START_BLOCKED",
            )
        if not t.main_air_shutoff_valve_open:
            return TurningGearAssessment(
                TurningGearInterlockState.MAIN_AIR_STOP_VALVE_CLOSED_LOCK,
                False,
                False,
                True,
                "ME_STARTING_AIR_STOP_VALVE_ISOLATED",
            )
        if not t.indicator_cocks_closed:
            return TurningGearAssessment(
                TurningGearInterlockState.INDICATOR_COCKS_OPEN_BLOWTHROUGH,
                True,
                False,
                True,
                "ME_INDICATOR_COCKS_OPEN_SLOW_TURN_ONLY",
            )
        return TurningGearAssessment(
            TurningGearInterlockState.READY_FOR_MAIN_START,
            True,
            True,
            False,
            "NONE",
        )
