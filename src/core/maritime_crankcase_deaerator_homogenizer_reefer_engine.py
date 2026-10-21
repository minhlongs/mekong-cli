"""Master Facade: Maritime Phases 455-458 Unified Automation Engine.

Integrates:
- Phase 455: Crankcase Explosion Relief Valve & Flame Quenching Mesh
- Phase 456: Boiler Feedwater Deaerator & Dissolved Oxygen Scavenging
- Phase 457: Marine Fuel Oil Homogenizer Ultrasonic Viscosity Conditioning
- Phase 458: Marine Refrigerated Container Socket Monitoring & Earth Leakage
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_455_crankcase_explosion_relief_valve import (
    CrankcaseExplosionReliefEngine,
    CrankcaseValveTelemetry,
    CrankcaseValveAssessment,
)
from src.core.maritime.phase_456_boiler_feedwater_deaerator import (
    BoilerFeedwaterDeaeratorEngine,
    DeaeratorTelemetry,
    DeaeratorAssessment,
)
from src.core.maritime.phase_457_fuel_oil_homogenizer_viscosity import (
    FuelHomogenizerViscosityEngine,
    FuelHomogenizerTelemetry,
    FuelHomogenizerAssessment,
)
from src.core.maritime.phase_458_reefer_container_socket_protection import (
    ReeferContainerSocketEngine,
    ReeferSocketTelemetry,
    ReeferSocketAssessment,
)


@dataclass(frozen=True)
class MaritimePhases455to458Assessment:
    crankcase_valve: CrankcaseValveAssessment
    deaerator: DeaeratorAssessment
    fuel_homogenizer: FuelHomogenizerAssessment
    reefer_socket: ReeferSocketAssessment
    overall_all_clear: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crankcase_valve_status": self.crankcase_valve.status.value,
            "deaerator_status": self.deaerator.status.value,
            "fuel_homogenizer_status": self.fuel_homogenizer.status.value,
            "reefer_socket_status": self.reefer_socket.status.value,
            "overall_all_clear": self.overall_all_clear,
        }


class MaritimeCrankcaseDeaeratorHomogenizerReeferEngine:
    @staticmethod
    def evaluate_all(
        crankcase_telemetry: CrankcaseValveTelemetry,
        deaerator_telemetry: DeaeratorTelemetry,
        homogenizer_telemetry: FuelHomogenizerTelemetry,
        reefer_telemetry: ReeferSocketTelemetry,
    ) -> MaritimePhases455to458Assessment:
        crank_res = CrankcaseExplosionReliefEngine.evaluate(crankcase_telemetry)
        deaer_res = BoilerFeedwaterDeaeratorEngine.evaluate(deaerator_telemetry)
        homog_res = FuelHomogenizerViscosityEngine.evaluate(homogenizer_telemetry)
        reefer_res = ReeferContainerSocketEngine.evaluate(reefer_telemetry)

        all_clear = not (
            crank_res.safety_alarm
            or deaer_res.safety_alarm
            or homog_res.safety_alarm
            or reefer_res.safety_alarm
        )

        return MaritimePhases455to458Assessment(
            crankcase_valve=crank_res,
            deaerator=deaer_res,
            fuel_homogenizer=homog_res,
            reefer_socket=reefer_res,
            overall_all_clear=all_clear,
        )
