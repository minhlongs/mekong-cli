"""Master Maritime Facade for Phases 443-446:
- Phase 443: Cargo Tank Deepwell Submerged Pump Hydraulic Header & Stripping Interlock
- Phase 444: Nitrogen PSA Inert Gas Membrane Purity & Low-Pressure Buffer Interlock
- Phase 445: Cargo Hold Toxic H2S Gas Detection & Vapor Extraction Fan Safety
- Phase 446: Double-Bottom Fuel Tank Emergency High-Level Radar Overfill Protection
"""

from dataclasses import dataclass
from typing import Dict, Any, List

from src.core.maritime.phase_443_cargo_deepwell_hydraulic_stripping import (
    DeepwellPumpEngine,
    DeepwellPumpTelemetry,
    DeepwellPumpAssessment,
)
from src.core.maritime.phase_444_nitrogen_psa_membrane_purity import (
    NitrogenPsaEngine,
    NitrogenPsaTelemetry,
    NitrogenPsaAssessment,
)
from src.core.maritime.phase_445_cargo_hold_h2s_extraction_fan import (
    ToxicGasExtractionEngine,
    ToxicGasExtractionTelemetry,
    ToxicGasExtractionAssessment,
)
from src.core.maritime.phase_446_double_bottom_radar_overfill import (
    TankOverfillEngine,
    TankOverfillTelemetry,
    TankOverfillAssessment,
)


@dataclass(frozen=True)
class MaritimeCargoSafetyAssessment:
    overall_safe: bool
    deepwell: DeepwellPumpAssessment
    nitrogen_psa: NitrogenPsaAssessment
    toxic_extraction: ToxicGasExtractionAssessment
    tank_overfill: TankOverfillAssessment
    aggregated_critical_alarms: List[str]


class MaritimeCargoSafetyFacade:
    def __init__(self) -> None:
        self.deepwell_engine = DeepwellPumpEngine()
        self.psa_engine = NitrogenPsaEngine()
        self.gas_engine = ToxicGasExtractionEngine()
        self.overfill_engine = TankOverfillEngine()

    def evaluate_all(
        self,
        deepwell_data: DeepwellPumpTelemetry,
        psa_data: NitrogenPsaTelemetry,
        gas_data: ToxicGasExtractionTelemetry,
        overfill_data: TankOverfillTelemetry,
        tank_capacity_m3: float = 500.0,
    ) -> MaritimeCargoSafetyAssessment:
        dw_res = self.deepwell_engine.evaluate(deepwell_data)
        psa_res = self.psa_engine.evaluate(psa_data)
        gas_res = self.gas_engine.evaluate(gas_data)
        of_res = self.overfill_engine.evaluate(overfill_data, tank_total_capacity_m3=tank_capacity_m3)

        all_safe = dw_res.is_safe and psa_res.is_safe and gas_res.is_safe and of_res.is_safe

        criticals = [
            alarm for alarm in (
                dw_res.active_alarms + psa_res.active_alarms +
                gas_res.active_alarms + of_res.active_alarms
            ) if "CRITICAL" in alarm
        ]

        return MaritimeCargoSafetyAssessment(
            overall_safe=all_safe,
            deepwell=dw_res,
            nitrogen_psa=psa_res,
            toxic_extraction=gas_res,
            tank_overfill=of_res,
            aggregated_critical_alarms=criticals,
        )
