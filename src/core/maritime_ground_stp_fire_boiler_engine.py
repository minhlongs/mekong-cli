"""Master Integration Facade: Maritime Automation Phases 435-438.

Coordinates:
- Phase 435: Marine Shaft Grounding Earthing Device (SEAD) & Slip Ring Potential Drop
- Phase 436: Sewage Treatment Plant (STP) Membrane Bioreactor (MBR) Effluent Quality
- Phase 437: Emergency Fire Pump Independent Suction & Priming Interlock
- Phase 438: Marine Auxiliary Boiler Water Chemical Dosing & Phosphate/Hydrazine Matrix
Strictly < 130 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.core.maritime.phase_435_shaft_grounding_earthing_device import (
    ShaftEarthingEngine,
    ShaftEarthingTelemetry,
    ShaftEarthingAssessment,
)
from src.core.maritime.phase_436_stp_membrane_bioreactor_effluent import (
    StpEffluentEngine,
    StpEffluentTelemetry,
    StpEffluentAssessment,
)
from src.core.maritime.phase_437_emergency_fire_pump_priming import (
    EmergencyFirePumpEngine,
    EmergencyFirePumpTelemetry,
    EmergencyFirePumpAssessment,
)
from src.core.maritime.phase_438_boiler_water_chemical_dosing import (
    BoilerWaterEngine,
    BoilerWaterTelemetry,
    BoilerWaterAssessment,
)


@dataclass(frozen=True)
class MaritimePhases435To438Summary:
    """Consolidated assessment across shaft earthing, STP effluent, fire pump, and boiler water."""
    shaft_earthing: ShaftEarthingAssessment
    stp_effluent: StpEffluentAssessment
    emergency_fire_pump: EmergencyFirePumpAssessment
    boiler_water: BoilerWaterAssessment
    overall_seaworthiness: bool
    critical_alarms_count: int
    system_readiness: Dict[str, str]


class MaritimeGroundStpFireBoilerMasterEngine:
    """Orchestrates comprehensive safety and environmental compliance for Phases 435-438."""

    def __init__(self) -> None:
        self.shaft_engine = ShaftEarthingEngine()
        self.stp_engine = StpEffluentEngine()
        self.fire_engine = EmergencyFirePumpEngine()
        self.boiler_engine = BoilerWaterEngine()

    def evaluate_all(
        self,
        shaft_telemetry: ShaftEarthingTelemetry,
        stp_telemetry: StpEffluentTelemetry,
        fire_telemetry: EmergencyFirePumpTelemetry,
        boiler_telemetry: BoilerWaterTelemetry,
    ) -> MaritimePhases435To438Summary:
        shaft_res = self.shaft_engine.evaluate(shaft_telemetry)
        stp_res = self.stp_engine.evaluate(stp_telemetry)
        fire_res = self.fire_engine.evaluate(fire_telemetry)
        boiler_res = self.boiler_engine.evaluate(boiler_telemetry)

        critical_count = 0
        if not shaft_res.earthing_healthy:
            critical_count += 1
        if stp_res.divert_to_holding_tank:
            critical_count += 1
        if not fire_res.pump_operational_ready:
            critical_count += 1
        if boiler_res.seawater_contamination or boiler_res.blowdown_required:
            critical_count += 1

        seaworthiness = (
            shaft_res.earthing_healthy
            and fire_res.pump_operational_ready
            and not boiler_res.seawater_contamination
        )

        readiness = {
            "SHAFT_EARTHING": shaft_res.status,
            "STP_MBR_EFFLUENT": stp_res.status,
            "EMERGENCY_FIRE_PUMP": fire_res.status,
            "BOILER_CHEMISTRY": boiler_res.status,
        }

        return MaritimePhases435To438Summary(
            shaft_earthing=shaft_res,
            stp_effluent=stp_res,
            emergency_fire_pump=fire_res,
            boiler_water=boiler_res,
            overall_seaworthiness=seaworthiness,
            critical_alarms_count=critical_count,
            system_readiness=readiness,
        )
