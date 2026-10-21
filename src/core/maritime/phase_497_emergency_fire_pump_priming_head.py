"""Phase 497: Emergency Fire Pump Priming Ejector & Discharge Head Protection.

Complies with SOLAS II-2 Reg 10.2.2.3.1.2 & IMO FSS Code Chapter 12.
Monitors sea suction vacuum priming time, delivery manifold head, and starter battery.
Strictly <= 95 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class EmergencyFirePumpStatus(str, Enum):
    NORMAL_DELIVERING = "normal_delivering"
    STANDBY_READY = "standby_ready"
    PRIMING_ACTIVE = "priming_active"
    PRIMING_TIMEOUT_ALARM = "priming_timeout_alarm"
    DISCHARGE_HEAD_LOW = "discharge_head_low"
    BATTERY_LOW_VOLTAGE = "battery_low_voltage"


@dataclass(frozen=True)
class EmergencyFirePumpTelemetry:
    pump_running: bool
    sea_suction_vacuum_bar: float  # -0.8 to -0.4 bar when primed
    discharge_manifold_head_bar: float  # >= 6.0 bar nominal delivering 2 jets
    priming_elapsed_seconds: float
    starter_battery_voltage_v: float
    suction_sea_chest_open: bool = True


@dataclass(frozen=True)
class EmergencyFirePumpAssessment:
    status: EmergencyFirePumpStatus
    pump_operational: bool
    jets_available: bool
    ejector_solenoid_command: bool
    alarm_active: bool
    description: str


class EmergencyFirePumpPrimingHeadEngine:
    """Evaluates emergency fire pump priming and discharge pressure compliance."""

    @staticmethod
    def evaluate(t: EmergencyFirePumpTelemetry) -> EmergencyFirePumpAssessment:
        if t.starter_battery_voltage_v < 21.6:
            return EmergencyFirePumpAssessment(
                EmergencyFirePumpStatus.BATTERY_LOW_VOLTAGE, t.pump_running,
                t.discharge_manifold_head_bar >= 6.0, False, True,
                "Dedicated diesel starter battery < 21.6 V (nominal 24.0 V): cranking capacity low.",
            )
        if not t.pump_running:
            return EmergencyFirePumpAssessment(
                EmergencyFirePumpStatus.STANDBY_READY, False, False, False, False,
                "Emergency fire pump in standby ready state.",
            )
        if t.sea_suction_vacuum_bar > -0.4:
            if t.priming_elapsed_seconds > 30.0:
                return EmergencyFirePumpAssessment(
                    EmergencyFirePumpStatus.PRIMING_TIMEOUT_ALARM, False, False, True, True,
                    "Priming vacuum timeout > 30.0 s: sea chest suction failed to prime.",
                )
            return EmergencyFirePumpAssessment(
                EmergencyFirePumpStatus.PRIMING_ACTIVE, True, False, True, False,
                "Vacuum priming ejector active (evacuating air from suction column).",
            )
        if t.discharge_manifold_head_bar < 6.0:
            return EmergencyFirePumpAssessment(
                EmergencyFirePumpStatus.DISCHARGE_HEAD_LOW, True, False, False, True,
                "Discharge head < 6.0 bar: insufficient pressure for statutory firefighting hydrants.",
            )
        return EmergencyFirePumpAssessment(
            EmergencyFirePumpStatus.NORMAL_DELIVERING, True, True, False, False,
            "Emergency fire pump primed and delivering nominal firefighting discharge pressure.",
        )
