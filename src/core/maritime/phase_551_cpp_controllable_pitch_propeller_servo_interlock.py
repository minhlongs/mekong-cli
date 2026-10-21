from dataclasses import dataclass
from enum import Enum


class CppPropellerServoState(str, Enum):
    CPP_PITCH_CONTROL_NOMINAL = "CPP_PITCH_CONTROL_NOMINAL"
    OD_BOX_OIL_HIGH_TEMP_WARN = "OD_BOX_OIL_HIGH_TEMP_WARN"
    SERVO_FEEDBACK_OR_STANDBY_PUMP_PRE_ALARM = "SERVO_FEEDBACK_OR_STANDBY_PUMP_PRE_ALARM"
    HYDRAULIC_PRESSURE_LOSS_PITCH_FREEZE_TRIP = "HYDRAULIC_PRESSURE_LOSS_PITCH_FREEZE_TRIP"


@dataclass(frozen=True)
class CppPropellerServoTelemetry:
    servo_oil_pressure_bar: float
    od_box_oil_temp_c: float
    pitch_feedback_error_pct: float = 0.3


@dataclass(frozen=True)
class CppPropellerServoAssessment:
    state: CppPropellerServoState
    hydraulic_pitch_lock_valve_engage: bool
    standby_servo_pump_start_cmd: bool
    cooler_bypass_close_max_cooling: bool
    interlock_code: str


class CppPropellerServoEngine:
    """IACS UR M43 & SOLAS II-1 Reg 28 Controllable Pitch Propeller (CPP) Servo Interlock."""

    @classmethod
    def evaluate(cls, t: CppPropellerServoTelemetry) -> CppPropellerServoAssessment:
        if t.servo_oil_pressure_bar < 25.0 or t.od_box_oil_temp_c >= 80.0:
            return CppPropellerServoAssessment(
                CppPropellerServoState.HYDRAULIC_PRESSURE_LOSS_PITCH_FREEZE_TRIP,
                True,
                True,
                True,
                "UR_M43_CPP_HUB_SERVO_LOSS_OR_OVERHEAT_PITCH_LOCK_TRIP",
            )
        if t.pitch_feedback_error_pct >= 3.5 or t.servo_oil_pressure_bar < 32.0:
            return CppPropellerServoAssessment(
                CppPropellerServoState.SERVO_FEEDBACK_OR_STANDBY_PUMP_PRE_ALARM,
                False,
                True,
                False,
                "SOLAS_II1_R28_CPP_FEEDBACK_DEV_OR_STANDBY_PUMP_START",
            )
        if t.od_box_oil_temp_c >= 68.0:
            return CppPropellerServoAssessment(
                CppPropellerServoState.OD_BOX_OIL_HIGH_TEMP_WARN,
                False,
                False,
                True,
                "UR_M43_CPP_OD_BOX_HIGH_OIL_TEMP_WARN",
            )
        return CppPropellerServoAssessment(
            CppPropellerServoState.CPP_PITCH_CONTROL_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
