"""Phase 488: Inert Gas System (IGS) Deck Water Seal Level & Non-Return Protection Engine.

Complies with SOLAS II-2/4.5.5. Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class DeckWaterSealStatus(Enum):
    NORMAL = "normal"
    GAS_BACKFLOW_TRIP = "gas_backflow_trip"
    LOW_LEVEL_VALVE_LOCK = "low_level_valve_lock"
    AUTO_REFILL_ACTIVE = "auto_refill_active"
    TRACE_HEATING_ACTIVE = "trace_heating_active"


@dataclass(frozen=True)
class DeckWaterSealTelemetry:
    water_column_height_mm: float
    ambient_temp_c: float
    downstream_pressure_mbar: float
    inlet_supply_pressure_mbar: float
    refill_valve_currently_open: bool = False


@dataclass(frozen=True)
class DeckWaterSealAssessment:
    status: DeckWaterSealStatus
    low_level_alarm: bool
    supply_valve_locked: bool
    auto_refill_solenoid_open: bool
    trace_heating_active: bool
    gas_backflow_trip: bool
    seal_integrity_safe: bool
    remarks: str


class DeckWaterSealLevelEngine:
    MIN_WATER_HEIGHT_ALARM_MM = 450.0
    AUTO_REFILL_OPEN_HEIGHT_MM = 480.0
    AUTO_REFILL_CLOSE_HEIGHT_MM = 550.0
    TRACE_HEATING_TEMP_C = 5.0
    CRITICAL_SEAL_DELTA_BACKFLOW_MM = 300.0

    @classmethod
    def evaluate(cls, telem: DeckWaterSealTelemetry) -> DeckWaterSealAssessment:
        trace_heat = telem.ambient_temp_c < cls.TRACE_HEATING_TEMP_C
        if telem.water_column_height_mm < cls.AUTO_REFILL_OPEN_HEIGHT_MM:
            refill_open = True
        elif telem.water_column_height_mm >= cls.AUTO_REFILL_CLOSE_HEIGHT_MM:
            refill_open = False
        else:
            refill_open = telem.refill_valve_currently_open

        backflow = (
            telem.downstream_pressure_mbar > telem.inlet_supply_pressure_mbar
            and telem.water_column_height_mm < cls.CRITICAL_SEAL_DELTA_BACKFLOW_MM
        )
        if backflow:
            return DeckWaterSealAssessment(
                DeckWaterSealStatus.GAS_BACKFLOW_TRIP, True, True, refill_open, trace_heat, True, False,
                "IGS gas backflow hazard detected. Downstream > inlet with seal < 300mm. Supply valve locked.",
            )
        if telem.water_column_height_mm < cls.MIN_WATER_HEIGHT_ALARM_MM:
            return DeckWaterSealAssessment(
                DeckWaterSealStatus.LOW_LEVEL_VALVE_LOCK, True, True, refill_open, trace_heat, False, False,
                f"Water seal {telem.water_column_height_mm:.1f}mm < 450mm. Low alarm & supply valve locked.",
            )
        if refill_open:
            return DeckWaterSealAssessment(
                DeckWaterSealStatus.AUTO_REFILL_ACTIVE, False, False, True, trace_heat, False, True,
                "Water seal level < 480mm. Auto-refill solenoid valve open to restore nominal water column.",
            )
        if trace_heat:
            return DeckWaterSealAssessment(
                DeckWaterSealStatus.TRACE_HEATING_ACTIVE, False, False, False, True, False, True,
                f"Ambient temp {telem.ambient_temp_c:.1f}C < 5.0C. Anti-freeze trace heating energized.",
            )
        return DeckWaterSealAssessment(
            DeckWaterSealStatus.NORMAL, False, False, False, False, False, True,
            "IGS deck water seal nominal under SOLAS II-2/4.5.5 non-return barrier criteria.",
        )
