"""Unified Facade for Maritime Phases 399-402.

Aggregates EGCS SOx Scrubber (MEPC.340(77)), Vacuum Fresh Water Generator (SOLAS II-1 Reg 26),
Deck Crane Anti-Sway & Dynamic SWL (ILO 152 / DNV-ST-0378), and UTM Hull Gauging (IACS UR Z10).
Strictly zero mock dependencies, < 180 LOC.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.core.maritime.phase_399_egcs_sox_wet_scrubber import (
    EgcsSoxScrubberEngine,
    EgcsScrubberInput,
    EgcsScrubberResult,
)
from src.core.maritime.phase_400_vacuum_fresh_water_generator import (
    VacuumFreshWaterGeneratorEngine,
    VacuumFwgInput,
    VacuumFwgResult,
)
from src.core.maritime.phase_401_deck_crane_anti_sway_swl import (
    DeckCraneAntiSwayEngine,
    DeckCraneInput,
    DeckCraneResult,
)
from src.core.maritime.phase_402_utm_hull_gauging_corrosion import (
    UtmHullGaugingEngine,
    UtmHullGaugingInput,
    UtmHullGaugingResult,
)


@dataclass
class MaritimeEgcsFwgCraneUtmResult:
    egcs_result: EgcsScrubberResult
    fwg_result: VacuumFwgResult
    crane_result: DeckCraneResult
    utm_result: UtmHullGaugingResult
    overall_seaworthiness_status: str
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_seaworthiness_status,
            "egcs_scrubber": {
                "emission_ratio": round(self.egcs_result.emission_ratio, 2),
                "compliant": self.egcs_result.mepc_340_77_compliant,
                "washwater_status": self.egcs_result.sox_washwater_status,
                "naoh_active": self.egcs_result.naoh_dosing_active,
                "discharge_lockout": self.egcs_result.discharge_lockout,
            },
            "fresh_water_generator": {
                "boiling_temp_c": round(self.fwg_result.evaporator_boiling_temp_c, 1),
                "purity_status": self.fwg_result.distillate_purity_status,
                "dump_valve": self.fwg_result.three_way_dump_valve,
                "thermal_efficiency_pct": round(self.fwg_result.thermal_efficiency_pct, 1),
                "potable_certified": self.fwg_result.potable_grade_certified,
            },
            "deck_crane": {
                "dynamic_swl_tonnes": round(self.crane_result.dynamic_swl_tonnes, 2),
                "load_moment_ton_m": round(self.crane_result.load_moment_ton_m, 2),
                "swl_utilization_pct": round(self.crane_result.swl_utilization_pct, 1),
                "sway_status": self.crane_result.anti_sway_dampening_status,
                "cutoff_active": self.crane_result.hoisting_safety_cutoff,
                "operation_status": self.crane_result.operation_status,
            },
            "utm_hull_gauging": {
                "wastage_pct": round(self.utm_result.wastage_pct, 1),
                "allowable_wastage_pct": self.utm_result.allowable_wastage_pct,
                "substantial_corrosion": self.utm_result.substantial_corrosion_detected,
                "renewal_required": self.utm_result.renewal_steel_required,
                "survey_recommendation": self.utm_result.survey_recommendation,
                "integrity_status": self.utm_result.structural_integrity_status,
            },
            "total_warnings": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeEgcsFwgCraneUtmEngine:
    """Unified Facade for EGCS Scrubber, Vacuum FWG, Deck Crane, and Hull UTM Gauging."""

    def __init__(self) -> None:
        self.egcs_engine = EgcsSoxScrubberEngine()
        self.fwg_engine = VacuumFreshWaterGeneratorEngine()
        self.crane_engine = DeckCraneAntiSwayEngine()
        self.utm_engine = UtmHullGaugingEngine()

    def evaluate(
        self,
        egcs_input: EgcsScrubberInput = None,
        fwg_input: VacuumFwgInput = None,
        crane_input: DeckCraneInput = None,
        utm_input: UtmHullGaugingInput = None,
    ) -> MaritimeEgcsFwgCraneUtmResult:
        egcs_inp = egcs_input or EgcsScrubberInput()
        fwg_inp = fwg_input or VacuumFwgInput()
        crane_inp = crane_input or DeckCraneInput()
        utm_inp = utm_input or UtmHullGaugingInput()

        egcs_res = self.egcs_engine.evaluate(egcs_inp)
        fwg_res = self.fwg_engine.evaluate(fwg_inp)
        crane_res = self.crane_engine.evaluate(crane_inp)
        utm_res = self.utm_engine.evaluate(utm_inp)

        warnings = []
        warnings.extend([f"[EGCS] {w}" for w in egcs_res.warnings])
        warnings.extend([f"[FWG] {w}" for w in fwg_res.warnings])
        warnings.extend([f"[CRANE] {w}" for w in crane_res.warnings])
        warnings.extend([f"[UTM] {w}" for w in utm_res.warnings])

        # Synthesize seaworthiness status
        if utm_res.renewal_steel_required or crane_res.hoisting_safety_cutoff:
            overall_status = "CRITICAL_SAFETY_HOLD"
        elif not egcs_res.mepc_340_77_compliant or not fwg_res.potable_grade_certified:
            overall_status = "OPERATIONAL_DEGRADED_COMPLIANCE_RISK"
        elif utm_res.substantial_corrosion_detected:
            overall_status = "CAUTION_SUBSTANTIAL_CORROSION_MONITORING"
        else:
            overall_status = "SEAWORTHY_OPTIMAL"

        return MaritimeEgcsFwgCraneUtmResult(
            egcs_result=egcs_res,
            fwg_result=fwg_res,
            crane_result=crane_res,
            utm_result=utm_res,
            overall_seaworthiness_status=overall_status,
            aggregated_warnings=warnings,
        )
