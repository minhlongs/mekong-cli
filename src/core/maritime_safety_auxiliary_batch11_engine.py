"""Maritime Safety Auxiliary Batch 11 Coordinator Engine (Phases 503-506).
Aggregates Hull ICCP, Sea Chest MGPS, Galley HVAC Fire Damper, and Provision Reefer Safety.
Strictly < 90 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_503_iccp_hull_potential_anode import (
    IccpAssessment, IccpHullPotentialAnodeEngine, IccpTelemetry,
)
from src.core.maritime.phase_504_mgps_sea_chest_dosing import (
    MgpsAssessment, MgpsSeaChestDosingEngine, MgpsTelemetry,
)
from src.core.maritime.phase_505_hvac_galley_fire_damper import (
    HvacGalleyAssessment, HvacGalleyFireDamperEngine, HvacGalleyTelemetry,
)
from src.core.maritime.phase_506_provision_reefer_leak_safety import (
    ProvisionReeferAssessment, ProvisionReeferLeakSafetyEngine, ProvisionReeferTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch11Assessment:
    iccp_assessment: IccpAssessment
    mgps_assessment: MgpsAssessment
    hvac_assessment: HvacGalleyAssessment
    reefer_assessment: ProvisionReeferAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch11Engine:
    @classmethod
    def evaluate_batch11(
        cls,
        iccp: IccpTelemetry,
        mgps: MgpsTelemetry,
        hvac: HvacGalleyTelemetry,
        reefer: ProvisionReeferTelemetry,
    ) -> MaritimeAuxiliaryBatch11Assessment:
        res_iccp = IccpHullPotentialAnodeEngine.evaluate(iccp)
        res_mgps = MgpsSeaChestDosingEngine.evaluate(mgps)
        res_hvac = HvacGalleyFireDamperEngine.evaluate(hvac)
        res_reefer = ProvisionReeferLeakSafetyEngine.evaluate(reefer)

        alarms: List[str] = []
        if res_iccp.alarm_active:
            alarms.append(f"ICCP: {res_iccp.alarm_code}")
        if res_mgps.alarm_active:
            alarms.append(f"MGPS: {res_mgps.alarm_code}")
        if res_hvac.alarm_active:
            alarms.append(f"HVAC: {res_hvac.alarm_code}")
        if res_reefer.alarm_active:
            alarms.append(f"REEFER: {res_reefer.alarm_code}")

        overall_safe = (
            not res_iccp.alarm_active
            and not res_mgps.alarm_active
            and not res_hvac.alarm_active
            and not res_reefer.alarm_active
        )

        return MaritimeAuxiliaryBatch11Assessment(
            iccp_assessment=res_iccp,
            mgps_assessment=res_mgps,
            hvac_assessment=res_hvac,
            reefer_assessment=res_reefer,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
