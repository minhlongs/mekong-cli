"""Maritime Safety Auxiliary Batch 10 Coordinator Engine (Phases 499-502).
Aggregates Turbocharger Surge, Fresh Water Generator, CO2 Flooding, and Fuel Viscometer.
Strictly < 90 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_499_turbocharger_overspeed_surge import (
    TurbochargerAssessment, TurbochargerOverspeedSurgeEngine, TurbochargerTelemetry,
)
from src.core.maritime.phase_500_fresh_water_generator_salinity import (
    FreshWaterGeneratorSalinityEngine, FwgAssessment, FwgTelemetry,
)
from src.core.maritime.phase_501_co2_total_flooding_interlock import (
    Co2FloodingAssessment, Co2FloodingTelemetry, Co2TotalFloodingInterlockEngine,
)
from src.core.maritime.phase_502_fuel_oil_viscometer_heater import (
    FuelOilViscometerHeaterEngine, FuelViscometerAssessment, FuelViscometerTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch10Assessment:
    tc_assessment: TurbochargerAssessment
    fwg_assessment: FwgAssessment
    co2_assessment: Co2FloodingAssessment
    viscometer_assessment: FuelViscometerAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch10Engine:
    @classmethod
    def evaluate_batch10(
        cls,
        tc: TurbochargerTelemetry,
        fwg: FwgTelemetry,
        co2: Co2FloodingTelemetry,
        visc: FuelViscometerTelemetry,
    ) -> MaritimeAuxiliaryBatch10Assessment:
        res_tc = TurbochargerOverspeedSurgeEngine.evaluate(tc)
        res_fwg = FreshWaterGeneratorSalinityEngine.evaluate(fwg)
        res_co2 = Co2TotalFloodingInterlockEngine.evaluate(co2)
        res_visc = FuelOilViscometerHeaterEngine.evaluate(visc)

        alarms: List[str] = []
        if res_tc.alarm_active:
            alarms.append(f"TC: {res_tc.alarm_code}")
        if res_fwg.alarm_active:
            alarms.append(f"FWG: {res_fwg.alarm_code}")
        if res_co2.alarm_active:
            alarms.append(f"CO2: {res_co2.alarm_code}")
        if res_visc.alarm_active:
            alarms.append(f"VISC: {res_visc.alarm_code}")

        overall_safe = (
            not res_tc.alarm_active
            and not res_fwg.alarm_active
            and not res_co2.alarm_active
            and not res_visc.alarm_active
        )

        return MaritimeAuxiliaryBatch10Assessment(
            tc_assessment=res_tc,
            fwg_assessment=res_fwg,
            co2_assessment=res_co2,
            viscometer_assessment=res_visc,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
