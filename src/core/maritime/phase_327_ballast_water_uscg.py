"""Phase 327: Advanced Ballast Water & Sediment Management Engine.

Complies with IMO BWM Convention Reg. D-2, USCG 46 CFR 162.060 (FDA/CMF viable
organism standard), and BWM Reg. B-5 sediment stripping and disposal.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List, Optional


@dataclass
class BallastWaterQualityInput:
    vessel_name: str
    bwms_type: str  # "UV" or "ELECTROCHLORINATION"
    standard_regime: str  # "IMO_D2" or "USCG_TYPE_APPROVAL"
    organisms_over_50um_per_m3: float  # Limit: < 10 viable / m3
    organisms_10_to_50um_per_ml: float  # Limit: < 10 viable / ml
    vibrio_cholerae_cfu_per_100ml: float  # Limit: < 1 cfu / 100ml
    ecoli_cfu_per_100ml: float  # Limit: < 250 cfu / 100ml
    enterococci_cfu_per_100ml: float  # Limit: < 100 cfu / 100ml
    uv_transmittance_pct: Optional[float] = None  # Minimum 50.0% for UV
    tro_discharge_mg_per_l: Optional[float] = None  # Neutralized <= 0.1 mg/L
    tro_neutralizer_applied: bool = False
    sediment_stripping_ratio_pct: float = 2.0  # Limit: < 5.0% of tank volume


@dataclass
class BallastWaterQualityResult:
    compliant: bool
    regime: str
    reasons: List[str]
    parameters: Dict[str, float]
    audit_trail_hash: str = field(default="")


class BallastWaterComplianceEngine:
    """Evaluates ballast water biological discharge and sediment management."""

    MAX_ORG_50UM = 10.0
    MAX_ORG_10_50UM = 10.0
    MAX_VIBRIO = 1.0
    MAX_ECOLI = 250.0
    MAX_ENTEROCOCCI = 100.0
    MIN_UVT_PCT = 50.0
    MAX_TRO_DISCHARGE_MG_L = 0.1
    MAX_SEDIMENT_STRIP_PCT = 5.0

    @classmethod
    def evaluate(cls, inp: BallastWaterQualityInput) -> BallastWaterQualityResult:
        reasons: List[str] = []
        is_compliant = True

        if inp.organisms_over_50um_per_m3 >= cls.MAX_ORG_50UM:
            is_compliant = False
            reasons.append(
                f"Viable organisms >=50um ({inp.organisms_over_50um_per_m3}/m3) "
                f"exceeds limit (<{cls.MAX_ORG_50UM}/m3)"
            )

        if inp.organisms_10_to_50um_per_ml >= cls.MAX_ORG_10_50UM:
            is_compliant = False
            reasons.append(
                f"Viable organisms 10-50um ({inp.organisms_10_to_50um_per_ml}/ml) "
                f"exceeds limit (<{cls.MAX_ORG_10_50UM}/ml)"
            )

        if inp.vibrio_cholerae_cfu_per_100ml >= cls.MAX_VIBRIO:
            is_compliant = False
            reasons.append(
                f"Vibrio cholerae ({inp.vibrio_cholerae_cfu_per_100ml} cfu) "
                f"exceeds limit (<{cls.MAX_VIBRIO} cfu/100ml)"
            )

        if inp.ecoli_cfu_per_100ml >= cls.MAX_ECOLI:
            is_compliant = False
            reasons.append(
                f"E. coli ({inp.ecoli_cfu_per_100ml} cfu) "
                f"exceeds limit (<{cls.MAX_ECOLI} cfu/100ml)"
            )

        if inp.enterococci_cfu_per_100ml >= cls.MAX_ENTEROCOCCI:
            is_compliant = False
            reasons.append(
                f"Enterococci ({inp.enterococci_cfu_per_100ml} cfu) "
                f"exceeds limit (<{cls.MAX_ENTEROCOCCI} cfu/100ml)"
            )

        # BWMS specific operational checks
        if inp.bwms_type.upper() == "UV":
            if inp.uv_transmittance_pct is not None and inp.uv_transmittance_pct < cls.MIN_UVT_PCT:
                is_compliant = False
                reasons.append(
                    f"UV Transmittance {inp.uv_transmittance_pct}% below operational threshold "
                    f"({cls.MIN_UVT_PCT}%)"
                )
        elif inp.bwms_type.upper() == "ELECTROCHLORINATION":
            if inp.tro_discharge_mg_per_l is not None:
                if inp.tro_discharge_mg_per_l > cls.MAX_TRO_DISCHARGE_MG_L:
                    if not inp.tro_neutralizer_applied:
                        is_compliant = False
                        reasons.append(
                            f"Residual TRO {inp.tro_discharge_mg_per_l} mg/L exceeds discharge limit "
                            f"({cls.MAX_TRO_DISCHARGE_MG_L} mg/L) without neutralizer"
                        )

        # Sediment stripping check
        if inp.sediment_stripping_ratio_pct >= cls.MAX_SEDIMENT_STRIP_PCT:
            is_compliant = False
            reasons.append(
                f"Sediment stripping ratio {inp.sediment_stripping_ratio_pct}% exceeds drydock "
                f"limit (<{cls.MAX_SEDIMENT_STRIP_PCT}%)"
            )

        if is_compliant:
            reasons.append(
                f"Ballast water complies with {inp.standard_regime} standards under {inp.bwms_type}"
            )

        params: Dict[str, float] = {
            "organisms_over_50um": inp.organisms_over_50um_per_m3,
            "organisms_10_50um": inp.organisms_10_to_50um_per_ml,
            "vibrio_cholerae": inp.vibrio_cholerae_cfu_per_100ml,
            "ecoli": inp.ecoli_cfu_per_100ml,
            "enterococci": inp.enterococci_cfu_per_100ml,
            "sediment_stripping_pct": inp.sediment_stripping_ratio_pct,
        }
        if inp.uv_transmittance_pct is not None:
            params["uv_transmittance_pct"] = inp.uv_transmittance_pct
        if inp.tro_discharge_mg_per_l is not None:
            params["tro_discharge_mg_l"] = inp.tro_discharge_mg_per_l

        audit_src = json.dumps(
            {"vessel": inp.vessel_name, "compliant": is_compliant, "params": params},
            sort_keys=True,
        )
        audit_hash = hashlib.sha256(audit_src.encode("utf-8")).hexdigest()

        return BallastWaterQualityResult(
            compliant=is_compliant,
            regime=inp.standard_regime,
            reasons=reasons,
            parameters=params,
            audit_trail_hash=audit_hash,
        )
