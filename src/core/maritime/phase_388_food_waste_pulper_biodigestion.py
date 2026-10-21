"""Maritime Phase 388: Food Waste Pulper & Bio-Digestion Automation.

Implements MARPOL Annex V Reg 4 & 5, IMO Resolution MEPC.295(71),
and MEPC Guidelines for the Implementation of Annex V.
Evaluates food waste comminution mesh size (<= 25 mm), geographic discharge criteria,
en-route vessel navigation status, bio-digester VFA/TIC stability, and grease trap oil content.
Strictly < 200 LOC, zero mocks, deterministic physical formulation.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class FoodWastePulperInput:
    """Input telemetry for shipboard food waste pulper, digester and discharge."""
    particle_size_mm: float = 18.0         # Screened particle size (comminuted <= 25mm)
    distance_to_nearest_land_nm: float = 14.0 # Distance to land / baseline
    in_special_area: bool = False          # E.g. Baltic, Mediterranean, Red Sea
    ship_speed_knots: float = 12.0         # Must be en route (> 0 knots)
    vfa_to_tic_ratio: float = 0.22         # Volatile Fatty Acid to Total Inorganic Carbon (<= 0.30)
    grease_trap_oil_ppm: float = 8.5       # Effluent oil content from galley grease separator
    daily_waste_mass_kg: float = 120.0     # Daily organic food waste treated


@dataclass
class FoodWastePulperResult:
    """Operational evaluation for MARPOL Annex V food waste processing."""
    comminution_compliant: bool
    discharge_permitted: bool
    digester_status: str                   # STABLE, SOURING_ALERT, UPSET
    grease_trap_compliant: bool
    biogas_yield_estimate_m3: float
    regulatory_classification: str         # DISCHARGE_PERMITTED, RETENTION_MANDATORY, PROHIBITED
    warnings: List[str] = field(default_factory=list)


class FoodWastePulperEngine:
    """Evaluates shipboard food waste comminution, bio-digester and overboard discharge."""

    MAX_COMMINUTED_SIZE_MM = 25.0
    MIN_DISTANCE_COMMINUTED_SPECIAL_AREA_NM = 12.0
    MIN_DISTANCE_COMMINUTED_GENERAL_NM = 3.0
    MIN_DISTANCE_UNCOMMINUTED_GENERAL_NM = 12.0
    MIN_EN_ROUTE_SPEED_KNOTS = 0.5
    MAX_VFA_TIC_STABLE = 0.30
    MAX_GREASE_OIL_PPM = 15.0
    BIOGAS_FACTOR_M3_PER_KG = 0.45          # Typical cubic meters biogas per kg wet organic waste digested

    def evaluate(self, telemetry: FoodWastePulperInput) -> FoodWastePulperResult:
        warnings: List[str] = []

        # 1. Comminution screen check (<= 25mm per MARPOL Annex V Reg 4.1.1)
        comminution_compliant = telemetry.particle_size_mm <= self.MAX_COMMINUTED_SIZE_MM
        if not comminution_compliant:
            warnings.append(
                f"COMMINUTION NON-COMPLIANT: Particle size {telemetry.particle_size_mm:.1f} mm exceeds 25.0 mm screen limit"
            )

        # 2. Grease trap separator compliance (<= 15 ppm)
        grease_trap_compliant = telemetry.grease_trap_oil_ppm <= self.MAX_GREASE_OIL_PPM
        if not grease_trap_compliant:
            warnings.append(
                f"GALLEY GREASE TRAP EXCEEDANCE: {telemetry.grease_trap_oil_ppm:.1f} ppm > {self.MAX_GREASE_OIL_PPM} ppm limit"
            )

        # 3. Anaerobic Bio-Digester Stability (VFA/TIC <= 0.30)
        if telemetry.vfa_to_tic_ratio <= self.MAX_VFA_TIC_STABLE:
            digester_status = "STABLE"
        elif telemetry.vfa_to_tic_ratio <= 0.40:
            digester_status = "SOURING_ALERT"
            warnings.append(
                f"DIGESTER SOURING WARNING: VFA/TIC ratio {telemetry.vfa_to_tic_ratio:.2f} > {self.MAX_VFA_TIC_STABLE:.2f}"
            )
        else:
            digester_status = "UPSET"
            warnings.append(
                f"CRITICAL DIGESTER UPSET: VFA/TIC ratio {telemetry.vfa_to_tic_ratio:.2f} (acidification risk)"
            )

        # Estimated biogas yield
        biogas_yield = round(telemetry.daily_waste_mass_kg * self.BIOGAS_FACTOR_M3_PER_KG, 2)

        # 4. MARPOL Annex V Overboard Discharge Legality Evaluation
        # Preconditions: Ship must be en route (speed > 0.5 knots)
        is_en_route = telemetry.ship_speed_knots >= self.MIN_EN_ROUTE_SPEED_KNOTS
        discharge_permitted = False

        if not is_en_route:
            warnings.append(
                f"VESSEL NOT EN ROUTE: Speed {telemetry.ship_speed_knots:.1f} kts < {self.MIN_EN_ROUTE_SPEED_KNOTS} kts. Overboard discharge prohibited in port or anchor."
            )

        if telemetry.in_special_area:
            # Special Area: Only comminuted (<= 25mm), as far as practicable, >= 12 NM from nearest land
            if comminution_compliant and telemetry.distance_to_nearest_land_nm >= self.MIN_DISTANCE_COMMINUTED_SPECIAL_AREA_NM and is_en_route:
                discharge_permitted = True
            else:
                if not comminution_compliant:
                    warnings.append("SPECIAL AREA PROHIBITION: Food waste must be comminuted <= 25 mm.")
                if telemetry.distance_to_nearest_land_nm < self.MIN_DISTANCE_COMMINUTED_SPECIAL_AREA_NM:
                    warnings.append(
                        f"SPECIAL AREA DISTANCE VIOLATION: {telemetry.distance_to_nearest_land_nm:.1f} NM < {self.MIN_DISTANCE_COMMINUTED_SPECIAL_AREA_NM} NM"
                    )
        else:
            # Outside Special Area:
            if comminution_compliant:
                # Comminuted >= 3 NM
                if telemetry.distance_to_nearest_land_nm >= self.MIN_DISTANCE_COMMINUTED_GENERAL_NM and is_en_route:
                    discharge_permitted = True
                else:
                    warnings.append(
                        f"OUTSIDE SPECIAL AREA: Comminuted distance {telemetry.distance_to_nearest_land_nm:.1f} NM < {self.MIN_DISTANCE_COMMINUTED_GENERAL_NM} NM"
                    )
            else:
                # Uncomminuted >= 12 NM
                if telemetry.distance_to_nearest_land_nm >= self.MIN_DISTANCE_UNCOMMINUTED_GENERAL_NM and is_en_route:
                    discharge_permitted = True
                else:
                    warnings.append(
                        f"OUTSIDE SPECIAL AREA: Uncomminuted distance {telemetry.distance_to_nearest_land_nm:.1f} NM < {self.MIN_DISTANCE_UNCOMMINUTED_GENERAL_NM} NM"
                    )

        if discharge_permitted:
            classification = "DISCHARGE_PERMITTED"
        else:
            classification = "RETENTION_MANDATORY"

        return FoodWastePulperResult(
            comminution_compliant=comminution_compliant,
            discharge_permitted=discharge_permitted,
            digester_status=digester_status,
            grease_trap_compliant=grease_trap_compliant,
            biogas_yield_estimate_m3=biogas_yield,
            regulatory_classification=classification,
            warnings=warnings,
        )
