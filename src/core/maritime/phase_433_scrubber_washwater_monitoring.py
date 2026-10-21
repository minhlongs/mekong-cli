"""Phase 433: Marine Wet Exhaust Gas Scrubber Washwater Quality Monitoring.

Implements IMO Resolution MEPC.340(77):
- Polycyclic Aromatic Hydrocarbons (PAH): normalized limit <= 50 ug/L phenanthrene eq.
- Turbidity: delta NTU <= 25 FNU above inlet water.
- Acidity: pH >= 6.5 at overboard discharge (or 4.0 m from shipside).
- Nitrates: <= 60 mg/L (or 12% total NOx removal limit).
Strictly < 160 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ScrubberWashwaterTelemetry:
    """Telemetry readings for exhaust gas cleaning system (EGCS) washwater effluent."""
    discharge_flow_m3_h: float = 450.0
    inlet_turbidity_fnu: float = 3.2
    discharge_turbidity_fnu: float = 18.5
    discharge_pah_ug_l: float = 24.0
    discharge_ph: float = 6.8
    nitrate_mg_l: float = 28.0
    engine_power_mcr_mw: float = 14.5


@dataclass(frozen=True)
class ScrubberWashwaterAssessment:
    """Washwater discharge compliance against IMO MEPC.340(77)."""
    delta_turbidity_fnu: float
    turbidity_compliant: bool
    pah_compliant: bool
    ph_compliant: bool
    nitrate_compliant: bool
    overboard_discharge_allowed: bool
    divert_to_holding_tank: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class ScrubberWashwaterEngine:
    """Evaluates EGCS wet scrubber effluent compliance against MARPOL Annex VI / MEPC.340(77)."""

    MAX_DELTA_TURBIDITY_FNU: float = 25.0
    MAX_PAH_UG_L: float = 50.0
    MIN_DISCHARGE_PH: float = 6.5
    CRITICAL_LOW_PH: float = 6.0
    MAX_NITRATE_MG_L: float = 60.0

    def evaluate(self, telemetry: ScrubberWashwaterTelemetry) -> ScrubberWashwaterAssessment:
        warnings: List[str] = []

        delta_turbidity = round(max(0.0, telemetry.discharge_turbidity_fnu - telemetry.inlet_turbidity_fnu), 2)
        turbidity_ok = delta_turbidity <= self.MAX_DELTA_TURBIDITY_FNU
        if not turbidity_ok:
            warnings.append(f"EXCEEDANCE: Delta turbidity ({delta_turbidity:.1f} FNU > {self.MAX_DELTA_TURBIDITY_FNU} FNU)")

        pah_ok = telemetry.discharge_pah_ug_l <= self.MAX_PAH_UG_L
        if not pah_ok:
            warnings.append(f"EXCEEDANCE: PAH concentration ({telemetry.discharge_pah_ug_l:.1f} ug/L > {self.MAX_PAH_UG_L} ug/L)")

        ph_ok = telemetry.discharge_ph >= self.MIN_DISCHARGE_PH
        if telemetry.discharge_ph < self.CRITICAL_LOW_PH:
            warnings.append(f"CRITICAL: Acidic discharge (pH {telemetry.discharge_ph:.2f} < {self.CRITICAL_LOW_PH:.1f}) - risk of hull corrosion")
        elif not ph_ok:
            warnings.append(f"EXCEEDANCE: Discharge pH below limit ({telemetry.discharge_ph:.2f} < {self.MIN_DISCHARGE_PH:.1f})")

        nitrate_ok = telemetry.nitrate_mg_l <= self.MAX_NITRATE_MG_L
        if not nitrate_ok:
            warnings.append(f"EXCEEDANCE: Nitrate concentration ({telemetry.nitrate_mg_l:.1f} mg/L > {self.MAX_NITRATE_MG_L} mg/L)")

        all_compliant = turbidity_ok and pah_ok and ph_ok and nitrate_ok
        divert_to_holding_tank = not all_compliant
        overboard_discharge_allowed = all_compliant

        if divert_to_holding_tank:
            warnings.append("ACTION: Overboard valve locked - washwater diverted to closed-loop / holding tank")

        if not ph_ok or not pah_ok:
            status = "MARPOL_VIOLATION_DIVERTED"
        elif not turbidity_ok or not nitrate_ok:
            status = "NON_COMPLIANT_DIVERTED"
        else:
            status = "MEPC_340_COMPLIANT_DISCHARGING"

        compliance_flags = {
            "TURBIDITY_COMPLIANT": turbidity_ok,
            "PAH_COMPLIANT": pah_ok,
            "PH_COMPLIANT": ph_ok,
            "NITRATE_COMPLIANT": nitrate_ok,
            "MEPC_340_77_OVERBOARD_PERMITTED": overboard_discharge_allowed,
        }

        return ScrubberWashwaterAssessment(
            delta_turbidity_fnu=delta_turbidity,
            turbidity_compliant=turbidity_ok,
            pah_compliant=pah_ok,
            ph_compliant=ph_ok,
            nitrate_compliant=nitrate_ok,
            overboard_discharge_allowed=overboard_discharge_allowed,
            divert_to_holding_tank=divert_to_holding_tank,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
