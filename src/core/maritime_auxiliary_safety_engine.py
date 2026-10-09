"""Unified Facade Engine for Maritime Auxiliary Safety Systems (Phases 407-410).

Combines:
- Phase 407: Marine Exhaust Gas Boiler (EGB) Economizer & Soot Blow Automation
- Phase 408: Marine Shaft Earthing & Hull Galvanic Potential Monitoring
- Phase 409: Cargo Hold Dew Point & Hold Ventilation Humidity Control
- Phase 410: Marine Emergency Diesel Generator (EDG) 45s Blackout Sequence

Strictly < 180 LOC, zero mocks, deterministic auxiliary safety monitoring.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_407_egb_economizer_soot_blow import (
    EgbEconomizerEngine,
    EgbEconomizerInput,
    EgbEconomizerResult,
    EgbEconomizerStatus,
)
from src.core.maritime.phase_408_shaft_earthing_galvanic import (
    ShaftEarthingEngine,
    ShaftEarthingInput,
    ShaftEarthingResult,
    ShaftEarthingStatus,
)
from src.core.maritime.phase_409_cargo_dewpoint_ventilation import (
    HoldPsychrometricInput,
    HoldPsychrometricResult,
    HoldVentilationEngine,
    HoldVentilationStatus,
)
from src.core.maritime.phase_410_emergency_generator_blackout import (
    EdgBlackoutEngine,
    EdgBlackoutInput,
    EdgBlackoutResult,
    EdgBlackoutStatus,
)


@dataclass
class MaritimeAuxiliarySafetyResult:
    """Consolidated assessment of vessel auxiliary safety and dead ship emergency readiness."""
    egb_economizer: EgbEconomizerResult
    shaft_earthing: ShaftEarthingResult
    hold_ventilation: HoldPsychrometricResult
    edg_blackout: EdgBlackoutResult
    overall_safety_status: str
    all_systems_green: bool
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_safety_status,
            "all_systems_green": self.all_systems_green,
            "egb_economizer": {
                "status": self.egb_economizer.status.value,
                "effectiveness": self.egb_economizer.heat_transfer_effectiveness,
                "soot_blow_recommended": self.egb_economizer.soot_blow_recommended,
                "soot_blow_permitted": self.egb_economizer.soot_blow_permitted,
                "soot_fire_risk": self.egb_economizer.soot_fire_risk_detected,
            },
            "shaft_earthing": {
                "status": self.shaft_earthing.status.value,
                "shaft_voltage_safe": self.shaft_earthing.shaft_voltage_safe,
                "brush_condition_safe": self.shaft_earthing.brush_condition_safe,
                "cathodic_potential_safe": self.shaft_earthing.cathodic_potential_safe,
                "bearing_spark_risk": self.shaft_earthing.bearing_spark_erosion_risk,
            },
            "hold_ventilation": {
                "status": self.hold_ventilation.status.value,
                "hold_dew_point_c": self.hold_ventilation.hold_dew_point_c,
                "outside_dew_point_c": self.hold_ventilation.outside_dew_point_c,
                "cargo_sweat_risk": self.hold_ventilation.cargo_sweat_risk,
                "ship_sweat_risk": self.hold_ventilation.ship_sweat_risk,
                "action": self.hold_ventilation.ventilation_action,
            },
            "edg_blackout": {
                "status": self.edg_blackout.status.value,
                "solas_45s_compliant": self.edg_blackout.solas_45s_compliant,
                "voltage_stabilized": self.edg_blackout.voltage_stabilized,
                "frequency_stabilized": self.edg_blackout.frequency_stabilized,
                "elapsed_time_sec": self.edg_blackout.elapsed_time_sec,
            },
            "warnings_count": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeAuxiliarySafetyEngine:
    """Unified orchestrator for marine waste heat, shaft grounding, hold air, and blackout recovery."""

    def __init__(self) -> None:
        self.egb_engine = EgbEconomizerEngine()
        self.shaft_engine = ShaftEarthingEngine()
        self.hold_engine = HoldVentilationEngine()
        self.edg_engine = EdgBlackoutEngine()

    def evaluate(
        self,
        egb_input: EgbEconomizerInput,
        shaft_input: ShaftEarthingInput,
        hold_input: HoldPsychrometricInput,
        edg_input: EdgBlackoutInput,
    ) -> MaritimeAuxiliarySafetyResult:
        egb_res = self.egb_engine.evaluate(egb_input)
        shaft_res = self.shaft_engine.evaluate(shaft_input)
        hold_res = self.hold_engine.evaluate(hold_input)
        edg_res = self.edg_engine.evaluate(edg_input)

        warnings: List[str] = (
            egb_res.warnings + shaft_res.warnings + hold_res.warnings + edg_res.warnings
        )

        critical_trips = (
            egb_res.soot_fire_risk_detected
            or shaft_res.bearing_spark_erosion_risk
            or not edg_res.starting_energy_sufficient
            or edg_res.status == EdgBlackoutStatus.OVER_TIME_SOLAS_VIOLATION
        )

        all_systems_green = (
            egb_res.status == EgbEconomizerStatus.NORMAL_HEAT_RECOVERY
            and shaft_res.status == ShaftEarthingStatus.OPTIMAL_PROTECTION
            and hold_res.status in (HoldVentilationStatus.MAINTAIN_SEALED, HoldVentilationStatus.VENTILATION_RECOMMENDED)
            and edg_res.status in (EdgBlackoutStatus.BLACKOUT_STANDBY, EdgBlackoutStatus.EMERGENCY_BUS_CONNECTED)
            and not critical_trips
        )

        if critical_trips:
            overall_status = "CRITICAL_AUXILIARY_SAFETY_ALERT"
        elif not all_systems_green:
            overall_status = "AUXILIARY_SAFETY_ATTENTION_REQUIRED"
        else:
            overall_status = "ALL_AUXILIARY_SAFETY_SYSTEMS_OPTIMAL"

        return MaritimeAuxiliarySafetyResult(
            egb_economizer=egb_res,
            shaft_earthing=shaft_res,
            hold_ventilation=hold_res,
            edg_blackout=edg_res,
            overall_safety_status=overall_status,
            all_systems_green=all_systems_green,
            aggregated_warnings=warnings,
        )
