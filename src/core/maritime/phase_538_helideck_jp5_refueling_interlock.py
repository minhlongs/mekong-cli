from dataclasses import dataclass
from enum import Enum


class HelideckRefuelingState(str, Enum):
    JP5_DISPENSING_AUTHORIZED = "JP5_DISPENSING_AUTHORIZED"
    DEADMAN_HANDLE_RELEASED_HOLD = "DEADMAN_HANDLE_RELEASED_HOLD"
    FILTER_COALESCER_DP_HIGH_LOCKOUT = "FILTER_COALESCER_DP_HIGH_LOCKOUT"
    STATIC_BONDING_CONTINUITY_FAULT = "STATIC_BONDING_CONTINUITY_FAULT"
    FREE_WATER_CONTAMINATION_SHUTOFF = "FREE_WATER_CONTAMINATION_SHUTOFF"


@dataclass(frozen=True)
class HelideckRefuelingTelemetry:
    static_bonding_ohms: float
    free_water_ppm: float
    filter_separator_dp_bar: float
    deadman_trigger_held: bool


@dataclass(frozen=True)
class HelideckRefuelingAssessment:
    state: HelideckRefuelingState
    fuel_solenoid_valve_open: bool
    dispensing_pump_running: bool
    contamination_trip_active: bool
    interlock_code: str


class HelideckJp5RefuelingInterlockEngine:
    """SOLAS II-2 Reg 18.7 & UK CAA CAP 437 Helideck JP-5 Refueling Supervision."""

    @classmethod
    def evaluate(cls, t: HelideckRefuelingTelemetry) -> HelideckRefuelingAssessment:
        if t.free_water_ppm >= 15.0:
            return HelideckRefuelingAssessment(
                HelideckRefuelingState.FREE_WATER_CONTAMINATION_SHUTOFF,
                False,
                False,
                True,
                "CAP437_JP5_FREE_WATER_OVER_15PPM_SHUTOFF",
            )
        if t.static_bonding_ohms >= 10.0:
            return HelideckRefuelingAssessment(
                HelideckRefuelingState.STATIC_BONDING_CONTINUITY_FAULT,
                False,
                False,
                False,
                "SOLAS_II2_18_7_STATIC_EARTH_CONTINUITY_OPEN",
            )
        if t.filter_separator_dp_bar > 1.0:
            return HelideckRefuelingAssessment(
                HelideckRefuelingState.FILTER_COALESCER_DP_HIGH_LOCKOUT,
                False,
                False,
                True,
                "CAP437_FILTER_COALESCER_ELEMENT_BLOCKED",
            )
        if not t.deadman_trigger_held:
            return HelideckRefuelingAssessment(
                HelideckRefuelingState.DEADMAN_HANDLE_RELEASED_HOLD,
                False,
                True,
                False,
                "CAP437_DEADMAN_NOZZLE_STANDBY_HOLD",
            )
        return HelideckRefuelingAssessment(
            HelideckRefuelingState.JP5_DISPENSING_AUTHORIZED,
            True,
            True,
            False,
            "NONE",
        )
