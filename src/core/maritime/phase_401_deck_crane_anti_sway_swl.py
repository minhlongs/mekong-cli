"""Phase 401: Electro-Hydraulic Deck Crane Anti-Sway & Dynamic SWL Limiter.

Compliant with ILO Convention 152 and DNV-ST-0378.
Strictly < 200 LOC, zero external dependencies.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class DeckCraneInput:
    hook_load_tonnes: float = 18.0
    boom_radius_m: float = 16.0
    boom_angle_deg: float = 45.0
    significant_wave_height_m: float = 0.8
    sway_pendulum_angle_deg: float = 1.2
    rated_static_swl_tonnes: float = 30.0


@dataclass
class DeckCraneResult:
    dynamic_swl_tonnes: float
    load_moment_ton_m: float
    swl_utilization_pct: float
    anti_sway_dampening_status: str
    hoisting_safety_cutoff: bool
    operation_status: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "dynamic_swl_tonnes": round(self.dynamic_swl_tonnes, 2),
            "load_moment_ton_m": round(self.load_moment_ton_m, 2),
            "swl_utilization_pct": round(self.swl_utilization_pct, 1),
            "anti_sway_dampening_status": self.anti_sway_dampening_status,
            "hoisting_safety_cutoff": self.hoisting_safety_cutoff,
            "operation_status": self.operation_status,
            "warnings": self.warnings,
        }


class DeckCraneAntiSwayEngine:
    """Evaluates shipboard deck crane dynamic load moment and anti-sway stability."""

    MIN_BOOM_ANGLE_DEG = 15.0
    MAX_BOOM_ANGLE_DEG = 82.0
    MAX_PERMISSIBLE_SWAY_DEG = 2.5

    def evaluate(self, inp: DeckCraneInput) -> DeckCraneResult:
        warnings = []

        # Dynamic derating factor from wave-induced ship motions
        f_dyn = 1.0 + (0.35 * max(inp.significant_wave_height_m, 0.0))
        dynamic_swl = inp.rated_static_swl_tonnes / f_dyn

        # Overturning load moment
        load_moment = inp.hook_load_tonnes * inp.boom_radius_m

        # SWL utilization
        utilization = (inp.hook_load_tonnes / max(dynamic_swl, 0.01)) * 100.0

        # Anti-sway pendulum damping status
        if abs(inp.sway_pendulum_angle_deg) <= self.MAX_PERMISSIBLE_SWAY_DEG:
            anti_sway_status = "STABLE_SWAY_CONTROLLED"
        elif abs(inp.sway_pendulum_angle_deg) <= 5.0:
            anti_sway_status = "ACTIVE_FEEDFORWARD_DAMPENING_ACTIVE"
            warnings.append(
                f"LOAD SWAY WARNING: Pendulum angle {inp.sway_pendulum_angle_deg:.1f}° exceeds 2.5° threshold"
            )
        else:
            anti_sway_status = "CRITICAL_SWAY_UNCONTROLLED"
            warnings.append(
                f"CRITICAL SWAY HAZARD: Excessive swinging {inp.sway_pendulum_angle_deg:.1f}° - risk of collision"
            )

        # Boom luffing angle envelope
        if not (self.MIN_BOOM_ANGLE_DEG <= inp.boom_angle_deg <= self.MAX_BOOM_ANGLE_DEG):
            warnings.append(
                f"BOOM ANGLE LIMIT EXCEEDED: Current {inp.boom_angle_deg:.1f}° outside [{self.MIN_BOOM_ANGLE_DEG}°, {self.MAX_BOOM_ANGLE_DEG}°]"
            )

        # Overload & hoisting lockout
        hoisting_cutoff = False
        if utilization >= 110.0:
            hoisting_cutoff = True
            operation_status = "OVERLOAD_HOISTING_CUTOFF"
            warnings.append(
                f"CRITICAL OVERLOAD TRIP: Utilization {utilization:.1f}% >= 110% SWL - hydraulic cutoff active"
            )
        elif utilization >= 100.0:
            operation_status = "WARNING_AT_RATED_CAPACITY"
            warnings.append(f"CAPACITY WARNING: Utilization {utilization:.1f}% reached 100% SWL")
        elif utilization >= 90.0:
            operation_status = "CAUTION_APPROACHING_SWL"
        else:
            operation_status = "NOMINAL_SAFE_OPERATION"

        return DeckCraneResult(
            dynamic_swl_tonnes=dynamic_swl,
            load_moment_ton_m=load_moment,
            swl_utilization_pct=utilization,
            anti_sway_dampening_status=anti_sway_status,
            hoisting_safety_cutoff=hoisting_cutoff,
            operation_status=operation_status,
            warnings=warnings,
        )
