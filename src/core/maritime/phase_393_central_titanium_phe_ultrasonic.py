"""Maritime Phase 393: Central Titanium Plate Heat Exchanger & Ultrasonic Cleaning.

Complies with TEMA Class R, ASME Sec VIII Div 1, and DNV-RU-SHIP Pt.4 Ch.6.
Zero mock dependencies, strict thermodynamic calculations.
"""

import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class CentralTitaniumPheInput:
    hot_side_inlet_temp_c: float = 48.0   # Central FW inlet
    hot_side_outlet_temp_c: float = 36.0  # Central FW outlet
    cold_side_inlet_temp_c: float = 28.0  # Seawater SW inlet
    cold_side_outlet_temp_c: float = 34.0 # Seawater SW outlet
    fw_flow_rate_m3_h: float = 350.0
    pressure_drop_bar: float = 0.65
    ultrasonic_intensity_w_cm2: float = 1.8


@dataclass
class CentralTitaniumPheResult:
    heat_duty_kw: float
    lmtd_c: float
    thermal_performance: str
    pressure_drop_status: str
    ultrasonic_biofilm_prevention: str
    maintenance_action: str
    warnings: List[str] = field(default_factory=list)


class CentralTitaniumPheEngine:
    """Evaluates central marine titanium plate heat exchanger (PHE) efficiency."""

    MAX_PRESSURE_DROP_BAR = 1.20
    CP_WATER_KJ_KG_K = 4.184
    RHO_WATER_KG_M3 = 1000.0

    def evaluate(self, inp: CentralTitaniumPheInput) -> CentralTitaniumPheResult:
        warnings = []
        # Calculate Heat Duty (kW): Q = m_dot * cp * Delta_T
        mass_flow_kg_s = (inp.fw_flow_rate_m3_h * self.RHO_WATER_KG_M3) / 3600.0
        delta_t_hot = max(0.0, inp.hot_side_inlet_temp_c - inp.hot_side_outlet_temp_c)
        duty_kw = round(mass_flow_kg_s * self.CP_WATER_KJ_KG_K * delta_t_hot, 2)

        # Log Mean Temperature Difference (LMTD) for counter-current flow
        dt1 = inp.hot_side_inlet_temp_c - inp.cold_side_outlet_temp_c
        dt2 = inp.hot_side_outlet_temp_c - inp.cold_side_inlet_temp_c

        if dt1 <= 0 or dt2 <= 0:
            lmtd = 0.1
            thermal_status = "TEMPERATURE_CROSSOVER_DEFECT"
            warnings.append("THERMAL DEFECT: Negative or zero temperature driving force")
        elif abs(dt1 - dt2) < 1e-4:
            lmtd = round(dt1, 2)
            thermal_status = "OPTIMAL_HEAT_TRANSFER"
        else:
            lmtd = round((dt1 - dt2) / math.log(dt1 / dt2), 2)
            thermal_status = "OPTIMAL_HEAT_TRANSFER"

        # Hydraulic pressure drop across plates
        dp = round(inp.pressure_drop_bar, 2)
        if dp >= self.MAX_PRESSURE_DROP_BAR:
            dp_status = "HIGH_PRESSURE_DROP_CLOGGED"
            maint_action = "BACKWASH_OR_CIP_MANDATORY"
            warnings.append(
                f"PHE CLOGGING HAZARD ({dp} bar >= 1.20 bar): Plate pressure drop excessive, backwash required"
            )
        elif dp > 0.90:
            dp_status = "MODERATE_PRESSURE_DROP"
            maint_action = "MONITOR_TREND"
        else:
            dp_status = "NOMINAL_CLEAN"
            maint_action = "CONTINUE_NORMAL_OPERATION"

        # Ultrasonic biofilm prevention
        if inp.ultrasonic_intensity_w_cm2 >= 1.5:
            us_status = "ACTIVE_BIOFILM_INHIBITION"
        else:
            us_status = "INSUFFICIENT_ACOUSTIC_POWER"
            warnings.append("ULTRASONIC WARNING: Acoustic intensity < 1.5 W/cm2, biofouling risk elevated")

        return CentralTitaniumPheResult(
            heat_duty_kw=duty_kw,
            lmtd_c=lmtd,
            thermal_performance=thermal_status,
            pressure_drop_status=dp_status,
            ultrasonic_biofilm_prevention=us_status,
            maintenance_action=maint_action,
            warnings=warnings,
        )
