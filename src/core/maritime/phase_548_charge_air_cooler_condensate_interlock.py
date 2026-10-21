from dataclasses import dataclass
from enum import Enum


class ChargeAirCondensateState(str, Enum):
    CAC_CONDENSATE_DRAIN_OPTIMAL = "CAC_CONDENSATE_DRAIN_OPTIMAL"
    CAC_AIR_SIDE_FOULING_HIGH_DP_WARN = "CAC_AIR_SIDE_FOULING_HIGH_DP_WARN"
    HIGH_HUMIDITY_CONTINUOUS_BLOWDOWN_ACTIVE = "HIGH_HUMIDITY_CONTINUOUS_BLOWDOWN_ACTIVE"
    TUBE_LEAK_OR_CARRYOVER_SLOWDOWN_TRIP = "TUBE_LEAK_OR_CARRYOVER_SLOWDOWN_TRIP"


@dataclass(frozen=True)
class ChargeAirCondensateTelemetry:
    water_catcher_level_pct: float
    condensate_salinity_ppm: float
    cac_air_dp_kpa: float = 2.1


@dataclass(frozen=True)
class ChargeAirCondensateAssessment:
    state: ChargeAirCondensateState
    engine_slowdown_cmd: bool
    continuous_blowdown_valve_open: bool
    interlock_code: str


class ChargeAirCoolerCondensateEngine:
    """IACS UR M10 & MAN B&W/WinGD Charge Air Cooler Condensate & Tube Leak Interlock."""

    @classmethod
    def evaluate(cls, t: ChargeAirCondensateTelemetry) -> ChargeAirCondensateAssessment:
        if t.water_catcher_level_pct >= 85.0 or t.condensate_salinity_ppm >= 500.0:
            return ChargeAirCondensateAssessment(
                ChargeAirCondensateState.TUBE_LEAK_OR_CARRYOVER_SLOWDOWN_TRIP,
                True,
                True,
                "UR_M10_CAC_TUBE_LEAK_OR_WATER_CARRYOVER_SLOWDOWN",
            )
        if t.water_catcher_level_pct >= 60.0:
            return ChargeAirCondensateAssessment(
                ChargeAirCondensateState.HIGH_HUMIDITY_CONTINUOUS_BLOWDOWN_ACTIVE,
                False,
                True,
                "MAN_WINGD_CAC_HIGH_CONDENSATE_BLOWDOWN_OPEN",
            )
        if t.cac_air_dp_kpa >= 4.5:
            return ChargeAirCondensateAssessment(
                ChargeAirCondensateState.CAC_AIR_SIDE_FOULING_HIGH_DP_WARN,
                False,
                False,
                "CAC_AIR_FIN_FOULING_HIGH_DP_WARN",
            )
        return ChargeAirCondensateAssessment(
            ChargeAirCondensateState.CAC_CONDENSATE_DRAIN_OPTIMAL,
            False,
            False,
            "NONE",
        )
