from dataclasses import dataclass
from enum import Enum


class CommonRailBoosterState(str, Enum):
    NOMINAL_COMMON_RAIL_PRESSURE = "NOMINAL_COMMON_RAIL_PRESSURE"
    LOW_RAIL_PRESSURE_BOOSTER_CUTIN = "LOW_RAIL_PRESSURE_BOOSTER_CUTIN"
    FLOW_LIMITING_VALVE_CUTOUT_TRIP = "FLOW_LIMITING_VALVE_CUTOUT_TRIP"
    RAIL_OVERPRESSURE_EPRV_LIFT_SLOWDOWN = "RAIL_OVERPRESSURE_EPRV_LIFT_SLOWDOWN"


@dataclass(frozen=True)
class CommonRailBoosterTelemetry:
    fuel_rail_pressure_bar: float
    servo_oil_pressure_bar: float
    eprv_lifted: bool = False
    flv_seized_open: bool = False


@dataclass(frozen=True)
class CommonRailBoosterAssessment:
    state: CommonRailBoosterState
    engine_slowdown_cmd: bool
    fuel_flow_limiting_valve_tripped: bool
    standby_hp_pump_cut_in: bool
    interlock_code: str


class CommonRailFuelBoosterEngine:
    """IACS UR M10 & SOLAS II-2 Reg 4.2.2 Common-Rail HP Fuel Booster & EPRV Supervision."""

    @classmethod
    def evaluate(cls, t: CommonRailBoosterTelemetry) -> CommonRailBoosterAssessment:
        if t.fuel_rail_pressure_bar >= 1050.0 or t.eprv_lifted:
            return CommonRailBoosterAssessment(
                CommonRailBoosterState.RAIL_OVERPRESSURE_EPRV_LIFT_SLOWDOWN,
                True,
                True,
                False,
                "UR_M10_COMMON_RAIL_OVERPRESSURE_EPRV_SLOWDOWN",
            )
        if t.flv_seized_open:
            return CommonRailBoosterAssessment(
                CommonRailBoosterState.FLOW_LIMITING_VALVE_CUTOUT_TRIP,
                True,
                True,
                False,
                "UR_M10_FLV_CONTINUOUS_INJECTION_CUTOUT_TRIP",
            )
        if t.fuel_rail_pressure_bar < 550.0 or t.servo_oil_pressure_bar < 180.0:
            return CommonRailBoosterAssessment(
                CommonRailBoosterState.LOW_RAIL_PRESSURE_BOOSTER_CUTIN,
                False,
                False,
                True,
                "UR_M10_COMMON_RAIL_LOW_PRESSURE_STANDBY_CUTIN",
            )
        return CommonRailBoosterAssessment(
            CommonRailBoosterState.NOMINAL_COMMON_RAIL_PRESSURE,
            False,
            False,
            False,
            "NONE",
        )
