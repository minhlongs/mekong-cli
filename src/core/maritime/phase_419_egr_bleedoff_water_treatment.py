"""Phase 419: EGR Bleed-off Water Treatment System (WTS).

Implements IMO MARPOL Annex VI Tier III and MEPC.307(73) 2018 Guidelines for EGR
Bleed-off Water Discharge: oil content monitoring (< 15 ppm), turbidity (< 25 FNU),
pH optical sensing (>= 6.5 via NaOH dosing), PAH measurement, and fail-safe
3-way divert valve interlocks to holding tank.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class EgrBleedoffTelemetry:
    """Telemetry readings for EGR Bleed-off Water Treatment System."""
    oil_content_ppm: float = 4.2
    ph_value: float = 7.35
    turbidity_fnu: float = 12.4
    inlet_turbidity_fnu: float = 2.1
    pah_concentration_ug_l: float = 22.0
    water_flow_rate_m3_h: float = 15.0
    naoh_dosing_rate_l_h: float = 2.4
    holding_tank_level_pct: float = 38.0
    divert_valve_override: bool = False


@dataclass(frozen=True)
class EgrBleedoffAssessment:
    """Discharge compliance and valve routing assessment for EGR WTS."""
    oil_compliant: bool
    ph_compliant: bool
    turbidity_compliant: bool
    pah_compliant: bool
    net_turbidity_fnu: float
    divert_valve_position: str
    discharge_flow_m3_h: float
    holding_tank_inflow_m3_h: float
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class EgrBleedoffWaterTreatmentEngine:
    """Evaluates EGR scrubber bleed-off water quality and controls overboard divert valve."""

    MAX_OIL_PPM: float = 15.0
    MIN_PH: float = 6.5
    MAX_TURBIDITY_DELTA_FNU: float = 25.0
    MAX_PAH_UG_L: float = 50.0
    HOLDING_TANK_HIGH_LEVEL_PCT: float = 85.0

    def evaluate(self, telemetry: EgrBleedoffTelemetry) -> EgrBleedoffAssessment:
        warnings: List[str] = []

        net_turbidity = max(0.0, telemetry.turbidity_fnu - telemetry.inlet_turbidity_fnu)
        oil_ok = telemetry.oil_content_ppm < self.MAX_OIL_PPM
        ph_ok = telemetry.ph_value >= self.MIN_PH
        turbidity_ok = (telemetry.turbidity_fnu <= self.MAX_TURBIDITY_DELTA_FNU) or (
            net_turbidity <= self.MAX_TURBIDITY_DELTA_FNU
        )
        pah_ok = telemetry.pah_concentration_ug_l <= self.MAX_PAH_UG_L

        if not oil_ok:
            warnings.append(
                f"High oil content in EGR bleed-off: {telemetry.oil_content_ppm:.1f} ppm "
                f"(MARPOL limit < {self.MAX_OIL_PPM:.1f} ppm)"
            )
        if not ph_ok:
            warnings.append(
                f"Low bleed-off pH: {telemetry.ph_value:.2f} (MEPC.307 limit >= {self.MIN_PH:.1f})"
            )
        if not turbidity_ok:
            warnings.append(
                f"High turbidity: {telemetry.turbidity_fnu:.1f} FNU "
                f"(limit <= {self.MAX_TURBIDITY_DELTA_FNU:.1f} FNU above inlet)"
            )
        if not pah_ok:
            warnings.append(
                f"High PAH concentration: {telemetry.pah_concentration_ug_l:.1f} ug/L "
                f"(limit <= {self.MAX_PAH_UG_L:.1f} ug/L)"
            )

        tank_full = telemetry.holding_tank_level_pct >= self.HOLDING_TANK_HIGH_LEVEL_PCT
        if tank_full:
            warnings.append(
                f"Holding tank level high: {telemetry.holding_tank_level_pct:.1f}% "
                f"(threshold {self.HOLDING_TANK_HIGH_LEVEL_PCT:.1f}%)"
            )

        all_compliant = oil_ok and ph_ok and turbidity_ok and pah_ok

        # Interlock: Fail-safe 3-way valve diverts to holding tank if non-compliant or overridden
        can_discharge = all_compliant and not telemetry.divert_valve_override

        if can_discharge:
            valve_pos = "OVERBOARD_DISCHARGE"
            discharge_flow = telemetry.water_flow_rate_m3_h
            holding_inflow = 0.0
            status = "COMPLIANT"
        else:
            valve_pos = "HOLDING_TANK_RECIRC"
            discharge_flow = 0.0
            holding_inflow = telemetry.water_flow_rate_m3_h
            status = "NON_COMPLIANT_DIVERTED" if not all_compliant else "MANUAL_RECIRC"

        compliance_flags = {
            "oil_under_15ppm": oil_ok,
            "ph_above_6_5": ph_ok,
            "turbidity_under_25fnu": turbidity_ok,
            "pah_under_50ug_l": pah_ok,
            "overboard_discharge_authorized": can_discharge,
            "holding_tank_available": not tank_full,
        }

        return EgrBleedoffAssessment(
            oil_compliant=oil_ok,
            ph_compliant=ph_ok,
            turbidity_compliant=turbidity_ok,
            pah_compliant=pah_ok,
            net_turbidity_fnu=round(net_turbidity, 2),
            divert_valve_position=valve_pos,
            discharge_flow_m3_h=round(discharge_flow, 2),
            holding_tank_inflow_m3_h=round(holding_inflow, 2),
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
