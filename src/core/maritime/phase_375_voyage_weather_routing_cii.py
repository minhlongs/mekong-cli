"""Voyage Weather Routing & Operational CII Decarbonization Engine.

Standards: IMO Res. MEPC.328(76), ISO 15016:2015, SEEMP Part III.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class CiiRating(str, Enum):
    """IMO operational carbon intensity indicator ratings."""

    A = "A"  # Superior
    B = "B"  # Minor superior
    C = "C"  # Standard compliant
    D = "D"  # Minor inferior (SEEMP alert)
    E = "E"  # Inferior (Mandatory CAP plan)


@dataclass
class VoyageRoutingInput:
    vessel_id: str
    dwt_tonnes: float
    distance_nm: float
    planned_speed_knots: float
    calm_sea_power_kw: float
    beaufort_scale: int
    significant_wave_height_m: float
    fuel_consumption_tonnes: float
    fuel_carbon_factor: float = 3.114  # t-CO2 / t-fuel (MGO/VLSFO)
    cii_ref_a: float = 296.8  # IMO reference line parameter for bulk/container
    cii_ref_c: float = 0.283
    reduction_factor_z_pct: float = 7.0  # 2026 IMO Z-factor reduction target


@dataclass
class VoyageWeatherCiiReport:
    vessel_id: str
    weather_power_kw: float
    added_resistance_pct: float
    attained_cii: float
    required_cii: float
    cii_ratio: float
    cii_rating: CiiRating
    optimal_speed_knots: float
    fuel_saving_potential_tonnes: float
    co2_reduction_tonnes: float
    seemp_action_required: bool
    warnings: List[str]
    metrics: Dict[str, float]


class VoyageWeatherRoutingCiiEngine:
    """Evaluates added wave/wind resistance, CII rating, and optimal speed."""

    # IMO Rating Boundaries (d1, d2, d3, d4)
    RATIO_A_MAX: float = 0.83
    RATIO_B_MAX: float = 0.94
    RATIO_C_MAX: float = 1.06
    RATIO_D_MAX: float = 1.19
    BEAUFORT_ALPHA: float = 0.015  # ISO 15016 weather power coefficient

    def evaluate(self, inp: VoyageRoutingInput) -> VoyageWeatherCiiReport:
        warnings: List[str] = []

        # 1. Weather Added Resistance via ISO 15016 / Beaufort power modeling
        bf_factor = self.BEAUFORT_ALPHA * (inp.beaufort_scale**2)
        wave_penalty = max(0.0, (inp.significant_wave_height_m - 1.0) * 0.04)
        added_resistance_pct = round((bf_factor + wave_penalty) * 100.0, 2)
        weather_power_kw = round(
            inp.calm_sea_power_kw * (1.0 + added_resistance_pct / 100.0), 2
        )

        if inp.beaufort_scale >= 7 or inp.significant_wave_height_m >= 4.0:
            warnings.append("Adverse weather threshold exceeded (BF >= 7 or Hs >= 4m)")

        # 2. Required CII = a * DWT^(-c) * (1 - Z / 100)
        dwt_safe = max(1000.0, inp.dwt_tonnes)
        base_cii_ref = inp.cii_ref_a * (dwt_safe ** (-inp.cii_ref_c))
        required_cii = round(base_cii_ref * (1.0 - inp.reduction_factor_z_pct / 100.0), 3)

        # 3. Attained CII = (Total Fuel Mass * CF / (DWT * Distance)) * 10^6
        transport_work = dwt_safe * max(1.0, inp.distance_nm)
        total_co2_grams = inp.fuel_consumption_tonnes * inp.fuel_carbon_factor * 1e6
        attained_cii = round((total_co2_grams / transport_work), 3)

        cii_ratio = round(attained_cii / required_cii, 3) if required_cii > 0 else 1.0

        # 4. Energy Efficiency Rating (A to E)
        if cii_ratio <= self.RATIO_A_MAX:
            rating = CiiRating.A
        elif cii_ratio <= self.RATIO_B_MAX:
            rating = CiiRating.B
        elif cii_ratio <= self.RATIO_C_MAX:
            rating = CiiRating.C
        elif cii_ratio <= self.RATIO_D_MAX:
            rating = CiiRating.D
        else:
            rating = CiiRating.E

        seemp_action = rating in (CiiRating.D, CiiRating.E)
        if seemp_action:
            warnings.append(
                f"CII Rating {rating.value} requires SEEMP Part III corrective action plan"
            )

        # 5. Speed Optimization (P proportional to V^3)
        if cii_ratio > 1.0:
            speed_factor = (required_cii / attained_cii) ** (1.0 / 3.0)
            optimal_speed_knots = round(inp.planned_speed_knots * speed_factor, 2)
        else:
            optimal_speed_knots = inp.planned_speed_knots

        fuel_reduction_ratio = max(
            0.0, 1.0 - (optimal_speed_knots / max(1.0, inp.planned_speed_knots)) ** 3
        )
        fuel_saving_tonnes = round(inp.fuel_consumption_tonnes * fuel_reduction_ratio, 2)
        co2_reduction_tonnes = round(fuel_saving_tonnes * inp.fuel_carbon_factor, 2)

        return VoyageWeatherCiiReport(
            vessel_id=inp.vessel_id,
            weather_power_kw=weather_power_kw,
            added_resistance_pct=added_resistance_pct,
            attained_cii=attained_cii,
            required_cii=required_cii,
            cii_ratio=cii_ratio,
            cii_rating=rating,
            optimal_speed_knots=optimal_speed_knots,
            fuel_saving_potential_tonnes=fuel_saving_tonnes,
            co2_reduction_tonnes=co2_reduction_tonnes,
            seemp_action_required=seemp_action,
            warnings=warnings,
            metrics={
                "transport_work_dwt_nm": transport_work,
                "base_cii_ref": round(base_cii_ref, 3),
                "weather_power_kw": weather_power_kw,
                "added_resistance_pct": added_resistance_pct,
            },
        )
