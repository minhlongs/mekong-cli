"""Central Seawater Cooling & MGPS Bio-Fouling Prevention Engine.

Implements Central Cooling Water System (CCWS) Plate Heat Exchanger LMTD,
Seawater Scoop Injection energy saving, and MGPS electrolytic Cu/Al dosing.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class CentralCoolingInput:
    vessel_id: str
    heat_duty_kw: float
    freshwater_in_temp_c: float
    freshwater_out_temp_c: float
    seawater_in_temp_c: float
    vessel_speed_knots: float = 14.0
    seawater_flow_m3_h: float = 850.0
    is_scoop_system_fitted: bool = True
    mgps_copper_current_amps: float = 2.5
    mgps_aluminum_current_amps: float = 1.8


@dataclass
class CentralCoolingResult:
    vessel_id: str
    seawater_out_temp_c: float
    lmtd_celsius: float
    is_scoop_active: bool
    pump_power_saved_kw: float
    cu_ion_concentration_ug_l: float
    is_mgps_effective: bool
    status: str
    advisories: List[str] = field(default_factory=list)


class CentralCoolingEngine:
    """Evaluates central marine cooling efficiency and MGPS bio-fouling protection."""

    @staticmethod
    def evaluate(inp: CentralCoolingInput) -> CentralCoolingResult:
        # Seawater heat absorption: Q = m * Cp * delta_T
        # Seawater Cp = ~3.99 kJ/(kg*K), density = 1025 kg/m3 -> ~4090 kJ/(m3*K) = 1.136 kWh/(m3*K)
        # delta_T_sw = Q_kw / (flow_m3_h * 1.136 kW/(m3*K))
        sw_delta_t = inp.heat_duty_kw / max(10.0, inp.seawater_flow_m3_h * 1.136)
        sw_out_temp = round(inp.seawater_in_temp_c + sw_delta_t, 2)

        # Logarithmic Mean Temperature Difference (LMTD) for counter-flow
        dt1 = inp.freshwater_in_temp_c - sw_out_temp
        dt2 = inp.freshwater_out_temp_c - inp.seawater_in_temp_c

        if dt1 <= 0.0 or dt2 <= 0.0:
            lmtd = 1.0  # Abnormal temperature crossover
        elif abs(dt1 - dt2) < 0.1:
            lmtd = round(dt1, 2)
        else:
            lmtd = round((dt1 - dt2) / math.log(dt1 / dt2), 2)

        # Seawater scoop energy saving: active when speed >= 12.0 knots
        is_scoop_active = inp.is_scoop_fitted_and_running(inp.vessel_speed_knots) if hasattr(inp, 'is_scoop_fitted_and_running') else (inp.is_scoop_system_fitted and inp.vessel_speed_knots >= 12.0)
        power_saved_kw = round(45.0 * (inp.vessel_speed_knots / 14.0)**2, 1) if is_scoop_active else 0.0

        # MGPS electrolytic copper concentration:
        # Faraday's law: Cu mass (mg/h) = (I * t * M) / (z * F) = (I * 3600 * 63.55) / (2 * 96485) ~= 1.185 * I (g/h)
        # Concentration (ug/L = mg/m3) = (I * 1185) / flow_m3_h
        cu_conc_ug_l = round((inp.mgps_copper_current_amps * 1185.0) / max(10.0, inp.seawater_flow_m3_h), 2)

        # Standard bio-fouling prevention target: 2.0 to 5.0 ug/L
        is_mgps_ok = 2.0 <= cu_conc_ug_l <= 10.0

        advisories: List[str] = [
            f"Seawater cooling discharge: {sw_out_temp}°C (inlet {inp.seawater_in_temp_c}°C, LMTD {lmtd}°C).",
            f"MGPS Cu ion concentration: {cu_conc_ug_l} ug/L.",
        ]

        if is_scoop_active:
            advisories.append(f"SEAWATER SCOOP ACTIVE: Saving {power_saved_kw} kW of main seawater pump power.")
        else:
            advisories.append("SCOOP INACTIVE: Main seawater circulating pumps running at standard load.")

        if not is_mgps_ok:
            if cu_conc_ug_l < 2.0:
                advisories.append("MGPS DOSING DEFICIENT: High risk of barnacle / mussel growth in sea chest.")
            else:
                advisories.append("MGPS OVER-DOSING: Exceeds environmental copper discharge limits.")

        if sw_out_temp > 45.0:
            advisories.append("THERMAL DISCHARGE ALERT: Seawater cooling outlet exceeds 45°C limit.")

        status = "OPTIMAL" if is_mgps_ok and sw_out_temp <= 45.0 else "SUB_OPTIMAL"

        return CentralCoolingResult(
            vessel_id=inp.vessel_id,
            seawater_out_temp_c=sw_out_temp,
            lmtd_celsius=lmtd,
            is_scoop_active=is_scoop_active,
            pump_power_saved_kw=power_saved_kw,
            cu_ion_concentration_ug_l=cu_conc_ug_l,
            is_mgps_effective=is_mgps_ok,
            status=status,
            advisories=advisories,
        )
