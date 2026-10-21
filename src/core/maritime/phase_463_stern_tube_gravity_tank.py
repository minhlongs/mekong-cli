"""Phase 463: Marine Stern Tube Lube Oil Gravity Tank Low Level & Temp Control.

Compliant with IACS UR M56 & DNV Rules Pt. 4 Ch. 4.
Monitors stern tube gravity tank level (>= 40% normal, < 25% trip transfer),
oil temperature envelope (35-55 deg C), aft seal oil-seawater differential pressure (>= 0.15 bar),
and water-in-oil emulsion ingress (<= 0.05%).
"""

from dataclasses import dataclass
from enum import Enum


class SternTubeGravityStatus(str, Enum):
    NORMAL = "NORMAL"
    LEVEL_LOW_WARNING = "LEVEL_LOW_WARNING"
    LEVEL_CRITICAL_TRIP = "LEVEL_CRITICAL_TRIP"
    SEAL_DP_LOW = "SEAL_DP_LOW"
    OIL_TEMP_ABNORMAL = "OIL_TEMP_ABNORMAL"
    WATER_CONTAMINATION = "WATER_CONTAMINATION"


@dataclass(frozen=True)
class SternTubeGravityTelemetry:
    gravity_tank_level_pct: float
    oil_temperature_celsius: float
    aft_seal_differential_pressure_bar: float
    water_content_pct: float
    standby_pump_auto_armed: bool


@dataclass(frozen=True)
class SternTubeGravityAssessment:
    status: SternTubeGravityStatus
    hydrostatic_head_adequate: bool
    seal_protection_intact: bool
    water_ingress_detected: bool
    emergency_pump_triggered: bool
    alarm_active: bool
    remarks: str


class SternTubeGravityTankEngine:
    """IACS UR M56 Stern Tube Lube Oil Gravity Tank Hydrostatic Pressure Logic."""

    WARN_LEVEL_PCT: float = 40.0
    CRITICAL_LEVEL_PCT: float = 25.0
    MIN_SEAL_DP_BAR: float = 0.15
    MIN_OIL_TEMP_C: float = 35.0
    MAX_OIL_TEMP_C: float = 55.0
    MAX_WATER_CONTENT_PCT: float = 0.05

    @classmethod
    def evaluate(cls, telemetry: SternTubeGravityTelemetry) -> SternTubeGravityAssessment:
        if telemetry.water_content_pct > cls.MAX_WATER_CONTENT_PCT:
            return SternTubeGravityAssessment(
                status=SternTubeGravityStatus.WATER_CONTAMINATION,
                hydrostatic_head_adequate=telemetry.gravity_tank_level_pct >= cls.WARN_LEVEL_PCT,
                seal_protection_intact=telemetry.aft_seal_differential_pressure_bar >= cls.MIN_SEAL_DP_BAR,
                water_ingress_detected=True,
                emergency_pump_triggered=False,
                alarm_active=True,
                remarks=f"Stern tube oil water ingress: {telemetry.water_content_pct:.2f}% > {cls.MAX_WATER_CONTENT_PCT}%",
            )

        if telemetry.aft_seal_differential_pressure_bar < cls.MIN_SEAL_DP_BAR:
            return SternTubeGravityAssessment(
                status=SternTubeGravityStatus.SEAL_DP_LOW,
                hydrostatic_head_adequate=telemetry.gravity_tank_level_pct >= cls.WARN_LEVEL_PCT,
                seal_protection_intact=False,
                water_ingress_detected=False,
                emergency_pump_triggered=telemetry.standby_pump_auto_armed,
                alarm_active=True,
                remarks=f"Aft seal DP {telemetry.aft_seal_differential_pressure_bar:.2f} bar < {cls.MIN_SEAL_DP_BAR} bar limit",
            )

        if telemetry.gravity_tank_level_pct < cls.CRITICAL_LEVEL_PCT:
            return SternTubeGravityAssessment(
                status=SternTubeGravityStatus.LEVEL_CRITICAL_TRIP,
                hydrostatic_head_adequate=False,
                seal_protection_intact=telemetry.aft_seal_differential_pressure_bar >= cls.MIN_SEAL_DP_BAR,
                water_ingress_detected=False,
                emergency_pump_triggered=True,
                alarm_active=True,
                remarks=f"Critical gravity tank level: {telemetry.gravity_tank_level_pct:.1f}% < {cls.CRITICAL_LEVEL_PCT}%",
            )

        if telemetry.gravity_tank_level_pct < cls.WARN_LEVEL_PCT:
            return SternTubeGravityAssessment(
                status=SternTubeGravityStatus.LEVEL_LOW_WARNING,
                hydrostatic_head_adequate=False,
                seal_protection_intact=telemetry.aft_seal_differential_pressure_bar >= cls.MIN_SEAL_DP_BAR,
                water_ingress_detected=False,
                emergency_pump_triggered=False,
                alarm_active=True,
                remarks=f"Gravity tank level low: {telemetry.gravity_tank_level_pct:.1f}% < {cls.WARN_LEVEL_PCT}%",
            )

        if not (cls.MIN_OIL_TEMP_C <= telemetry.oil_temperature_celsius <= cls.MAX_OIL_TEMP_C):
            return SternTubeGravityAssessment(
                status=SternTubeGravityStatus.OIL_TEMP_ABNORMAL,
                hydrostatic_head_adequate=True,
                seal_protection_intact=True,
                water_ingress_detected=False,
                emergency_pump_triggered=False,
                alarm_active=True,
                remarks=f"Stern tube oil temperature {telemetry.oil_temperature_celsius:.1f}C out of {cls.MIN_OIL_TEMP_C}-{cls.MAX_OIL_TEMP_C}C band",
            )

        return SternTubeGravityAssessment(
            status=SternTubeGravityStatus.NORMAL,
            hydrostatic_head_adequate=True,
            seal_protection_intact=True,
            water_ingress_detected=False,
            emergency_pump_triggered=False,
            alarm_active=False,
            remarks="Stern tube gravity tank and aft seal differential pressure in normal specification",
        )
