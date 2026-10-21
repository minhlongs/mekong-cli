"""Phase 459: Marine Ballast Tank Stripping Eductor & Venturi Vacuum Monitoring.

Compliant with IMO Ballast Water Management Convention & IACS UR M62.
Monitors driving water supply pressure (P_drive >= 4.0 bar), suction vacuum (>= -0.80 bar / <= 0.20 bar abs),
backpressure ratio (P_back / P_drive <= 0.35), and cavitation noise limit to ensure complete tank drying.
"""

from dataclasses import dataclass
from enum import Enum


class BallastEductorStatus(str, Enum):
    NORMAL_STRIPPING = "NORMAL_STRIPPING"
    INSUFFICIENT_DRIVE_PRESSURE = "INSUFFICIENT_DRIVE_PRESSURE"
    HIGH_BACKPRESSURE = "HIGH_BACKPRESSURE"
    CAVITATION_WARNING = "CAVITATION_WARNING"
    SUCTION_LOSS_DRY = "SUCTION_LOSS_DRY"


@dataclass(frozen=True)
class BallastEductorTelemetry:
    drive_water_pressure_bar: float
    suction_vacuum_bar_gauge: float
    discharge_backpressure_bar: float
    cavitation_vibration_mm_s: float
    stripping_flow_rate_m3_h: float


@dataclass(frozen=True)
class BallastEductorAssessment:
    status: BallastEductorStatus
    backpressure_ratio: float
    effective_vacuum_adequate: bool
    cavitation_detected: bool
    tank_stripped_dry: bool
    safety_alarm: bool
    remarks: str


class BallastTankStrippingEductorEngine:
    """IACS UR M62 Ballast Stripping Eductor Physical Control Logic."""

    MIN_DRIVE_PRESSURE_BAR: float = 4.0
    MIN_SUCTION_VACUUM_BAR: float = -0.70  # More negative than -0.70 bar gauge indicates deep vacuum
    MAX_BACKPRESSURE_RATIO: float = 0.35
    MAX_VIBRATION_CAVITATION_MM_S: float = 7.5
    MIN_DRY_FLOW_RATE_M3_H: float = 2.0

    @classmethod
    def evaluate(cls, telemetry: BallastEductorTelemetry) -> BallastEductorAssessment:
        if telemetry.drive_water_pressure_bar <= 0:
            ratio = 1.0
        else:
            ratio = telemetry.discharge_backpressure_bar / telemetry.drive_water_pressure_bar

        if telemetry.drive_water_pressure_bar < cls.MIN_DRIVE_PRESSURE_BAR:
            return BallastEductorAssessment(
                status=BallastEductorStatus.INSUFFICIENT_DRIVE_PRESSURE,
                backpressure_ratio=ratio,
                effective_vacuum_adequate=False,
                cavitation_detected=False,
                tank_stripped_dry=False,
                safety_alarm=True,
                remarks="Drive water motive pressure below 4.0 bar minimum limit.",
            )

        if ratio > cls.MAX_BACKPRESSURE_RATIO:
            return BallastEductorAssessment(
                status=BallastEductorStatus.HIGH_BACKPRESSURE,
                backpressure_ratio=ratio,
                effective_vacuum_adequate=False,
                cavitation_detected=False,
                tank_stripped_dry=False,
                safety_alarm=True,
                remarks=f"Eductor discharge backpressure ratio {ratio:.3f} exceeds 0.35 limit.",
            )

        cavitation = telemetry.cavitation_vibration_mm_s >= cls.MAX_VIBRATION_CAVITATION_MM_S
        if cavitation:
            return BallastEductorAssessment(
                status=BallastEductorStatus.CAVITATION_WARNING,
                backpressure_ratio=ratio,
                effective_vacuum_adequate=telemetry.suction_vacuum_bar_gauge <= cls.MIN_SUCTION_VACUUM_BAR,
                cavitation_detected=True,
                tank_stripped_dry=False,
                safety_alarm=True,
                remarks="High acoustic vibration indicates severe venturi nozzle cavitation.",
            )

        tank_dry = telemetry.stripping_flow_rate_m3_h < cls.MIN_DRY_FLOW_RATE_M3_H
        vacuum_ok = telemetry.suction_vacuum_bar_gauge <= cls.MIN_SUCTION_VACUUM_BAR

        if tank_dry and vacuum_ok:
            return BallastEductorAssessment(
                status=BallastEductorStatus.SUCTION_LOSS_DRY,
                backpressure_ratio=ratio,
                effective_vacuum_adequate=True,
                cavitation_detected=False,
                tank_stripped_dry=True,
                safety_alarm=False,
                remarks="Ballast tank stripped dry: suction flow drop with high vacuum maintained.",
            )

        return BallastEductorAssessment(
            status=BallastEductorStatus.NORMAL_STRIPPING,
            backpressure_ratio=ratio,
            effective_vacuum_adequate=vacuum_ok,
            cavitation_detected=False,
            tank_stripped_dry=False,
            safety_alarm=False,
            remarks="Eductor motive venturi operating within nominal physical design envelope.",
        )
