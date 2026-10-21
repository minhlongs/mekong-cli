"""Oil Tanker VOC Emission Recovery & Vapor Balancing Engine.

Standards: MARPOL Annex VI Reg 15, IMO MSC/Circ.585, OCIMF VEC Systems.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VocRecoveryInput:
    tanker_id: str
    loading_rate_m3_h: float
    vapor_return_capacity_m3_h: float
    tank_pressure_kpa: float
    oxygen_content_pct: float
    voc_concentration_g_m3: float = 800.0  # Typical crude hydrocarbon vapor density
    recovery_efficiency_pct: float = 95.0
    pv_valve_setting_kpa: float = 14.0  # Standard positive P/V valve setpoint
    h2s_content_ppm: float = 0.0


@dataclass
class VocRecoveryReport:
    tanker_id: str
    is_safe_to_load: bool
    is_inerting_compliant: bool
    is_pressure_safe: bool
    is_vapor_balanced: bool
    required_vapor_flow_m3_h: float
    vapor_balance_ratio: float
    voc_recovered_kg_h: float
    co2_eq_offset_kg_h: float
    warnings: List[str]
    metrics: Dict[str, float]


class VocVaporRecoveryBalancingEngine:
    """Monitors closed-loop vapor recovery, inert gas safety, and GHG offsets."""

    MAX_O2_INERT_LIMIT_PCT: float = 8.0  # SOLAS/MARPOL inerting limit
    PRESSURE_SAFETY_MARGIN_RATIO: float = 0.80  # Max 80% P/V setting before alarm
    VAPOR_EXPANSION_RATIO: float = 1.25  # OCIMF 125% loading rate vapor factor
    CO2_EQUIVALENT_FACTOR: float = 2.8  # kg CO2 eq / kg VOC (IMO GHG study)
    H2S_TOXIC_THRESHOLD_PPM: float = 5.0

    def evaluate(self, inp: VocRecoveryInput) -> VocRecoveryReport:
        warnings: List[str] = []

        # 1. Inert Gas Oxygen Envelope (SOLAS II-2/Reg 4.5.5: O2 <= 8% vol)
        is_inerting_compliant = inp.oxygen_content_pct <= self.MAX_O2_INERT_LIMIT_PCT
        if not is_inerting_compliant:
            warnings.append(
                f"High O2 level ({inp.oxygen_content_pct}% > {self.MAX_O2_INERT_LIMIT_PCT}%): "
                "Inert gas compliance failed, explosion risk"
            )

        # 2. Tank Pressure Protection against P/V Valve Setpoint
        max_safe_pressure = inp.pv_valve_setting_kpa * self.PRESSURE_SAFETY_MARGIN_RATIO
        is_pressure_safe = inp.tank_pressure_kpa <= max_safe_pressure
        if not is_pressure_safe:
            warnings.append(
                f"Tank pressure ({inp.tank_pressure_kpa} kPa) exceeds 80% P/V setpoint "
                f"({max_safe_pressure:.1f} kPa)"
            )

        # 3. Vapor Balancing Capacity (Q_vapor >= 1.25 * Q_loading)
        required_vapor_flow = round(inp.loading_rate_m3_h * self.VAPOR_EXPANSION_RATIO, 2)
        vapor_balance_ratio = (
            round(inp.vapor_return_capacity_m3_h / required_vapor_flow, 2)
            if required_vapor_flow > 0
            else 1.0
        )
        is_vapor_balanced = inp.vapor_return_capacity_m3_h >= required_vapor_flow
        if not is_vapor_balanced:
            warnings.append(
                f"Insufficient vapor recovery capacity ({inp.vapor_return_capacity_m3_h} < "
                f"{required_vapor_flow} m3/h)"
            )

        # 4. Toxic Gas H2S Monitoring
        if inp.h2s_content_ppm >= self.H2S_TOXIC_THRESHOLD_PPM:
            warnings.append(
                f"Toxic H2S detected ({inp.h2s_content_ppm} ppm >= "
                f"{self.H2S_TOXIC_THRESHOLD_PPM} ppm): Breathing apparatus required"
            )

        # 5. Mass Recovery & GHG Emissions Avoidance
        effective_vapor_flow = min(inp.vapor_return_capacity_m3_h, required_vapor_flow)
        raw_voc_kg_h = effective_vapor_flow * (inp.voc_concentration_g_m3 / 1000.0)
        voc_recovered_kg_h = round(
            raw_voc_kg_h * (inp.recovery_efficiency_pct / 100.0), 2
        )
        co2_eq_offset_kg_h = round(voc_recovered_kg_h * self.CO2_EQUIVALENT_FACTOR, 2)

        # Overall safety gating
        is_safe_to_load = is_inerting_compliant and is_pressure_safe and is_vapor_balanced

        return VocRecoveryReport(
            tanker_id=inp.tanker_id,
            is_safe_to_load=is_safe_to_load,
            is_inerting_compliant=is_inerting_compliant,
            is_pressure_safe=is_pressure_safe,
            is_vapor_balanced=is_vapor_balanced,
            required_vapor_flow_m3_h=required_vapor_flow,
            vapor_balance_ratio=vapor_balance_ratio,
            voc_recovered_kg_h=voc_recovered_kg_h,
            co2_eq_offset_kg_h=co2_eq_offset_kg_h,
            warnings=warnings,
            metrics={
                "tank_pressure_kpa": inp.tank_pressure_kpa,
                "oxygen_content_pct": inp.oxygen_content_pct,
                "effective_vapor_flow_m3_h": effective_vapor_flow,
                "co2_offset_factor": self.CO2_EQUIVALENT_FACTOR,
            },
        )
