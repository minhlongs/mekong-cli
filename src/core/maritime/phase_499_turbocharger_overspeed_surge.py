"""Phase 499: Main Engine Turbocharger Overspeed, Lube Oil & Surge Protection.
Complies with IACS UR M10 and MAN B&W / WinGD Turbocharger Safety Standards.
Strictly < 90 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class TurbochargerStatus(str, Enum):
    NORMAL_OPERATION = "NORMAL_OPERATION"
    COMPRESSOR_SURGE_BYPASS = "COMPRESSOR_SURGE_BYPASS"
    HIGH_EXHAUST_TEMP_ALARM = "HIGH_EXHAUST_TEMP_ALARM"
    LOW_LUBE_OIL_ALARM = "LOW_LUBE_OIL_ALARM"
    OVERSPEED_ALARM = "OVERSPEED_ALARM"
    EMERGENCY_SLOWDOWN_TRIP = "EMERGENCY_SLOWDOWN_TRIP"


@dataclass(frozen=True)
class TurbochargerTelemetry:
    rotor_rpm: float
    lube_oil_inlet_bar: float
    exhaust_inlet_temp_c: float
    surge_pulses_per_min: int = 0


@dataclass(frozen=True)
class TurbochargerAssessment:
    status: TurbochargerStatus
    slowdown_requested: bool
    wastegate_bypass_open: bool
    alarm_active: bool
    alarm_code: str


class TurbochargerOverspeedSurgeEngine:
    """Evaluates ME turbocharger rotor RPM, bearing lube oil, exhaust temp, and surge."""

    ALARM_RPM: float = 18500.0
    TRIP_RPM: float = 19500.0
    MIN_LUBE_BAR: float = 1.2
    TRIP_LUBE_BAR: float = 0.8
    MAX_EXHAUST_TEMP_C: float = 550.0
    SURGE_PULSE_LIMIT: int = 3

    @classmethod
    def evaluate(cls, t: TurbochargerTelemetry) -> TurbochargerAssessment:
        if t.rotor_rpm >= cls.TRIP_RPM or t.lube_oil_inlet_bar < cls.TRIP_LUBE_BAR:
            code = "TC_CRITICAL_OVERSPEED_TRIP" if t.rotor_rpm >= cls.TRIP_RPM else "TC_CRITICAL_LO_PRESSURE_TRIP"
            return TurbochargerAssessment(
                TurbochargerStatus.EMERGENCY_SLOWDOWN_TRIP, True, True, True, code
            )
        if t.rotor_rpm >= cls.ALARM_RPM:
            return TurbochargerAssessment(
                TurbochargerStatus.OVERSPEED_ALARM, True, True, True, "TC_OVERSPEED_WARNING"
            )
        if t.lube_oil_inlet_bar < cls.MIN_LUBE_BAR:
            return TurbochargerAssessment(
                TurbochargerStatus.LOW_LUBE_OIL_ALARM, False, False, True, "TC_LOW_LUBE_OIL_PRESSURE"
            )
        if t.surge_pulses_per_min >= cls.SURGE_PULSE_LIMIT:
            return TurbochargerAssessment(
                TurbochargerStatus.COMPRESSOR_SURGE_BYPASS, True, True, True, "TC_COMPRESSOR_SURGING"
            )
        if t.exhaust_inlet_temp_c > cls.MAX_EXHAUST_TEMP_C:
            return TurbochargerAssessment(
                TurbochargerStatus.HIGH_EXHAUST_TEMP_ALARM, True, True, True, "TC_HIGH_EXHAUST_GAS_TEMP"
            )
        return TurbochargerAssessment(
            TurbochargerStatus.NORMAL_OPERATION, False, False, False, "NONE"
        )
