"""Phase 357: Smart Mooring Line Tension & Quay Berth Surge Monitoring Engine.

Compliant with OCIMF Mooring Equipment Guidelines (MEG4) and PIANC WG 115/121.
Evaluates Working Load Limit (WLL) margins, passing ship hydrodynamic surge forces,
and snap-back hazard boundary prediction.
Strictly kept under 200 lines.
"""

import math
from dataclasses import dataclass, field


@dataclass
class SmartMooringInput:
    berth_id: str
    vessel_id: str
    line_material: str = "SYNTHETIC"  # SYNTHETIC or STEEL_WIRE
    ship_design_mbl_tonnes: float = 85.0
    measured_line_tension_tonnes: float = 38.0
    passing_vessel_speed_knots: float = 8.0
    passing_vessel_displacement_tonnes: float = 60000.0
    passing_vessel_separation_m: float = 65.0
    line_angle_horizontal_deg: float = 30.0
    line_angle_vertical_deg: float = 20.0
    fairlead_deck_zone: str = "FORECASTLE"  # FORECASTLE or POOP_DECK


@dataclass
class SmartMooringResult:
    berth_id: str
    vessel_id: str
    line_material: str
    permissible_wll_tonnes: float
    tension_to_mbl_percent: float
    is_tension_within_wll: bool
    hydrodynamic_surge_force_kn: float
    total_projected_tension_tonnes: float
    is_snap_back_risk_critical: bool
    snap_back_exclusion_radius_m: float
    status: str
    advisories: list[str] = field(default_factory=list)


class SmartMooringEngine:
    """Engine for OCIMF MEG4 mooring line safety and passing ship surge analytics."""

    # MEG4 WLL limits: 50% for synthetic fiber, 55% for steel wire
    WLL_RATIO = {
        "SYNTHETIC": 0.50,
        "STEEL_WIRE": 0.55,
    }

    @classmethod
    def evaluate(cls, inp: SmartMooringInput) -> SmartMooringResult:
        mat_key = inp.line_material.upper()
        wll_factor = cls.WLL_RATIO.get(mat_key, 0.50)

        mbl = max(10.0, inp.ship_design_mbl_tonnes)
        wll_tonnes = round(mbl * wll_factor, 1)

        # Tension utilization ratio against MBL
        tension_pct = round((inp.measured_line_tension_tonnes / mbl) * 100.0, 1)
        is_wll_safe = inp.measured_line_tension_tonnes <= wll_tonnes

        # Hydrodynamic Surge Force from passing ship (PIANC empirical model):
        # F_surge = C * 0.5 * rho * V^2 * (Displacement / L_est) * (1 / sep)
        # where V is in m/s (1 knot = 0.5144 m/s), rho = 1.025 t/m3
        v_ms = inp.passing_vessel_speed_knots * 0.5144
        sep_m = max(15.0, inp.passing_vessel_separation_m)

        # Surge coefficient approximation
        surge_coeff = 0.045
        surge_force_kn = round(
            surge_coeff
            * 0.5
            * 1.025
            * (v_ms**2)
            * (inp.passing_vessel_displacement_tonnes / 200.0)
            * (100.0 / sep_m),
            1,
        )

        # Convert surge force component into line axial tension addition
        # 1 tonne ~= 9.80665 kN. Surge acts longitudinally along spring lines.
        horiz_rad = math.radians(inp.line_angle_horizontal_deg)
        vert_rad = math.radians(inp.line_angle_vertical_deg)
        cos_align = max(0.1, math.cos(horiz_rad) * math.cos(vert_rad))

        surge_tension_tonnes = round((surge_force_kn / 9.81) / (12.0 * cos_align), 1)
        total_projected_tension = round(
            inp.measured_line_tension_tonnes + surge_tension_tonnes, 1
        )

        # Snap-back hazard: Synthetic ropes store massive elastic elongation energy.
        # Critical when tension >= 55% MBL
        snap_risk = (total_projected_tension / mbl) >= 0.55

        # Snap-back exclusion radius around fairlead/chock
        base_radius = 18.0 if mat_key == "SYNTHETIC" else 12.0
        snap_radius = (
            round(base_radius * (total_projected_tension / wll_tonnes), 1)
            if snap_risk
            else base_radius
        )

        advisories: list[str] = []

        if total_projected_tension > mbl * 0.70:
            status = "DANGER_PARTING_IMMINENT"
            advisories.append(
                f"CRITICAL: Line tension ({total_projected_tension} t) projected to reach {round((total_projected_tension/mbl)*100, 1)}% MBL! Parting hazard."
            )
        elif not is_wll_safe or (total_projected_tension > wll_tonnes):
            status = "WLL_EXCEEDED"
            advisories.append(
                f"WARNING: Measured tension or surge will exceed OCIMF MEG4 WLL ({wll_tonnes} t). Slacken or tend winches."
            )
        else:
            status = "SECURE"
            advisories.append(
                f"NORMAL: Line tension within MEG4 WLL limits ({tension_pct}% MBL). Mooring array secure."
            )

        if snap_risk:
            advisories.append(
                f"SNAP-BACK HAZARD: Clear all personnel from {inp.fairlead_deck_zone} within {snap_radius} m exclusion boundary!"
            )

        if inp.passing_vessel_speed_knots > 6.0 and inp.passing_vessel_separation_m < 80.0:
            advisories.append(
                f"PASSING SHIP ALERT: High speed ({inp.passing_vessel_speed_knots} kts) at close proximity ({inp.passing_vessel_separation_m} m) induces {surge_force_kn} kN surge force."
            )

        return SmartMooringResult(
            berth_id=inp.berth_id,
            vessel_id=inp.vessel_id,
            line_material=mat_key,
            permissible_wll_tonnes=wll_tonnes,
            tension_to_mbl_percent=tension_pct,
            is_tension_within_wll=is_wll_safe,
            hydrodynamic_surge_force_kn=surge_force_kn,
            total_projected_tension_tonnes=total_projected_tension,
            is_snap_back_risk_critical=snap_risk,
            snap_back_exclusion_radius_m=snap_radius,
            status=status,
            advisories=advisories,
        )
