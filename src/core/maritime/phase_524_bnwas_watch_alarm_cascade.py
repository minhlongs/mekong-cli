"""Phase 524: Bridge Navigational Watch Alarm System (BNWAS) Dead-Man Cascade.
Complies with IMO Resolution MSC.128(75) and SOLAS Chapter V Reg 19.2.2.3.
Strictly < 85 LOC, zero mocks, pure deterministic timer cascade machine.
"""
from dataclasses import dataclass
from enum import Enum


class BnwasCascadeState(str, Enum):
    STANDBY_MANUAL_STEERING = "STANDBY_MANUAL_STEERING"
    WATCH_OFFICER_ALERT_DORMANT = "WATCH_OFFICER_ALERT_DORMANT"
    STAGE1_BRIDGE_VISUAL_AUDIBLE_ALERT = "STAGE1_BRIDGE_VISUAL_AUDIBLE_ALERT"
    STAGE2_BACKUP_OFFICER_CABIN_ALARM = "STAGE2_BACKUP_OFFICER_CABIN_ALARM"
    STAGE3_MASTER_SHIPWIDE_EMERGENCY_ALARM = "STAGE3_MASTER_SHIPWIDE_EMERGENCY_ALARM"


@dataclass(frozen=True)
class BnwasTelemetry:
    unattended_elapsed_sec: float
    dormant_period_sec: float = 360.0
    autopilot_engaged: bool = True
    continuous_on_mode: bool = False


@dataclass(frozen=True)
class BnwasAssessment:
    cascade_state: BnwasCascadeState
    bridge_local_alarm: bool
    back_up_officer_call: bool
    master_all_cabin_gong: bool
    alarm_active: bool
    alarm_code: str


class BnwasWatchAlarmCascadeEngine:
    """Enforces IMO MSC.128(75) BNWAS Stage 1 (+0s), Stage 2 (+15s), and Stage 3 (+105s) cascade."""

    STAGE2_DELAY_SEC: float = 15.0
    STAGE3_DELAY_SEC: float = 105.0

    @classmethod
    def evaluate(cls, t: BnwasTelemetry) -> BnwasAssessment:
        if not t.autopilot_engaged and not t.continuous_on_mode:
            return BnwasAssessment(
                BnwasCascadeState.STANDBY_MANUAL_STEERING, False, False, False, False, "NONE"
            )
        if t.unattended_elapsed_sec >= t.dormant_period_sec + cls.STAGE3_DELAY_SEC:
            return BnwasAssessment(
                BnwasCascadeState.STAGE3_MASTER_SHIPWIDE_EMERGENCY_ALARM,
                True, True, True, True, "MSC128_BNWAS_STAGE3_INCAPACITATED_OOW_EMERGENCY",
            )
        if t.unattended_elapsed_sec >= t.dormant_period_sec + cls.STAGE2_DELAY_SEC:
            return BnwasAssessment(
                BnwasCascadeState.STAGE2_BACKUP_OFFICER_CABIN_ALARM,
                True, True, False, True, "MSC128_BNWAS_STAGE2_OFFICER_CABIN_CALL",
            )
        if t.unattended_elapsed_sec >= t.dormant_period_sec:
            return BnwasAssessment(
                BnwasCascadeState.STAGE1_BRIDGE_VISUAL_AUDIBLE_ALERT,
                True, False, False, True, "MSC128_BNWAS_STAGE1_BRIDGE_ALERT",
            )
        return BnwasAssessment(
            BnwasCascadeState.WATCH_OFFICER_ALERT_DORMANT, False, False, False, False, "NONE"
        )
