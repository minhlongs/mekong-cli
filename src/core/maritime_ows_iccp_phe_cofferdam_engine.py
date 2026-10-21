"""Unified Facade for Maritime Phases 391-394.

Aggregates OWS 15 ppm, ICCP Cathodic Protection, Central Titanium PHE,
and Chemical Tanker Cofferdam Vapor Sniffing & Inerting.
Strictly zero mock dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.core.maritime.phase_391_oily_water_separator_ceramic import (
    OilyWaterSeparatorEngine,
    OilyWaterSeparatorInput,
    OilyWaterSeparatorResult,
)
from src.core.maritime.phase_392_iccp_cathodic_protection_shaft import (
    IccpCathodicProtectionEngine,
    IccpCathodicProtectionInput,
    IccpCathodicProtectionResult,
)
from src.core.maritime.phase_393_central_titanium_phe_ultrasonic import (
    CentralTitaniumPheEngine,
    CentralTitaniumPheInput,
    CentralTitaniumPheResult,
)
from src.core.maritime.phase_394_chemical_cofferdam_vapor_inerting import (
    ChemicalCofferdamEngine,
    ChemicalCofferdamInput,
    ChemicalCofferdamResult,
)


@dataclass
class MaritimeOwsIccpPheCofferdamResult:
    ows_result: OilyWaterSeparatorResult
    iccp_result: IccpCathodicProtectionResult
    phe_result: CentralTitaniumPheResult
    cofferdam_result: ChemicalCofferdamResult
    overall_maritime_status: str
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_maritime_status,
            "ows_bilge": {
                "oil_content_ppm": self.ows_result.oil_content_ppm,
                "discharge_permitted": self.ows_result.discharge_permitted,
                "alarm_status": self.ows_result.alarm_status,
                "three_way_valve": self.ows_result.three_way_valve_command,
                "membrane_fouling": self.ows_result.membrane_fouling_status,
                "regulatory": self.ows_result.regulatory_status,
            },
            "iccp_protection": {
                "hull_potential_mv": self.iccp_result.hull_potential_mv,
                "protection_status": self.iccp_result.protection_status,
                "shaft_status": self.iccp_result.shaft_grounding_status,
                "recommended_current_a": self.iccp_result.recommended_anode_current_a,
                "hydrogen_risk": self.iccp_result.hydrogen_embrittlement_risk,
                "corrosion_risk": self.iccp_result.corrosion_activity_risk,
            },
            "central_phe": {
                "heat_duty_kw": self.phe_result.heat_duty_kw,
                "lmtd_c": self.phe_result.lmtd_c,
                "thermal_status": self.phe_result.thermal_performance,
                "pressure_drop_status": self.phe_result.pressure_drop_status,
                "ultrasonic_biofilm": self.phe_result.ultrasonic_biofilm_prevention,
                "maintenance_action": self.phe_result.maintenance_action,
            },
            "chemical_cofferdam": {
                "safety_status": self.cofferdam_result.cofferdam_safety_status,
                "inerting_compliant": self.cofferdam_result.inerting_compliant,
                "pressure_barrier_intact": self.cofferdam_result.positive_pressure_intact,
                "n2_purge_required": self.cofferdam_result.nitrogen_purge_required,
                "cargo_breach_detected": self.cofferdam_result.chemical_breach_detected,
            },
            "total_warnings": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeOwsIccpPheCofferdamEngine:
    """Central engine orchestrating Maritime Phases 391-394."""

    def __init__(self):
        self.ows_engine = OilyWaterSeparatorEngine()
        self.iccp_engine = IccpCathodicProtectionEngine()
        self.phe_engine = CentralTitaniumPheEngine()
        self.cofferdam_engine = ChemicalCofferdamEngine()

    def evaluate(
        self,
        ows_inp: OilyWaterSeparatorInput = OilyWaterSeparatorInput(),
        iccp_inp: IccpCathodicProtectionInput = IccpCathodicProtectionInput(),
        phe_inp: CentralTitaniumPheInput = CentralTitaniumPheInput(),
        cofferdam_inp: ChemicalCofferdamInput = ChemicalCofferdamInput(),
    ) -> MaritimeOwsIccpPheCofferdamResult:
        ows_res = self.ows_engine.evaluate(ows_inp)
        iccp_res = self.iccp_engine.evaluate(iccp_inp)
        phe_res = self.phe_engine.evaluate(phe_inp)
        cofferdam_res = self.cofferdam_engine.evaluate(cofferdam_inp)

        all_warnings = (
            ows_res.warnings
            + iccp_res.warnings
            + phe_res.warnings
            + cofferdam_res.warnings
        )

        # Overall seaworthiness arbitration
        if (
            ows_res.alarm_status == "ALARM_15PPM_EXCEEDED"
            or cofferdam_res.cofferdam_safety_status == "CRITICAL_CHEMICAL_BREACH"
            or iccp_res.hydrogen_embrittlement_risk
        ):
            overall_status = "CRITICAL_HAZARD"
        elif (
            not ows_res.discharge_permitted
            or iccp_res.corrosion_activity_risk
            or iccp_res.shaft_grounding_status == "SPARK_EROSION_RISK"
            or phe_res.pressure_drop_status == "HIGH_PRESSURE_DROP_CLOGGED"
            or not cofferdam_res.inerting_compliant
        ):
            overall_status = "WARNING_SUB_OPTIMAL"
        else:
            overall_status = "NOMINAL_OPTIMAL"

        return MaritimeOwsIccpPheCofferdamResult(
            ows_result=ows_res,
            iccp_result=iccp_res,
            phe_result=phe_res,
            cofferdam_result=cofferdam_res,
            overall_maritime_status=overall_status,
            aggregated_warnings=all_warnings,
        )
