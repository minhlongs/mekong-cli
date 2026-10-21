"""Phase 405: Stern Tube Environmentally Acceptable Lubricant (EAL) Hydrodynamic System.

Implements US Vessel General Permit (VGP 2013) / DNV Rules Pt.4 Ch.4, Walther-ASTM D341
viscosity-temperature relation, Sommerfeld lubrication number, film parameter lambda > 3,
draft differential pressure control (aft seal delta P), and bio-oil oxidative degradation.
Strictly < 200 LOC, zero mocks, pure analytical physics.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Dict, List


class LubricationRegime(str, Enum):
    HYDRODYNAMIC_FULL_FILM = "HYDRODYNAMIC_FULL_FILM"
    MIXED_LUBRICATION = "MIXED_LUBRICATION"
    BOUNDARY_LUBRICATION = "BOUNDARY_LUBRICATION"


@dataclass(frozen=True)
class SternTubeTelemetry:
    """Telemetry readings for propeller shaft stern tube bearing and seal."""
    bearing_temperature_c: float = 48.0
    shaft_speed_rpm: float = 85.0
    shaft_diameter_m: float = 0.52
    bearing_length_m: float = 1.04
    radial_clearance_m: float = 0.00065  # c = 0.65 mm
    bearing_load_n: float = 185000.0     # 185 kN static/dynamic reaction
    composite_roughness_um: float = 0.85 # Combined surface roughness sigma (bearing + journal)
    aft_draft_m: float = 9.8             # Seawater head
    header_tank_height_above_draft_m: float = 2.5
    seal_oil_pressure_bar: float = 1.25
    seawater_density_kg_m3: float = 1025.0
    eal_viscosity_40c_cst: float = 68.0  # ISO VG 68 synthetic ester
    eal_viscosity_100c_cst: float = 10.5
    eal_water_content_ppm: float = 350.0 # VGP limit < 1000 ppm
    total_acid_number_tan_mg_koh_g: float = 0.65 # Alarm > 2.0


@dataclass(frozen=True)
class SternTubeAssessment:
    """Assessment of stern tube lubrication regime, lambda ratio, and seal integrity."""
    dynamic_viscosity_pa_s: float
    sommerfeld_number: float
    minimum_film_thickness_um: float
    film_parameter_lambda: float
    regime: LubricationRegime
    differential_seal_pressure_bar: float
    oil_overpressure_adequate: bool
    eal_health_status: str
    compliance_flags: Dict[str, bool]
    warnings: List[str] = field(default_factory=list)


class SternTubeBioLubricationEngine:
    """Hydrodynamic journal bearing calculation and VGP 2013 EAL compliance."""

    GRAVITY_M_S2: float = 9.80665

    def calculate_walther_viscosity(self, temp_c: float, v40: float, v100: float) -> float:
        """Walther / ASTM D341 equation for kinematic viscosity nu (cSt) at temp_c."""
        t1 = 40.0 + 273.15
        t2 = 100.0 + 273.15
        tx = max(0.0, temp_c) + 273.15

        # W = log10(log10(nu + 0.7))
        w1 = math.log10(math.log10(v40 + 0.7))
        w2 = math.log10(math.log10(v100 + 0.7))
        b = (w1 - w2) / (math.log10(t2) - math.log10(t1))
        a = w1 + b * math.log10(t1)

        wx = a - b * math.log10(tx)
        nu_cst = max(1.0, (10.0 ** (10.0**wx)) - 0.7)
        # Convert cSt to dynamic viscosity Pa.s (assuming density ~ 915 kg/m3)
        return (nu_cst * 1e-6) * 915.0

    def evaluate(self, telemetry: SternTubeTelemetry) -> SternTubeAssessment:
        warnings: List[str] = []

        mu = self.calculate_walther_viscosity(
            telemetry.bearing_temperature_c,
            telemetry.eal_viscosity_40c_cst,
            telemetry.eal_viscosity_100c_cst,
        )

        n_rev_per_s = max(0.01, telemetry.shaft_speed_rpm / 60.0)
        proj_area = telemetry.shaft_diameter_m * telemetry.bearing_length_m
        p_load = telemetry.bearing_load_n / max(0.01, proj_area)
        r = telemetry.shaft_diameter_m / 2.0
        c = max(1e-5, telemetry.radial_clearance_m)

        # Sommerfeld number S = (r/c)^2 * (mu * N / P)
        sommerfeld = ((r / c) ** 2) * (mu * n_rev_per_s / max(1.0, p_load))

        # Eccentricity ratio epsilon approximation: epsilon ~ 1 / (1 + 0.6 * S^0.8)
        epsilon = min(0.98, max(0.05, 1.0 / (1.0 + 0.6 * (sommerfeld**0.8))))
        h_min_m = c * (1.0 - epsilon)
        h_min_um = round(h_min_m * 1e6, 2)

        # Film parameter lambda = h_min / sigma
        sigma_um = max(0.1, telemetry.composite_roughness_um)
        lambda_ratio = round(h_min_um / sigma_um, 2)

        if lambda_ratio >= 3.0:
            regime = LubricationRegime.HYDRODYNAMIC_FULL_FILM
        elif lambda_ratio >= 1.0:
            regime = LubricationRegime.MIXED_LUBRICATION
            warnings.append(
                f"LUBRICATION WARNING: Film lambda {lambda_ratio:.2f} < 3.0 indicates mixed lubrication / partial asperity contact."
            )
        else:
            regime = LubricationRegime.BOUNDARY_LUBRICATION
            warnings.append(
                f"LUBRICATION CRITICAL: Film lambda {lambda_ratio:.2f} < 1.0 indicates severe boundary contact / wear!"
            )

        # Draft hydrostatic pressure P_sw = rho * g * draft (in bar)
        p_sw_bar = (telemetry.seawater_density_kg_m3 * self.GRAVITY_M_S2 * telemetry.aft_draft_m) / 100000.0
        # Target header oil pressure must maintain +0.15 to +0.30 bar over seawater
        delta_p_seal = round(telemetry.seal_oil_pressure_bar - p_sw_bar, 3)
        oil_overpressure_ok = 0.10 <= delta_p_seal <= 0.50

        if delta_p_seal < 0.10:
            warnings.append(
                f"SEAL INGRESS RISK: Seal oil differential {delta_p_seal:.3f} bar < +0.10 bar! Risk of seawater ingress."
            )
        elif delta_p_seal > 0.50:
            warnings.append(
                f"SEAL EGRESS RISK: Seal oil differential {delta_p_seal:.3f} bar > +0.50 bar! Risk of EAL leakage overboard."
            )

        # EAL chemical degradation (VGP compliance)
        eal_ok = (telemetry.eal_water_content_ppm < 1000.0) and (telemetry.total_acid_number_tan_mg_koh_g < 2.0)
        if not eal_ok:
            if telemetry.eal_water_content_ppm >= 1000.0:
                warnings.append(
                    f"EAL MOISTURE HIGH: Water content {telemetry.eal_water_content_ppm:.0f} ppm >= 1000 ppm VGP limit!"
                )
            if telemetry.total_acid_number_tan_mg_koh_g >= 2.0:
                warnings.append(
                    f"EAL ACIDITY HIGH: TAN {telemetry.total_acid_number_tan_mg_koh_g:.2f} mg KOH/g indicates ester hydrolysis."
                )

        compliance_flags = {
            "vgp_2013_eal_water_acceptable": telemetry.eal_water_content_ppm < 1000.0,
            "vgp_tan_within_limits": telemetry.total_acid_number_tan_mg_koh_g < 2.0,
            "hydrodynamic_lambda_safe": lambda_ratio >= 3.0,
            "aft_seal_positive_differential": delta_p_seal >= 0.10,
            "bearing_temp_normal": telemetry.bearing_temperature_c <= 65.0,
        }

        return SternTubeAssessment(
            dynamic_viscosity_pa_s=round(mu, 5),
            sommerfeld_number=round(sommerfeld, 4),
            minimum_film_thickness_um=h_min_um,
            film_parameter_lambda=lambda_ratio,
            regime=regime,
            differential_seal_pressure_bar=delta_p_seal,
            oil_overpressure_adequate=oil_overpressure_ok,
            eal_health_status="HEALTHY" if eal_ok else "DEGRADED",
            compliance_flags=compliance_flags,
            warnings=warnings,
        )
