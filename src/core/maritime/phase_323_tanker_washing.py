"""Phase 323: MARPOL Annex I COW & IBC Code Chemical Tanker Prewash.

Deterministic, zero-mock compliance engine with SHA-256 audit trail.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List


class ChemicalPollutionCategory(str, Enum):
    """Phân loại chất lỏng độc hại NLS theo IBC Code & MARPOL Annex II."""
    CAT_X = "CAT_X"  # Nguy hại nghiêm trọng nhất, bắt buộc Prewash và xả lên bờ
    CAT_Y = "CAT_Y"  # Nguy hại, rửa trước nếu nhớt cao hoặc điểm đông cao
    CAT_Z = "CAT_Z"  # Nguy hại nhỏ
    OS = "OS"        # Other Substances - Không độc hại


@dataclass
class CrudeOilWashingInput:
    """Tham số đầu vào kiểm tra quy trình rửa dầu thô (COW) theo MARPOL Annex I Reg 33/35."""
    tank_id: str
    inert_gas_o2_percent: float          # Hàm lượng O2 trong khí trơ (phải <= 8.0%)
    tank_pressure_mmwg: float            # Áp suất dương duy trì trong két (>= 100 mmWG)
    cow_machine_pressure_bar: float      # Áp suất dầu thô cấp cho súng rửa (>= 7.0 bar)
    remaining_sludge_volume_m3: float    # Lượng cặn dầu lắng đọng sau rửa (m3)
    max_allowable_sludge_m3: float       # Ngưỡng cặn tối đa cho phép theo tài liệu phê duyệt (m3)
    is_draining_dry: bool                # Hệ thống Stripping hút khô đáy két hiệu quả


@dataclass
class ChemicalTankerPrewashInput:
    """Tham số rửa két hóa chất theo IBC Code Ch.16 & P/A Manual."""
    tank_id: str
    cargo_category: ChemicalPollutionCategory
    viscosity_at_unloading_temp_mpa_s: float  # Độ nhớt tại nhiệt độ dỡ hàng (mPa.s)
    cargo_melting_point_c: float              # Điểm đông đặc của hàng hóa (°C)
    unloading_temperature_c: float            # Nhiệt độ hàng khi dỡ (°C)
    stripping_residue_liters: float           # Lượng cặn còn lại sau hút vét (lít)
    effluent_concentration_ppm: float         # Nồng độ hóa chất trong nước rửa xả lên bờ (ppm)
    vessel_speed_knots: float                 # Tốc độ hành trình khi xả nước rửa biển (knots)
    distance_from_shore_nm: float             # Khoảng cách tới bờ biển gần nhất (NM)
    water_depth_meters: float                 # Độ sâu luồng nước (m)


@dataclass
class TankerWashingResult:
    """Kết quả thẩm định quy trình rửa két tàu dầu và tàu hóa chất."""
    tank_id: str
    cow_permitted: bool
    prewash_mandatory: bool
    discharge_to_sea_permitted: bool
    rejection_reasons: List[str] = field(default_factory=list)
    remarks: str = ""
    audit_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TankerWashingComplianceEngine:
    """Engine thẩm tra kỹ thuật rửa tàu dầu thô (COW) và hóa chất (IBC Code P/A Manual)."""

    @staticmethod
    def evaluate_cow(inp: CrudeOilWashingInput) -> TankerWashingResult:
        rejections: List[str] = []

        if inp.inert_gas_o2_percent > 8.0:
            rejections.append(
                f"Nồng độ O2 ({inp.inert_gas_o2_percent:.1f}%) vượt ngưỡng an toàn tối đa 8.0%. "
                "Nguy cơ nổ hầm hàng, nghiêm cấm rửa dầu thô (COW)!"
            )

        if inp.tank_pressure_mmwg < 100.0:
            rejections.append(
                f"Áp suất két ({inp.tank_pressure_mmwg:.1f} mmWG) nhỏ hơn 100 mmWG. "
                "Không đảm bảo áp suất dương ngăn không khí bên ngoài lọt vào két."
            )

        if inp.cow_machine_pressure_bar < 7.0:
            rejections.append(
                f"Áp suất dầu rửa ({inp.cow_machine_pressure_bar:.1f} bar) nhỏ hơn ngưỡng thiết kế tối thiểu 7.0 bar."
            )

        if not inp.is_draining_dry:
            rejections.append("Hệ thống hút khô vét két (Stripping) không hoạt động hiệu quả hoặc bị đọng dầu.")

        if inp.remaining_sludge_volume_m3 > inp.max_allowable_sludge_m3:
            rejections.append(
                f"Thể tích cặn tồn lưu ({inp.remaining_sludge_volume_m3:.3f} m3) vượt quá giới hạn "
                f"cho phép ({inp.max_allowable_sludge_m3:.3f} m3)."
            )

        cow_permitted = len(rejections) == 0
        remarks = (
            "Quy trình rửa dầu thô (COW) an toàn và tuân thủ MARPOL Annex I."
            if cow_permitted
            else "Quy trình rửa dầu thô BỊ ĐÌNH CHỈ do vi phạm an toàn phòng chống cháy nổ / kỹ thuật!"
        )

        raw = f"{inp.tank_id}:{cow_permitted}:{rejections}"
        audit_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return TankerWashingResult(
            tank_id=inp.tank_id,
            cow_permitted=cow_permitted,
            prewash_mandatory=False,
            discharge_to_sea_permitted=False,
            rejection_reasons=rejections,
            remarks=remarks,
            audit_hash=audit_hash,
        )

    @staticmethod
    def evaluate_chemical_prewash(inp: ChemicalTankerPrewashInput) -> TankerWashingResult:
        rejections: List[str] = []
        prewash_mandatory = False

        temp_margin = inp.unloading_temperature_c - inp.cargo_melting_point_c
        is_high_viscosity = inp.viscosity_at_unloading_temp_mpa_s >= 50.0
        is_solidifying = temp_margin < 15.0

        if inp.cargo_category == ChemicalPollutionCategory.CAT_X:
            prewash_mandatory = True
        elif inp.cargo_category in (ChemicalPollutionCategory.CAT_Y, ChemicalPollutionCategory.CAT_Z):
            if is_high_viscosity or is_solidifying:
                prewash_mandatory = True

        if prewash_mandatory and inp.cargo_category == ChemicalPollutionCategory.CAT_X:
            if inp.effluent_concentration_ppm > 1000.0:
                rejections.append(
                    f"Nồng độ cặn trong nước rửa két ({inp.effluent_concentration_ppm:.1f} ppm) "
                    "vượt mức 1,000 ppm (0.1% wt). Bắt buộc tiếp tục rửa và bơm lên trạm tiếp nhận trên bờ!"
                )
            if inp.stripping_residue_liters > 75.0:
                rejections.append(
                    f"Cặn tồn dư sau hút vét ({inp.stripping_residue_liters:.1f} lít) vượt quá mức tối đa 75 lít."
                )

        discharge_sea_possible = True
        if inp.vessel_speed_knots < 7.0:
            rejections.append(f"Tốc độ tàu ({inp.vessel_speed_knots:.1f} knots) nhỏ hơn tốc độ tối thiểu 7.0 knots.")
            discharge_sea_possible = False
        if inp.distance_from_shore_nm < 12.0:
            rejections.append(f"Khoảng cách bờ ({inp.distance_from_shore_nm:.1f} NM) nhỏ hơn tối thiểu 12.0 NM.")
            discharge_sea_possible = False
        if inp.water_depth_meters < 25.0:
            rejections.append(f"Độ sâu nước ({inp.water_depth_meters:.1f} m) nhỏ hơn độ sâu tối thiểu 25.0 m.")
            discharge_sea_possible = False

        discharge_permitted = (
            discharge_sea_possible
            and (
                not prewash_mandatory
                or inp.cargo_category != ChemicalPollutionCategory.CAT_X
                or inp.effluent_concentration_ppm <= 1000.0
            )
        )

        remarks = (
            "Quy trình rửa két hóa chất và xả thải tuân thủ IBC Code & MARPOL Annex II."
            if discharge_permitted
            else "Vi phạm quy trình P/A Manual hoặc điều kiện xả thải ngoài khơi!"
        )

        raw = f"{inp.tank_id}:{inp.cargo_category}:{prewash_mandatory}:{discharge_permitted}:{rejections}"
        audit_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return TankerWashingResult(
            tank_id=inp.tank_id,
            cow_permitted=False,
            prewash_mandatory=prewash_mandatory,
            discharge_to_sea_permitted=discharge_permitted,
            rejection_reasons=rejections,
            remarks=remarks,
            audit_hash=audit_hash,
        )
