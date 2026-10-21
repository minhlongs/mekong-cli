from dataclasses import dataclass
from enum import Enum


class EnclosedSpaceEntryState(str, Enum):
    ENTRY_PERMIT_SAFE_AUTHORIZED = "ENTRY_PERMIT_SAFE_AUTHORIZED"
    INSUFFICIENT_VENTILATION_PURGE_HOLD = "INSUFFICIENT_VENTILATION_PURGE_HOLD"
    OXYGEN_DEFICIENCY_OR_ENRICHMENT_LOCKOUT = "OXYGEN_DEFICIENCY_OR_ENRICHMENT_LOCKOUT"
    TOXIC_OR_FLAMMABLE_GAS_HAZARD_LOCKOUT = "TOXIC_OR_FLAMMABLE_GAS_HAZARD_LOCKOUT"


@dataclass(frozen=True)
class EnclosedSpaceEntryTelemetry:
    oxygen_vol_pct: float
    flammable_lel_pct: float
    carbon_monoxide_ppm: float
    hydrogen_sulfide_ppm: float
    ventilation_purge_minutes: float
    ventilation_ach: float


@dataclass(frozen=True)
class EnclosedSpaceEntryAssessment:
    state: EnclosedSpaceEntryState
    entry_hatch_interlock_released: bool
    rescue_scba_alarm_active: bool
    forced_ventilation_boost: bool
    interlock_code: str


class EnclosedSpaceEntryGasInterlockEngine:
    """SOLAS XI-1 Reg 7 & IMO Res. A.1050(27) Enclosed Space Entry Supervision."""

    @classmethod
    def evaluate(cls, t: EnclosedSpaceEntryTelemetry) -> EnclosedSpaceEntryAssessment:
        if t.flammable_lel_pct >= 1.0 or t.carbon_monoxide_ppm >= 20.0 or t.hydrogen_sulfide_ppm >= 5.0:
            return EnclosedSpaceEntryAssessment(
                EnclosedSpaceEntryState.TOXIC_OR_FLAMMABLE_GAS_HAZARD_LOCKOUT,
                False,
                True,
                True,
                "SOLAS_XI1_REG7_TOXIC_FLAMMABLE_ENTRY_PROHIBITED",
            )
        if not (20.8 <= t.oxygen_vol_pct <= 21.5):
            return EnclosedSpaceEntryAssessment(
                EnclosedSpaceEntryState.OXYGEN_DEFICIENCY_OR_ENRICHMENT_LOCKOUT,
                False,
                True,
                True,
                "IMO_A1050_27_OXYGEN_OUT_OF_SAFE_BOUNDS",
            )
        if t.ventilation_purge_minutes < 30.0 or t.ventilation_ach < 10.0:
            return EnclosedSpaceEntryAssessment(
                EnclosedSpaceEntryState.INSUFFICIENT_VENTILATION_PURGE_HOLD,
                False,
                False,
                True,
                "IMO_A1050_27_PRE_ENTRY_PURGE_INCOMPLETE",
            )
        return EnclosedSpaceEntryAssessment(
            EnclosedSpaceEntryState.ENTRY_PERMIT_SAFE_AUTHORIZED,
            True,
            False,
            False,
            "NONE",
        )
