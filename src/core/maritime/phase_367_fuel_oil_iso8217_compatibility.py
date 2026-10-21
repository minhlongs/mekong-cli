"""Marine Fuel Oil Quality Assessment & ISO 8217 Compatibility Engine.

Standards: ISO 8217:2024, CIMAC Guidelines, MARPOL Annex VI Reg 14/18,
ASTM D4740 Spot Test, and SOLAS II-2/Reg 4.2.1.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class SpotTestRating(str, Enum):
    """ASTM D4740 spot test compatibility rating (1 to 5)."""

    EXCELLENT = "1"
    GOOD = "2"
    BORDERLINE = "3"
    POOR = "4"
    VERY_POOR = "5"


@dataclass
class FuelSampleInput:
    sample_id: str
    fuel_grade: str  # e.g., "VLSFO", "HSFO", "MGO", "RMG 380"
    al_plus_si_mg_kg: float
    flash_point_c: float
    viscosity_at_50c_cst: float = 180.0
    total_sediment_potential_pct: float = 0.04
    sulfur_pct: float = 0.48
    spot_test_rating: SpotTestRating = SpotTestRating.GOOD
    target_injection_viscosity_cst: float = 12.0


@dataclass
class FuelQualityReport:
    sample_id: str
    is_compliant: bool
    status: str
    cat_fines_status: str
    flash_point_status: str
    sediment_status: str
    compatibility_status: str
    recommended_preheat_temp_c: float
    warnings: List[str]
    metrics: Dict[str, float]


class FuelOilIso8217Engine:
    """Evaluates marine bunker fuel quality and compatibility."""

    MAX_AL_PLUS_SI_PPM: float = 60.0  # ISO 8217 statutory limit
    CIMAC_CAT_FINES_ALERT_PPM: float = 25.0  # Safe engine inlet limit
    MIN_FLASH_POINT_C: float = 60.0  # SOLAS II-2 threshold
    MAX_TSP_PCT: float = 0.10  # Max total sediment potential

    def calculate_preheat_temperature(
        self, visc_50c: float, target_visc: float = 12.0
    ) -> float:
        """Estimate required preheating temperature using Walther equation approximation."""
        if visc_50c <= 15.0:
            return 40.0
        # Empirical marine engine preheating curve for heavy fuel oil
        ratio = visc_50c / max(target_visc, 8.0)
        est_temp = 50.0 + (ratio - 1.0) * 2.8
        return round(min(max(est_temp, 50.0), 145.0), 1)

    def evaluate(self, sample: FuelSampleInput) -> FuelQualityReport:
        warnings: List[str] = []
        is_compliant = True

        # 1. Cat fines (Al + Si)
        if sample.al_plus_si_mg_kg > self.MAX_AL_PLUS_SI_PPM:
            is_compliant = False
            cat_fines_status = "CRITICAL_OFF_SPEC"
            warnings.append(
                f"Al+Si {sample.al_plus_si_mg_kg} ppm exceeds ISO 8217 max {self.MAX_AL_PLUS_SI_PPM} ppm"
            )
        elif sample.al_plus_si_mg_kg > self.CIMAC_CAT_FINES_ALERT_PPM:
            cat_fines_status = "HIGH_TREATMENT_NEEDED"
            warnings.append(
                f"Al+Si {sample.al_plus_si_mg_kg} ppm requires multi-stage separator & slow throughput"
            )
        else:
            cat_fines_status = "OPTIMAL"

        # 2. Flash point
        if sample.flash_point_c < self.MIN_FLASH_POINT_C:
            is_compliant = False
            flash_point_status = "CRITICAL_SOLAS_VIOLATION"
            warnings.append(
                f"Flash point {sample.flash_point_c}°C below SOLAS min {self.MIN_FLASH_POINT_C}°C"
            )
        else:
            flash_point_status = "COMPLIANT"

        # 3. Total Sediment Potential (TSP)
        if sample.total_sediment_potential_pct > self.MAX_TSP_PCT:
            is_compliant = False
            sediment_status = "OFF_SPEC_SLUDGE_RISK"
            warnings.append(
                f"TSP {sample.total_sediment_potential_pct}% exceeds max {self.MAX_TSP_PCT}%"
            )
        else:
            sediment_status = "COMPLIANT"

        # 4. Spot test compatibility (ASTM D4740)
        rating_val = int(sample.spot_test_rating.value)
        if rating_val >= 4:
            is_compliant = False
            compatibility_status = "INCOMPATIBLE_PRECIPITATION"
            warnings.append(f"ASTM D4740 spot rating {rating_val}: severe asphaltene flocculation")
        elif rating_val == 3:
            compatibility_status = "BORDERLINE_RISK"
            warnings.append("ASTM D4740 spot rating 3: marginal stability, monitor fuel filters")
        else:
            compatibility_status = "COMPATIBLE"

        preheat_temp = self.calculate_preheat_temperature(
            sample.viscosity_at_50c_cst, sample.target_injection_viscosity_cst
        )

        overall_status = "COMPLIANT" if is_compliant else "OFF_SPEC"
        if is_compliant and warnings:
            overall_status = "CONDITIONAL_ACCEPT"

        return FuelQualityReport(
            sample_id=sample.sample_id,
            is_compliant=is_compliant,
            status=overall_status,
            cat_fines_status=cat_fines_status,
            flash_point_status=flash_point_status,
            sediment_status=sediment_status,
            compatibility_status=compatibility_status,
            recommended_preheat_temp_c=preheat_temp,
            warnings=warnings,
            metrics={
                "al_plus_si_ppm": sample.al_plus_si_mg_kg,
                "flash_point_c": sample.flash_point_c,
                "viscosity_50c_cst": sample.viscosity_at_50c_cst,
                "tsp_pct": sample.total_sediment_potential_pct,
                "spot_rating": float(rating_val),
            },
        )


__all__ = [
    "SpotTestRating",
    "FuelSampleInput",
    "FuelQualityReport",
    "FuelOilIso8217Engine",
]
