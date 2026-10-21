"""Phase 439: Bow Thruster Hydraulic Header Pressure & Oil Temperature Interlocks.

DNV-RU-SHIP Pt.4 Ch.5 & SOLAS II-1 Reg 29 compliant hydraulic control engine.
Monitors servo header pressure, oil temperature, gravity tank level, and pitch deviation.
Strictly < 140 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BowThrusterTelemetry:
    header_pressure_bar: float
    oil_temperature_c: float
    gravity_tank_level_pct: float
    pitch_demand_deg: float
    pitch_actual_deg: float
    motor_current_a: float


@dataclass(frozen=True)
class BowThrusterAssessment:
    is_operational: bool
    pitch_deviation_deg: float
    is_pressure_normal: bool
    is_temp_normal: bool
    is_gravity_tank_adequate: bool
    is_pitch_within_tolerance: bool
    alarms: List[str]
    trips: List[str]
    summary_vi: str
    summary_en: str


class BowThrusterEngine:
    MIN_OPERATING_PRESSURE_BAR: float = 140.0
    MIN_EMERGENCY_PRESSURE_BAR: float = 120.0
    MAX_NORMAL_TEMP_C: float = 60.0
    MAX_TRIP_TEMP_C: float = 75.0
    MIN_GRAVITY_TANK_PCT: float = 35.0
    MAX_PITCH_ERROR_TOLERANCE_DEG: float = 1.5

    def evaluate(self, telemetry: BowThrusterTelemetry) -> BowThrusterAssessment:
        alarms: List[str] = []
        trips: List[str] = []

        pitch_dev = round(abs(telemetry.pitch_demand_deg - telemetry.pitch_actual_deg), 2)
        is_pitch_ok = pitch_dev <= self.MAX_PITCH_ERROR_TOLERANCE_DEG
        if not is_pitch_ok:
            alarms.append(f"Pitch error {pitch_dev} deg exceeds {self.MAX_PITCH_ERROR_TOLERANCE_DEG} deg")

        is_press_ok = telemetry.header_pressure_bar >= self.MIN_OPERATING_PRESSURE_BAR
        if telemetry.header_pressure_bar < self.MIN_EMERGENCY_PRESSURE_BAR:
            trips.append(f"Header pressure {telemetry.header_pressure_bar} bar below critical trip limit {self.MIN_EMERGENCY_PRESSURE_BAR} bar")
        elif not is_press_ok:
            alarms.append(f"Header pressure {telemetry.header_pressure_bar} bar below normal operating threshold {self.MIN_OPERATING_PRESSURE_BAR} bar")

        is_temp_ok = telemetry.oil_temperature_c <= self.MAX_NORMAL_TEMP_C
        if telemetry.oil_temperature_c > self.MAX_TRIP_TEMP_C:
            trips.append(f"Hydraulic oil temperature {telemetry.oil_temperature_c} C exceeds critical trip limit {self.MAX_TRIP_TEMP_C} C")
        elif not is_temp_ok:
            alarms.append(f"Hydraulic oil temperature {telemetry.oil_temperature_c} C exceeds warning limit {self.MAX_NORMAL_TEMP_C} C")

        is_tank_ok = telemetry.gravity_tank_level_pct >= self.MIN_GRAVITY_TANK_PCT
        if not is_tank_ok:
            alarms.append(f"Gravity tank level {telemetry.gravity_tank_level_pct}% below seal minimum {self.MIN_GRAVITY_TANK_PCT}%")

        operational = len(trips) == 0

        summary_en = (
            "Bow thruster hydraulics operational"
            if operational and not alarms
            else f"Bow thruster warning/tripped with {len(trips)} trips and {len(alarms)} alarms"
        )
        summary_vi = (
            "Hệ thống thủy lực chân vịt mũi hoạt động chuẩn xác"
            if operational and not alarms
            else f"Chân vịt mũi gặp sự cố với {len(trips)} ngắt khẩn cấp và {len(alarms)} cảnh báo"
        )

        return BowThrusterAssessment(
            is_operational=operational,
            pitch_deviation_deg=pitch_dev,
            is_pressure_normal=is_press_ok,
            is_temp_normal=is_temp_ok,
            is_gravity_tank_adequate=is_tank_ok,
            is_pitch_within_tolerance=is_pitch_ok,
            alarms=alarms,
            trips=trips,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )
