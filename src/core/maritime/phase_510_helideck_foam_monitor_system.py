"""Phase 510: Helideck Foam Monitor & Pop-Up Nozzle Fire System.
Complies with SOLAS II-2 Reg 18 and UK CAA CAP 437 / ICAO Annex 14 Standards.
Strictly < 85 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class HelideckFoamStatus(str, Enum):
    STANDBY_READY = "STANDBY_READY"
    DISCHARGING_COMPLIANT_FOAM = "DISCHARGING_COMPLIANT_FOAM"
    PROPORTIONER_RATIO_FAULT = "PROPORTIONER_RATIO_FAULT"
    LOW_NOZZLE_PRESSURE_ALARM = "LOW_NOZZLE_PRESSURE_ALARM"
    LOW_FOAM_TANK_RESERVE_ALARM = "LOW_FOAM_TANK_RESERVE_ALARM"


@dataclass(frozen=True)
class HelideckFoamTelemetry:
    release_activated: bool
    nozzle_manifold_bar: float
    afff_induction_ratio_pct: float
    foam_tank_level_pct: float = 95.0


@dataclass(frozen=True)
class HelideckFoamAssessment:
    foam_status: HelideckFoamStatus
    pop_up_nozzles_deployed: bool
    cap437_compliant: bool
    alarm_active: bool
    alarm_code: str


class HelideckFoamMonitorSystemEngine:
    """Evaluates helideck pop-up nozzle pressure (>= 7.0 bar) and 3% AFFF proportioning."""

    MIN_NOZZLE_BAR: float = 7.0
    MIN_RATIO_PCT: float = 2.8
    MAX_RATIO_PCT: float = 3.5
    MIN_TANK_RESERVE_PCT: float = 85.0

    @classmethod
    def evaluate(cls, t: HelideckFoamTelemetry) -> HelideckFoamAssessment:
        if t.foam_tank_level_pct < cls.MIN_TANK_RESERVE_PCT:
            return HelideckFoamAssessment(
                HelideckFoamStatus.LOW_FOAM_TANK_RESERVE_ALARM,
                t.release_activated,
                False,
                True,
                "HELIDECK_AFFF_TANK_BELOW_5MIN_RESERVE",
            )
        if not t.release_activated:
            return HelideckFoamAssessment(
                HelideckFoamStatus.STANDBY_READY, False, True, False, "NONE"
            )
        if t.nozzle_manifold_bar < cls.MIN_NOZZLE_BAR:
            return HelideckFoamAssessment(
                HelideckFoamStatus.LOW_NOZZLE_PRESSURE_ALARM,
                True,
                False,
                True,
                "HELIDECK_POPUP_NOZZLE_LOW_PRESSURE",
            )
        if not (cls.MIN_RATIO_PCT <= t.afff_induction_ratio_pct <= cls.MAX_RATIO_PCT):
            return HelideckFoamAssessment(
                HelideckFoamStatus.PROPORTIONER_RATIO_FAULT,
                True,
                False,
                True,
                "HELIDECK_AFFF_PROPORTIONER_OUT_OF_3PCT_BAND",
            )
        return HelideckFoamAssessment(
            HelideckFoamStatus.DISCHARGING_COMPLIANT_FOAM,
            True,
            True,
            False,
            "NONE",
        )
