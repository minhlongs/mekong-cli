"""Phase 494: Bow Thruster Tunnel Hydraulic Pitch & Overload Power Management.

Compliant with DNV Rules for Ships & IACS UR M65.
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class BowThrusterStatus(str, Enum):
    NORMAL = "normal"
    MOTOR_OVERLOAD_PITCH_REDUCTION = "motor_overload_pitch_reduction"
    HYDRAULIC_LOW_PRESSURE_TRIP = "hydraulic_low_pressure_trip"
    HEADER_TANK_LOW_LEVEL = "header_tank_low_level"
    OIL_HIGH_TEMP_COOLING_BOOST = "oil_high_temp_cooling_boost"


@dataclass(frozen=True)
class BowThrusterTelemetry:
    motor_load_fla_pct: float
    servo_oil_pressure_bar: float
    header_tank_level_pct: float
    hydraulic_oil_temp_c: float
    cooling_boost_valve_open: bool = False


@dataclass(frozen=True)
class BowThrusterAssessment:
    status: BowThrusterStatus
    pitch_reduction_command: bool
    emergency_freeze_pitch: bool
    cooling_boost_command: bool
    thruster_available: bool
    remarks: str


class BowThrusterPitchPowerEngine:
    """IACS UR M65 / DNV Bow Thruster Hydraulic & Drive Safety Engine."""

    MAX_MOTOR_LOAD_FLA_PCT = 105.0
    MIN_SERVO_PRESSURE_BAR = 25.0
    MIN_HEADER_TANK_PCT = 40.0
    MAX_HYDRAULIC_TEMP_C = 70.0

    @classmethod
    def evaluate(cls, telem: BowThrusterTelemetry) -> BowThrusterAssessment:
        if telem.servo_oil_pressure_bar < cls.MIN_SERVO_PRESSURE_BAR:
            return BowThrusterAssessment(
                BowThrusterStatus.HYDRAULIC_LOW_PRESSURE_TRIP,
                False, True, False, False,
                f"Servo P {telem.servo_oil_pressure_bar:.1f} bar < {cls.MIN_SERVO_PRESSURE_BAR} bar; pitch frozen",
            )
        if telem.motor_load_fla_pct > cls.MAX_MOTOR_LOAD_FLA_PCT:
            return BowThrusterAssessment(
                BowThrusterStatus.MOTOR_OVERLOAD_PITCH_REDUCTION,
                True, False, telem.hydraulic_oil_temp_c > cls.MAX_HYDRAULIC_TEMP_C, True,
                f"Motor load {telem.motor_load_fla_pct:.1f}% > {cls.MAX_MOTOR_LOAD_FLA_PCT}% FLA; reducing pitch",
            )
        if telem.header_tank_level_pct < cls.MIN_HEADER_TANK_PCT:
            return BowThrusterAssessment(
                BowThrusterStatus.HEADER_TANK_LOW_LEVEL,
                False, False, False, True,
                f"Header tank {telem.header_tank_level_pct:.1f}% < {cls.MIN_HEADER_TANK_PCT}% warning limit",
            )
        if telem.hydraulic_oil_temp_c > cls.MAX_HYDRAULIC_TEMP_C:
            return BowThrusterAssessment(
                BowThrusterStatus.OIL_HIGH_TEMP_COOLING_BOOST,
                False, False, True, True,
                f"Oil temp {telem.hydraulic_oil_temp_c:.1f} °C > {cls.MAX_HYDRAULIC_TEMP_C} °C; cooling boost",
            )
        return BowThrusterAssessment(
            BowThrusterStatus.NORMAL,
            False, False, False, True,
            f"Bow thruster nominal. Load: {telem.motor_load_fla_pct:.1f}%, Servo P: {telem.servo_oil_pressure_bar:.1f} bar",
        )
