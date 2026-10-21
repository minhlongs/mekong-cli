"""Phase 336: Project Cargo & Heavy Lift CSS Lashing Safety Engine.

Calculates multi-axis ship accelerations, dunnage friction, effective lashing capacity,
and sliding/tipping safety factors according to IMO CSS Code Annex 13 and DNV-ST-N001.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List
import math


@dataclass
class LashingDevice:
    device_id: str
    msl_kn: float  # Maximum Securing Load in kN
    vertical_angle_deg: float  # alpha: angle to deck
    horizontal_angle_deg: float  # beta: angle to transverse axis


@dataclass
class ProjectCargoLashingInput:
    cargo_id: str
    description: str
    mass_metric_ton: float
    cog_height_m: float  # Center of Gravity height above deck
    cargo_width_m: float  # Width for tipping calculation
    accel_transverse_ay: float  # m/s^2 (e.g. 5.5 m/s^2)
    accel_vertical_az: float  # m/s^2 (e.g. 2.0 m/s^2)
    dunnage_friction_mu: float = 0.3  # 0.3 wood/steel, 0.1 steel/steel
    lashings: List[LashingDevice] = field(default_factory=list)


@dataclass
class ProjectCargoLashingResult:
    cargo_id: str
    mass_metric_ton: float
    external_transverse_force_kn: float
    dunnage_friction_force_kn: float
    total_lashing_restraint_kn: float
    total_restraining_force_kn: float
    sliding_safety_factor: float
    overturning_moment_kn_m: float
    restoring_moment_kn_m: float
    tipping_safety_factor: float
    is_sliding_safe: bool
    is_tipping_safe: bool
    is_overall_compliant: bool
    advisories: List[str]


class ProjectCargoCssLashingEngine:
    G_ACCEL = 9.81  # m/s^2
    MIN_SAFETY_FACTOR = 1.25  # IMO CSS Code Annex 13 standard

    @classmethod
    def evaluate(cls, inp: ProjectCargoLashingInput) -> ProjectCargoLashingResult:
        advisories: List[str] = []

        # 1. External forces in kN: F = m * a (mass in tons = 1000 kg, kN = mass * a)
        f_ext_y = round(inp.mass_metric_ton * inp.accel_transverse_ay, 2)

        # 2. Net vertical acceleration & normal force
        net_az = max(0.0, cls.G_ACCEL - inp.accel_vertical_az)
        normal_force_kn = inp.mass_metric_ton * net_az
        f_friction = round(inp.dunnage_friction_mu * normal_force_kn, 2)

        # 3. Lashing contributions
        total_lash_y = 0.0
        total_lash_restoring_moment = 0.0

        for lash in inp.lashings:
            alpha_rad = math.radians(lash.vertical_angle_deg)
            beta_rad = math.radians(lash.horizontal_angle_deg)

            # Transverse restraining component
            f_ly = lash.msl_kn * math.cos(alpha_rad) * math.cos(beta_rad)
            total_lash_y += f_ly

            # Tipping lever: half cargo width * sin(alpha) + cog_height * cos(alpha)
            lever_arm = (inp.cargo_width_m / 2.0) * math.sin(alpha_rad)
            total_lash_restoring_moment += lash.msl_kn * lever_arm

        total_lash_y = round(total_lash_y, 2)
        total_restraint = round(f_friction + total_lash_y, 2)

        # 4. Sliding Safety Factor
        sf_sliding = (
            round(total_restraint / f_ext_y, 2) if f_ext_y > 0.0 else 99.99
        )
        is_sliding_safe = sf_sliding >= cls.MIN_SAFETY_FACTOR

        if not is_sliding_safe:
            advisories.append(
                f"UNSAFE SLIDING: SF {sf_sliding} < {cls.MIN_SAFETY_FACTOR} (Deficit: {round(f_ext_y * cls.MIN_SAFETY_FACTOR - total_restraint, 2)} kN)"
            )

        # 5. Overturning & Restoring moments (kN.m)
        m_overturn = round(f_ext_y * inp.cog_height_m, 2)
        # Self-weight restoring moment = Normal Force * (Width / 2)
        m_restore_gravity = normal_force_kn * (inp.cargo_width_m / 2.0)
        m_restore_total = round(m_restore_gravity + total_lash_restoring_moment, 2)

        sf_tipping = (
            round(m_restore_total / m_overturn, 2) if m_overturn > 0.0 else 99.99
        )
        is_tipping_safe = sf_tipping >= cls.MIN_SAFETY_FACTOR

        if not is_tipping_safe:
            advisories.append(
                f"UNSAFE TIPPING: SF {sf_tipping} < {cls.MIN_SAFETY_FACTOR} (Overturning moment: {m_overturn} kNm)"
            )

        overall_compliant = is_sliding_safe and is_tipping_safe
        if overall_compliant:
            advisories.append(
                f"COMPLIANT: CSS Code Annex 13 satisfied with sliding SF {sf_sliding} and tipping SF {sf_tipping}"
            )

        return ProjectCargoLashingResult(
            cargo_id=inp.cargo_id,
            mass_metric_ton=inp.mass_metric_ton,
            external_transverse_force_kn=f_ext_y,
            dunnage_friction_force_kn=f_friction,
            total_lashing_restraint_kn=total_lash_y,
            total_restraining_force_kn=total_restraint,
            sliding_safety_factor=sf_sliding,
            overturning_moment_kn_m=m_overturn,
            restoring_moment_kn_m=m_restore_total,
            tipping_safety_factor=sf_tipping,
            is_sliding_safe=is_sliding_safe,
            is_tipping_safe=is_tipping_safe,
            is_overall_compliant=overall_compliant,
            advisories=advisories,
        )
