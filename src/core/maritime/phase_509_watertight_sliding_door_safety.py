"""Phase 509: Hydraulic Watertight Sliding Door Closure & Pinch Safety.
Complies with SOLAS II-1 Reg 13 Power-Operated Watertight Sliding Doors.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class WatertightDoorStatus(str, Enum):
    CLOSED_AND_DOG_LOCKED = "CLOSED_AND_DOG_LOCKED"
    CLOSING_WITH_AUDIBLE_ALARM = "CLOSING_WITH_AUDIBLE_ALARM"
    OBSTRUCTION_REOPEN_PAUSE = "OBSTRUCTION_REOPEN_PAUSE"
    ACCUMULATOR_LOW_PRESSURE_FAULT = "ACCUMULATOR_LOW_PRESSURE_FAULT"
    CLOSING_SPEED_OUT_OF_SPEC = "CLOSING_SPEED_OUT_OF_SPEC"


@dataclass(frozen=True)
class WatertightDoorTelemetry:
    bridge_master_close_cmd: bool
    door_fully_closed: bool
    accumulator_pressure_bar: float
    closing_duration_sec: float = 28.0
    pinch_strip_obstructed: bool = False


@dataclass(frozen=True)
class WatertightDoorAssessment:
    door_status: WatertightDoorStatus
    solas_3_closures_ready: bool
    audible_beacon_active: bool
    alarm_active: bool
    alarm_code: str


class WatertightSlidingDoorSafetyEngine:
    """Evaluates SOLAS II-1 Reg 13 hydraulic accumulator reserve and 20-40s closure speed."""

    MIN_ACCUMULATOR_BAR: float = 145.0
    MIN_CLOSE_SEC: float = 20.0
    MAX_CLOSE_SEC: float = 40.0

    @classmethod
    def evaluate(cls, t: WatertightDoorTelemetry) -> WatertightDoorAssessment:
        acc_ok = t.accumulator_pressure_bar >= cls.MIN_ACCUMULATOR_BAR
        if not acc_ok:
            return WatertightDoorAssessment(
                WatertightDoorStatus.ACCUMULATOR_LOW_PRESSURE_FAULT,
                False,
                t.bridge_master_close_cmd,
                True,
                "WTD_HYDRAULIC_ACCUMULATOR_LOW_PRESSURE",
            )
        if t.pinch_strip_obstructed and not t.door_fully_closed:
            return WatertightDoorAssessment(
                WatertightDoorStatus.OBSTRUCTION_REOPEN_PAUSE,
                True,
                True,
                True,
                "WTD_PERSONNEL_PINCH_STRIP_ACTIVATED",
            )
        if t.closing_duration_sec < cls.MIN_CLOSE_SEC or t.closing_duration_sec > cls.MAX_CLOSE_SEC:
            return WatertightDoorAssessment(
                WatertightDoorStatus.CLOSING_SPEED_OUT_OF_SPEC,
                True,
                True,
                True,
                "WTD_SOLAS_CLOSURE_TIME_VIOLATION",
            )
        if t.door_fully_closed:
            return WatertightDoorAssessment(
                WatertightDoorStatus.CLOSED_AND_DOG_LOCKED, True, False, False, "NONE"
            )
        return WatertightDoorAssessment(
            WatertightDoorStatus.CLOSING_WITH_AUDIBLE_ALARM,
            True,
            t.bridge_master_close_cmd,
            False,
            "NONE",
        )
