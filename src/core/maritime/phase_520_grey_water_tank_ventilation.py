"""Phase 520: Grey Water Collecting Tank High-Level & H2S Ventilation Safety.
Complies with MARPOL Annex IV and ISO 15749 Marine Drainage Systems.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class GreyWaterSystemState(str, Enum):
    NORMAL_COLLECTION = "NORMAL_COLLECTION"
    STANDBY_PUMP_AUTO_ASSIST = "STANDBY_PUMP_AUTO_ASSIST"
    HIGH_LEVEL_OVERFLOW_ALARM = "HIGH_LEVEL_OVERFLOW_ALARM"
    H2S_TOXIC_GAS_VENT_LOCKDOWN = "H2S_TOXIC_GAS_VENT_LOCKDOWN"
    ILLEGAL_PORT_OVERBOARD_BLOCK = "ILLEGAL_PORT_OVERBOARD_BLOCK"


@dataclass(frozen=True)
class GreyWaterTelemetry:
    tank_level_pct: float
    h2s_concentration_ppm: float
    in_zero_discharge_port_zone: bool = False
    overboard_valve_open: bool = False


@dataclass(frozen=True)
class GreyWaterAssessment:
    system_state: GreyWaterSystemState
    standby_pump_running: bool
    emergency_vent_fan_boost: bool
    alarm_active: bool
    alarm_code: str


class GreyWaterTankVentilationEngine:
    """Evaluates grey water tank level, H2S gas ppm, and zero-discharge port interlock."""

    STANDBY_CUTIN_PCT: float = 80.0
    OVERFLOW_ALARM_PCT: float = 92.0
    MAX_H2S_PPM: float = 10.0

    @classmethod
    def evaluate(cls, t: GreyWaterTelemetry) -> GreyWaterAssessment:
        if t.h2s_concentration_ppm >= cls.MAX_H2S_PPM:
            return GreyWaterAssessment(
                GreyWaterSystemState.H2S_TOXIC_GAS_VENT_LOCKDOWN,
                True,
                True,
                True,
                "GREYWATER_H2S_TOXIC_GAS_ALARM",
            )
        if t.in_zero_discharge_port_zone and t.overboard_valve_open:
            return GreyWaterAssessment(
                GreyWaterSystemState.ILLEGAL_PORT_OVERBOARD_BLOCK,
                False,
                False,
                True,
                "MARPOL_PORT_OVERBOARD_VALVE_VIOLATION",
            )
        if t.tank_level_pct >= cls.OVERFLOW_ALARM_PCT:
            return GreyWaterAssessment(
                GreyWaterSystemState.HIGH_LEVEL_OVERFLOW_ALARM,
                True,
                True,
                True,
                "GREYWATER_TANK_HIGH_HIGH_OVERFLOW",
            )
        if t.tank_level_pct >= cls.STANDBY_CUTIN_PCT:
            return GreyWaterAssessment(
                GreyWaterSystemState.STANDBY_PUMP_AUTO_ASSIST,
                True,
                False,
                False,
                "NONE",
            )
        return GreyWaterAssessment(
            GreyWaterSystemState.NORMAL_COLLECTION,
            False,
            False,
            False,
            "NONE",
        )
