"""Phase 420: STP Electrolytic Chlorination & Overboard Dechlorination.

Implements IMO Resolution MEPC.227(64) and MARPOL Annex IV standards:
Electrolytic NaOCl generation, Total Residual Chlorine (TRC) disinfection,
active bisulfite dechlorination before overboard discharge, and TSS/COD compliance.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StpChlorinationTelemetry:
    """Telemetry readings for marine STP electrolytic disinfection system."""
    effluent_flow_m3_h: float = 2.5
    cell_current_amperes: float = 25.0
    cell_voltage_volts: float = 12.0
    salinity_ppt: float = 30.0               # Seawater feed ~30-35 ppt
    disinfection_tank_trc_ppm: float = 2.2   # Total Residual Chlorine in contact tank (target 1.5 - 3.0)
    overboard_trc_ppm: float = 0.2           # Residual Cl2 after dechlorination (limit < 0.5 ppm)
    turbidity_ntu: float = 12.0              # Target < 25 NTU
    chemical_oxygen_demand_mg_l: float = 95.0 # Proxy for BOD5/COD limit (COD < 125 mg/L)
    aeration_blower_running: bool = True
    dechlorination_agent_level_pct: float = 65.0


@dataclass(frozen=True)
class StpChlorinationAssessment:
    """Assessment of effluent disinfection, dechlorination efficacy, and overboard permissives."""
    disinfection_effective: bool
    dechlorination_effective: bool
    electrolytic_cell_efficiency_pct: float
    overboard_discharge_permitted: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class StpChlorinationEngine:
    """Evaluates electrolytic NaOCl dosing, contact time disinfection, and discharge safety."""

    MIN_DISINFECTION_TRC_PPM: float = 1.5
    MAX_OVERBOARD_TRC_PPM: float = 0.5
    MAX_COD_MG_L: float = 125.0
    MAX_TURBIDITY_NTU: float = 25.0
    MIN_SALINITY_PPT: float = 15.0

    def evaluate(self, telemetry: StpChlorinationTelemetry) -> StpChlorinationAssessment:
        warnings: List[str] = []

        # Electrolytic cell efficiency: ideal yield ~0.4 kg NaOCl per kAh
        power_kw = (telemetry.cell_current_amperes * telemetry.cell_voltage_volts) / 1000.0
        efficiency_pct = min(100.0, max(0.0, (telemetry.cell_current_amperes / 30.0) * (telemetry.salinity_ppt / 35.0) * 100.0))

        if telemetry.salinity_ppt < self.MIN_SALINITY_PPT:
            warnings.append(f"Low salinity ({telemetry.salinity_ppt} ppt): insufficient chloride ions for NaOCl electrolysis")

        # Disinfection verification in contact chamber
        disinfection_effective = telemetry.disinfection_tank_trc_ppm >= self.MIN_DISINFECTION_TRC_PPM
        if not disinfection_effective:
            warnings.append(f"Inadequate disinfection: TRC {telemetry.disinfection_tank_trc_ppm} ppm < {self.MIN_DISINFECTION_TRC_PPM} ppm")

        # Dechlorination verification prior to overboard
        dechlorination_effective = telemetry.overboard_trc_ppm <= self.MAX_OVERBOARD_TRC_PPM
        if not dechlorination_effective:
            warnings.append(f"Dechlorination failure: Overboard TRC {telemetry.overboard_trc_ppm} ppm exceeds {self.MAX_OVERBOARD_TRC_PPM} ppm limit")

        if telemetry.dechlorination_agent_level_pct < 15.0:
            warnings.append("Low sodium bisulfite dechlorination reagent level (< 15%)")

        if not telemetry.aeration_blower_running:
            warnings.append("Aeration blower stopped: bio-oxidation compromised")

        # Overboard Permissive Gate
        overboard_permitted = (
            disinfection_effective and
            dechlorination_effective and
            telemetry.chemical_oxygen_demand_mg_l <= self.MAX_COD_MG_L and
            telemetry.turbidity_ntu <= self.MAX_TURBIDITY_NTU and
            telemetry.aeration_blower_running
        )

        if not overboard_permitted:
            warnings.append("Overboard discharge valve locked shut: effluent recirculated to holding tank")

        status = "NORMAL" if overboard_permitted and not warnings else ("WARNING" if overboard_permitted else "ISOLATED")

        return StpChlorinationAssessment(
            disinfection_effective=disinfection_effective,
            dechlorination_effective=dechlorination_effective,
            electrolytic_cell_efficiency_pct=round(efficiency_pct, 2),
            overboard_discharge_permitted=overboard_permitted,
            status=status,
            warnings=warnings,
            compliance_flags={
                "mepc_227_64_trc_disinfected": disinfection_effective,
                "marpol_annex_iv_dechlorinated": dechlorination_effective,
                "cod_within_effluent_limits": telemetry.chemical_oxygen_demand_mg_l <= self.MAX_COD_MG_L,
                "turbidity_clarity_compliant": telemetry.turbidity_ntu <= self.MAX_TURBIDITY_NTU,
            },
        )
