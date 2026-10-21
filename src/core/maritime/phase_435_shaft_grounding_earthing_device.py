"""Phase 435: Marine Shaft Grounding Earthing Device (SEAD) & Slip Ring Potential Drop.

Implements IACS UR E22, DNV-RU-SHIP Pt.4 Ch.8:
- Propeller shaft slip ring potential drop (normal <= 50 mV, warning > 50 mV, critical > 80 mV).
- Galvanic spark erosion risk index across main engine journal and thrust bearings.
- Silver-graphite brush contact current density (<= 0.01 A/cm2) and brush wear monitoring.
Strictly < 150 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ShaftEarthingTelemetry:
    """Telemetry readings for propeller shaft earthing device and brush gear."""
    shaft_potential_mv: float = 35.0  # Measured between shaft slip ring and ship hull
    shaft_current_a: float = 1.2      # Measured discharge current to hull
    contact_area_cm2: float = 150.0   # Total active silver-graphite brush contact area
    shaft_rpm: float = 85.0
    brush_wear_pct: float = 30.0      # Brush physical wear percentage
    slip_ring_cleanliness_pct: float = 95.0  # Optical track cleanliness


@dataclass(frozen=True)
class ShaftEarthingAssessment:
    """Electrical potential drop, current density, and bearing erosion risk assessment."""
    shaft_potential_mv: float
    current_density_a_cm2: float
    spark_erosion_risk: str
    earthing_healthy: bool
    brush_replacement_needed: bool
    slip_ring_cleaning_needed: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class ShaftEarthingEngine:
    """Evaluates propeller shaft grounding performance against IACS UR E22."""

    MAX_NORMAL_POTENTIAL_MV: float = 50.0
    WARN_POTENTIAL_MV: float = 80.0
    CRITICAL_POTENTIAL_MV: float = 100.0
    MAX_CURRENT_DENSITY_A_CM2: float = 0.01
    MAX_BRUSH_WEAR_PCT: float = 80.0
    MIN_CLEANLINESS_PCT: float = 70.0

    def evaluate(self, telemetry: ShaftEarthingTelemetry) -> ShaftEarthingAssessment:
        warnings: List[str] = []
        area = max(1.0, telemetry.contact_area_cm2)
        current_density = round(telemetry.shaft_current_a / area, 6)

        v_shaft = telemetry.shaft_potential_mv
        brush_worn = telemetry.brush_wear_pct >= self.MAX_BRUSH_WEAR_PCT
        cleaning_needed = telemetry.slip_ring_cleanliness_pct < self.MIN_CLEANLINESS_PCT

        if brush_worn:
            warnings.append(f"Brush wear critical ({telemetry.brush_wear_pct:.1f}% >= {self.MAX_BRUSH_WEAR_PCT}%)")
        if cleaning_needed:
            warnings.append(f"Slip ring track contaminated ({telemetry.slip_ring_cleanliness_pct:.1f}%)")

        if v_shaft <= self.MAX_NORMAL_POTENTIAL_MV:
            erosion_risk = "NEGLIGIBLE"
            earthing_healthy = True
            status = "OPTIMAL_GROUNDING"
        elif v_shaft <= self.WARN_POTENTIAL_MV:
            erosion_risk = "MODERATE"
            earthing_healthy = False
            status = "GROUNDING_DEGRADED"
            warnings.append(f"Shaft potential elevated ({v_shaft:.1f} mV > {self.MAX_NORMAL_POTENTIAL_MV} mV)")
        elif v_shaft <= self.CRITICAL_POTENTIAL_MV:
            erosion_risk = "HIGH_SPARK_EROSION_DANGER"
            earthing_healthy = False
            status = "CRITICAL_SPARK_RISK"
            warnings.append(f"High risk of dielectric breakdown across oil films ({v_shaft:.1f} mV)")
        else:
            erosion_risk = "SEVERE_BEARING_PITTING"
            earthing_healthy = False
            status = "BEARING_DAMAGE_IMMINENT"
            warnings.append(f"Extreme shaft potential ({v_shaft:.1f} mV > {self.CRITICAL_POTENTIAL_MV} mV)")

        density_ok = current_density <= self.MAX_CURRENT_DENSITY_A_CM2
        if not density_ok:
            warnings.append(f"Current density exceeds limits ({current_density:.4f} A/cm2)")

        compliance_flags = {
            "IACS_UR_E22_COMPLIANT": earthing_healthy and density_ok,
            "POTENTIAL_UNDER_50MV": v_shaft <= self.MAX_NORMAL_POTENTIAL_MV,
            "BRUSH_CONDITION_ACCEPTABLE": not brush_worn,
            "DNV_PT4_CH8_SATISFIED": earthing_healthy and not brush_worn,
        }

        return ShaftEarthingAssessment(
            shaft_potential_mv=v_shaft,
            current_density_a_cm2=current_density,
            spark_erosion_risk=erosion_risk,
            earthing_healthy=earthing_healthy,
            brush_replacement_needed=brush_worn,
            slip_ring_cleaning_needed=cleaning_needed,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
