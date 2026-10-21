"""Maritime Safety Auxiliary Batch 20 Coordinator Engine (Phases 539-542).
Aggregates Piston Rod Stuffing Box, BESS Thermal Runaway, Dry Chemical Powder, and Common-Rail Booster.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_539_piston_rod_stuffing_box_drain import (
    PistonRodStuffingBoxDrainEngine, StuffingBoxDrainAssessment, StuffingBoxDrainTelemetry,
)
from src.core.maritime.phase_540_bess_thermal_runaway_offgas_interlock import (
    BessThermalRunawayAssessment, BessThermalRunawayOffgasEngine, BessThermalRunawayTelemetry,
)
from src.core.maritime.phase_541_dry_chemical_powder_nitrogen_interlock import (
    DryChemicalPowderNitrogenEngine, DryPowderSystemAssessment, DryPowderSystemTelemetry,
)
from src.core.maritime.phase_542_common_rail_fuel_booster_interlock import (
    CommonRailBoosterAssessment, CommonRailBoosterTelemetry, CommonRailFuelBoosterEngine,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch20Assessment:
    stuffing_box_assessment: StuffingBoxDrainAssessment
    bess_thermal_assessment: BessThermalRunawayAssessment
    dry_powder_assessment: DryPowderSystemAssessment
    common_rail_assessment: CommonRailBoosterAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch20Engine:
    @classmethod
    def evaluate_batch20(
        cls,
        stuffing_box: StuffingBoxDrainTelemetry,
        bess_thermal: BessThermalRunawayTelemetry,
        dry_powder: DryPowderSystemTelemetry,
        common_rail: CommonRailBoosterTelemetry,
    ) -> MaritimeAuxiliaryBatch20Assessment:
        res_sb = PistonRodStuffingBoxDrainEngine.evaluate(stuffing_box)
        res_bess = BessThermalRunawayOffgasEngine.evaluate(bess_thermal)
        res_dcp = DryChemicalPowderNitrogenEngine.evaluate(dry_powder)
        res_cr = CommonRailFuelBoosterEngine.evaluate(common_rail)

        alarms: List[str] = []
        if res_sb.interlock_code != "NONE":
            alarms.append(f"STUFFING_BOX: {res_sb.interlock_code}")
        if res_bess.interlock_code != "NONE":
            alarms.append(f"BESS_THERMAL: {res_bess.interlock_code}")
        if res_dcp.interlock_code != "NONE":
            alarms.append(f"DRY_POWDER: {res_dcp.interlock_code}")
        if res_cr.interlock_code != "NONE":
            alarms.append(f"COMMON_RAIL: {res_cr.interlock_code}")

        return MaritimeAuxiliaryBatch20Assessment(
            stuffing_box_assessment=res_sb,
            bess_thermal_assessment=res_bess,
            dry_powder_assessment=res_dcp,
            common_rail_assessment=res_cr,
            overall_safe=len(alarms) == 0,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
