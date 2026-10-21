"""Phase 517: Bow Visor & Stern Ramp Hydraulic Cleat & Watertight Seal Integrity.
Complies with SOLAS II-1 Reg 15-1 and IACS UR S8 / S9 Ro-Ro Shell Door Rules.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class ShellDoorSealStatus(str, Enum):
    LOCKED_AND_WATERTIGHT_AT_SEA = "LOCKED_AND_WATERTIGHT_AT_SEA"
    PORT_CARGO_OPERATIONS_OPEN = "PORT_CARGO_OPERATIONS_OPEN"
    UNSECURED_CLEAT_SEA_DEPARTURE_BLOCK = "UNSECURED_CLEAT_SEA_DEPARTURE_BLOCK"
    PNEUMATIC_SEAL_LOW_PRESSURE = "PNEUMATIC_SEAL_LOW_PRESSURE"
    COLLISION_BULKHEAD_WATER_INGRESS = "COLLISION_BULKHEAD_WATER_INGRESS"


@dataclass(frozen=True)
class BowVisorRampTelemetry:
    vessel_at_sea_mode: bool
    all_hydraulic_cleats_locked: bool
    pneumatic_gasket_bar: float = 3.0
    threshold_water_ingress_detected: bool = False


@dataclass(frozen=True)
class BowVisorRampAssessment:
    seal_status: ShellDoorSealStatus
    bridge_departure_green_light: bool
    alarm_active: bool
    alarm_code: str


class BowVisorSternRampCleatEngine:
    """Evaluates Ro-Ro shell door hydraulic cleats, gasket seal bar, and water ingress."""

    MIN_GASKET_BAR: float = 2.5

    @classmethod
    def evaluate(cls, t: BowVisorRampTelemetry) -> BowVisorRampAssessment:
        if t.threshold_water_ingress_detected:
            return BowVisorRampAssessment(
                ShellDoorSealStatus.COLLISION_BULKHEAD_WATER_INGRESS,
                False,
                True,
                "RORO_SHELL_DOOR_SEA_WATER_INGRESS_ALARM",
            )
        if not t.vessel_at_sea_mode and not t.all_hydraulic_cleats_locked:
            return BowVisorRampAssessment(
                ShellDoorSealStatus.PORT_CARGO_OPERATIONS_OPEN,
                False,
                False,
                "NONE",
            )
        if not t.all_hydraulic_cleats_locked:
            return BowVisorRampAssessment(
                ShellDoorSealStatus.UNSECURED_CLEAT_SEA_DEPARTURE_BLOCK,
                False,
                True,
                "SOLAS_SHELL_DOOR_CLEAT_UNLOCKED_AT_SEA",
            )
        if t.pneumatic_gasket_bar < cls.MIN_GASKET_BAR:
            return BowVisorRampAssessment(
                ShellDoorSealStatus.PNEUMATIC_SEAL_LOW_PRESSURE,
                False,
                True,
                "SHELL_DOOR_GASKET_SEAL_DEFLATED",
            )
        return BowVisorRampAssessment(
            ShellDoorSealStatus.LOCKED_AND_WATERTIGHT_AT_SEA,
            True,
            False,
            "NONE",
        )
