"""Phase 334: Hull & Machinery (H&M) Marine Casualty Damage Survey.

Calculates Particular Average (PA), General Average (GA) apportionment,
contractual policy deductibles, and customary "New for Old" depreciation.
Kept strictly under 200 lines according to KISS/YAGNI principles.
"""

from dataclasses import dataclass
from typing import Dict
import hashlib
import json


@dataclass
class HmDamageSurveyInput:
    incident_id: str
    vessel_name: str
    insured_hull_value_usd: float
    deductible_usd: float
    particular_average_repair_usd: float  # Tổn thất riêng thân vỏ/máy
    general_average_sacrifice_usd: float  # Hy sinh tổn thất chung
    salvage_award_usd: float = 0.0  # Chi phí cứu hộ
    surveyor_fee_usd: float = 0.0
    vessel_age_years: int = 5
    new_for_old_deduction_applicable: bool = False  # Trừ khấu hao phụ tùng thay mới


@dataclass
class HmClaimAssessmentResult:
    incident_id: str
    vessel_name: str
    gross_adjusted_loss_usd: float
    new_for_old_depreciation_usd: float
    net_claim_before_deductible_usd: float
    applied_deductible_usd: float
    net_insurers_payable_usd: float
    is_constructive_total_loss: bool  # CTL: tổn thất >= 80% giá trị bảo hiểm
    claim_summary: Dict[str, float]
    audit_hash: str


class HmDamageSurveyEngine:
    CTL_RATIO_THRESHOLD = 0.80  # 80% Insured Value constitutes CTL

    @classmethod
    def calculate_depreciation(cls, repair_cost: float, age_years: int, applicable: bool) -> float:
        if not applicable:
            return 0.0
        # Institute Time Clauses "New for Old" sliding scale
        if age_years <= 5:
            return 0.0
        elif age_years <= 10:
            return round(repair_cost * 0.15, 2)  # 15% deduction
        elif age_years <= 15:
            return round(repair_cost * 0.25, 2)  # 25% deduction
        return round(repair_cost * 0.33, 2)  # 1/3 (33%) deduction

    @classmethod
    def evaluate(cls, inp: HmDamageSurveyInput) -> HmClaimAssessmentResult:
        gross_loss = round(
            inp.particular_average_repair_usd
            + inp.general_average_sacrifice_usd
            + inp.salvage_award_usd
            + inp.surveyor_fee_usd,
            2,
        )

        depreciation = cls.calculate_depreciation(
            inp.particular_average_repair_usd,
            inp.vessel_age_years,
            inp.new_for_old_deduction_applicable,
        )

        net_before_deductible = round(gross_loss - depreciation, 2)
        applied_deductible = min(net_before_deductible, inp.deductible_usd)
        net_payable = max(0.0, round(net_before_deductible - applied_deductible, 2))

        # Check for Constructive Total Loss (CTL)
        is_ctl = gross_loss >= (inp.insured_hull_value_usd * cls.CTL_RATIO_THRESHOLD)

        summary = {
            "particular_average_usd": inp.particular_average_repair_usd,
            "general_average_sacrifice_usd": inp.general_average_sacrifice_usd,
            "salvage_award_usd": inp.salvage_award_usd,
            "surveyor_fee_usd": inp.surveyor_fee_usd,
            "depreciation_deducted_usd": depreciation,
            "policy_deductible_usd": applied_deductible,
            "net_indemnity_payable_usd": net_payable,
        }

        # Tamper-evident audit hash
        audit_payload = {
            "incident_id": inp.incident_id,
            "vessel": inp.vessel_name,
            "gross_loss": gross_loss,
            "net_payable": net_payable,
            "is_ctl": is_ctl,
            "summary": summary,
        }
        audit_hash = hashlib.sha256(
            json.dumps(audit_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return HmClaimAssessmentResult(
            incident_id=inp.incident_id,
            vessel_name=inp.vessel_name,
            gross_adjusted_loss_usd=gross_loss,
            new_for_old_depreciation_usd=depreciation,
            net_claim_before_deductible_usd=net_before_deductible,
            applied_deductible_usd=applied_deductible,
            net_insurers_payable_usd=net_payable,
            is_constructive_total_loss=is_ctl,
            claim_summary=summary,
            audit_hash=audit_hash,
        )
