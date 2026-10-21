from dataclasses import dataclass
from enum import Enum


class ExhaustValveActuatorState(str, Enum):
    OPTIMAL_ACTUATOR_OPERATION = "OPTIMAL_ACTUATOR_OPERATION"
    ACTUATOR_OIL_LEAK_SEAL_WARN = "ACTUATOR_OIL_LEAK_SEAL_WARN"
    AIR_SPRING_LOW_PRESSURE_WARN = "AIR_SPRING_LOW_PRESSURE_WARN"
    SPINDLE_ROTATION_SEIZURE_ALARM = "SPINDLE_ROTATION_SEIZURE_ALARM"
    AIR_SPRING_COLLAPSE_CYLINDER_CUTOUT = "AIR_SPRING_COLLAPSE_CYLINDER_CUTOUT"


@dataclass(frozen=True)
class ExhaustValveActuatorTelemetry:
    air_spring_pressure_bar: float
    spindle_rotation_rpm: float
    hydraulic_drain_leak_l_h: float
    engine_load_pct: float = 75.0


@dataclass(frozen=True)
class ExhaustValveActuatorAssessment:
    state: ExhaustValveActuatorState
    cylinder_fuel_cutout_cmd: bool
    engine_slowdown_cmd: bool
    standby_air_supply_open: bool
    interlock_code: str


class ExhaustValveActuatorSupervisionEngine:
    """IACS UR M10 & MAN B&W/WinGD Exhaust Valve Air-Spring & Spindle Supervision."""

    @classmethod
    def evaluate(cls, t: ExhaustValveActuatorTelemetry) -> ExhaustValveActuatorAssessment:
        if t.air_spring_pressure_bar < 5.0:
            return ExhaustValveActuatorAssessment(
                ExhaustValveActuatorState.AIR_SPRING_COLLAPSE_CYLINDER_CUTOUT,
                True,
                True,
                True,
                "UR_M10_EXH_VALVE_AIR_SPRING_COLLAPSE_CUTOUT",
            )
        if t.engine_load_pct >= 25.0 and t.spindle_rotation_rpm < 4.0:
            return ExhaustValveActuatorAssessment(
                ExhaustValveActuatorState.SPINDLE_ROTATION_SEIZURE_ALARM,
                False,
                True,
                False,
                "MAN_EXH_VALVE_SPINDLE_STOP_HOT_CORROSION_ALARM",
            )
        if t.air_spring_pressure_bar < 6.0:
            return ExhaustValveActuatorAssessment(
                ExhaustValveActuatorState.AIR_SPRING_LOW_PRESSURE_WARN,
                False,
                False,
                True,
                "UR_M10_EXH_VALVE_AIR_SPRING_LOW_WARN",
            )
        if t.hydraulic_drain_leak_l_h > 1.5:
            return ExhaustValveActuatorAssessment(
                ExhaustValveActuatorState.ACTUATOR_OIL_LEAK_SEAL_WARN,
                False,
                False,
                False,
                "EXH_ACTUATOR_HYDRAULIC_SEAL_WEEPING_WARN",
            )
        return ExhaustValveActuatorAssessment(
            ExhaustValveActuatorState.OPTIMAL_ACTUATOR_OPERATION,
            False,
            False,
            False,
            "NONE",
        )
