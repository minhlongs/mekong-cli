"""Central Facade for Maritime Phases 383-386.

Orchestrates Fuel Purifier Automation, Auxiliary Emergency Steering,
Anti-Heeling Ballast Control, and Tanker Pump Room Gas Sniffer engines.
"""

from dataclasses import dataclass, field
from typing import List

from src.core.maritime.phase_383_marine_fuel_purifier_clarifier import (
    FuelPurifierInput,
    FuelPurifierResult,
    MarineFuelPurifierEngine,
)
from src.core.maritime.phase_384_auxiliary_emergency_steering import (
    AuxiliaryEmergencySteeringEngine,
    SteeringGearInput,
    SteeringGearResult,
)
from src.core.maritime.phase_385_anti_heeling_ballast_pumping import (
    AntiHeelingBallastEngine,
    AntiHeelingInput,
    AntiHeelingResult,
)
from src.core.maritime.phase_386_tanker_pumproom_gas_sniffer import (
    PumpRoomGasInput,
    PumpRoomGasResult,
    TankerPumpRoomGasEngine,
)


@dataclass
class Maritime383To386AggregateResult:
    """Consolidated assessment of engine room, steering, ballast, and safety systems."""
    purifier: FuelPurifierResult
    steering: SteeringGearResult
    anti_heeling: AntiHeelingResult
    gas_sniffer: PumpRoomGasResult
    overall_seaworthiness: str  # FULLY_COMPLIANT, CAUTION, NON_COMPLIANT
    all_warnings: List[str] = field(default_factory=list)


class MaritimePurifierSteeringHeelingSnifferEngine:
    """Facade orchestrating Maritime Phases 383-386 diagnostic suites."""

    def __init__(self) -> None:
        self.purifier_engine = MarineFuelPurifierEngine()
        self.steering_engine = AuxiliaryEmergencySteeringEngine()
        self.anti_heeling_engine = AntiHeelingBallastEngine()
        self.gas_engine = TankerPumpRoomGasEngine()

    def evaluate_all(
        self,
        purifier_input: FuelPurifierInput,
        steering_input: SteeringGearInput,
        heeling_input: AntiHeelingInput,
        gas_input: PumpRoomGasInput,
    ) -> Maritime383To386AggregateResult:
        purifier_res = self.purifier_engine.evaluate(purifier_input)
        steering_res = self.steering_engine.evaluate(steering_input)
        heeling_res = self.anti_heeling_engine.evaluate(heeling_input)
        gas_res = self.gas_engine.evaluate(gas_input)

        warnings: List[str] = (
            purifier_res.warnings
            + steering_res.warnings
            + heeling_res.warnings
            + gas_res.warnings
        )

        critical_conditions = (
            purifier_res.purifier_status == "CRITICAL_TRIP"
            or steering_res.steering_status in ("TRIPPED", "ALARM")
            or heeling_res.operational_status == "CRITICAL_SHUTDOWN"
            or gas_res.cargo_pump_trip_required
            or gas_res.atmosphere_status in ("CRITICAL_EXPLOSION_HAZARD", "TOXIC_HAZARD")
        )

        caution_conditions = (
            purifier_res.purifier_status in ("SUB_OPTIMAL", "WARNING")
            or steering_res.steering_status == "DEGRADED"
            or heeling_res.operational_status == "LIST_WARNING"
            or gas_res.atmosphere_status == "WARNING"
            or not gas_res.entry_permitted
        )

        if critical_conditions:
            overall_status = "NON_COMPLIANT"
        elif caution_conditions:
            overall_status = "CAUTION"
        else:
            overall_status = "FULLY_COMPLIANT"

        return Maritime383To386AggregateResult(
            purifier=purifier_res,
            steering=steering_res,
            anti_heeling=heeling_res,
            gas_sniffer=gas_res,
            overall_seaworthiness=overall_status,
            all_warnings=warnings,
        )
