"""Phase 326: IMO Res. A.1050(27) & MSC.1/Circ.1401 Enclosed Space Multi-Gas Entry.

Deterministic, zero-mock enclosed space safety engine with SHA-256 audit trail.
"""

from dataclasses import asdict, dataclass, field
import hashlib
from typing import Any, Dict, List


@dataclass
class EnclosedSpaceGasInput:
    """Tham số đo 4 loại khí và điều kiện an toàn vào không gian kín trên tàu."""
    space_name: str                      # Tên không gian kín (Hầm hàng, Két ballast, Khoang xích, Pumproom)
    oxygen_percent: float                # Nồng độ Oxy O2 (% thể tích, chuẩn an toàn: 20.8% - 22.0%)
    flammable_lel_percent: float         # Nồng độ khí dễ cháy (% LEL, giới hạn tối đa: <= 1.0% LEL)
    hydrogen_sulfide_ppm: float          # Nồng độ khí độc H2S (ppm, giới hạn tối đa: <= 5.0 ppm)
    carbon_monoxide_ppm: float           # Nồng độ khí độc CO (ppm, giới hạn tối đa: <= 25.0 ppm)
    mechanical_ventilation_hours: float  # Thời gian thông gió cơ học liên tục trước khi vào (giờ)
    ventilation_turnover_adequate: bool  # Đã trao đổi tối thiểu 3 lần thể tích không khí trong khoang
    standby_person_equipped: bool        # Người cảnh giới bên ngoài có SCBA, EEBD, bộ đàm liên lạc
    pipes_isolated_blanked: bool         # Các đường ống dẫn dầu/hóa chất đã được lắp bích mù cô lập


@dataclass
class EnclosedSpaceEntryResult:
    """Kết quả thẩm duyệt cấp giấy phép vào không gian kín (Enclosed Space Entry Permit)."""
    space_name: str
    is_entry_permitted: bool
    atmospheric_test_passed: bool
    oxygen_status: str
    gas_hazards_detected: List[str] = field(default_factory=list)
    permit_validity_hours: int = 0
    rejection_reasons: List[str] = field(default_factory=list)
    remarks: str = ""
    audit_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EnclosedSpaceSafetyEngine:
    """Engine đánh giá an toàn đo khí 4-Gas và cấp Entry Permit theo IMO Res. A.1050(27)."""

    O2_MIN_SAFE = 20.8
    O2_MAX_SAFE = 22.0
    LEL_MAX_SAFE = 1.0
    H2S_MAX_SAFE = 5.0
    CO_MAX_SAFE = 25.0

    @classmethod
    def evaluate_entry_permit(cls, inp: EnclosedSpaceGasInput) -> EnclosedSpaceEntryResult:
        rejections: List[str] = []
        gas_hazards: List[str] = []

        if inp.oxygen_percent < cls.O2_MIN_SAFE:
            gas_hazards.append(f"Thiếu dưỡng khí Oxy ({inp.oxygen_percent:.1f}% < {cls.O2_MIN_SAFE}%)")
            rejections.append(f"Nồng độ O2 ({inp.oxygen_percent:.1f}%) không đạt mức dưỡng khí tự nhiên tối thiểu 20.8%.")
            oxygen_status = "OXYGEN_DEFICIENT"
        elif inp.oxygen_percent > cls.O2_MAX_SAFE:
            gas_hazards.append(f"Dư thừa Oxy ({inp.oxygen_percent:.1f}% > {cls.O2_MAX_SAFE}%) - Nguy cơ cháy nổ cao")
            rejections.append(f"Nồng độ O2 ({inp.oxygen_percent:.1f}%) vượt quá 22.0%, tiềm ẩn nguy cơ bắt cháy nổ.")
            oxygen_status = "OXYGEN_ENRICHED"
        else:
            oxygen_status = "OXYGEN_NORMAL"

        if inp.flammable_lel_percent > cls.LEL_MAX_SAFE:
            gas_hazards.append(f"Khí dễ cháy vượt ngưỡng ({inp.flammable_lel_percent:.1f}% LEL > 1.0% LEL)")
            rejections.append(
                f"Khí dễ cháy ({inp.flammable_lel_percent:.1f}% LEL) vượt mức cho phép tối đa 1% LEL."
            )

        if inp.hydrogen_sulfide_ppm > cls.H2S_MAX_SAFE:
            gas_hazards.append(f"Khí kịch độc H2S ({inp.hydrogen_sulfide_ppm:.1f} ppm > 5.0 ppm)")
            rejections.append(
                f"Nồng độ khí độc H2S ({inp.hydrogen_sulfide_ppm:.1f} ppm) vượt giới hạn phơi nhiễm 5 ppm."
            )

        if inp.carbon_monoxide_ppm > cls.CO_MAX_SAFE:
            gas_hazards.append(f"Khí độc CO ({inp.carbon_monoxide_ppm:.1f} ppm > 25.0 ppm)")
            rejections.append(
                f"Nồng độ khí độc CO ({inp.carbon_monoxide_ppm:.1f} ppm) vượt giới hạn phơi nhiễm 25 ppm."
            )

        atmospheric_passed = len(gas_hazards) == 0

        if not inp.ventilation_turnover_adequate:
            rejections.append("Chưa thông gió đạt tối thiểu 3 lần thể tích không khí trong khoang hầm.")

        if not inp.pipes_isolated_blanked:
            rejections.append("Chưa lắp bích mù cách ly hoàn toàn các đường ống kết nối vào khoang.")

        if not inp.standby_person_equipped:
            rejections.append(
                "Người trực cảnh giới bên ngoài chưa được trang bị đầy đủ thiết bị thở SCBA/EEBD và bộ đàm."
            )

        is_permitted = len(rejections) == 0
        permit_validity_hours = 8 if is_permitted else 0

        remarks = (
            "ĐỦ ĐIỀU KIỆN CẤP PHÉP VÀO KHÔNG GIAN KÍN (Permit có hiệu lực tối đa 8 giờ)."
            if is_permitted
            else "CẤM VÀO KHÔNG GIAN KÍN! Không khí độc hại hoặc không tuân thủ an toàn IMO Res. A.1050(27)!"
        )

        raw = f"{inp.space_name}:{is_permitted}:{atmospheric_passed}:{oxygen_status}:{gas_hazards}"
        audit_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return EnclosedSpaceEntryResult(
            space_name=inp.space_name,
            is_entry_permitted=is_permitted,
            atmospheric_test_passed=atmospheric_passed,
            oxygen_status=oxygen_status,
            gas_hazards_detected=gas_hazards,
            permit_validity_hours=permit_validity_hours,
            rejection_reasons=rejections,
            remarks=remarks,
            audit_hash=audit_hash,
        )
