"""Maritime Safety Auxiliary Batch 9 Coordinator Engine (Phases 495-498).
Aggregates OWS, Crankcase OMD, Boiler Water Level, and Emergency Fire Pump.
Strictly < 95 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_495_ows_15ppm_bilge_alarm import (
    Ows15PpmBilgeAlarmEngine, OwsAssessment, OwsTelemetry,
)
from src.core.maritime.phase_496_crankcase_oil_mist_detector import (
    CrankcaseOilMistDetectorEngine, OilMistAssessment, OilMistTelemetry,
)
from src.core.maritime.phase_497_boiler_water_level_fuel_cutoff import (
    BoilerWaterAssessment, BoilerWaterLevelFuelCutoffEngine, BoilerWaterTelemetry,
)
from src.core.maritime.phase_498_emergency_fire_pump_priming import (
    EmergencyFirePumpPrimingEngine, FirePumpAssessment, FirePumpTelemetry,
)

@dataclass(frozen=True)
class MaritimeAuxiliaryBatch9Assessment:
    ows_assessment: OwsAssessment
    omd_assessment: OilMistAssessment
    boiler_assessment: BoilerWaterAssessment
    fire_pump_assessment: FirePumpAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]

class MaritimeSafetyAuxiliaryBatch9Engine:
    @classmethod
    def evaluate_batch9(
        cls,
        ows: OwsTelemetry,
        omd: OilMistTelemetry,
        boiler: BoilerWaterTelemetry,
        fire: FirePumpTelemetry,
    ) -> MaritimeAuxiliaryBatch9Assessment:
        res_ows = Ows15PpmBilgeAlarmEngine.evaluate(ows)
        res_omd = CrankcaseOilMistDetectorEngine.evaluate(omd)
        res_boiler = BoilerWaterLevelFuelCutoffEngine.evaluate(boiler)
        res_fire = EmergencyFirePumpPrimingEngine.evaluate(fire)

        alarms: List[str] = []
        if res_ows.alarm_active:
            alarms.append(f"OWS: {res_ows.alarm_reason}")
        if res_omd.alarm_active:
            alarms.append(f"OMD: {res_omd.alarm_code}")
        if res_boiler.alarm_active:
            alarms.append(f"BOILER: {res_boiler.alarm_code}")
        if res_fire.alarm_active:
            alarms.append(f"FIRE_PUMP: {res_fire.alarm_code}")

        overall_safe = (
            not res_omd.explosion_risk_critical
            and res_boiler.burner_state.value == "FIRING_ALLOWED"
            and not res_fire.alarm_active
            and not res_ows.alarm_active
        )

        return MaritimeAuxiliaryBatch9Assessment(
            ows_assessment=res_ows,
            omd_assessment=res_omd,
            boiler_assessment=res_boiler,
            fire_pump_assessment=res_fire,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
