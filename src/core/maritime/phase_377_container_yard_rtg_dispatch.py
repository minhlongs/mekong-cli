"""Port Container Terminal Yard Stacking & RTG Crane Dispatch Engine.

Standards: UNCTAD Container Terminal Handbook, IAPH Smart Ports, Decision 1579/QD-TTg.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ContainerItem:
    container_id: str
    bay: int
    row: int
    tier: int
    departure_order: int  # 1 is earliest departure, 2 is later, etc.
    is_reefer: bool = False
    imdg_class: Optional[str] = None


@dataclass
class YardBlockInput:
    block_id: str
    containers: List[ContainerItem]
    available_rtg_cranes: int
    active_quay_cranes: int
    gantry_travel_distance_m: float = 100.0
    reefer_plug_capacity: int = 50
    active_reefer_count: int = 35


@dataclass
class YardStackRtgReport:
    block_id: str
    total_containers: int
    total_reshuffles_required: int
    reshuffle_ratio_pct: float
    imdg_segregation_compliant: bool
    rtg_qc_ratio: float
    is_crane_capacity_sufficient: bool
    cost_to_go_score: float
    warnings: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)


class ContainerYardRtgDispatchEngine:
    """Evaluates container stacking reshuffle penalties, IMDG segregation, and RTG allocation."""

    MIN_RTG_PER_QC_RATIO: float = 0.50  # UNCTAD minimum 1 RTG per 2 Quay Cranes
    MAX_REEFER_LOAD_PCT: float = 90.0  # Safe substation transformer limit
    RESHUFFLE_WEIGHT: float = 3.5  # Cost weight per reshuffle move
    GANTRY_MOVE_WEIGHT: float = 0.05  # Cost weight per gantry travel meter

    def evaluate(self, inp: YardBlockInput) -> YardStackRtgReport:
        warnings: List[str] = []
        total_containers = len(inp.containers)

        # 1. Reshuffle Calculation: In same (bay, row), if higher tier departs LATER
        # than lower tier (larger departure_order), higher tier blocks retrieval.
        stacks: Dict[tuple, List[ContainerItem]] = {}
        for c in inp.containers:
            key = (c.bay, c.row)
            stacks.setdefault(key, []).append(c)

        total_reshuffles = 0
        for key, stack in stacks.items():
            # Sort by tier ascending
            sorted_stack = sorted(stack, key=lambda x: x.tier)
            for i, lower in enumerate(sorted_stack):
                for higher in sorted_stack[i + 1 :]:
                    if higher.departure_order > lower.departure_order:
                        total_reshuffles += 1

        reshuffle_ratio_pct = (
            round((total_reshuffles / total_containers) * 100.0, 2)
            if total_containers > 0
            else 0.0
        )
        if total_reshuffles > 0:
            warnings.append(
                f"Stack contains {total_reshuffles} blocking container(s) "
                f"requiring reshuffle ({reshuffle_ratio_pct}%)"
            )

        # 2. IMDG Segregation Separation (Class 3 Flammable vs Class 5.1 Oxidizer)
        imdg_compliant = True
        imdg_containers = [c for c in inp.containers if c.imdg_class]
        for i, c1 in enumerate(imdg_containers):
            for c2 in imdg_containers[i + 1 :]:
                if {c1.imdg_class, c2.imdg_class} == {"3", "5.1"}:
                    if abs(c1.bay - c2.bay) < 2 and c1.row == c2.row:
                        imdg_compliant = False
                        warnings.append(
                            f"IMDG Segregation Violation: Class 3 ({c1.container_id}) and "
                            f"Class 5.1 ({c2.container_id}) within 1 bay longitudinal buffer"
                        )

        # 3. Reefer Plug Capacity
        reefer_util_pct = (
            round((inp.active_reefer_count / max(1, inp.reefer_plug_capacity)) * 100.0, 2)
        )
        if reefer_util_pct > self.MAX_REEFER_LOAD_PCT:
            warnings.append(
                f"Reefer plug capacity critical ({reefer_util_pct}% > {self.MAX_REEFER_LOAD_PCT}%)"
            )

        # 4. RTG Crane Dispatch & Quay Crane Coupling
        rtg_qc_ratio = (
            round(inp.available_rtg_cranes / max(1, inp.active_quay_cranes), 2)
        )
        is_crane_capacity_sufficient = rtg_qc_ratio >= self.MIN_RTG_PER_QC_RATIO
        if not is_crane_capacity_sufficient:
            warnings.append(
                f"RTG allocation bottleneck (ratio {rtg_qc_ratio} < {self.MIN_RTG_PER_QC_RATIO}): "
                "Quay crane truck queuing expected"
            )

        # 5. Composite Cost-to-Go Dispatch Metric J
        cost_to_go = round(
            inp.gantry_travel_distance_m * self.GANTRY_MOVE_WEIGHT
            + total_reshuffles * self.RESHUFFLE_WEIGHT,
            2,
        )

        return YardStackRtgReport(
            block_id=inp.block_id,
            total_containers=total_containers,
            total_reshuffles_required=total_reshuffles,
            reshuffle_ratio_pct=reshuffle_ratio_pct,
            imdg_segregation_compliant=imdg_compliant,
            rtg_qc_ratio=rtg_qc_ratio,
            is_crane_capacity_sufficient=is_crane_capacity_sufficient,
            cost_to_go_score=cost_to_go,
            warnings=warnings,
            metrics={
                "reefer_utilization_pct": reefer_util_pct,
                "gantry_travel_distance_m": inp.gantry_travel_distance_m,
                "cost_to_go_score": cost_to_go,
            },
        )
