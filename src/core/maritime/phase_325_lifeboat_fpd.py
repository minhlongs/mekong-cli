"""Phase 325: SOLAS III/20 & MSC.1/Circ.1392 Lifeboat FPD Safety Release Engine.

Deterministic, zero-mock lifeboat safety engine with SHA-256 audit trail.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List


class LifeboatReleaseMode(str, Enum):
    """Chế độ nhả móc xuồng cứu sinh theo SOLAS III."""
    OFF_LOAD = "OFF_LOAD"  # Nhả khi xuồng đã nổi hoàn toàn trên mặt nước
    ON_LOAD = "ON_LOAD"    # Nhả khi xuồng còn đang treo trên dây (tình huống khẩn cấp)


@dataclass
class LifeboatFpdInput:
    """Tham số đánh giá an toàn cơ cấu móc nhả xuồng cứu sinh và thiết bị giữ FPD."""
    lifeboat_id: str
    release_mode: LifeboatReleaseMode
    lifeboat_total_weight_kg: float      # Trọng lượng xuồng đầy tải người và trang bị (kg)
    hook_swl_tonnes: float               # Tải trọng làm việc an toàn của mỗi móc nâng SWL (tấn)
    fpd_sling_mbl_tonnes: float          # Tải trọng đứt gãy tối thiểu của dây an toàn FPD (MBL, tấn)
    hydrostatic_interlock_engaged: bool  # Cảm biến thủy tĩnh báo xuồng đã nổi trên nước
    hook_cam_wear_mm: float              # Độ mòn khấc then khóa của móc treo (mm, tối đa <= 2.0 mm)
    fpd_pins_fitted: bool                # Đã gắn chốt chặn FPD an toàn (Mechanical Locking Pins)
    emergency_override_used: bool        # Có sử dụng cơ chế mở khóa cưỡng bức không


@dataclass
class LifeboatReleaseSafetyResult:
    """Kết quả đánh giá an toàn nhả xuồng cứu sinh theo MSC.1/Circ.1392 & Circ.1327."""
    lifeboat_id: str
    is_release_permitted: bool
    fpd_safety_factor: float
    accidental_release_risk: bool
    crew_drill_in_boat_permitted: bool
    rejection_reasons: List[str] = field(default_factory=list)
    remarks: str = ""
    audit_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LifeboatFpdSafetyEngine:
    """Engine đánh giá an toàn móc nhả xuồng cứu sinh và thiết bị bảo vệ chống rơi FPD."""

    @staticmethod
    def evaluate_lifeboat_safety(inp: LifeboatFpdInput) -> LifeboatReleaseSafetyResult:
        rejections: List[str] = []
        accidental_risk = False

        hook_load_tonnes = (inp.lifeboat_total_weight_kg / 1000.0) / 2.0
        fpd_safety_factor = (
            inp.fpd_sling_mbl_tonnes / max(hook_load_tonnes, 0.001)
            if hook_load_tonnes > 0
            else 0.0
        )

        if fpd_safety_factor < 6.0:
            rejections.append(
                f"Hệ số an toàn cáp chống rơi FPD ({fpd_safety_factor:.2f}) nhỏ hơn 6.0 lần tải trọng móc. "
                "Vi phạm hướng dẫn an toàn MSC.1/Circ.1327!"
            )

        if inp.hook_cam_wear_mm > 2.0:
            accidental_risk = True
            rejections.append(
                f"Độ mòn khấc cam móc ({inp.hook_cam_wear_mm:.1f} mm) vượt dung sai an toàn 2.0 mm. "
                "Nguy cơ bật móc ngoài ý muốn (accidental release) cực kỳ nguy hiểm!"
            )

        if inp.release_mode == LifeboatReleaseMode.OFF_LOAD:
            if not inp.hydrostatic_interlock_engaged:
                rejections.append(
                    "Cảm biến thủy tĩnh chưa kích hoạt (xuồng chưa nổi hoàn toàn trên mặt nước). "
                    "Khóa liên động Off-load ngăn chặn nhả cáp!"
                )
        elif inp.release_mode == LifeboatReleaseMode.ON_LOAD:
            if not inp.emergency_override_used:
                rejections.append(
                    "Chế độ On-load yêu cầu kích hoạt chốt phá khóa khẩn cấp 2 tầng (Two-tier Emergency Override)."
                )

        crew_drill_permitted = (
            inp.fpd_pins_fitted and fpd_safety_factor >= 6.0 and inp.hook_cam_wear_mm <= 2.0
        )

        is_permitted = len(rejections) == 0
        remarks = (
            "Cơ cấu móc nhả và FPD đạt chuẩn an toàn SOLAS III & IMO MSC.1/Circ.1392."
            if is_permitted
            else "CẤM THẢ XUỒNG! Cơ cấu nhả không đảm bảo an toàn sinh mạng thuyền viên!"
        )

        raw = f"{inp.lifeboat_id}:{inp.release_mode}:{is_permitted}:{accidental_risk}:{crew_drill_permitted}"
        audit_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return LifeboatReleaseSafetyResult(
            lifeboat_id=inp.lifeboat_id,
            is_release_permitted=is_permitted,
            fpd_safety_factor=round(fpd_safety_factor, 2),
            accidental_release_risk=accidental_risk,
            crew_drill_in_boat_permitted=crew_drill_permitted,
            rejection_reasons=rejections,
            remarks=remarks,
            audit_hash=audit_hash,
        )
