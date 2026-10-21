"""Phase 440: Marine Incinerator Flue Gas Temperature & Oxygen Quench Safety.

IMO MEPC.76(40) / MEPC.244(66) & MARPOL Annex VI Reg 16 compliant incinerator engine.
Monitors combustion chamber temperature, flue exit temperature, residual O2, and furnace draft.
Strictly < 140 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class IncineratorTelemetry:
    combustion_temp_c: float
    flue_gas_temp_c: float
    oxygen_residual_pct: float
    furnace_draft_mbar: float
    sludge_viscosity_cst: float


@dataclass(frozen=True)
class IncineratorAssessment:
    is_safe_to_burn_sludge: bool
    is_quench_damper_required: bool
    is_combustion_temp_normal: bool
    is_flue_temp_normal: bool
    is_oxygen_adequate: bool
    is_draft_safe: bool
    alarms: List[str]
    trips: List[str]
    summary_vi: str
    summary_en: str


class IncineratorEngine:
    MIN_COMBUSTION_TEMP_C: float = 850.0
    MAX_COMBUSTION_TEMP_C: float = 1200.0
    MAX_FLUE_TEMP_NORMAL_C: float = 350.0
    MAX_FLUE_TEMP_TRIP_C: float = 380.0
    MIN_OXYGEN_RESIDUAL_PCT: float = 6.0
    MIN_DRAFT_MBAR: float = -5.0
    MAX_DRAFT_MBAR: float = -2.0
    MAX_SLUDGE_VISCOSITY_CST: float = 15.0

    def evaluate(self, telemetry: IncineratorTelemetry) -> IncineratorAssessment:
        alarms: List[str] = []
        trips: List[str] = []

        is_comb_ok = self.MIN_COMBUSTION_TEMP_C <= telemetry.combustion_temp_c <= self.MAX_COMBUSTION_TEMP_C
        if telemetry.combustion_temp_c < self.MIN_COMBUSTION_TEMP_C:
            alarms.append(f"Combustion chamber temp {telemetry.combustion_temp_c} C below dioxin decomposition minimum {self.MIN_COMBUSTION_TEMP_C} C")
        elif telemetry.combustion_temp_c > self.MAX_COMBUSTION_TEMP_C:
            trips.append(f"Combustion chamber temp {telemetry.combustion_temp_c} C exceeds refractory thermal limit {self.MAX_COMBUSTION_TEMP_C} C")

        is_flue_ok = telemetry.flue_gas_temp_c <= self.MAX_FLUE_TEMP_NORMAL_C
        quench_required = telemetry.flue_gas_temp_c > self.MAX_FLUE_TEMP_NORMAL_C
        if telemetry.flue_gas_temp_c > self.MAX_FLUE_TEMP_TRIP_C:
            trips.append(f"Flue gas exit temp {telemetry.flue_gas_temp_c} C exceeds chimney safety trip {self.MAX_FLUE_TEMP_TRIP_C} C")
        elif quench_required:
            alarms.append(f"Flue gas exit temp {telemetry.flue_gas_temp_c} C high, auto quench damper active")

        is_o2_ok = telemetry.oxygen_residual_pct >= self.MIN_OXYGEN_RESIDUAL_PCT
        if not is_o2_ok:
            alarms.append(f"Residual oxygen {telemetry.oxygen_residual_pct}% vol below clean combustion threshold {self.MIN_OXYGEN_RESIDUAL_PCT}%")

        is_draft_ok = self.MIN_DRAFT_MBAR <= telemetry.furnace_draft_mbar <= self.MAX_DRAFT_MBAR
        if not is_draft_ok:
            trips.append(f"Furnace draft {telemetry.furnace_draft_mbar} mbar outside negative safety window [{self.MIN_DRAFT_MBAR}, {self.MAX_DRAFT_MBAR}] mbar")

        is_visc_ok = telemetry.sludge_viscosity_cst <= self.MAX_SLUDGE_VISCOSITY_CST
        if not is_visc_ok:
            alarms.append(f"Sludge viscosity {telemetry.sludge_viscosity_cst} cSt exceeds atomization limit {self.MAX_SLUDGE_VISCOSITY_CST} cSt")

        safe_to_burn = (
            telemetry.combustion_temp_c >= self.MIN_COMBUSTION_TEMP_C
            and len(trips) == 0
            and is_visc_ok
            and is_o2_ok
        )

        summary_en = (
            "Marine incinerator operating within IMO MEPC parameters"
            if safe_to_burn and not alarms
            else f"Incinerator safety alerts: {len(trips)} trips, {len(alarms)} warnings"
        )
        summary_vi = (
            "Lò đốt rác hàng hải đạt chuẩn phát thải IMO MEPC"
            if safe_to_burn and not alarms
            else f"Cảnh báo an toàn lò đốt: {len(trips)} ngắt khẩn cấp, {len(alarms)} cảnh báo"
        )

        return IncineratorAssessment(
            is_safe_to_burn_sludge=safe_to_burn,
            is_quench_damper_required=quench_required,
            is_combustion_temp_normal=is_comb_ok,
            is_flue_temp_normal=is_flue_ok,
            is_oxygen_adequate=is_o2_ok,
            is_draft_safe=is_draft_ok,
            alarms=alarms,
            trips=trips,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )
