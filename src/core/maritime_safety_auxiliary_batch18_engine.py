"""Maritime Safety Auxiliary Batch 18 Coordinator Engine (Phases 531-534).
Aggregates Double-Wall Fuel Pipe, Inert Gas Generator, Stern Tube Air-Guard, and Enclosed Space Entry.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_531_double_wall_fuel_pipe_leak import (
    DoubleWallFuelPipeAssessment, DoubleWallFuelPipeLeakEngine, DoubleWallFuelPipeTelemetry,
)
from src.core.maritime.phase_532_inert_gas_generator_stoichiometry import (
    InertGasGeneratorAssessment, InertGasGeneratorStoichiometryEngine, InertGasGeneratorTelemetry,
)
from src.core.maritime.phase_533_stern_tube_airguard_seal_balance import (
    SternTubeAirguardAssessment, SternTubeAirguardSealBalanceEngine, SternTubeAirguardTelemetry,
)
from src.core.maritime.phase_534_enclosed_space_entry_gas_interlock import (
    EnclosedSpaceEntryAssessment, EnclosedSpaceEntryGasInterlockEngine, EnclosedSpaceEntryTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch18Assessment:
    fuel_pipe_assessment: DoubleWallFuelPipeAssessment
    inert_gas_assessment: InertGasGeneratorAssessment
    stern_airguard_assessment: SternTubeAirguardAssessment
    enclosed_space_assessment: EnclosedSpaceEntryAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch18Engine:
    @classmethod
    def evaluate_batch18(
        cls,
        fuel_pipe: DoubleWallFuelPipeTelemetry,
        inert_gas: InertGasGeneratorTelemetry,
        stern_airguard: SternTubeAirguardTelemetry,
        enclosed_space: EnclosedSpaceEntryTelemetry,
    ) -> MaritimeAuxiliaryBatch18Assessment:
        res_fuel = DoubleWallFuelPipeLeakEngine.evaluate(fuel_pipe)
        res_igg = InertGasGeneratorStoichiometryEngine.evaluate(inert_gas)
        res_stern = SternTubeAirguardSealBalanceEngine.evaluate(stern_airguard)
        res_space = EnclosedSpaceEntryGasInterlockEngine.evaluate(enclosed_space)

        alarms: List[str] = []
        if res_fuel.interlock_code != "NONE":
            alarms.append(f"HP_FUEL_PIPE: {res_fuel.interlock_code}")
        if res_igg.interlock_code != "NONE":
            alarms.append(f"IGG_STOICHIOMETRY: {res_igg.interlock_code}")
        if res_stern.interlock_code != "NONE":
            alarms.append(f"STERN_AIRGUARD: {res_stern.interlock_code}")
        if res_space.interlock_code != "NONE":
            alarms.append(f"ENCLOSED_SPACE: {res_space.interlock_code}")

        return MaritimeAuxiliaryBatch18Assessment(
            fuel_pipe_assessment=res_fuel,
            inert_gas_assessment=res_igg,
            stern_airguard_assessment=res_stern,
            enclosed_space_assessment=res_space,
            overall_safe=len(alarms) == 0,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
