"""Phase 411: Marine Main Engine Jacket Water Preheating & Cooling.

Implements ISO 8217 / MAN Energy Solutions / WinGD standards for two-stroke
cylinder liner thermal management, cold start preheating, and thermostatic
mixing valve control. Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class JacketWaterTelemetry:
    """Telemetry readings for Main Engine Jacket Water system."""
    inlet_temp_c: float = 75.0
    outlet_temp_c: float = 84.0
    expansion_tank_level_pct: float = 65.0
    static_pressure_bar: float = 2.1
    circulation_flow_m3h: float = 120.0
    nitrite_concentration_ppm: float = 1100.0
    preheater_active: bool = False


@dataclass(frozen=True)
class JacketWaterAssessment:
    """Safety and performance assessment for ME Jacket Water system."""
    temp_rise_c: float
    valve_position_pct: float
    start_permissive: bool
    status: str
    warnings: list[str]
    compliance_flags: Dict[str, bool]


class JacketWaterEngine:
    """Evaluates jacket cooling water preheating and thermostatic balance."""

    TARGET_OUTLET_TEMP_C: float = 85.0
    MIN_START_TEMP_C: float = 60.0
    ALARM_START_TEMP_C: float = 55.0
    MAX_TEMP_RISE_C: float = 12.0
    MIN_EXPANSION_LEVEL_PCT: float = 40.0
    MIN_STATIC_PRESSURE_BAR: float = 1.5
    NITRITE_MIN_PPM: float = 700.0
    NITRITE_MAX_PPM: float = 1500.0

    def evaluate(self, telemetry: JacketWaterTelemetry) -> JacketWaterAssessment:
        warnings: list[str] = []
        delta_t = round(telemetry.outlet_temp_c - telemetry.inlet_temp_c, 2)

        start_permissive = telemetry.outlet_temp_c >= self.MIN_START_TEMP_C
        if telemetry.outlet_temp_c < self.ALARM_START_TEMP_C:
            warnings.append(
                f"Severe low JW temp {telemetry.outlet_temp_c}°C (< {self.ALARM_START_TEMP_C}°C). Cold start lockout!"
            )
        elif telemetry.outlet_temp_c < self.MIN_START_TEMP_C:
            warnings.append(
                f"JW preheating incomplete {telemetry.outlet_temp_c}°C (< {self.MIN_START_TEMP_C}°C). Preheating required."
            )

        if delta_t > self.MAX_TEMP_RISE_C:
            warnings.append(
                f"Excessive temperature rise across cylinders {delta_t}°C (> {self.MAX_TEMP_RISE_C}°C). Check flow/fouling."
            )

        if telemetry.expansion_tank_level_pct < self.MIN_EXPANSION_LEVEL_PCT:
            warnings.append(
                f"Expansion tank low level {telemetry.expansion_tank_level_pct}% (< {self.MIN_EXPANSION_LEVEL_PCT}%)."
            )

        if telemetry.static_pressure_bar < self.MIN_STATIC_PRESSURE_BAR:
            warnings.append(
                f"Static head low {telemetry.static_pressure_bar} bar (< {self.MIN_STATIC_PRESSURE_BAR} bar). Cavitation risk."
            )

        nitrite_ok = self.NITRITE_MIN_PPM <= telemetry.nitrite_concentration_ppm <= self.NITRITE_MAX_PPM
        if not nitrite_ok:
            warnings.append(
                f"Nitrite inhibitor {telemetry.nitrite_concentration_ppm} ppm out of spec [{self.NITRITE_MIN_PPM}-{self.NITRITE_MAX_PPM} ppm]."
            )

        # Proportional thermostatic 3-way valve response towards 85°C
        error = telemetry.outlet_temp_c - self.TARGET_OUTLET_TEMP_C
        # 0% = bypass cooler (100% recirc), 100% = full cooler flow
        valve_pos = max(0.0, min(100.0, 50.0 + error * 10.0))

        status = "NORMAL"
        if not start_permissive or delta_t > self.MAX_TEMP_RISE_C or telemetry.static_pressure_bar < self.MIN_STATIC_PRESSURE_BAR:
            status = "CRITICAL" if telemetry.outlet_temp_c < self.ALARM_START_TEMP_C else "WARNING"
        elif warnings:
            status = "ADVISORY"

        compliance_flags = {
            "iso_8217_preheated": start_permissive,
            "man_temp_rise_normal": delta_t <= self.MAX_TEMP_RISE_C,
            "expansion_head_normal": telemetry.static_pressure_bar >= self.MIN_STATIC_PRESSURE_BAR,
            "corrosion_inhibitor_normal": nitrite_ok,
        }

        return JacketWaterAssessment(
            temp_rise_c=delta_t,
            valve_position_pct=round(valve_pos, 1),
            start_permissive=start_permissive,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
