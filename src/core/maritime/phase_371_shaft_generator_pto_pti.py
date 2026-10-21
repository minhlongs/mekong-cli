"""Marine Shaft Generator & PTO/PTI Hybrid Propulsion Engine.

Standards: DNV-RU-SHIP Pt.4 Ch.8, IEC 60092-501, IMO MEPC.333(76) (EEXI/CII).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ShaftHybridMode(str, Enum):
    """Shaft generator operational modes."""

    PTO = "PTO"  # Power Take-Off (supplies ship service grid)
    PTI = "PTI"  # Power Take-In (motor booster for propulsion)
    PTH = "PTH"  # Power Take-Home (emergency electric propulsion)
    DISENGAGED = "DISENGAGED"


@dataclass
class ShaftGeneratorInput:
    vessel_id: str
    main_engine_mcr_kw: float
    main_engine_speed_rpm: float
    main_engine_rated_rpm: float
    current_me_load_kw: float
    shaft_gen_capacity_kw: float
    shaft_power_kw: float
    hotel_load_kw: float
    requested_mode: ShaftHybridMode
    sfoc_aux_diesel_g_kwh: float = 215.0
    sfoc_main_engine_g_kwh: float = 165.0
    fuel_price_usd_tonne: float = 650.0


@dataclass
class ShaftGeneratorPtoPtiReport:
    vessel_id: str
    active_mode: ShaftHybridMode
    is_pto_permitted: bool
    me_speed_ratio_pct: float
    me_combined_load_pct_mcr: float
    fuel_savings_kg_per_h: float
    cost_savings_usd_per_h: float
    co2_reduction_kg_per_h: float
    warnings: List[str]
    metrics: Dict[str, float]


class ShaftGeneratorPtoPtiEngine:
    """Manages shaft generator PTO/PTI hybrid control, limits, and fuel gains."""

    MIN_PTO_SPEED_RATIO_PCT: float = 65.0  # Inhibit PTO below 65% MCR speed
    TORQUE_LIMIT_WARNING_PCT: float = 80.0  # Overload warning threshold
    CO2_FACTOR_KG_PER_KG_FUEL: float = 3.114  # IMO MEPC carbon factor

    def evaluate(self, inp: ShaftGeneratorInput) -> ShaftGeneratorPtoPtiReport:
        warnings: List[str] = []
        speed_ratio = (
            inp.main_engine_speed_rpm / max(inp.main_engine_rated_rpm, 1.0)
        ) * 100.0

        active_mode = inp.requested_mode
        is_pto_permitted = True
        actual_pto_kw = 0.0

        if inp.requested_mode == ShaftHybridMode.PTO:
            if speed_ratio < self.MIN_PTO_SPEED_RATIO_PCT:
                is_pto_permitted = False
                active_mode = ShaftHybridMode.DISENGAGED
                warnings.append(
                    f"PTO inhibited: Engine speed {speed_ratio:.1f}% < "
                    f"minimum {self.MIN_PTO_SPEED_RATIO_PCT}% rated RPM"
                )
            else:
                actual_pto_kw = min(inp.shaft_power_kw, inp.shaft_gen_capacity_kw)
                if actual_pto_kw < inp.hotel_load_kw:
                    warnings.append(
                        f"PTO power {actual_pto_kw:.1f} kW cannot fully meet "
                        f"hotel load {inp.hotel_load_kw:.1f} kW; aux gen needed"
                    )

        combined_me_kw = inp.current_me_load_kw
        if active_mode == ShaftHybridMode.PTO:
            combined_me_kw += actual_pto_kw
        elif active_mode in (ShaftHybridMode.PTI, ShaftHybridMode.PTH):
            # PTI reduces ME torque demand
            combined_me_kw = max(0.0, combined_me_kw - inp.shaft_power_kw)

        combined_load_pct = (
            combined_me_kw / max(inp.main_engine_mcr_kw, 1.0)
        ) * 100.0

        if combined_load_pct > self.TORQUE_LIMIT_WARNING_PCT:
            warnings.append(
                f"ME total load {combined_load_pct:.1f}% MCR exceeds "
                f"limit {self.TORQUE_LIMIT_WARNING_PCT}%: Torque overload risk"
            )

        fuel_saving_kg_h = 0.0
        cost_saving_usd_h = 0.0
        co2_reduction_kg_h = 0.0

        if active_mode == ShaftHybridMode.PTO and is_pto_permitted:
            sfoc_diff = max(
                0.0, inp.sfoc_aux_diesel_g_kwh - inp.sfoc_main_engine_g_kwh
            )
            fuel_saving_kg_h = (actual_pto_kw * sfoc_diff) / 1000.0
            cost_saving_usd_h = (
                fuel_saving_kg_h / 1000.0
            ) * inp.fuel_price_usd_tonne
            co2_reduction_kg_h = fuel_saving_kg_h * self.CO2_FACTOR_KG_PER_KG_FUEL
        elif active_mode == ShaftHybridMode.PTH:
            warnings.append(
                "PTH Take-Me-Home booster mode engaged: ME derated/offline"
            )

        metrics = {
            "main_engine_mcr_kw": inp.main_engine_mcr_kw,
            "engine_speed_ratio_pct": round(speed_ratio, 2),
            "combined_load_pct_mcr": round(combined_load_pct, 2),
            "delivered_shaft_power_kw": round(actual_pto_kw or inp.shaft_power_kw, 2),
            "fuel_savings_kg_per_h": round(fuel_saving_kg_h, 2),
            "cost_savings_usd_per_h": round(cost_saving_usd_h, 2),
            "co2_reduction_kg_per_h": round(co2_reduction_kg_h, 2),
        }

        return ShaftGeneratorPtoPtiReport(
            vessel_id=inp.vessel_id,
            active_mode=active_mode,
            is_pto_permitted=is_pto_permitted,
            me_speed_ratio_pct=round(speed_ratio, 2),
            me_combined_load_pct_mcr=round(combined_load_pct, 2),
            fuel_savings_kg_per_h=round(fuel_saving_kg_h, 2),
            cost_savings_usd_per_h=round(cost_saving_usd_h, 2),
            co2_reduction_kg_per_h=round(co2_reduction_kg_h, 2),
            warnings=warnings,
            metrics=metrics,
        )
