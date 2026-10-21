from dataclasses import dataclass
from enum import Enum


class CargoReliqBoilOffGcuState(str, Enum):
    RELIQ_BOG_PRESSURE_NOMINAL = "RELIQ_BOG_PRESSURE_NOMINAL"
    CRYOGENIC_SUCTION_WARM_RECYCLE_WARN = "CRYOGENIC_SUCTION_WARM_RECYCLE_WARN"
    GCU_AUTO_THERMAL_OXIDATION_CUTIN = "GCU_AUTO_THERMAL_OXIDATION_CUTIN"
    TANK_OVERPRESSURE_OR_GCU_FLAME_FAIL_TRIP = "TANK_OVERPRESSURE_OR_GCU_FLAME_FAIL_TRIP"


@dataclass(frozen=True)
class CargoReliqBoilOffGcuTelemetry:
    cargo_tank_pressure_kpag: float
    bog_discharge_temp_c: float
    bog_suction_temp_c: float = -125.0
    gcu_flame_established: bool = True


@dataclass(frozen=True)
class CargoReliqBoilOffGcuAssessment:
    state: CargoReliqBoilOffGcuState
    gcu_free_flow_valve_open_cmd: bool
    warm_gas_recycle_valve_open_cmd: bool
    emergency_mast_riser_prv_armed: bool
    interlock_code: str


class CargoReliqBoilOffGcuEngine:
    """IMO IGC Code Ch. 7 & Ch. 16 LNG Cargo Reliquefaction BOG & GCU Interlock."""

    @classmethod
    def evaluate(cls, t: CargoReliqBoilOffGcuTelemetry) -> CargoReliqBoilOffGcuAssessment:
        if (
            t.cargo_tank_pressure_kpag >= 24.0
            or t.bog_discharge_temp_c >= 145.0
            or (t.cargo_tank_pressure_kpag >= 18.0 and not t.gcu_flame_established)
        ):
            return CargoReliqBoilOffGcuAssessment(
                CargoReliqBoilOffGcuState.TANK_OVERPRESSURE_OR_GCU_FLAME_FAIL_TRIP,
                True,
                True,
                True,
                "IGC_CH7_TANK_OVERPRESSURE_OR_GCU_FLAME_LOSS_TRIP",
            )
        if t.cargo_tank_pressure_kpag >= 18.0:
            return CargoReliqBoilOffGcuAssessment(
                CargoReliqBoilOffGcuState.GCU_AUTO_THERMAL_OXIDATION_CUTIN,
                True,
                False,
                False,
                "IGC_CH16_GCU_EXCESS_BOG_THERMAL_OXIDATION_CUTIN",
            )
        if t.bog_suction_temp_c < -155.0:
            return CargoReliqBoilOffGcuAssessment(
                CargoReliqBoilOffGcuState.CRYOGENIC_SUCTION_WARM_RECYCLE_WARN,
                False,
                True,
                False,
                "IGC_CH7_BOG_SUCTION_ANTI_LIQUID_WARM_RECYCLE",
            )
        return CargoReliqBoilOffGcuAssessment(
            CargoReliqBoilOffGcuState.RELIQ_BOG_PRESSURE_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
