"""Master Facade: Maritime Phases 451-454 Unified Automation Engine.

Integrates:
- Phase 451: EGR Water Treatment System & Sludge Centrifuge
- Phase 452: Cargo Tank High-Velocity P/V Valve & Deflagration Screen
- Phase 453: Marine Sewage Vacuum Collection System
- Phase 454: Waste Heat Recovery (WHR) ORC Evaporator Safety
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_451_egr_water_treatment_system import (
    EgrWaterTreatmentEngine,
    EgrWtsTelemetry,
    EgrWtsAssessment,
)
from src.core.maritime.phase_452_cargo_tank_high_velocity_pv_valve import (
    CargoPvValveEngine,
    PvValveTelemetry,
    PvValveAssessment,
)
from src.core.maritime.phase_453_marine_sewage_vacuum_collection import (
    SewageVacuumSystemEngine,
    SewageVacuumTelemetry,
    SewageVacuumAssessment,
)
from src.core.maritime.phase_454_waste_heat_recovery_orc_evaporator import (
    WhrOrcEvaporatorEngine,
    OrcEvaporatorTelemetry,
    OrcEvaporatorAssessment,
)


@dataclass(frozen=True)
class MaritimePhases451to454Assessment:
    egr_wts: EgrWtsAssessment
    pv_valve: PvValveAssessment
    sewage_vacuum: SewageVacuumAssessment
    orc_evaporator: OrcEvaporatorAssessment
    overall_all_clear: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "egr_wts_status": self.egr_wts.status.value,
            "pv_valve_status": self.pv_valve.status.value,
            "sewage_vacuum_status": self.sewage_vacuum.status.value,
            "orc_evaporator_status": self.orc_evaporator.status.value,
            "overall_all_clear": self.overall_all_clear,
        }


class MaritimeEgrPvVacuumOrcEngine:
    @staticmethod
    def evaluate_all(
        egr_telemetry: EgrWtsTelemetry,
        pv_telemetry: PvValveTelemetry,
        sewage_telemetry: SewageVacuumTelemetry,
        orc_telemetry: OrcEvaporatorTelemetry,
    ) -> MaritimePhases451to454Assessment:
        egr_res = EgrWaterTreatmentEngine.evaluate(egr_telemetry)
        pv_res = CargoPvValveEngine.evaluate(pv_telemetry)
        sewage_res = SewageVacuumSystemEngine.evaluate(sewage_telemetry)
        orc_res = WhrOrcEvaporatorEngine.evaluate(orc_telemetry)

        all_clear = not (
            egr_res.sludge_holding_alarm
            or pv_res.safety_alarm
            or sewage_res.alarm_active
            or orc_res.safety_alarm
        )

        return MaritimePhases451to454Assessment(
            egr_wts=egr_res,
            pv_valve=pv_res,
            sewage_vacuum=sewage_res,
            orc_evaporator=orc_res,
            overall_all_clear=all_clear,
        )
