"""Phase 493: Exhaust Gas Scrubbing Washwater Demister & SOx Quench Loop.

Compliant with MARPOL Annex VI Reg 14 & IMO Res MEPC.340(77).
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class ScrubberStatus(str, Enum):
    NORMAL = "normal"
    QUENCH_HIGH_TEMP_BYPASS = "quench_high_temp_bypass"
    DEMISTER_WASH_TRIGGERED = "demister_wash_triggered"
    PH_NEUTRALIZATION_REQUIRED = "ph_neutralization_required"
    TURBIDITY_LIMIT_EXCEEDED = "turbidity_limit_exceeded"


@dataclass(frozen=True)
class ScrubberTelemetry:
    quench_inlet_temp_c: float
    demister_diff_pressure_kpa: float
    washwater_ph: float
    discharge_turbidity_fnu: float
    demister_wash_active: bool = False


@dataclass(frozen=True)
class ScrubberAssessment:
    status: ScrubberStatus
    scrubber_bypass_command: bool
    demister_wash_command: bool
    caustic_dosing_command: bool
    emission_compliant: bool
    remarks: str


class ExhaustScrubberWashwaterDemisterEngine:
    """MARPOL Annex VI SOx Scrubber Safety & Washwater Discharge Engine."""

    MAX_QUENCH_TEMP_C = 250.0
    MAX_DEMISTER_DP_KPA = 2.5
    MIN_WASHWATER_PH = 6.5
    MAX_TURBIDITY_FNU = 25.0

    @classmethod
    def evaluate(cls, telem: ScrubberTelemetry) -> ScrubberAssessment:
        if telem.quench_inlet_temp_c >= cls.MAX_QUENCH_TEMP_C:
            return ScrubberAssessment(
                ScrubberStatus.QUENCH_HIGH_TEMP_BYPASS,
                True, False, False, False,
                f"Quench gas temp {telem.quench_inlet_temp_c:.1f} °C >= {cls.MAX_QUENCH_TEMP_C} °C; opening bypass",
            )
        if telem.discharge_turbidity_fnu > cls.MAX_TURBIDITY_FNU:
            return ScrubberAssessment(
                ScrubberStatus.TURBIDITY_LIMIT_EXCEEDED,
                False, False, False, False,
                f"Discharge turbidity {telem.discharge_turbidity_fnu:.1f} FNU > {cls.MAX_TURBIDITY_FNU} FNU",
            )
        if telem.demister_diff_pressure_kpa >= cls.MAX_DEMISTER_DP_KPA:
            return ScrubberAssessment(
                ScrubberStatus.DEMISTER_WASH_TRIGGERED,
                False, True, telem.washwater_ph < cls.MIN_WASHWATER_PH, True,
                f"Demister dP {telem.demister_diff_pressure_kpa:.2f} kPa >= {cls.MAX_DEMISTER_DP_KPA} kPa; washing soot",
            )
        if telem.washwater_ph < cls.MIN_WASHWATER_PH:
            return ScrubberAssessment(
                ScrubberStatus.PH_NEUTRALIZATION_REQUIRED,
                False, False, True, True,
                f"Washwater pH {telem.washwater_ph:.2f} < {cls.MIN_WASHWATER_PH}; dosing caustic soda",
            )
        return ScrubberAssessment(
            ScrubberStatus.NORMAL,
            False, False, False, True,
            f"Scrubber normal. pH: {telem.washwater_ph:.2f}, dP: {telem.demister_diff_pressure_kpa:.2f} kPa",
        )
