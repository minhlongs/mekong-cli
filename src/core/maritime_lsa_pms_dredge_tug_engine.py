"""Central Facade for Maritime Phases 363-366.

Unifies:
- Phase 363: LSA Free-Fall Lifeboat & Hydrostatic Release Unit (HRU)
- Phase 364: Marine Generator PMS & Blackout Prevention
- Phase 365: Port Dredging Sediment Quality & Beneficial Reuse
- Phase 366: OCIMF OVID Tug Vetting & Towing Winch Safety
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_363_lsa_lifeboat_hru_release import (
    LifeboatHruEngine,
    LifeboatHruInput,
    LifeboatHruReleaseEngine,
    LifeboatHruResult,
)
from src.core.maritime.phase_364_marine_generator_pms_blackout import (
    MarineGeneratorPmsEngine,
    MarineGeneratorUnit,
    PmsEvaluationInput,
    PmsEvaluationResult,
)
from src.core.maritime.phase_365_dredging_sediment_beneficiation import (
    DredgedSedimentInput,
    DredgingSedimentBeneficiationEngine,
    SedimentReuseResult,
)
from src.core.maritime.phase_366_ovid_tug_winch_vetting import (
    OvidTugWinchVettingEngine,
    TugVettingInput,
    TugVettingResult,
)

__all__ = [
    "LifeboatHruEngine",
    "LifeboatHruInput",
    "LifeboatHruReleaseEngine",
    "LifeboatHruResult",
    "MarineGeneratorPmsEngine",
    "MarineGeneratorUnit",
    "PmsEvaluationInput",
    "PmsEvaluationResult",
    "DredgedSedimentInput",
    "DredgingSedimentBeneficiationEngine",
    "SedimentReuseResult",
    "OvidTugWinchVettingEngine",
    "TugVettingInput",
    "TugVettingResult",
    "MaritimeMultiDomain363To366Report",
    "MaritimeLsaPmsDredgeTugEngine",
]


@dataclass
class MaritimeMultiDomain363To366Report:
    overall_risk_level: str
    lifeboat_result: LifeboatHruResult
    pms_result: PmsEvaluationResult
    sediment_result: SedimentReuseResult
    tug_vetting_result: TugVettingResult
    critical_alerts: List[str] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class MaritimeLsaPmsDredgeTugEngine:
    """Unified Facade for Maritime Operations & Safety Phases 363-366."""

    @classmethod
    def evaluate_lifeboat(cls, inp: LifeboatHruInput) -> LifeboatHruResult:
        return LifeboatHruReleaseEngine.evaluate(inp)

    @classmethod
    def evaluate_pms(cls, inp: PmsEvaluationInput) -> PmsEvaluationResult:
        return MarineGeneratorPmsEngine.evaluate(inp)

    @classmethod
    def evaluate_sediment(cls, inp: DredgedSedimentInput) -> SedimentReuseResult:
        return DredgingSedimentBeneficiationEngine.evaluate(inp)

    @classmethod
    def evaluate_tug_vetting(cls, inp: TugVettingInput) -> TugVettingResult:
        return OvidTugWinchVettingEngine.evaluate(inp)

    @classmethod
    def run_all(
        cls,
        lifeboat_inp: LifeboatHruInput,
        pms_inp: PmsEvaluationInput,
        sediment_inp: DredgedSedimentInput,
        tug_inp: TugVettingInput,
    ) -> MaritimeMultiDomain363To366Report:
        lb_res = cls.evaluate_lifeboat(lifeboat_inp)
        pms_res = cls.evaluate_pms(pms_inp)
        sed_res = cls.evaluate_sediment(sediment_inp)
        tug_res = cls.evaluate_tug_vetting(tug_inp)

        critical_alerts: List[str] = []
        if not lb_res.is_safe_to_launch_or_float:
            critical_alerts.append(f"LIFEBOAT [{lb_res.boat_id}]: {lb_res.safety_status}")
        if pms_res.blackout_risk_status == "EMERGENCY_BLACKOUT_TRIP":
            critical_alerts.append("PMS: Nguy cơ Blackout lưới điện tàu - Rơ le ngắt khẩn cấp.")
        if sed_res.sediment_class == "CLASS_3_HAZARDOUS":
            critical_alerts.append(f"SEDIMENT [{sed_res.batch_id}]: Độc tính nặng TBT/Kim loại nặng - Cấm đổ biển.")
        if tug_res.overall_vetting_status == "OVID_REJECTED_EQUIPMENT_DEFECT":
            critical_alerts.append(f"TUG [{tug_res.tug_id}]: Không đạt kiểm định tời kéo/phanh OCIMF OVID.")

        if critical_alerts:
            overall_risk = "CRITICAL"
        elif (
            lb_res.safety_status == "WARNING_RESTRICTED"
            or pms_res.shedding_stage > 0
            or not sed_res.is_beneficial_reuse_approved
            or tug_res.overall_vetting_status != "OVID_APPROVED_SUITABLE"
        ):
            overall_risk = "WARNING"
        else:
            overall_risk = "COMPLIANT"

        metrics = {
            "lifeboat_accel_g": lifeboat_inp.peak_acceleration_g,
            "pms_total_load_pct": pms_res.total_load_pct,
            "sediment_ucs_kpa": sediment_inp.stabilized_ucs_kpa,
            "tug_brake_hold_pct": tug_res.brake_hold_ratio_pct,
        }

        return MaritimeMultiDomain363To366Report(
            overall_risk_level=overall_risk,
            lifeboat_result=lb_res,
            pms_result=pms_res,
            sediment_result=sed_res,
            tug_vetting_result=tug_res,
            critical_alerts=critical_alerts,
            summary_metrics=metrics,
        )
