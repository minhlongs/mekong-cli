"""Phase 421: Ballast Water Management System (BWMS) Electro-Chlorination & Neutralization.

Implements IMO BWM Convention Regulation D-2, USCG Phase-II ETV protocol, and
MEPC.300(72) standards: electro-chlorination generation of Sodium Hypochlorite (NaOCl),
ballasting TRO control (1.5-2.0 mg/L), hydrogen (H2) safety degassing (< 1.0% vol),
and de-ballasting stoichiometric neutralization (NaHSO3) for discharge TRO <= 0.10 mg/L.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BwmsChlorinationTelemetry:
    """Telemetry readings for BWMS Electro-chlorination & Neutralization Unit."""
    operational_mode: str = "DEBALLASTING"  # "BALLASTING" or "DEBALLASTING"
    tro_sensor_reading_mg_l: float = 0.03
    ballast_water_flow_m3_h: float = 500.0
    electrolytic_cell_current_a: float = 1200.0
    electrolytic_cell_voltage_v: float = 18.5
    cell_hydrogen_pct_vol: float = 0.22
    degassing_blower_running: bool = True
    neutralizer_dosing_rate_l_h: float = 4.8
    neutralizer_storage_level_pct: float = 65.0


@dataclass(frozen=True)
class BwmsChlorinationAssessment:
    """Safety and chemical discharge compliance assessment for BWMS."""
    tro_discharge_compliant: bool
    hydrogen_safety_compliant: bool
    neutralizer_dosing_active: bool
    electrolysis_efficiency_kg_cl2_h: float
    required_neutralizer_l_h: float
    discharge_interlock_open: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class BwmsChlorinationNeutralizationEngine:
    """Evaluates electro-chlorination cell kinetics, H2 interlocks, and neutralization dosing."""

    MAX_DISCHARGE_TRO_MG_L: float = 0.10
    USCG_DISCHARGE_TRO_MG_L: float = 0.05
    TARGET_BALLAST_TRO_MIN_MG_L: float = 1.5
    TARGET_BALLAST_TRO_MAX_MG_L: float = 2.0
    MAX_H2_PCT_VOL: float = 1.0  # 25% LEL of Hydrogen
    FARADAY_CONSTANT: float = 96485.0  # C / mol electrons
    CHLORINE_MOLAR_MASS_G_MOL: float = 70.9  # Cl2

    def evaluate(self, telemetry: BwmsChlorinationTelemetry) -> BwmsChlorinationAssessment:
        warnings: List[str] = []

        # Faraday's law of electrolysis: m_dot = (I * eta * M) / (z * F) * 3600
        # z = 2 electrons per Cl2 molecule; estimated current efficiency eta ~ 85%
        eta_efficiency = 0.85
        cl2_prod_kg_h = (
            (telemetry.electrolytic_cell_current_a * eta_efficiency * self.CHLORINE_MOLAR_MASS_G_MOL)
            / (2.0 * self.FARADAY_CONSTANT)
        ) * 3.6

        # Hydrogen Safety Interlock
        h2_safe = (
            telemetry.cell_hydrogen_pct_vol < self.MAX_H2_PCT_VOL
            and telemetry.degassing_blower_running
        )
        if telemetry.cell_hydrogen_pct_vol >= self.MAX_H2_PCT_VOL:
            warnings.append(
                f"Electrolytic cell H2 exceeds LEL safety limit: {telemetry.cell_hydrogen_pct_vol:.2f}% vol "
                f"(limit < {self.MAX_H2_PCT_VOL:.1f}% vol)"
            )
        if not telemetry.degassing_blower_running:
            warnings.append("Degassing blower failure! Risk of explosive hydrogen accumulation")

        is_deballasting = telemetry.operational_mode.upper() == "DEBALLASTING"

        # Stoichiometric Neutralizer Requirement (NaHSO3 38% wt solution: ~1.46 kg NaHSO3 per kg Cl2)
        # For de-ballasting flow Q (m3/h) with residual TRO:
        inlet_tro_mg_l = max(0.5, telemetry.tro_sensor_reading_mg_l * 10.0) if is_deballasting else 0.0
        tro_mass_kg_h = (telemetry.ballast_water_flow_m3_h * inlet_tro_mg_l) / 1000.0
        req_neutralizer_l_h = tro_mass_kg_h * 2.85  # liters of 38% solution per kg TRO

        tro_compliant = True
        if is_deballasting:
            tro_compliant = telemetry.tro_sensor_reading_mg_l <= self.MAX_DISCHARGE_TRO_MG_L
            if not tro_compliant:
                warnings.append(
                    f"Overboard discharge TRO exceeds D-2 limit: {telemetry.tro_sensor_reading_mg_l:.3f} mg/L "
                    f"(limit <= {self.MAX_DISCHARGE_TRO_MG_L:.2f} mg/L)"
                )
        else:
            # Ballasting Mode
            in_range = (
                self.TARGET_BALLAST_TRO_MIN_MG_L
                <= telemetry.tro_sensor_reading_mg_l
                <= self.TARGET_BALLAST_TRO_MAX_MG_L
            )
            if not in_range:
                warnings.append(
                    f"Ballasting TRO out of biocidal target: {telemetry.tro_sensor_reading_mg_l:.2f} mg/L "
                    f"(target {self.TARGET_BALLAST_TRO_MIN_MG_L}-{self.TARGET_BALLAST_TRO_MAX_MG_L} mg/L)"
                )

        discharge_allowed = tro_compliant and h2_safe

        status = "COMPLIANT_ACTIVE" if discharge_allowed else "INTERLOCK_HALTED"
        if not h2_safe:
            status = "H2_DEGAS_ALARM"

        compliance_flags = {
            "tro_discharge_d2_compliant": tro_compliant,
            "h2_under_lel_threshold": h2_safe,
            "neutralizer_stock_sufficient": telemetry.neutralizer_storage_level_pct > 15.0,
            "degassing_blower_active": telemetry.degassing_blower_running,
            "overboard_discharge_permitted": discharge_allowed,
        }

        return BwmsChlorinationAssessment(
            tro_discharge_compliant=tro_compliant,
            hydrogen_safety_compliant=h2_safe,
            neutralizer_dosing_active=telemetry.neutralizer_dosing_rate_l_h > 0.1,
            electrolysis_efficiency_kg_cl2_h=round(cl2_prod_kg_h, 3),
            required_neutralizer_l_h=round(req_neutralizer_l_h, 2),
            discharge_interlock_open=discharge_allowed,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
