"""Phase 486: Emergency Diesel Generator (EDG) Blackout Auto-Start Engine.

Complies with SOLAS II-1 Reg 43 and IACS UR M51.
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class EmergencyGenStatus(Enum):
    NORMAL = "normal"
    BLACKOUT_CRANKING_ACTIVE = "blackout_cranking_active"
    EMERGENCY_POWER_CONNECTED = "emergency_power_connected"
    TAKEOVER_TIME_EXCEEDED = "takeover_time_exceeded"
    FUEL_RESERVE_DEPLETED = "fuel_reserve_depleted"
    PNEUMATIC_QC_TRIP = "pneumatic_qc_trip"
    CRANK_FAILURE_LOCKOUT = "crank_failure_lockout"


@dataclass(frozen=True)
class EmergencyGenTelemetry:
    main_bus_voltage_pct: float
    edg_frequency_hz: float
    edg_voltage_v: float
    blackout_elapsed_s: float
    fuel_day_tank_hours: float
    start_attempts_remaining: int
    breaker_closed: bool
    pneumatic_quick_closing_tripped: bool = False


@dataclass(frozen=True)
class EmergencyGenAssessment:
    status: EmergencyGenStatus
    crank_start_command: bool
    breaker_close_permissive: bool
    emergency_power_restored: bool
    fuel_endurance_ok: bool
    remarks: str


class EmergencyGenBlackoutEngine:
    MAIN_BUS_DEAD_PCT = 20.0
    SOLAS_MAX_RESTORE_TIME_S = 45.0
    SOLAS_MIN_FUEL_HOURS = 8.0
    CRITICAL_FUEL_HOURS = 2.0
    RATED_VOLTAGE_MIN_V = 418.0
    RATED_VOLTAGE_MAX_V = 462.0
    RATED_FREQ_MIN_HZ = 58.5
    RATED_FREQ_MAX_HZ = 61.5

    @classmethod
    def evaluate(cls, telem: EmergencyGenTelemetry) -> EmergencyGenAssessment:
        fuel_ok = telem.fuel_day_tank_hours >= cls.SOLAS_MIN_FUEL_HOURS
        freq_volt_ok = (
            cls.RATED_VOLTAGE_MIN_V <= telem.edg_voltage_v <= cls.RATED_VOLTAGE_MAX_V
            and cls.RATED_FREQ_MIN_HZ <= telem.edg_frequency_hz <= cls.RATED_FREQ_MAX_HZ
        )

        if telem.pneumatic_quick_closing_tripped:
            return EmergencyGenAssessment(
                EmergencyGenStatus.PNEUMATIC_QC_TRIP, False, False, False, fuel_ok,
                "Pneumatic quick-closing fuel valve tripped. Start inhibited.",
            )

        if telem.fuel_day_tank_hours < cls.CRITICAL_FUEL_HOURS:
            return EmergencyGenAssessment(
                EmergencyGenStatus.FUEL_RESERVE_DEPLETED, False, False, False, False,
                f"Emergency fuel {telem.fuel_day_tank_hours:.1f}h < 2h critical limit. Fuel depleted.",
            )

        if telem.main_bus_voltage_pct > cls.MAIN_BUS_DEAD_PCT:
            return EmergencyGenAssessment(
                EmergencyGenStatus.NORMAL, False, False, False, fuel_ok,
                "Main bus energized. Emergency generator on cold standby.",
            )

        if telem.start_attempts_remaining <= 0 and not telem.breaker_closed and not freq_volt_ok:
            return EmergencyGenAssessment(
                EmergencyGenStatus.CRANK_FAILURE_LOCKOUT, False, False, False, fuel_ok,
                "Crank failure lockout. Consecutive start attempts exhausted.",
            )

        if telem.breaker_closed and freq_volt_ok:
            return EmergencyGenAssessment(
                EmergencyGenStatus.EMERGENCY_POWER_CONNECTED, False, True, True, fuel_ok,
                "Emergency switchboard energized. Vital services supplied under SOLAS II-1/43.",
            )

        if telem.blackout_elapsed_s > cls.SOLAS_MAX_RESTORE_TIME_S:
            return EmergencyGenAssessment(
                EmergencyGenStatus.TAKEOVER_TIME_EXCEEDED, True, freq_volt_ok, False, fuel_ok,
                f"Takeover time {telem.blackout_elapsed_s}s exceeded 45s SOLAS ceiling.",
            )

        return EmergencyGenAssessment(
            EmergencyGenStatus.BLACKOUT_CRANKING_ACTIVE, True, freq_volt_ok, False, fuel_ok,
            "Blackout detected. Autonomous start & frequency ramp sequence in progress.",
        )
