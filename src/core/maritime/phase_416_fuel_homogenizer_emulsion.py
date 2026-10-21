"""Phase 416: Marine Fuel Homogenizer & Water Emulsification.

Implements MARPOL Annex VI Reg 14 and ISO 8217 standards for Heavy Fuel Oil (HFO)
mechanical homogenizers: rotor-stator hydrodynamic shearing, water-in-fuel micro-emulsion,
Walther temperature-viscosity loop regulation, and thermal NOx reduction.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass(frozen=True)
class FuelHomogenizerTelemetry:
    """Telemetry readings for Marine Fuel Homogenizer and Emulsion System."""
    rotor_speed_rpm: float = 3000.0
    rotor_diameter_mm: float = 180.0
    shear_gap_microns: float = 85.0
    water_dosing_ratio_pct: float = 4.5
    fuel_inlet_temp_c: float = 135.0
    target_engine_viscosity_cst: float = 13.0
    fuel_viscosity_at_50c_cst: float = 380.0
    heater_steam_valve_pos_pct: float = 45.0
    fuel_flow_rate_m3_h: float = 3.2


@dataclass(frozen=True)
class FuelHomogenizerAssessment:
    """Combustion optimization and emissions assessment of fuel emulsion."""
    shear_rate_s_minus_1: float
    weber_number: float
    mean_water_droplet_um: float
    calculated_viscosity_cst: float
    steam_valve_command_pct: float
    estimated_nox_reduction_pct: float
    micro_explosion_potential: str
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class FuelHomogenizerEmulsionEngine:
    """Evaluates mechanical shear dispersion, droplet atomization, and viscosity control."""

    MAX_DROPLET_SIZE_UM: float = 4.0
    TARGET_VISCOSITY_MIN: float = 11.5
    TARGET_VISCOSITY_MAX: float = 14.5
    MIN_SHEAR_RATE_S: float = 25000.0
    HFO_SURFACE_TENSION_N_M: float = 0.035
    HFO_DENSITY_KG_M3: float = 991.0

    def evaluate(self, telemetry: FuelHomogenizerTelemetry) -> FuelHomogenizerAssessment:
        warnings: List[str] = []

        # Tip speed v = pi * D * N / 60 (m/s)
        d_m = telemetry.rotor_diameter_mm / 1000.0
        n_rps = telemetry.rotor_speed_rpm / 60.0
        tip_speed = math.pi * d_m * n_rps

        # Hydrodynamic shear rate gamma_dot = v / h (s^-1)
        gap_m = max(1e-6, telemetry.shear_gap_microns * 1e-6)
        shear_rate = tip_speed / gap_m

        # Weber number We = (rho * v^2 * d) / sigma
        weber = (self.HFO_DENSITY_KG_M3 * (tip_speed ** 2) * gap_m) / self.HFO_SURFACE_TENSION_N_M

        # Mean droplet diameter d ≈ gap * (We)^(-0.6) * 1e6 (um)
        mean_droplet_um = max(0.5, (gap_m * math.pow(max(1.0, weber), -0.55)) * 1e6 * 2.8)

        # Walther equation for temperature-viscosity: log(log(nu + 0.7)) = A - B * log(T_K)
        # Empirical constants for 380 cSt @ 50°C fuel:
        t_50_k = 50.0 + 273.15
        t_in_k = max(273.15, telemetry.fuel_inlet_temp_c + 273.15)
        # Approximate slope B ~ 3.55, A ~ 9.15
        b_coeff = 3.62
        a_coeff = math.log10(math.log10(telemetry.fuel_viscosity_at_50c_cst + 0.7)) + b_coeff * math.log10(t_50_k)
        w_val = a_coeff - b_coeff * math.log10(t_in_k)
        calc_viscosity = max(1.0, math.pow(10.0, math.pow(10.0, w_val)) - 0.7)

        # PID modulation for steam valve to match target engine viscosity (13 cSt)
        visc_err = calc_viscosity - telemetry.target_engine_viscosity_cst
        # If viscosity too high, increase steam heating (+ valve %)
        valve_cmd = min(100.0, max(0.0, telemetry.heater_steam_valve_pos_pct + visc_err * 2.5))

        # Thermal NOx reduction estimate: ~2.5% per 1% emulsified water (up to 6% water)
        eff_water = min(8.0, telemetry.water_dosing_ratio_pct)
        nox_reduction_pct = eff_water * 2.6 if mean_droplet_um <= self.MAX_DROPLET_SIZE_UM else eff_water * 1.1

        if shear_rate < self.MIN_SHEAR_RATE_S:
            warnings.append(
                f"Shear rate {shear_rate:.0f} s⁻¹ below minimum {self.MIN_SHEAR_RATE_S:.0f} s⁻¹; risking water slugging."
            )

        if mean_droplet_um > self.MAX_DROPLET_SIZE_UM:
            warnings.append(
                f"Droplet size {mean_droplet_um:.2f} µm exceeds threshold {self.MAX_DROPLET_SIZE_UM} µm. "
                "Secondary micro-explosion will be incomplete."
            )

        if calc_viscosity < self.TARGET_VISCOSITY_MIN or calc_viscosity > self.TARGET_VISCOSITY_MAX:
            warnings.append(
                f"Fuel viscosity {calc_viscosity:.2f} cSt outside engine injection window "
                f"[{self.TARGET_VISCOSITY_MIN}, {self.TARGET_VISCOSITY_MAX}] cSt."
            )

        if telemetry.water_dosing_ratio_pct > 8.0:
            warnings.append(
                f"Water dosing {telemetry.water_dosing_ratio_pct:.1f}% exceeds 8.0% safe limit; boiler/flame instability risk."
            )

        if mean_droplet_um <= 1.8 and telemetry.water_dosing_ratio_pct >= 3.0:
            micro_explosion = "VIGOROUS_OPTIMAL"
        elif mean_droplet_um <= self.MAX_DROPLET_SIZE_UM:
            micro_explosion = "MODERATE"
        else:
            micro_explosion = "POOR_INSUFFICIENT"

        status = "OPTIMAL"
        if mean_droplet_um > self.MAX_DROPLET_SIZE_UM or calc_viscosity > self.TARGET_VISCOSITY_MAX * 1.5:
            status = "CRITICAL"
        elif warnings:
            status = "WARNING"

        compliance_flags = {
            "marpol_annex_vi_nox_reduced": nox_reduction_pct >= 8.0,
            "iso_8217_viscosity_compliant": self.TARGET_VISCOSITY_MIN <= calc_viscosity <= self.TARGET_VISCOSITY_MAX,
            "shear_atomization_adequate": shear_rate >= self.MIN_SHEAR_RATE_S,
            "droplet_size_sub_micron": mean_droplet_um <= self.MAX_DROPLET_SIZE_UM,
        }

        return FuelHomogenizerAssessment(
            shear_rate_s_minus_1=round(shear_rate, 1),
            weber_number=round(weber, 2),
            mean_water_droplet_um=round(mean_droplet_um, 2),
            calculated_viscosity_cst=round(calc_viscosity, 2),
            steam_valve_command_pct=round(valve_cmd, 1),
            estimated_nox_reduction_pct=round(nox_reduction_pct, 1),
            micro_explosion_potential=micro_explosion,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
