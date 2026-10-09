"""Bulk Carrier Loading Computer, Stability & Hull Stress Engine.

Implements SOLAS XII/11, IACS UR S1/S1A Bending Moment (BM) & Shear Force (SF) limits,
and IMO 2008 Intact Stability Code (IS Code) GM / GZ righting arm evaluation.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class BulkLoadingInput:
    vessel_id: str
    displacement_tonnes: float
    km_transverse_m: float
    kg_solid_m: float
    free_surface_correction_m: float = 0.05
    calculated_swbm_kntm: float = 120000.0
    permissible_swbm_kntm: float = 150000.0
    calculated_swsf_kn: float = 18000.0
    permissible_swsf_kn: float = 22000.0
    cross_curves_ms_30deg_m: float = 2.45
    cross_curves_ms_40deg_m: float = 3.10
    is_harbour_condition: bool = False


@dataclass
class BulkLoadingResult:
    vessel_id: str
    gm_fluid_m: float
    gz_30deg_m: float
    gz_40deg_m: float
    swbm_percent: float
    swsf_percent: float
    is_stability_compliant: bool
    is_hull_stress_compliant: bool
    status: str
    advisories: List[str] = field(default_factory=list)


class BulkLoadingEngine:
    """Evaluates bulk carrier loading computer intact stability and hull stress."""

    @staticmethod
    def evaluate(inp: BulkLoadingInput) -> BulkLoadingResult:
        # Effective GM with free surface correction
        kg_fluid = inp.kg_solid_m + max(0.0, inp.free_surface_correction_m)
        gm_fluid = round(inp.km_transverse_m - kg_fluid, 3)

        # Righting lever GZ at 30 deg and 40 deg
        sin_30 = math.sin(math.radians(30.0))
        sin_40 = math.sin(math.radians(40.0))

        gz_30 = round(inp.cross_curves_ms_30deg_m - kg_fluid * sin_30, 3)
        gz_40 = round(inp.cross_curves_ms_40deg_m - kg_fluid * sin_40, 3)

        # Hull stress ratios
        swbm_pct = round((inp.calculated_swbm_kntm / max(1.0, inp.permissible_swbm_kntm)) * 100.0, 1)
        swsf_pct = round((inp.calculated_swsf_kn / max(1.0, inp.permissible_swsf_kn)) * 100.0, 1)

        # Stability checks per 2008 IS Code (Part A 2.2)
        # GM >= 0.15m, GZ_30 >= 0.20m
        is_gm_ok = gm_fluid >= 0.15
        is_gz_ok = gz_30 >= 0.20 and gz_40 > 0.0
        is_stab_ok = is_gm_ok and is_gz_ok

        # Stress limits per IACS UR S1 (<= 100% of permissible)
        is_stress_ok = swbm_pct <= 100.0 and swsf_pct <= 100.0

        advisories: List[str] = []
        if not is_gm_ok:
            advisories.append(f"DEFICIENT METACENTRIC HEIGHT: GM {gm_fluid}m < 0.15m statutory minimum.")
        if not is_gz_ok:
            advisories.append(f"INSUFFICIENT RIGHTING LEVER: GZ at 30 deg {gz_30}m < 0.20m.")
        if swbm_pct > 100.0:
            advisories.append(f"CRITICAL OVERBENDING: SWBM is {swbm_pct}% of permissible limit.")
        if swsf_pct > 100.0:
            advisories.append(f"CRITICAL SHEAR OVERLOAD: SWSF is {swsf_pct}% of permissible limit.")

        if is_stab_ok and is_stress_ok:
            status = "SEAWORTHY"
            advisories.append("All loading, stability, and longitudinal stress criteria satisfied.")
        elif not is_stress_ok and is_stab_ok:
            status = "HULL_STRESS_EXCEEDED"
        elif not is_stab_ok and is_stress_ok:
            status = "INTACT_STABILITY_FAILURE"
        else:
            status = "CRITICAL_HAZARD"

        return BulkLoadingResult(
            vessel_id=inp.vessel_id,
            gm_fluid_m=gm_fluid,
            gz_30deg_m=gz_30,
            gz_40deg_m=gz_40,
            swbm_percent=swbm_pct,
            swsf_percent=swsf_pct,
            is_stability_compliant=is_stab_ok,
            is_hull_stress_compliant=is_stress_ok,
            status=status,
            advisories=advisories,
        )
