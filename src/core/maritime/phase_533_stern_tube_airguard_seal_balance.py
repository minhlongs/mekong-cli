from dataclasses import dataclass
from enum import Enum


class SternTubeAirguardState(str, Enum):
    BALANCED_AIRGUARD_BARRIER = "BALANCED_AIRGUARD_BARRIER"
    SEAL_RING_WEAR_EXCESS_AIRFLOW_WARN = "SEAL_RING_WEAR_EXCESS_AIRFLOW_WARN"
    AIR_BARRIER_COLLAPSE_INGRESS_ALARM = "AIR_BARRIER_COLLAPSE_INGRESS_ALARM"
    EAL_WATER_EMULSIFICATION_CRITICAL = "EAL_WATER_EMULSIFICATION_CRITICAL"


@dataclass(frozen=True)
class SternTubeAirguardTelemetry:
    aft_seal_air_pressure_bar: float
    seawater_draft_pressure_bar: float
    aft_seal_airflow_nl_min: float
    eal_water_content_pct: float
    stern_bearing_temp_c: float


@dataclass(frozen=True)
class SternTubeAirguardAssessment:
    state: SternTubeAirguardState
    air_over_sea_dp_bar: float
    standby_air_regulator_cutin: bool
    high_gravity_header_boost: bool
    interlock_code: str


class SternTubeAirguardSealBalanceEngine:
    """IACS UR M10, VGP EAL & ClassNK/DNV Stern Tube Air-Guard Seal Supervision."""

    @classmethod
    def evaluate(cls, t: SternTubeAirguardTelemetry) -> SternTubeAirguardAssessment:
        dp = round(t.aft_seal_air_pressure_bar - t.seawater_draft_pressure_bar, 3)
        if t.eal_water_content_pct >= 1.0 or t.stern_bearing_temp_c >= 65.0:
            return SternTubeAirguardAssessment(
                SternTubeAirguardState.EAL_WATER_EMULSIFICATION_CRITICAL,
                dp,
                dp < 0.15,
                True,
                "UR_M10_STERN_TUBE_EAL_CONTAMINATION_OR_TEMP_TRIP",
            )
        if dp < 0.10:
            return SternTubeAirguardAssessment(
                SternTubeAirguardState.AIR_BARRIER_COLLAPSE_INGRESS_ALARM,
                dp,
                True,
                True,
                "UR_M10_AIRGUARD_PRESSURE_LOW_STANDBY_AIR_CUTIN",
            )
        if t.aft_seal_airflow_nl_min > 45.0:
            return SternTubeAirguardAssessment(
                SternTubeAirguardState.SEAL_RING_WEAR_EXCESS_AIRFLOW_WARN,
                dp,
                False,
                False,
                "STERN_TUBE_AFT_SEAL_EXCESS_AIR_LEAK",
            )
        return SternTubeAirguardAssessment(
            SternTubeAirguardState.BALANCED_AIRGUARD_BARRIER,
            dp,
            False,
            False,
            "NONE",
        )
