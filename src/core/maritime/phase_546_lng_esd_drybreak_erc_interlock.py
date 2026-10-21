from dataclasses import dataclass
from enum import Enum


class LngEsdErcState(str, Enum):
    LNG_MANIFOLD_TRANSFER_NORMAL = "LNG_MANIFOLD_TRANSFER_NORMAL"
    ERC_HYDRAULIC_ACCUMULATOR_LOW_WARN = "ERC_HYDRAULIC_ACCUMULATOR_LOW_WARN"
    ESD1_MANIFOLD_SHUTDOWN_TRIP = "ESD1_MANIFOLD_SHUTDOWN_TRIP"
    ESD2_DRY_BREAK_ERC_DECOUPLE_TRIP = "ESD2_DRY_BREAK_ERC_DECOUPLE_TRIP"


@dataclass(frozen=True)
class LngEsdErcTelemetry:
    vessel_surge_drift_m: float
    drip_tray_temp_c: float
    erc_hydraulic_pressure_bar: float
    ship_shore_link_healthy: bool = True


@dataclass(frozen=True)
class LngEsdErcAssessment:
    state: LngEsdErcState
    esd1_manifold_valves_close_cmd: bool
    esd2_erc_collar_release_cmd: bool
    cargo_pumps_compressors_trip_cmd: bool
    interlock_code: str


class LngEsdDrybreakErcEngine:
    """IMO IGC Code Ch. 18.10 & SIGTTO LNG/LPG ESD-1 / ESD-2 & Dry-Break ERC Interlock."""

    @classmethod
    def evaluate(cls, t: LngEsdErcTelemetry) -> LngEsdErcAssessment:
        if t.vessel_surge_drift_m >= 3.5 or t.drip_tray_temp_c <= -110.0:
            return LngEsdErcAssessment(
                LngEsdErcState.ESD2_DRY_BREAK_ERC_DECOUPLE_TRIP,
                True,
                True,
                True,
                "IGC_CH18_ESD2_EMERGENCY_RELEASE_COUPLING_DECOUPLE",
            )
        if t.vessel_surge_drift_m >= 2.0 or not t.ship_shore_link_healthy:
            return LngEsdErcAssessment(
                LngEsdErcState.ESD1_MANIFOLD_SHUTDOWN_TRIP,
                True,
                False,
                True,
                "SIGTTO_ESD1_MANIFOLD_VALVE_CLOSURE_TRIP",
            )
        if t.erc_hydraulic_pressure_bar < 165.0:
            return LngEsdErcAssessment(
                LngEsdErcState.ERC_HYDRAULIC_ACCUMULATOR_LOW_WARN,
                False,
                False,
                False,
                "IGC_CH18_ERC_ACCUMULATOR_LOW_PRESSURE_WARN",
            )
        return LngEsdErcAssessment(
            LngEsdErcState.LNG_MANIFOLD_TRANSFER_NORMAL,
            False,
            False,
            False,
            "NONE",
        )
