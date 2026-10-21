"""Master Coordinator Engine for Maritime Automation Phases 487-490.

Coordinates:
- Phase 487: Jacket Cooling Water Temp & Flow
- Phase 488: Deck Water Seal Level & Non-Return
- Phase 489: Central Cooling 3-Way Valve & SW Head
- Phase 490: Starting Air Compressor Unloader & Relief

Strictly < 95 LOC.
"""

from dataclasses import dataclass

from src.core.maritime.phase_487_jacket_cooling_temp_flow import (
    JacketCoolingAssessment,
    JacketCoolingTelemetry,
    JacketCoolingTempFlowEngine,
)
from src.core.maritime.phase_488_deck_water_seal_level import (
    DeckWaterSealAssessment,
    DeckWaterSealLevelEngine,
    DeckWaterSealStatus,
    DeckWaterSealTelemetry,
)
from src.core.maritime.phase_489_central_cooling_3way_valve import (
    CentralCooling3WayValveEngine,
    CentralCoolingAssessment,
    CentralCoolingStatus,
    CentralCoolingTelemetry,
)
from src.core.maritime.phase_490_starting_air_compressor_unloader import (
    StartingAirAssessment,
    StartingAirCompressorUnloaderEngine,
    StartingAirStatus,
    StartingAirTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch7Telemetry:
    jacket: JacketCoolingTelemetry
    deck_seal: DeckWaterSealTelemetry
    central_cooling: CentralCoolingTelemetry
    starting_air: StartingAirTelemetry


@dataclass(frozen=True)
class MaritimePhases487to490Assessment:
    jacket_eval: JacketCoolingAssessment
    deck_seal_eval: DeckWaterSealAssessment
    central_cooling_eval: CentralCoolingAssessment
    starting_air_eval: StartingAirAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: str


class MaritimeSafetyAuxiliaryBatch7Engine:
    @classmethod
    def evaluate(cls, telem: MaritimeAuxiliaryBatch7Telemetry) -> MaritimePhases487to490Assessment:
        jacket = JacketCoolingTempFlowEngine.evaluate(telem.jacket)
        deck_seal = DeckWaterSealLevelEngine.evaluate(telem.deck_seal)
        central = CentralCooling3WayValveEngine.evaluate(telem.central_cooling)
        air = StartingAirCompressorUnloaderEngine.evaluate(telem.starting_air)

        alarms = sum([
            jacket.slowdown_trip_command or jacket.expansion_tank_alarm_active,
            deck_seal.status in (DeckWaterSealStatus.GAS_BACKFLOW_TRIP, DeckWaterSealStatus.LOW_LEVEL_VALVE_LOCK),
            central.status in (CentralCoolingStatus.STANDBY_SW_PUMP_CUT_IN, CentralCoolingStatus.LT_TEMP_OUT_OF_SPEC),
            air.trip_lockout or air.status in (StartingAirStatus.HIGH_DISCHARGE_TEMP_TRIP, StartingAirStatus.SAFETY_VALVE_LIFT_TRIP),
        ])

        overall_safe = (
            jacket.cooling_adequate
            and not jacket.slowdown_trip_command
            and deck_seal.seal_integrity_safe
            and central.cooling_loop_balanced
            and not air.trip_lockout
            and alarms == 0
        )

        return MaritimePhases487to490Assessment(
            jacket_eval=jacket,
            deck_seal_eval=deck_seal,
            central_cooling_eval=central,
            starting_air_eval=air,
            overall_safe=overall_safe,
            active_alarms_count=alarms,
            system_health_summary=f"Batch 7 Evaluated. Active Alarms: {alarms}. Safe: {overall_safe}.",
        )
