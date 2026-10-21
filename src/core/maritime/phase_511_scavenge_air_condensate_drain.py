"""Phase 511: Main Engine Scavenge Air Condensate Drain & Cooler Carryover Control.
Complies with IACS UR M10 and MAN B&W / WinGD Liner Lubrication Protection Rules.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class ScavengeCondensateState(str, Enum):
    OPTIMAL_DRY_SCAVENGE = "OPTIMAL_DRY_SCAVENGE"
    UNDERCOOLING_LINER_WASH_RISK = "UNDERCOOLING_LINER_WASH_RISK"
    DRAIN_TRAP_BLOCKED_HIGH_LEVEL = "DRAIN_TRAP_BLOCKED_HIGH_LEVEL"
    MIST_CATCHER_CARRYOVER_ALARM = "MIST_CATCHER_CARRYOVER_ALARM"


@dataclass(frozen=True)
class ScavengeCondensateTelemetry:
    scavenge_air_temp_c: float
    compressed_dewpoint_c: float
    drain_pot_level_pct: float
    mist_catcher_dp_kpa: float = 1.2


@dataclass(frozen=True)
class ScavengeCondensateAssessment:
    condensate_state: ScavengeCondensateState
    bypass_drain_valve_open: bool
    cylinder_oil_feed_boost: bool
    alarm_active: bool
    alarm_code: str


class ScavengeAirCondensateDrainEngine:
    """Evaluates scavenge air dewpoint margin, drain pot float level, and mist catcher dP."""

    MAX_DRAIN_POT_PCT: float = 80.0
    MAX_MIST_DP_KPA: float = 3.0
    MIN_DEWPOINT_MARGIN_C: float = 2.0

    @classmethod
    def evaluate(cls, t: ScavengeCondensateTelemetry) -> ScavengeCondensateAssessment:
        if t.drain_pot_level_pct >= cls.MAX_DRAIN_POT_PCT:
            return ScavengeCondensateAssessment(
                ScavengeCondensateState.DRAIN_TRAP_BLOCKED_HIGH_LEVEL,
                True,
                True,
                True,
                "SCAV_CONDENSATE_TRAP_CHOKED_BYPASS_OPEN",
            )
        if t.mist_catcher_dp_kpa >= cls.MAX_MIST_DP_KPA:
            return ScavengeCondensateAssessment(
                ScavengeCondensateState.MIST_CATCHER_CARRYOVER_ALARM,
                True,
                True,
                True,
                "SCAV_WATER_MIST_CATCHER_FOULED",
            )
        if t.scavenge_air_temp_c < t.compressed_dewpoint_c + cls.MIN_DEWPOINT_MARGIN_C:
            return ScavengeCondensateAssessment(
                ScavengeCondensateState.UNDERCOOLING_LINER_WASH_RISK,
                False,
                True,
                True,
                "SCAV_AIR_BELOW_DEWPOINT_LINER_SCUFFING_RISK",
            )
        return ScavengeCondensateAssessment(
            ScavengeCondensateState.OPTIMAL_DRY_SCAVENGE,
            False,
            False,
            False,
            "NONE",
        )
