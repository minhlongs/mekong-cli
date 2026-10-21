from dataclasses import dataclass
from enum import Enum


class ScrUreaDosingState(str, Enum):
    TIER_III_SCR_DOSING_ACTIVE = "TIER_III_SCR_DOSING_ACTIVE"
    CATALYST_SOOT_FOULING_PURGE_WARN = "CATALYST_SOOT_FOULING_PURGE_WARN"
    HIGH_AMMONIA_SLIP_DOSING_TRIM_ALARM = "HIGH_AMMONIA_SLIP_DOSING_TRIM_ALARM"
    LOW_TEMP_BISULFATE_FOULING_DOSING_CUTOFF = "LOW_TEMP_BISULFATE_FOULING_DOSING_CUTOFF"
    CATALYST_THERMAL_SINTERING_BYPASS_TRIP = "CATALYST_THERMAL_SINTERING_BYPASS_TRIP"


@dataclass(frozen=True)
class ScrUreaDosingTelemetry:
    catalyst_bed_temp_c: float
    fuel_sulfur_pct: float
    ammonia_slip_ppm: float
    catalyst_dp_kpa: float = 1.1


@dataclass(frozen=True)
class ScrUreaDosingAssessment:
    state: ScrUreaDosingState
    urea_dosing_valve_open: bool
    reactor_bypass_valve_open: bool
    compressed_air_sootblow_purge_cmd: bool
    interlock_code: str


class ScrUreaAmmoniaSlipEngine:
    """MARPOL Annex VI Reg 13 & MEPC.291(71) SCR Urea Dosing & Ammonia Slip Interlock."""

    @classmethod
    def evaluate(cls, t: ScrUreaDosingTelemetry) -> ScrUreaDosingAssessment:
        if t.catalyst_bed_temp_c > 450.0:
            return ScrUreaDosingAssessment(
                ScrUreaDosingState.CATALYST_THERMAL_SINTERING_BYPASS_TRIP,
                False,
                True,
                True,
                "MARPOL_REG13_SCR_THERMAL_SINTERING_BYPASS_TRIP",
            )
        min_temp_c = 310.0 if t.fuel_sulfur_pct > 0.10 else 270.0
        if t.catalyst_bed_temp_c < min_temp_c:
            return ScrUreaDosingAssessment(
                ScrUreaDosingState.LOW_TEMP_BISULFATE_FOULING_DOSING_CUTOFF,
                False,
                True,
                True,
                "MEPC291_SCR_ABS_DEWPOINT_UREA_CUTOFF",
            )
        if t.ammonia_slip_ppm >= 10.0:
            return ScrUreaDosingAssessment(
                ScrUreaDosingState.HIGH_AMMONIA_SLIP_DOSING_TRIM_ALARM,
                True,
                False,
                False,
                "MEPC291_SCR_NH3_SLIP_EXCEEDANCE_ALARM",
            )
        if t.catalyst_dp_kpa >= 2.5:
            return ScrUreaDosingAssessment(
                ScrUreaDosingState.CATALYST_SOOT_FOULING_PURGE_WARN,
                True,
                False,
                True,
                "SCR_CATALYST_HIGH_DP_SOOTBLOW_WARN",
            )
        return ScrUreaDosingAssessment(
            ScrUreaDosingState.TIER_III_SCR_DOSING_ACTIVE,
            True,
            False,
            False,
            "NONE",
        )
