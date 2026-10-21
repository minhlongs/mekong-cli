"""Phase 490: Starting Air Compressor Unloader & Receiver Pressure Safety Engine.

Complies with IACS UR M12 standards. Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class StartingAirStatus(Enum):
    COMPRESSOR_STOPPED_IDLE = "compressor_stopped_idle"
    PURGE_UNLOADER_RUNNING = "purge_unloader_running"
    COMPRESSION_CHARGING = "compression_charging"
    SAFETY_VALVE_LIFT_TRIP = "safety_valve_lift_trip"
    HIGH_DISCHARGE_TEMP_TRIP = "high_discharge_temp_trip"


@dataclass(frozen=True)
class StartingAirTelemetry:
    receiver_pressure_bar: float
    high_stage_discharge_temp_c: float
    compressor_running: bool
    unloader_purge_elapsed_s: float
    compressor_start_requested: bool = False


@dataclass(frozen=True)
class StartingAirAssessment:
    status: StartingAirStatus
    motor_start_command: bool
    unloader_purge_solenoid_open: bool
    safety_relief_lifted: bool
    trip_lockout: bool
    remarks: str


class StartingAirCompressorUnloaderEngine:
    RECEIVER_CUT_IN_BAR = 25.0
    RECEIVER_CUT_OUT_BAR = 30.0
    SAFETY_VALVE_LIFT_SETPOINT_BAR = 31.5
    MAX_DISCHARGE_TEMP_C = 160.0
    UNLOADER_PURGE_DURATION_S = 5.0

    @classmethod
    def evaluate(cls, telem: StartingAirTelemetry) -> StartingAirAssessment:
        if telem.high_stage_discharge_temp_c > cls.MAX_DISCHARGE_TEMP_C:
            return StartingAirAssessment(
                StartingAirStatus.HIGH_DISCHARGE_TEMP_TRIP, False, False, False, True,
                f"High discharge temp {telem.high_stage_discharge_temp_c:.1f}C > 160C. Compressor trip lockout.",
            )
        if telem.receiver_pressure_bar >= cls.SAFETY_VALVE_LIFT_SETPOINT_BAR:
            return StartingAirAssessment(
                StartingAirStatus.SAFETY_VALVE_LIFT_TRIP, False, True, True, True,
                f"Pressure {telem.receiver_pressure_bar:.1f} bar >= 31.5 bar (105% WP). Safety valve lifted.",
            )
        needs_charge = (
            telem.receiver_pressure_bar < cls.RECEIVER_CUT_IN_BAR
            or (telem.compressor_running and telem.receiver_pressure_bar < cls.RECEIVER_CUT_OUT_BAR)
            or telem.compressor_start_requested
        )
        if not needs_charge and telem.receiver_pressure_bar >= cls.RECEIVER_CUT_OUT_BAR:
            return StartingAirAssessment(
                StartingAirStatus.COMPRESSOR_STOPPED_IDLE, False, False, False, False,
                f"Receiver pressure {telem.receiver_pressure_bar:.1f} bar >= 30.0 bar. Compressor cut-out stopped.",
            )
        if telem.unloader_purge_elapsed_s < cls.UNLOADER_PURGE_DURATION_S:
            return StartingAirAssessment(
                StartingAirStatus.PURGE_UNLOADER_RUNNING, True, True, False, False,
                f"Pre-start unloader purge active ({telem.unloader_purge_elapsed_s:.1f}s / 5.0s). Solenoid open.",
            )
        return StartingAirAssessment(
            StartingAirStatus.COMPRESSION_CHARGING, True, False, False, False,
            f"Compressor loaded and charging receiver ({telem.receiver_pressure_bar:.1f} bar -> 30.0 bar).",
        )
