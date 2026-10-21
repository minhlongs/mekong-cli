"""Phase 431: Marine Stern Tube Lube Oil Gravity Tank, Differential Pressure & Seal Temperature.

Implements DNV-RU-SHIP Pt.4 Ch.4, ISO 19973:
- Stern tube gravity tank hydrostatic head vs ship draft differential pressure control (+0.15 to +0.35 bar).
- Forward and aft lip seal temperature monitoring (warning >= 70 C, alarm >= 75 C).
- Water-in-oil capacitance/permittivity sensing (<= 1.0% limit, purge trigger at >= 1.5%).
Strictly < 160 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SternTubeLubeTelemetry:
    """Telemetry readings for stern tube lubrication and shaft seals."""
    gravity_tank_level_pct: float = 85.0
    gravity_tank_height_m: float = 6.5  # Head above shaft centerline
    ship_draft_m: float = 8.2  # Seawater draft above shaft centerline
    lube_oil_density_kg_m3: float = 890.0
    seawater_density_kg_m3: float = 1025.0
    fwd_seal_temp_c: float = 52.0
    aft_seal_temp_c: float = 58.0
    water_content_pct: float = 0.35
    lube_oil_flow_l_min: float = 18.5


@dataclass(frozen=True)
class SternTubeLubeAssessment:
    """Hydrostatic pressure differential, seal thermal integrity, and purity assessment."""
    lube_pressure_bar: float
    seawater_pressure_bar: float
    differential_pressure_bar: float
    dp_in_envelope: bool
    seal_overheat: bool
    water_contamination: bool
    purge_required: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class SternTubeLubeEngine:
    """Evaluates stern tube hydrostatic head, differential pressure, and seal temperatures."""

    MIN_DP_BAR: float = 0.15
    MAX_DP_BAR: float = 0.35
    SEAL_WARN_TEMP_C: float = 70.0
    SEAL_ALARM_TEMP_C: float = 75.0
    MAX_WATER_CONTENT_PCT: float = 1.00
    PURGE_WATER_CONTENT_PCT: float = 1.50
    GRAVITY: float = 9.80665

    def evaluate(self, telemetry: SternTubeLubeTelemetry) -> SternTubeLubeAssessment:
        warnings: List[str] = []

        # Hydrostatic pressures: P = rho * g * h (Pa) -> 1 bar = 100,000 Pa
        lube_press_pa = telemetry.lube_oil_density_kg_m3 * self.GRAVITY * max(0.0, telemetry.gravity_tank_height_m)
        seawater_press_pa = telemetry.seawater_density_kg_m3 * self.GRAVITY * max(0.0, telemetry.ship_draft_m)

        lube_press_bar = round(lube_press_pa / 100000.0, 3)
        seawater_press_bar = round(seawater_press_pa / 100000.0, 3)
        differential_bar = round(lube_press_bar - seawater_press_bar, 3)

        dp_in_envelope = self.MIN_DP_BAR <= differential_bar <= self.MAX_DP_BAR
        if differential_bar < self.MIN_DP_BAR:
            warnings.append(f"CRITICAL: Low stern tube DP ({differential_bar:.2f} bar) - seawater ingress hazard")
        elif differential_bar > self.MAX_DP_BAR:
            warnings.append(f"WARNING: High stern tube DP ({differential_bar:.2f} bar) - lip seal wear/oil leak hazard")

        max_seal_temp = max(telemetry.fwd_seal_temp_c, telemetry.aft_seal_temp_c)
        seal_overheat = max_seal_temp >= self.SEAL_ALARM_TEMP_C
        if max_seal_temp >= self.SEAL_ALARM_TEMP_C:
            warnings.append(f"CRITICAL: Shaft seal temperature alarm ({max_seal_temp:.1f} °C >= {self.SEAL_ALARM_TEMP_C} °C)")
        elif max_seal_temp >= self.SEAL_WARN_TEMP_C:
            warnings.append(f"WARNING: Shaft seal temperature high ({max_seal_temp:.1f} °C)")

        water_contamination = telemetry.water_content_pct > self.MAX_WATER_CONTENT_PCT
        purge_required = telemetry.water_content_pct >= self.PURGE_WATER_CONTENT_PCT
        if purge_required:
            warnings.append(f"CRITICAL: Excessive water in stern lube oil ({telemetry.water_content_pct:.2f}% >= {self.PURGE_WATER_CONTENT_PCT}%) - purge triggered")
        elif water_contamination:
            warnings.append(f"WARNING: Water content high in lube oil ({telemetry.water_content_pct:.2f}%)")

        if telemetry.gravity_tank_level_pct < 50.0:
            warnings.append(f"WARNING: Low stern tube gravity tank level ({telemetry.gravity_tank_level_pct:.1f}%)")

        # Status determination
        if seal_overheat or purge_required or differential_bar < 0.05:
            status = "CRITICAL_SEAL_FAILURE_RISK"
        elif not dp_in_envelope or water_contamination or max_seal_temp >= self.SEAL_WARN_TEMP_C:
            status = "ABNORMAL_OPERATION"
        else:
            status = "OPTIMAL_LUBRICATION"

        compliance_flags = {
            "DNV_DP_ENVELOPE": dp_in_envelope,
            "SEAL_THERMAL_SAFE": not seal_overheat,
            "WATER_PURITY_SAFE": not water_contamination,
            "ISO_19973_COMPLIANT": dp_in_envelope and not seal_overheat and not water_contamination,
        }

        return SternTubeLubeAssessment(
            lube_pressure_bar=lube_press_bar,
            seawater_pressure_bar=seawater_press_bar,
            differential_pressure_bar=differential_bar,
            dp_in_envelope=dp_in_envelope,
            seal_overheat=seal_overheat,
            water_contamination=water_contamination,
            purge_required=purge_required,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
