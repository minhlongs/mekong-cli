"""Phase 421: Ballast Tank Cathodic Protection & Anode Depletion.

Implements DNV-RP-B401 and IMO MSC.215(82) (PSPC - Protective Coatings) standards:
Galvanic polarization potential maintenance (Ag/AgCl), current density demand,
sacrificial zinc mass loss calculation, and hydrogen embrittlement lockout.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BallastAnodicTelemetry:
    """Telemetry readings for ballast tank corrosion protection system."""
    tank_water_level_pct: float = 85.0       # Only active when ballasted (> 20%)
    ref_electrode_potential_mv: float = -920.0  # Ag/AgCl reference: target -850 to -1050 mV
    applied_current_amperes: float = 4.8
    anode_circuit_voltage_volts: float = 2.4
    steel_surface_area_m2: float = 1250.0
    initial_zinc_mass_kg: float = 450.0
    accumulated_operating_hours: float = 4800.0
    water_salinity_ppt: float = 34.0


@dataclass(frozen=True)
class BallastAnodicAssessment:
    """Evaluation of polarization state, anode depletion percentage, and safety margins."""
    protection_potential_mv: float
    current_density_ma_m2: float
    polarization_adequate: bool
    over_protection_embrittlement_risk: bool
    depleted_zinc_mass_kg: float
    remaining_anode_life_pct: float
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class BallastAnodicProtectionEngine:
    """Monitors cathodic protection potential and models electrochemical zinc dissolution."""

    MIN_PROTECTION_POTENTIAL_MV: float = -850.0   # Less negative = under-protected / corrosion active
    MAX_OVERPROTECTION_POTENTIAL_MV: float = -1150.0 # More negative = hydrogen evolution / coating blistering
    ZINC_ELECTROCHEMICAL_CONSUMPTION_KG_A_YEAR: float = 10.7  # Faraday's law standard for Zn anode (kg/A·year)
    DESIGN_LIFE_HOURS: float = 43800.0  # 5 years drydock interval

    def evaluate(self, telemetry: BallastAnodicTelemetry) -> BallastAnodicAssessment:
        warnings: List[str] = []

        # Current density: mA/m2
        current_density_ma_m2 = (telemetry.applied_current_amperes * 1000.0) / max(1.0, telemetry.steel_surface_area_m2)

        # Polarization checks
        pot = telemetry.ref_electrode_potential_mv
        polarization_adequate = pot <= self.MIN_PROTECTION_POTENTIAL_MV
        over_protection = pot < self.MAX_OVERPROTECTION_POTENTIAL_MV

        if telemetry.tank_water_level_pct < 20.0:
            warnings.append("Ballast tank de-ballasted (< 20%): cathodic circuit on standby")
        else:
            if not polarization_adequate:
                warnings.append(f"Under-protection warning: Potential {pot} mV is above -850 mV (active steel corrosion risk)")
            if over_protection:
                warnings.append(f"Over-protection risk: Potential {pot} mV below -1150 mV. Risk of hydrogen embrittlement & coating disbondment!")

        # Faraday mass loss: Mass (kg) = (Consumption rate * Current (A) * Hours) / 8760
        consumption_years = telemetry.accumulated_operating_hours / 8760.0
        depleted_zinc_kg = round(self.ZINC_ELECTROCHEMICAL_CONSUMPTION_KG_A_YEAR * telemetry.applied_current_amperes * consumption_years, 2)
        remaining_zinc_kg = max(0.0, telemetry.initial_zinc_mass_kg - depleted_zinc_kg)
        remaining_pct = round((remaining_zinc_kg / max(1.0, telemetry.initial_zinc_mass_kg)) * 100.0, 1)

        if remaining_pct < 25.0:
            warnings.append(f"Anode renewal required: Zinc depleted down to {remaining_pct}% (< 25% threshold)")

        status = "CRITICAL" if over_protection else ("WARNING" if warnings else "NORMAL")

        return BallastAnodicAssessment(
            protection_potential_mv=pot,
            current_density_ma_m2=round(current_density_ma_m2, 2),
            polarization_adequate=polarization_adequate,
            over_protection_embrittlement_risk=over_protection,
            depleted_zinc_mass_kg=depleted_zinc_kg,
            remaining_anode_life_pct=remaining_pct,
            status=status,
            warnings=warnings,
            compliance_flags={
                "dnv_rp_b401_polarization_adequate": polarization_adequate,
                "pspc_msc215_coating_safe_from_blistering": not over_protection,
                "zinc_anode_inventory_healthy": remaining_pct >= 25.0,
            },
        )
