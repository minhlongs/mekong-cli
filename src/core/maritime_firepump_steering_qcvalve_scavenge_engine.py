"""Unified Facade for Maritime Phases 395-398.

Aggregates Emergency Fire Pump (SOLAS II-2 Reg 10), Steering Gear Dual Actuators (SOLAS II-1 Reg 29),
Quick-Closing Valves (SOLAS II-2 Reg 4.2.2.3.4), and Scavenge Air Fire Interlock (IACS M44).
Strictly zero mock dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.core.maritime.phase_395_emergency_fire_pump_sea_suction import (
    EmergencyFirePumpEngine,
    EmergencyFirePumpInput,
    EmergencyFirePumpResult,
)
from src.core.maritime.phase_396_steering_gear_dual_hydraulic import (
    SteeringGearEngine,
    SteeringGearInput,
    SteeringGearResult,
)
from src.core.maritime.phase_397_quick_closing_valve_emergency_shutoff import (
    QuickClosingValveEngine,
    QuickClosingValveInput,
    QuickClosingValveResult,
)
from src.core.maritime.phase_398_scavenge_air_fire_detection import (
    ScavengeFireEngine,
    ScavengeFireInput,
    ScavengeFireResult,
)


@dataclass
class MaritimeSafetyPropulsionControlResult:
    fire_pump_result: EmergencyFirePumpResult
    steering_result: SteeringGearResult
    quick_closing_result: QuickClosingValveResult
    scavenge_result: ScavengeFireResult
    overall_maritime_safety_status: str
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_maritime_safety_status,
            "emergency_fire_pump": {
                "status": self.fire_pump_result.pump_operational_status,
                "flow_compliant": self.fire_pump_result.discharge_capacity_compliant,
                "pressure_compliant": self.fire_pump_result.discharge_pressure_compliant,
                "priming_compliant": self.fire_pump_result.suction_priming_compliant,
                "endurance_compliant": self.fire_pump_result.endurance_compliant,
                "jets_supported": self.fire_pump_result.fire_hose_jets_supported,
            },
            "steering_gear": {
                "status": self.steering_result.steering_readiness_status,
                "speed_compliant": self.steering_result.main_gear_speed_compliant,
                "aux_compliant": self.steering_result.auxiliary_gear_speed_compliant,
                "redundancy_active": self.steering_result.redundancy_active,
                "pressure_status": self.steering_result.hydraulic_pressure_status,
                "reservoir_ok": self.steering_result.reservoir_level_ok,
            },
            "quick_closing_valves": {
                "status": self.quick_closing_result.valve_system_status,
                "air_pressure_ok": self.quick_closing_result.control_air_pressure_ok,
                "speed_compliant": self.quick_closing_result.closure_speed_compliant,
                "completeness_pct": self.quick_closing_result.closure_completeness_pct,
                "accumulator_ok": self.quick_closing_result.accumulator_capacity_ok,
            },
            "scavenge_air_fire": {
                "hazard_status": self.scavenge_result.fire_hazard_status,
                "temp_margin_c": self.scavenge_result.temperature_margin_c,
                "slowdown_demanded": self.scavenge_result.engine_slowdown_demanded,
                "fouling_level": self.scavenge_result.unburnt_oil_fouling_level,
                "smothering_ready": self.scavenge_result.smothering_medium_ready,
            },
            "total_warnings": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeSafetyPropulsionControlEngine:
    """Central engine orchestrating Maritime Phases 395-398."""

    def __init__(self):
        self.fire_pump_engine = EmergencyFirePumpEngine()
        self.steering_engine = SteeringGearEngine()
        self.quick_closing_engine = QuickClosingValveEngine()
        self.scavenge_engine = ScavengeFireEngine()

    def evaluate(
        self,
        pump_inp: EmergencyFirePumpInput = EmergencyFirePumpInput(),
        steering_inp: SteeringGearInput = SteeringGearInput(),
        qc_inp: QuickClosingValveInput = QuickClosingValveInput(),
        scav_inp: ScavengeFireInput = ScavengeFireInput(),
    ) -> MaritimeSafetyPropulsionControlResult:
        pump_res = self.fire_pump_engine.evaluate(pump_inp)
        steer_res = self.steering_engine.evaluate(steering_inp)
        qc_res = self.quick_closing_engine.evaluate(qc_inp)
        scav_res = self.scavenge_engine.evaluate(scav_inp)

        warnings = (
            pump_res.warnings
            + steer_res.warnings
            + qc_res.warnings
            + scav_res.warnings
        )

        critical_conditions = (
            pump_res.pump_operational_status == "CRITICAL_DEFECT_NOT_SEAWORTHY"
            or steer_res.steering_readiness_status in ("CRITICAL_STEERING_FAILURE", "NON_COMPLIANT_NAVIGATION_HAZARD")
            or qc_res.valve_system_status == "CRITICAL_ISOLATION_FAILURE"
            or scav_res.fire_hazard_status == "SCAVENGE_FIRE_ACTIVE"
        )

        degraded_conditions = (
            pump_res.pump_operational_status == "DEGRADED_AUTONOMY_DEFICIT"
            or steer_res.steering_readiness_status == "DEGRADED_OPERATIONAL_MODE"
            or qc_res.valve_system_status == "DEGRADED_ACTUATION_SYSTEM"
            or scav_res.fire_hazard_status == "ELEVATED_PRE_FIRE_ALARM"
        )

        if critical_conditions:
            overall = "CRITICAL_MARITIME_HAZARD"
        elif degraded_conditions:
            overall = "DEGRADED_OPERATIONAL_ALERT"
        else:
            overall = "SEAWORTHY_NOMINAL_OPTIMAL"

        return MaritimeSafetyPropulsionControlResult(
            fire_pump_result=pump_res,
            steering_result=steer_res,
            quick_closing_result=qc_res,
            scavenge_result=scav_res,
            overall_maritime_safety_status=overall,
            aggregated_warnings=warnings,
        )
