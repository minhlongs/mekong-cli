from dataclasses import dataclass

from src.core.maritime.phase_551_cpp_controllable_pitch_propeller_servo_interlock import (
    CppPropellerServoAssessment,
    CppPropellerServoEngine,
    CppPropellerServoState,
    CppPropellerServoTelemetry,
)
from src.core.maritime.phase_552_cargo_reliquefaction_boil_off_gcu_interlock import (
    CargoReliqBoilOffGcuAssessment,
    CargoReliqBoilOffGcuEngine,
    CargoReliqBoilOffGcuState,
    CargoReliqBoilOffGcuTelemetry,
)
from src.core.maritime.phase_553_engine_room_local_water_mist_fwla_interlock import (
    EngineRoomLocalWaterMistFwlaEngine,
    LocalWaterMistFwlaAssessment,
    LocalWaterMistFwlaState,
    LocalWaterMistFwlaTelemetry,
)
from src.core.maritime.phase_554_rudder_roll_fin_stabilizer_zero_speed_interlock import (
    FinStabilizerHousingAssessment,
    FinStabilizerHousingEngine,
    FinStabilizerHousingState,
    FinStabilizerHousingTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch23Assessment:
    cpp_servo: CppPropellerServoAssessment
    cargo_reliq_gcu: CargoReliqBoilOffGcuAssessment
    local_water_mist: LocalWaterMistFwlaAssessment
    fin_stabilizer: FinStabilizerHousingAssessment
    any_critical_interlock_active: bool


class MaritimeSafetyAuxiliaryBatch23Engine:
    """Unified coordinator for Maritime Auxiliary Automation Batch 23 (Phases 551-554)."""

    @classmethod
    def evaluate_batch(
        cls,
        cpp: CppPropellerServoTelemetry,
        reliq: CargoReliqBoilOffGcuTelemetry,
        fwla: LocalWaterMistFwlaTelemetry,
        fin: FinStabilizerHousingTelemetry,
    ) -> MaritimeAuxiliaryBatch23Assessment:
        c_res = CppPropellerServoEngine.evaluate(cpp)
        r_res = CargoReliqBoilOffGcuEngine.evaluate(reliq)
        w_res = EngineRoomLocalWaterMistFwlaEngine.evaluate(fwla)
        f_res = FinStabilizerHousingEngine.evaluate(fin)
        crit = (
            c_res.state != CppPropellerServoState.CPP_PITCH_CONTROL_NOMINAL
            or r_res.state != CargoReliqBoilOffGcuState.RELIQ_BOG_PRESSURE_NOMINAL
            or w_res.state != LocalWaterMistFwlaState.FWLA_SYSTEM_ARMED_STANDBY
            or f_res.state != FinStabilizerHousingState.FIN_ACTIVE_ROLL_DAMPING_NOMINAL
        )
        return MaritimeAuxiliaryBatch23Assessment(c_res, r_res, w_res, f_res, crit)
