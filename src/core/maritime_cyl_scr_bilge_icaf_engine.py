"""Master Integration Facade Engine for Maritime Automation Phases 427-430.

Coordinates:
- Phase 427: Cylinder Lubrication Alpha ACC & BN Neutralization.
- Phase 428: SCR Urea / DEF De-NOx Kinetics & IMO Tier III Compliance.
- Phase 429: Cargo Hold Bilge Suction Interlocks & Dewatering Eductor.
- Phase 430: Hull Impressed Current Anti-Fouling (ICAF) & Ultrasonic Acoustic Protection.
Strictly < 130 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List

from src.core.maritime.phase_427_cylinder_lubrication_alpha import (
    CylinderLubricationEngine,
    CylinderLubricationTelemetry,
    CylinderLubricationAssessment,
)
from src.core.maritime.phase_428_scr_urea_denox import (
    SCRDeNOxEngine,
    SCRDeNOxTelemetry,
    SCRDeNOxAssessment,
)
from src.core.maritime.phase_429_cargo_hold_bilge_eductor import (
    CargoHoldBilgeEngine,
    CargoHoldBilgeTelemetry,
    CargoHoldBilgeAssessment,
)
from src.core.maritime.phase_430_hull_icaf_ultrasonic import (
    HullAntiFoulingEngine,
    HullAntiFoulingTelemetry,
    HullAntiFoulingAssessment,
)


@dataclass(frozen=True)
class MaritimePhases427to430Telemetry:
    """Master telemetry container aggregating Phases 427-430 readings."""
    cylinder: CylinderLubricationTelemetry = CylinderLubricationTelemetry()
    scr: SCRDeNOxTelemetry = SCRDeNOxTelemetry()
    bilge: CargoHoldBilgeTelemetry = CargoHoldBilgeTelemetry()
    icaf: HullAntiFoulingTelemetry = HullAntiFoulingTelemetry()


@dataclass(frozen=True)
class MaritimePhases427to430Assessment:
    """Consolidated assessment across engine lubrication, emissions, bilge, and hull protection."""
    cylinder: CylinderLubricationAssessment
    scr: SCRDeNOxAssessment
    bilge: CargoHoldBilgeAssessment
    icaf: HullAntiFoulingAssessment
    overall_status: str
    all_systems_operational: bool
    combined_warnings: List[str]


class MaritimeCylSCRBilgeICAFEngine:
    """Master facade executing unified evaluation for Maritime Phases 427-430."""

    def __init__(self) -> None:
        self.cyl_engine = CylinderLubricationEngine()
        self.scr_engine = SCRDeNOxEngine()
        self.bilge_engine = CargoHoldBilgeEngine()
        self.icaf_engine = HullAntiFoulingEngine()

    def evaluate_all(self, telem: MaritimePhases427to430Telemetry) -> MaritimePhases427to430Assessment:
        cyl_res = self.cyl_engine.evaluate(telem.cylinder)
        scr_res = self.scr_engine.evaluate(telem.scr)
        bilge_res = self.bilge_engine.evaluate(telem.bilge)
        icaf_res = self.icaf_engine.evaluate(telem.icaf)

        combined_warnings: List[str] = (
            cyl_res.warnings + scr_res.warnings + bilge_res.warnings + icaf_res.warnings
        )

        critical = (
            cyl_res.status == "CRITICAL_LINER_WEAR"
            or scr_res.status in ("CRITICAL_SCR_FAULT", "AMMONIA_SLIP_EXCESS")
            or bilge_res.status == "CRITICAL_FLOODING_HAZARD"
            or icaf_res.status == "CRITICAL_SYSTEM_FAULT"
        )
        warning = (
            cyl_res.status in ("CORROSION_WARNING", "ASH_DEPOSIT_RISK")
            or scr_res.status in ("INJECTION_INHIBITED_COLD", "CATALYST_FOULING_SOOTBLOW")
            or bilge_res.status in ("WATER_INGRESS_PRE_ALARM", "ACTIVE_DEWATERING")
            or icaf_res.status in ("MAINTENANCE_REQUIRED", "SUB_OPTIMAL_DOSING")
        )

        if critical:
            overall_status = "CRITICAL_HAZARD"
        elif warning:
            overall_status = "WARNING_OPERATIONAL"
        else:
            overall_status = "NORMAL"

        operational = (
            cyl_res.compliance_flags["feed_rate_within_limits"]
            and scr_res.compliance_flags["tier_iii_compliant"]
            and bilge_res.compliance_flags["wids_level_safe"]
            and icaf_res.compliance_flags["ultrasonic_transducer_healthy"]
        )

        return MaritimePhases427to430Assessment(
            cylinder=cyl_res,
            scr=scr_res,
            bilge=bilge_res,
            icaf=icaf_res,
            overall_status=overall_status,
            all_systems_operational=operational,
            combined_warnings=combined_warnings,
        )
