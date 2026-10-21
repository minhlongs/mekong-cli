from dataclasses import dataclass
from enum import Enum


class StuffingBoxDrainState(str, Enum):
    OPTIMAL_STUFFING_BOX_SEALING = "OPTIMAL_STUFFING_BOX_SEALING"
    SCRAPER_RING_EXCESS_LEAKAGE_WARN = "SCRAPER_RING_EXCESS_LEAKAGE_WARN"
    STUFFING_BOX_CONTAMINATION_SLUDGE_DIVERT = "STUFFING_BOX_CONTAMINATION_SLUDGE_DIVERT"
    GAS_BLOWBY_SEALING_RING_FAILURE_SLOWDOWN = "GAS_BLOWBY_SEALING_RING_FAILURE_SLOWDOWN"


@dataclass(frozen=True)
class StuffingBoxDrainTelemetry:
    blowby_gas_pressure_bar: float
    drain_oil_temp_c: float
    drain_leakage_rate_l_24h: float
    iron_wear_ppm: float = 40.0


@dataclass(frozen=True)
class StuffingBoxDrainAssessment:
    state: StuffingBoxDrainState
    engine_slowdown_cmd: bool
    divert_drain_to_sludge_tank: bool
    interlock_code: str


class PistonRodStuffingBoxDrainEngine:
    """IACS UR M10 & MAN B&W/WinGD Piston Rod Stuffing Box Drain & Blow-By Supervision."""

    @classmethod
    def evaluate(cls, t: StuffingBoxDrainTelemetry) -> StuffingBoxDrainAssessment:
        if t.blowby_gas_pressure_bar >= 0.35 or t.drain_oil_temp_c >= 85.0:
            return StuffingBoxDrainAssessment(
                StuffingBoxDrainState.GAS_BLOWBY_SEALING_RING_FAILURE_SLOWDOWN,
                True,
                True,
                "UR_M10_STUFFING_BOX_GAS_BLOWBY_CRANKCASE_RISK_SLOWDOWN",
            )
        if t.iron_wear_ppm >= 150.0:
            return StuffingBoxDrainAssessment(
                StuffingBoxDrainState.STUFFING_BOX_CONTAMINATION_SLUDGE_DIVERT,
                False,
                True,
                "MAN_STUFFING_BOX_HIGH_FE_SLUDGE_DIVERT",
            )
        if t.drain_leakage_rate_l_24h > 25.0:
            return StuffingBoxDrainAssessment(
                StuffingBoxDrainState.SCRAPER_RING_EXCESS_LEAKAGE_WARN,
                False,
                True,
                "UR_M10_STUFFING_BOX_SCRAPER_WEAR_WARN",
            )
        return StuffingBoxDrainAssessment(
            StuffingBoxDrainState.OPTIMAL_STUFFING_BOX_SEALING,
            False,
            False,
            "NONE",
        )
