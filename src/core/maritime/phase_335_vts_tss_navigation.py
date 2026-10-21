"""Phase 335: Vessel Traffic Service (VTS) & Traffic Separation Schemes (TSS) Engine.

Evaluates COLREGs Rule 10 TSS lane compliance, wrong-way detection,
cross-track error (XTE), and CPA/TCPA collision risk under IMO Res. A.1158(32).
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class VtsNavigationInput:
    vessel_mmsi: str
    vessel_name: str
    lat: float
    lon: float
    course_deg: float
    speed_knots: float
    tss_lane_name: str
    tss_lane_heading_deg: float
    tss_lane_width_nm: float = 1.5
    cross_track_error_nm: float = 0.2
    target_mmsi: Optional[str] = None
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None
    target_course_deg: Optional[float] = None
    target_speed_knots: Optional[float] = None


@dataclass
class VtsNavigationResult:
    vessel_mmsi: str
    tss_lane_name: str
    heading_deviation_deg: float
    is_wrong_way: bool
    is_outside_corridor: bool
    cpa_nm: Optional[float]
    tcpa_minutes: Optional[float]
    collision_risk: bool
    vts_service_level: str  # "INS", "TOS", "NAS"
    colregs_rule10_compliant: bool
    advisories: List[str]


class VtsTssNavigationEngine:
    CPA_RISK_THRESHOLD_NM = 1.0
    TCPA_RISK_THRESHOLD_MIN = 15.0

    @staticmethod
    def calculate_heading_deviation(actual_deg: float, lane_deg: float) -> float:
        diff = (actual_deg - lane_deg + 180.0) % 360.0 - 180.0
        return round(abs(diff), 2)

    @classmethod
    def calculate_cpa_tcpa(
        cls,
        lat1: float,
        lon1: float,
        cog1: float,
        sog1: float,
        lat2: float,
        lon2: float,
        cog2: float,
        sog2: float,
    ) -> tuple[float, float]:
        """Calculates Closest Point of Approach (NM) and Time to CPA (minutes)."""
        # Distance components in Nautical Miles
        d_lat = (lat2 - lat1) * 60.0
        d_lon = (lon2 - lon1) * 60.0 * math.cos(math.radians((lat1 + lat2) / 2.0))

        # Velocity components in knots (NM/h)
        rad1, rad2 = math.radians(cog1), math.radians(cog2)
        v1_x = sog1 * math.sin(rad1)
        v1_y = sog1 * math.cos(rad1)
        v2_x = sog2 * math.sin(rad2)
        v2_y = sog2 * math.cos(rad2)

        # Relative velocity
        v_rel_x = v2_x - v1_x
        v_rel_y = v2_y - v1_y
        v_rel_sq = v_rel_x**2 + v_rel_y**2

        if v_rel_sq < 1e-6:
            # Parallel or zero relative motion
            dist = math.sqrt(d_lat**2 + d_lon**2)
            return round(dist, 2), 0.0

        # TCPA in hours = - (r . v) / |v|^2
        # where r is target relative to own: (d_lon, d_lat)
        tcpa_hours = -(d_lon * v_rel_x + d_lat * v_rel_y) / v_rel_sq
        tcpa_minutes = max(0.0, tcpa_hours * 60.0)

        # Position at CPA
        cpa_x = d_lon + v_rel_x * tcpa_hours
        cpa_y = d_lat + v_rel_y * tcpa_hours
        cpa_dist = math.sqrt(cpa_x**2 + cpa_y**2)

        return round(cpa_dist, 2), round(tcpa_minutes, 2)

    @classmethod
    def evaluate(cls, inp: VtsNavigationInput) -> VtsNavigationResult:
        advisories: List[str] = []
        heading_dev = cls.calculate_heading_deviation(inp.course_deg, inp.tss_lane_heading_deg)
        is_wrong_way = heading_dev > 90.0
        is_outside = inp.cross_track_error_nm > (inp.tss_lane_width_nm / 2.0)

        if is_wrong_way:
            advisories.append(
                f"CRITICAL: Vessel heading dev {heading_dev}° opposes TSS traffic flow (COLREGs Rule 10 violation)"
            )
        if is_outside:
            advisories.append(
                f"WARNING: Cross-track error {inp.cross_track_error_nm} NM exceeds lane half-width {inp.tss_lane_width_nm / 2.0} NM"
            )

        cpa_nm: Optional[float] = None
        tcpa_min: Optional[float] = None
        collision_risk = False

        if (
            inp.target_mmsi
            and inp.target_lat is not None
            and inp.target_lon is not None
            and inp.target_course_deg is not None
            and inp.target_speed_knots is not None
        ):
            cpa_nm, tcpa_min = cls.calculate_cpa_tcpa(
                inp.lat,
                inp.lon,
                inp.course_deg,
                inp.speed_knots,
                inp.target_lat,
                inp.target_lon,
                inp.target_course_deg,
                inp.target_speed_knots,
            )
            if cpa_nm < cls.CPA_RISK_THRESHOLD_NM and tcpa_min <= cls.TCPA_RISK_THRESHOLD_MIN:
                collision_risk = True
                advisories.append(
                    f"COLLISION RISK: Target {inp.target_mmsi} CPA {cpa_nm} NM < {cls.CPA_RISK_THRESHOLD_NM} NM, TCPA {tcpa_min} min"
                )

        # Service level classification pursuant to IMO Res. A.1158(32)
        if is_wrong_way or collision_risk:
            service_level = "NAS"  # Navigational Assistance Service
        elif is_outside or inp.speed_knots > 15.0:
            service_level = "TOS"  # Traffic Organization Service
        else:
            service_level = "INS"  # Information Service

        compliant = (not is_wrong_way) and (not is_outside)

        return VtsNavigationResult(
            vessel_mmsi=inp.vessel_mmsi,
            tss_lane_name=inp.tss_lane_name,
            heading_deviation_deg=heading_dev,
            is_wrong_way=is_wrong_way,
            is_outside_corridor=is_outside,
            cpa_nm=cpa_nm,
            tcpa_minutes=tcpa_min,
            collision_risk=collision_risk,
            vts_service_level=service_level,
            colregs_rule10_compliant=compliant,
            advisories=advisories,
        )
