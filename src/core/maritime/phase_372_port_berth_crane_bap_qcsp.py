"""Port Berth Allocation & Quay Crane Scheduling Optimization (BAP/QCSP) Engine.

Standards: UNCTAD Port Development Handbook, PIANC MarCom WG 158,
and Vietnam Decision 1579/QD-TTg Seaport Master Plan.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class BerthAllocationStatus(str, Enum):
    """Berth and crane allocation compliance status."""

    APPROVED = "APPROVED"
    TIDAL_WAIT = "TIDAL_WAIT"  # Requires higher tide window
    BERTH_INSUFFICIENT = "BERTH_INSUFFICIENT"
    CRANE_INTERFERENCE_VIOLATION = "CRANE_INTERFERENCE_VIOLATION"


@dataclass
class BerthRequest:
    vessel_name: str
    loa_m: float  # Length Overall
    draft_m: float
    container_moves: int
    assigned_berth_length_m: float
    berth_chart_depth_m: float
    tide_height_m: float
    assigned_cranes: int
    crane_spacing_m: float
    crane_productivity_moves_per_h: float = 28.0


@dataclass
class BerthAllocationReport:
    vessel_name: str
    status: BerthAllocationStatus
    required_berth_length_m: float
    effective_water_depth_m: float
    actual_ukc_m: float
    estimated_turnaround_hours: float
    warnings: List[str]
    metrics: Dict[str, float]


class PortBerthCraneBapQcspEngine:
    """Evaluates continuous berth allocation and quay crane non-crossing safety."""

    BERTH_CLEARANCE_BUFFER_M: float = 30.0  # 15m forward + 15m aft (PIANC)
    MIN_UKC_M: float = 1.5  # Minimum Under-Keel Clearance
    MIN_CRANE_SEPARATION_M: float = 35.0  # Non-crossing boom safety buffer
    DEEP_DRAFT_THRESHOLD_M: float = 14.0  # Cai Mep / Lach Huyen deep channel

    def evaluate(self, req: BerthRequest) -> BerthAllocationReport:
        warnings: List[str] = []
        required_length = req.loa_m + self.BERTH_CLEARANCE_BUFFER_M
        effective_depth = req.berth_chart_depth_m + req.tide_height_m
        actual_ukc = effective_depth - req.draft_m

        status = BerthAllocationStatus.APPROVED

        # Length check
        if req.assigned_berth_length_m < required_length:
            status = BerthAllocationStatus.BERTH_INSUFFICIENT
            warnings.append(
                f"Assigned berth {req.assigned_berth_length_m:.1f}m < required "
                f"{required_length:.1f}m (LOA {req.loa_m}m + {self.BERTH_CLEARANCE_BUFFER_M}m buffer)"
            )

        # Depth & Under-Keel Clearance (UKC) check
        if actual_ukc < self.MIN_UKC_M:
            if req.draft_m >= self.DEEP_DRAFT_THRESHOLD_M:
                status = BerthAllocationStatus.TIDAL_WAIT
                needed_tide = req.draft_m + self.MIN_UKC_M - req.berth_chart_depth_m
                warnings.append(
                    f"UKC {actual_ukc:.2f}m < required {self.MIN_UKC_M}m: "
                    f"Tidal window gating required (min tide: {needed_tide:.2f}m)"
                )
            else:
                status = BerthAllocationStatus.BERTH_INSUFFICIENT
                warnings.append(
                    f"UKC {actual_ukc:.2f}m < required {self.MIN_UKC_M}m: Insufficient berth water depth"
                )

        # Quay Crane Scheduling (QCSP) non-crossing clearance
        if req.assigned_cranes > 1 and req.crane_spacing_m < self.MIN_CRANE_SEPARATION_M:
            status = BerthAllocationStatus.CRANE_INTERFERENCE_VIOLATION
            warnings.append(
                f"Quay crane spacing {req.crane_spacing_m:.1f}m < safety buffer "
                f"{self.MIN_CRANE_SEPARATION_M}m: Crane boom collision risk"
            )

        # Turnaround time computation
        effective_cranes = max(1, req.assigned_cranes)
        total_crane_rate = effective_cranes * req.crane_productivity_moves_per_h
        turnaround_hours = req.container_moves / max(1.0, total_crane_rate)

        metrics = {
            "loa_m": req.loa_m,
            "required_berth_length_m": round(required_length, 2),
            "effective_water_depth_m": round(effective_depth, 2),
            "actual_ukc_m": round(actual_ukc, 2),
            "assigned_cranes": float(req.assigned_cranes),
            "crane_spacing_m": round(req.crane_spacing_m, 2),
            "estimated_turnaround_hours": round(turnaround_hours, 2),
        }

        return BerthAllocationReport(
            vessel_name=req.vessel_name,
            status=status,
            required_berth_length_m=round(required_length, 2),
            effective_water_depth_m=round(effective_depth, 2),
            actual_ukc_m=round(actual_ukc, 2),
            estimated_turnaround_hours=round(turnaround_hours, 2),
            warnings=warnings,
            metrics=metrics,
        )
