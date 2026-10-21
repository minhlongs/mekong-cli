"""Phase 324: IGC Code LNG/LPG BOG & Custody Transfer CTMS.

Deterministic, zero-mock gas management engine with SHA-256 audit trail.
"""

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Dict


@dataclass
class LngBogInput:
    """Tham số quản lý khí bốc tự nhiên (BOG) tàu chở khí LNG/LPG theo IGC Code Ch.7."""
    cargo_volume_m3: float             # Tổng thể tích hàng lỏng trong các két (m3)
    lng_density_kg_per_m3: float       # Khối lượng riêng LNG (thường ~ 450 - 480 kg/m3)
    latent_heat_kj_per_kg: float       # Nhiệt hóa hơi ẩn (kJ/kg, ví dụ Methane ~ 510 kJ/kg)
    heat_ingress_kw: float             # Nhiệt lượng xâm nhập qua vách cách nhiệt vào két (kW = kJ/s)
    tank_design_marvs_kpa: float       # Áp suất mở van an toàn thiết kế MARVS (kPa)
    current_tank_pressure_kpa: float   # Áp suất hiện tại trong két (kPa)
    reliquefaction_capacity_kg_h: float  # Công suất trạm tái hóa lỏng BOG (kg/giờ)
    engine_gas_consumption_kg_h: float   # Lượng BOG tiêu thụ bởi động cơ DFDE/nồi hơi (kg/giờ)


@dataclass
class LngCtmsInput:
    """Tham số chuyển giao thương mại LNG (Custody Transfer Measurement System - CTMS)."""
    ship_name: str
    opening_volume_m3: float           # Thể tích đo trước khi dỡ hàng (m3)
    closing_volume_m3: float           # Thể tích đo sau khi dỡ hàng (m3)
    trim_list_correction_m3: float     # Lượng hiệu chỉnh hiệu số mớn nước (Trim) và độ nghiêng (List) (m3)
    liquid_temp_c: float               # Nhiệt độ trung bình LNG lỏng (°C)
    liquid_density_kg_per_m3: float    # Khối lượng riêng thực tế của LNG (kg/m3)
    gross_calorific_value_mj_per_kg: float  # Nhiệt trị toàn phần GCV (MJ/kg, ~52-55 MJ/kg)
    vapour_return_volume_m3: float     # Thể tích khí trả về tàu từ bờ (m3)
    vapour_density_kg_per_m3: float    # Khối lượng riêng của hơi khí (kg/m3, ~1.5 - 2.0 kg/m3)


@dataclass
class LngGasManagementResult:
    """Kết quả tính toán quản lý khí hóa lỏng và chuyển giao thương mại."""
    bog_rate_kg_per_hour: float
    natural_bor_percent_per_day: float
    total_bog_disposal_capacity_kg_h: float
    is_pressure_controlled: bool
    gas_combustion_unit_required: bool
    unloaded_liquid_volume_m3: float
    net_delivered_mass_metric_tonnes: float
    total_energy_delivered_mmbtu: float
    remarks: str = ""
    audit_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LngGasCustodyEngine:
    """Engine tính toán BOG và Custody Transfer theo IGC Code & Sổ tay GIIGNL."""

    MJ_TO_MMBTU = 1.0 / 1055.05585

    @classmethod
    def evaluate_bog_and_ctms(cls, bog_in: LngBogInput, ctms_in: LngCtmsInput) -> LngGasManagementResult:
        heat_kj_per_hour = bog_in.heat_ingress_kw * 3600.0
        bog_rate_kg_h = heat_kj_per_hour / max(bog_in.latent_heat_kj_per_kg, 1.0)

        total_cargo_mass_kg = bog_in.cargo_volume_m3 * bog_in.lng_density_kg_per_m3
        daily_bog_kg = bog_rate_kg_h * 24.0
        natural_bor_pct_day = (daily_bog_kg / max(total_cargo_mass_kg, 1.0)) * 100.0

        total_disposal_capacity = bog_in.reliquefaction_capacity_kg_h + bog_in.engine_gas_consumption_kg_h
        gcu_required = False
        is_pressure_controlled = True

        if bog_rate_kg_h > total_disposal_capacity:
            gcu_required = True

        if bog_in.current_tank_pressure_kpa >= bog_in.tank_design_marvs_kpa:
            is_pressure_controlled = False

        raw_volume_transferred = (ctms_in.opening_volume_m3 - ctms_in.closing_volume_m3)
        net_unloaded_volume = raw_volume_transferred + ctms_in.trim_list_correction_m3

        liquid_mass_kg = net_unloaded_volume * ctms_in.liquid_density_kg_per_m3
        vapour_mass_kg = ctms_in.vapour_return_volume_m3 * ctms_in.vapour_density_kg_per_m3
        net_delivered_mass_kg = max(liquid_mass_kg - vapour_mass_kg, 0.0)
        net_delivered_mass_tonnes = net_delivered_mass_kg / 1000.0

        total_energy_mj = net_delivered_mass_kg * ctms_in.gross_calorific_value_mj_per_kg
        total_energy_mmbtu = total_energy_mj * cls.MJ_TO_MMBTU

        remarks = (
            f"BOG phát sinh: {bog_rate_kg_h:.1f} kg/h (BOR: {natural_bor_pct_day:.3f}%/ngày). "
            f"Khối lượng giao ròng: {net_delivered_mass_tonnes:,.2f} MT ({total_energy_mmbtu:,.1f} MMBtu)."
        )

        raw = f"{bog_rate_kg_h:.2f}:{natural_bor_pct_day:.4f}:{net_delivered_mass_tonnes:.2f}:{total_energy_mmbtu:.2f}"
        audit_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return LngGasManagementResult(
            bog_rate_kg_per_hour=round(bog_rate_kg_h, 2),
            natural_bor_percent_per_day=round(natural_bor_pct_day, 4),
            total_bog_disposal_capacity_kg_h=round(total_disposal_capacity, 2),
            is_pressure_controlled=is_pressure_controlled,
            gas_combustion_unit_required=gcu_required,
            unloaded_liquid_volume_m3=round(net_unloaded_volume, 3),
            net_delivered_mass_metric_tonnes=round(net_delivered_mass_tonnes, 2),
            total_energy_delivered_mmbtu=round(total_energy_mmbtu, 2),
            remarks=remarks,
            audit_hash=audit_hash,
        )
