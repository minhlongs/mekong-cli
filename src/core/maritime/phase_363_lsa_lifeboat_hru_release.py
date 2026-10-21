"""Maritime Phase 363: LSA Free-Fall Lifeboat & Hydrostatic Release Unit (HRU) Engine.

Compliant with SOLAS III/Reg 13 & 33, IMO LSA Code Ch. IV/VI, and IMO Res. MSC.81(70).
Evaluates water entry trajectory, occupant g-load deceleration, and HRU hydrostatic activation.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class LifeboatHruInput:
    boat_id: str
    drop_height_m: float
    ramp_angle_deg: float
    entry_angle_deg: float
    peak_acceleration_g: float
    hru_water_depth_m: float
    is_manual_interlock_released: bool = True


@dataclass
class LifeboatHruResult:
    boat_id: str
    impact_velocity_m_s: float
    is_entry_angle_compliant: bool
    is_acceleration_tolerable: bool
    is_hru_depth_compliant: bool
    is_safe_to_launch_or_float: bool
    safety_status: str
    advisories: List[str] = field(default_factory=list)


class LifeboatHruReleaseEngine:
    """Evaluates free-fall lifeboat launch dynamics and HRU hydrostatic activation."""

    MIN_ENTRY_ANGLE_DEG: float = 50.0
    MAX_ENTRY_ANGLE_DEG: float = 65.0
    MAX_ALLOWABLE_G_FORCE: float = 15.0  # IMO MSC.81(70) occupant headward g-limit
    MIN_HRU_DEPTH_M: float = 1.5         # Must not release on wave action < 1.5m
    MAX_HRU_DEPTH_M: float = 4.0         # Must release before sinking beyond 4.0m
    GRAVITY_ACCEL: float = 9.80665

    @classmethod
    def evaluate(cls, inp: LifeboatHruInput) -> LifeboatHruResult:
        advisories: List[str] = []

        # Theoretical water impact velocity v = sqrt(2 * g * h)
        impact_vel = round(math.sqrt(max(0.0, 2.0 * cls.GRAVITY_ACCEL * inp.drop_height_m)), 2)

        # Entry angle check (50° - 65°)
        entry_angle_ok = cls.MIN_ENTRY_ANGLE_DEG <= inp.entry_angle_deg <= cls.MAX_ENTRY_ANGLE_DEG
        if not entry_angle_ok:
            if inp.entry_angle_deg < cls.MIN_ENTRY_ANGLE_DEG:
                advisories.append(
                    f"CẢNH BÁO: Góc vào nước {inp.entry_angle_deg}° quá nông (< 50°), nguy cơ va đập sống xuồng."
                )
            else:
                advisories.append(
                    f"CẢNH BÁO: Góc vào nước {inp.entry_angle_deg}° quá dốc (> 65°), nguy cơ lặn sâu mất kiểm soát."
                )

        # Peak occupant deceleration g-force check
        accel_tolerable = inp.peak_acceleration_g <= cls.MAX_ALLOWABLE_G_FORCE
        if not accel_tolerable:
            advisories.append(
                f"NGUY HIỂM: Gia tốc va chạm {inp.peak_acceleration_g}g vượt ngưỡng 15.0g theo IMO Res. MSC.81(70)."
            )

        # HRU depth check (1.5m - 4.0m)
        hru_ok = cls.MIN_HRU_DEPTH_M <= inp.hru_water_depth_m <= cls.MAX_HRU_DEPTH_M
        if not hru_ok:
            if inp.hru_water_depth_m < cls.MIN_HRU_DEPTH_M:
                advisories.append(
                    f"CHÚ Ý: Độ sâu HRU {inp.hru_water_depth_m}m chưa đạt ngưỡng tối thiểu 1.5m (tránh nhả do sóng vỗ)."
                )
            else:
                advisories.append(
                    f"NGUY HIỂM: Độ sâu HRU {inp.hru_water_depth_m}m vượt quá 4.0m mà chưa cắt dây chằng tự nổi."
                )

        # Manual interlock check for free-fall launch
        if not inp.is_manual_interlock_released:
            advisories.append("KHÓA AN TOÀN: Chốt khóa liên động cơ khí hai cấp (dual-lock) chưa mở.")

        # Determine overall safety status
        is_safe = entry_angle_ok and accel_tolerable and (hru_ok or inp.hru_water_depth_m == 0.0)

        if is_safe and inp.is_manual_interlock_released:
            safety_status = "READY_FOR_DEPLOYMENT"
        elif not accel_tolerable or inp.hru_water_depth_m > cls.MAX_HRU_DEPTH_M:
            safety_status = "CRITICAL_FAILURE"
        else:
            safety_status = "WARNING_RESTRICTED"

        return LifeboatHruResult(
            boat_id=inp.boat_id,
            impact_velocity_m_s=impact_vel,
            is_entry_angle_compliant=entry_angle_ok,
            is_acceleration_tolerable=accel_tolerable,
            is_hru_depth_compliant=hru_ok,
            is_safe_to_launch_or_float=is_safe,
            safety_status=safety_status,
            advisories=advisories,
        )


LifeboatHruEngine = LifeboatHruReleaseEngine

