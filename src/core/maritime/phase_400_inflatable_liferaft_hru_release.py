"""Phase 400: Inflatable Liferaft & Hydrostatic Release Unit (HRU) Float-Free Dynamics.

Complies with SOLAS III Reg 13/20/31 and IMO LSA Code Chapter IV.
Evaluates hydrostatic release actuation, weak link break strain, and painter compliance.
Strictly < 200 LOC, zero-mock deterministic safety verification.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class HRUActuationState(str, Enum):
    """Hydrostatic release unit trigger state."""
    INACTIVE_STOWED = "INACTIVE_STOWED"
    HYDROSTATIC_ACTUATED = "HYDROSTATIC_ACTUATED"
    MANUAL_OVERRIDE_CUT = "MANUAL_OVERRIDE_CUT"


class FloatFreeState(str, Enum):
    """Overall liferaft float-free progression."""
    SECURED_IN_CRADLE = "SECURED_IN_CRADLE"
    LASHING_RELEASED = "LASHING_RELEASED"
    PAINTER_PULLING_INFLATING = "PAINTER_PULLING_INFLATING"
    WEAK_LINK_PARTED_FLOAT_FREE = "WEAK_LINK_PARTED_FLOAT_FREE"
    DEPLOYMENT_BLOCKED = "DEPLOYMENT_BLOCKED"


@dataclass
class LiferaftHRUInput:
    """Telemetry and inspection parameters for liferaft HRU system."""
    submersion_depth_m: float = 0.0
    painter_line_tension_kn: float = 0.0
    stowage_height_m: float = 12.0
    painter_line_length_m: float = 28.0
    hru_service_age_months: int = 14
    liferaft_service_age_months: int = 8
    manual_pelican_hook_released: bool = False
    weak_link_rating_kn: float = 2.2


@dataclass
class LiferaftHRUResult:
    """Operational validation and actuation status."""
    hru_actuated: bool
    hru_actuation_state: HRUActuationState
    float_free_state: FloatFreeState
    painter_length_compliant: bool
    min_required_painter_m: float
    weak_link_parted: bool
    weak_link_compliant: bool
    service_valid: bool
    warnings: List[str] = field(default_factory=list)


class LiferaftHRUEngine:
    """Deterministic physical evaluator for HRU and float-free liferaft."""

    MIN_ACTUATION_DEPTH_M = 1.5
    MAX_ACTUATION_DEPTH_M = 4.0
    WEAK_LINK_MIN_KN = 1.8
    WEAK_LINK_MAX_KN = 2.6
    HRU_MAX_SERVICE_MONTHS = 24
    LIFERAFT_MAX_SERVICE_MONTHS = 12

    def evaluate(self, inp: LiferaftHRUInput) -> LiferaftHRUResult:
        """Evaluate float-free progression and regulatory conformance."""
        warnings: List[str] = []

        # Painter line length check (SOLAS: stowage height + 10m or 15m minimum)
        min_painter = max(15.0, inp.stowage_height_m + 10.0)
        painter_compliant = inp.painter_line_length_m >= min_painter
        if not painter_compliant:
            warnings.append(
                f"Painter length ({inp.painter_line_length_m}m) < required minimum ({min_painter}m)"
            )

        # Service validity check
        hru_valid = inp.hru_service_age_months <= self.HRU_MAX_SERVICE_MONTHS
        if not hru_valid:
            warnings.append(f"HRU expired: {inp.hru_service_age_months} months > 24 months")

        raft_valid = inp.liferaft_service_age_months <= self.LIFERAFT_MAX_SERVICE_MONTHS
        if not raft_valid:
            warnings.append(
                f"Liferaft service overdue: {inp.liferaft_service_age_months} months > 12 months"
            )

        service_valid = hru_valid and raft_valid

        # Weak link rating compliance (2.2 +/- 0.4 kN)
        wl_compliant = (
            self.WEAK_LINK_MIN_KN <= inp.weak_link_rating_kn <= self.WEAK_LINK_MAX_KN
        )
        if not wl_compliant:
            warnings.append(
                f"Weak link rating {inp.weak_link_rating_kn} kN outside [1.8, 2.6] kN envelope"
            )

        # Actuation logic
        hru_triggered = False
        act_state = HRUActuationState.INACTIVE_STOWED

        if inp.manual_pelican_hook_released:
            hru_triggered = True
            act_state = HRUActuationState.MANUAL_OVERRIDE_CUT
        elif inp.submersion_depth_m >= self.MIN_ACTUATION_DEPTH_M:
            hru_triggered = True
            act_state = HRUActuationState.HYDROSTATIC_ACTUATED
            if inp.submersion_depth_m > self.MAX_ACTUATION_DEPTH_M:
                warnings.append(
                    f"Submersion depth {inp.submersion_depth_m}m exceeded 4.0m upper threshold"
                )

        # Progression
        wl_parted = False
        if not hru_triggered:
            prog_state = FloatFreeState.SECURED_IN_CRADLE
        else:
            # Lashing released, raft begins floating & pulling painter
            if inp.painter_line_tension_kn >= inp.weak_link_rating_kn:
                wl_parted = True
                prog_state = FloatFreeState.WEAK_LINK_PARTED_FLOAT_FREE
            elif inp.painter_line_tension_kn > 0.5:
                prog_state = FloatFreeState.PAINTER_PULLING_INFLATING
            else:
                prog_state = FloatFreeState.LASHING_RELEASED

        if not service_valid and prog_state == FloatFreeState.SECURED_IN_CRADLE:
            prog_state = FloatFreeState.DEPLOYMENT_BLOCKED

        return LiferaftHRUResult(
            hru_actuated=hru_triggered,
            hru_actuation_state=act_state,
            float_free_state=prog_state,
            painter_length_compliant=painter_compliant,
            min_required_painter_m=min_painter,
            weak_link_parted=wl_parted,
            weak_link_compliant=wl_compliant,
            service_valid=service_valid,
            warnings=warnings,
        )
