"""Phase 436: Sewage Treatment Plant (STP) Membrane Bioreactor (MBR) Effluent Quality.

Implements IMO Resolution MEPC.227(64) & MARPOL Annex IV:
- Effluent purity monitoring (TSS <= 35 mg/L, COD <= 125 mg/L, BOD5 <= 25 mg/L, Coliform <= 100 CFU/100mL).
- Residual free chlorine monitoring (<= 0.5 mg/L) to prevent marine ecotoxicity.
- Transmembrane differential pressure (TMP <= 0.45 bar) and automatic divert to holding tank.
Strictly < 150 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StpEffluentTelemetry:
    """Telemetry readings for STP Membrane Bioreactor effluent and permeate sensors."""
    transmembrane_dp_bar: float = 0.22      # Transmembrane pressure (feed vs permeate)
    total_suspended_solids_mg_l: float = 8.5 # Benchmark <= 35 mg/L
    chemical_oxygen_demand_mg_l: float = 45.0# Benchmark <= 125 mg/L
    biological_oxygen_demand_mg_l: float = 12.0 # Benchmark <= 25 mg/L
    coliform_cfu_100ml: float = 15.0        # Benchmark <= 100 CFU/100mL
    free_chlorine_mg_l: float = 0.25        # Benchmark <= 0.5 mg/L
    permeate_flow_m3_h: float = 2.4
    holding_tank_level_pct: float = 28.0


@dataclass(frozen=True)
class StpEffluentAssessment:
    """MEPC.227(64) compliance assessment and discharge valve interlock decision."""
    discharge_permitted: bool
    divert_to_holding_tank: bool
    membrane_fouled: bool
    chlorine_in_limit: bool
    coliform_in_limit: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class StpEffluentEngine:
    """Evaluates MBR sewage effluent quality against IMO MEPC.227(64) standards."""

    MAX_TMP_BAR: float = 0.45
    MAX_TSS_MG_L: float = 35.0
    MAX_COD_MG_L: float = 125.0
    MAX_BOD_MG_L: float = 25.0
    MAX_COLIFORM_CFU: float = 100.0
    MAX_FREE_CHLORINE_MG_L: float = 0.50

    def evaluate(self, telemetry: StpEffluentTelemetry) -> StpEffluentAssessment:
        warnings: List[str] = []

        membrane_fouled = telemetry.transmembrane_dp_bar > self.MAX_TMP_BAR
        tss_ok = telemetry.total_suspended_solids_mg_l <= self.MAX_TSS_MG_L
        cod_ok = telemetry.chemical_oxygen_demand_mg_l <= self.MAX_COD_MG_L
        bod_ok = telemetry.biological_oxygen_demand_mg_l <= self.MAX_BOD_MG_L
        coliform_ok = telemetry.coliform_cfu_100ml <= self.MAX_COLIFORM_CFU
        chlorine_ok = telemetry.free_chlorine_mg_l <= self.MAX_FREE_CHLORINE_MG_L

        if membrane_fouled:
            warnings.append(f"MBR Transmembrane DP high ({telemetry.transmembrane_dp_bar:.3f} > {self.MAX_TMP_BAR} bar)")
        if not tss_ok:
            warnings.append(f"TSS exceeded ({telemetry.total_suspended_solids_mg_l:.1f} > {self.MAX_TSS_MG_L} mg/L)")
        if not cod_ok:
            warnings.append(f"COD exceeded ({telemetry.chemical_oxygen_demand_mg_l:.1f} > {self.MAX_COD_MG_L} mg/L)")
        if not bod_ok:
            warnings.append(f"BOD5 exceeded ({telemetry.biological_oxygen_demand_mg_l:.1f} > {self.MAX_BOD_MG_L} mg/L)")
        if not coliform_ok:
            warnings.append(f"Coliform counts exceeded ({telemetry.coliform_cfu_100ml:.0f} > {self.MAX_COLIFORM_CFU} CFU)")
        if not chlorine_ok:
            warnings.append(f"Residual chlorine toxic ({telemetry.free_chlorine_mg_l:.2f} > {self.MAX_FREE_CHLORINE_MG_L} mg/L)")

        water_quality_ok = tss_ok and cod_ok and bod_ok and coliform_ok and chlorine_ok
        discharge_permitted = water_quality_ok and not membrane_fouled
        divert = not discharge_permitted

        if discharge_permitted:
            status = "MEPC_227_DISCHARGE_APPROVED"
        elif membrane_fouled and water_quality_ok:
            status = "MEMBRANE_CLEAN_REQUIRED"
        else:
            status = "EFFLUENT_NON_COMPLIANT_DIVERTED"

        compliance_flags = {
            "MEPC_227_64_COMPLIANT": water_quality_ok,
            "MARPOL_ANNEX_IV_VALID": water_quality_ok and discharge_permitted,
            "DISINFECTION_SAFE": chlorine_ok and coliform_ok,
            "TMP_WITHIN_DESIGN": not membrane_fouled,
        }

        return StpEffluentAssessment(
            discharge_permitted=discharge_permitted,
            divert_to_holding_tank=divert,
            membrane_fouled=membrane_fouled,
            chlorine_in_limit=chlorine_ok,
            coliform_in_limit=coliform_ok,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
