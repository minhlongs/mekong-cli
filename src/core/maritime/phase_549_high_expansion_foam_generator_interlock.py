from dataclasses import dataclass
from enum import Enum


class HighExpFoamGeneratorState(str, Enum):
    HIGH_EXP_FOAM_DISCHARGE_ACTIVE = "HIGH_EXP_FOAM_DISCHARGE_ACTIVE"
    OVERPRESSURE_RELIEF_DAMPER_MODULATING = "OVERPRESSURE_RELIEF_DAMPER_MODULATING"
    FOAM_MANIFOLD_OR_PROPORTIONER_RESERVE_CUTIN = "FOAM_MANIFOLD_OR_PROPORTIONER_RESERVE_CUTIN"
    QCV_OR_VENT_DAMPER_OPEN_DISCHARGE_LOCKOUT = "QCV_OR_VENT_DAMPER_OPEN_DISCHARGE_LOCKOUT"


@dataclass(frozen=True)
class HighExpFoamGeneratorTelemetry:
    foam_manifold_pressure_bar: float
    concentrate_ratio_pct: float
    space_backpressure_pa: float
    qcv_and_fire_dampers_closed: bool = True


@dataclass(frozen=True)
class HighExpFoamGeneratorAssessment:
    state: HighExpFoamGeneratorState
    foam_generator_valve_open: bool
    reserve_foam_pump_cut_in: bool
    overpressure_relief_damper_open: bool
    interlock_code: str


class HighExpansionFoamGeneratorEngine:
    """SOLAS II-2 Reg 10.4 & FSS Code Ch. 6 Fixed High-Expansion Foam Interlock."""

    @classmethod
    def evaluate(cls, t: HighExpFoamGeneratorTelemetry) -> HighExpFoamGeneratorAssessment:
        if not t.qcv_and_fire_dampers_closed:
            return HighExpFoamGeneratorAssessment(
                HighExpFoamGeneratorState.QCV_OR_VENT_DAMPER_OPEN_DISCHARGE_LOCKOUT,
                False,
                False,
                False,
                "FSS_CH6_QCV_OR_FIRE_DAMPER_OPEN_FOAM_LOCKOUT",
            )
        if t.foam_manifold_pressure_bar < 5.5 or not (1.8 <= t.concentrate_ratio_pct <= 2.5):
            return HighExpFoamGeneratorAssessment(
                HighExpFoamGeneratorState.FOAM_MANIFOLD_OR_PROPORTIONER_RESERVE_CUTIN,
                True,
                True,
                t.space_backpressure_pa > 150.0,
                "FSS_CH6_HIGH_EXP_FOAM_RESERVE_PUMP_CUTIN",
            )
        if t.space_backpressure_pa > 150.0:
            return HighExpFoamGeneratorAssessment(
                HighExpFoamGeneratorState.OVERPRESSURE_RELIEF_DAMPER_MODULATING,
                True,
                False,
                True,
                "SOLAS_II2_FOAM_SPACE_OVERPRESSURE_DAMPER_OPEN",
            )
        return HighExpFoamGeneratorAssessment(
            HighExpFoamGeneratorState.HIGH_EXP_FOAM_DISCHARGE_ACTIVE,
            True,
            False,
            False,
            "NONE",
        )
