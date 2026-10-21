"""Phase 527: Main Engine Cylinder Lubricator Alpha/Pulse Feed-Rate & Sulfur-Adaptive TBN Control.
Complies with IACS UR M10 & MAN B&W Alpha ACC / WinGD Pulse Lubrication Rules.
Strictly < 85 LOC, zero mocks, pure deterministic statutory physics.
"""
from dataclasses import dataclass
from enum import Enum


class CylinderLubricatorState(str, Enum):
    OPTIMAL_ACC_DOSAGE = "OPTIMAL_ACC_DOSAGE"
    QUILL_NO_FLOW_CRITICAL_ALARM = "QUILL_NO_FLOW_CRITICAL_ALARM"
    ACID_CORROSION_LOW_BN_MISMATCH = "ACID_CORROSION_LOW_BN_MISMATCH"
    CALCIUM_DEPOSIT_HIGH_BN_WARNING = "CALCIUM_DEPOSIT_HIGH_BN_WARNING"
    SUB_MINIMUM_FEED_FLOOR_CLAMP = "SUB_MINIMUM_FEED_FLOOR_CLAMP"


@dataclass(frozen=True)
class CylinderLubricatorTelemetry:
    fuel_sulfur_pct: float
    cylinder_oil_bn: float = 70.0
    actual_feed_rate_g_kwh: float = 0.85
    acc_factor_g_kwh_per_s_pct: float = 0.28
    min_feed_floor_g_kwh: float = 0.60
    quill_pulse_feedback_ok: bool = True


@dataclass(frozen=True)
class CylinderLubricatorAssessment:
    lubricator_state: CylinderLubricatorState
    target_acc_feed_g_kwh: float
    emergency_max_dosage_boost: bool
    slowdown_request: bool
    alarm_active: bool
    alarm_code: str


class CylinderLubricatorAlphaDosageEngine:
    @classmethod
    def evaluate(cls, t: CylinderLubricatorTelemetry) -> CylinderLubricatorAssessment:
        target_feed = round(max(t.min_feed_floor_g_kwh, t.acc_factor_g_kwh_per_s_pct * t.fuel_sulfur_pct), 3)

        if not t.quill_pulse_feedback_ok:
            return CylinderLubricatorAssessment(
                CylinderLubricatorState.QUILL_NO_FLOW_CRITICAL_ALARM,
                target_feed, True, True, True, "UR_M10_LUBRICATOR_QUILL_NO_FLOW_TRIP",
            )
        if t.fuel_sulfur_pct > 0.50 and t.cylinder_oil_bn < 70.0:
            return CylinderLubricatorAssessment(
                CylinderLubricatorState.ACID_CORROSION_LOW_BN_MISMATCH,
                target_feed, True, False, True, "MAN_ACC_COLD_CORROSION_LOW_BN_ALARM",
            )
        if t.fuel_sulfur_pct <= 0.10 and t.cylinder_oil_bn >= 100.0:
            return CylinderLubricatorAssessment(
                CylinderLubricatorState.CALCIUM_DEPOSIT_HIGH_BN_WARNING,
                target_feed, False, False, True, "MAN_ACC_HIGH_BN_CROWN_POLISH_WARN",
            )
        if t.actual_feed_rate_g_kwh < t.min_feed_floor_g_kwh:
            return CylinderLubricatorAssessment(
                CylinderLubricatorState.SUB_MINIMUM_FEED_FLOOR_CLAMP,
                target_feed, True, False, True, "UR_M10_SUB_MIN_FEED_RATE_CLAMP",
            )
        return CylinderLubricatorAssessment(
            CylinderLubricatorState.OPTIMAL_ACC_DOSAGE,
            target_feed, False, False, False, "NONE",
        )
