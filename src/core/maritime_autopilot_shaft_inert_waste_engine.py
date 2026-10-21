"""Central Facade for Maritime Phases 359-362.

Unifies:
- Phase 359: Adaptive Autopilot & Rudder Monitoring
- Phase 360: Propeller Shaft Alignment & Whirling Vibration
- Phase 361: N2 Inert Gas Generator & Dew Point
- Phase 362: Remote Seaport Wastewater Recycling & Zero-Discharge
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from src.core.maritime.phase_359_adaptive_autopilot_rudder import (
    AdaptiveAutopilotEngine,
    AdaptiveAutopilotInput,
    AdaptiveAutopilotResult,
)
from src.core.maritime.phase_360_shaft_alignment_vibration import (
    ShaftAlignmentVibrationEngine,
    ShaftAlignmentVibrationInput,
    ShaftAlignmentVibrationResult,
)
from src.core.maritime.phase_361_n2_inert_gas_dew_point import (
    N2InertGasEngine,
    N2InertGasInput,
    N2InertGasResult,
)
from src.core.maritime.phase_362_seaport_wastewater_recycling import (
    SeaportWastewaterEngine,
    SeaportWastewaterInput,
    SeaportWastewaterResult,
)


@dataclass
class MaritimeMultiDomain359To362Report:
    overall_risk_level: str
    autopilot_result: AdaptiveAutopilotResult
    shaft_result: ShaftAlignmentVibrationResult
    inert_gas_result: N2InertGasResult
    wastewater_result: SeaportWastewaterResult
    critical_alerts: List[str] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)


class MaritimeAutopilotShaftInertWasteEngine:
    """Unified Facade for Maritime Phases 359-362."""

    @classmethod
    def evaluate_autopilot(cls, inp: AdaptiveAutopilotInput) -> AdaptiveAutopilotResult:
        return AdaptiveAutopilotEngine.evaluate(inp)

    @classmethod
    def evaluate_shaft(cls, inp: ShaftAlignmentVibrationInput) -> ShaftAlignmentVibrationResult:
        return ShaftAlignmentVibrationEngine.evaluate(inp)

    @classmethod
    def evaluate_inert_gas(cls, inp: N2InertGasInput) -> N2InertGasResult:
        return N2InertGasEngine.evaluate(inp)

    @classmethod
    def evaluate_wastewater(cls, inp: SeaportWastewaterInput) -> SeaportWastewaterResult:
        return SeaportWastewaterEngine.evaluate(inp)

    @classmethod
    def run_all(
        cls,
        autopilot_inp: AdaptiveAutopilotInput,
        shaft_inp: ShaftAlignmentVibrationInput,
        inert_inp: N2InertGasInput,
        waste_inp: SeaportWastewaterInput,
    ) -> MaritimeMultiDomain359To362Report:
        auto_res = cls.evaluate_autopilot(autopilot_inp)
        shaft_res = cls.evaluate_shaft(shaft_inp)
        inert_res = cls.evaluate_inert_gas(inert_inp)
        waste_res = cls.evaluate_wastewater(waste_inp)

        critical_alerts: List[str] = []
        if auto_res.is_steering_gear_lag_critical:
            critical_alerts.append(f"AUTOPILOT: Critical rudder lag detected for vessel {auto_res.vessel_id}")
        if not shaft_res.is_bearing_pressure_safe or shaft_res.is_in_barred_speed_range:
            critical_alerts.append(f"SHAFT: Propulsion hazard (Pressure Safe: {shaft_res.is_bearing_pressure_safe}, BSR: {shaft_res.is_in_barred_speed_range})")
        if not inert_res.is_cargo_supply_permitted:
            critical_alerts.append(f"INERT GAS: Atmosphere out-of-spec (O2 compliant: {inert_res.is_o2_compliant_igc}, Dew dry: {inert_res.is_dew_point_dry})")
        if not waste_res.is_effluent_compliant:
            critical_alerts.append(f"WASTEWATER: Contaminated effluent lock-out at {waste_res.facility_id}")

        if critical_alerts:
            overall_risk = "CRITICAL"
        elif (
            auto_res.status != "STEADY_SEAWAY_HEADING"
            or shaft_res.vibration_severity_grade in ["SATISFACTORY", "RESTRICTED_ALARM"]
            or inert_res.is_dryer_regeneration_required
            or not waste_res.is_zld_target_achieved
        ):
            overall_risk = "MODERATE"
        else:
            overall_risk = "NOMINAL"

        metrics = {
            "heading_error_deg": auto_res.heading_error_deg,
            "commanded_rudder_deg": auto_res.commanded_rudder_angle_deg,
            "aft_bearing_pressure_mpa": shaft_res.aft_bearing_pressure_mpa,
            "blade_passing_freq_hz": shaft_res.blade_passing_frequency_hz,
            "inert_cargo_supply_permitted": inert_res.is_cargo_supply_permitted,
            "water_recovery_percent": waste_res.water_recovery_rate_percent,
        }

        return MaritimeMultiDomain359To362Report(
            overall_risk_level=overall_risk,
            autopilot_result=auto_res,
            shaft_result=shaft_res,
            inert_gas_result=inert_res,
            wastewater_result=waste_res,
            critical_alerts=critical_alerts,
            summary_metrics=metrics,
        )
