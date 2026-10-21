"""Phase 418: Crankcase Explosion Relief Valve & Oil Mist Detector (OMD).

Implements SOLAS II-1 Reg 47 and IACS M9 / M10 standards for 2-stroke/4-stroke
marine diesel engine crankcases: Beer-Lambert optical oil mist density detection,
multi-compartment hotspot triangulation, spring-loaded relief valve lift dynamics,
and flame arrester thermal dissipation.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass(frozen=True)
class CrankcaseOmdTelemetry:
    """Telemetry readings for Crankcase Oil Mist Detector and Relief Valves."""
    sample_cell_transmission_pct: float = 94.0
    reference_cell_transmission_pct: float = 99.0
    optical_path_length_m: float = 0.22
    optical_extinction_coeff_m2_mg: float = 0.85
    compartment_hotspot_temps_c: tuple[float, ...] = (72.0, 74.0, 71.0, 73.0, 75.0, 70.0)
    crankcase_internal_pressure_mbar: float = -2.5
    relief_valve_opening_setpoint_mbar: float = 200.0
    flame_arrester_mesh_temp_c: float = 65.0
    engine_load_pct: float = 85.0


@dataclass(frozen=True)
class CrankcaseOmdAssessment:
    """Optical mist obscuration, explosion risk, and relief valve actuation state."""
    oil_mist_concentration_mg_l: float
    lel_percentage: float
    max_bearing_hotspot_temp_c: float
    hotspot_bearing_index: int
    crankcase_pressure_status: str
    relief_valve_lifted: bool
    flame_arrester_intact: bool
    engine_slowdown_required: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CrankcaseReliefOmdEngine:
    """Evaluates Beer-Lambert optical extinction, explosive mist concentration, and relief valves."""

    # IACS M10: Oil mist alarm limit is 1.0 mg/L or ~5% LEL; Shutdown at 2.0 mg/L (~10% LEL)
    # 100% LEL for lubricating oil mist is approx 20.0 mg/L (or 50 g/m3)
    LEL_100_PCT_MG_L: float = 20.0
    PRE_ALARM_MIST_MG_L: float = 1.0
    SHUTDOWN_MIST_MG_L: float = 2.0
    HOTSPOT_WARNING_TEMP_C: float = 82.0
    HOTSPOT_CRITICAL_TEMP_C: float = 95.0
    MAX_MESH_TEMP_C: float = 180.0

    def evaluate(self, telemetry: CrankcaseOmdTelemetry) -> CrankcaseOmdAssessment:
        warnings: List[str] = []

        # Beer-Lambert: I / I_0 = exp(-ext * L * C)
        # C (mg/L) = -ln(T_sample / T_ref) / (ext * L * 1000)
        t_sample = max(0.001, telemetry.sample_cell_transmission_pct / 100.0)
        t_ref = max(0.001, telemetry.reference_cell_transmission_pct / 100.0)
        ratio = min(1.0, t_sample / t_ref)

        path_l = max(0.05, telemetry.optical_path_length_m)
        ext_coeff = max(0.1, telemetry.optical_extinction_coeff_m2_mg)
        # ext in m^2/mg, path in m -> C in mg/m^3. 1 mg/L = 1000 mg/m^3
        c_mist_mg_m3 = -math.log(ratio) / (ext_coeff * path_l)
        c_mist_mg_l = max(0.0, c_mist_mg_m3 / 1000.0)

        lel_pct = (c_mist_mg_l / self.LEL_100_PCT_MG_L) * 100.0

        # Bearing hotspot check
        temps = telemetry.compartment_hotspot_temps_c
        max_temp = max(temps) if temps else 0.0
        hotspot_idx = temps.index(max_temp) if temps else -1

        # Crankcase pressure & relief valve dynamics
        valve_lifted = telemetry.crankcase_internal_pressure_mbar >= telemetry.relief_valve_opening_setpoint_mbar
        arrester_intact = telemetry.flame_arrester_mesh_temp_c < self.MAX_MESH_TEMP_C

        if c_mist_mg_l >= self.SHUTDOWN_MIST_MG_L:
            warnings.append(
                f"EMERGENCY: Crankcase oil mist concentration {c_mist_mg_l:.2f} mg/L exceeds shutdown threshold "
                f"{self.SHUTDOWN_MIST_MG_L:.2f} mg/L ({lel_pct:.1f}% LEL). EXPLOSION IMMINENT!"
            )
        elif c_mist_mg_l >= self.PRE_ALARM_MIST_MG_L:
            warnings.append(
                f"HIGH OIL MIST WARNING: {c_mist_mg_l:.2f} mg/L exceeds pre-alarm threshold "
                f"{self.PRE_ALARM_MIST_MG_L:.2f} mg/L ({lel_pct:.1f}% LEL)."
            )

        if max_temp >= self.HOTSPOT_CRITICAL_TEMP_C:
            warnings.append(
                f"Critical bearing hotspot: Compartment #{hotspot_idx + 1} reaches {max_temp:.1f}°C (> {self.HOTSPOT_CRITICAL_TEMP_C}°C)."
            )
        elif max_temp >= self.HOTSPOT_WARNING_TEMP_C:
            warnings.append(
                f"Bearing friction warming: Compartment #{hotspot_idx + 1} at {max_temp:.1f}°C (> {self.HOTSPOT_WARNING_TEMP_C}°C)."
            )

        if valve_lifted:
            warnings.append(
                f"CRANKCASE RELIEF VALVE LIFTED: Internal pressure {telemetry.crankcase_internal_pressure_mbar:.1f} mbar "
                f"exceeded setpoint {telemetry.relief_valve_opening_setpoint_mbar:.1f} mbar. Deflagration venting!"
            )

        if not arrester_intact:
            warnings.append(
                f"Flame arrester mesh overheat: {telemetry.flame_arrester_mesh_temp_c:.1f}°C exceeds {self.MAX_MESH_TEMP_C}°C. "
                "Risk of external crankcase flash fire!"
            )

        slowdown = c_mist_mg_l >= self.PRE_ALARM_MIST_MG_L or max_temp >= self.HOTSPOT_WARNING_TEMP_C or valve_lifted

        if telemetry.crankcase_internal_pressure_mbar < -10.0:
            press_status = "EXCESSIVE_VACUUM"
        elif telemetry.crankcase_internal_pressure_mbar > 10.0:
            press_status = "OVERPRESSURE_WARNING"
        else:
            press_status = "NORMAL_SLIGHT_VACUUM"

        status = "OPTIMAL"
        if c_mist_mg_l >= self.SHUTDOWN_MIST_MG_L or valve_lifted or not arrester_intact:
            status = "CRITICAL"
        elif warnings:
            status = "WARNING"

        compliance_flags = {
            "iacs_m10_omd_below_trip_level": c_mist_mg_l < self.SHUTDOWN_MIST_MG_L,
            "iacs_m9_relief_valves_operational": not valve_lifted and arrester_intact,
            "bearing_temperatures_normal": max_temp < self.HOTSPOT_WARNING_TEMP_C,
            "crankcase_ventilation_vacuum_maintained": -8.0 <= telemetry.crankcase_internal_pressure_mbar <= 0.0,
        }

        return CrankcaseOmdAssessment(
            oil_mist_concentration_mg_l=round(c_mist_mg_l, 3),
            lel_percentage=round(lel_pct, 2),
            max_bearing_hotspot_temp_c=round(max_temp, 1),
            hotspot_bearing_index=hotspot_idx + 1 if hotspot_idx >= 0 else 0,
            crankcase_pressure_status=press_status,
            relief_valve_lifted=valve_lifted,
            flame_arrester_intact=arrester_intact,
            engine_slowdown_required=slowdown,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
