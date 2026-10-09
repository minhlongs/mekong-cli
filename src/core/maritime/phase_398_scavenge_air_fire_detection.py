"""Maritime Phase 398: Main Engine Scavenge Air Fire Detection & Temperature Interlock.

Complies with IACS UR M44, SOLAS II-2 Reg 4.2.5.2, and CIMAC Recommendation 28.
Zero mock dependencies, strict thermodynamic temperature profiling & fire trips.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ScavengeFireInput:
    max_under_piston_temp_c: float = 85.0
    scavenge_manifold_pressure_bar: float = 2.4
    exhaust_gas_diff_temp_c: float = 25.0
    cylinder_oil_drain_rate_l_h: float = 1.2
    soot_density_mg_m3: float = 15.0
    slowdown_interlock_active: bool = False
    co2_smothering_valve_armed: bool = True


@dataclass
class ScavengeFireResult:
    fire_hazard_status: str
    under_piston_temp_ok: bool
    temperature_margin_c: float
    scavenge_pressure_normal: bool
    unburnt_oil_fouling_level: str
    engine_slowdown_demanded: bool
    smothering_medium_ready: bool
    warnings: List[str] = field(default_factory=list)


class ScavengeFireEngine:
    """Monitors 2-stroke engine scavenge trunking, under-piston temps, and fire trips."""

    TEMP_WARNING_THRESHOLD_C = 120.0
    TEMP_FIRE_TRIP_THRESHOLD_C = 180.0
    MAX_EXHAUST_DIFF_C = 50.0
    HIGH_FOULING_OIL_RATE_L_H = 3.0
    HIGH_SOOT_DENSITY_MG_M3 = 50.0

    def evaluate(self, inp: ScavengeFireInput) -> ScavengeFireResult:
        warnings = []
        t_piston = round(inp.max_under_piston_temp_c, 1)
        p_scav = round(inp.scavenge_manifold_pressure_bar, 2)
        diff_exh = round(inp.exhaust_gas_diff_temp_c, 1)
        oil_drain = round(inp.cylinder_oil_drain_rate_l_h, 2)
        soot = round(inp.soot_density_mg_m3, 1)

        # Under-piston thermal condition
        temp_margin = round(self.TEMP_FIRE_TRIP_THRESHOLD_C - t_piston, 1)
        if t_piston >= self.TEMP_FIRE_TRIP_THRESHOLD_C:
            fire_hazard = "SCAVENGE_FIRE_ACTIVE"
            temp_ok = False
            slowdown_needed = True
            warnings.append(
                f"CRITICAL SCAVENGE FIRE DETECTED: {t_piston}°C >= 180°C. Immediate slow-down & smothering!"
            )
        elif t_piston >= self.TEMP_WARNING_THRESHOLD_C:
            fire_hazard = "ELEVATED_PRE_FIRE_ALARM"
            temp_ok = False
            slowdown_needed = True
            warnings.append(
                f"SCAVENGE HIGH TEMP PRE-ALARM: {t_piston}°C >= 120°C. Reduce engine load!"
            )
        else:
            fire_hazard = "NORMAL_CLEAR"
            temp_ok = True
            slowdown_needed = False

        # Scavenge air manifold pressure (typically 1.5 to 3.5 bar at load)
        pressure_ok = 1.2 <= p_scav <= 4.0
        if not pressure_ok:
            warnings.append(f"SCAVENGE PRESSURE ABNORMAL: {p_scav} bar outside [1.2-4.0 bar]")

        # Exhaust gas temperature balance
        if diff_exh > self.MAX_EXHAUST_DIFF_C:
            warnings.append(
                f"EXHAUST GAS DEVIATION: {diff_exh}°C spread indicates faulty injection or blow-by"
            )

        # Fouling assessment from unburnt cylinder lube oil and soot
        if oil_drain > self.HIGH_FOULING_OIL_RATE_L_H or soot > self.HIGH_SOOT_DENSITY_MG_M3:
            fouling = "HIGH_COMBUSTIBLE_RESIDUE"
            warnings.append("EXCESSIVE UNBURNT OIL & SOOT: Severe fuel load in scavenge air trunk")
        elif oil_drain > 1.8 or soot > 25.0:
            fouling = "MODERATE_ACCUMULATION"
        else:
            fouling = "CLEAN_OPTIMAL"

        # Smothering system readiness
        armed = inp.co2_smothering_valve_armed
        if not armed:
            warnings.append("SMOTHERING VALVE DISARMED: Extinguishing medium unavailable")

        return ScavengeFireResult(
            fire_hazard_status=fire_hazard,
            under_piston_temp_ok=temp_ok,
            temperature_margin_c=temp_margin,
            scavenge_pressure_normal=pressure_ok,
            unburnt_oil_fouling_level=fouling,
            engine_slowdown_demanded=slowdown_needed,
            smothering_medium_ready=armed,
            warnings=warnings,
        )
