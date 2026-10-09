"""HNS Chemical Spill Drift Trajectory & Hazard Zone Engine.

Implements OPRC-HNS Protocol 2000, CEDRE SEACARAMB chemical classification
(Evaporator, Floater, Dissolver, Sinker) and surface vector drift dynamics.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class HnsDriftInput:
    chemical_un_number: str
    chemical_name: str
    behavior_group: str  # 'E' (Evaporator), 'F' (Floater), 'D' (Dissolver), 'S' (Sinker), 'FE', 'FED'
    spill_quantity_tonnes: float
    current_speed_knots: float = 1.0
    current_direction_deg: float = 90.0
    wind_speed_knots: float = 15.0
    wind_direction_deg: float = 180.0
    elapsed_hours: float = 3.0
    initial_latitude: float = 10.75
    initial_longitude: float = 106.85


@dataclass
class HnsDriftResult:
    chemical_un_number: str
    chemical_name: str
    behavior_group: str
    projected_latitude: float
    projected_longitude: float
    drift_distance_nm: float
    drift_speed_knots: float
    hazard_isolation_radius_nm: float
    dispersion_risk: str
    advisories: List[str] = field(default_factory=list)


class HnsDriftEngine:
    """Evaluates hazardous chemical drift vector and hazard isolation perimeter."""

    @staticmethod
    def evaluate(inp: HnsDriftInput) -> HnsDriftResult:
        # Standard leeway drift: 100% current vector + 3% wind vector
        curr_rad = math.radians(inp.current_direction_deg)
        wind_down_rad = math.radians((inp.wind_direction_deg + 180.0) % 360.0)

        # Vector decomposition in knots (u: East, v: North)
        u_curr = inp.current_speed_knots * math.sin(curr_rad)
        v_curr = inp.current_speed_knots * math.cos(curr_rad)

        leeway_factor = 0.03
        u_wind = (inp.wind_speed_knots * leeway_factor) * math.sin(wind_down_rad)
        v_wind = (inp.wind_speed_knots * leeway_factor) * math.cos(wind_down_rad)

        u_total = u_curr + u_wind
        v_total = v_curr + v_wind

        drift_speed = round(math.sqrt(u_total**2 + v_total**2), 2)
        total_distance_nm = round(drift_speed * max(0.1, inp.elapsed_hours), 2)

        # Coordinate projection
        lat_shift_deg = (v_total * inp.elapsed_hours) / 60.0
        cos_lat = math.cos(math.radians(inp.initial_latitude))
        cos_lat = max(0.01, cos_lat)
        lon_shift_deg = (u_total * inp.elapsed_hours) / (60.0 * cos_lat)

        proj_lat = round(inp.initial_latitude + lat_shift_deg, 4)
        proj_lon = round(inp.initial_longitude + lon_shift_deg, 4)

        # Hazard isolation radius based on chemical behavior group
        bg = inp.behavior_group.upper()
        mass_scale = math.sqrt(max(0.1, inp.spill_quantity_tonnes) / 10.0)

        if "E" in bg:  # Evaporator / Gas plume risk
            base_radius = 1.5
            dispersion_risk = "HIGH_VAPOR_HAZARD"
        elif "F" in bg:  # Floater / Slick risk
            base_radius = 0.8
            dispersion_risk = "SURFACE_SLICK_HAZARD"
        elif "D" in bg:  # Dissolver / Aquatic toxicity
            base_radius = 0.5
            dispersion_risk = "WATER_COLUMN_CONTAMINATION"
        else:  # Sinker / Benthic risk
            base_radius = 0.3
            dispersion_risk = "SEABED_BENTHIC_DEPOSITION"

        isolation_radius = round(base_radius * mass_scale, 2)

        advisories: List[str] = [
            f"CEDRE classification: {bg}. Primary hazard: {dispersion_risk}.",
            f"Predicted drift speed: {drift_speed} kts, distance after {inp.elapsed_hours}h: {total_distance_nm} NM.",
        ]
        if "E" in bg:
            advisories.append("EVAPORATOR TOXIC CLOUD: Establish upwind exclusion zone immediately.")
        if isolation_radius > 2.0:
            advisories.append(f"EXTENDED ISOLATION ZONE: Perimeter {isolation_radius} NM exceeds standard port limits.")

        return HnsDriftResult(
            chemical_un_number=inp.chemical_un_number,
            chemical_name=inp.chemical_name,
            behavior_group=bg,
            projected_latitude=proj_lat,
            projected_longitude=proj_lon,
            drift_distance_nm=total_distance_nm,
            drift_speed_knots=drift_speed,
            hazard_isolation_radius_nm=isolation_radius,
            dispersion_risk=dispersion_risk,
            advisories=advisories,
        )
