"""Phase 530: Free-Fall Lifeboat Hydraulic Release Hook, Ramp Securing Pin & Launch Interlock.
Complies with SOLAS III Reg 16 & Reg 20 and IMO LSA Code Chapter IV (4.7).
Strictly < 85 LOC, zero mocks, pure deterministic statutory physics.
"""
from dataclasses import dataclass
from enum import Enum


class FreefallLifeboatState(str, Enum):
    SEA_READINESS_ARMED = "SEA_READINESS_ARMED"
    HARBOR_PIN_ENGAGED_AT_SEA_ALARM = "HARBOR_PIN_ENGAGED_AT_SEA_ALARM"
    HYDRAULIC_PRESSURE_LOW_SECONDARY_PUMP = "HYDRAULIC_PRESSURE_LOW_SECONDARY_PUMP"
    HATCH_OR_HARNESS_UNSECURED_LOCK = "HATCH_OR_HARNESS_UNSECURED_LOCK"


@dataclass(frozen=True)
class FreefallLifeboatTelemetry:
    hydraulic_release_bar: float
    harbor_securing_pin_removed: bool = True
    vessel_speed_kn: float = 12.0
    aft_boarding_hatch_dogged: bool = True
    all_crew_harnesses_locked: bool = True


@dataclass(frozen=True)
class FreefallLifeboatAssessment:
    lifeboat_state: FreefallLifeboatState
    primary_freefall_release_permitted: bool
    engage_emergency_hand_pump: bool
    alarm_active: bool
    alarm_code: str


class FreefallLifeboatReleaseInterlockEngine:
    @classmethod
    def evaluate(cls, t: FreefallLifeboatTelemetry) -> FreefallLifeboatAssessment:
        if not t.harbor_securing_pin_removed and t.vessel_speed_kn > 1.0:
            return FreefallLifeboatAssessment(
                FreefallLifeboatState.HARBOR_PIN_ENGAGED_AT_SEA_ALARM,
                False, False, True, "SOLAS_III_R20_HARBOR_PIN_LOCKED_AT_SEA",
            )
        if not t.aft_boarding_hatch_dogged or not t.all_crew_harnesses_locked:
            return FreefallLifeboatAssessment(
                FreefallLifeboatState.HATCH_OR_HARNESS_UNSECURED_LOCK,
                False, False, True, "LSA_IV_47_HATCH_HARNESS_INTERLOCK",
            )
        if t.hydraulic_release_bar < 150.0:
            return FreefallLifeboatAssessment(
                FreefallLifeboatState.HYDRAULIC_PRESSURE_LOW_SECONDARY_PUMP,
                False, True, True, "LSA_IV_47_HYDRAULIC_RELEASE_LOW_BAR",
            )
        return FreefallLifeboatAssessment(
            FreefallLifeboatState.SEA_READINESS_ARMED,
            t.harbor_securing_pin_removed, False, False, "NONE",
        )
