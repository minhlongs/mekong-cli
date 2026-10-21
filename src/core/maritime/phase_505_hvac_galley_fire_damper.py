"""Phase 505: Accommodation HVAC Galley Exhaust Fire Damper & Smoke Interlock.
Complies with SOLAS II-2 Reg 9.7.5 and ISO 7547 Marine HVAC Safety Rules.
Strictly < 90 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class HvacDamperMode(str, Enum):
    NORMAL_VENTILATION = "NORMAL_VENTILATION"
    SMOKE_PURGE_FRESH_AIR = "SMOKE_PURGE_FRESH_AIR"
    GALLEY_DUCT_PRE_ALARM = "GALLEY_DUCT_PRE_ALARM"
    FIRE_DAMPER_TRIPPED_CLOSED = "FIRE_DAMPER_TRIPPED_CLOSED"


@dataclass(frozen=True)
class HvacGalleyTelemetry:
    galley_duct_temp_c: float
    recirc_smoke_detected: bool
    manual_fire_pull_activated: bool = False


@dataclass(frozen=True)
class HvacGalleyAssessment:
    damper_mode: HvacDamperMode
    fire_damper_closed: bool
    exhaust_fan_running: bool
    alarm_active: bool
    alarm_code: str


class HvacGalleyFireDamperEngine:
    """Evaluates galley grease duct thermal trip (>= 74 C) and accommodation smoke purge."""

    PRE_ALARM_TEMP_C: float = 68.0
    FUSIBLE_TRIP_TEMP_C: float = 74.0

    @classmethod
    def evaluate(cls, t: HvacGalleyTelemetry) -> HvacGalleyAssessment:
        if t.manual_fire_pull_activated or t.galley_duct_temp_c >= cls.FUSIBLE_TRIP_TEMP_C:
            return HvacGalleyAssessment(
                HvacDamperMode.FIRE_DAMPER_TRIPPED_CLOSED,
                True,
                False,
                True,
                "SOLAS_GALLEY_DUCT_FIRE_DAMPER_TRIP",
            )
        if t.recirc_smoke_detected:
            return HvacGalleyAssessment(
                HvacDamperMode.SMOKE_PURGE_FRESH_AIR,
                False,
                True,
                True,
                "HVAC_SMOKE_DETECTED_RECIRC_ISOLATED",
            )
        if t.galley_duct_temp_c >= cls.PRE_ALARM_TEMP_C:
            return HvacGalleyAssessment(
                HvacDamperMode.GALLEY_DUCT_PRE_ALARM,
                False,
                True,
                True,
                "GALLEY_GREASE_DUCT_HIGH_TEMP_WARNING",
            )
        return HvacGalleyAssessment(
            HvacDamperMode.NORMAL_VENTILATION,
            False,
            True,
            False,
            "NONE",
        )
