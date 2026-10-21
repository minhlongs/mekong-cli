"""Phase 523: Main Engine Torsional Vibration Damper & Barred Speed Range (BSR) Control.
Complies with IACS UR M68 and MAN B&W / WinGD Propulsion Shafting Rules.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class TorsionalBsrState(str, Enum):
    SAFE_CONTINUOUS_RPM_ENVELOPE = "SAFE_CONTINUOUS_RPM_ENVELOPE"
    BSR_FAST_PASSAGE_TRANSIT = "BSR_FAST_PASSAGE_TRANSIT"
    BSR_DWELL_RESONANCE_SLOWDOWN_TRIP = "BSR_DWELL_RESONANCE_SLOWDOWN_TRIP"
    DAMPER_THERMAL_STRESS_CRITICAL_ALARM = "DAMPER_THERMAL_STRESS_CRITICAL_ALARM"


@dataclass(frozen=True)
class TorsionalBsrTelemetry:
    shaft_rpm: float
    dwell_time_in_bsr_sec: float = 0.0
    torsional_stress_mpa: float = 18.0
    damper_oil_temp_c: float = 65.0
    damper_oil_pressure_bar: float = 2.2
    bsr_low_rpm: float = 42.0
    bsr_high_rpm: float = 54.0


@dataclass(frozen=True)
class TorsionalBsrAssessment:
    bsr_state: TorsionalBsrState
    fast_passage_boost_active: bool
    governor_leave_bsr_cmd: bool
    alarm_active: bool
    alarm_code: str


class TorsionalVibrationBsrDamperEngine:
    """Enforces IACS UR M68 Barred Speed Range dwell limits and Geislinger damper health."""

    MAX_BSR_DWELL_SEC: float = 25.0
    MAX_STRESS_MPA: float = 45.0
    MAX_DAMPER_TEMP_C: float = 90.0
    MIN_DAMPER_OIL_BAR: float = 1.2

    @classmethod
    def evaluate(cls, t: TorsionalBsrTelemetry) -> TorsionalBsrAssessment:
        if (
            t.torsional_stress_mpa >= cls.MAX_STRESS_MPA
            or t.damper_oil_temp_c >= cls.MAX_DAMPER_TEMP_C
            or t.damper_oil_pressure_bar < cls.MIN_DAMPER_OIL_BAR
        ):
            return TorsionalBsrAssessment(
                TorsionalBsrState.DAMPER_THERMAL_STRESS_CRITICAL_ALARM,
                False,
                True,
                True,
                "TORSIONAL_DAMPER_OVERSTRESS_OR_OIL_FAULT",
            )
        in_bsr = t.bsr_low_rpm <= t.shaft_rpm <= t.bsr_high_rpm
        if in_bsr and t.dwell_time_in_bsr_sec >= cls.MAX_BSR_DWELL_SEC:
            return TorsionalBsrAssessment(
                TorsionalBsrState.BSR_DWELL_RESONANCE_SLOWDOWN_TRIP,
                True,
                True,
                True,
                "IACS_M68_BSR_PROLONGED_DWELL_TRIP",
            )
        if in_bsr:
            return TorsionalBsrAssessment(
                TorsionalBsrState.BSR_FAST_PASSAGE_TRANSIT,
                True,
                False,
                False,
                "NONE",
            )
        return TorsionalBsrAssessment(
            TorsionalBsrState.SAFE_CONTINUOUS_RPM_ENVELOPE,
            False,
            False,
            False,
            "NONE",
        )
