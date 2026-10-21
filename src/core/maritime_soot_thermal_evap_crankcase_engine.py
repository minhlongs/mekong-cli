"""Master Unified Maritime Thermal, Exhaust, Evaporator & Crankcase Safety Engine (Phases 423-426).

Combines:
- Phase 423: Marine Economizer Automated Soot Water Washing & Fire Prevention (MARPOL VI, MEPC.340(77), IACS M53)
- Phase 424: Thermal Oil Heater & Expansion Tank Closed-Loop Control (DIN 4754, ISO 5149, DNV Pt.4 Ch.6 Sec.7)
- Phase 425: Bilge Water Vacuum Evaporator & Concentrated Sludge Distillation (MARPOL I Reg 15, MEPC.107(49))
- Phase 426: Crankcase Explosion Relief Valve & Gravimetric Oil Mist Detector (IACS M9/M10, SOLAS II-1 Reg 27.5)

Strictly < 150 LOC, zero mocks.
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from src.core.maritime.phase_423_economizer_soot_wash_fire import (
    EconomizerSootWaterWashEngine,
    EconomizerSootTelemetry,
    EconomizerSootAssessment,
)
from src.core.maritime.phase_424_thermal_oil_heater_expansion import (
    ThermalOilHeaterExpansionEngine,
    ThermalOilTelemetry,
    ThermalOilAssessment,
)
from src.core.maritime.phase_425_bilge_vacuum_evaporator import (
    BilgeVacuumEvaporatorEngine,
    BilgeVacuumEvaporatorTelemetry,
    BilgeVacuumEvaporatorAssessment,
)
from src.core.maritime.phase_426_crankcase_relief_oil_mist import (
    CrankcaseReliefMistEngine,
    CrankcaseReliefMistTelemetry,
    CrankcaseReliefMistAssessment,
)


@dataclass(frozen=True)
class MaritimePhases423to426Telemetry:
    """Consolidated telemetry for maritime soot, thermal oil, evaporator, and crankcase systems."""
    economizer: EconomizerSootTelemetry = field(default_factory=EconomizerSootTelemetry)
    thermal_oil: ThermalOilTelemetry = field(default_factory=ThermalOilTelemetry)
    bilge_evap: BilgeVacuumEvaporatorTelemetry = field(default_factory=BilgeVacuumEvaporatorTelemetry)
    crankcase: CrankcaseReliefMistTelemetry = field(default_factory=CrankcaseReliefMistTelemetry)


@dataclass(frozen=True)
class MaritimePhases423to426Assessment:
    """Consolidated safety and operational assessment for Phases 423-426."""
    economizer: EconomizerSootAssessment
    thermal_oil: ThermalOilAssessment
    bilge_evap: BilgeVacuumEvaporatorAssessment
    crankcase: CrankcaseReliefMistAssessment
    overall_status: str
    all_systems_operational: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "economizer_status": self.economizer.status,
            "economizer_fire_trip": self.economizer.emergency_soot_fire_trip,
            "thermal_oil_status": self.thermal_oil.status,
            "thermal_oil_trip": self.thermal_oil.burner_trip_demanded,
            "bilge_evap_status": self.bilge_evap.status,
            "bilge_discharge_permitted": self.bilge_evap.overboard_discharge_permitted,
            "crankcase_status": self.crankcase.status,
            "crankcase_emergency_trip": self.crankcase.emergency_slowdown_trip,
            "overall_status": self.overall_status,
            "all_systems_operational": self.all_systems_operational,
        }


class MaritimeSootThermalEvapCrankcaseEngine:
    """Unified controller orchestrating phases 423 through 426."""

    def __init__(self) -> None:
        self.economizer_engine = EconomizerSootWaterWashEngine()
        self.thermal_oil_engine = ThermalOilHeaterExpansionEngine()
        self.bilge_evap_engine = BilgeVacuumEvaporatorEngine()
        self.crankcase_engine = CrankcaseReliefMistEngine()

    def evaluate_all(self, telemetry: MaritimePhases423to426Telemetry) -> MaritimePhases423to426Assessment:
        econ_res = self.economizer_engine.evaluate(telemetry.economizer)
        thermal_res = self.thermal_oil_engine.evaluate(telemetry.thermal_oil)
        bilge_res = self.bilge_evap_engine.evaluate(telemetry.bilge_evap)
        crank_res = self.crankcase_engine.evaluate(telemetry.crankcase)

        critical_alert = (
            econ_res.emergency_soot_fire_trip or
            thermal_res.burner_trip_demanded or
            crank_res.emergency_slowdown_trip
        )
        has_warnings = bool(
            econ_res.warnings or
            thermal_res.warnings or
            bilge_res.warnings or
            crank_res.warnings
        )

        overall_status = "CRITICAL" if critical_alert else ("WARNING" if has_warnings else "NORMAL")
        all_systems_operational = (
            not econ_res.emergency_soot_fire_trip
            and not thermal_res.burner_trip_demanded
            and not crank_res.emergency_slowdown_trip
            and bilge_res.distillate_purity_compliant
        )

        return MaritimePhases423to426Assessment(
            economizer=econ_res,
            thermal_oil=thermal_res,
            bilge_evap=bilge_res,
            crankcase=crank_res,
            overall_status=overall_status,
            all_systems_operational=all_systems_operational,
        )
