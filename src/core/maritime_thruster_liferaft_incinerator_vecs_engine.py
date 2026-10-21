"""Unified Facade for Maritime Phases 399-402 (Advanced Engineering AH).

Integrates:
- Phase 399: Marine Bow Thruster Thrust & Pitch Control (SOLAS II-1 Reg 29, DNV Pt.4 Ch.5)
- Phase 400: Inflatable Liferaft & HRU Float-Free Dynamics (SOLAS III, IMO LSA Code IV)
- Phase 401: Shipboard Waste High-Temp Incinerator (MARPOL Annex V, MEPC.244(66))
- Phase 402: Tanker Closed Vapor Emission Control System (IMO MSC/Circ.585, USCG 46 CFR 39)

Strictly zero mock dependencies, < 200 LOC.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.core.maritime.phase_399_bow_thruster_thrust_pitch import (
    BowThrusterEngine,
    BowThrusterInput,
    BowThrusterResult,
)
from src.core.maritime.phase_400_inflatable_liferaft_hru_release import (
    LiferaftHRUEngine,
    LiferaftHRUInput,
    LiferaftHRUResult,
)
from src.core.maritime.phase_401_waste_incinerator_gasification import (
    IncineratorEngine,
    IncineratorInput,
    IncineratorResult,
)
from src.core.maritime.phase_402_vapor_emission_control_vecs import (
    VECSEngine,
    VECSInput,
    VECSResult,
)


@dataclass
class MaritimeThrusterLiferaftIncineratorVECSResult:
    """Consolidated assessment of the 4 maritime auxiliary systems."""
    thruster_result: BowThrusterResult
    liferaft_result: LiferaftHRUResult
    incinerator_result: IncineratorResult
    vecs_result: VECSResult
    overall_system_status: str
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_system_status,
            "bow_thruster": {
                "thrust_kn": self.thruster_result.net_thrust_kn,
                "tip_speed_m_s": self.thruster_result.tip_speed_m_s,
                "cavitation_index": self.thruster_result.cavitation_index,
                "cavitation_status": self.thruster_result.cavitation_status.value,
                "power_kw": self.thruster_result.effective_power_kw,
                "motor_load_pct": self.thruster_result.motor_load_pct,
                "power_limit_active": self.thruster_result.power_limit_active,
                "interlock_status": self.thruster_result.interlock_status.value,
                "operational_permitted": self.thruster_result.operational_permitted,
            },
            "liferaft_hru": {
                "actuated": self.liferaft_result.hru_actuated,
                "actuation_state": self.liferaft_result.hru_actuation_state.value,
                "float_free_state": self.liferaft_result.float_free_state.value,
                "painter_compliant": self.liferaft_result.painter_length_compliant,
                "weak_link_parted": self.liferaft_result.weak_link_parted,
                "service_valid": self.liferaft_result.service_valid,
            },
            "waste_incinerator": {
                "status": self.incinerator_result.status.value,
                "charging_permitted": self.incinerator_result.waste_charging_permitted,
                "dioxin_destruction": self.incinerator_result.dioxin_destruction_verified,
                "emissions_compliant": self.incinerator_result.flue_emissions_compliant,
                "safety_trip": self.incinerator_result.safety_trip_active,
                "combustion_efficiency_pct": self.incinerator_result.combustion_efficiency_pct,
            },
            "vecs": {
                "pressure_status": self.vecs_result.pressure_status.value,
                "overfill_level": self.vecs_result.overfill_level.value,
                "oxygen_safe": self.vecs_result.oxygen_safe,
                "arrester_pass": self.vecs_result.arrester_pass,
                "loading_permitted": self.vecs_result.cargo_loading_permitted,
                "max_loading_rate": self.vecs_result.max_allowable_loading_rate_m3_h,
            },
            "total_warnings": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeThrusterLiferaftIncineratorVECSEngine:
    """Master facade for Maritime Phases 399-402."""

    def __init__(self):
        self.thruster_engine = BowThrusterEngine()
        self.liferaft_engine = LiferaftHRUEngine()
        self.incinerator_engine = IncineratorEngine()
        self.vecs_engine = VECSEngine()

    def evaluate(
        self,
        thruster_inp: BowThrusterInput = BowThrusterInput(),
        liferaft_inp: LiferaftHRUInput = LiferaftHRUInput(),
        incinerator_inp: IncineratorInput = IncineratorInput(),
        vecs_inp: VECSInput = VECSInput(),
    ) -> MaritimeThrusterLiferaftIncineratorVECSResult:
        """Run integrated physical evaluation and classify seaworthiness."""
        th_res = self.thruster_engine.evaluate(thruster_inp)
        lr_res = self.liferaft_engine.evaluate(liferaft_inp)
        inc_res = self.incinerator_engine.evaluate(incinerator_inp)
        vec_res = self.vecs_engine.evaluate(vecs_inp)

        warnings = (
            th_res.warnings
            + lr_res.warnings
            + inc_res.warnings
            + vec_res.warnings
        )

        critical_hazard = (
            not th_res.operational_permitted
            or not lr_res.service_valid
            or inc_res.safety_trip_active
            or not vec_res.cargo_loading_permitted
        )

        warning_state = (
            th_res.power_limit_active
            or th_res.cavitation_status.value != "NO_CAVITATION"
            or not lr_res.painter_length_compliant
            or not inc_res.waste_charging_permitted
            or not inc_res.flue_emissions_compliant
            or vec_res.pressure_status.value != "NOMINAL_SAFE"
        )

        if critical_hazard:
            overall = "CRITICAL_SAFETY_TRIP"
        elif warning_state:
            overall = "OPERATIONAL_WARNING_ACTIVE"
        else:
            overall = "ALL_SYSTEMS_NOMINAL"

        return MaritimeThrusterLiferaftIncineratorVECSResult(
            thruster_result=th_res,
            liferaft_result=lr_res,
            incinerator_result=inc_res,
            vecs_result=vec_res,
            overall_system_status=overall,
            aggregated_warnings=warnings,
        )
