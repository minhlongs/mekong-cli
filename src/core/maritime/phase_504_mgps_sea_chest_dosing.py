"""Phase 504: Marine Growth Prevention System (MGPS) Sea Chest Electrolytic Dosing.
Complies with IACS UR M14 and ClassNK Sea Chest Anti-Fouling Safety Rules.
Strictly < 90 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class MgpsOperatingState(str, Enum):
    ACTIVE_ELECTROLYTIC_DOSING = "ACTIVE_ELECTROLYTIC_DOSING"
    LOW_FLOW_GAS_POCKET_CUTOFF = "LOW_FLOW_GAS_POCKET_CUTOFF"
    ANODE_DEPLETED_HIGH_VOLTAGE = "ANODE_DEPLETED_HIGH_VOLTAGE"


@dataclass(frozen=True)
class MgpsTelemetry:
    seawater_flow_m3_h: float
    copper_anode_amps: float
    aluminum_anode_amps: float
    cell_voltage_v: float = 8.5


@dataclass(frozen=True)
class MgpsAssessment:
    operating_state: MgpsOperatingState
    dosing_power_enabled: bool
    anode_replacement_required: bool
    alarm_active: bool
    alarm_code: str


class MgpsSeaChestDosingEngine:
    """Evaluates MGPS sea chest flow interlock and electrolytic Cu/Al anode health."""

    MIN_SEAWATER_FLOW_M3_H: float = 25.0
    MAX_CELL_VOLTAGE_V: float = 14.5

    @classmethod
    def evaluate(cls, t: MgpsTelemetry) -> MgpsAssessment:
        if t.seawater_flow_m3_h < cls.MIN_SEAWATER_FLOW_M3_H:
            return MgpsAssessment(
                MgpsOperatingState.LOW_FLOW_GAS_POCKET_CUTOFF,
                False,
                False,
                True,
                "MGPS_STAGNANT_SEACHEST_HYDROGEN_CUTOFF",
            )
        if t.cell_voltage_v > cls.MAX_CELL_VOLTAGE_V:
            return MgpsAssessment(
                MgpsOperatingState.ANODE_DEPLETED_HIGH_VOLTAGE,
                True,
                True,
                True,
                "MGPS_ANODE_PASSIVATION_OR_DEPLETION",
            )
        return MgpsAssessment(
            MgpsOperatingState.ACTIVE_ELECTROLYTIC_DOSING,
            True,
            False,
            False,
            "NONE",
        )
