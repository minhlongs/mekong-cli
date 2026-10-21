"""Central Facade for Maritime Phases 367-370.

Unifies:
- Phase 367: Marine Fuel Oil Quality & ISO 8217 Compatibility
- Phase 368: Marine Battery Energy Storage System (BESS) Safety
- Phase 369: World Ports Environmental Ship Index (ESI) & Green Incentives
- Phase 370: Mooring Winch Auto-Tension & Active Heave Compensation (AHC)
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_367_fuel_oil_iso8217_compatibility import (
    FuelOilIso8217Engine,
    FuelQualityReport,
    FuelSampleInput,
    SpotTestRating,
)
from src.core.maritime.phase_368_marine_battery_bess_safety import (
    BessModuleInput,
    BessSafetyReport,
    BessSafetyTripStage,
    MarineBatteryBessEngine,
)
from src.core.maritime.phase_369_port_esi_green_incentive import (
    EsiEvaluationReport,
    EsiShipInput,
    GreenPortTier,
    PortEsiGreenIncentiveEngine,
)
from src.core.maritime.phase_370_mooring_autotension_ahc import (
    AutoTensionAhcReport,
    MooringAutoTensionAhcEngine,
    WinchActionState,
    WinchSensorInput,
)

__all__ = [
    "SpotTestRating",
    "FuelSampleInput",
    "FuelQualityReport",
    "FuelOilIso8217Engine",
    "BessSafetyTripStage",
    "BessModuleInput",
    "BessSafetyReport",
    "MarineBatteryBessEngine",
    "GreenPortTier",
    "EsiShipInput",
    "EsiEvaluationReport",
    "PortEsiGreenIncentiveEngine",
    "WinchActionState",
    "WinchSensorInput",
    "AutoTensionAhcReport",
    "MooringAutoTensionAhcEngine",
    "MaritimeMultiDomain367To370Report",
    "MaritimeFuelBessEsiAhcEngine",
]


@dataclass
class MaritimeMultiDomain367To370Report:
    overall_status: str
    fuel_report: FuelQualityReport
    bess_report: BessSafetyReport
    esi_report: EsiEvaluationReport
    mooring_report: AutoTensionAhcReport
    critical_alerts: List[str] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class MaritimeFuelBessEsiAhcEngine:
    """Unified Facade for Maritime Phases 367-370."""

    @classmethod
    def evaluate_fuel(cls, sample: FuelSampleInput) -> FuelQualityReport:
        return FuelOilIso8217Engine().evaluate(sample)

    @classmethod
    def evaluate_bess(cls, module: BessModuleInput) -> BessSafetyReport:
        return MarineBatteryBessEngine().evaluate(module)

    @classmethod
    def evaluate_esi(cls, ship: EsiShipInput) -> EsiEvaluationReport:
        return PortEsiGreenIncentiveEngine().evaluate(ship)

    @classmethod
    def evaluate_mooring(cls, sensor: WinchSensorInput) -> AutoTensionAhcReport:
        return MooringAutoTensionAhcEngine().evaluate(sensor)

    @classmethod
    def run_all(
        cls,
        fuel_sample: FuelSampleInput,
        bess_module: BessModuleInput,
        esi_ship: EsiShipInput,
        mooring_sensor: WinchSensorInput,
    ) -> MaritimeMultiDomain367To370Report:
        fuel_res = cls.evaluate_fuel(fuel_sample)
        bess_res = cls.evaluate_bess(bess_module)
        esi_res = cls.evaluate_esi(esi_ship)
        mooring_res = cls.evaluate_mooring(mooring_sensor)

        critical_alerts: List[str] = []
        if not fuel_res.is_compliant:
            critical_alerts.append(f"FUEL [{fuel_res.sample_id}]: {fuel_res.status} - Rủi ro hư hỏng động cơ/cháy nổ.")
        if not bess_res.is_safe:
            critical_alerts.append(f"BESS [{bess_res.pack_id}]: {bess_res.trip_stage.value} - Nguy cơ thoát nhiệt/chập cháy.")
        if mooring_res.action_state == WinchActionState.OVERLOAD_ALARM:
            critical_alerts.append(f"MOORING [{mooring_res.winch_id}]: Quá tải đứt cáp buộc tàu (>50% MBL).")

        if critical_alerts:
            overall_status = "CRITICAL"
        elif (
            fuel_res.warnings
            or bess_res.trip_stage != BessSafetyTripStage.STAGE_0_NORMAL
            or mooring_res.warnings
        ):
            overall_status = "WARNING"
        else:
            overall_status = "OPTIMAL"

        summary = {
            "fuel_flash_point_c": fuel_sample.flash_point_c,
            "bess_soc_pct": bess_module.soc_pct,
            "esi_total_score": esi_res.esi_total_score,
            "mooring_tension_kn": mooring_sensor.measured_tension_kn,
            "port_discount_pct": esi_res.port_dues_discount_pct,
        }

        return MaritimeMultiDomain367To370Report(
            overall_status=overall_status,
            fuel_report=fuel_res,
            bess_report=bess_res,
            esi_report=esi_res,
            mooring_report=mooring_res,
            critical_alerts=critical_alerts,
            summary_metrics=summary,
        )
