"""Phase 438: Marine Auxiliary Boiler Water Chemical Dosing & Phosphate/Hydrazine Matrix.

Implements BS 2486, JIS B8223 & IACS UR M53:
- Coordinated phosphate treatment for scale prevention (PO4 15-30 mg/L).
- Hydrazine oxygen scavenger & magnetite passivation (N2H4 0.05-0.10 mg/L, dissolved O2 <= 0.005 mg/L).
- Boiler water alkalinity (pH 9.5-10.5) and automatic surface/bottom blowdown (conductivity <= 700 uS/cm).
Strictly < 150 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BoilerWaterTelemetry:
    """Telemetry readings for auxiliary boiler feedwater and drum water chemistry."""
    phosphate_po4_mg_l: float = 22.0       # Target 15.0 - 30.0 mg/L
    hydrazine_n2h4_mg_l: float = 0.07      # Target 0.05 - 0.10 mg/L
    dissolved_oxygen_mg_l: float = 0.003   # Target <= 0.005 mg/L
    ph_value: float = 10.1                 # Target 9.5 - 10.5
    conductivity_us_cm: float = 480.0      # Blowdown trigger at > 700 uS/cm
    chloride_cl_mg_l: float = 18.0         # Benchmark <= 30.0 mg/L (seawater contamination index)
    steam_pressure_bar: float = 7.0


@dataclass(frozen=True)
class BoilerWaterAssessment:
    """Passivation state, scale risk, blowdown necessity, and chemical dosing advisory."""
    scale_prevention_ok: bool
    oxygen_passivated: bool
    alkalinity_ok: bool
    blowdown_required: bool
    seawater_contamination: bool
    status: str
    dosing_recommendations: List[str]
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class BoilerWaterEngine:
    """Evaluates boiler water chemistry and dosing commands per BS 2486."""

    MIN_PO4_MG_L: float = 15.0
    MAX_PO4_MG_L: float = 30.0
    MIN_N2H4_MG_L: float = 0.05
    MAX_N2H4_MG_L: float = 0.10
    MAX_O2_MG_L: float = 0.005
    MIN_PH: float = 9.5
    MAX_PH: float = 10.5
    MAX_CONDUCTIVITY_US_CM: float = 700.0
    MAX_CHLORIDE_MG_L: float = 30.0

    def evaluate(self, telemetry: BoilerWaterTelemetry) -> BoilerWaterAssessment:
        warnings: List[str] = []
        dosing: List[str] = []

        scale_ok = self.MIN_PO4_MG_L <= telemetry.phosphate_po4_mg_l <= self.MAX_PO4_MG_L
        passivated = (telemetry.hydrazine_n2h4_mg_l >= self.MIN_N2H4_MG_L) and (telemetry.dissolved_oxygen_mg_l <= self.MAX_O2_MG_L)
        alkaline_ok = self.MIN_PH <= telemetry.ph_value <= self.MAX_PH
        blowdown = telemetry.conductivity_us_cm > self.MAX_CONDUCTIVITY_US_CM
        seawater_ingress = telemetry.chloride_cl_mg_l > self.MAX_CHLORIDE_MG_L

        if telemetry.phosphate_po4_mg_l < self.MIN_PO4_MG_L:
            dosing.append(f"Increase sodium phosphate dosing (+{self.MIN_PO4_MG_L - telemetry.phosphate_po4_mg_l:.1f} mg/L)")
            warnings.append("Low phosphate — risk of calcium scale crystallization on boiler tubes")
        elif telemetry.phosphate_po4_mg_l > self.MAX_PO4_MG_L:
            warnings.append("High phosphate concentration — excess chemical consumption")

        if telemetry.hydrazine_n2h4_mg_l < self.MIN_N2H4_MG_L:
            dosing.append(f"Increase hydrazine/DEHA dosing (residual {telemetry.hydrazine_n2h4_mg_l:.3f} < {self.MIN_N2H4_MG_L} mg/L)")
            warnings.append("Low hydrazine reserve — oxygen pitting risk in economizer/boiler tubes")
        if telemetry.dissolved_oxygen_mg_l > self.MAX_O2_MG_L:
            warnings.append(f"High dissolved oxygen ({telemetry.dissolved_oxygen_mg_l:.4f} > {self.MAX_O2_MG_L} mg/L)")

        if telemetry.ph_value < self.MIN_PH:
            dosing.append("Inject caustic/neutralizing amine to increase alkalinity")
            warnings.append(f"Acidic boiler water (pH {telemetry.ph_value:.1f} < {self.MIN_PH})")
        elif telemetry.ph_value > self.MAX_PH:
            warnings.append(f"Excessive alkalinity (pH {telemetry.ph_value:.1f} > {self.MAX_PH}) — risk of caustic embrittlement")

        if blowdown:
            warnings.append(f"Conductivity elevated ({telemetry.conductivity_us_cm:.0f} > {self.MAX_CONDUCTIVITY_US_CM} uS/cm) — initiate blowdown")
        if seawater_ingress:
            warnings.append(f"Chloride contamination ({telemetry.chloride_cl_mg_l:.1f} > {self.MAX_CHLORIDE_MG_L} mg/L) — condenser tube leak suspected")

        if seawater_ingress:
            status = "SEAWATER_INGRESS_ALARM"
        elif blowdown:
            status = "CONDUCTIVITY_HIGH_BLOWDOWN_REQUIRED"
        elif scale_ok and passivated and alkaline_ok:
            status = "OPTIMAL_CHEMISTRY_PASSIVATED"
        else:
            status = "DOSING_ADJUSTMENT_REQUIRED"

        compliance_flags = {
            "BS_2486_COMPLIANT": scale_ok and passivated and alkaline_ok and not blowdown,
            "CORROSION_PASSIVATED": passivated,
            "SCALE_PROTECTED": scale_ok,
            "NO_SEAWATER_INGRESS": not seawater_ingress,
        }

        return BoilerWaterAssessment(
            scale_prevention_ok=scale_ok,
            oxygen_passivated=passivated,
            alkalinity_ok=alkaline_ok,
            blowdown_required=blowdown,
            seawater_contamination=seawater_ingress,
            status=status,
            dosing_recommendations=dosing,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
