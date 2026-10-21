from dataclasses import dataclass
from enum import Enum


class PtoShaftGeneratorState(str, Enum):
    PTO_GRID_PARALLEL_NOMINAL = "PTO_GRID_PARALLEL_NOMINAL"
    AFE_HARMONIC_THD_HIGH_WARN = "AFE_HARMONIC_THD_HIGH_WARN"
    RPM_WINDOW_DG_AUTO_START_TRANSFER = "RPM_WINDOW_DG_AUTO_START_TRANSFER"
    CRASH_STOP_OR_DC_LINK_FAULT_ACB_TRIP = "CRASH_STOP_OR_DC_LINK_FAULT_ACB_TRIP"


@dataclass(frozen=True)
class PtoShaftGeneratorTelemetry:
    shaft_speed_mcr_pct: float
    dc_link_voltage_v: float
    igbt_heatsink_temp_c: float = 58.0
    voltage_thd_pct: float = 2.4
    me_crash_stop_active: bool = False


@dataclass(frozen=True)
class PtoShaftGeneratorAssessment:
    state: PtoShaftGeneratorState
    pto_acb_fast_trip_open: bool
    standby_diesel_gen_start_transfer_cmd: bool
    excitation_crowbar_deenergize: bool
    interlock_code: str


class PtoShaftGeneratorConverterEngine:
    """IACS UR E11 & UR M53 PTO Shaft Generator & AFE Frequency Converter Interlock."""

    @classmethod
    def evaluate(cls, t: PtoShaftGeneratorTelemetry) -> PtoShaftGeneratorAssessment:
        if (
            t.me_crash_stop_active
            or t.dc_link_voltage_v >= 1150.0
            or t.igbt_heatsink_temp_c >= 85.0
        ):
            return PtoShaftGeneratorAssessment(
                PtoShaftGeneratorState.CRASH_STOP_OR_DC_LINK_FAULT_ACB_TRIP,
                True,
                True,
                True,
                "UR_E11_PTO_CRASH_STOP_OR_INVERTER_FAULT_ACB_TRIP",
            )
        if t.shaft_speed_mcr_pct < 65.0 or t.shaft_speed_mcr_pct > 104.0:
            return PtoShaftGeneratorAssessment(
                PtoShaftGeneratorState.RPM_WINDOW_DG_AUTO_START_TRANSFER,
                False,
                True,
                False,
                "UR_M53_PTO_SHAFT_SPEED_OUT_OF_WINDOW_DG_TRANSFER",
            )
        if t.voltage_thd_pct >= 5.0:
            return PtoShaftGeneratorAssessment(
                PtoShaftGeneratorState.AFE_HARMONIC_THD_HIGH_WARN,
                False,
                False,
                False,
                "UR_E11_AFE_CONVERTER_HARMONIC_DISTORTION_HIGH_WARN",
            )
        return PtoShaftGeneratorAssessment(
            PtoShaftGeneratorState.PTO_GRID_PARALLEL_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
