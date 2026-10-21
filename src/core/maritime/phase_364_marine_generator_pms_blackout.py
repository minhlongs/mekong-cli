"""Maritime Phase 364: Marine Generator PMS & Blackout Prevention Engine.

Compliant with SOLAS II-1/Reg 53, IEC 60092-202, and DNV/ABS Marine Power Rules.
Evaluates active load sharing, standby DG auto-start, preferential tripping, and blackout trip.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class MarineGeneratorUnit:
    gen_id: str
    rated_kw: float
    current_kw: float
    frequency_hz: float
    voltage_pct: float
    is_online: bool = True


@dataclass
class PmsEvaluationInput:
    generators: List[MarineGeneratorUnit]
    grid_nominal_hz: float = 60.0
    sustained_overload_seconds: float = 0.0


@dataclass
class PmsEvaluationResult:
    total_running_kw: float
    total_capacity_kw: float
    total_load_pct: float
    is_auto_start_required: bool
    is_load_sharing_balanced: bool
    max_imbalance_pct: float
    shedding_stage: int
    blackout_risk_status: str
    advisories: List[str] = field(default_factory=list)


class MarineGeneratorPmsEngine:
    """Evaluates marine switchboard power management and prevents cascading blackout."""

    AUTO_START_THRESHOLD_PCT: float = 85.0
    STAGE_1_SHED_PCT: float = 90.0
    STAGE_2_SHED_PCT: float = 95.0
    STAGE_3_SHED_PCT: float = 100.0
    MAX_LOAD_IMBALANCE_PCT: float = 10.0
    UNDER_FREQ_TRIP_HZ: float = 57.0  # 60Hz nominal under-frequency trip
    UNDER_VOLT_TRIP_PCT: float = 85.0

    @classmethod
    def evaluate(cls, inp: PmsEvaluationInput) -> PmsEvaluationResult:
        advisories: List[str] = []
        online_gens = [g for g in inp.generators if g.is_online]

        if not online_gens:
            return PmsEvaluationResult(
                total_running_kw=0.0,
                total_capacity_kw=0.0,
                total_load_pct=0.0,
                is_auto_start_required=True,
                is_load_sharing_balanced=False,
                max_imbalance_pct=0.0,
                shedding_stage=3,
                blackout_risk_status="BLACKOUT_COLLAPSE",
                advisories=["KHẨN CẤP: Không có máy phát điện nào đang hòa đồng bộ trực tuyến."],
            )

        total_running_kw = sum(g.current_kw for g in online_gens)
        total_capacity_kw = sum(g.rated_kw for g in online_gens)
        total_load_pct = round((total_running_kw / total_capacity_kw) * 100.0, 1) if total_capacity_kw > 0 else 0.0

        # Load sharing balance check across online generators
        gen_load_ratios = [g.current_kw / g.rated_kw for g in online_gens if g.rated_kw > 0]
        if len(gen_load_ratios) > 1:
            max_imbalance_pct = round((max(gen_load_ratios) - min(gen_load_ratios)) * 100.0, 1)
            is_balanced = max_imbalance_pct <= cls.MAX_LOAD_IMBALANCE_PCT
        else:
            max_imbalance_pct = 0.0
            is_balanced = True

        if not is_balanced:
            advisories.append(
                f"CẢNH BÁO: Lệch tải giữa các tổ máy phát {max_imbalance_pct}% vượt mức cho phép 10.0% (IEC 60092-202)."
            )

        # Standby DG auto-start trigger at >= 85% MCR
        auto_start = total_load_pct >= cls.AUTO_START_THRESHOLD_PCT
        if auto_start:
            advisories.append(
                f"PMS TỰ ĐỘNG: Phụ tải lưới đạt {total_load_pct}% MCR (>= 85%), lệnh tự động khởi động máy phát dự phòng."
            )

        # Preferential tripping stages determination
        shedding_stage = 0
        if total_load_pct >= cls.STAGE_3_SHED_PCT:
            shedding_stage = 3
            advisories.append("SA THẢI PHỤ TẢI CẤP 3: Cắt tải công nghiệp phụ (bơm chuyển dầu, máy nén khí).")
        elif total_load_pct >= cls.STAGE_2_SHED_PCT:
            shedding_stage = 2
            advisories.append("SA THẢI PHỤ TẢI CẤP 2: Cắt quạt thông gió hầm hàng, máy sấy khí boong.")
        elif total_load_pct >= cls.STAGE_1_SHED_PCT:
            shedding_stage = 1
            advisories.append("SA THẢI PHỤ TẢI CẤP 1: Cắt điều hòa không khí sinh hoạt, bếp điện phụ.")

        # Emergency under-frequency / under-voltage blackout trip
        min_freq = min(g.frequency_hz for g in online_gens)
        min_volt = min(g.voltage_pct for g in online_gens)

        is_blackout_trip = (
            min_freq <= cls.UNDER_FREQ_TRIP_HZ or min_volt <= cls.UNDER_VOLT_TRIP_PCT
        ) and inp.sustained_overload_seconds >= 0.5

        if is_blackout_trip:
            blackout_status = "EMERGENCY_BLACKOUT_TRIP"
            advisories.append(
                f"BẢO VỆ BLACKOUT: Tần số sụt {min_freq}Hz (<=57.0Hz) hoặc áp sụt {min_volt}% (>0.5s), trip bảo vệ rơ le."
            )
        elif shedding_stage > 0:
            blackout_status = "LOAD_SHEDDING_ACTIVE"
        elif auto_start:
            blackout_status = "HIGH_LOAD_STANDBY_START"
        else:
            blackout_status = "NORMAL_STABLE"

        return PmsEvaluationResult(
            total_running_kw=round(total_running_kw, 1),
            total_capacity_kw=round(total_capacity_kw, 1),
            total_load_pct=total_load_pct,
            is_auto_start_required=auto_start,
            is_load_sharing_balanced=is_balanced,
            max_imbalance_pct=max_imbalance_pct,
            shedding_stage=shedding_stage,
            blackout_risk_status=blackout_status,
            advisories=advisories,
        )
