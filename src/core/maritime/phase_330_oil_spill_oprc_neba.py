"""Phase 330: National Marine Oil Spill Response & NEBA Dispersant Engine.

Complies with OPRC 1990 Tier 1-3 classification, Net Environmental Benefit Analysis
(NEBA) chemical dispersant decision matrix, and containment boom/skimmer sizing.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List


@dataclass
class OilSpillIncidentInput:
    incident_id: str
    spill_volume_metric_tonnes: float
    water_depth_meters: float  # Limit: >= 10.0 m for dispersant
    distance_from_shore_nm: float  # Limit: >= 3.0 NM for dispersant
    oil_viscosity_cst: float  # Limit: < 10,000 cSt for dispersant
    vessel_length_overall_meters: float  # LOA
    current_velocity_knots: float
    skimmer_efficiency_factor: float = 0.75  # Typical 0.60 - 0.85
    slick_thickness_mm: float = 1.0


@dataclass
class OilSpillResponseResult:
    tier_classification: str  # "TIER_1", "TIER_2", "TIER_3"
    dispersant_permitted: bool
    required_boom_length_meters: float
    skimmer_recovery_rate_m3_per_hour: float
    reasons: List[str]
    parameters: Dict[str, float]
    audit_trail_hash: str = field(default="")


class MarineOilSpillResponseEngine:
    """Evaluates oil spill response tiers, NEBA dispersant, and equipment sizing."""

    MIN_DEPTH_DISPERSANT_M = 10.0
    MIN_DISTANCE_DISPERSANT_NM = 3.0
    MAX_VISCOSITY_DISPERSANT_CST = 10000.0

    @classmethod
    def classify_tier(cls, volume_mt: float) -> str:
        if volume_mt <= 20.0:
            return "TIER_1"
        elif volume_mt <= 500.0:
            return "TIER_2"
        else:
            return "TIER_3"

    @classmethod
    def evaluate(cls, inp: OilSpillIncidentInput) -> OilSpillResponseResult:
        reasons: List[str] = []
        tier = cls.classify_tier(inp.spill_volume_metric_tonnes)

        reasons.append(
            f"Incident classified as {tier} for {inp.spill_volume_metric_tonnes} MT spill"
        )

        # NEBA Dispersant Decision Matrix
        dispersant_ok = True
        if inp.water_depth_meters < cls.MIN_DEPTH_DISPERSANT_M:
            dispersant_ok = False
            reasons.append(
                f"Dispersant rejected: Water depth {inp.water_depth_meters}m < {cls.MIN_DEPTH_DISPERSANT_M}m"
            )

        if inp.distance_from_shore_nm < cls.MIN_DISTANCE_DISPERSANT_NM:
            dispersant_ok = False
            reasons.append(
                f"Dispersant rejected: Distance {inp.distance_from_shore_nm} NM < {cls.MIN_DISTANCE_DISPERSANT_NM} NM"
            )

        if inp.oil_viscosity_cst >= cls.MAX_VISCOSITY_DISPERSANT_CST:
            dispersant_ok = False
            reasons.append(
                f"Dispersant rejected: Oil viscosity {inp.oil_viscosity_cst} cSt >= {cls.MAX_VISCOSITY_DISPERSANT_CST} cSt"
            )

        if dispersant_ok:
            reasons.append("NEBA Approved: Chemical dispersant application permitted")

        # Containment & Recovery Engineering
        boom_length = round(3.0 * inp.vessel_length_overall_meters, 1)

        # Skimmer recovery rate: R = Efficiency * (speed_m_s * boom_swath * thickness)
        speed_m_s = inp.current_velocity_knots * 0.514444
        swath_width_m = min(boom_length * 0.33, 50.0)  # Effective swath
        thickness_m = inp.slick_thickness_mm / 1000.0
        encounter_m3_h = speed_m_s * swath_width_m * thickness_m * 3600.0
        recovery_m3_h = round(inp.skimmer_efficiency_factor * encounter_m3_h, 2)

        params: Dict[str, float] = {
            "spill_volume_mt": inp.spill_volume_metric_tonnes,
            "boom_length_m": boom_length,
            "skimmer_recovery_m3_h": recovery_m3_h,
            "water_depth_m": inp.water_depth_meters,
            "distance_shore_nm": inp.distance_from_shore_nm,
            "oil_viscosity_cst": inp.oil_viscosity_cst,
        }

        audit_src = json.dumps(
            {"id": inp.incident_id, "tier": tier, "dispersant": dispersant_ok, "params": params},
            sort_keys=True,
        )
        audit_hash = hashlib.sha256(audit_src.encode("utf-8")).hexdigest()

        return OilSpillResponseResult(
            tier_classification=tier,
            dispersant_permitted=dispersant_ok,
            required_boom_length_meters=boom_length,
            skimmer_recovery_rate_m3_per_hour=recovery_m3_h,
            reasons=reasons,
            parameters=params,
            audit_trail_hash=audit_hash,
        )
