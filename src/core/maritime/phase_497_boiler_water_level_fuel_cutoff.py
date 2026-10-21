"""Phase 497: Auxiliary Boiler Water Level & Low-Water Fuel Oil Cutoff Interlock.
IACS UR M53 & ASME Section I compliance. Strictly < 95 LOC.
"""
from dataclasses import dataclass
from enum import Enum

class BurnerState(str, Enum):
    FIRING_ALLOWED = "FIRING_ALLOWED"
    SAFETY_SHUTOFF_TRIPPED = "SAFETY_SHUTOFF_TRIPPED"

@dataclass(frozen=True)
class BoilerWaterTelemetry:
    water_level_mm: float
    differential_probe_matched: bool = True
    feedwater_pump_running: bool = True

@dataclass(frozen=True)
class BoilerWaterAssessment:
    burner_state: BurnerState
    alarm_active: bool
    alarm_code: str
    feedwater_boost_required: bool

class BoilerWaterLevelFuelCutoffEngine:
    NORMAL_MAX_MM = 50.0
    NORMAL_MIN_MM = -50.0
    LOW_LEVEL_ALARM_MM = -75.0
    CRITICAL_LOW_LOW_CUTOFF_MM = -120.0
    HIGH_WATER_ALARM_MM = 90.0

    @classmethod
    def evaluate(cls, telem: BoilerWaterTelemetry) -> BoilerWaterAssessment:
        if not telem.differential_probe_matched:
            return BoilerWaterAssessment(
                burner_state=BurnerState.SAFETY_SHUTOFF_TRIPPED,
                alarm_active=True,
                alarm_code="LEVEL_PROBE_DISAGREEMENT_FAIL_SAFE_TRIP",
                feedwater_boost_required=False,
            )
        if telem.water_level_mm <= cls.CRITICAL_LOW_LOW_CUTOFF_MM:
            return BoilerWaterAssessment(
                burner_state=BurnerState.SAFETY_SHUTOFF_TRIPPED,
                alarm_active=True,
                alarm_code=f"CRITICAL_LOW_LOW_WATER_{telem.water_level_mm:.1f}MM_BURNER_CUTOFF",
                feedwater_boost_required=True,
            )
        if telem.water_level_mm <= cls.LOW_LEVEL_ALARM_MM:
            return BoilerWaterAssessment(
                burner_state=BurnerState.FIRING_ALLOWED,
                alarm_active=True,
                alarm_code=f"LOW_WATER_LEVEL_{telem.water_level_mm:.1f}MM_BOOST_PUMP",
                feedwater_boost_required=True,
            )
        if telem.water_level_mm >= cls.HIGH_WATER_ALARM_MM:
            return BoilerWaterAssessment(
                burner_state=BurnerState.FIRING_ALLOWED,
                alarm_active=True,
                alarm_code=f"HIGH_WATER_LEVEL_{telem.water_level_mm:.1f}MM_PRIMING_RISK",
                feedwater_boost_required=False,
            )
        return BoilerWaterAssessment(
            burner_state=BurnerState.FIRING_ALLOWED,
            alarm_active=False,
            alarm_code="WATER_LEVEL_NORMAL",
            feedwater_boost_required=False,
        )
