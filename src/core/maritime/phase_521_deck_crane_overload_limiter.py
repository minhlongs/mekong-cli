"""Phase 521: Deck Crane Hydraulic Slewing & Hoisting Overload Moment Limiter.
Complies with SOLAS II-1 Reg 3-13, IACS UR A2, and ILO Convention 152.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class DeckCraneOperatingState(str, Enum):
    SAFE_CARGO_HANDLING = "SAFE_CARGO_HANDLING"
    SWL_APPROACHING_WARNING = "SWL_APPROACHING_WARNING"
    OVERLOAD_MOMENT_CUTOUT_TRIP = "OVERLOAD_MOMENT_CUTOUT_TRIP"
    SLACK_WIRE_DRUM_LOCKOUT = "SLACK_WIRE_DRUM_LOCKOUT"
    BOOM_ANGLE_LIMIT_STOP = "BOOM_ANGLE_LIMIT_STOP"


@dataclass(frozen=True)
class DeckCraneTelemetry:
    hook_load_pct_swl: float
    boom_angle_deg: float
    slack_wire_detected: bool = False


@dataclass(frozen=True)
class DeckCraneAssessment:
    operating_state: DeckCraneOperatingState
    hoist_up_permitted: bool
    hydraulic_brake_applied: bool
    alarm_active: bool
    alarm_code: str


class DeckCraneOverloadLimiterEngine:
    """Evaluates crane % SWL load moment, jib angle limits (15-80 deg), and slack wire."""

    WARN_SWL_PCT: float = 95.0
    CUTOUT_SWL_PCT: float = 105.0
    MIN_BOOM_DEG: float = 15.0
    MAX_BOOM_DEG: float = 80.0

    @classmethod
    def evaluate(cls, t: DeckCraneTelemetry) -> DeckCraneAssessment:
        if t.hook_load_pct_swl >= cls.CUTOUT_SWL_PCT:
            return DeckCraneAssessment(
                DeckCraneOperatingState.OVERLOAD_MOMENT_CUTOUT_TRIP,
                False,
                True,
                True,
                "SOLAS_CRANE_OVERLOAD_MOMENT_CUTOUT",
            )
        if t.slack_wire_detected:
            return DeckCraneAssessment(
                DeckCraneOperatingState.SLACK_WIRE_DRUM_LOCKOUT,
                False,
                True,
                True,
                "CRANE_HOIST_DRUM_SLACK_WIRE_TRIP",
            )
        if t.boom_angle_deg < cls.MIN_BOOM_DEG or t.boom_angle_deg > cls.MAX_BOOM_DEG:
            return DeckCraneAssessment(
                DeckCraneOperatingState.BOOM_ANGLE_LIMIT_STOP,
                False,
                True,
                True,
                "CRANE_LUFFING_BOOM_LIMIT_SWITCH_STOP",
            )
        if t.hook_load_pct_swl >= cls.WARN_SWL_PCT:
            return DeckCraneAssessment(
                DeckCraneOperatingState.SWL_APPROACHING_WARNING,
                True,
                False,
                True,
                "CRANE_SWL_95PCT_APPROACHING_WARNING",
            )
        return DeckCraneAssessment(
            DeckCraneOperatingState.SAFE_CARGO_HANDLING,
            True,
            False,
            False,
            "NONE",
        )
