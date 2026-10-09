"""Phase 349: Port Anchorage Windlass Holding Power & Ground Tackle Scope Engine.

Implements IACS UR A1 and OCIMF MEG4 standards for ship anchoring safety:
- Equipment Number (EN) derivation for ground tackle sizing.
- Anchor holding capacity and seabed chain friction calculation.
- Chain scope ratio verification (minimum 4:1 to 6:1).
- Environmental drag forces (wind + current) vs anchor holding power.
- Dragging anchor alert triggering.
Strictly under 200 LOC.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class AnchorageHoldingInput:
    vessel_id: str
    displacement_tonnes: float
    breadth_m: float
    freeboard_superstructure_height_m: float  # a
    lateral_windage_area_m2: float
    water_depth_m: float
    shackles_paid_out: float  # 1 shackle = 27.5 meters
    anchor_mass_kg: float = 5000.0
    chain_weight_submerged_kg_m: float = 85.0
    wind_speed_knots: float = 25.0
    current_speed_knots: float = 2.0
    is_high_holding_power_anchor: bool = True
    seabed_type: str = "MUD_SAND"  # MUD_SAND, SOFT_MUD, ROCK


@dataclass
class AnchorageHoldingResult:
    vessel_id: str
    equipment_number_en: float
    scope_ratio: float
    total_chain_length_m: float
    anchor_holding_capacity_kn: float
    chain_holding_capacity_kn: float
    total_holding_capacity_kn: float
    environmental_load_kn: float
    safety_factor: float
    is_holding_secure: bool
    dragging_risk: str  # LOW, MODERATE, HIGH
    advisories: List[str] = field(default_factory=list)


class AnchorageHoldingEngine:
    """Calculates anchorage ground tackle holding power and scope per IACS UR A1 & MEG4."""

    SHACKLE_LENGTH_M = 27.5
    GRAVITY_ACCEL = 9.81 / 1000.0  # kN per kg

    @classmethod
    def evaluate(cls, inp: AnchorageHoldingInput) -> AnchorageHoldingResult:
        advisories: List[str] = []

        # 1. Equipment Number EN = Delta^(2/3) + 2*B*a + 0.1*A_lat
        delta_term = math.pow(inp.displacement_tonnes, 2.0 / 3.0)
        en = round(
            delta_term
            + 2.0 * inp.breadth_m * inp.freeboard_superstructure_height_m
            + 0.1 * inp.lateral_windage_area_m2,
            1,
        )

        # 2. Scope calculation
        total_chain_m = round(inp.shackles_paid_out * cls.SHACKLE_LENGTH_M, 1)
        scope = round(total_chain_m / inp.water_depth_m, 2) if inp.water_depth_m > 0 else 1.0

        if scope < 4.0:
            advisories.append(
                f"INSUFFICIENT SCOPE WARNING: Scope ratio {scope}:1 < 4.0:1. "
                "Risk of vertical uplift lifting anchor shank. Veer more cable."
            )

        # 3. Anchor holding power
        # HHP anchor holding ratio = ~10.0, Standard = ~4.0
        anchor_ratio = 10.0 if inp.is_high_holding_power_anchor else 4.0
        anchor_hold_kn = round(inp.anchor_mass_kg * anchor_ratio * cls.GRAVITY_ACCEL, 2)

        # 4. Chain on seabed holding power
        # Suspended catenary approx length ~ 1.5 * depth
        suspended_m = min(total_chain_m, 1.5 * inp.water_depth_m)
        on_seabed_m = max(0.0, total_chain_m - suspended_m)
        seabed_mu = 0.6 if inp.seabed_type == "MUD_SAND" else (0.4 if inp.seabed_type == "SOFT_MUD" else 0.2)
        chain_hold_kn = round(on_seabed_m * inp.chain_weight_submerged_kg_m * seabed_mu * cls.GRAVITY_ACCEL, 2)

        total_hold_kn = round(anchor_hold_kn + chain_hold_kn, 2)

        # 5. Environmental loads estimation (Wind + Current in kN)
        # Wind load: 0.5 * rho_air (1.225) * Cd (1.0) * Area * V^2 (m/s)
        wind_ms = inp.wind_speed_knots * 0.5144
        wind_load_kn = round(0.5 * 1.225 * 0.9 * inp.lateral_windage_area_m2 * math.pow(wind_ms, 2) / 1000.0, 2)

        current_ms = inp.current_speed_knots * 0.5144
        # Hydrodynamic hull drag proxy: 0.5 * rho_water * Cd * (B * d) * V^2
        current_load_kn = round(0.5 * 1025.0 * 0.08 * inp.displacement_tonnes * math.pow(current_ms, 2) / 10000.0, 2)

        total_env_kn = round(wind_load_kn + current_load_kn, 2)

        # Safety factor
        sf = round(total_hold_kn / total_env_kn, 2) if total_env_kn > 0 else 99.0
        is_secure = sf >= 1.33 and scope >= 4.0

        if sf < 1.0:
            drag_risk = "HIGH"
            advisories.append(
                f"DRAGGING ANCHOR ALERT: Env load {total_env_kn} kN exceeds holding power {total_hold_kn} kN. "
                "Engage main engine immediately."
            )
        elif sf < 1.33:
            drag_risk = "MODERATE"
            advisories.append(
                f"MARGINAL HOLDING CAPACITY: Safety factor {sf} < 1.33. Monitor GPS anchor watch closely."
            )
        else:
            drag_risk = "LOW"
            advisories.append("ANCHOR HOLDING SECURE: Ground tackle capacity provides safe holding margin.")

        return AnchorageHoldingResult(
            vessel_id=inp.vessel_id,
            equipment_number_en=en,
            scope_ratio=scope,
            total_chain_length_m=total_chain_m,
            anchor_holding_capacity_kn=anchor_hold_kn,
            chain_holding_capacity_kn=chain_hold_kn,
            total_holding_capacity_kn=total_hold_kn,
            environmental_load_kn=total_env_kn,
            safety_factor=sf,
            is_holding_secure=is_secure,
            dragging_risk=drag_risk,
            advisories=advisories,
        )
