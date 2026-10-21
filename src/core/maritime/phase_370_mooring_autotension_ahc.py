"""Mooring Winch Auto-Tension & Active Heave Compensation (AHC) Engine.

Standards: OCIMF MEG4, ISO 3730 Mooring Winches,
and IMCA D 018 Heave Compensation Systems.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class WinchActionState(str, Enum):
    """Auto-tension control actions."""

    HOLD = "HOLD"
    HEAVE_IN = "HEAVE_IN"  # Line tension below lower threshold
    RENDER_OUT = "RENDER_OUT"  # Line tension above upper threshold
    OVERLOAD_ALARM = "OVERLOAD_ALARM"


@dataclass
class WinchSensorInput:
    winch_id: str
    measured_tension_kn: float
    mbl_kn: float  # Minimum Breaking Load
    target_tension_pct_mbl: float = 20.0  # Default 20% MBL
    ship_heave_amplitude_m: float = 0.8
    wave_period_s: float = 8.0
    load_displacement_rms_m: float = 0.08  # Residual motion of load
    winch_speed_m_s: float = 0.5


@dataclass
class AutoTensionAhcReport:
    winch_id: str
    action_state: WinchActionState
    is_ahc_active: bool
    ahc_efficiency_pct: float
    target_tension_kn: float
    render_threshold_kn: float
    heave_threshold_kn: float
    command_winch_speed_m_s: float
    warnings: List[str]
    metrics: Dict[str, float]


class MooringAutoTensionAhcEngine:
    """Controls auto-tension rendering/heaving and AHC wave compensation."""

    RENDER_FACTOR: float = 1.25  # Render when tension >= 125% target
    HEAVE_FACTOR: float = 0.75  # Heave when tension <= 75% target
    MIN_AHC_EFFICIENCY_PCT: float = 85.0
    MAX_SAFE_LINE_TENSION_MBL_PCT: float = 50.0  # MEG4 safe working limit

    def compute_ahc_efficiency(
        self, ship_amp_m: float, load_rms_m: float
    ) -> float:
        """Calculate AHC wave heave filtering efficiency."""
        ship_rms = ship_amp_m / math.sqrt(2.0)
        if ship_rms <= 0.001:
            return 100.0
        eff = (1.0 - (load_rms_m / ship_rms)) * 100.0
        return round(min(100.0, max(0.0, eff)), 2)

    def evaluate(self, sensor: WinchSensorInput) -> AutoTensionAhcReport:
        warnings: List[str] = []
        target_kn = sensor.mbl_kn * (sensor.target_tension_pct_mbl / 100.0)
        render_kn = target_kn * self.RENDER_FACTOR
        heave_kn = target_kn * self.HEAVE_FACTOR

        tension_pct_mbl = (sensor.measured_tension_kn / max(sensor.mbl_kn, 1.0)) * 100.0

        # Auto-tension logic
        if tension_pct_mbl >= self.MAX_SAFE_LINE_TENSION_MBL_PCT:
            action = WinchActionState.OVERLOAD_ALARM
            warnings.append(
                f"Line tension {tension_pct_mbl:.1f}% MBL exceeds MEG4 limit {self.MAX_SAFE_LINE_TENSION_MBL_PCT}%"
            )
        elif sensor.measured_tension_kn >= render_kn:
            action = WinchActionState.RENDER_OUT
            warnings.append(
                f"Tension {sensor.measured_tension_kn:.1f} kN >= render threshold {render_kn:.1f} kN: Auto-rendering line"
            )
        elif sensor.measured_tension_kn <= heave_kn:
            action = WinchActionState.HEAVE_IN
            warnings.append(
                f"Tension {sensor.measured_tension_kn:.1f} kN <= heave threshold {heave_kn:.1f} kN: Auto-heaving line"
            )
        else:
            action = WinchActionState.HOLD

        # Active Heave Compensation (AHC)
        ahc_eff = self.compute_ahc_efficiency(
            sensor.ship_heave_amplitude_m, sensor.load_displacement_rms_m
        )
        is_ahc_active = sensor.ship_heave_amplitude_m > 0.1

        if is_ahc_active and ahc_eff < self.MIN_AHC_EFFICIENCY_PCT:
            warnings.append(
                f"AHC compensation efficiency {ahc_eff}% below IMCA minimum {self.MIN_AHC_EFFICIENCY_PCT}%"
            )

        # Feedforward winch velocity compensation
        omega = (2.0 * math.pi) / max(sensor.wave_period_s, 1.0)
        max_feedforward_vel = sensor.ship_heave_amplitude_m * omega

        return AutoTensionAhcReport(
            winch_id=sensor.winch_id,
            action_state=action,
            is_ahc_active=is_ahc_active,
            ahc_efficiency_pct=ahc_eff,
            target_tension_kn=round(target_kn, 2),
            render_threshold_kn=round(render_kn, 2),
            heave_threshold_kn=round(heave_kn, 2),
            command_winch_speed_m_s=round(max_feedforward_vel, 3),
            warnings=warnings,
            metrics={
                "measured_tension_kn": sensor.measured_tension_kn,
                "target_tension_kn": target_kn,
                "tension_pct_mbl": tension_pct_mbl,
                "ahc_efficiency_pct": ahc_eff,
                "command_velocity_m_s": max_feedforward_vel,
            },
        )


__all__ = [
    "WinchActionState",
    "WinchSensorInput",
    "AutoTensionAhcReport",
    "MooringAutoTensionAhcEngine",
]
