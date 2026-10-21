"""Phase 528: Engine Room Bilge Holding Tank Oil-Water Interface & High-Level Overfill Alarm.
Complies with MARPOL Annex I Reg 16 & Reg 17 and IACS UR M24.
Strictly < 85 LOC, zero mocks, pure deterministic statutory physics.
"""
from dataclasses import dataclass
from enum import Enum


class BilgeHoldingTankState(str, Enum):
    NORMAL_GRAVITY_SEPARATION = "NORMAL_GRAVITY_SEPARATION"
    OWS_AUTO_PROCESS_REQUEST = "OWS_AUTO_PROCESS_REQUEST"
    SLUDGE_INTERFACE_SKIM_ACTIVE = "SLUDGE_INTERFACE_SKIM_ACTIVE"
    HIGH_LEVEL_90PCT_ALARM = "HIGH_LEVEL_90PCT_ALARM"
    CRITICAL_OVERFILL_OR_THERMAL_LOCK = "CRITICAL_OVERFILL_OR_THERMAL_LOCK"


@dataclass(frozen=True)
class BilgeHoldingTankTelemetry:
    tank_fill_pct: float
    oil_emulsion_layer_mm: float = 80.0
    heating_coil_temp_c: float = 52.0
    inlet_transfer_valve_open: bool = True


@dataclass(frozen=True)
class BilgeHoldingTankAssessment:
    tank_state: BilgeHoldingTankState
    close_inlet_transfer_valve: bool
    skim_to_sludge_tank_cmd: bool
    start_ows_feed_pump_cmd: bool
    alarm_active: bool
    alarm_code: str


class BilgeHoldingTankInterfaceEngine:
    @classmethod
    def evaluate(cls, t: BilgeHoldingTankTelemetry) -> BilgeHoldingTankAssessment:
        if t.tank_fill_pct >= 95.0 or t.heating_coil_temp_c > 70.0:
            return BilgeHoldingTankAssessment(
                BilgeHoldingTankState.CRITICAL_OVERFILL_OR_THERMAL_LOCK,
                True, True, False, True, "MARPOL_REG17_BILGE_TANK_CRITICAL_LOCK",
            )
        if t.tank_fill_pct >= 90.0:
            return BilgeHoldingTankAssessment(
                BilgeHoldingTankState.HIGH_LEVEL_90PCT_ALARM,
                True, t.oil_emulsion_layer_mm >= 250.0, True, True, "UR_M24_BILGE_HOLDING_90PCT_ALARM",
            )
        if t.oil_emulsion_layer_mm >= 250.0:
            return BilgeHoldingTankAssessment(
                BilgeHoldingTankState.SLUDGE_INTERFACE_SKIM_ACTIVE,
                False, True, False, True, "MARPOL_OIL_INTERFACE_SKIM_TRIGGER",
            )
        if t.tank_fill_pct >= 80.0:
            return BilgeHoldingTankAssessment(
                BilgeHoldingTankState.OWS_AUTO_PROCESS_REQUEST,
                False, False, True, False, "NONE",
            )
        return BilgeHoldingTankAssessment(
            BilgeHoldingTankState.NORMAL_GRAVITY_SEPARATION,
            False, False, False, False, "NONE",
        )
