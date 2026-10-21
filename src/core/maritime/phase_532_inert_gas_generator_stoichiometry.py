from dataclasses import dataclass
from enum import Enum


class InertGasGeneratorState(str, Enum):
    OPTIMAL_INERT_DELIVERY = "OPTIMAL_INERT_DELIVERY"
    STOICHIOMETRY_TRIM_REQUIRED = "STOICHIOMETRY_TRIM_REQUIRED"
    HIGH_O2_QUALITY_ALARM = "HIGH_O2_QUALITY_ALARM"
    HIGH_HIGH_O2_VENT_TO_ATMOSPHERE_TRIP = "HIGH_HIGH_O2_VENT_TO_ATMOSPHERE_TRIP"
    SCRUBBER_HIGH_GAS_TEMP_SHUTDOWN = "SCRUBBER_HIGH_GAS_TEMP_SHUTDOWN"


@dataclass(frozen=True)
class InertGasGeneratorTelemetry:
    flue_gas_o2_pct: float
    scrubber_outlet_temp_c: float
    scrubber_cooling_water_bar: float
    air_fuel_equivalence_lambda: float


@dataclass(frozen=True)
class InertGasGeneratorAssessment:
    state: InertGasGeneratorState
    deck_main_isolation_valve_open: bool
    vent_to_atmosphere_open: bool
    burner_trip_active: bool
    interlock_code: str


class InertGasGeneratorStoichiometryEngine:
    """SOLAS II-2 Reg 4.5.5 & IMO FSS Code Ch. 15 Inert Gas Generator Supervision."""

    @classmethod
    def evaluate(cls, t: InertGasGeneratorTelemetry) -> InertGasGeneratorAssessment:
        if t.scrubber_outlet_temp_c > 65.0 or t.scrubber_cooling_water_bar < 1.5:
            return InertGasGeneratorAssessment(
                InertGasGeneratorState.SCRUBBER_HIGH_GAS_TEMP_SHUTDOWN,
                False,
                True,
                True,
                "FSS_CH15_IGG_SCRUBBER_OVERHEAT_TRIP",
            )
        if t.flue_gas_o2_pct >= 8.0:
            return InertGasGeneratorAssessment(
                InertGasGeneratorState.HIGH_HIGH_O2_VENT_TO_ATMOSPHERE_TRIP,
                False,
                True,
                False,
                "FSS_CH15_O2_OVER_8PCT_DECK_ISOLATION",
            )
        if t.flue_gas_o2_pct > 5.0:
            return InertGasGeneratorAssessment(
                InertGasGeneratorState.HIGH_O2_QUALITY_ALARM,
                True,
                False,
                False,
                "FSS_CH15_O2_OVER_5PCT_ALARM",
            )
        if not (0.95 <= t.air_fuel_equivalence_lambda <= 1.15):
            return InertGasGeneratorAssessment(
                InertGasGeneratorState.STOICHIOMETRY_TRIM_REQUIRED,
                True,
                False,
                False,
                "IGG_BURNER_AIR_FUEL_TRIM_WARN",
            )
        return InertGasGeneratorAssessment(
            InertGasGeneratorState.OPTIMAL_INERT_DELIVERY,
            True,
            False,
            False,
            "NONE",
        )
