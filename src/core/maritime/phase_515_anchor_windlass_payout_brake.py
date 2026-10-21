"""Phase 515: Anchor Windlass Chain Payout Velocity, Bitter End & Wash Interlock.
Complies with IACS UR A1 and SOLAS II-1 Anchoring Equipment Safety Standards.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class WindlassOperatingState(str, Enum):
    CONTROLLED_ANCHOR_HANDLING = "CONTROLLED_ANCHOR_HANDLING"
    RUNAWAY_CHAIN_EMERGENCY_BRAKE = "RUNAWAY_CHAIN_EMERGENCY_BRAKE"
    BITTER_END_LOW_SHACKLE_ALARM = "BITTER_END_LOW_SHACKLE_ALARM"
    HAWSEPIPE_WASH_PRESSURE_LOW = "HAWSEPIPE_WASH_PRESSURE_LOW"


@dataclass(frozen=True)
class AnchorWindlassTelemetry:
    payout_speed_m_s: float
    remaining_shackles_in_locker: float
    heaving_in_active: bool = False
    hawsepipe_wash_bar: float = 2.8


@dataclass(frozen=True)
class AnchorWindlassAssessment:
    operating_state: WindlassOperatingState
    band_brake_auto_clamp: bool
    bitter_end_quick_release_armed: bool
    alarm_active: bool
    alarm_code: str


class AnchorWindlassPayoutBrakeEngine:
    """Evaluates chain payout speed (<= 7.5 m/s), remaining shackles, and hawsepipe wash."""

    MAX_PAYOUT_SPEED_M_S: float = 7.5
    MIN_SHACKLES_RESERVE: float = 1.5
    MIN_WASH_BAR: float = 2.0

    @classmethod
    def evaluate(cls, t: AnchorWindlassTelemetry) -> AnchorWindlassAssessment:
        if t.payout_speed_m_s > cls.MAX_PAYOUT_SPEED_M_S:
            return AnchorWindlassAssessment(
                WindlassOperatingState.RUNAWAY_CHAIN_EMERGENCY_BRAKE,
                True,
                True,
                True,
                "WINDLASS_RUNAWAY_CABLE_BAND_BRAKE_TRIP",
            )
        if t.remaining_shackles_in_locker <= cls.MIN_SHACKLES_RESERVE:
            return AnchorWindlassAssessment(
                WindlassOperatingState.BITTER_END_LOW_SHACKLE_ALARM,
                True,
                True,
                True,
                "WINDLASS_BITTER_END_LIMIT_APPROACHING",
            )
        if t.heaving_in_active and t.hawsepipe_wash_bar < cls.MIN_WASH_BAR:
            return AnchorWindlassAssessment(
                WindlassOperatingState.HAWSEPIPE_WASH_PRESSURE_LOW,
                False,
                False,
                True,
                "WINDLASS_HAWSEPIPE_FLUSH_LOW_PRESSURE",
            )
        return AnchorWindlassAssessment(
            WindlassOperatingState.CONTROLLED_ANCHOR_HANDLING,
            False,
            False,
            False,
            "NONE",
        )
