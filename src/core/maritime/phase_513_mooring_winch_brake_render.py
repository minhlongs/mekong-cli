"""Phase 513: Mooring Winch Hydraulic Brake Holding & Render-Recover Tension Control.
Complies with OCIMF MEG4 (Mooring Equipment Guidelines) and ISO 3730 Standards.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class MooringBrakeStatus(str, Enum):
    SAFE_HOLDING_TENSION = "SAFE_HOLDING_TENSION"
    HIGH_TENSION_PRE_RENDER_WARN = "HIGH_TENSION_PRE_RENDER_WARN"
    BRAKE_RENDERING_PAYOUT = "BRAKE_RENDERING_PAYOUT"
    MEG4_OVER_HOLDING_CAP_VIOLATION = "MEG4_OVER_HOLDING_CAP_VIOLATION"
    BRAKE_LINING_WEAR_FAULT = "BRAKE_LINING_WEAR_FAULT"


@dataclass(frozen=True)
class MooringWinchTelemetry:
    line_tension_pct_mbl: float
    brake_setpoint_pct_mbl: float = 60.0
    lining_wear_mm: float = 1.5


@dataclass(frozen=True)
class MooringWinchAssessment:
    brake_status: MooringBrakeStatus
    drum_rendering_active: bool
    meg4_compliant: bool
    alarm_active: bool
    alarm_code: str


class MooringWinchBrakeRenderEngine:
    """Evaluates mooring line % MBL tension against 60% MBL render setpoint and 80% MEG4 cap."""

    PRE_RENDER_WARN_PCT: float = 52.0
    MEG4_MAX_BRAKE_PCT: float = 80.0
    MAX_LINING_WEAR_MM: float = 5.0

    @classmethod
    def evaluate(cls, t: MooringWinchTelemetry) -> MooringWinchAssessment:
        if t.lining_wear_mm >= cls.MAX_LINING_WEAR_MM:
            return MooringWinchAssessment(
                MooringBrakeStatus.BRAKE_LINING_WEAR_FAULT,
                False,
                False,
                True,
                "MOORING_BRAKE_BAND_LINING_WORN",
            )
        if t.brake_setpoint_pct_mbl > cls.MEG4_MAX_BRAKE_PCT:
            return MooringWinchAssessment(
                MooringBrakeStatus.MEG4_OVER_HOLDING_CAP_VIOLATION,
                False,
                False,
                True,
                "OCIMF_MEG4_BRAKE_EXCEEDS_80PCT_MBL",
            )
        if t.line_tension_pct_mbl >= t.brake_setpoint_pct_mbl:
            return MooringWinchAssessment(
                MooringBrakeStatus.BRAKE_RENDERING_PAYOUT,
                True,
                True,
                True,
                "MOORING_WINCH_BRAKE_RENDERING_SURGE",
            )
        if t.line_tension_pct_mbl >= cls.PRE_RENDER_WARN_PCT:
            return MooringWinchAssessment(
                MooringBrakeStatus.HIGH_TENSION_PRE_RENDER_WARN,
                False,
                True,
                True,
                "MOORING_LINE_HIGH_TENSION_WARNING",
            )
        return MooringWinchAssessment(
            MooringBrakeStatus.SAFE_HOLDING_TENSION,
            False,
            True,
            False,
            "NONE",
        )
