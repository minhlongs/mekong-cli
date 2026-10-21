"""Master Unified Maritime Economizer, Thermal Oil, Bilge Evaporator & Crankcase Engine.

Phases 423-426:
- Phase 423: Exhaust Gas Economizer Soot Water Washing & Delta-P (MEPC.340(77), IACS M53)
- Phase 424: Marine Thermal Oil Heating System & N2 Blanketing (DIN 4754, ISO 5149)
- Phase 425: Machinery Bilge Water Vacuum Evaporator & Distillation (MARPOL Annex I, MEPC.107(49))
- Phase 426: Crankcase Explosion Relief Valve & Oil Mist Detector (IACS UR M9/M10, SOLAS II-1/31)

Strictly < 140 LOC, zero mocks.
"""

from dataclasses import dataclass, field

from src.core.maritime.phase_423_economizer_soot_wash import (
    EconomizerSootWashEngine,
    EconomizerSootWashTelemetry,
    EconomizerSootWashAssessment,
)
from src.core.maritime.phase_424_thermal_oil_system import (
    ThermalOilSystemEngine,
    ThermalOilTelemetry,
    ThermalOilAssessment,
)
from src.core.maritime.phase_425_bilge_water_evaporator import (
    BilgeEvaporatorEngine,
    BilgeEvaporatorTelemetry,
    BilgeEvaporatorAssessment,
)
from src.core.maritime.phase_426_crankcase_relief_omd import (
    CrankcaseOmdEngine,
    CrankcaseOmdTelemetry,
    CrankcaseOmdAssessment,
)


@dataclass(frozen=True)
class MaritimePhases423to426Telemetry:
    """Consolidated telemetry for maritime economizer, thermal oil, bilge evaporator & crankcase."""
    sootwash: EconomizerSootWashTelemetry = field(default_factory=EconomizerSootWashTelemetry)
    thermaloil: ThermalOilTelemetry = field(default_factory=ThermalOilTelemetry)
    bilgeevap: BilgeEvaporatorTelemetry = field(default_factory=BilgeEvaporatorTelemetry)
    crankcaseomd: CrankcaseOmdTelemetry = field(default_factory=CrankcaseOmdTelemetry)


@dataclass(frozen=True)
class MaritimePhases423to426Assessment:
    """Consolidated safety assessment across Phases 423 to 426."""
    sootwash: EconomizerSootWashAssessment
    thermaloil: ThermalOilAssessment
    bilgeevap: BilgeEvaporatorAssessment
    crankcaseomd: CrankcaseOmdAssessment
    system_wide_trip_active: bool
    overall_status: str


class MaritimeEconomizerThermalBilgeCrankcaseEngine:
    """Master facade coordinating phases 423-426 maritime engineering subsystems."""

    def __init__(self) -> None:
        self.sootwash_engine = EconomizerSootWashEngine()
        self.thermaloil_engine = ThermalOilSystemEngine()
        self.bilgeevap_engine = BilgeEvaporatorEngine()
        self.crankcaseomd_engine = CrankcaseOmdEngine()

    def evaluate_all(self, telem: MaritimePhases423to426Telemetry) -> MaritimePhases423to426Assessment:
        res_sootwash = self.sootwash_engine.evaluate(telem.sootwash)
        res_thermaloil = self.thermaloil_engine.evaluate(telem.thermaloil)
        res_bilgeevap = self.bilgeevap_engine.evaluate(telem.bilgeevap)
        res_crankcaseomd = self.crankcaseomd_engine.evaluate(telem.crankcaseomd)

        any_trip = (
            res_sootwash.soot_fire_emergency_trip
            or res_thermaloil.emergency_burner_trip
            or (res_bilgeevap.status == "EMERGENCY_DIVERT")
            or res_crankcaseomd.emergency_slowdown_trip
        )

        statuses = [
            res_sootwash.status,
            res_thermaloil.status,
            res_bilgeevap.status,
            res_crankcaseomd.status,
        ]

        if any_trip or any("EMERGENCY" in s for s in statuses):
            overall = "EMERGENCY_ACTIVE"
        elif any("WARNING" in s or "REQUIRED" in s for s in statuses):
            overall = "WARNING"
        else:
            overall = "ALL_SYSTEMS_NOMINAL"

        return MaritimePhases423to426Assessment(
            sootwash=res_sootwash,
            thermaloil=res_thermaloil,
            bilgeevap=res_bilgeevap,
            crankcaseomd=res_crankcaseomd,
            system_wide_trip_active=any_trip,
            overall_status=overall,
        )
