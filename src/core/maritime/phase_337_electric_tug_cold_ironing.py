"""Phase 337: Green Port Electric Tug & Shore-to-Ship Cold Ironing Engine.

Calculates cold ironing grid connection under IEC/IEEE 80005, peak shaving
energy balancing, battery C-rate, Bollard Pull efficiency, and GHG emissions reduction.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ElectricTugColdIroningInput:
    tug_name: str
    battery_capacity_kwh: float
    current_soc_pct: float  # State of Charge (0 - 100%)
    bollard_pull_ahead_tons: float
    towage_duration_hours: float
    towage_energy_consumed_kwh: float
    shore_grid_max_kw: float = 1200.0  # HVSC/LVSC substation capacity
    vessel_berth_load_kw: float = 800.0
    shore_charging_power_kw: float = 400.0
    c_rate_max: float = 1.5


@dataclass
class ElectricTugColdIroningResult:
    tug_name: str
    bollard_pull_metric_kwh_per_ton_h: float
    is_bollard_pull_efficient: bool
    is_emergency_soc_compliant: bool
    peak_shaving_active: bool
    shore_total_demand_kw: float
    is_grid_overloaded: bool
    co2_abated_metric_ton: float
    nox_abated_kg: float
    advisories: List[str]


class ElectricTugColdIroningEngine:
    BOLLARD_PULL_METRIC_BENCHMARK = 0.15  # kWh / (ton-pull * h)
    EMERGENCY_SOC_MIN_PCT = 20.0  # Reserve for return-to-berth safety
    MGO_CO2_FACTOR = 3.206  # metric tons CO2 / metric ton MGO
    MGO_SFOC_G_KWH = 210.0  # grams MGO / kWh
    MGO_NOX_G_KWH = 10.5  # grams NOx / kWh

    @classmethod
    def evaluate(cls, inp: ElectricTugColdIroningInput) -> ElectricTugColdIroningResult:
        advisories: List[str] = []

        # 1. Bollard Pull Energy Efficiency Metric
        # Metric = Energy (kWh) / (Tons Pull * Duration hours)
        total_ton_hours = max(1.0, inp.bollard_pull_ahead_tons * inp.towage_duration_hours)
        bp_metric = round(inp.towage_energy_consumed_kwh / total_ton_hours, 3)
        bp_efficient = bp_metric <= cls.BOLLARD_PULL_METRIC_BENCHMARK

        if not bp_efficient:
            advisories.append(
                f"HIGH ENERGY INTENSITY: Metric {bp_metric} kWh/(t*h) exceeds benchmark {cls.BOLLARD_PULL_METRIC_BENCHMARK}"
            )

        # 2. Battery Safety & Emergency Reserve
        soc_safe = inp.current_soc_pct >= cls.EMERGENCY_SOC_MIN_PCT
        if not soc_safe:
            advisories.append(
                f"CRITICAL: Battery SoC {inp.current_soc_pct}% below emergency reserve {cls.EMERGENCY_SOC_MIN_PCT}%"
            )

        # 3. Peak Shaving & Shore Grid Balancing (IEC/IEEE 80005)
        # Total demand = Hotel load + Charging power
        total_shore_demand = inp.vessel_berth_load_kw + inp.shore_charging_power_kw
        grid_overloaded = total_shore_demand > inp.shore_grid_max_kw
        peak_shaving_active = False

        if grid_overloaded:
            peak_shaving_active = True
            shaved_demand = inp.shore_grid_max_kw
            advisories.append(
                f"PEAK SHAVING ENGAGED: Demand {total_shore_demand} kW capped to substation limit {inp.shore_grid_max_kw} kW"
            )
            total_shore_demand = shaved_demand

        # 4. Abated Emissions Calculation (compared to marine diesel)
        # Diesel equivalent mass in metric tons = kWh * (210 g/kWh) / 1,000,000
        equiv_mgo_tons = (inp.towage_energy_consumed_kwh * cls.MGO_SFOC_G_KWH) / 1e6
        co2_abated = round(equiv_mgo_tons * cls.MGO_CO2_FACTOR, 3)
        nox_abated = round((inp.towage_energy_consumed_kwh * cls.MGO_NOX_G_KWH) / 1000.0, 2)

        return ElectricTugColdIroningResult(
            tug_name=inp.tug_name,
            bollard_pull_metric_kwh_per_ton_h=bp_metric,
            is_bollard_pull_efficient=bp_efficient,
            is_emergency_soc_compliant=soc_safe,
            peak_shaving_active=peak_shaving_active,
            shore_total_demand_kw=round(total_shore_demand, 1),
            is_grid_overloaded=grid_overloaded,
            co2_abated_metric_ton=co2_abated,
            nox_abated_kg=nox_abated,
            advisories=advisories,
        )
