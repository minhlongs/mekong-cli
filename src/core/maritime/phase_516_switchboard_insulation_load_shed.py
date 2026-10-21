"""Phase 516: Main Switchboard Earth Fault Insulation & Preferential Load Shedding.
Complies with SOLAS II-1 Reg 41 and IACS UR E11 Electrical Distribution Rules.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class SwitchboardBusState(str, Enum):
    HEALTHY_BUS_DISTRIBUTION = "HEALTHY_BUS_DISTRIBUTION"
    EARTH_FAULT_INSULATION_WARN = "EARTH_FAULT_INSULATION_WARN"
    CRITICAL_GROUND_FAULT_ALARM = "CRITICAL_GROUND_FAULT_ALARM"
    PREFERENTIAL_TRIP_STAGE_1_SHED = "PREFERENTIAL_TRIP_STAGE_1_SHED"
    PREFERENTIAL_TRIP_STAGE_2_SHED = "PREFERENTIAL_TRIP_STAGE_2_SHED"


@dataclass(frozen=True)
class SwitchboardTelemetry:
    insulation_mohm: float
    generator_load_pct: float
    overload_duration_sec: float = 0.0


@dataclass(frozen=True)
class SwitchboardAssessment:
    bus_state: SwitchboardBusState
    non_essential_loads_shed: bool
    earth_fault_beacon_on: bool
    alarm_active: bool
    alarm_code: str


class SwitchboardInsulationLoadShedEngine:
    """Evaluates bus insulation resistance (MOhm) and preferential overload shedding."""

    CRITICAL_INSULATION_MOHM: float = 0.05
    WARN_INSULATION_MOHM: float = 0.20
    STAGE_1_LOAD_PCT: float = 100.0
    STAGE_2_LOAD_PCT: float = 110.0

    @classmethod
    def evaluate(cls, t: SwitchboardTelemetry) -> SwitchboardAssessment:
        if t.generator_load_pct >= cls.STAGE_2_LOAD_PCT and t.overload_duration_sec >= 5.0:
            return SwitchboardAssessment(
                SwitchboardBusState.PREFERENTIAL_TRIP_STAGE_2_SHED,
                True,
                False,
                True,
                "MSB_PREFERENTIAL_TRIP_STAGE2_DECK_SHED",
            )
        if t.generator_load_pct > cls.STAGE_1_LOAD_PCT and t.overload_duration_sec >= 5.0:
            return SwitchboardAssessment(
                SwitchboardBusState.PREFERENTIAL_TRIP_STAGE_1_SHED,
                True,
                False,
                True,
                "MSB_PREFERENTIAL_TRIP_STAGE1_GALLEY_HVAC_SHED",
            )
        if t.insulation_mohm <= cls.CRITICAL_INSULATION_MOHM:
            return SwitchboardAssessment(
                SwitchboardBusState.CRITICAL_GROUND_FAULT_ALARM,
                False,
                True,
                True,
                "MSB_CRITICAL_EARTH_FAULT_BELOW_50KOHM",
            )
        if t.insulation_mohm <= cls.WARN_INSULATION_MOHM:
            return SwitchboardAssessment(
                SwitchboardBusState.EARTH_FAULT_INSULATION_WARN,
                False,
                True,
                True,
                "MSB_LOW_INSULATION_EARTH_FAULT_WARNING",
            )
        return SwitchboardAssessment(
            SwitchboardBusState.HEALTHY_BUS_DISTRIBUTION,
            False,
            False,
            False,
            "NONE",
        )
