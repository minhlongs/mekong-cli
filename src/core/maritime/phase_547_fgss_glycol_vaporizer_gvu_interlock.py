from dataclasses import dataclass
from enum import Enum


class FgssGlycolGvuState(str, Enum):
    FGSS_GAS_SUPPLY_NOMINAL = "FGSS_GAS_SUPPLY_NOMINAL"
    GLYCOL_HEATING_MEDIUM_LOW_TEMP_WARN = "GLYCOL_HEATING_MEDIUM_LOW_TEMP_WARN"
    GVU_ENCLOSURE_VENT_OR_LEAK_PRE_ALARM = "GVU_ENCLOSURE_VENT_OR_LEAK_PRE_ALARM"
    CRYOGENIC_CARRYOVER_OR_GVU_GAS_MGFV_TRIP = "CRYOGENIC_CARRYOVER_OR_GVU_GAS_MGFV_TRIP"


@dataclass(frozen=True)
class FgssGlycolGvuTelemetry:
    vaporizer_gas_out_temp_c: float
    gvu_enclosure_lel_pct: float
    gvu_ventilation_ach: float
    glycol_supply_temp_c: float = 45.0


@dataclass(frozen=True)
class FgssGlycolGvuAssessment:
    state: FgssGlycolGvuState
    master_gas_fuel_valve_close_cmd: bool
    nitrogen_dbb_purge_open_cmd: bool
    gvu_extraction_fan_boost_cmd: bool
    interlock_code: str


class FgssGlycolVaporizerGvuEngine:
    """IMO IGF Code Ch. 9 & IACS UR M78 LNG HP FGSS Glycol Vaporizer & GVU Interlock."""

    @classmethod
    def evaluate(cls, t: FgssGlycolGvuTelemetry) -> FgssGlycolGvuAssessment:
        if t.vaporizer_gas_out_temp_c < 0.0 or t.gvu_enclosure_lel_pct >= 40.0:
            return FgssGlycolGvuAssessment(
                FgssGlycolGvuState.CRYOGENIC_CARRYOVER_OR_GVU_GAS_MGFV_TRIP,
                True,
                True,
                True,
                "IGF_CH9_FGSS_LIQUID_CARRYOVER_OR_GVU_GAS_MGFV_TRIP",
            )
        if t.gvu_enclosure_lel_pct >= 20.0 or t.gvu_ventilation_ach < 30.0:
            return FgssGlycolGvuAssessment(
                FgssGlycolGvuState.GVU_ENCLOSURE_VENT_OR_LEAK_PRE_ALARM,
                False,
                False,
                True,
                "UR_M78_GVU_ENCLOSURE_LEL_OR_LOW_ACH_BOOST",
            )
        if t.glycol_supply_temp_c < 25.0:
            return FgssGlycolGvuAssessment(
                FgssGlycolGvuState.GLYCOL_HEATING_MEDIUM_LOW_TEMP_WARN,
                False,
                False,
                False,
                "IGF_FGSS_GLYCOL_WATER_LOW_TEMP_WARN",
            )
        return FgssGlycolGvuAssessment(
            FgssGlycolGvuState.FGSS_GAS_SUPPLY_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
