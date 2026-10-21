"""Maritime Phase 392: Impressed Current Cathodic Protection (ICCP) & Shaft Grounding.

Complies with DNV-RP-B401, NACE SP0169, and ISO 12473.
Zero mock dependencies, strict electrochemical calculations.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class IccpCathodicProtectionInput:
    hull_potential_mv: float = -880.0  # vs Ag/AgCl reference electrode
    target_potential_mv: float = -850.0
    shaft_to_hull_voltage_mv: float = 25.0
    anode_output_current_amps: float = 35.0
    max_anode_capacity_amps: float = 100.0


@dataclass
class IccpCathodicProtectionResult:
    hull_potential_mv: float
    protection_status: str
    shaft_grounding_status: str
    recommended_anode_current_a: float
    hydrogen_embrittlement_risk: bool
    corrosion_activity_risk: bool
    warnings: List[str] = field(default_factory=list)


class IccpCathodicProtectionEngine:
    """Evaluates hull ICCP and propeller shaft grounding under DNV-RP-B401."""

    OPTIMAL_MIN_MV = -1050.0  # More negative than -1050 mV causes overprotection
    OPTIMAL_MAX_MV = -800.0   # Less negative than -800 mV (e.g. -750 mV) causes corrosion
    SHAFT_BEARING_SPARK_LIMIT_MV = 50.0

    def evaluate(self, inp: IccpCathodicProtectionInput) -> IccpCathodicProtectionResult:
        warnings = []
        pot = round(inp.hull_potential_mv, 1)
        shaft_v = round(inp.shaft_to_hull_voltage_mv, 1)

        # Hull polarization status
        if pot < self.OPTIMAL_MIN_MV:
            protection_status = "OVER_PROTECTED"
            hydrogen_risk = True
            corrosion_risk = False
            warnings.append(
                f"OVER-PROTECTION HAZARD ({pot} mV): Risk of cathodic hydrogen embrittlement and coating disbondment"
            )
            # Reduce anode current
            recommended_a = max(0.0, round(inp.anode_output_current_amps * 0.7, 1))
        elif pot > self.OPTIMAL_MAX_MV:
            protection_status = "UNDER_PROTECTED"
            hydrogen_risk = False
            corrosion_risk = True
            warnings.append(
                f"UNDER-PROTECTION ALERT ({pot} mV): Active galvanic hull corrosion underway"
            )
            # Increase anode current up to max capacity
            recommended_a = min(
                inp.max_anode_capacity_amps,
                round(inp.anode_output_current_amps * 1.35, 1),
            )
        else:
            protection_status = "OPTIMAL_PROTECTION"
            hydrogen_risk = False
            corrosion_risk = False
            recommended_a = inp.anode_output_current_amps

        # Propeller shaft slip-ring grounding status
        if shaft_v > self.SHAFT_BEARING_SPARK_LIMIT_MV:
            shaft_status = "SPARK_EROSION_RISK"
            warnings.append(
                f"SHAFT GROUNDING DEFECT ({shaft_v} mV > 50 mV): Stern tube bearing spark erosion risk"
            )
        else:
            shaft_status = "NORMAL_GROUNDED"

        return IccpCathodicProtectionResult(
            hull_potential_mv=pot,
            protection_status=protection_status,
            shaft_grounding_status=shaft_status,
            recommended_anode_current_a=recommended_a,
            hydrogen_embrittlement_risk=hydrogen_risk,
            corrosion_activity_risk=corrosion_risk,
            warnings=warnings,
        )
