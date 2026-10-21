"""Phase 507: Shaft Grounding Slip Ring & Spark Erosion Protection.
Complies with IACS UR M10 and DNV Propeller Shaft Earthing Rules.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class ShaftGroundingState(str, Enum):
    OPTIMAL_EARTHING = "OPTIMAL_EARTHING"
    BRUSH_CONTACT_DEGRADED = "BRUSH_CONTACT_DEGRADED"
    SPARK_EROSION_CRITICAL_ALARM = "SPARK_EROSION_CRITICAL_ALARM"
    OPEN_CIRCUIT_BRUSH_LIFTED = "OPEN_CIRCUIT_BRUSH_LIFTED"


@dataclass(frozen=True)
class ShaftGroundingTelemetry:
    shaft_potential_mv: float
    grounding_current_ma: float
    brush_wear_pct: float = 20.0


@dataclass(frozen=True)
class ShaftGroundingAssessment:
    grounding_state: ShaftGroundingState
    bearing_pitting_risk: bool
    brush_service_required: bool
    alarm_active: bool
    alarm_code: str


class ShaftGroundingSlipRingEngine:
    """Evaluates propeller shaft-to-hull potential (< 50 mV nominal, >= 100 mV spark erosion)."""

    WARNING_MV: float = 50.0
    CRITICAL_SPARK_MV: float = 100.0
    MAX_BRUSH_WEAR_PCT: float = 80.0

    @classmethod
    def evaluate(cls, t: ShaftGroundingTelemetry) -> ShaftGroundingAssessment:
        if t.grounding_current_ma <= 0.1 and t.shaft_potential_mv >= cls.WARNING_MV:
            return ShaftGroundingAssessment(
                ShaftGroundingState.OPEN_CIRCUIT_BRUSH_LIFTED,
                True,
                True,
                True,
                "SHAFT_EARTHING_OPEN_CIRCUIT_FAULT",
            )
        if t.shaft_potential_mv >= cls.CRITICAL_SPARK_MV:
            return ShaftGroundingAssessment(
                ShaftGroundingState.SPARK_EROSION_CRITICAL_ALARM,
                True,
                True,
                True,
                "SHAFT_BEARING_EDM_SPARK_EROSION_RISK",
            )
        if t.shaft_potential_mv >= cls.WARNING_MV or t.brush_wear_pct >= cls.MAX_BRUSH_WEAR_PCT:
            return ShaftGroundingAssessment(
                ShaftGroundingState.BRUSH_CONTACT_DEGRADED,
                False,
                True,
                True,
                "SHAFT_SLIP_RING_HIGH_RESISTANCE_OR_WEAR",
            )
        return ShaftGroundingAssessment(
            ShaftGroundingState.OPTIMAL_EARTHING,
            False,
            False,
            False,
            "NONE",
        )
