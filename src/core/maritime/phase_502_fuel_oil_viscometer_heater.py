"""Phase 502: Main Engine Fuel Oil Viscosity Viscometer & Steam Heater Control.
Complies with IACS UR M10 and ISO 8217 Marine Fuel Injection Standards.
Strictly < 90 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class ViscometerControlState(str, Enum):
    OPTIMAL_INJECTION_VISCOSITY = "OPTIMAL_INJECTION_VISCOSITY"
    THERMAL_RAMP_RATE_EXCEEDED = "THERMAL_RAMP_RATE_EXCEEDED"
    HIGH_VISCOSITY_BOOST_STEAM = "HIGH_VISCOSITY_BOOST_STEAM"
    LOW_VISCOSITY_LUBRICITY_ALARM = "LOW_VISCOSITY_LUBRICITY_ALARM"


@dataclass(frozen=True)
class FuelViscometerTelemetry:
    viscosity_cst: float
    fuel_temp_c: float
    temp_ramp_c_per_min: float
    steam_valve_opening_pct: float = 50.0


@dataclass(frozen=True)
class FuelViscometerAssessment:
    control_state: ViscometerControlState
    recommended_steam_valve_pct: float
    plunger_seizure_risk: bool
    alarm_active: bool
    alarm_code: str


class FuelOilViscometerHeaterEngine:
    """Evaluates HFO/MGO injection viscosity (12-15 cSt) and changeover thermal gradient."""

    MIN_VISCOSITY_CST: float = 10.0
    MAX_VISCOSITY_CST: float = 18.0
    MAX_RAMP_C_PER_MIN: float = 2.0

    @classmethod
    def evaluate(cls, t: FuelViscometerTelemetry) -> FuelViscometerAssessment:
        if abs(t.temp_ramp_c_per_min) > cls.MAX_RAMP_C_PER_MIN:
            return FuelViscometerAssessment(
                ViscometerControlState.THERMAL_RAMP_RATE_EXCEEDED,
                t.steam_valve_opening_pct,
                True,
                True,
                "FO_CHANGEOVER_THERMAL_SHOCK_RISK",
            )
        if t.viscosity_cst < cls.MIN_VISCOSITY_CST:
            new_valve = max(0.0, t.steam_valve_opening_pct - 20.0)
            return FuelViscometerAssessment(
                ViscometerControlState.LOW_VISCOSITY_LUBRICITY_ALARM,
                new_valve,
                True,
                True,
                "FO_LOW_VISCOSITY_LUBRICITY_WARNING",
            )
        if t.viscosity_cst > cls.MAX_VISCOSITY_CST:
            new_valve = min(100.0, t.steam_valve_opening_pct + 25.0)
            return FuelViscometerAssessment(
                ViscometerControlState.HIGH_VISCOSITY_BOOST_STEAM,
                new_valve,
                False,
                True,
                "FO_HIGH_VISCOSITY_POOR_ATOMIZATION",
            )
        return FuelViscometerAssessment(
            ViscometerControlState.OPTIMAL_INJECTION_VISCOSITY,
            t.steam_valve_opening_pct,
            False,
            False,
            "NONE",
        )
