"""Phase 347: Impressed Current Cathodic Protection (ICCP) & Sacrificial Anode Engine.

Implements NACE SP0176 and DNV-RP-B401 standards for marine hull corrosion mitigation:
- Ag/AgCl reference electrode potential monitoring (-800 mV to -1050 mV safe window).
- Under-protection and over-protection (cathodic disbondment) detection.
- Wetted hull area calculation and required protective current demand.
- Sacrificial anode backup sizing.
Strictly under 200 LOC.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class IccpCathodicInput:
    vessel_id: str
    length_bp_m: float
    breadth_m: float
    draft_m: float
    block_coefficient_cb: float = 0.80
    reference_potential_mv: float = -850.0  # mV vs Ag/AgCl
    design_current_density_ma_m2: float = 30.0  # mA/m^2
    coating_breakdown_factor: float = 0.10  # 10% bare steel exposure
    anode_material: str = "ZINC"  # ZINC (780 Ah/kg) or ALUMINUM (2000 Ah/kg)
    service_years: float = 2.5


@dataclass
class IccpCathodicResult:
    vessel_id: str
    wetted_surface_area_m2: float
    required_current_amps: float
    reference_potential_mv: float
    protection_status: str  # OPTIMAL, UNDER_PROTECTED, OVER_PROTECTED
    corrosion_risk: str  # NEGLIGIBLE, ELEVATED, CRITICAL
    cathodic_disbondment_risk: bool
    recommended_anode_mass_kg: float
    advisories: List[str] = field(default_factory=list)


class IccpCathodicEngine:
    """Evaluates hull cathodic protection status per NACE SP0176 & DNV-RP-B401."""

    MIN_PROTECTION_POTENTIAL_MV = -800.0  # More positive than -800 mV is under-protected
    MAX_OVERPROTECTION_POTENTIAL_MV = -1050.0  # More negative than -1050 mV causes paint peeling
    ZINC_CAPACITY_AH_KG = 780.0
    ALUMINUM_CAPACITY_AH_KG = 2000.0
    UTILIZATION_FACTOR = 0.85

    @classmethod
    def evaluate(cls, inp: IccpCathodicInput) -> IccpCathodicResult:
        advisories: List[str] = []

        # 1. Wetted surface area (Mumford formula variant)
        wetted_area = round(
            1.025 * inp.length_bp_m * (inp.block_coefficient_cb * inp.breadth_m + 1.7 * inp.draft_m),
            2,
        )

        # 2. Required ICCP current demand (Amperes)
        # I = Area * (j in mA/m2) * fc / 1000
        req_current = round(
            wetted_area * inp.design_current_density_ma_m2 * inp.coating_breakdown_factor / 1000.0,
            2,
        )

        # 3. Assess reference potential window vs Ag/AgCl
        pot = inp.reference_potential_mv
        disbondment_risk = False

        if pot > cls.MIN_PROTECTION_POTENTIAL_MV:
            prot_status = "UNDER_PROTECTED"
            corrosion_risk = "CRITICAL"
            advisories.append(
                f"CORROSION ALERT: Potential {pot} mV > {cls.MIN_PROTECTION_POTENTIAL_MV} mV. "
                "Insufficient cathodic polarization. Increase ICCP rectifier output."
            )
        elif pot < cls.MAX_OVERPROTECTION_POTENTIAL_MV:
            prot_status = "OVER_PROTECTED"
            corrosion_risk = "NEGLIGIBLE"
            disbondment_risk = True
            advisories.append(
                f"OVER-PROTECTION WARNING: Potential {pot} mV < {cls.MAX_OVERPROTECTION_POTENTIAL_MV} mV. "
                "Risk of hydrogen evolution and cathodic paint disbondment. Decrease rectifier voltage."
            )
        else:
            prot_status = "OPTIMAL"
            corrosion_risk = "NEGLIGIBLE"
            advisories.append(
                f"OPTIMAL PROTECTION: Potential {pot} mV within safe window "
                f"[{cls.MAX_OVERPROTECTION_POTENTIAL_MV}, {cls.MIN_PROTECTION_POTENTIAL_MV}] mV."
            )

        # 4. Sacrificial Anode backup sizing
        cap = cls.ALUMINUM_CAPACITY_AH_KG if inp.anode_material.upper() == "ALUMINUM" else cls.ZINC_CAPACITY_AH_KG
        hours = inp.service_years * 8760.0
        anode_mass = round((req_current * hours) / (cap * cls.UTILIZATION_FACTOR), 2)

        return IccpCathodicResult(
            vessel_id=inp.vessel_id,
            wetted_surface_area_m2=wetted_area,
            required_current_amps=req_current,
            reference_potential_mv=pot,
            protection_status=prot_status,
            corrosion_risk=corrosion_risk,
            cathodic_disbondment_risk=disbondment_risk,
            recommended_anode_mass_kg=anode_mass,
            advisories=advisories,
        )
