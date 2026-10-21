from dataclasses import dataclass
from enum import Enum


class AirLubricationAlsState(str, Enum):
    ALS_MICROBUBBLE_CARPET_NOMINAL = "ALS_MICROBUBBLE_CARPET_NOMINAL"
    HEADER_OVERPRESSURE_MARGIN_LOW_WARN = "HEADER_OVERPRESSURE_MARGIN_LOW_WARN"
    LOW_VESSEL_SPEED_AUTO_STANDBY_IDLE = "LOW_VESSEL_SPEED_AUTO_STANDBY_IDLE"
    WATER_BACKFLOW_OR_ROLL_ISOLATION_TRIP = "WATER_BACKFLOW_OR_ROLL_ISOLATION_TRIP"


@dataclass(frozen=True)
class AirLubricationAlsTelemetry:
    vessel_speed_knots: float
    roll_angle_deg: float
    header_diff_pressure_bar: float = 0.65
    compressor_discharge_temp_c: float = 78.0
    water_backflow_detected: bool = False


@dataclass(frozen=True)
class AirLubricationAlsAssessment:
    state: AirLubricationAlsState
    hull_non_return_isolation_valve_close: bool
    als_blower_compressor_trip_cmd: bool
    air_purge_scavenge_cycle_active: bool
    interlock_code: str


class AirLubricationAlsEngine:
    """IMO MEPC.1/Circ.896 Hull Air Lubrication System (ALS) Backflow & Roll Interlock."""

    @classmethod
    def evaluate(cls, t: AirLubricationAlsTelemetry) -> AirLubricationAlsAssessment:
        if (
            t.water_backflow_detected
            or t.roll_angle_deg >= 10.0
            or t.compressor_discharge_temp_c >= 115.0
        ):
            return AirLubricationAlsAssessment(
                AirLubricationAlsState.WATER_BACKFLOW_OR_ROLL_ISOLATION_TRIP,
                True,
                True,
                True,
                "MEPC896_ALS_BACKFLOW_OR_EXCESS_ROLL_HULL_ISOLATION_TRIP",
            )
        if t.vessel_speed_knots < 8.0:
            return AirLubricationAlsAssessment(
                AirLubricationAlsState.LOW_VESSEL_SPEED_AUTO_STANDBY_IDLE,
                True,
                False,
                False,
                "MEPC896_ALS_LOW_SPEED_INEFFECTIVE_BUBBLE_STANDBY",
            )
        if t.header_diff_pressure_bar < 0.35:
            return AirLubricationAlsAssessment(
                AirLubricationAlsState.HEADER_OVERPRESSURE_MARGIN_LOW_WARN,
                False,
                False,
                True,
                "UR_M44_ALS_NOZZLE_HYDROSTATIC_DIFF_PRESSURE_LOW_WARN",
            )
        return AirLubricationAlsAssessment(
            AirLubricationAlsState.ALS_MICROBUBBLE_CARPET_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
