"""Phase 484: Main Engine Bearing Temperature & Oil Mist Slowdown Engine.

Complies with IACS UR M10/M3 and SOLAS II-1 Reg 31. Strictly < 95 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class BearingMistStatus(Enum):
    NORMAL = "normal"
    BEARING_HIGH_TEMP_ALERT = "bearing_high_temp_alert"
    OIL_MIST_PRE_ALARM = "oil_mist_pre_alarm"
    EMERGENCY_SLOWDOWN_TRIP = "emergency_slowdown_trip"
    LUBE_OIL_PRESSURE_CRITICAL = "lube_oil_pressure_critical"


@dataclass(frozen=True)
class BearingMistSlowdownTelemetry:
    max_crosshead_temp_c: float
    max_main_bearing_temp_c: float
    bearing_delta_t_c: float
    crankcase_oil_mist_pct_lel: float
    lube_oil_inlet_p_bar: float
    engine_load_pct: float


@dataclass(frozen=True)
class BearingMistSlowdownAssessment:
    status: BearingMistStatus
    slowdown_command: bool
    crankcase_explosion_risk: bool
    lube_oil_pressure_ok: bool
    remarks: str


class BearingMistSlowdownEngine:
    MAX_CROSSHEAD_ALERT_C = 80.0
    MAX_MAIN_BEARING_ALERT_C = 78.0
    MAX_BEARING_SPREAD_C = 12.0
    MIST_PRE_ALARM_LEL_PCT = 1.5
    MIST_SLOWDOWN_LEL_PCT = 2.5
    MIN_LUBE_OIL_PRESSURE_BAR = 1.8

    @classmethod
    def evaluate(cls, telem: BearingMistSlowdownTelemetry) -> BearingMistSlowdownAssessment:
        if telem.lube_oil_inlet_p_bar < cls.MIN_LUBE_OIL_PRESSURE_BAR:
            return BearingMistSlowdownAssessment(
                BearingMistStatus.LUBE_OIL_PRESSURE_CRITICAL, True, False, False,
                "L.O. inlet pressure < 1.8 bar. Immediate engine shutdown/slowdown.",
            )
        if telem.crankcase_oil_mist_pct_lel >= cls.MIST_SLOWDOWN_LEL_PCT:
            return BearingMistSlowdownAssessment(
                BearingMistStatus.EMERGENCY_SLOWDOWN_TRIP, True, True, True,
                "Crankcase oil mist >= 2.5% LEL. Severe explosion risk. Auto slowdown.",
            )
        if (
            telem.max_crosshead_temp_c >= cls.MAX_CROSSHEAD_ALERT_C
            or telem.max_main_bearing_temp_c >= cls.MAX_MAIN_BEARING_ALERT_C
        ):
            return BearingMistSlowdownAssessment(
                BearingMistStatus.EMERGENCY_SLOWDOWN_TRIP, True, False, True,
                "Bearing overheat (crosshead >= 80C or main >= 78C). Auto slowdown.",
            )
        if telem.crankcase_oil_mist_pct_lel >= cls.MIST_PRE_ALARM_LEL_PCT:
            return BearingMistSlowdownAssessment(
                BearingMistStatus.OIL_MIST_PRE_ALARM, False, False, True,
                "Crankcase optical oil mist pre-alarm active (1.5 - 2.5% LEL).",
            )
        if telem.bearing_delta_t_c >= cls.MAX_BEARING_SPREAD_C:
            return BearingMistSlowdownAssessment(
                BearingMistStatus.BEARING_HIGH_TEMP_ALERT, False, False, True,
                "Bearing temperature deviation spread >= 12C detected.",
            )
        return BearingMistSlowdownAssessment(
            BearingMistStatus.NORMAL, False, False, True,
            "Bearing temperatures and crankcase atmosphere within IACS safe limits.",
        )
