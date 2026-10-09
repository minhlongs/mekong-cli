"""Phase 400: Vacuum Plate Fresh Water Generator (FWG) Evaporator.

Compliant with SOLAS II-1 Reg 26 & WHO Guide to Ship Sanitation.
Strictly < 200 LOC, zero external dependencies.
"""

import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class VacuumFwgInput:
    jacket_water_temp_c: float = 80.0
    evaporator_vacuum_bar: float = -0.93  # -0.90 to -0.95 bar relative
    distillate_salinity_ppm: float = 3.5
    feed_seawater_flow_m3_h: float = 12.0
    distillate_flow_m3_h: float = 1.0


@dataclass
class VacuumFwgResult:
    evaporator_boiling_temp_c: float
    distillate_purity_status: str
    three_way_dump_valve: str
    scale_formation_risk: bool
    thermal_efficiency_pct: float
    potable_grade_certified: bool
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "evaporator_boiling_temp_c": round(self.evaporator_boiling_temp_c, 1),
            "distillate_purity_status": self.distillate_purity_status,
            "three_way_dump_valve": self.three_way_dump_valve,
            "scale_formation_risk": self.scale_formation_risk,
            "thermal_efficiency_pct": round(self.thermal_efficiency_pct, 1),
            "potable_grade_certified": self.potable_grade_certified,
            "warnings": self.warnings,
        }


class VacuumFreshWaterGeneratorEngine:
    """Evaluates marine sub-atmospheric vacuum evaporation and distillate purity."""

    SALINITY_POTABLE_MAX_PPM = 10.0
    MIN_JACKET_WATER_TEMP_C = 65.0
    OPTIMAL_VACUUM_MIN = -0.95
    OPTIMAL_VACUUM_MAX = -0.90

    def evaluate(self, inp: VacuumFwgInput) -> VacuumFwgResult:
        warnings = []

        # Boiling saturation temperature via Antoine equation for water
        # log10(P_bar) = 5.20389 - 1733.926 / (T + 233.665)
        rel_vac = max(min(inp.evaporator_vacuum_bar, 0.0), -0.98)
        abs_p_bar = max(1.013 + rel_vac, 0.02)
        boiling_temp = 1733.926 / (5.20389 - math.log10(abs_p_bar)) - 233.665

        # Jacket water heat sufficiency
        if inp.jacket_water_temp_c < self.MIN_JACKET_WATER_TEMP_C:
            warnings.append(
                f"INSUFFICIENT HT HEAT SOURCE: Jacket water {inp.jacket_water_temp_c:.1f}°C < 65.0°C"
            )

        # Vacuum condition
        if inp.evaporator_vacuum_bar > self.OPTIMAL_VACUUM_MAX:
            warnings.append(
                f"POOR VACUUM: Evaporator vacuum {inp.evaporator_vacuum_bar:.2f} bar too weak (boiling temp elevated)"
            )

        # Distillate salinity check and 3-way solenoid valve command
        if inp.distillate_salinity_ppm <= self.SALINITY_POTABLE_MAX_PPM:
            distillate_purity_status = "POTABLE_PURE_DISTILLATE"
            three_way_dump_valve = "DIRECT_TO_FRESHWATER_STORAGE"
            potable_certified = True
        else:
            distillate_purity_status = "SALINE_CONTAMINATED_DEFECT"
            three_way_dump_valve = "DUMP_OVERBOARD_OR_EVAP_RECIRC"
            potable_certified = False
            warnings.append(
                f"SALINITY HIGH TRIP: Salinity {inp.distillate_salinity_ppm:.1f} ppm exceeds 10.0 ppm limit"
            )

        # Brine concentration factor & scaling risk (scale forms when recovery is too high)
        recovery_ratio = (inp.distillate_flow_m3_h / max(inp.feed_seawater_flow_m3_h, 0.1))
        scale_formation_risk = recovery_ratio > 0.15 or boiling_temp > 50.0
        if scale_formation_risk:
            warnings.append(
                "SCALE FORMATION RISK: High recovery ratio or elevated boiling temperature causing CaCO3 deposition"
            )

        # Thermal efficiency indicator
        dt_available = max(inp.jacket_water_temp_c - boiling_temp, 1.0)
        thermal_eff = min(100.0, max(20.0, (dt_available / 40.0) * 85.0))

        return VacuumFwgResult(
            evaporator_boiling_temp_c=boiling_temp,
            distillate_purity_status=distillate_purity_status,
            three_way_dump_valve=three_way_dump_valve,
            scale_formation_risk=scale_formation_risk,
            thermal_efficiency_pct=thermal_eff,
            potable_grade_certified=potable_certified,
            warnings=warnings,
        )
