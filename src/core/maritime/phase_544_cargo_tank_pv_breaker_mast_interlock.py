from dataclasses import dataclass
from enum import Enum


class CargoPvBreakerMastState(str, Enum):
    NOMINAL_CARGO_TANK_PRESSURE_ENVELOPE = "NOMINAL_CARGO_TANK_PRESSURE_ENVELOPE"
    PV_BREAKER_LIQUID_SEAL_LOW_LEVEL_ALARM = "PV_BREAKER_LIQUID_SEAL_LOW_LEVEL_ALARM"
    PV_BREAKER_BLOWOUT_CARGO_TRANSFER_TRIP = "PV_BREAKER_BLOWOUT_CARGO_TRANSFER_TRIP"
    MAST_RISER_VENT_FIRE_N2_SNUFFING_TRIP = "MAST_RISER_VENT_FIRE_N2_SNUFFING_TRIP"


@dataclass(frozen=True)
class CargoPvBreakerMastTelemetry:
    cargo_tank_pressure_kpa: float
    pv_breaker_liquid_level_mmwg: float
    mast_riser_flame_screen_temp_c: float
    inert_gas_main_pressure_kpa: float = 8.5


@dataclass(frozen=True)
class CargoPvBreakerMastAssessment:
    state: CargoPvBreakerMastState
    cargo_transfer_emergency_stop_cmd: bool
    mast_riser_n2_snuffing_open: bool
    interlock_code: str


class CargoTankPvBreakerMastEngine:
    """SOLAS II-2 Reg 4.5.3/11.6 & MSC/Circ.677 Cargo Tank P/V Breaker & Mast Riser Supervision."""

    @classmethod
    def evaluate(cls, t: CargoPvBreakerMastTelemetry) -> CargoPvBreakerMastAssessment:
        if t.mast_riser_flame_screen_temp_c >= 75.0:
            return CargoPvBreakerMastAssessment(
                CargoPvBreakerMastState.MAST_RISER_VENT_FIRE_N2_SNUFFING_TRIP,
                True,
                True,
                "SOLAS_II2_MAST_RISER_FLAME_ARRESTER_FIRE_TRIP",
            )
        if t.cargo_tank_pressure_kpa >= 24.0 or t.cargo_tank_pressure_kpa <= -7.0:
            return CargoPvBreakerMastAssessment(
                CargoPvBreakerMastState.PV_BREAKER_BLOWOUT_CARGO_TRANSFER_TRIP,
                True,
                True,
                "SOLAS_II2_REG11_PV_BREAKER_RUPTURE_CARGO_STOP",
            )
        if t.pv_breaker_liquid_level_mmwg < 1600.0:
            return CargoPvBreakerMastAssessment(
                CargoPvBreakerMastState.PV_BREAKER_LIQUID_SEAL_LOW_LEVEL_ALARM,
                False,
                False,
                "ISGOTT_PV_BREAKER_LIQUID_SEAL_DEPLETED_ALARM",
            )
        return CargoPvBreakerMastAssessment(
            CargoPvBreakerMastState.NOMINAL_CARGO_TANK_PRESSURE_ENVELOPE,
            False,
            False,
            "NONE",
        )
