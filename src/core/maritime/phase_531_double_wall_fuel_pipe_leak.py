from dataclasses import dataclass
from enum import Enum


class DoubleWallFuelPipeState(str, Enum):
    NORMAL_JACKETED_INTEGRITY = "NORMAL_JACKETED_INTEGRITY"
    ANNULAR_WEEPING_PRE_ALARM = "ANNULAR_WEEPING_PRE_ALARM"
    QCV_PILOT_PRESSURE_LOW_FAULT = "QCV_PILOT_PRESSURE_LOW_FAULT"
    HOT_SURFACE_SHIELD_OVERHEAT_ALARM = "HOT_SURFACE_SHIELD_OVERHEAT_ALARM"
    HIGH_PRESSURE_FUEL_RUPTURE_ALARM = "HIGH_PRESSURE_FUEL_RUPTURE_ALARM"


@dataclass(frozen=True)
class DoubleWallFuelPipeTelemetry:
    annular_space_pressure_bar: float
    leak_drain_tank_level_pct: float
    exposed_surface_max_temp_c: float
    qcv_pneumatic_pilot_bar: float


@dataclass(frozen=True)
class DoubleWallFuelPipeAssessment:
    state: DoubleWallFuelPipeState
    engine_slowdown_required: bool
    drain_tank_pumpout_active: bool
    qcv_readiness_ok: bool
    fire_hazard_alarm: bool
    interlock_code: str


class DoubleWallFuelPipeLeakEngine:
    """SOLAS II-2 Reg 4.2.2.5.2 & IACS UR M10/M75 Jacketed HP Fuel Pipe Supervision."""

    @classmethod
    def evaluate(cls, t: DoubleWallFuelPipeTelemetry) -> DoubleWallFuelPipeAssessment:
        qcv_ok = t.qcv_pneumatic_pilot_bar >= 4.5
        if t.annular_space_pressure_bar >= 1.5 or t.leak_drain_tank_level_pct >= 80.0:
            return DoubleWallFuelPipeAssessment(
                DoubleWallFuelPipeState.HIGH_PRESSURE_FUEL_RUPTURE_ALARM,
                True,
                True,
                qcv_ok,
                True,
                "SOLAS_II2_4_2_HP_FUEL_JACKET_RUPTURE_TRIP",
            )
        if t.exposed_surface_max_temp_c > 220.0:
            return DoubleWallFuelPipeAssessment(
                DoubleWallFuelPipeState.HOT_SURFACE_SHIELD_OVERHEAT_ALARM,
                True,
                t.leak_drain_tank_level_pct >= 35.0,
                qcv_ok,
                True,
                "SOLAS_II2_4_2_2_6_HOT_SURFACE_OVER_220C",
            )
        if not qcv_ok:
            return DoubleWallFuelPipeAssessment(
                DoubleWallFuelPipeState.QCV_PILOT_PRESSURE_LOW_FAULT,
                False,
                t.leak_drain_tank_level_pct >= 35.0,
                False,
                True,
                "SOLAS_II2_4_2_QCV_PNEUMATIC_RESERVE_LOW",
            )
        if t.annular_space_pressure_bar >= 0.4 or t.leak_drain_tank_level_pct >= 35.0:
            return DoubleWallFuelPipeAssessment(
                DoubleWallFuelPipeState.ANNULAR_WEEPING_PRE_ALARM,
                False,
                True,
                True,
                True,
                "UR_M75_HP_FUEL_DRAIN_TANK_WEEPING_WARN",
            )
        return DoubleWallFuelPipeAssessment(
            DoubleWallFuelPipeState.NORMAL_JACKETED_INTEGRITY,
            False,
            False,
            True,
            False,
            "NONE",
        )
