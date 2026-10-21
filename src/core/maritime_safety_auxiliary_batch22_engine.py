from dataclasses import dataclass

from src.core.maritime.phase_547_fgss_glycol_vaporizer_gvu_interlock import (
    FgssGlycolGvuAssessment,
    FgssGlycolGvuState,
    FgssGlycolGvuTelemetry,
    FgssGlycolVaporizerGvuEngine,
)
from src.core.maritime.phase_548_charge_air_cooler_condensate_interlock import (
    ChargeAirCondensateAssessment,
    ChargeAirCondensateState,
    ChargeAirCondensateTelemetry,
    ChargeAirCoolerCondensateEngine,
)
from src.core.maritime.phase_549_high_expansion_foam_generator_interlock import (
    HighExpansionFoamGeneratorEngine,
    HighExpFoamGeneratorAssessment,
    HighExpFoamGeneratorState,
    HighExpFoamGeneratorTelemetry,
)
from src.core.maritime.phase_550_dp_bus_tie_wcsf_redundancy_interlock import (
    DpBusTieRedundancyAssessment,
    DpBusTieRedundancyState,
    DpBusTieRedundancyTelemetry,
    DpBusTieWcsfRedundancyEngine,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch22Assessment:
    fgss_gvu: FgssGlycolGvuAssessment
    cac_condensate: ChargeAirCondensateAssessment
    high_exp_foam: HighExpFoamGeneratorAssessment
    dp_bus_tie: DpBusTieRedundancyAssessment
    any_critical_interlock_active: bool


class MaritimeSafetyAuxiliaryBatch22Engine:
    """Unified coordinator for Maritime Auxiliary Automation Batch 22 (Phases 547-550)."""

    @classmethod
    def evaluate_batch(
        cls,
        fgss: FgssGlycolGvuTelemetry,
        cac: ChargeAirCondensateTelemetry,
        foam: HighExpFoamGeneratorTelemetry,
        dp_bus: DpBusTieRedundancyTelemetry,
    ) -> MaritimeAuxiliaryBatch22Assessment:
        f_res = FgssGlycolVaporizerGvuEngine.evaluate(fgss)
        c_res = ChargeAirCoolerCondensateEngine.evaluate(cac)
        h_res = HighExpansionFoamGeneratorEngine.evaluate(foam)
        d_res = DpBusTieWcsfRedundancyEngine.evaluate(dp_bus)
        crit = (
            f_res.state != FgssGlycolGvuState.FGSS_GAS_SUPPLY_NOMINAL
            or c_res.state != ChargeAirCondensateState.CAC_CONDENSATE_DRAIN_OPTIMAL
            or h_res.state != HighExpFoamGeneratorState.HIGH_EXP_FOAM_DISCHARGE_ACTIVE
            or d_res.state != DpBusTieRedundancyState.DP_CLOSED_BUS_REDUNDANCY_GREEN
        )
        return MaritimeAuxiliaryBatch22Assessment(f_res, c_res, h_res, d_res, crit)
