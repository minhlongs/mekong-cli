"""Phase 508: Engine Room Bilge Flood Alarm & Emergency Direct Suction Interlock.
Complies with SOLAS II-1 Reg 35-1 and Reg 48 Machinery Space Flooding Protection.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class BilgeFloodState(str, Enum):
    DRY_WELL_STANDBY = "DRY_WELL_STANDBY"
    NORMAL_BILGE_PUMPING = "NORMAL_BILGE_PUMPING"
    HIGH_LEVEL_FLOODING_ALARM = "HIGH_LEVEL_FLOODING_ALARM"
    EMERGENCY_DIRECT_SUCTION_ACTIVE = "EMERGENCY_DIRECT_SUCTION_ACTIVE"


@dataclass(frozen=True)
class EmergencyBilgeTelemetry:
    well_water_level_mm: float
    main_sw_pump_running: bool = True
    independent_high_sensor_tripped: bool = False


@dataclass(frozen=True)
class EmergencyBilgeAssessment:
    flood_state: BilgeFloodState
    bilge_pump_start_cmd: bool
    emergency_direct_suction_open: bool
    alarm_active: bool
    alarm_code: str


class EmergencyBilgeDirectSuctionEngine:
    """Evaluates machinery space bilge flooding and main SW pump emergency injection."""

    PUMP_START_MM: float = 150.0
    HIGH_FLOOD_MM: float = 350.0
    CATASTROPHIC_FLOOD_MM: float = 600.0

    @classmethod
    def evaluate(cls, t: EmergencyBilgeTelemetry) -> EmergencyBilgeAssessment:
        if t.well_water_level_mm >= cls.CATASTROPHIC_FLOOD_MM and t.main_sw_pump_running:
            return EmergencyBilgeAssessment(
                BilgeFloodState.EMERGENCY_DIRECT_SUCTION_ACTIVE,
                True,
                True,
                True,
                "SOLAS_EMERGENCY_BILGE_INJECTION_OPENED",
            )
        if t.well_water_level_mm >= cls.HIGH_FLOOD_MM or t.independent_high_sensor_tripped:
            return EmergencyBilgeAssessment(
                BilgeFloodState.HIGH_LEVEL_FLOODING_ALARM,
                True,
                False,
                True,
                "SOLAS_REG48_ENGINE_ROOM_FLOODING_ALARM",
            )
        if t.well_water_level_mm >= cls.PUMP_START_MM:
            return EmergencyBilgeAssessment(
                BilgeFloodState.NORMAL_BILGE_PUMPING,
                True,
                False,
                False,
                "NONE",
            )
        return EmergencyBilgeAssessment(
            BilgeFloodState.DRY_WELL_STANDBY,
            False,
            False,
            False,
            "NONE",
        )
