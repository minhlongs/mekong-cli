from dataclasses import dataclass
from enum import Enum


class LocalWaterMistFwlaState(str, Enum):
    FWLA_SYSTEM_ARMED_STANDBY = "FWLA_SYSTEM_ARMED_STANDBY"
    HEADER_SUPPLY_LOW_PRESSURE_FAULT = "HEADER_SUPPLY_LOW_PRESSURE_FAULT"
    SINGLE_DETECTOR_PRE_ALARM_STANDBY = "SINGLE_DETECTOR_PRE_ALARM_STANDBY"
    COINCIDENCE_HOTSPOT_MIST_DISCHARGE_TRIP = "COINCIDENCE_HOTSPOT_MIST_DISCHARGE_TRIP"


@dataclass(frozen=True)
class LocalWaterMistFwlaTelemetry:
    flame_detector_active: bool
    smoke_detector_active: bool
    header_pressure_bar: float = 6.5
    manual_release_pulled: bool = False


@dataclass(frozen=True)
class LocalWaterMistFwlaAssessment:
    state: LocalWaterMistFwlaState
    section_deluge_valve_open_cmd: bool
    fwla_pump_start_cmd: bool
    local_fuel_booster_trip_cmd: bool
    interlock_code: str


class EngineRoomLocalWaterMistFwlaEngine:
    """SOLAS II-2 Reg 10.5.6 & MSC/Circ.913 Fixed Water-Based Local Application (FWLA) Interlock."""

    @classmethod
    def evaluate(cls, t: LocalWaterMistFwlaTelemetry) -> LocalWaterMistFwlaAssessment:
        if (t.flame_detector_active and t.smoke_detector_active) or t.manual_release_pulled:
            return LocalWaterMistFwlaAssessment(
                LocalWaterMistFwlaState.COINCIDENCE_HOTSPOT_MIST_DISCHARGE_TRIP,
                True,
                True,
                True,
                "SOLAS_II2_R10_5_6_FWLA_COINCIDENCE_DISCHARGE_ACTIVE",
            )
        if t.flame_detector_active or t.smoke_detector_active:
            return LocalWaterMistFwlaAssessment(
                LocalWaterMistFwlaState.SINGLE_DETECTOR_PRE_ALARM_STANDBY,
                False,
                False,
                False,
                "MSC_CIRC913_SINGLE_ZONE_DETECTOR_PRE_ALARM",
            )
        if t.header_pressure_bar < 4.0:
            return LocalWaterMistFwlaAssessment(
                LocalWaterMistFwlaState.HEADER_SUPPLY_LOW_PRESSURE_FAULT,
                False,
                True,
                False,
                "SOLAS_II2_FWLA_HEADER_LOW_PRESSURE_JOCKEY_START",
            )
        return LocalWaterMistFwlaAssessment(
            LocalWaterMistFwlaState.FWLA_SYSTEM_ARMED_STANDBY,
            False,
            False,
            False,
            "NONE",
        )
