"""Master Maritime Safety Auxiliary Systems Coordinator (Phases 479-482).

Aggregates:
- Phase 479: Cargo Hold Bilge Eductor & Flooding Detection Interlock (SOLAS XII/9)
- Phase 480: Turbocharger Auxiliary Blower & Surge Protection (IACS UR M9)
- Phase 481: Boiler Feedwater Deaerator & Condensate Salinity (IACS UR M14)
- Phase 482: Steering Gear Phase Failure & Hydraulic Auto-Isolation (SOLAS II-1/29)

Strictly < 95 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass

from src.core.maritime.phase_479_cargo_hold_bilge_eductor import (
    CargoHoldBilgeAssessment,
    CargoHoldBilgeEductorEngine,
    CargoHoldBilgeStatus,
    CargoHoldBilgeTelemetry,
)
from src.core.maritime.phase_480_turbocharger_aux_blower import (
    AuxBlowerAssessment,
    AuxBlowerStatus,
    AuxBlowerTelemetry,
    TurbochargerAuxBlowerEngine,
)
from src.core.maritime.phase_481_boiler_feedwater_deaerator import (
    BoilerFeedwaterAssessment,
    BoilerFeedwaterDeaeratorEngine,
    BoilerFeedwaterStatus,
    BoilerFeedwaterTelemetry,
)
from src.core.maritime.phase_482_steering_gear_phase_failure import (
    SteeringGearAssessment,
    SteeringGearSafetyEngine,
    SteeringGearStatus,
    SteeringGearTelemetry,
)


@dataclass(frozen=True)
class MaritimePhases479to482Telemetry:
    cargo_hold_bilge: CargoHoldBilgeTelemetry
    aux_blower: AuxBlowerTelemetry
    boiler_feedwater: BoilerFeedwaterTelemetry
    steering_gear: SteeringGearTelemetry


@dataclass(frozen=True)
class MaritimePhases479to482Assessment:
    overall_safe: bool
    cargo_hold_bilge_res: CargoHoldBilgeAssessment
    aux_blower_res: AuxBlowerAssessment
    boiler_feedwater_res: BoilerFeedwaterAssessment
    steering_gear_res: SteeringGearAssessment
    active_alarms_count: int


class MaritimeSafetyAuxiliaryBatch5Engine:
    @classmethod
    def evaluate(
        cls, telemetry: MaritimePhases479to482Telemetry
    ) -> MaritimePhases479to482Assessment:
        bilge_res = CargoHoldBilgeEductorEngine.evaluate(telemetry.cargo_hold_bilge)
        blower_res = TurbochargerAuxBlowerEngine.evaluate(telemetry.aux_blower)
        boiler_res = BoilerFeedwaterDeaeratorEngine.evaluate(telemetry.boiler_feedwater)
        steering_res = SteeringGearSafetyEngine.evaluate(telemetry.steering_gear)

        alarms = 0
        if bilge_res.status not in (CargoHoldBilgeStatus.NORMAL, CargoHoldBilgeStatus.PRE_ALARM):
            alarms += 1
        if blower_res.status in (AuxBlowerStatus.TC_SURGE_RELIEF_ACTIVE,):
            alarms += 1
        if boiler_res.status != BoilerFeedwaterStatus.NORMAL:
            alarms += 1
        if steering_res.status != SteeringGearStatus.NORMAL:
            alarms += 1

        overall_safe = (
            not bilge_res.flooding_alarm_active
            and not blower_res.surge_relief_bypass_open
            and not boiler_res.condensate_dump_valve_open
            and steering_res.steering_capable
        )

        return MaritimePhases479to482Assessment(
            overall_safe=overall_safe,
            cargo_hold_bilge_res=bilge_res,
            aux_blower_res=blower_res,
            boiler_feedwater_res=boiler_res,
            steering_gear_res=steering_res,
            active_alarms_count=alarms,
        )
