from dataclasses import dataclass
from enum import Enum


class FinStabilizerHousingState(str, Enum):
    FIN_ACTIVE_ROLL_DAMPING_NOMINAL = "FIN_ACTIVE_ROLL_DAMPING_NOMINAL"
    HIGH_HYDRODYNAMIC_LOAD_ANGLE_LIMIT = "HIGH_HYDRODYNAMIC_LOAD_ANGLE_LIMIT"
    LOCKING_PIN_PROXIMITY_INTERLOCK_FAULT = "LOCKING_PIN_PROXIMITY_INTERLOCK_FAULT"
    LOW_SPEED_OR_HYDRAULIC_AUTO_RETRACT_TRIP = "LOW_SPEED_OR_HYDRAULIC_AUTO_RETRACT_TRIP"


@dataclass(frozen=True)
class FinStabilizerHousingTelemetry:
    vessel_speed_knots: float
    hydraulic_pressure_bar: float
    hydrodynamic_load_pct: float = 55.0
    locking_pin_fully_disengaged: bool = True


@dataclass(frozen=True)
class FinStabilizerHousingAssessment:
    state: FinStabilizerHousingState
    auto_center_zero_angle_cmd: bool
    retract_fin_to_housing_cmd: bool
    engage_hull_locking_pin_cmd: bool
    interlock_code: str


class FinStabilizerHousingEngine:
    """IACS UR M42 Fin Stabilizer Zero-Speed Auto-Retraction & Hull Locking Pin Interlock."""

    @classmethod
    def evaluate(cls, t: FinStabilizerHousingTelemetry) -> FinStabilizerHousingAssessment:
        if t.vessel_speed_knots < 4.0 or t.hydraulic_pressure_bar < 90.0:
            return FinStabilizerHousingAssessment(
                FinStabilizerHousingState.LOW_SPEED_OR_HYDRAULIC_AUTO_RETRACT_TRIP,
                True,
                True,
                True,
                "UR_M42_LOW_SPEED_OR_HYD_LOSS_AUTO_CENTER_RETRACT",
            )
        if not t.locking_pin_fully_disengaged:
            return FinStabilizerHousingAssessment(
                FinStabilizerHousingState.LOCKING_PIN_PROXIMITY_INTERLOCK_FAULT,
                True,
                False,
                False,
                "UR_M42_HULL_LOCKING_PIN_PROXIMITY_SERVO_INHIBIT",
            )
        if t.hydrodynamic_load_pct >= 85.0:
            return FinStabilizerHousingAssessment(
                FinStabilizerHousingState.HIGH_HYDRODYNAMIC_LOAD_ANGLE_LIMIT,
                False,
                False,
                False,
                "UR_M42_FIN_CAVITATION_TORQUE_MAX_ANGLE_DERATE",
            )
        return FinStabilizerHousingAssessment(
            FinStabilizerHousingState.FIN_ACTIVE_ROLL_DAMPING_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
