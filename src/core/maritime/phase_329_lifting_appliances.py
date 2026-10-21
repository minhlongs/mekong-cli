"""Phase 329: Port Lifting Appliances & Cargo Handling Gear Engine.

Complies with ILO Convention 152, QCVN 23:2010/BGTVT (Safe Working Load proof
load test ratios), and ISO 4309 wire rope discard criteria.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List


@dataclass
class LiftingApplianceInput:
    equipment_id: str
    swl_tonnes: float  # Safe Working Load
    tested_proof_load_tonnes: float
    months_since_last_quadrennial_survey: int  # Max 60 months (5 years)
    months_since_last_annual_inspection: int  # Max 12 months
    wire_rope_nominal_diameter_mm: float
    wire_rope_measured_diameter_mm: float
    visible_broken_wires_in_lay_length: int
    max_allowed_broken_wires: int
    corrosion_pitting_severe: bool = False


@dataclass
class LiftingApplianceResult:
    certified_safe: bool
    calculated_proof_load_required_tonnes: float
    reasons: List[str]
    parameters: Dict[str, float]
    audit_trail_hash: str = field(default="")


class PortLiftingComplianceEngine:
    """Evaluates port lifting gear proof load and wire rope safety."""

    DIAMETER_DISCARD_PCT_THRESHOLD = 7.0

    @classmethod
    def calculate_proof_load(cls, swl: float) -> float:
        """ILO Convention 152 / QCVN 23:2010 proof load ratio calculation."""
        if swl <= 20.0:
            return round(1.25 * swl, 2)
        elif swl <= 50.0:
            return round(swl + 5.0, 2)
        else:
            return round(1.10 * swl, 2)

    @classmethod
    def evaluate(cls, inp: LiftingApplianceInput) -> LiftingApplianceResult:
        reasons: List[str] = []
        certified = True

        req_proof_load = cls.calculate_proof_load(inp.swl_tonnes)

        # 1. Proof load test check
        if inp.tested_proof_load_tonnes < req_proof_load:
            certified = False
            reasons.append(
                f"Tested proof load ({inp.tested_proof_load_tonnes}T) < required "
                f"statutory load ({req_proof_load}T) for SWL {inp.swl_tonnes}T"
            )

        # 2. Survey schedule checks
        if inp.months_since_last_annual_inspection > 12:
            certified = False
            reasons.append(
                f"Annual thorough examination overdue: {inp.months_since_last_annual_inspection} months (>12m)"
            )
        if inp.months_since_last_quadrennial_survey > 60:
            certified = False
            reasons.append(
                f"5-Year thorough survey & load test overdue: {inp.months_since_last_quadrennial_survey} months (>60m)"
            )

        # 3. ISO 4309 Wire rope discard criteria
        diameter_reduction_pct = (
            (inp.wire_rope_nominal_diameter_mm - inp.wire_rope_measured_diameter_mm)
            / inp.wire_rope_nominal_diameter_mm
        ) * 100.0

        if diameter_reduction_pct >= cls.DIAMETER_DISCARD_PCT_THRESHOLD:
            certified = False
            reasons.append(
                f"ISO 4309 Discard: Diameter reduction {diameter_reduction_pct:.2f}% "
                f"exceeds limit (>={cls.DIAMETER_DISCARD_PCT_THRESHOLD}%)"
            )

        if inp.visible_broken_wires_in_lay_length > inp.max_allowed_broken_wires:
            certified = False
            reasons.append(
                f"ISO 4309 Discard: Broken wires {inp.visible_broken_wires_in_lay_length} "
                f"exceeds allowable {inp.max_allowed_broken_wires}"
            )

        if inp.corrosion_pitting_severe:
            certified = False
            reasons.append("ISO 4309 Discard: Severe corrosion pitting detected")

        if certified:
            reasons.append(
                f"Equipment {inp.equipment_id} certified safe for SWL {inp.swl_tonnes}T"
            )

        params: Dict[str, float] = {
            "swl_tonnes": inp.swl_tonnes,
            "required_proof_load_tonnes": req_proof_load,
            "tested_proof_load_tonnes": inp.tested_proof_load_tonnes,
            "diameter_reduction_pct": round(diameter_reduction_pct, 2),
            "broken_wires": float(inp.visible_broken_wires_in_lay_length),
        }

        audit_src = json.dumps(
            {"id": inp.equipment_id, "certified": certified, "params": params},
            sort_keys=True,
        )
        audit_hash = hashlib.sha256(audit_src.encode("utf-8")).hexdigest()

        return LiftingApplianceResult(
            certified_safe=certified,
            calculated_proof_load_required_tonnes=req_proof_load,
            reasons=reasons,
            parameters=params,
            audit_trail_hash=audit_hash,
        )
