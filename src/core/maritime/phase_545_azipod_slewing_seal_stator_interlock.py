from dataclasses import dataclass
from enum import Enum


class AzipodPropulsorState(str, Enum):
    OPTIMAL_AZIPOD_OPERATION = "OPTIMAL_AZIPOD_OPERATION"
    SLEWING_HYDRAULIC_LOW_PRESSURE_STANDBY_CUTIN = "SLEWING_HYDRAULIC_LOW_PRESSURE_STANDBY_CUTIN"
    STATOR_THERMAL_PRE_ALARM_COOLING_BOOST = "STATOR_THERMAL_PRE_ALARM_COOLING_BOOST"
    POD_CRITICAL_STATOR_OR_INGRESS_PROPULSION_DERATE = "POD_CRITICAL_STATOR_OR_INGRESS_PROPULSION_DERATE"


@dataclass(frozen=True)
class AzipodPropulsorTelemetry:
    stator_winding_temp_c: float
    pod_bilge_ingress_liters: float
    slewing_hydraulic_pressure_bar: float
    cooling_air_temp_c: float = 42.0


@dataclass(frozen=True)
class AzipodPropulsorAssessment:
    state: AzipodPropulsorState
    propulsion_power_derate_cmd: bool
    standby_slewing_pump_cut_in: bool
    cooling_air_blower_boost_cmd: bool
    interlock_code: str


class AzipodSlewingSealStatorEngine:
    """IACS UR M65/E11 & SOLAS II-1 Reg 29 Azimuth Podded Propulsor Supervision."""

    @classmethod
    def evaluate(cls, t: AzipodPropulsorTelemetry) -> AzipodPropulsorAssessment:
        if t.stator_winding_temp_c >= 155.0 or t.pod_bilge_ingress_liters >= 25.0:
            return AzipodPropulsorAssessment(
                AzipodPropulsorState.POD_CRITICAL_STATOR_OR_INGRESS_PROPULSION_DERATE,
                True,
                True,
                True,
                "UR_M65_AZIPOD_CRITICAL_STATOR_OR_SEAL_INGRESS_DERATE",
            )
        if t.stator_winding_temp_c >= 135.0 or t.cooling_air_temp_c > 55.0:
            return AzipodPropulsorAssessment(
                AzipodPropulsorState.STATOR_THERMAL_PRE_ALARM_COOLING_BOOST,
                False,
                False,
                True,
                "UR_E11_AZIPOD_STATOR_THERMAL_COOLING_BOOST",
            )
        if t.slewing_hydraulic_pressure_bar < 140.0:
            return AzipodPropulsorAssessment(
                AzipodPropulsorState.SLEWING_HYDRAULIC_LOW_PRESSURE_STANDBY_CUTIN,
                False,
                True,
                False,
                "SOLAS_REG29_AZIPOD_SLEWING_STANDBY_PUMP_CUTIN",
            )
        return AzipodPropulsorAssessment(
            AzipodPropulsorState.OPTIMAL_AZIPOD_OPERATION,
            False,
            False,
            False,
            "NONE",
        )
