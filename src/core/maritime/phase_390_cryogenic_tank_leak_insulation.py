"""Maritime Phase 390: Cryogenic Cargo Tank Leak Sniffing & Insulation Pressure Relief.

Implements IMO IGC Code Ch. 8, Ch. 13, and SIGTTO Liquefied Gas Carrier Safety Standards.
Monitors LNG/LPG cargo tank primary barrier integrity, interbarrier space methane/helium sniffing,
insulation space differential pressure venting, and hull inner plating temperature limits.
Strictly < 200 LOC, zero mocks, deterministic physical formulation.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CryogenicTankLeakInput:
    """Input telemetry for cryogenic cargo tank barrier and insulation space."""
    methane_concentration_vol_pct: float = 0.05 # CH4 in N2 inerted interbarrier space
    dew_point_c: float = -45.0                  # Dew point in insulation space (<= -40C required)
    oxygen_concentration_pct: float = 0.5       # O2 in N2 buffer (<= 1.0% vol max)
    insulation_diff_pressure_kpa: float = 0.8   # Delta P: P_insulation - P_cargo (normal -5 to +2 kPa)
    inner_hull_steel_temp_c: float = 12.0       # Inner bottom / hull temperature (>= 0.0C limit)
    glycol_heating_active: bool = True          # Glycol thermal barrier heating loop


@dataclass
class CryogenicTankLeakResult:
    """Operational evaluation for cryogenic gas carrier insulation and leak barriers."""
    barrier_integrity: str                 # INTACT, MINOR_SEEPAGE, PRIMARY_BARRIER_BREACH
    atmosphere_inert_compliant: bool
    pressure_relief_required: bool
    hull_cold_spot_detected: bool
    cargo_tank_safety_status: str          # SAFE, WARNING, CRITICAL_EMERGENCY
    vent_mast_exhaust_active: bool
    warnings: List[str] = field(default_factory=list)


class CryogenicTankLeakEngine:
    """Evaluates cryogenic LNG/LPG barrier leaks, inerting and insulation space pressure."""

    CH4_LEAK_WARNING_VOL_PCT = 0.50        # Warning threshold in interbarrier space
    CH4_LEAK_CRITICAL_VOL_PCT = 1.50       # Critical breach (~30% LEL in air eq)
    MAX_DEW_POINT_C = -40.0                # Frost / hydrate formation limit
    MAX_INERT_O2_PCT = 1.0                 # Max oxygen content in N2 blanket
    MIN_INNER_HULL_TEMP_C = 0.0            # Hull steel brittle fracture prevention threshold
    MAX_INSULATION_PRESSURE_KPA = 2.5      # Pressure relief venting trigger to atmosphere

    def evaluate(self, telemetry: CryogenicTankLeakInput) -> CryogenicTankLeakResult:
        warnings: List[str] = []

        # 1. Interbarrier Atmosphere Quality (Dew point <= -40C and O2 <= 1.0%)
        atmosphere_inert_compliant = (
            telemetry.dew_point_c <= self.MAX_DEW_POINT_C
            and telemetry.oxygen_concentration_pct <= self.MAX_INERT_O2_PCT
        )
        if telemetry.dew_point_c > self.MAX_DEW_POINT_C:
            warnings.append(
                f"INSULATION DEW POINT HIGH: {telemetry.dew_point_c:.1f} C > {self.MAX_DEW_POINT_C} C (frost hazard)"
            )
        if telemetry.oxygen_concentration_pct > self.MAX_INERT_O2_PCT:
            warnings.append(
                f"INERT OXYGEN HIGH: {telemetry.oxygen_concentration_pct:.2f}% > {self.MAX_INERT_O2_PCT}% vol limit"
            )

        # 2. Hydrocarbon (Methane) Gas Leak Sniffing
        if telemetry.methane_concentration_vol_pct >= self.CH4_LEAK_CRITICAL_VOL_PCT:
            barrier_integrity = "PRIMARY_BARRIER_BREACH"
            warnings.append(
                f"PRIMARY BARRIER BREACH: CH4 {telemetry.methane_concentration_vol_pct:.2f}% >= {self.CH4_LEAK_CRITICAL_VOL_PCT}% vol"
            )
        elif telemetry.methane_concentration_vol_pct >= self.CH4_LEAK_WARNING_VOL_PCT:
            barrier_integrity = "MINOR_SEEPAGE"
            warnings.append(
                f"INTERBARRIER CH4 SEEPAGE WARNING: {telemetry.methane_concentration_vol_pct:.2f}% vol"
            )
        else:
            barrier_integrity = "INTACT"

        # 3. Inner Hull Steel Cold Spot & Thermal Protection
        hull_cold_spot = telemetry.inner_hull_steel_temp_c < self.MIN_INNER_HULL_TEMP_C
        if hull_cold_spot:
            warnings.append(
                f"CRITICAL COLD SPOT DETECTED: Inner hull temp {telemetry.inner_hull_steel_temp_c:.1f} C < {self.MIN_INNER_HULL_TEMP_C} C"
            )

        # 4. Insulation Space Pressure Relief
        pressure_relief_required = telemetry.insulation_diff_pressure_kpa >= self.MAX_INSULATION_PRESSURE_KPA
        vent_mast_exhaust = pressure_relief_required
        if pressure_relief_required:
            warnings.append(
                f"INSULATION OVERPRESSURE: Diff pressure {telemetry.insulation_diff_pressure_kpa:.2f} kPa >= {self.MAX_INSULATION_PRESSURE_KPA} kPa (venting active)"
            )

        # 5. Composite Cargo Tank Safety Status
        if barrier_integrity == "PRIMARY_BARRIER_BREACH" or hull_cold_spot:
            status = "CRITICAL_EMERGENCY"
        elif barrier_integrity == "MINOR_SEEPAGE" or not atmosphere_inert_compliant or pressure_relief_required:
            status = "WARNING"
        else:
            status = "SAFE"

        return CryogenicTankLeakResult(
            barrier_integrity=barrier_integrity,
            atmosphere_inert_compliant=atmosphere_inert_compliant,
            pressure_relief_required=pressure_relief_required,
            hull_cold_spot_detected=hull_cold_spot,
            cargo_tank_safety_status=status,
            vent_mast_exhaust_active=vent_mast_exhaust,
            warnings=warnings,
        )
