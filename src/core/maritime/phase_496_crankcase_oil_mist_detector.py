"""Phase 496: Main Engine Crankcase Oil Mist Detector & Relief Valve Supervisory.
IACS UR M10 & SOLAS Reg II-1/47 compliance. Strictly < 95 LOC.
"""
from dataclasses import dataclass
from enum import Enum

class EngineSafeties(str, Enum):
    NORMAL = "NORMAL"
    SLOWDOWN_REQUESTED = "SLOWDOWN_REQUESTED"
    EMERGENCY_STOP_REQUESTED = "EMERGENCY_STOP_REQUESTED"

@dataclass(frozen=True)
class OilMistTelemetry:
    mist_opacity_pct: float
    fan_differential_pa: float
    flame_arrester_intact: bool = True
    scavenge_isolation_active: bool = False

@dataclass(frozen=True)
class OilMistAssessment:
    engine_command: EngineSafeties
    alarm_active: bool
    alarm_code: str
    explosion_risk_critical: bool

class CrankcaseOilMistDetectorEngine:
    PRE_ALARM_OPACITY_PCT = 1.0
    SLOWDOWN_OPACITY_PCT = 2.0
    EMERGENCY_STOP_OPACITY_PCT = 3.5
    MIN_FAN_DRAFT_PA = 100.0

    @classmethod
    def evaluate(cls, telem: OilMistTelemetry) -> OilMistAssessment:
        if not telem.flame_arrester_intact:
            return OilMistAssessment(
                engine_command=EngineSafeties.EMERGENCY_STOP_REQUESTED,
                alarm_active=True,
                alarm_code="FLAME_ARRESTER_RUPTURED_IMMEDIATE_STOP",
                explosion_risk_critical=True,
            )
        if telem.fan_differential_pa < cls.MIN_FAN_DRAFT_PA:
            return OilMistAssessment(
                engine_command=EngineSafeties.NORMAL,
                alarm_active=True,
                alarm_code="OMD_EXTRACTION_FAN_DRAFT_LOSS",
                explosion_risk_critical=False,
            )
        if telem.mist_opacity_pct >= cls.EMERGENCY_STOP_OPACITY_PCT:
            return OilMistAssessment(
                engine_command=EngineSafeties.EMERGENCY_STOP_REQUESTED,
                alarm_active=True,
                alarm_code=f"CRITICAL_MIST_OPACITY_{telem.mist_opacity_pct:.1f}PCT_CRANKCASE_EXPLOSION_IMMINENT",
                explosion_risk_critical=True,
            )
        if telem.mist_opacity_pct >= cls.SLOWDOWN_OPACITY_PCT:
            return OilMistAssessment(
                engine_command=EngineSafeties.SLOWDOWN_REQUESTED,
                alarm_active=True,
                alarm_code=f"HIGH_MIST_OPACITY_{telem.mist_opacity_pct:.1f}PCT_SLOWDOWN_INITIATED",
                explosion_risk_critical=True,
            )
        if telem.mist_opacity_pct >= cls.PRE_ALARM_OPACITY_PCT:
            return OilMistAssessment(
                engine_command=EngineSafeties.NORMAL,
                alarm_active=True,
                alarm_code=f"PRE_ALARM_MIST_OPACITY_{telem.mist_opacity_pct:.1f}PCT",
                explosion_risk_critical=False,
            )
        return OilMistAssessment(
            engine_command=EngineSafeties.NORMAL,
            alarm_active=False,
            alarm_code="NORMAL_OPACITY_LEVEL",
            explosion_risk_critical=False,
        )
