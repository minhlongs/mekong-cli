"""Maritime Phase 366: OCIMF OVID Tug Vetting & Towing Winch Safety Engine.

Compliant with OCIMF OVID Guidelines, IMCA M 149 / CMID, and STCW Code III/3.
Evaluates certified bollard pull, winch brake holding (>= 80% MBL), quick release, and escort forces.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class TugVettingInput:
    tug_id: str
    certified_bollard_pull_t: float
    towline_mbl_t: float
    winch_brake_hold_t: float
    quick_release_time_s: float
    escort_speed_knots: float = 10.0
    has_stcw_iii_3_endorsement: bool = True


@dataclass
class TugVettingResult:
    tug_id: str
    brake_hold_ratio_pct: float
    is_winch_brake_compliant: bool
    is_quick_release_safe: bool
    is_crew_competency_certified: bool
    escort_steering_force_kn: float
    escort_braking_force_kn: float
    overall_vetting_status: str
    advisories: List[str] = field(default_factory=list)


class OvidTugWinchVettingEngine:
    """Evaluates port tug suitability, winch brake capacity, and escort safety according to OCIMF OVID."""

    MIN_BRAKE_HOLD_MBL_PCT: float = 80.0
    MAX_QUICK_RELEASE_SECONDS: float = 3.0
    GRAVITY_ACCEL: float = 9.80665

    @classmethod
    def evaluate(cls, inp: TugVettingInput) -> TugVettingResult:
        advisories: List[str] = []

        # Winch static brake holding capacity vs Towline MBL (>= 80.0%)
        if inp.towline_mbl_t > 0:
            brake_ratio = round((inp.winch_brake_hold_t / inp.towline_mbl_t) * 100.0, 1)
        else:
            brake_ratio = 0.0

        brake_ok = brake_ratio >= cls.MIN_BRAKE_HOLD_MBL_PCT
        if not brake_ok:
            advisories.append(
                f"TỜI KÉO: Lực giữ phanh {brake_ratio}% MBL không đạt tối thiểu {cls.MIN_BRAKE_HOLD_MBL_PCT}% theo OCIMF."
            )

        # Quick release activation time under emergency (< 3.0s)
        release_ok = inp.quick_release_time_s <= cls.MAX_QUICK_RELEASE_SECONDS
        if not release_ok:
            advisories.append(
                f"NHẢ KHẨN CẤP: Thời gian ngắt phanh tời {inp.quick_release_time_s}s vượt quá 3.0s, nguy cơ lật tàu lai (girting)."
            )

        # Crew certification check STCW III/3
        crew_ok = inp.has_stcw_iii_3_endorsement
        if not crew_ok:
            advisories.append(
                "NĂNG LỰC THUYỀN VIÊN: Thuyền trưởng/Máy trưởng thiếu chứng chỉ chuyên môn tàu kéo STCW III/3."
            )

        # Dynamic escort hydrodynamic steering & braking forces at speed (approximate DNV/OCIMF empirical model)
        # Convert bollard pull tonnes to kN: BP (kN) = BP (t) * 9.80665
        bp_kn = inp.certified_bollard_pull_t * cls.GRAVITY_ACCEL
        speed_factor = math.pow(max(0.1, inp.escort_speed_knots / 10.0), 1.2)

        escort_steering_kn = round(1.8 * bp_kn * speed_factor, 1)
        escort_braking_kn = round(1.2 * bp_kn * speed_factor, 1)

        # Overall vetting status determination
        all_passed = brake_ok and release_ok and crew_ok

        if all_passed:
            status = "OVID_APPROVED_SUITABLE"
        elif not brake_ok or not release_ok:
            status = "OVID_REJECTED_EQUIPMENT_DEFECT"
        else:
            status = "OVID_CONDITIONAL_CREW_DEFICIENCY"

        return TugVettingResult(
            tug_id=inp.tug_id,
            brake_hold_ratio_pct=brake_ratio,
            is_winch_brake_compliant=brake_ok,
            is_quick_release_safe=release_ok,
            is_crew_competency_certified=crew_ok,
            escort_steering_force_kn=escort_steering_kn,
            escort_braking_force_kn=escort_braking_kn,
            overall_vetting_status=status,
            advisories=advisories,
        )
