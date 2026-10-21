"""Phase 489: Central Cooling System 3-Way Thermostatic Mixing Valve & SW Head Engine.

Complies with IACS UR M14 standards. Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class CentralCoolingStatus(Enum):
    NORMAL = "normal"
    STANDBY_SW_PUMP_CUT_IN = "standby_sw_pump_cut_in"
    SW_PUMP_LOW_PRESSURE_WARNING = "sw_pump_low_pressure_warning"
    LT_TEMP_OUT_OF_SPEC = "lt_temp_out_of_spec"
    HT_OVERHEAT_FULL_COOLING = "ht_overheat_full_cooling"


@dataclass(frozen=True)
class CentralCoolingTelemetry:
    lt_freshwater_temp_c: float
    ht_jacket_water_temp_c: float
    seawater_pump_diff_pressure_bar: float
    standby_sw_pump_available: bool = True
    ht_target_setpoint_c: float = 85.0


@dataclass(frozen=True)
class CentralCoolingAssessment:
    status: CentralCoolingStatus
    ht_bypass_valve_pct: float
    standby_sw_pump_command: bool
    lt_temp_deviation_c: float
    cooling_loop_balanced: bool
    remarks: str


class CentralCooling3WayValveEngine:
    LT_TARGET_TEMP_C = 36.0
    LT_TOLERANCE_C = 1.5
    SW_HEAD_NOMINAL_BAR = 1.5
    SW_HEAD_CUT_IN_BAR = 1.0
    HT_BAND_HALF_SPAN_C = 5.0

    @classmethod
    def calculate_ht_bypass_pct(cls, ht_temp: float, setpoint: float) -> float:
        min_temp = setpoint - cls.HT_BAND_HALF_SPAN_C
        max_temp = setpoint + cls.HT_BAND_HALF_SPAN_C
        if ht_temp <= min_temp:
            return 100.0
        if ht_temp >= max_temp:
            return 0.0
        return round(100.0 - ((ht_temp - min_temp) / (2.0 * cls.HT_BAND_HALF_SPAN_C)) * 100.0, 2)

    @classmethod
    def evaluate(cls, telem: CentralCoolingTelemetry) -> CentralCoolingAssessment:
        lt_dev = round(telem.lt_freshwater_temp_c - cls.LT_TARGET_TEMP_C, 2)
        bypass = cls.calculate_ht_bypass_pct(telem.ht_jacket_water_temp_c, telem.ht_target_setpoint_c)
        lt_ok = abs(lt_dev) <= cls.LT_TOLERANCE_C
        sw_cmd = telem.seawater_pump_diff_pressure_bar < cls.SW_HEAD_CUT_IN_BAR and telem.standby_sw_pump_available

        if telem.seawater_pump_diff_pressure_bar < cls.SW_HEAD_CUT_IN_BAR:
            return CentralCoolingAssessment(
                CentralCoolingStatus.STANDBY_SW_PUMP_CUT_IN, bypass, sw_cmd, lt_dev, False,
                f"SW head {telem.seawater_pump_diff_pressure_bar:.2f} bar < 1.0 bar. Standby SW pump cut-in.",
            )
        if not lt_ok:
            return CentralCoolingAssessment(
                CentralCoolingStatus.LT_TEMP_OUT_OF_SPEC, bypass, False, lt_dev, False,
                f"LT temp {telem.lt_freshwater_temp_c:.1f}C outside 36.0 +/- 1.5C band (dev: {lt_dev:+.1f}C).",
            )
        if bypass <= 0.0 and telem.ht_jacket_water_temp_c >= telem.ht_target_setpoint_c + cls.HT_BAND_HALF_SPAN_C:
            return CentralCoolingAssessment(
                CentralCoolingStatus.HT_OVERHEAT_FULL_COOLING, 0.0, False, lt_dev, True,
                f"HT temp {telem.ht_jacket_water_temp_c:.1f}C >= 90C. 3-way valve 0% bypass (100% cooling).",
            )
        if telem.seawater_pump_diff_pressure_bar < cls.SW_HEAD_NOMINAL_BAR:
            return CentralCoolingAssessment(
                CentralCoolingStatus.SW_PUMP_LOW_PRESSURE_WARNING, bypass, False, lt_dev, True,
                f"SW head {telem.seawater_pump_diff_pressure_bar:.2f} bar < 1.5 bar nominal. Monitor strainer.",
            )
        return CentralCoolingAssessment(
            CentralCoolingStatus.NORMAL, bypass, False, lt_dev, True,
            "Central cooling LT loop and HT 3-way valve balanced under IACS UR M14 standards.",
        )
