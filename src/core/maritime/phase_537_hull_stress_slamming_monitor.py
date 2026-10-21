from dataclasses import dataclass
from enum import Enum


class HullStressSlammingState(str, Enum):
    NOMINAL_HULL_GIRDER_LOAD = "NOMINAL_HULL_GIRDER_LOAD"
    ELEVATED_BENDING_STRESS_WARNING = "ELEVATED_BENDING_STRESS_WARNING"
    BOW_SLAMMING_SPEED_REDUCTION_ADVICE = "BOW_SLAMMING_SPEED_REDUCTION_ADVICE"
    CRITICAL_HULL_GIRDER_OVERSTRESS_ALARM = "CRITICAL_HULL_GIRDER_OVERSTRESS_ALARM"


@dataclass(frozen=True)
class HullStressSlammingTelemetry:
    deck_bending_stress_mpa: float
    permissible_stress_limit_mpa: float
    bow_slamming_events_per_10min: int
    bow_vertical_accel_g: float


@dataclass(frozen=True)
class HullStressSlammingAssessment:
    state: HullStressSlammingState
    stress_utilization_pct: float
    speed_course_alteration_required: bool
    vdr_event_trigger_active: bool
    interlock_code: str


class HullStressSlammingMonitorEngine:
    """IMO MSC/Circ.646, IACS UR S11 & DNV HMON Hull Girder Stress & Slamming Supervision."""

    @classmethod
    def evaluate(cls, t: HullStressSlammingTelemetry) -> HullStressSlammingAssessment:
        limit = max(1.0, t.permissible_stress_limit_mpa)
        util_pct = round((t.deck_bending_stress_mpa / limit) * 100.0, 2)
        if util_pct >= 100.0:
            return HullStressSlammingAssessment(
                HullStressSlammingState.CRITICAL_HULL_GIRDER_OVERSTRESS_ALARM,
                util_pct,
                True,
                True,
                "IACS_UR_S11_HULL_GIRDER_STRESS_LIMIT_EXCEEDED",
            )
        if t.bow_slamming_events_per_10min >= 4 or t.bow_vertical_accel_g > 0.45:
            return HullStressSlammingAssessment(
                HullStressSlammingState.BOW_SLAMMING_SPEED_REDUCTION_ADVICE,
                util_pct,
                True,
                True,
                "MSC_CIRC_646_BOW_SLAMMING_IMPACT_ALARM",
            )
        if util_pct >= 85.0:
            return HullStressSlammingAssessment(
                HullStressSlammingState.ELEVATED_BENDING_STRESS_WARNING,
                util_pct,
                False,
                False,
                "HMON_DECK_STRESS_85PCT_PRE_WARNING",
            )
        return HullStressSlammingAssessment(
            HullStressSlammingState.NOMINAL_HULL_GIRDER_LOAD,
            util_pct,
            False,
            False,
            "NONE",
        )
