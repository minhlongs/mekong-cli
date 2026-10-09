"""Phase 404: Stern Tube Lubrication & Bio-Lubricant Seal Water Ingress / EAL Degradation.

Complies with US EPA Vessel General Permit (VGP 2013) Section 2.2.9 and DNV GL Pt.4 Ch.2.
Monitors differential lip seal pressure, water contamination in EAL, and viscosity shift.
Strictly < 180 LOC, zero-mock deterministic marine tribology.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class SternTubeSealStatus(str, Enum):
    """Integrity state of stern tube sealing and bio-lubricant."""
    SEAL_INTEGRITY_NORMAL = "SEAL_INTEGRITY_NORMAL"
    WATER_INGRESS_WARNING = "WATER_INGRESS_WARNING"
    WATER_INGRESS_CRITICAL = "WATER_INGRESS_CRITICAL"
    PRESSURE_DIFFERENTIAL_ALARM = "PRESSURE_DIFFERENTIAL_ALARM"
    EAL_VISCOSITY_DEGRADED = "EAL_VISCOSITY_DEGRADED"


@dataclass
class SternTubeInput:
    """Aft and forward stern tube seal telemetry and oil lab condition."""
    lube_header_pressure_bar: float = 0.55  # Lube oil pressure in aft seal ring cavity
    seawater_draft_pressure_bar: float = 0.32  # Seawater hydrostatic head at shaft centerline
    water_content_ppm: float = 350.0  # Moisture in oil (VGP target <= 1000 ppm)
    viscosity_cst_40c: float = 68.0  # Measured kinematic viscosity at 40°C
    nominal_viscosity_cst: float = 68.0  # Nominal fresh oil rating (e.g. ISO VG 68)
    aft_bearing_temp_c: float = 52.0  # White metal bearing temperature (limit < 65°C)
    header_tank_level_pct: float = 85.0  # Gravity header tank oil level (low alarm < 60%)


@dataclass
class SternTubeResult:
    """Evaluation result for stern tube lip seals and EAL bio-oil."""
    status: SternTubeSealStatus
    pressure_diff_bar: float
    seal_barrier_intact: bool
    eal_water_compliant: bool
    eal_viscosity_compliant: bool
    bearing_thermal_safe: bool
    drain_catch_volume_indicated: bool
    warnings: List[str] = field(default_factory=list)


class SternTubeEngine:
    """Physics-based evaluation engine for stern tube seals and EAL oil."""

    MIN_DIFF_PRESSURE_BAR = 0.15
    MAX_DIFF_PRESSURE_BAR = 0.35
    WARN_WATER_PPM = 1000.0  # VGP 2013 warning boundary
    CRIT_WATER_PPM = 1500.0  # Critical emulsification trip boundary
    MAX_VISCOSITY_DEVIATION_PCT = 10.0
    MAX_BEARING_TEMP_C = 65.0
    MIN_HEADER_LEVEL_PCT = 60.0

    def evaluate(self, telemetry: SternTubeInput) -> SternTubeResult:
        warnings: List[str] = []

        diff_p = telemetry.lube_header_pressure_bar - telemetry.seawater_draft_pressure_bar
        seal_barrier_intact = (
            self.MIN_DIFF_PRESSURE_BAR <= diff_p <= self.MAX_DIFF_PRESSURE_BAR
            and telemetry.header_tank_level_pct >= self.MIN_HEADER_LEVEL_PCT
        )

        if diff_p < self.MIN_DIFF_PRESSURE_BAR:
            warnings.append(
                f"Low seal differential pressure: {diff_p:.3f} bar < {self.MIN_DIFF_PRESSURE_BAR} bar. "
                "Risk of seawater ingress into stern tube."
            )
        elif diff_p > self.MAX_DIFF_PRESSURE_BAR:
            warnings.append(
                f"High seal differential pressure: {diff_p:.3f} bar > {self.MAX_DIFF_PRESSURE_BAR} bar. "
                "Risk of lip seal extrusion or oil egress to sea."
            )

        if telemetry.header_tank_level_pct < self.MIN_HEADER_LEVEL_PCT:
            warnings.append(
                f"Stern tube header tank level low: {telemetry.header_tank_level_pct}% < {self.MIN_HEADER_LEVEL_PCT}%"
            )

        eal_water_compliant = telemetry.water_content_ppm <= self.WARN_WATER_PPM
        if telemetry.water_content_ppm > self.CRIT_WATER_PPM:
            warnings.append(
                f"Critical water ingress in bio-lubricant: {telemetry.water_content_ppm} ppm > {self.CRIT_WATER_PPM} ppm. "
                "Severe hydrodynamic film collapse danger."
            )
        elif telemetry.water_content_ppm > self.WARN_WATER_PPM:
            warnings.append(
                f"Elevated water ingress in bio-lubricant: {telemetry.water_content_ppm} ppm > {self.WARN_WATER_PPM} ppm. "
                "Exceeds US EPA VGP recommendation."
            )

        visc_dev = abs(telemetry.viscosity_cst_40c - telemetry.nominal_viscosity_cst) / telemetry.nominal_viscosity_cst * 100.0
        eal_viscosity_compliant = visc_dev <= self.MAX_VISCOSITY_DEVIATION_PCT
        if not eal_viscosity_compliant:
            warnings.append(
                f"EAL viscosity deviation {visc_dev:.1f}% exceeds ±{self.MAX_VISCOSITY_DEVIATION_PCT}% limit."
            )

        bearing_thermal_safe = telemetry.aft_bearing_temp_c <= self.MAX_BEARING_TEMP_C
        if not bearing_thermal_safe:
            warnings.append(
                f"Aft stern tube bearing temp {telemetry.aft_bearing_temp_c}°C exceeds limit {self.MAX_BEARING_TEMP_C}°C."
            )

        drain_catch_volume_indicated = telemetry.water_content_ppm > 500.0

        if telemetry.water_content_ppm > self.CRIT_WATER_PPM:
            status = SternTubeSealStatus.WATER_INGRESS_CRITICAL
        elif not seal_barrier_intact:
            status = SternTubeSealStatus.PRESSURE_DIFFERENTIAL_ALARM
        elif not eal_water_compliant:
            status = SternTubeSealStatus.WATER_INGRESS_WARNING
        elif not eal_viscosity_compliant:
            status = SternTubeSealStatus.EAL_VISCOSITY_DEGRADED
        else:
            status = SternTubeSealStatus.SEAL_INTEGRITY_NORMAL

        return SternTubeResult(
            status=status,
            pressure_diff_bar=round(diff_p, 4),
            seal_barrier_intact=seal_barrier_intact,
            eal_water_compliant=eal_water_compliant,
            eal_viscosity_compliant=eal_viscosity_compliant,
            bearing_thermal_safe=bearing_thermal_safe,
            drain_catch_volume_indicated=drain_catch_volume_indicated,
            warnings=warnings,
        )
