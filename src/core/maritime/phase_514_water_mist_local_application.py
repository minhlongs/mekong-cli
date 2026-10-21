"""Phase 514: Engine Room Fixed Local Application Water-Mist Fire Fighting System.
Complies with SOLAS II-2 Reg 10.5.6 and IMO MSC/Circ.1387 Guidelines.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class WaterMistSystemState(str, Enum):
    STANDBY_MONITORING = "STANDBY_MONITORING"
    SINGLE_SENSOR_PRE_ALARM = "SINGLE_SENSOR_PRE_ALARM"
    LOCAL_SECTION_MIST_DISCHARGING = "LOCAL_SECTION_MIST_DISCHARGING"
    LOW_MIST_PRESSURE_FAULT = "LOW_MIST_PRESSURE_FAULT"


@dataclass(frozen=True)
class WaterMistTelemetry:
    flame_detector_active: bool
    smoke_heat_detector_active: bool
    manual_local_release: bool = False
    pump_discharge_bar: float = 95.0


@dataclass(frozen=True)
class WaterMistAssessment:
    system_state: WaterMistSystemState
    section_valve_open: bool
    high_pressure_pump_running: bool
    alarm_active: bool
    alarm_code: str


class WaterMistLocalApplicationEngine:
    """Enforces dual-detector coincidence logic and >= 80 bar high-pressure water mist."""

    MIN_MIST_BAR: float = 80.0

    @classmethod
    def evaluate(cls, t: WaterMistTelemetry) -> WaterMistAssessment:
        coincidence = t.flame_detector_active and t.smoke_heat_detector_active
        release_triggered = coincidence or t.manual_local_release

        if release_triggered:
            if t.pump_discharge_bar < cls.MIN_MIST_BAR:
                return WaterMistAssessment(
                    WaterMistSystemState.LOW_MIST_PRESSURE_FAULT,
                    True,
                    True,
                    True,
                    "WATER_MIST_PUMP_LOW_DISCHARGE_PRESSURE",
                )
            return WaterMistAssessment(
                WaterMistSystemState.LOCAL_SECTION_MIST_DISCHARGING,
                True,
                True,
                True,
                "SOLAS_LOCAL_WATER_MIST_ACTIVE",
            )
        if t.flame_detector_active or t.smoke_heat_detector_active:
            return WaterMistAssessment(
                WaterMistSystemState.SINGLE_SENSOR_PRE_ALARM,
                False,
                False,
                True,
                "WATER_MIST_SINGLE_DETECTOR_PRE_ALARM",
            )
        return WaterMistAssessment(
            WaterMistSystemState.STANDBY_MONITORING,
            False,
            False,
            False,
            "NONE",
        )
