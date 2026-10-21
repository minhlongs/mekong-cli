"""Phase 529: Cargo Hold Fixed Smoke Detection Sample Extraction & Three-Way CO2 Valve Supervision.
Complies with SOLAS II-2 Reg 7.2 & IMO FSS Code Chapter 10.
Strictly < 85 LOC, zero mocks, pure deterministic statutory physics.
"""
from dataclasses import dataclass
from enum import Enum


class CargoSmokeExtractionState(str, Enum):
    NORMAL_SAMPLING_PATROL = "NORMAL_SAMPLING_PATROL"
    SMOKE_PRE_ALARM_OBSCURATION = "SMOKE_PRE_ALARM_OBSCURATION"
    CONFIRMED_HOLD_FIRE_ALARM = "CONFIRMED_HOLD_FIRE_ALARM"
    EXTRACTION_VACUUM_LOSS_STANDBY_CUTIN = "EXTRACTION_VACUUM_LOSS_STANDBY_CUTIN"
    THREE_WAY_VALVE_ALIGNMENT_FAULT = "THREE_WAY_VALVE_ALIGNMENT_FAULT"


@dataclass(frozen=True)
class CargoSmokeExtractionTelemetry:
    fan_suction_dp_pa: float
    smoke_obscuration_pct_per_m: float = 0.2
    three_way_valve_aligned_to_panel: bool = True
    co2_discharge_in_progress: bool = False


@dataclass(frozen=True)
class CargoSmokeExtractionAssessment:
    extraction_state: CargoSmokeExtractionState
    standby_fan_cutin_cmd: bool
    bridge_fire_bell_active: bool
    alarm_active: bool
    alarm_code: str


class CargoSmokeExtractionFanSupervisionEngine:
    @classmethod
    def evaluate(cls, t: CargoSmokeExtractionTelemetry) -> CargoSmokeExtractionAssessment:
        if t.smoke_obscuration_pct_per_m >= 4.0:
            return CargoSmokeExtractionAssessment(
                CargoSmokeExtractionState.CONFIRMED_HOLD_FIRE_ALARM,
                False, True, True, "FSS_CH10_CARGO_HOLD_SMOKE_FIRE_ALARM",
            )
        if not t.three_way_valve_aligned_to_panel and not t.co2_discharge_in_progress:
            return CargoSmokeExtractionAssessment(
                CargoSmokeExtractionState.THREE_WAY_VALVE_ALIGNMENT_FAULT,
                False, False, True, "FSS_CH10_3WAY_CO2_VALVE_MISALIGNED",
            )
        if t.fan_suction_dp_pa < 80.0:
            return CargoSmokeExtractionAssessment(
                CargoSmokeExtractionState.EXTRACTION_VACUUM_LOSS_STANDBY_CUTIN,
                True, False, True, "FSS_CH10_EXTRACTION_FAN_VACUUM_LOSS",
            )
        if t.smoke_obscuration_pct_per_m >= 2.0:
            return CargoSmokeExtractionAssessment(
                CargoSmokeExtractionState.SMOKE_PRE_ALARM_OBSCURATION,
                False, False, True, "SOLAS_II2_R7_SMOKE_PRE_ALARM",
            )
        return CargoSmokeExtractionAssessment(
            CargoSmokeExtractionState.NORMAL_SAMPLING_PATROL,
            False, False, False, "NONE",
        )
