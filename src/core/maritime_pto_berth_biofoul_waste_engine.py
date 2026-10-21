"""Central Facade for Maritime Phases 371-374.

Unifies:
- Phase 371: Shaft Generator PTO/PTI Hybrid Propulsion Engine
- Phase 372: Port Berth Allocation & Quay Crane Scheduling (BAP/QCSP)
- Phase 373: Marine Biofouling Risk Assessment & In-Water Cleaning
- Phase 374: Port Circular Waste Oil Recovery & Co-Processing Engine
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_371_shaft_generator_pto_pti import (
    ShaftGeneratorInput,
    ShaftGeneratorPtoPtiEngine,
    ShaftGeneratorPtoPtiReport,
    ShaftHybridMode,
)
from src.core.maritime.phase_372_port_berth_crane_bap_qcsp import (
    BerthAllocationReport,
    BerthAllocationStatus,
    BerthRequest,
    PortBerthCraneBapQcspEngine,
)
from src.core.maritime.phase_373_biofouling_hull_cleaning import (
    BiofoulingCleaningReport,
    BiofoulingHullCleaningEngine,
    BiofoulingInspection,
    CleaningPermission,
)
from src.core.maritime.phase_374_port_waste_oil_coprocessing import (
    PortWasteOilCoprocessingEngine,
    WasteOilBatch,
    WasteOilComplianceStatus,
    WasteOilCoprocessingReport,
)

__all__ = [
    "ShaftHybridMode",
    "ShaftGeneratorInput",
    "ShaftGeneratorPtoPtiReport",
    "ShaftGeneratorPtoPtiEngine",
    "BerthAllocationStatus",
    "BerthRequest",
    "BerthAllocationReport",
    "PortBerthCraneBapQcspEngine",
    "CleaningPermission",
    "BiofoulingInspection",
    "BiofoulingCleaningReport",
    "BiofoulingHullCleaningEngine",
    "WasteOilComplianceStatus",
    "WasteOilBatch",
    "WasteOilCoprocessingReport",
    "PortWasteOilCoprocessingEngine",
    "MaritimeMultiDomain371To374Report",
    "MaritimePtoBerthBiofoulWasteEngine",
]


@dataclass
class MaritimeMultiDomain371To374Report:
    overall_status: str
    pto_report: ShaftGeneratorPtoPtiReport
    berth_report: BerthAllocationReport
    biofoul_report: BiofoulingCleaningReport
    waste_oil_report: WasteOilCoprocessingReport
    critical_alerts: List[str] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class MaritimePtoBerthBiofoulWasteEngine:
    """Unified Facade for Maritime Phases 371-374."""

    @classmethod
    def evaluate_pto(
        cls, inp: ShaftGeneratorInput
    ) -> ShaftGeneratorPtoPtiReport:
        return ShaftGeneratorPtoPtiEngine().evaluate(inp)

    @classmethod
    def evaluate_berth(cls, req: BerthRequest) -> BerthAllocationReport:
        return PortBerthCraneBapQcspEngine().evaluate(req)

    @classmethod
    def evaluate_biofouling(
        cls, insp: BiofoulingInspection
    ) -> BiofoulingCleaningReport:
        return BiofoulingHullCleaningEngine().evaluate(insp)

    @classmethod
    def evaluate_waste_oil(
        cls, batch: WasteOilBatch
    ) -> WasteOilCoprocessingReport:
        return PortWasteOilCoprocessingEngine().evaluate(batch)

    @classmethod
    def run_all(
        cls,
        pto_input: ShaftGeneratorInput,
        berth_req: BerthRequest,
        biofoul_insp: BiofoulingInspection,
        waste_batch: WasteOilBatch,
    ) -> MaritimeMultiDomain371To374Report:
        pto_res = cls.evaluate_pto(pto_input)
        berth_res = cls.evaluate_berth(berth_req)
        biofoul_res = cls.evaluate_biofouling(biofoul_insp)
        waste_res = cls.evaluate_waste_oil(waste_batch)

        alerts: List[str] = []
        alerts.extend(pto_res.warnings)
        alerts.extend(berth_res.warnings)
        alerts.extend(biofoul_res.warnings)
        alerts.extend(waste_res.warnings)

        # Overall status calculation
        is_critical = (
            not pto_res.is_pto_permitted and pto_input.requested_mode == ShaftHybridMode.PTO
            or berth_res.status == BerthAllocationStatus.CRANE_INTERFERENCE_VIOLATION
            or biofoul_res.permission in (
                CleaningPermission.DRYDOCK_MANDATORY,
                CleaningPermission.PROHIBITED_INADEQUATE_FILTER,
            )
            or not waste_res.is_safe_to_receive
        )

        overall_status = "CRITICAL_ACTION_REQUIRED" if is_critical else "OPTIMAL_OPERATIONAL"

        summary = {
            "pto_savings_kg_per_h": pto_res.fuel_savings_kg_per_h,
            "pto_co2_reduction_kg_per_h": pto_res.co2_reduction_kg_per_h,
            "berth_turnaround_hours": berth_res.estimated_turnaround_hours,
            "biofoul_power_penalty_pct": biofoul_res.power_penalty_pct,
            "waste_recovered_rfo_tonnes": waste_res.recovered_fuel_oil_tonnes,
            "waste_co2_offset_tonnes": waste_res.co2_offset_tonnes,
        }

        return MaritimeMultiDomain371To374Report(
            overall_status=overall_status,
            pto_report=pto_res,
            berth_report=berth_res,
            biofoul_report=biofoul_res,
            waste_oil_report=waste_res,
            critical_alerts=alerts,
            summary_metrics=summary,
        )
