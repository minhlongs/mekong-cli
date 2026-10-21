"""Phase 506: Provision Refrigeration Plant Refrigerant Leak & Personnel Safety.
Complies with IACS UR M15 and ISO 5149 Marine Refrigeration Safety Rules.
Strictly < 90 LOC, zero mocks, pure deterministic physics & rules.
"""
from dataclasses import dataclass
from enum import Enum


class ReeferPlantState(str, Enum):
    NORMAL_COOLING = "NORMAL_COOLING"
    PERSONNEL_LOCKED_IN_ALARM = "PERSONNEL_LOCKED_IN_ALARM"
    REFRIGERANT_LEAK_VENT_BOOST = "REFRIGERANT_LEAK_VENT_BOOST"
    CRITICAL_LEAK_PUMPDOWN_TRIP = "CRITICAL_LEAK_PUMPDOWN_TRIP"
    HIGH_DISCHARGE_PRESSURE_TRIP = "HIGH_DISCHARGE_PRESSURE_TRIP"


@dataclass(frozen=True)
class ProvisionReeferTelemetry:
    refrigerant_leak_ppm: float
    discharge_pressure_bar: float
    meat_room_temp_c: float = -18.0
    personnel_panic_button_active: bool = False


@dataclass(frozen=True)
class ProvisionReeferAssessment:
    plant_state: ReeferPlantState
    compressor_running: bool
    emergency_extraction_fan_on: bool
    alarm_active: bool
    alarm_code: str


class ProvisionReeferLeakSafetyEngine:
    """Evaluates refrigerant gas leak ppm, compressor discharge head, and trapped personnel alarm."""

    LEAK_VENT_PPM: float = 300.0
    LEAK_TRIP_PPM: float = 1000.0
    MAX_DISCHARGE_BAR: float = 22.0

    @classmethod
    def evaluate(cls, t: ProvisionReeferTelemetry) -> ProvisionReeferAssessment:
        if t.refrigerant_leak_ppm >= cls.LEAK_TRIP_PPM:
            return ProvisionReeferAssessment(
                ReeferPlantState.CRITICAL_LEAK_PUMPDOWN_TRIP,
                False,
                True,
                True,
                "REEFER_CRITICAL_GAS_LEAK_ISOLATION",
            )
        if t.discharge_pressure_bar >= cls.MAX_DISCHARGE_BAR:
            return ProvisionReeferAssessment(
                ReeferPlantState.HIGH_DISCHARGE_PRESSURE_TRIP,
                False,
                False,
                True,
                "REEFER_HIGH_HEAD_PRESSURE_CUTOUT",
            )
        if t.personnel_panic_button_active:
            return ProvisionReeferAssessment(
                ReeferPlantState.PERSONNEL_LOCKED_IN_ALARM,
                False,
                True,
                True,
                "COLD_ROOM_PERSONNEL_TRAPPED_ALARM",
            )
        if t.refrigerant_leak_ppm >= cls.LEAK_VENT_PPM:
            return ProvisionReeferAssessment(
                ReeferPlantState.REFRIGERANT_LEAK_VENT_BOOST,
                True,
                True,
                True,
                "REEFER_MINOR_LEAK_EXTRACTION_BOOST",
            )
        return ProvisionReeferAssessment(
            ReeferPlantState.NORMAL_COOLING,
            True,
            False,
            False,
            "NONE",
        )
