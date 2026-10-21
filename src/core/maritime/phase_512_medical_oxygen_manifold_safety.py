"""Phase 512: Shipboard Hospital Medical Oxygen Manifold & Enrichment Leak Safety.
Complies with SOLAS II-1 and WHO/ILO International Medical Guide for Ships.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class MedicalGasState(str, Enum):
    DUTY_BANK_SUPPLYING = "DUTY_BANK_SUPPLYING"
    RESERVE_BANK_AUTO_CHANGEOVER = "RESERVE_BANK_AUTO_CHANGEOVER"
    LOW_DELIVERY_LINE_PRESSURE = "LOW_DELIVERY_LINE_PRESSURE"
    LOCKER_O2_ENRICHMENT_SHUTOFF = "LOCKER_O2_ENRICHMENT_SHUTOFF"


@dataclass(frozen=True)
class MedicalOxygenTelemetry:
    duty_cylinder_bar: float
    delivery_line_bar: float
    locker_ambient_o2_pct: float = 20.9


@dataclass(frozen=True)
class MedicalOxygenAssessment:
    gas_state: MedicalGasState
    reserve_bank_engaged: bool
    manifold_isolation_tripped: bool
    alarm_active: bool
    alarm_code: str


class MedicalOxygenManifoldSafetyEngine:
    """Evaluates hospital O2 cylinder changeover (< 35 bar), line pressure, and ambient O2 leak."""

    CHANGEOVER_BAR: float = 35.0
    MIN_LINE_BAR: float = 3.5
    MAX_AMBIENT_O2_PCT: float = 23.5

    @classmethod
    def evaluate(cls, t: MedicalOxygenTelemetry) -> MedicalOxygenAssessment:
        if t.locker_ambient_o2_pct >= cls.MAX_AMBIENT_O2_PCT:
            return MedicalOxygenAssessment(
                MedicalGasState.LOCKER_O2_ENRICHMENT_SHUTOFF,
                False,
                True,
                True,
                "MED_O2_LOCKER_ENRICHMENT_FIRE_HAZARD",
            )
        if t.delivery_line_bar < cls.MIN_LINE_BAR:
            return MedicalOxygenAssessment(
                MedicalGasState.LOW_DELIVERY_LINE_PRESSURE,
                True,
                False,
                True,
                "MED_O2_HOSPITAL_LINE_LOW_PRESSURE",
            )
        if t.duty_cylinder_bar < cls.CHANGEOVER_BAR:
            return MedicalOxygenAssessment(
                MedicalGasState.RESERVE_BANK_AUTO_CHANGEOVER,
                True,
                False,
                True,
                "MED_O2_DUTY_DEPLETED_RESERVE_ACTIVE",
            )
        return MedicalOxygenAssessment(
            MedicalGasState.DUTY_BANK_SUPPLYING,
            False,
            False,
            False,
            "NONE",
        )
