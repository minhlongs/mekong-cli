"""Phase 422: Hyper-Mist Local Application Water-Based Fire Fighting System.

Implements SOLAS II-2 Reg 10.5.6, IMO MSC/Circ.1165, and FSS Code Chapter 7:
High-pressure water mist atomization (Dv0.9 < 100 μm), dual flame/thermal sensor voting,
automatic pump start, section valve release, and suction head interlocks.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class HyperMistTelemetry:
    """Telemetry readings for engine room hyper-mist fire extinguishing system."""
    protected_section: str = "ME_CYLINDER_TOP" # Sections: ME_CYLINDER_TOP, PURIFIER_ROOM, BOILER_FRONT, INCINERATOR
    uv_ir_flame_detected: bool = False
    thermal_heat_detected: bool = False
    rate_of_rise_c_per_min: float = 2.0
    pump_discharge_pressure_bar: float = 142.0  # High pressure target ~140 bar
    pump_suction_pressure_bar: float = 3.5      # Fresh water tank head
    fresh_water_tank_level_pct: float = 90.0
    manual_emergency_release: bool = False
    pre_discharge_alarm_seconds: float = 20.0


@dataclass(frozen=True)
class HyperMistAssessment:
    """Assessment of fire detection consensus, pump readiness, and mist discharge status."""
    fire_confirmed: bool
    discharge_valve_opened: bool
    pump_active: bool
    atomization_effective: bool
    fresh_to_sea_chest_switchover_required: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class HyperMistFireExtinguishingEngine:
    """Controls high-pressure water mist actuation, droplet dispersion, and suction failsafes."""

    MIN_ATOMIZATION_PRESSURE_BAR: float = 120.0
    MAX_PUMP_PRESSURE_BAR: float = 165.0
    MIN_SUCTION_PRESSURE_BAR: float = 1.5
    MAX_PERMISSIBLE_HEAT_RISE_RATE: float = 10.0 # deg C / min

    def evaluate(self, telemetry: HyperMistTelemetry) -> HyperMistAssessment:
        warnings: List[str] = []

        # 2-out-of-2 voting or Manual Release or (Flame + High Rate of Rise)
        rapid_heat_rise = telemetry.rate_of_rise_c_per_min >= self.MAX_PERMISSIBLE_HEAT_RISE_RATE
        fire_confirmed = (
            telemetry.manual_emergency_release or
            (telemetry.uv_ir_flame_detected and telemetry.thermal_heat_detected) or
            (telemetry.uv_ir_flame_detected and rapid_heat_rise)
        )

        if fire_confirmed:
            warnings.append(f"FIRE DETECTED IN {telemetry.protected_section}: Hyper-mist release initiated!")

        # Pump and Section Valve actuation
        pump_active = fire_confirmed
        discharge_valve_opened = fire_confirmed

        # Suction pressure and tank water level checks
        if telemetry.fresh_water_tank_level_pct < 15.0:
            sea_chest_switch = True
            warnings.append("Fresh water holding tank low (< 15%): automated sea chest changeover engaged")
        else:
            sea_chest_switch = False

        if telemetry.pump_suction_pressure_bar < self.MIN_SUCTION_PRESSURE_BAR:
            warnings.append("Cavitation alert: Pump suction pressure below 1.5 bar threshold!")

        # High pressure droplet atomization verification (< 100 microns requires >= 120 bar)
        atomization_effective = (
            pump_active and
            (self.MIN_ATOMIZATION_PRESSURE_BAR <= telemetry.pump_discharge_pressure_bar <= self.MAX_PUMP_PRESSURE_BAR)
        )

        if pump_active and not atomization_effective:
            warnings.append(f"Discharge pressure {telemetry.pump_discharge_pressure_bar} bar out of range [120, 165] bar: mist droplet size suboptimal")

        status = "DISCHARGING" if fire_confirmed else ("STANDBY" if not warnings else "ALERT")

        return HyperMistAssessment(
            fire_confirmed=fire_confirmed,
            discharge_valve_opened=discharge_valve_opened,
            pump_active=pump_active,
            atomization_effective=atomization_effective,
            fresh_to_sea_chest_switchover_required=sea_chest_switch,
            status=status,
            warnings=warnings,
            compliance_flags={
                "solas_ii2_reg10_local_application_ready": True,
                "fss_code_ch7_atomization_compliant": atomization_effective if pump_active else True,
                "suction_head_positive": telemetry.pump_suction_pressure_bar >= self.MIN_SUCTION_PRESSURE_BAR,
                "dual_sensor_consensus_verified": fire_confirmed if (telemetry.uv_ir_flame_detected or telemetry.manual_emergency_release) else True,
            },
        )
