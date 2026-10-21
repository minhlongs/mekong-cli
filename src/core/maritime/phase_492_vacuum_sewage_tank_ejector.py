"""Phase 492: Vacuum Sewage Collecting Tank & Ejector Discharge Control.

Compliant with MARPOL Annex IV.
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class VacuumSewageStatus(str, Enum):
    NORMAL_HOLDING = "normal_holding"
    EJECTOR_VACUUM_CREATION = "ejector_vacuum_creation"
    VACUUM_LOSS_ALARM = "vacuum_loss_alarm"
    MACERATOR_DISCHARGE_ACTIVE = "macerator_discharge_active"
    HIGH_HIGH_LEVEL_LOCKOUT = "high_high_level_lockout"


@dataclass(frozen=True)
class VacuumSewageTelemetry:
    system_vacuum_bar: float  # Gauge pressure (e.g. -0.55 bar)
    tank_level_pct: float
    ejector_pump_running: bool
    discharge_macerator_running: bool = False


@dataclass(frozen=True)
class VacuumSewageAssessment:
    status: VacuumSewageStatus
    ejector_command: bool
    discharge_command: bool
    toilet_inlet_isolated: bool
    system_ready: bool
    remarks: str


class VacuumSewageTankEjectorEngine:
    """MARPOL Annex IV Vacuum Sewage Holding & Discharge Safety Engine."""

    VACUUM_CUT_IN_BAR = -0.45
    VACUUM_CUT_OUT_BAR = -0.65
    VACUUM_LOSS_ALARM_BAR = -0.30
    TANK_MACERATOR_CUT_IN_PCT = 80.0
    TANK_HIGH_HIGH_LOCKOUT_PCT = 95.0

    @classmethod
    def evaluate(cls, telem: VacuumSewageTelemetry) -> VacuumSewageAssessment:
        if telem.tank_level_pct >= cls.TANK_HIGH_HIGH_LOCKOUT_PCT:
            return VacuumSewageAssessment(
                VacuumSewageStatus.HIGH_HIGH_LEVEL_LOCKOUT,
                False, True, True, False,
                f"Collecting tank level {telem.tank_level_pct:.1f}% >= {cls.TANK_HIGH_HIGH_LOCKOUT_PCT}% limit",
            )
        if telem.system_vacuum_bar > cls.VACUUM_LOSS_ALARM_BAR:
            return VacuumSewageAssessment(
                VacuumSewageStatus.VACUUM_LOSS_ALARM,
                True, False, False, False,
                f"Vacuum pressure {telem.system_vacuum_bar:.2f} bar > {cls.VACUUM_LOSS_ALARM_BAR} bar alarm",
            )
        if telem.tank_level_pct >= cls.TANK_MACERATOR_CUT_IN_PCT:
            return VacuumSewageAssessment(
                VacuumSewageStatus.MACERATOR_DISCHARGE_ACTIVE,
                telem.system_vacuum_bar > cls.VACUUM_CUT_IN_BAR, True, False, True,
                f"Tank level {telem.tank_level_pct:.1f}% requires macerator transfer",
            )
        if telem.system_vacuum_bar > cls.VACUUM_CUT_IN_BAR:
            return VacuumSewageAssessment(
                VacuumSewageStatus.EJECTOR_VACUUM_CREATION,
                True, False, False, True,
                f"Vacuum {telem.system_vacuum_bar:.2f} bar depleted; running ejector",
            )
        return VacuumSewageAssessment(
            VacuumSewageStatus.NORMAL_HOLDING,
            False, False, False, True,
            f"Vacuum nominal at {telem.system_vacuum_bar:.2f} bar, tank at {telem.tank_level_pct:.1f}%",
        )
