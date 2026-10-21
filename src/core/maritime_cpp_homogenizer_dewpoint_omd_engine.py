"""Master Facade Engine for Maritime Automation Phases 415-418.

Integrates:
- Phase 415: Propeller CPP & OD Box Hydraulics (DNV Pt.4 Ch.5, SOLAS II-1 Reg 28/31)
- Phase 416: Marine Fuel Homogenizer & Water Emulsification (MARPOL Annex VI, ISO 8217)
- Phase 417: Cargo Hold Dew Point & Desiccant Wheel (IMSBC Code, DNV Cargo Care)
- Phase 418: Crankcase Explosion Relief & Oil Mist Detector (SOLAS II-1 Reg 47, IACS M9/M10)

Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.core.maritime.phase_415_cpp_propeller_odbox_hydraulics import (
    CppPropellerTelemetry,
    CppPropellerAssessment,
    CppPropellerOdBoxEngine,
)
from src.core.maritime.phase_416_fuel_homogenizer_emulsion import (
    FuelHomogenizerTelemetry,
    FuelHomogenizerAssessment,
    FuelHomogenizerEmulsionEngine,
)
from src.core.maritime.phase_417_cargo_hold_dewpoint_desiccant import (
    CargoHoldDewPointTelemetry,
    CargoHoldDewPointAssessment,
    CargoHoldDewPointEngine,
)
from src.core.maritime.phase_418_crankcase_relief_oil_mist_detector import (
    CrankcaseOmdTelemetry,
    CrankcaseOmdAssessment,
    CrankcaseReliefOmdEngine,
)


@dataclass(frozen=True)
class MaritimePhases415to418Telemetry:
    """Consolidated telemetry for propulsion, fuel, cargo hold, and crankcase systems."""
    cpp_telemetry: CppPropellerTelemetry = field(default_factory=CppPropellerTelemetry)
    homogenizer_telemetry: FuelHomogenizerTelemetry = field(default_factory=FuelHomogenizerTelemetry)
    dewpoint_telemetry: CargoHoldDewPointTelemetry = field(default_factory=CargoHoldDewPointTelemetry)
    omd_telemetry: CrankcaseOmdTelemetry = field(default_factory=CrankcaseOmdTelemetry)


@dataclass(frozen=True)
class MaritimePhases415to418Assessment:
    """Consolidated holistic assessment for Phases 415-418."""
    cpp_propeller: CppPropellerAssessment
    fuel_homogenizer: FuelHomogenizerAssessment
    cargo_hold_dewpoint: CargoHoldDewPointAssessment
    crankcase_omd: CrankcaseOmdAssessment
    overall_safety_status: str
    combined_warnings: List[str]
    system_readiness_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpp_propeller": {
                "status": self.cpp_propeller.status,
                "advance_ratio_j": self.cpp_propeller.advance_ratio_j,
                "thrust_force_kn": self.cpp_propeller.thrust_force_kn,
                "odbox_leakage_lpm": self.cpp_propeller.odbox_seal_leakage_lpm,
                "pitch_error_deg": self.cpp_propeller.pitch_tracking_error_deg,
            },
            "fuel_homogenizer": {
                "status": self.fuel_homogenizer.status,
                "mean_water_droplet_um": self.fuel_homogenizer.mean_water_droplet_um,
                "calculated_viscosity_cst": self.fuel_homogenizer.calculated_viscosity_cst,
                "nox_reduction_pct": self.fuel_homogenizer.estimated_nox_reduction_pct,
                "micro_explosion_potential": self.fuel_homogenizer.micro_explosion_potential,
            },
            "cargo_hold_dewpoint": {
                "status": self.cargo_hold_dewpoint.status,
                "hold_dew_point_c": self.cargo_hold_dewpoint.hold_dew_point_c,
                "ship_sweat_margin_c": self.cargo_hold_dewpoint.ship_sweat_margin_c,
                "ventilation_rule": self.cargo_hold_dewpoint.ventilation_rule,
                "moisture_removal_rate_kg_h": self.cargo_hold_dewpoint.moisture_removal_rate_kg_h,
            },
            "crankcase_omd": {
                "status": self.crankcase_omd.status,
                "oil_mist_concentration_mg_l": self.crankcase_omd.oil_mist_concentration_mg_l,
                "lel_percentage": self.crankcase_omd.lel_percentage,
                "hotspot_temp_c": self.crankcase_omd.max_bearing_hotspot_temp_c,
                "engine_slowdown_required": self.crankcase_omd.engine_slowdown_required,
            },
            "overall_safety_status": self.overall_safety_status,
            "combined_warnings": self.combined_warnings,
            "system_readiness_pct": self.system_readiness_pct,
        }


class MaritimeCppHomogenizerDewpointOmdEngine:
    """Master coordinating engine for Maritime Phases 415-418."""

    def __init__(self) -> None:
        self.cpp_engine = CppPropellerOdBoxEngine()
        self.homogenizer_engine = FuelHomogenizerEmulsionEngine()
        self.dewpoint_engine = CargoHoldDewPointEngine()
        self.omd_engine = CrankcaseReliefOmdEngine()

    def evaluate(self, telemetry: MaritimePhases415to418Telemetry) -> MaritimePhases415to418Assessment:
        cpp_res = self.cpp_engine.evaluate(telemetry.cpp_telemetry)
        homo_res = self.homogenizer_engine.evaluate(telemetry.homogenizer_telemetry)
        dew_res = self.dewpoint_engine.evaluate(telemetry.dewpoint_telemetry)
        omd_res = self.omd_engine.evaluate(telemetry.omd_telemetry)

        all_warnings: List[str] = (
            [f"[CPP] {w}" for w in cpp_res.warnings]
            + [f"[HOMOGENIZER] {w}" for w in homo_res.warnings]
            + [f"[DEWPOINT] {w}" for w in dew_res.warnings]
            + [f"[OMD] {w}" for w in omd_res.warnings]
        )

        all_flags = list(cpp_res.compliance_flags.values()) + \
                    list(homo_res.compliance_flags.values()) + \
                    list(dew_res.compliance_flags.values()) + \
                    list(omd_res.compliance_flags.values())

        passed_count = sum(1 for f in all_flags if f)
        readiness_pct = (passed_count / len(all_flags)) * 100.0 if all_flags else 100.0

        if any(s == "CRITICAL" for s in (cpp_res.status, homo_res.status, dew_res.status, omd_res.status)):
            overall_status = "CRITICAL_ATTENTION_REQUIRED"
        elif any(s in ("WARNING", "FAILSAFE_ENGAGED") for s in (cpp_res.status, homo_res.status, dew_res.status, omd_res.status)):
            overall_status = "WARNING_OPERATIONAL"
        else:
            overall_status = "OPTIMAL_OPERATIONAL"

        return MaritimePhases415to418Assessment(
            cpp_propeller=cpp_res,
            fuel_homogenizer=homo_res,
            cargo_hold_dewpoint=dew_res,
            crankcase_omd=omd_res,
            overall_safety_status=overall_status,
            combined_warnings=all_warnings,
            system_readiness_pct=round(readiness_pct, 1),
        )
