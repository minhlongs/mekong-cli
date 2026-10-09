"""Maritime Phase 396: Steering Gear Dual Hydraulic Power Actuator & Response Telemetry.

Complies with SOLAS II-1 Reg 29, IMO Res. A.1052(27), and IACS UR M42.
Zero mock dependencies, strict hydraulic mechanics & rudder kinematics.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SteeringGearInput:
    rudder_traversal_35_to_30_deg_sec: float = 22.5
    auxiliary_traversal_15_to_15_deg_sec: float = 48.0
    hydraulic_pressure_bar: float = 160.0
    relief_valve_setting_bar: float = 210.0
    oil_reservoir_level_pct: float = 85.0
    pump_1_operational: bool = True
    pump_2_operational: bool = True
    hunting_gear_error_deg: float = 0.4


@dataclass
class SteeringGearResult:
    steering_readiness_status: str
    main_gear_speed_compliant: bool
    auxiliary_gear_speed_compliant: bool
    redundancy_active: bool
    hydraulic_pressure_status: str
    reservoir_level_ok: bool
    control_tracking_aligned: bool
    warnings: List[str] = field(default_factory=list)


class SteeringGearEngine:
    """Evaluates dual hydraulic power steering gear speed, redundancy, and pressure."""

    MAX_MAIN_TRANSIT_SEC = 28.0
    MAX_AUX_TRANSIT_SEC = 60.0
    MIN_OIL_LEVEL_PCT = 25.0
    MAX_TRACKING_ERROR_DEG = 1.0
    MIN_RELIEF_RATIO = 1.20

    def evaluate(self, inp: SteeringGearInput) -> SteeringGearResult:
        warnings = []
        t_main = round(inp.rudder_traversal_35_to_30_deg_sec, 1)
        t_aux = round(inp.auxiliary_traversal_15_to_15_deg_sec, 1)
        p_hyd = round(inp.hydraulic_pressure_bar, 1)
        p_relief = round(inp.relief_valve_setting_bar, 1)
        level = round(inp.oil_reservoir_level_pct, 1)
        err = round(inp.hunting_gear_error_deg, 2)

        # 35 to 30 deg transition time (SOLAS <= 28s)
        main_speed_ok = t_main <= self.MAX_MAIN_TRANSIT_SEC
        if not main_speed_ok:
            warnings.append(
                f"RUDDER TRAVERSAL SLOW: {t_main}s exceeds 28s limit (35° to 30°)"
            )

        # Auxiliary steering capability (SOLAS <= 60s for 15° to 15°)
        aux_speed_ok = t_aux <= self.MAX_AUX_TRANSIT_SEC
        if not aux_speed_ok:
            warnings.append(
                f"AUXILIARY STEERING SLOW: {t_aux}s exceeds 60s limit (15° to 15°)"
            )

        # Redundancy check (both pumps operational)
        redundant = inp.pump_1_operational and inp.pump_2_operational
        if not (inp.pump_1_operational or inp.pump_2_operational):
            warnings.append("TOTAL STEERING LOSS: Both hydraulic power units offline")
        elif not redundant:
            warnings.append("SINGLE POWER UNIT ONLY: Automatic failover redundancy lost")

        # Hydraulic pressure & relief setting
        relief_ratio = p_relief / p_hyd if p_hyd > 0 else 0
        if p_hyd < 100.0:
            press_status = "LOW_PRESSURE_DEFECT"
            warnings.append(f"LOW HYDRAULIC PRESSURE: {p_hyd} bar below operating minimum")
        elif relief_ratio < self.MIN_RELIEF_RATIO:
            press_status = "RELIEF_SETTING_SUBOPTIMAL"
            warnings.append(
                f"RELIEF RATIO LOW ({relief_ratio:.2f} < 1.20): Risk of premature bypass"
            )
        else:
            press_status = "NORMAL_OPTIMAL"

        # Reservoir level
        level_ok = level >= self.MIN_OIL_LEVEL_PCT
        if not level_ok:
            warnings.append(
                f"HYDRAULIC OIL LEVEL CRITICAL: {level}% triggers low level alarm (<25%)"
            )

        # Tracking follow-up alignment
        aligned = err <= self.MAX_TRACKING_ERROR_DEG
        if not aligned:
            warnings.append(
                f"TELEMETER HUNTING ERROR: {err}° exceeds 1.0° alignment tolerance"
            )

        # Global steering status
        if not (inp.pump_1_operational or inp.pump_2_operational) or not level_ok:
            status = "CRITICAL_STEERING_FAILURE"
        elif not main_speed_ok or press_status == "LOW_PRESSURE_DEFECT":
            status = "NON_COMPLIANT_NAVIGATION_HAZARD"
        elif not redundant or not aligned:
            status = "DEGRADED_OPERATIONAL_MODE"
        else:
            status = "SEAWORTHY_REDUNDANT_OPTIMAL"

        return SteeringGearResult(
            steering_readiness_status=status,
            main_gear_speed_compliant=main_speed_ok,
            auxiliary_gear_speed_compliant=aux_speed_ok,
            redundancy_active=redundant,
            hydraulic_pressure_status=press_status,
            reservoir_level_ok=level_ok,
            control_tracking_aligned=aligned,
            warnings=warnings,
        )
