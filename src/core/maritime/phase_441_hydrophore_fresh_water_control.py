"""Phase 441: Hydrophore Sanitary Fresh Water Pressure Vessel Dual-Pump Control.

WHO Guide to Ship Sanitation & ClassNK Rules Pt.D compliant fresh water supply engine.
Monitors cut-in/cut-out pressures, air-cushion volume, and UV dosage.
Strictly < 130 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class HydrophoreTelemetry:
    system_pressure_bar: float
    water_volume_pct: float
    uv_intensity_dose_mj_cm2: float


@dataclass(frozen=True)
class HydrophoreAssessment:
    is_pump1_running: bool
    is_pump2_running: bool
    is_air_charge_valve_open: bool
    is_pressure_normal: bool
    is_air_ratio_normal: bool
    is_uv_sterilization_adequate: bool
    alarms: List[str]
    trips: List[str]
    summary_vi: str
    summary_en: str


class HydrophoreEngine:
    CUT_IN_PRESSURE_BAR: float = 3.20
    CUT_OUT_PRESSURE_BAR: float = 5.00
    DUAL_PUMP_STAGING_PRESSURE_BAR: float = 2.80
    MIN_WATER_RATIO_PCT: float = 60.0
    MAX_WATER_RATIO_PCT: float = 75.0
    MIN_UV_DOSE_MJ_CM2: float = 40.0

    def evaluate(self, telemetry: HydrophoreTelemetry, current_pump1_running: bool) -> HydrophoreAssessment:
        alarms: List[str] = []
        trips: List[str] = []

        is_pump1_running = current_pump1_running
        if telemetry.system_pressure_bar <= self.CUT_IN_PRESSURE_BAR:
            is_pump1_running = True
        elif telemetry.system_pressure_bar >= self.CUT_OUT_PRESSURE_BAR:
            is_pump1_running = False

        is_pump2_running = telemetry.system_pressure_bar <= self.DUAL_PUMP_STAGING_PRESSURE_BAR

        is_press_ok = telemetry.system_pressure_bar >= self.DUAL_PUMP_STAGING_PRESSURE_BAR
        if not is_press_ok:
            alarms.append(f"System pressure {telemetry.system_pressure_bar} bar below dual-staging threshold {self.DUAL_PUMP_STAGING_PRESSURE_BAR} bar")

        is_air_valve_open = telemetry.water_volume_pct > self.MAX_WATER_RATIO_PCT
        is_air_ratio_ok = self.MIN_WATER_RATIO_PCT <= telemetry.water_volume_pct <= self.MAX_WATER_RATIO_PCT
        if is_air_valve_open:
            alarms.append(f"Waterlogged vessel ({telemetry.water_volume_pct}% water), control air charging active")
        elif telemetry.water_volume_pct < self.MIN_WATER_RATIO_PCT:
            alarms.append(f"Excess air cushion ({telemetry.water_volume_pct}% water), bleeding required")

        is_uv_ok = telemetry.uv_intensity_dose_mj_cm2 >= self.MIN_UV_DOSE_MJ_CM2
        if not is_uv_ok:
            trips.append(f"UV sterilization dose {telemetry.uv_intensity_dose_mj_cm2} mJ/cm2 below WHO minimum {self.MIN_UV_DOSE_MJ_CM2} mJ/cm2 limit")

        operational = len(trips) == 0

        summary_en = (
            "Hydrophore system and UV disinfection normal"
            if operational and not alarms
            else f"Hydrophore alerts: {len(trips)} sterile trips, {len(alarms)} condition warnings"
        )
        summary_vi = (
            "Hệ thống bồn áp lực nước ngọt và tiệt trùng UV hoạt động bình thường"
            if operational and not alarms
            else f"Mạng nước sinh hoạt cảnh báo: {len(trips)} lỗi tiệt trùng, {len(alarms)} lỗi màng khí"
        )

        return HydrophoreAssessment(
            is_pump1_running=is_pump1_running,
            is_pump2_running=is_pump2_running,
            is_air_charge_valve_open=is_air_valve_open,
            is_pressure_normal=is_press_ok,
            is_air_ratio_normal=is_air_ratio_ok,
            is_uv_sterilization_adequate=is_uv_ok,
            alarms=alarms,
            trips=trips,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )
