"""Phase 503: Hull Impressed Current Cathodic Protection (ICCP) Control.
Complies with IACS UR Z3 and ISO 13174 Marine Cathodic Protection Standards.
Strictly < 90 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class IccpProtectionState(str, Enum):
    OPTIMAL_PASSIVATION = "OPTIMAL_PASSIVATION"
    OVER_PROTECTION_SHIELD_RISK = "OVER_PROTECTION_SHIELD_RISK"
    UNDER_PROTECTION_CORROSION_RISK = "UNDER_PROTECTION_CORROSION_RISK"
    RECTIFIER_OVERCURRENT_LIMIT = "RECTIFIER_OVERCURRENT_LIMIT"


@dataclass(frozen=True)
class IccpTelemetry:
    reference_potential_mv: float
    anode_current_amps: float
    max_rated_current_amps: float = 150.0


@dataclass(frozen=True)
class IccpAssessment:
    protection_state: IccpProtectionState
    recommended_current_amps: float
    dielectric_disbondment_risk: bool
    alarm_active: bool
    alarm_code: str


class IccpHullPotentialAnodeEngine:
    """Evaluates Ag/AgCl hull reference potential (-800 to -900 mV) and anode current."""

    OVER_PROTECT_MV: float = -1050.0
    UNDER_PROTECT_MV: float = -750.0
    TARGET_POTENTIAL_MV: float = -850.0

    @classmethod
    def evaluate(cls, t: IccpTelemetry) -> IccpAssessment:
        if t.reference_potential_mv < cls.OVER_PROTECT_MV:
            throttled = max(0.0, t.anode_current_amps * 0.5)
            return IccpAssessment(
                IccpProtectionState.OVER_PROTECTION_SHIELD_RISK,
                throttled,
                True,
                True,
                "ICCP_OVER_PROTECTION_HYDROGEN_EMBRITTLEMENT",
            )
        if t.anode_current_amps > t.max_rated_current_amps:
            return IccpAssessment(
                IccpProtectionState.RECTIFIER_OVERCURRENT_LIMIT,
                t.max_rated_current_amps,
                False,
                True,
                "ICCP_THYRISTOR_CURRENT_CLAMPED",
            )
        if t.reference_potential_mv > cls.UNDER_PROTECT_MV:
            boosted = min(t.max_rated_current_amps, t.anode_current_amps * 1.35 + 10.0)
            return IccpAssessment(
                IccpProtectionState.UNDER_PROTECTION_CORROSION_RISK,
                boosted,
                False,
                True,
                "ICCP_UNDER_PROTECTION_HULL_CORROSION",
            )
        return IccpAssessment(
            IccpProtectionState.OPTIMAL_PASSIVATION,
            t.anode_current_amps,
            False,
            False,
            "NONE",
        )
