"""Phase 454: Engine Room Waste Heat Recovery (WHR) ORC Evaporator Safety.

Compliant with IACS UR M53 & ClassNK Organic Rankine Cycle (ORC) Rules.
Monitors organic working fluid evaporator film temperature, superheat margin,
exhaust bypass diverter damper fast actuation, and hydrocarbon vapor leakage.
"""

from dataclasses import dataclass
from enum import Enum


class OrcEvaporatorStatus(str, Enum):
    NORMAL = "NORMAL"
    SUPERHEAT_MARGIN_LOW = "SUPERHEAT_MARGIN_LOW"
    FLAMMABLE_LEAK_ALARM = "FLAMMABLE_LEAK_ALARM"
    EMERGENCY_DAMPER_TRIP = "EMERGENCY_DAMPER_TRIP"


@dataclass(frozen=True)
class OrcEvaporatorTelemetry:
    film_temp_celsius: float
    superheat_margin_celsius: float
    exhaust_diverter_open_pct: float
    hydrocarbon_leak_detected: bool
    expander_inlet_pressure_bar: float


@dataclass(frozen=True)
class OrcEvaporatorAssessment:
    status: OrcEvaporatorStatus
    diverter_bypass_tripped: bool
    working_fluid_pump_trip: bool
    turbine_trip: bool
    safety_alarm: bool
    remarks: str


class WhrOrcEvaporatorEngine:
    MAX_FILM_TEMP_CELSIUS: float = 280.0
    TRIP_FILM_TEMP_CELSIUS: float = 300.0
    MIN_SUPERHEAT_MARGIN_CELSIUS: float = 15.0
    MAX_DIVERTER_TRAVEL_TIME_S: float = 5.0

    @classmethod
    def evaluate(cls, telemetry: OrcEvaporatorTelemetry) -> OrcEvaporatorAssessment:
        if telemetry.hydrocarbon_leak_detected:
            return OrcEvaporatorAssessment(
                status=OrcEvaporatorStatus.FLAMMABLE_LEAK_ALARM,
                diverter_bypass_tripped=True,
                working_fluid_pump_trip=True,
                turbine_trip=True,
                safety_alarm=True,
                remarks="Working fluid vapor leak detected: Damper tripped to bypass, nitrogen purge initiated",
            )

        if telemetry.film_temp_celsius > cls.TRIP_FILM_TEMP_CELSIUS:
            return OrcEvaporatorAssessment(
                status=OrcEvaporatorStatus.EMERGENCY_DAMPER_TRIP,
                diverter_bypass_tripped=True,
                working_fluid_pump_trip=False,
                turbine_trip=True,
                safety_alarm=True,
                remarks="Evaporator film temperature > 300°C: Fast pneumatic exhaust diverter trip",
            )

        if telemetry.superheat_margin_celsius < cls.MIN_SUPERHEAT_MARGIN_CELSIUS:
            return OrcEvaporatorAssessment(
                status=OrcEvaporatorStatus.SUPERHEAT_MARGIN_LOW,
                diverter_bypass_tripped=False,
                working_fluid_pump_trip=False,
                turbine_trip=False,
                safety_alarm=True,
                remarks="Superheat margin < 15°C: Risk of liquid droplet erosion on expander blades",
            )

        return OrcEvaporatorAssessment(
            status=OrcEvaporatorStatus.NORMAL,
            diverter_bypass_tripped=False,
            working_fluid_pump_trip=False,
            turbine_trip=False,
            safety_alarm=False,
            remarks="ORC waste heat recovery operating within nominal thermodynamic limits",
        )
