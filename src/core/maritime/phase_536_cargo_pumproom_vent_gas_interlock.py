from dataclasses import dataclass
from enum import Enum


class CargoPumproomState(str, Enum):
    SAFE_PUMPROOM_OPERATING = "SAFE_PUMPROOM_OPERATING"
    BILGE_HIGH_LEVEL_ALARM = "BILGE_HIGH_LEVEL_ALARM"
    HYDROCARBON_10PCT_LEL_PRE_ALARM = "HYDROCARBON_10PCT_LEL_PRE_ALARM"
    VENTILATION_LOSS_INTERLOCK_HOLD = "VENTILATION_LOSS_INTERLOCK_HOLD"
    EMERGENCY_COP_SHUTDOWN_TRIP = "EMERGENCY_COP_SHUTDOWN_TRIP"


@dataclass(frozen=True)
class CargoPumproomTelemetry:
    ventilation_ach: float
    hydrocarbon_lel_pct: float
    pump_casing_bearing_temp_c: float
    pumproom_bilge_level_mm: float


@dataclass(frozen=True)
class CargoPumproomAssessment:
    state: CargoPumproomState
    cargo_oil_pump_trip_cmd: bool
    standby_exhaust_fan_start: bool
    lighting_interlock_permitted: bool
    interlock_code: str


class CargoPumproomVentGasInterlockEngine:
    """SOLAS II-2 Reg 4.5.4 & IBC Code Cargo Pump Room Ventilation & Gas Supervision."""

    @classmethod
    def evaluate(cls, t: CargoPumproomTelemetry) -> CargoPumproomAssessment:
        vent_ok = t.ventilation_ach >= 20.0
        if t.hydrocarbon_lel_pct >= 30.0 or t.pump_casing_bearing_temp_c >= 80.0:
            return CargoPumproomAssessment(
                CargoPumproomState.EMERGENCY_COP_SHUTDOWN_TRIP,
                True,
                True,
                vent_ok,
                "SOLAS_II2_4_5_4_COP_GAS_OR_BEARING_TEMP_TRIP",
            )
        if not vent_ok:
            return CargoPumproomAssessment(
                CargoPumproomState.VENTILATION_LOSS_INTERLOCK_HOLD,
                False,
                True,
                False,
                "SOLAS_II2_4_5_4_PUMPROOM_VENT_UNDER_20ACH",
            )
        if t.hydrocarbon_lel_pct >= 10.0:
            return CargoPumproomAssessment(
                CargoPumproomState.HYDROCARBON_10PCT_LEL_PRE_ALARM,
                False,
                True,
                True,
                "SOLAS_II2_4_5_4_GAS_10PCT_LEL_CONTINUOUS_ALARM",
            )
        if t.pumproom_bilge_level_mm >= 250.0:
            return CargoPumproomAssessment(
                CargoPumproomState.BILGE_HIGH_LEVEL_ALARM,
                False,
                False,
                True,
                "PUMPROOM_BILGE_HIGH_LEVEL_ALARM",
            )
        return CargoPumproomAssessment(
            CargoPumproomState.SAFE_PUMPROOM_OPERATING,
            False,
            False,
            True,
            "NONE",
        )
