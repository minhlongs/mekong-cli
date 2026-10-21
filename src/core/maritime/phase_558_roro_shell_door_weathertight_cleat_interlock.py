from dataclasses import dataclass
from enum import Enum


class RoRoShellDoorInterlockState(str, Enum):
    SHELL_DOOR_WEATHERTIGHT_SEALED_NOMINAL = "SHELL_DOOR_WEATHERTIGHT_SEALED_NOMINAL"
    CLEAT_HYDRAULIC_PRESSURE_LOW_WARN = "CLEAT_HYDRAULIC_PRESSURE_LOW_WARN"
    GASKET_LEAK_BILGE_WELL_HIGH_ALARM = "GASKET_LEAK_BILGE_WELL_HIGH_ALARM"
    UNSECURED_SHELL_DOOR_SEA_MODE_TRIP = "UNSECURED_SHELL_DOOR_SEA_MODE_TRIP"


@dataclass(frozen=True)
class RoRoShellDoorTelemetry:
    all_cleats_and_pins_locked: bool
    inner_bow_door_closed: bool
    bilge_well_ingress_l_min: float = 1.5
    cleat_hydraulic_pressure_bar: float = 155.0
    vessel_sea_going_mode: bool = True


@dataclass(frozen=True)
class RoRoShellDoorAssessment:
    state: RoRoShellDoorInterlockState
    bridge_red_indicator_audible_alarm: bool
    departure_propulsion_inhibit_cmd: bool
    door_bilge_eductor_start_cmd: bool
    interlock_code: str


class RoRoShellDoorIndicatorsInterlockEngine:
    """SOLAS II-1 Reg 15-1 / 23-2 & IACS UR S8 Ro-Ro Shell & Inner Bow Door Interlock."""

    @classmethod
    def evaluate(cls, t: RoRoShellDoorTelemetry) -> RoRoShellDoorAssessment:
        if t.vessel_sea_going_mode and (
            not t.all_cleats_and_pins_locked or not t.inner_bow_door_closed
        ):
            return RoRoShellDoorAssessment(
                RoRoShellDoorInterlockState.UNSECURED_SHELL_DOOR_SEA_MODE_TRIP,
                True,
                True,
                True,
                "SOLAS_II1_R15_1_RORO_SHELL_DOOR_UNSECURED_SEA_MODE_TRIP",
            )
        if t.bilge_well_ingress_l_min >= 15.0:
            return RoRoShellDoorAssessment(
                RoRoShellDoorInterlockState.GASKET_LEAK_BILGE_WELL_HIGH_ALARM,
                True,
                False,
                True,
                "UR_S8_SHELL_DOOR_GASKET_WATER_INGRESS_BILGE_ALARM",
            )
        if t.cleat_hydraulic_pressure_bar < 110.0:
            return RoRoShellDoorAssessment(
                RoRoShellDoorInterlockState.CLEAT_HYDRAULIC_PRESSURE_LOW_WARN,
                False,
                False,
                False,
                "UR_S8_CLEAT_LOCKING_HYDRAULIC_PRESSURE_LOW_WARN",
            )
        return RoRoShellDoorAssessment(
            RoRoShellDoorInterlockState.SHELL_DOOR_WEATHERTIGHT_SEALED_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
