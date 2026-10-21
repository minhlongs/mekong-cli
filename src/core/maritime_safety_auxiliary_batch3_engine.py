"""Master Maritime Safety Auxiliary Systems Coordinator (Phases 471-474).

Aggregates:
- Phase 471: Tunnel Bow Thruster Hydraulic Pitch & Generator Overload Interlock
- Phase 472: Emergency Fire Pump Sea Suction Priming & Head Protection
- Phase 473: Engine Crankcase Oil Mist Optical Detector & Auto Slowdown Interlock
- Phase 474: Exhaust Gas Scrubber Washwater Effluent pH & PAH Environmental Safety

Strictly < 90 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass

from src.core.maritime.phase_471_bow_thruster_interlock import (
    BowThrusterAssessment,
    BowThrusterInterlockEngine,
    BowThrusterStatus,
    BowThrusterTelemetry,
)
from src.core.maritime.phase_472_emergency_fire_pump_sea_suction import (
    EmergencyFirePumpAssessment,
    EmergencyFirePumpSafetyEngine,
    EmergencyFirePumpStatus,
    EmergencyFirePumpTelemetry,
)
from src.core.maritime.phase_473_crankcase_oil_mist_optical_detector import (
    OilMistAssessment,
    OilMistDetectorEngine,
    OilMistStatus,
    OilMistTelemetry,
)
from src.core.maritime.phase_474_scrubber_effluent_ph_polycyclic_aromatic import (
    ScrubberEffluentAssessment,
    ScrubberEffluentSafetyEngine,
    ScrubberEffluentStatus,
    ScrubberEffluentTelemetry,
)


@dataclass(frozen=True)
class MaritimePhases471to474Telemetry:
    bow_thruster: BowThrusterTelemetry
    emergency_fire_pump: EmergencyFirePumpTelemetry
    oil_mist: OilMistTelemetry
    scrubber_effluent: ScrubberEffluentTelemetry


@dataclass(frozen=True)
class MaritimePhases471to474Assessment:
    overall_safe: bool
    bow_thruster_res: BowThrusterAssessment
    emergency_fire_pump_res: EmergencyFirePumpAssessment
    oil_mist_res: OilMistAssessment
    scrubber_effluent_res: ScrubberEffluentAssessment
    active_alarms_count: int


class MaritimeSafetyAuxiliaryBatch3Engine:
    @classmethod
    def evaluate(
        cls, telemetry: MaritimePhases471to474Telemetry
    ) -> MaritimePhases471to474Assessment:
        bt_eval = BowThrusterInterlockEngine.evaluate(telemetry.bow_thruster)
        efp_eval = EmergencyFirePumpSafetyEngine.evaluate(telemetry.emergency_fire_pump)
        om_eval = OilMistDetectorEngine.evaluate(telemetry.oil_mist)
        sc_eval = ScrubberEffluentSafetyEngine.evaluate(telemetry.scrubber_effluent)

        alarms = 0
        if bt_eval.status != BowThrusterStatus.NORMAL:
            alarms += 1
        if efp_eval.status != EmergencyFirePumpStatus.NORMAL:
            alarms += 1
        if om_eval.status != OilMistStatus.NORMAL:
            alarms += 1
        if sc_eval.status != ScrubberEffluentStatus.NORMAL:
            alarms += 1

        overall_safe = (
            bt_eval.thruster_run_permissive
            and not om_eval.engine_slowdown_tripped
            and not sc_eval.holding_tank_diversion_valve_open
        )

        return MaritimePhases471to474Assessment(
            overall_safe=overall_safe,
            bow_thruster_res=bt_eval,
            emergency_fire_pump_res=efp_eval,
            oil_mist_res=om_eval,
            scrubber_effluent_res=sc_eval,
            active_alarms_count=alarms,
        )
