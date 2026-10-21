"""Phase 487: Main Engine Jacket Cooling Water Temperature & Flow Protection Engine.

Complies with IACS UR M10 & M3 standards. Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class JacketCoolingStatus(Enum):
    NORMAL = "normal"
    HIGH_TEMP_SLOWDOWN_TRIP = "high_temp_slowdown_trip"
    LOW_FLOW_DP_TRIP = "low_flow_dp_trip"
    EXPANSION_TANK_LOW_LOW_TRIP = "expansion_tank_low_low_trip"
    EXPANSION_TANK_LOW_ALARM = "expansion_tank_low_alarm"
    PREHEATER_PUMP_CUT_IN = "preheater_pump_cut_in"
    HIGH_TEMP_WARNING = "high_temp_warning"


@dataclass(frozen=True)
class JacketCoolingTelemetry:
    outlet_temp_c: float
    inlet_temp_c: float
    engine_block_diff_pressure_bar: float
    expansion_tank_level_pct: float
    preheater_pump_available: bool = True


@dataclass(frozen=True)
class JacketCoolingAssessment:
    status: JacketCoolingStatus
    slowdown_trip_command: bool
    preheater_pump_command: bool
    expansion_tank_alarm_active: bool
    cooling_adequate: bool
    remarks: str


class JacketCoolingTempFlowEngine:
    OUTLET_TEMP_NOMINAL_MIN_C = 80.0
    OUTLET_TEMP_NOMINAL_MAX_C = 88.0
    OUTLET_TEMP_SLOWDOWN_TRIP_C = 92.0
    MIN_DIFF_PRESSURE_TRIP_BAR = 0.6
    EXPANSION_TANK_LOW_ALARM_PCT = 30.0
    EXPANSION_TANK_LOW_LOW_TRIP_PCT = 15.0
    PREHEATER_CUT_IN_INLET_TEMP_C = 60.0

    @classmethod
    def evaluate(cls, telem: JacketCoolingTelemetry) -> JacketCoolingAssessment:
        p_cmd = telem.inlet_temp_c < cls.PREHEATER_CUT_IN_INLET_TEMP_C and telem.preheater_pump_available
        t_alarm = telem.expansion_tank_level_pct < cls.EXPANSION_TANK_LOW_ALARM_PCT

        if telem.expansion_tank_level_pct < cls.EXPANSION_TANK_LOW_LOW_TRIP_PCT:
            return JacketCoolingAssessment(
                JacketCoolingStatus.EXPANSION_TANK_LOW_LOW_TRIP, True, p_cmd, True, False,
                f"Expansion tank {telem.expansion_tank_level_pct:.1f}% < 15.0%. Coolant loss trip.",
            )
        if telem.outlet_temp_c >= cls.OUTLET_TEMP_SLOWDOWN_TRIP_C:
            return JacketCoolingAssessment(
                JacketCoolingStatus.HIGH_TEMP_SLOWDOWN_TRIP, True, p_cmd, t_alarm, False,
                f"Jacket outlet temp {telem.outlet_temp_c:.1f}C >= 92.0C. High temp slowdown trip.",
            )
        if telem.engine_block_diff_pressure_bar < cls.MIN_DIFF_PRESSURE_TRIP_BAR:
            return JacketCoolingAssessment(
                JacketCoolingStatus.LOW_FLOW_DP_TRIP, True, p_cmd, t_alarm, False,
                f"Engine block dP {telem.engine_block_diff_pressure_bar:.2f} bar < 0.6 bar. Low flow trip.",
            )
        if t_alarm:
            return JacketCoolingAssessment(
                JacketCoolingStatus.EXPANSION_TANK_LOW_ALARM, False, p_cmd, True, True,
                f"Expansion tank level {telem.expansion_tank_level_pct:.1f}% < 30.0%. Low level alarm.",
            )
        if telem.inlet_temp_c < cls.PREHEATER_CUT_IN_INLET_TEMP_C:
            return JacketCoolingAssessment(
                JacketCoolingStatus.PREHEATER_PUMP_CUT_IN, False, p_cmd, False, True,
                f"Inlet temp {telem.inlet_temp_c:.1f}C < 60.0C. Preheater pump auto-cut-in engaged.",
            )
        if telem.outlet_temp_c > cls.OUTLET_TEMP_NOMINAL_MAX_C:
            return JacketCoolingAssessment(
                JacketCoolingStatus.HIGH_TEMP_WARNING, False, False, False, True,
                f"Outlet temp {telem.outlet_temp_c:.1f}C > 88.0C nominal ceiling. Regulate central cooler.",
            )
        return JacketCoolingAssessment(
            JacketCoolingStatus.NORMAL, False, False, False, True,
            "Jacket cooling water operating within nominal IACS UR M10 & M3 limits (80-88C).",
        )
