"""Phase 518: Marine Accommodation Elevator Governor & Heavy-Weather Roll Lockout.
Complies with SOLAS II-1 and ISO 8383 / EN 81-41 Shipboard Lift Safety Rules.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class MarineElevatorMode(str, Enum):
    NORMAL_PASSENGER_SERVICE = "NORMAL_PASSENGER_SERVICE"
    HEAVY_WEATHER_ROLL_HOMING_LOCK = "HEAVY_WEATHER_ROLL_HOMING_LOCK"
    FIRE_SMOKE_EMBARKATION_RECALL = "FIRE_SMOKE_EMBARKATION_RECALL"
    GOVERNOR_OVERSPEED_SAFETY_CLAMP = "GOVERNOR_OVERSPEED_SAFETY_CLAMP"


@dataclass(frozen=True)
class MarineElevatorTelemetry:
    vessel_roll_angle_deg: float
    car_speed_pct_rated: float = 100.0
    hoistway_smoke_detected: bool = False


@dataclass(frozen=True)
class MarineElevatorAssessment:
    elevator_mode: MarineElevatorMode
    safety_gear_wedges_engaged: bool
    parked_at_embarkation_deck: bool
    alarm_active: bool
    alarm_code: str


class MarineElevatorRollGovernorEngine:
    """Evaluates heavy-weather roll lockout (>= 15 deg), smoke recall, and >= 115% governor trip."""

    MAX_ROLL_DEG: float = 15.0
    GOVERNOR_TRIP_SPEED_PCT: float = 115.0

    @classmethod
    def evaluate(cls, t: MarineElevatorTelemetry) -> MarineElevatorAssessment:
        if t.car_speed_pct_rated >= cls.GOVERNOR_TRIP_SPEED_PCT:
            return MarineElevatorAssessment(
                MarineElevatorMode.GOVERNOR_OVERSPEED_SAFETY_CLAMP,
                True,
                False,
                True,
                "ELEVATOR_GOVERNOR_MECHANICAL_SAFETY_TRIP",
            )
        if t.hoistway_smoke_detected:
            return MarineElevatorAssessment(
                MarineElevatorMode.FIRE_SMOKE_EMBARKATION_RECALL,
                False,
                True,
                True,
                "ELEVATOR_HOISTWAY_SMOKE_RECALL_ACTIVE",
            )
        if abs(t.vessel_roll_angle_deg) >= cls.MAX_ROLL_DEG:
            return MarineElevatorAssessment(
                MarineElevatorMode.HEAVY_WEATHER_ROLL_HOMING_LOCK,
                False,
                True,
                True,
                "ELEVATOR_HEAVY_SEAS_INCLINATION_PARK",
            )
        return MarineElevatorAssessment(
            MarineElevatorMode.NORMAL_PASSENGER_SERVICE,
            False,
            False,
            False,
            "NONE",
        )
