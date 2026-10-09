"""Phase 382: Port Pilotage Navigational Safety & ARPA Collision Avoidance Engine.

Implements IMO Res. MSC.192(79) ARPA kinematic radar tracking, CPA/TCPA collision
assessment, and port pilotage boarding safety under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List, Optional


@dataclass
class TargetTrack:
    target_id: str
    relative_x_nm: float
    relative_y_nm: float
    target_speed_knots: float
    target_course_deg: float


@dataclass
class PilotageArpaInput:
    vessel_id: str
    own_speed_knots: float = 12.0
    own_course_deg: float = 90.0
    targets: List[TargetTrack] = field(default_factory=list)
    pilot_boarding_active: bool = False
    ground_speed_knots: float = 6.5
    dwt_tonnes: float = 50000.0
    available_tug_bollard_pull_tonnes: float = 65.0


@dataclass
class TargetAssessment:
    target_id: str
    cpa_nm: float
    tcpa_minutes: float
    is_collision_risk: bool


@dataclass
class PilotageArpaReport:
    vessel_id: str
    assessed_targets: List[TargetAssessment]
    critical_cpa_target_id: Optional[str]
    min_cpa_nm: float
    is_pilot_speed_compliant: bool
    is_tug_escort_adequate: bool
    system_status: str
    warnings: List[str] = field(default_factory=list)


class PortPilotageArpaCollisionEngine:
    """Evaluates ARPA radar kinematics, CPA/TCPA risks, and pilotage safety."""

    CPA_ALARM_THRESHOLD_NM: float = 1.00
    TCPA_ALARM_THRESHOLD_MIN: float = 12.0
    MAX_PILOT_BOARDING_SPEED_KN: float = 8.0
    TUG_BP_FACTOR: float = 0.0012

    def evaluate(self, inp: PilotageArpaInput) -> PilotageArpaReport:
        warnings: List[str] = []

        # Own ship velocity vector in Cartesian coordinates
        own_rad = math.radians(inp.own_course_deg)
        v_own_x = inp.own_speed_knots * math.sin(own_rad)
        v_own_y = inp.own_speed_knots * math.cos(own_rad)

        target_results: List[TargetAssessment] = []
        min_cpa = 999.0
        critical_tgt: Optional[str] = None
        has_collision_danger = False

        for tgt in inp.targets:
            t_rad = math.radians(tgt.target_course_deg)
            v_t_x = tgt.target_speed_knots * math.sin(t_rad)
            v_t_y = tgt.target_speed_knots * math.cos(t_rad)

            v_rel_x = v_t_x - v_own_x
            v_rel_y = v_t_y - v_own_y
            v_rel_sq = v_rel_x**2 + v_rel_y**2

            p_x = tgt.relative_x_nm
            p_y = tgt.relative_y_nm

            if v_rel_sq > 0.0001:
                tcpa_h = -(p_x * v_rel_x + p_y * v_rel_y) / v_rel_sq
                tcpa_m = tcpa_h * 60.0
                cpa_x = p_x + v_rel_x * tcpa_h
                cpa_y = p_y + v_rel_y * tcpa_h
                cpa = math.sqrt(cpa_x**2 + cpa_y**2)
            else:
                tcpa_m = 0.0
                cpa = math.sqrt(p_x**2 + p_y**2)

            is_risk = (cpa < self.CPA_ALARM_THRESHOLD_NM) and (0.0 <= tcpa_m <= self.TCPA_ALARM_THRESHOLD_MIN)
            if is_risk:
                has_collision_danger = True
                warnings.append(
                    f"COLLISION RISK: Target {tgt.target_id} CPA {cpa:.2f} NM (< 1.0 NM) in {tcpa_m:.1f} min."
                )

            if cpa < min_cpa:
                min_cpa = cpa
                critical_tgt = tgt.target_id

            target_results.append(
                TargetAssessment(
                    target_id=tgt.target_id,
                    cpa_nm=round(cpa, 2),
                    tcpa_minutes=round(tcpa_m, 1),
                    is_collision_risk=is_risk,
                )
            )

        if not inp.targets:
            min_cpa = 0.0

        # Pilot boarding speed compliance
        is_pilot_ok = True
        if inp.pilot_boarding_active and inp.ground_speed_knots > self.MAX_PILOT_BOARDING_SPEED_KN:
            is_pilot_ok = False
            warnings.append(
                f"Pilot boarding speed {inp.ground_speed_knots:.1f} kn exceeds 8.0 kn maximum safe limit."
            )

        # Escort tug bollard pull check
        req_bp = max(30.0, inp.dwt_tonnes * self.TUG_BP_FACTOR)
        is_tug_ok = inp.available_tug_bollard_pull_tonnes >= req_bp
        if not is_tug_ok:
            warnings.append(
                f"Escort tug bollard pull {inp.available_tug_bollard_pull_tonnes:.1f} TBP < required {req_bp:.1f} TBP."
            )

        # Overall status
        if has_collision_danger:
            status = "CRITICAL_COLLISION_ALARM"
        elif not is_pilot_ok or not is_tug_ok:
            status = "WARNING"
        else:
            status = "OPTIMAL"

        return PilotageArpaReport(
            vessel_id=inp.vessel_id,
            assessed_targets=target_results,
            critical_cpa_target_id=critical_tgt,
            min_cpa_nm=round(min_cpa, 2) if min_cpa < 999.0 else 0.0,
            is_pilot_speed_compliant=is_pilot_ok,
            is_tug_escort_adequate=is_tug_ok,
            system_status=status,
            warnings=warnings,
        )
