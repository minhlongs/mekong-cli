from dataclasses import dataclass
from enum import Enum


class BessThermalRunawayState(str, Enum):
    NOMINAL_BESS_ENCLOSURE = "NOMINAL_BESS_ENCLOSURE"
    COOLING_LOOP_LOW_FLOW_DERATE_WARN = "COOLING_LOOP_LOW_FLOW_DERATE_WARN"
    ELECTROLYTE_OFFGAS_PRE_ALARM_ISOLATE = "ELECTROLYTE_OFFGAS_PRE_ALARM_ISOLATE"
    THERMAL_RUNAWAY_DELUGE_DC_ISOLATION_TRIP = "THERMAL_RUNAWAY_DELUGE_DC_ISOLATION_TRIP"


@dataclass(frozen=True)
class BessThermalRunawayTelemetry:
    max_cell_temp_c: float
    offgas_h2_lel_pct: float
    offgas_co_ppm: float
    coolant_flow_l_min: float = 28.0


@dataclass(frozen=True)
class BessThermalRunawayAssessment:
    state: BessThermalRunawayState
    dc_breaker_trip_cmd: bool
    water_mist_deluge_release_cmd: bool
    emergency_exhaust_boost_cmd: bool
    interlock_code: str


class BessThermalRunawayOffgasEngine:
    """IACS UR E26/E27 & DNV Battery Power BESS Thermal Runaway Off-Gas & Deluge Interlock."""

    @classmethod
    def evaluate(cls, t: BessThermalRunawayTelemetry) -> BessThermalRunawayAssessment:
        if t.max_cell_temp_c >= 65.0 or t.offgas_h2_lel_pct >= 25.0:
            return BessThermalRunawayAssessment(
                BessThermalRunawayState.THERMAL_RUNAWAY_DELUGE_DC_ISOLATION_TRIP,
                True,
                True,
                True,
                "UR_E26_BESS_THERMAL_RUNAWAY_DELUGE_TRIP",
            )
        if t.offgas_h2_lel_pct >= 10.0 or t.offgas_co_ppm >= 50.0 or t.max_cell_temp_c >= 55.0:
            return BessThermalRunawayAssessment(
                BessThermalRunawayState.ELECTROLYTE_OFFGAS_PRE_ALARM_ISOLATE,
                True,
                False,
                True,
                "UR_E26_BESS_ELECTROLYTE_VENT_ISOLATE_ALARM",
            )
        if t.coolant_flow_l_min < 15.0:
            return BessThermalRunawayAssessment(
                BessThermalRunawayState.COOLING_LOOP_LOW_FLOW_DERATE_WARN,
                False,
                False,
                False,
                "DNV_BESS_COOLANT_LOW_FLOW_DERATE_WARN",
            )
        return BessThermalRunawayAssessment(
            BessThermalRunawayState.NOMINAL_BESS_ENCLOSURE,
            False,
            False,
            False,
            "NONE",
        )
