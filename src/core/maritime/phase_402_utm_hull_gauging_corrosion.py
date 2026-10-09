"""Phase 402: Ultrasonic Thickness Measurement (UTM) Hull Gauging & Wastage Limits.

Compliant with IACS UR Z10.1/Z10.2 and IMO ESP Code.
Strictly < 200 LOC, zero external dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class HullPlateCategory(str, Enum):
    CATEGORY_A_STRENGTH_DECK_BOTTOM = "CATEGORY_A_STRENGTH_DECK_BOTTOM"
    CATEGORY_B_SIDE_SHELL_BULKHEAD = "CATEGORY_B_SIDE_SHELL_BULKHEAD"
    CATEGORY_C_INTERNAL_STIFFENER = "CATEGORY_C_INTERNAL_STIFFENER"


@dataclass
class UtmHullGaugingInput:
    plate_category: HullPlateCategory = HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM
    as_built_thickness_mm: float = 20.0
    actual_gauged_thickness_mm: float = 18.2
    pitting_depth_mm: float = 1.5
    pitting_density_pct: float = 4.0


@dataclass
class UtmHullGaugingResult:
    wastage_pct: float
    allowable_wastage_pct: float
    substantial_corrosion_detected: bool
    renewal_steel_required: bool
    survey_recommendation: str
    structural_integrity_status: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "wastage_pct": round(self.wastage_pct, 1),
            "allowable_wastage_pct": self.allowable_wastage_pct,
            "substantial_corrosion_detected": self.substantial_corrosion_detected,
            "renewal_steel_required": self.renewal_steel_required,
            "survey_recommendation": self.survey_recommendation,
            "structural_integrity_status": self.structural_integrity_status,
            "warnings": self.warnings,
        }


class UtmHullGaugingEngine:
    """Evaluates hull structural steel ultrasonic thickness measurements and corrosion limits."""

    LIMITS = {
        HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM: 15.0,  # Max 15% wastage
        HullPlateCategory.CATEGORY_B_SIDE_SHELL_BULKHEAD: 20.0,    # Max 20% wastage
        HullPlateCategory.CATEGORY_C_INTERNAL_STIFFENER: 25.0,    # Max 25% wastage
    }

    def evaluate(self, inp: UtmHullGaugingInput) -> UtmHullGaugingResult:
        warnings = []
        as_built = max(inp.as_built_thickness_mm, 1.0)
        wastage_mm = max(0.0, as_built - inp.actual_gauged_thickness_mm)
        wastage_pct = (wastage_mm / as_built) * 100.0

        allowable_limit = self.LIMITS.get(inp.plate_category, 20.0)

        # IACS Substantial Corrosion: Wastage >= 75% of allowable limit
        substantial_corrosion_threshold = 0.75 * allowable_limit
        substantial_corrosion = wastage_pct >= substantial_corrosion_threshold

        renewal_required = False
        if wastage_pct >= allowable_limit:
            renewal_required = True
            structural_status = "CRITICAL_STEEL_RENEWAL_MANDATORY"
            survey_recommendation = "IMMEDIATE_RENEWAL_PRIOR_TO_VOYAGE"
            warnings.append(
                f"IACS WASTAGE EXCEEDED: Wastage {wastage_pct:.1f}% exceeds maximum allowable {allowable_limit:.1f}%"
            )
        elif substantial_corrosion:
            structural_status = "SUBSTANTIAL_CORROSION_CLOSE_SURVEY"
            survey_recommendation = "MANDATORY_ANNUAL_INTERMEDIATE_REGAUGING"
            warnings.append(
                f"SUBSTANTIAL CORROSION: Wastage {wastage_pct:.1f}% >= 75% allowable ({substantial_corrosion_threshold:.1f}%)"
            )
        else:
            structural_status = "SATISFACTORY_ACCEPTABLE_MARGIN"
            survey_recommendation = "ROUTINE_SPECIAL_SURVEY_CYCLE"

        # Pitting corrosion check
        remaining_thickness = inp.actual_gauged_thickness_mm
        if inp.pitting_density_pct > 15.0 or (inp.pitting_depth_mm / max(remaining_thickness, 0.1)) > 0.50:
            structural_status = "CRITICAL_PITTING_DEFECT"
            renewal_required = True
            survey_recommendation = "STEEL_INSERT_OR_CLADDING_REPAIRS"
            warnings.append(
                f"LOCAL PITTING FAILURE: Pitting depth {inp.pitting_depth_mm:.1f}mm or density {inp.pitting_density_pct:.1f}% severe"
            )

        return UtmHullGaugingResult(
            wastage_pct=wastage_pct,
            allowable_wastage_pct=allowable_limit,
            substantial_corrosion_detected=substantial_corrosion,
            renewal_steel_required=renewal_required,
            survey_recommendation=survey_recommendation,
            structural_integrity_status=structural_status,
            warnings=warnings,
        )
