"""Phase 526: Accommodation Ladder & Gangway Winch Inclination, SWL & Stowage Safety.
Complies with SOLAS II-1 Reg 3-9, IMO MSC.1/Circ.1331, and ISO 5488.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class AccommodationLadderState(str, Enum):
    SAFE_EMBARKATION_ACCESS = "SAFE_EMBARKATION_ACCESS"
    STEEP_INCLINATION_55DEG_LOCKOUT = "STEEP_INCLINATION_55DEG_LOCKOUT"
    OVERLOAD_BRAKE_HOLD_TRIP = "OVERLOAD_BRAKE_HOLD_TRIP"
    UNSTOWED_AT_SEA_DEPARTURE_ALARM = "UNSTOWED_AT_SEA_DEPARTURE_ALARM"


@dataclass(frozen=True)
class AccommodationLadderTelemetry:
    ladder_angle_deg: float
    live_load_kg: float
    rated_swl_kg: float = 750.0
    vessel_underway_speed_kn: float = 0.0
    ladder_stowed_and_latched: bool = False


@dataclass(frozen=True)
class AccommodationLadderAssessment:
    ladder_state: AccommodationLadderState
    winch_lowering_permitted: bool
    mechanical_pawl_engaged: bool
    alarm_active: bool
    alarm_code: str


class AccommodationLadderWinchSafetyEngine:
    """Enforces SOLAS II-1 Reg 3-9 & ISO 5488 <=55 deg inclination, SWL & underway stowage."""

    MAX_INCLINATION_DEG: float = 55.0
    UNDERWAY_SPEED_THRESHOLD_KN: float = 0.5

    @classmethod
    def evaluate(cls, t: AccommodationLadderTelemetry) -> AccommodationLadderAssessment:
        if t.vessel_underway_speed_kn > cls.UNDERWAY_SPEED_THRESHOLD_KN and not t.ladder_stowed_and_latched:
            return AccommodationLadderAssessment(
                AccommodationLadderState.UNSTOWED_AT_SEA_DEPARTURE_ALARM,
                False,
                True,
                True,
                "SOLAS_GANGWAY_UNSTOWED_WHILE_UNDERWAY",
            )
        if t.live_load_kg > t.rated_swl_kg:
            return AccommodationLadderAssessment(
                AccommodationLadderState.OVERLOAD_BRAKE_HOLD_TRIP,
                False,
                True,
                True,
                "ACCOMMODATION_LADDER_SWL_OVERLOAD_TRIP",
            )
        if t.ladder_angle_deg > cls.MAX_INCLINATION_DEG:
            return AccommodationLadderAssessment(
                AccommodationLadderState.STEEP_INCLINATION_55DEG_LOCKOUT,
                False,
                True,
                True,
                "SOLAS_REG3_9_LADDER_ANGLE_EXCEEDS_55DEG",
            )
        return AccommodationLadderAssessment(
            AccommodationLadderState.SAFE_EMBARKATION_ACCESS,
            True,
            False,
            False,
            "NONE",
        )
