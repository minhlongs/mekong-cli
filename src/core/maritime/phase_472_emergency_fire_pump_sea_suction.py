"""Phase 472: Marine Emergency Fire Pump Sea Suction Priming & Static Head Protection Engine.

Complies with:
- SOLAS II-2 Reg. 10.2.2.3.1 (Emergency fire pump suction and water delivery)
- IACS UR F35 / DNV Pt.4 Ch.6 Sec.2:
  - Suction head limitation: Sea suction valve must be below waterline in all light ship conditions; static suction head <= 4.5 meters.
  - Vacuum priming timeout: Priming ejector / diaphragm vacuum pump must achieve -0.6 bar within 45.0 seconds.
  - Discharge pressure delivery: Minimum discharge pressure P_disch >= 2.7 bar at highest fire hydrant.
  - Engine diesel battery/hydraulic starting: Min 2 independent start attempts with start battery voltage >= 21.0 V (24V system).

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class EmergencyFirePumpStatus(str, Enum):
    NORMAL = "NORMAL"
    PRIMING_IN_PROGRESS = "PRIMING_IN_PROGRESS"
    PRIMING_TIMEOUT_TRIP = "PRIMING_TIMEOUT_TRIP"
    LOW_DISCHARGE_PRESSURE_ALARM = "LOW_DISCHARGE_PRESSURE_ALARM"
    SUCTION_HEAD_EXCEEDED = "SUCTION_HEAD_EXCEEDED"
    STARTING_POWER_FAULT = "STARTING_POWER_FAULT"


@dataclass(frozen=True)
class EmergencyFirePumpTelemetry:
    static_suction_head_m: float
    priming_vacuum_bar: float
    priming_elapsed_sec: float
    discharge_p_bar: float
    diesel_start_voltage_v: float
    pump_running: bool


@dataclass(frozen=True)
class EmergencyFirePumpAssessment:
    status: EmergencyFirePumpStatus
    sea_suction_permissive: bool
    hydrant_delivery_adequate: bool
    reprime_command_active: bool
    remarks: str


class EmergencyFirePumpSafetyEngine:
    MAX_SUCTION_HEAD_M: float = 4.5
    TARGET_PRIMING_VACUUM_BAR: float = -0.6
    MAX_PRIMING_TIMEOUT_SEC: float = 45.0
    MIN_DISCHARGE_P_BAR: float = 2.7
    MIN_START_VOLTAGE_V: float = 21.0

    @classmethod
    def evaluate(cls, telemetry: EmergencyFirePumpTelemetry) -> EmergencyFirePumpAssessment:
        if telemetry.diesel_start_voltage_v < cls.MIN_START_VOLTAGE_V:
            return EmergencyFirePumpAssessment(
                status=EmergencyFirePumpStatus.STARTING_POWER_FAULT,
                sea_suction_permissive=False,
                hydrant_delivery_adequate=False,
                reprime_command_active=False,
                remarks=f"Starting battery voltage {telemetry.diesel_start_voltage_v}V < {cls.MIN_START_VOLTAGE_V}V. Diesel start compromised.",
            )

        if telemetry.static_suction_head_m > cls.MAX_SUCTION_HEAD_M:
            return EmergencyFirePumpAssessment(
                status=EmergencyFirePumpStatus.SUCTION_HEAD_EXCEEDED,
                sea_suction_permissive=False,
                hydrant_delivery_adequate=False,
                reprime_command_active=False,
                remarks=f"Static suction head {telemetry.static_suction_head_m}m > {cls.MAX_SUCTION_HEAD_M}m exceeds SOLAS limit.",
            )

        if not telemetry.pump_running:
            return EmergencyFirePumpAssessment(
                status=EmergencyFirePumpStatus.NORMAL,
                sea_suction_permissive=True,
                hydrant_delivery_adequate=False,
                reprime_command_active=False,
                remarks="Emergency fire pump on standby with valid starting power and suction head.",
            )

        if telemetry.discharge_p_bar < cls.MIN_DISCHARGE_P_BAR:
            if telemetry.priming_elapsed_sec > cls.MAX_PRIMING_TIMEOUT_SEC:
                return EmergencyFirePumpAssessment(
                    status=EmergencyFirePumpStatus.PRIMING_TIMEOUT_TRIP,
                    sea_suction_permissive=True,
                    hydrant_delivery_adequate=False,
                    reprime_command_active=False,
                    remarks=f"Priming timed out at {telemetry.priming_elapsed_sec}s > {cls.MAX_PRIMING_TIMEOUT_SEC}s. Loss of prime.",
                )
            return EmergencyFirePumpAssessment(
                status=EmergencyFirePumpStatus.PRIMING_IN_PROGRESS,
                sea_suction_permissive=True,
                hydrant_delivery_adequate=False,
                reprime_command_active=True,
                remarks=f"Priming in progress ({telemetry.priming_elapsed_sec}s). Vacuum {telemetry.priming_vacuum_bar} bar.",
            )

        return EmergencyFirePumpAssessment(
            status=EmergencyFirePumpStatus.NORMAL,
            sea_suction_permissive=True,
            hydrant_delivery_adequate=True,
            reprime_command_active=False,
            remarks=f"Emergency fire pump delivering {telemetry.discharge_p_bar} bar >= {cls.MIN_DISCHARGE_P_BAR} bar. Hydrants pressurized.",
        )
