"""Unified Facade for Maritime Propulsion, Auxiliary & Fire Safety (Phases 411-414).

Consolidates:
- Phase 411: ME Jacket Water Preheating & Thermostatic Cooling
- Phase 412: Main Starting Air Compressor & Unloader Relief
- Phase 413: Fixed High-Pressure CO2 Total Flooding Fire System
- Phase 414: Ro-Ro Bow Visor & Inner Door Hydraulic Latching
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, Any, List

from src.core.maritime.phase_411_jacket_water_preheating import (
    JacketWaterEngine,
    JacketWaterTelemetry,
    JacketWaterAssessment,
)
from src.core.maritime.phase_412_starting_air_compressor import (
    StartingAirCompressorEngine,
    AirCompressorTelemetry,
    AirCompressorAssessment,
)
from src.core.maritime.phase_413_fixed_co2_fire_extinguishing import (
    FixedCo2FireSystemEngine,
    Co2SystemTelemetry,
    Co2SystemAssessment,
)
from src.core.maritime.phase_414_roro_bow_door_latching import (
    RoRoBowDoorLatchingEngine,
    BowDoorTelemetry,
    BowDoorAssessment,
)


@dataclass(frozen=True)
class PropulsionFireSafetyFleetTelemetry:
    """Fleet-wide telemetry bundle across auxiliary propulsion and fire safety."""
    jacket_water: JacketWaterTelemetry
    air_compressor: AirCompressorTelemetry
    co2_fire_system: Co2SystemTelemetry
    bow_door: BowDoorTelemetry


@dataclass(frozen=True)
class PropulsionFireSafetyFleetAssessment:
    """Comprehensive safety and readiness status for vessel."""
    overall_status: str
    subsystem_assessments: Dict[str, Any]
    all_start_permissives_granted: bool
    sea_passage_ready: bool
    critical_alarms: List[str]


class MaritimePropulsionFireSafetyEngine:
    """Coordinates propulsion pre-start readiness, fire safety, and bow integrity."""

    def __init__(self) -> None:
        self.jw_engine = JacketWaterEngine()
        self.compressor_engine = StartingAirCompressorEngine()
        self.co2_engine = FixedCo2FireSystemEngine()
        self.bow_engine = RoRoBowDoorLatchingEngine()

    def evaluate_fleet(
        self, telemetry: PropulsionFireSafetyFleetTelemetry
    ) -> PropulsionFireSafetyFleetAssessment:
        jw_eval = self.jw_engine.evaluate(telemetry.jacket_water)
        comp_eval = self.compressor_engine.evaluate(telemetry.air_compressor)
        co2_eval = self.co2_engine.evaluate(telemetry.co2_fire_system)
        bow_eval = self.bow_engine.evaluate(telemetry.bow_door)

        critical_alarms: List[str] = []
        for name, sub_eval in [
            ("JW", jw_eval),
            ("Compressor", comp_eval),
            ("CO2", co2_eval),
            ("BowDoor", bow_eval),
        ]:
            if sub_eval.status == "CRITICAL":
                critical_alarms.extend([f"[{name}] {w}" for w in sub_eval.warnings])

        all_permissives = (
            jw_eval.start_permissive
            and bow_eval.navigation_permissive
            and comp_eval.compliance_flags["relief_pressure_safe"]
        )

        passage_ready = (
            all_permissives
            and co2_eval.status != "CRITICAL"
            and bow_eval.status == "NORMAL"
            and jw_eval.status in ("NORMAL", "ADVISORY")
        )

        overall_status = "NORMAL"
        if critical_alarms or bow_eval.water_ingress_alarm_level > 0:
            overall_status = "CRITICAL"
        elif any(
            e.status == "WARNING" for e in [jw_eval, comp_eval, co2_eval, bow_eval]
        ):
            overall_status = "WARNING"
        elif any(
            e.status == "ADVISORY" for e in [jw_eval, comp_eval, co2_eval, bow_eval]
        ):
            overall_status = "ADVISORY"

        return PropulsionFireSafetyFleetAssessment(
            overall_status=overall_status,
            subsystem_assessments={
                "phase_411_jacket_water": jw_eval,
                "phase_412_air_compressor": comp_eval,
                "phase_413_co2_fire_system": co2_eval,
                "phase_414_bow_door": bow_eval,
            },
            all_start_permissives_granted=all_permissives,
            sea_passage_ready=passage_ready,
            critical_alarms=critical_alarms,
        )
