"""Master Facade for Maritime Phases 459-462 Propulsion & Cargo Auxiliary Safety Systems.

Integrates:
- Phase 459: Ballast Tank Stripping Eductor (IMO BWMC & IACS UR M62)
- Phase 460: Cargo Pump Room Gas Detection (SOLAS II-2 Reg 4.5.10.1.3 & IACS UR F35)
- Phase 461: CPP Emergency Pitch Control & Locking (SOLAS II-1 Reg 29 & DNV Pt. 4 Ch. 5)
- Phase 462: Intermediate Shaft Bearing Cooling (IACS UR M68 & Lloyd's Register Pt. 5 Ch. 2)
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_459_ballast_tank_stripping_eductor import (
    BallastTankStrippingEductorEngine,
    BallastEductorTelemetry,
    BallastEductorAssessment,
)
from src.core.maritime.phase_460_cargo_pump_room_gas_detection import (
    CargoPumpRoomGasDetectionEngine,
    PumpRoomGasTelemetry,
    PumpRoomGasAssessment,
)
from src.core.maritime.phase_461_controllable_pitch_propeller_emergency_pitch import (
    CppEmergencyPitchEngine,
    CppPitchTelemetry,
    CppPitchAssessment,
)
from src.core.maritime.phase_462_intermediate_shaft_bearing_cooling import (
    IntermediateShaftBearingEngine,
    ShaftBearingTelemetry,
    ShaftBearingAssessment,
)


@dataclass(frozen=True)
class MaritimePhases459To462UnifiedAssessment:
    ballast_eductor: BallastEductorAssessment
    pump_room_gas: PumpRoomGasAssessment
    cpp_emergency_pitch: CppPitchAssessment
    shaft_bearing: ShaftBearingAssessment
    all_systems_nominal: bool
    critical_shutdown_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_systems_nominal": self.all_systems_nominal,
            "critical_shutdown_active": self.critical_shutdown_active,
            "ballast_eductor_status": self.ballast_eductor.status.value,
            "pump_room_gas_status": self.pump_room_gas.status.value,
            "cpp_pitch_status": self.cpp_emergency_pitch.status.value,
            "shaft_bearing_status": self.shaft_bearing.status.value,
        }


class MaritimeAuxiliaryPropulsionMasterFacade:
    """Unified Facade for Maritime Phases 459-462."""

    @classmethod
    def evaluate_all(
        cls,
        eductor_telemetry: BallastEductorTelemetry,
        pumproom_telemetry: PumpRoomGasTelemetry,
        cpp_telemetry: CppPitchTelemetry,
        bearing_telemetry: ShaftBearingTelemetry,
    ) -> MaritimePhases459To462UnifiedAssessment:
        eductor_res = BallastTankStrippingEductorEngine.evaluate(eductor_telemetry)
        pumproom_res = CargoPumpRoomGasDetectionEngine.evaluate(pumproom_telemetry)
        cpp_res = CppEmergencyPitchEngine.evaluate(cpp_telemetry)
        bearing_res = IntermediateShaftBearingEngine.evaluate(bearing_telemetry)

        nominal = (
            not eductor_res.safety_alarm
            and not pumproom_res.safety_alarm
            and not cpp_res.safety_alarm
            and not bearing_res.safety_alarm
        )

        critical = (
            pumproom_res.pump_room_isolated
            or bearing_res.engine_slowdown_required
            or cpp_res.fail_as_is_engaged
        )

        return MaritimePhases459To462UnifiedAssessment(
            ballast_eductor=eductor_res,
            pump_room_gas=pumproom_res,
            cpp_emergency_pitch=cpp_res,
            shaft_bearing=bearing_res,
            all_systems_nominal=nominal,
            critical_shutdown_active=critical,
        )
