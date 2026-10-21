from dataclasses import dataclass

from src.core.maritime.phase_543_scr_urea_ammonia_slip_interlock import (
    ScrUreaAmmoniaSlipEngine,
    ScrUreaDosingAssessment,
    ScrUreaDosingState,
    ScrUreaDosingTelemetry,
)
from src.core.maritime.phase_544_cargo_tank_pv_breaker_mast_interlock import (
    CargoPvBreakerMastAssessment,
    CargoPvBreakerMastState,
    CargoPvBreakerMastTelemetry,
    CargoTankPvBreakerMastEngine,
)
from src.core.maritime.phase_545_azipod_slewing_seal_stator_interlock import (
    AzipodPropulsorAssessment,
    AzipodPropulsorState,
    AzipodPropulsorTelemetry,
    AzipodSlewingSealStatorEngine,
)
from src.core.maritime.phase_546_lng_esd_drybreak_erc_interlock import (
    LngEsdDrybreakErcEngine,
    LngEsdErcAssessment,
    LngEsdErcState,
    LngEsdErcTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch21Assessment:
    scr_urea: ScrUreaDosingAssessment
    cargo_pv_breaker: CargoPvBreakerMastAssessment
    azipod_propulsor: AzipodPropulsorAssessment
    lng_esd_erc: LngEsdErcAssessment
    any_critical_interlock_active: bool


class MaritimeSafetyAuxiliaryBatch21Engine:
    """Unified coordinator for Maritime Auxiliary Automation Batch 21 (Phases 543-546)."""

    @classmethod
    def evaluate_batch(
        cls,
        scr: ScrUreaDosingTelemetry,
        pv_breaker: CargoPvBreakerMastTelemetry,
        azipod: AzipodPropulsorTelemetry,
        lng_esd: LngEsdErcTelemetry,
    ) -> MaritimeAuxiliaryBatch21Assessment:
        s_res = ScrUreaAmmoniaSlipEngine.evaluate(scr)
        p_res = CargoTankPvBreakerMastEngine.evaluate(pv_breaker)
        a_res = AzipodSlewingSealStatorEngine.evaluate(azipod)
        l_res = LngEsdDrybreakErcEngine.evaluate(lng_esd)
        crit = (
            s_res.state != ScrUreaDosingState.TIER_III_SCR_DOSING_ACTIVE
            or p_res.state != CargoPvBreakerMastState.NOMINAL_CARGO_TANK_PRESSURE_ENVELOPE
            or a_res.state != AzipodPropulsorState.OPTIMAL_AZIPOD_OPERATION
            or l_res.state != LngEsdErcState.LNG_MANIFOLD_TRANSFER_NORMAL
        )
        return MaritimeAuxiliaryBatch21Assessment(s_res, p_res, a_res, l_res, crit)
