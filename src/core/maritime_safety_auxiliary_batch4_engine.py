"""Master Maritime Safety Auxiliary Systems Coordinator (Phases 475-478).

Aggregates:
- Phase 475: Stern Tube L.O. Forward/Aft Seal Temperature & Air Barrier DP Interlock
- Phase 476: Deck Nitrogen Generator Membrane Separation & O2 Analyzer Interlock
- Phase 477: Main Engine Scavenge Air Manifold Relief Valve & Fire Snuffing System
- Phase 478: Ballast Water Management System (BWMS) UV Reactor Transmittance & Dose Interlock

Strictly < 95 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass

from src.core.maritime.phase_475_stern_tube_seal_interlock import (
    SternTubeSealAssessment,
    SternTubeSealInterlockEngine,
    SternTubeSealStatus,
    SternTubeSealTelemetry,
)
from src.core.maritime.phase_476_nitrogen_generator_interlock import (
    NitrogenGeneratorAssessment,
    NitrogenGeneratorSafetyEngine,
    NitrogenGeneratorStatus,
    NitrogenGeneratorTelemetry,
)
from src.core.maritime.phase_477_scavenge_air_relief_fire_snuffing import (
    ScavengeFireAssessment,
    ScavengeFireSafetyEngine,
    ScavengeFireStatus,
    ScavengeFireTelemetry,
)
from src.core.maritime.phase_478_bwms_uv_dose_transmittance import (
    BwmsUvAssessment,
    BwmsUvSafetyEngine,
    BwmsUvStatus,
    BwmsUvTelemetry,
)


@dataclass(frozen=True)
class MaritimePhases475to478Telemetry:
    stern_tube_seal: SternTubeSealTelemetry
    nitrogen_generator: NitrogenGeneratorTelemetry
    scavenge_fire: ScavengeFireTelemetry
    bwms_uv: BwmsUvTelemetry


@dataclass(frozen=True)
class MaritimePhases475to478Assessment:
    overall_safe: bool
    stern_tube_seal_res: SternTubeSealAssessment
    nitrogen_generator_res: NitrogenGeneratorAssessment
    scavenge_fire_res: ScavengeFireAssessment
    bwms_uv_res: BwmsUvAssessment
    active_alarms_count: int


class MaritimeSafetyAuxiliaryBatch4Engine:
    @classmethod
    def evaluate(
        cls, telemetry: MaritimePhases475to478Telemetry
    ) -> MaritimePhases475to478Assessment:
        st_eval = SternTubeSealInterlockEngine.evaluate(telemetry.stern_tube_seal)
        ng_eval = NitrogenGeneratorSafetyEngine.evaluate(telemetry.nitrogen_generator)
        sf_eval = ScavengeFireSafetyEngine.evaluate(telemetry.scavenge_fire)
        uv_eval = BwmsUvSafetyEngine.evaluate(telemetry.bwms_uv)

        alarms = 0
        if st_eval.status != SternTubeSealStatus.NORMAL:
            alarms += 1
        if ng_eval.status != NitrogenGeneratorStatus.NORMAL:
            alarms += 1
        if sf_eval.status != ScavengeFireStatus.NORMAL:
            alarms += 1
        if uv_eval.status != BwmsUvStatus.NORMAL:
            alarms += 1

        overall_safe = (
            not st_eval.propulsion_slowdown_tripped
            and not sf_eval.fuel_rack_cutoff_command
            and not sf_eval.explosion_relief_open
            and (uv_eval.status != BwmsUvStatus.INSUFFICIENT_DOSE_BALLAST_TRIP)
        )

        return MaritimePhases475to478Assessment(
            overall_safe=overall_safe,
            stern_tube_seal_res=st_eval,
            nitrogen_generator_res=ng_eval,
            scavenge_fire_res=sf_eval,
            bwms_uv_res=uv_eval,
            active_alarms_count=alarms,
        )
