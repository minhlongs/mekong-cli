"""Phase 429: Cargo Hold Bilge Suction Valve Interlock & Dewatering Eductor Sizing.

Implements SOLAS II-1 Reg 21, SOLAS XII Reg 12, and IACS UR SC18:
Cargo hold bilge suction screw-down non-return (SDNR) backflow prevention,
water ingress detection system (WIDS Level 1 at >= 0.5m, Level 2 at >= 2.0m),
and venturi jet eductor dewatering sizing with motive pressure safety interlocks.
Strictly < 180 LOC, zero mocks.
"""

import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CargoHoldBilgeTelemetry:
    """Telemetry readings for Cargo Hold Bilge and Dewatering Eductor System."""
    cargo_hold_id: str = "HOLD_NO_1"
    water_level_meters: float = 0.08  # Bilge well water height
    bilge_well_depth_m: float = 0.60
    inner_bottom_height_m: float = 1.20
    motive_water_pressure_bar: float = 6.8  # Supplied by ballast or fire pump
    eductor_discharge_pressure_bar: float = 1.5
    suction_lift_height_m: float = 4.2  # Height difference from bilge well to eductor
    bilge_suction_valve_open: bool = False
    motive_valve_open: bool = False
    non_return_valve_seated: bool = True
    motive_flow_rate_m3_h: float = 80.0


@dataclass(frozen=True)
class CargoHoldBilgeAssessment:
    """Cargo hold water ingress, eductor dewatering capacity, and safety interlocks."""
    water_ingress_alarm_level: str  # NORMAL, LEVEL_1_PRE_ALARM, LEVEL_2_EMERGENCY
    dewatering_capacity_m3_h: float
    entrainment_ratio: float
    backflow_risk: bool
    eductor_operational_ready: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CargoHoldBilgeEngine:
    """Evaluates cargo hold bilge water ingress and jet eductor dewatering performance."""

    WIDS_LEVEL_1_METERS: float = 0.50  # SOLAS XII Reg 12 Level 1 alarm
    WIDS_LEVEL_2_METERS: float = 2.00  # SOLAS XII Reg 12 Level 2 emergency
    MIN_MOTIVE_PRESSURE_BAR: float = 4.5  # Below this, eductor will backflow if opened
    NOMINAL_MOTIVE_PRESSURE_BAR: float = 6.0
    MAX_SUCTION_LIFT_M: float = 6.5
    EDUCTOR_COEFFICIENT_K: float = 0.65
    SEAWATER_DENSITY_KG_M3: float = 1025.0
    GRAVITY: float = 9.81

    def evaluate(self, telem: CargoHoldBilgeTelemetry) -> CargoHoldBilgeAssessment:
        warnings: List[str] = []

        # 1. SOLAS XII Reg 12 Water Ingress Detection System (WIDS)
        if telem.water_level_meters >= self.WIDS_LEVEL_2_METERS:
            ingress_level = "LEVEL_2_EMERGENCY"
            warnings.append(
                f"EMERGENCY: Cargo hold water level {telem.water_level_meters:.2f} m exceeds "
                f"Level 2 threshold ({self.WIDS_LEVEL_2_METERS:.2f} m). Catastrophic hold flooding risk!"
            )
        elif telem.water_level_meters >= self.WIDS_LEVEL_1_METERS:
            ingress_level = "LEVEL_1_PRE_ALARM"
            warnings.append(
                f"ALERT: Water ingress Level 1 pre-alarm: {telem.water_level_meters:.2f} m >= "
                f"{self.WIDS_LEVEL_1_METERS:.2f} m above inner bottom."
            )
        else:
            ingress_level = "NORMAL"

        # 2. Backflow Protection & Interlock Check (SOLAS II-1 Reg 21 & IACS SC18)
        # Motive pressure must be established (> 4.5 bar) BEFORE suction valve opens
        motive_ready = (
            telem.motive_valve_open
            and telem.motive_water_pressure_bar >= self.MIN_MOTIVE_PRESSURE_BAR
        )
        # Backflow hazard occurs if suction valve is open without adequate motive pressure
        backflow = telem.bilge_suction_valve_open and not motive_ready

        if backflow:
            warnings.append(
                "CRITICAL INTERLOCK VIOLATION: Bilge suction valve open while motive pressure is insufficient "
                f"({telem.motive_water_pressure_bar:.1f} bar < {self.MIN_MOTIVE_PRESSURE_BAR:.1f} bar). "
                "Risk of seawater backflooding into cargo hold!"
            )
        if not telem.non_return_valve_seated and not telem.bilge_suction_valve_open:
            warnings.append("WARNING: Screw-down non-return (SDNR) valve not properly seated.")

        # 3. Venturi Jet Eductor Sizing & Dewatering Rate
        # Entrainment ratio R_q = Q_bilge / Q_motive = K * sqrt((P_motive - P_dis) / (P_dis + rho*g*H_lift))
        delta_p_motive = max(0.1, telem.motive_water_pressure_bar - telem.eductor_discharge_pressure_bar)
        lift_head_bar = (self.SEAWATER_DENSITY_KG_M3 * self.GRAVITY * telem.suction_lift_height_m) / 100000.0
        denom_head_bar = max(0.2, telem.eductor_discharge_pressure_bar + lift_head_bar)

        if motive_ready and telem.suction_lift_height_m <= self.MAX_SUCTION_LIFT_M:
            entrainment = self.EDUCTOR_COEFFICIENT_K * math.sqrt(delta_p_motive / denom_head_bar)
            dewatering_m3_h = telem.motive_flow_rate_m3_h * entrainment
            eductor_ok = True
        else:
            entrainment = 0.0
            dewatering_m3_h = 0.0
            eductor_ok = False

        if telem.suction_lift_height_m > self.MAX_SUCTION_LIFT_M:
            warnings.append(
                f"Suction lift {telem.suction_lift_height_m:.1f} m exceeds maximum suction limit "
                f"({self.MAX_SUCTION_LIFT_M:.1f} m). Eductor will lose prime/cavitate."
            )

        # 4. Status determination
        if backflow or ingress_level == "LEVEL_2_EMERGENCY":
            status = "CRITICAL_FLOODING_HAZARD"
        elif ingress_level == "LEVEL_1_PRE_ALARM":
            status = "WATER_INGRESS_PRE_ALARM"
        elif telem.bilge_suction_valve_open and eductor_ok:
            status = "ACTIVE_DEWATERING"
        elif motive_ready:
            status = "EDUCTOR_ARMED_READY"
        else:
            status = "NORMAL_STANDBY"

        compliance_flags = {
            "wids_level_safe": ingress_level == "NORMAL",
            "backflow_prevented": not backflow,
            "sdnr_valve_healthy": telem.non_return_valve_seated,
            "motive_pressure_adequate": telem.motive_water_pressure_bar >= self.MIN_MOTIVE_PRESSURE_BAR,
            "suction_lift_within_limit": telem.suction_lift_height_m <= self.MAX_SUCTION_LIFT_M,
        }

        return CargoHoldBilgeAssessment(
            water_ingress_alarm_level=ingress_level,
            dewatering_capacity_m3_h=round(dewatering_m3_h, 2),
            entrainment_ratio=round(entrainment, 3),
            backflow_risk=backflow,
            eductor_operational_ready=eductor_ok,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
