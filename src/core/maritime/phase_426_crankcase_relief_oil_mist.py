"""Phase 426: Crankcase Explosion Relief Valve & Gravimetric Oil Mist Detector.

Implements IACS UR M9/M10, SOLAS II-1 Reg 27.5, and ISO 10816-6 rules:
crankcase relief valve vent area sizing (A_relief >= V_crankcase / 0.02 cm2),
spring setpoint (0.20 +- 0.05 bar), Beer-Lambert optical extinction gravimetric
oil mist concentration (alarm >= 1.0 mg/L, shutdown trip >= 2.0 mg/L),
and bearing temperature differential hot-spot corroboration (dT >= 15.0°C).
Strictly < 180 LOC, zero mocks.
"""

import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CrankcaseReliefMistTelemetry:
    """Telemetry readings for Crankcase Relief Valve and Gravimetric Oil Mist Detector."""
    crankcase_volume_m3: float = 48.0
    installed_relief_valve_area_cm2: float = 2500.0
    crankcase_pressure_bar_gauge: float = 0.05
    relief_valve_lifted: bool = False
    flame_arrester_intact: bool = True
    optical_intensity_i0: float = 100.0
    optical_intensity_i: float = 98.0
    optical_path_length_m: float = 0.5
    extinction_coefficient_m2_mg: float = 0.15
    bearing_temperatures_c: tuple = (72.0, 74.0, 73.0, 75.0, 73.5, 74.5)
    engine_rpm: float = 95.0
    slowdown_active: bool = False


@dataclass(frozen=True)
class CrankcaseReliefMistAssessment:
    """Crankcase explosion risk, relief sizing, and oil mist concentration evaluation."""
    oil_mist_concentration_mg_l: float
    required_relief_area_cm2: float
    relief_area_compliant: bool
    oil_mist_alarm: bool
    emergency_slowdown_trip: bool
    max_bearing_delta_c: float
    hot_spot_bearing_detected: bool
    relief_valve_operating_safe: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CrankcaseReliefMistEngine:
    """Evaluates crankcase explosion relief valves, gravimetric mist, and bearing thermal runaway."""

    # IACS M9 minimum relief valve discharge area factor: A >= V / 0.02 cm2
    M9_AREA_DIVISOR: float = 0.02
    RELIEF_CRITICAL_PRESSURE_BAR: float = 0.20
    MIST_PRE_ALARM_MG_L: float = 1.0
    MIST_EMERGENCY_TRIP_MG_L: float = 2.0
    BEARING_DELTA_HOTSPOT_C: float = 15.0

    def evaluate(self, telem: CrankcaseReliefMistTelemetry) -> CrankcaseReliefMistAssessment:
        warnings: List[str] = []

        # 1. Relief Valve Sizing Compliance (IACS M9)
        required_area = telem.crankcase_volume_m3 / self.M9_AREA_DIVISOR
        area_ok = telem.installed_relief_valve_area_cm2 >= required_area
        if not area_ok:
            warnings.append(
                f"Installed relief area {telem.installed_relief_valve_area_cm2:.1f} cm² below "
                f"IACS M9 requirement ({required_area:.1f} cm²)."
            )

        # Relief valve lifting / overpressure check
        relief_safe = (
            telem.flame_arrester_intact
            and telem.crankcase_pressure_bar_gauge <= self.RELIEF_CRITICAL_PRESSURE_BAR
        )
        if not telem.flame_arrester_intact:
            warnings.append("CRITICAL: Crankcase flame arrester mesh compromised or fouled!")
        if telem.relief_valve_lifted:
            warnings.append("ALERT: Crankcase relief valve has lifted due to internal overpressure.")

        # 2. Gravimetric Oil Mist Extinction via Beer-Lambert Law: I = I0 * exp(-kappa * C * L)
        # C_mist = -ln(I / I0) / (kappa * L)
        ratio = max(0.001, min(1.0, telem.optical_intensity_i / max(1.0, telem.optical_intensity_i0)))
        denom = max(1e-4, telem.extinction_coefficient_m2_mg * telem.optical_path_length_m)
        mist_mg_l = -math.log(ratio) / denom

        mist_alarm = mist_mg_l >= self.MIST_PRE_ALARM_MG_L
        mist_trip = mist_mg_l >= self.MIST_EMERGENCY_TRIP_MG_L

        if mist_trip:
            warnings.append(
                f"EMERGENCY: Crankcase oil mist concentration {mist_mg_l:.2f} mg/L exceeds "
                f"trip threshold ({self.MIST_EMERGENCY_TRIP_MG_L} mg/L). Immediate engine trip required!"
            )
        elif mist_alarm:
            warnings.append(
                f"Oil mist pre-alarm: Concentration {mist_mg_l:.2f} mg/L exceeds {self.MIST_PRE_ALARM_MG_L} mg/L."
            )

        # 3. Bearing Hot-Spot Temperature Corroboration
        bearing_temps = telem.bearing_temperatures_c or (0.0,)
        mean_temp = sum(bearing_temps) / len(bearing_temps)
        max_delta = max(0.0, max(bearing_temps) - mean_temp)
        hot_spot = max_delta >= self.BEARING_DELTA_HOTSPOT_C

        if hot_spot:
            warnings.append(
                f"Bearing hot spot detected: Max deviation +{max_delta:.1f}°C from mean ({mean_temp:.1f}°C)."
            )

        # Combined Trip Condition (SOLAS II-1 Reg 27.5 & IACS M10)
        trip_demanded = mist_trip or (mist_alarm and hot_spot)

        # Status determination
        if trip_demanded:
            status = "EMERGENCY_SHUTDOWN_TRIP"
        elif mist_alarm:
            status = "OIL_MIST_PRE_ALARM"
        elif hot_spot:
            status = "BEARING_HOTSPOT_WARNING"
        elif not area_ok:
            status = "RELIEF_AREA_NON_COMPLIANT"
        elif not telem.flame_arrester_intact:
            status = "FLAME_ARRESTER_FAULT"
        else:
            status = "NORMAL_OPTIMAL"

        compliance_flags = {
            "relief_area_compliant": area_ok,
            "flame_arrester_healthy": telem.flame_arrester_intact,
            "mist_below_alarm": not mist_alarm,
            "mist_below_trip": not mist_trip,
            "bearing_temperatures_normal": not hot_spot,
            "relief_valve_closed_ready": not telem.relief_valve_lifted,
        }

        return CrankcaseReliefMistAssessment(
            oil_mist_concentration_mg_l=round(mist_mg_l, 3),
            required_relief_area_cm2=round(required_area, 1),
            relief_area_compliant=area_ok,
            oil_mist_alarm=mist_alarm,
            emergency_slowdown_trip=trip_demanded,
            max_bearing_delta_c=round(max_delta, 1),
            hot_spot_bearing_detected=hot_spot,
            relief_valve_operating_safe=relief_safe,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
