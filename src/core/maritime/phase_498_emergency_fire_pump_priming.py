"""Phase 498: Emergency Fire Pump Sea Chest Suction & Priming Pressure Interlock.
SOLAS Reg II-2/10 & IACS UR F35 compliance. Strictly < 95 LOC.
"""
from dataclasses import dataclass
from enum import Enum

class FirePumpStatus(str, Enum):
    DELIVERING_PRESSURE = "DELIVERING_PRESSURE"
    PRIMING_IN_PROGRESS = "PRIMING_IN_PROGRESS"
    PRIMING_FAILURE_TRIP = "PRIMING_FAILURE_TRIP"

@dataclass(frozen=True)
class FirePumpTelemetry:
    suction_valve_open: bool
    suction_vacuum_bar: float
    discharge_pressure_bar: float
    priming_elapsed_sec: float
    pump_motor_running: bool = True

@dataclass(frozen=True)
class FirePumpAssessment:
    pump_status: FirePumpStatus
    standby_ejector_command: bool
    alarm_active: bool
    alarm_code: str
    fire_main_pressurized: bool

class EmergencyFirePumpPrimingEngine:
    MIN_FIRE_MAIN_BAR = 2.7
    PRIMING_PRESSURE_BAR = 1.5
    MAX_PRIMING_TIME_SEC = 30.0
    MIN_SUCTION_VACUUM_BAR = -0.40

    @classmethod
    def evaluate(cls, telem: FirePumpTelemetry) -> FirePumpAssessment:
        if not telem.suction_valve_open:
            return FirePumpAssessment(
                pump_status=FirePumpStatus.PRIMING_FAILURE_TRIP,
                standby_ejector_command=False,
                alarm_active=True,
                alarm_code="SEA_CHEST_SUCTION_VALVE_CLOSED_LOCKOUT",
                fire_main_pressurized=False,
            )
        if telem.discharge_pressure_bar >= cls.MIN_FIRE_MAIN_BAR:
            return FirePumpAssessment(
                pump_status=FirePumpStatus.DELIVERING_PRESSURE,
                standby_ejector_command=False,
                alarm_active=False,
                alarm_code="FIRE_MAIN_FULLY_PRESSURIZED",
                fire_main_pressurized=True,
            )
        if telem.discharge_pressure_bar >= cls.PRIMING_PRESSURE_BAR:
            return FirePumpAssessment(
                pump_status=FirePumpStatus.DELIVERING_PRESSURE,
                standby_ejector_command=False,
                alarm_active=False,
                alarm_code="PUMP_PRIMED_BUILDING_MAIN_PRESSURE",
                fire_main_pressurized=False,
            )
        if telem.priming_elapsed_sec >= cls.MAX_PRIMING_TIME_SEC:
            return FirePumpAssessment(
                pump_status=FirePumpStatus.PRIMING_FAILURE_TRIP,
                standby_ejector_command=True,
                alarm_active=True,
                alarm_code="PRIMING_TIMEOUT_EXCEEDED_STANDBY_EJECTOR_CUT_IN",
                fire_main_pressurized=False,
            )
        return FirePumpAssessment(
            pump_status=FirePumpStatus.PRIMING_IN_PROGRESS,
            standby_ejector_command=False,
            alarm_active=False,
            alarm_code="NORMAL_PRIMING_CYCLE_ACTIVE",
            fire_main_pressurized=False,
        )
