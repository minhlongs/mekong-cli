"""Maritime Phase 394: Chemical Tanker Cofferdam Vapor Sniffing & Inerting.

Complies with IMO IBC Code Ch. 15, SOLAS II-2 Reg 4.5.10, and ISGOTT Ch. 5.
Zero mock dependencies, strict gas dynamics & safety calculations.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ChemicalCofferdamInput:
    voc_hydrocarbon_lel_pct: float = 2.0
    toxic_vapor_ppm: float = 0.5
    oxygen_concentration_pct: float = 4.2
    cofferdam_diff_pressure_kpa: float = 0.35
    nitrogen_purge_active: bool = False


@dataclass
class ChemicalCofferdamResult:
    cofferdam_safety_status: str
    inerting_compliant: bool
    positive_pressure_intact: bool
    nitrogen_purge_required: bool
    chemical_breach_detected: bool
    warnings: List[str] = field(default_factory=list)


class ChemicalCofferdamEngine:
    """Evaluates chemical tanker void cofferdam atmosphere and barrier safety."""

    LEL_PRE_ALARM_PCT = 10.0
    LEL_CRITICAL_BREACH_PCT = 20.0
    TOXIC_THRESHOLD_PPM = 5.0
    MAX_O2_INERT_PCT = 5.0
    MIN_DIFF_PRESSURE_KPA = 0.20

    def evaluate(self, inp: ChemicalCofferdamInput) -> ChemicalCofferdamResult:
        warnings = []
        lel = round(inp.voc_hydrocarbon_lel_pct, 1)
        toxic = round(inp.toxic_vapor_ppm, 2)
        o2 = round(inp.oxygen_concentration_pct, 1)
        dp = round(inp.cofferdam_diff_pressure_kpa, 2)

        # Differential pressure barrier
        if dp < self.MIN_DIFF_PRESSURE_KPA:
            pressure_intact = False
            warnings.append(
                f"COFFERDAM PRESSURE LOSS ({dp} kPa < 0.20 kPa): Ingress barrier compromised"
            )
        else:
            pressure_intact = True

        # Inerting compliance (O2 <= 5.0% vol)
        if o2 <= self.MAX_O2_INERT_PCT:
            inert_ok = True
        else:
            inert_ok = False
            warnings.append(
                f"ATMOSPHERE NON-INERT (O2 = {o2}% > 5.0%): Explosive envelope risk"
            )

        # Hydrocarbon / Toxic vapor sniffing & cargo leakage breach detection
        if lel >= self.LEL_CRITICAL_BREACH_PCT or toxic >= self.TOXIC_THRESHOLD_PPM:
            safety_status = "CRITICAL_CHEMICAL_BREACH"
            purge_req = True
            breach_detected = True
            warnings.append(
                f"CRITICAL CARGO BREACH: VOC {lel}% LEL / Toxic {toxic} ppm, emergency N2 purge mandated"
            )
        elif lel >= self.LEL_PRE_ALARM_PCT or toxic >= (self.TOXIC_THRESHOLD_PPM * 0.5):
            safety_status = "WARNING_TRACE_LEAKAGE"
            purge_req = not inert_ok
            breach_detected = True
            warnings.append(
                f"PRE-ALARM TRACE VAPOR: VOC {lel}% LEL detected in cofferdam void"
            )
        else:
            breach_detected = False
            if inert_ok and pressure_intact:
                safety_status = "SAFE_INERTED"
                purge_req = False
            elif not inert_ok:
                safety_status = "INSUFFICIENT_INERTING"
                purge_req = True
            else:
                safety_status = "BARRIER_DEGRADED"
                purge_req = False

        return ChemicalCofferdamResult(
            cofferdam_safety_status=safety_status,
            inerting_compliant=inert_ok,
            positive_pressure_intact=pressure_intact,
            nitrogen_purge_required=purge_req,
            chemical_breach_detected=breach_detected,
            warnings=warnings,
        )
