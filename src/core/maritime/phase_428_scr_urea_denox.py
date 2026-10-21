"""Phase 428: Selective Catalytic Reduction (SCR) Urea / DEF De-NOx Kinetics.

Implements IMO Tier III, NOx Technical Code 2008, and MEPC.198(62):
AUS 40 urea thermolysis & hydrolysis to NH3, stoichiometric De-NOx reduction,
catalyst Minimum Operating Temperature (MOT >= 300°C) Ammonium Bisulfate (ABS)
condensation inhibition, ammonia slip compliance (<= 10.0 ppm), and catalyst dP sootblower.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SCRDeNOxTelemetry:
    """Telemetry readings for Marine SCR De-NOx and Urea Injection System."""
    exhaust_gas_flow_kg_h: float = 85000.0
    catalyst_inlet_temp_c: float = 330.0  # Must be >= 300°C to prevent ABS deposit
    raw_nox_ppm: float = 1150.0  # Uncontrolled Tier II level
    exhaust_nox_outlet_ppm: float = 195.0  # Measured at SCR outlet
    ammonia_slip_ppm: float = 4.2  # MEPC limit <= 10.0 ppm
    catalyst_dp_kpa: float = 1.45  # Clean <= 1.2 kPa, sootblow >= 2.2 kPa, trip >= 3.5 kPa
    urea_solution_concentration_pct: float = 40.0  # Standard AUS 40
    def_tank_level_pct: float = 68.0
    scr_bypass_damper_open: bool = False
    sootblower_active: bool = False


@dataclass(frozen=True)
class SCRDeNOxAssessment:
    """SCR De-NOx catalytic reduction efficiency, urea dosing, and compliance status."""
    denox_efficiency_pct: float
    urea_dosing_rate_l_h: float
    ammonia_slip_compliant: bool
    tier_iii_compliant: bool
    catalyst_sootblower_demanded: bool
    abs_condensation_risk: bool
    urea_injection_inhibited: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class SCRDeNOxEngine:
    """Evaluates marine SCR De-NOx kinetics, urea dosing rates, and catalyst health."""

    MIN_CATALYST_TEMP_MOT_C: float = 300.0
    AMMONIA_SLIP_LIMIT_PPM: float = 10.0
    TARGET_DENOX_EFFICIENCY_MIN_PCT: float = 75.0
    CATALYST_DP_SOOTBLOW_KPA: float = 2.2
    CATALYST_DP_CRITICAL_KPA: float = 3.5
    AUS40_DENSITY_KG_L: float = 1.11  # kg/L for 40% urea
    UREA_MOLAR_MASS: float = 60.06  # g/mol
    NOX_EQUIV_MOLAR_MASS: float = 46.01  # NO2 equivalent g/mol

    def evaluate(self, telem: SCRDeNOxTelemetry) -> SCRDeNOxAssessment:
        warnings: List[str] = []

        # 1. Catalyst Temperature & Ammonium Bisulfate (ABS) Condensation Check
        abs_risk = telem.catalyst_inlet_temp_c < self.MIN_CATALYST_TEMP_MOT_C
        injection_inhibited = abs_risk or telem.scr_bypass_damper_open

        if abs_risk:
            warnings.append(
                f"Catalyst inlet temp {telem.catalyst_inlet_temp_c:.1f}°C below MOT "
                f"({self.MIN_CATALYST_TEMP_MOT_C:.1f}°C). Ammonium Bisulfate (ABS) risk; DEF injection inhibited!"
            )
        if telem.scr_bypass_damper_open:
            warnings.append("SCR system in BYPASS mode. Exhaust gas bypassing catalyst bed.")

        # 2. De-NOx Reduction Efficiency: eta = (NOx_in - NOx_out) / NOx_in * 100
        raw_nox = max(1.0, telem.raw_nox_ppm)
        outlet_nox = max(0.0, telem.exhaust_nox_outlet_ppm)
        efficiency_pct = max(0.0, min(99.9, (raw_nox - outlet_nox) / raw_nox * 100.0))

        tier_iii_ok = efficiency_pct >= self.TARGET_DENOX_EFFICIENCY_MIN_PCT and not telem.scr_bypass_damper_open
        if not tier_iii_ok and not telem.scr_bypass_damper_open:
            warnings.append(
                f"De-NOx efficiency {efficiency_pct:.1f}% below IMO Tier III requirement "
                f"({self.TARGET_DENOX_EFFICIENCY_MIN_PCT:.1f}%)."
            )

        # 3. Stoichiometric Urea Dosing Rate (AUS 40)
        # 1 mol Urea produces 2 mol NH3; 1 mol NH3 reduces 1 mol NOx
        # Mass NOx reduced per hour = exhaust_flow * (delta_NOx * 1e-6) * (M_NOx / M_air=28.97)
        delta_nox_ppm = max(0.0, raw_nox - outlet_nox)
        nox_reduced_kg_h = telem.exhaust_gas_flow_kg_h * (delta_nox_ppm * 1e-6) * (self.NOX_EQUIV_MOLAR_MASS / 28.97)
        # Moles of NOx reduced = kg * 1000 / 46.01
        moles_nox_h = nox_reduced_kg_h * 1000.0 / self.NOX_EQUIV_MOLAR_MASS
        # Moles urea required = moles_nox / 2
        urea_pure_kg_h = (moles_nox_h / 2.0) * self.UREA_MOLAR_MASS / 1000.0
        # AUS 40 solution flow:
        concentration_ratio = max(0.1, telem.urea_solution_concentration_pct / 100.0)
        urea_solution_kg_h = urea_pure_kg_h / concentration_ratio
        dosing_l_h = 0.0 if injection_inhibited else (urea_solution_kg_h / self.AUS40_DENSITY_KG_L)

        # 4. Ammonia Slip Monitoring (MEPC Annex VI requirement <= 10.0 ppm)
        slip_ok = telem.ammonia_slip_ppm <= self.AMMONIA_SLIP_LIMIT_PPM
        if not slip_ok:
            warnings.append(
                f"Ammonia slip {telem.ammonia_slip_ppm:.1f} ppm exceeds statutory limit "
                f"({self.AMMONIA_SLIP_LIMIT_PPM:.1f} ppm). Over-dosing or catalyst degradation!"
            )

        # 5. Catalyst Differential Pressure & Sootblowing
        sootblow_demanded = telem.catalyst_dp_kpa >= self.CATALYST_DP_SOOTBLOW_KPA
        critical_dp = telem.catalyst_dp_kpa >= self.CATALYST_DP_CRITICAL_KPA

        if critical_dp:
            warnings.append(
                f"CRITICAL: Catalyst dP {telem.catalyst_dp_kpa:.2f} kPa exceeds critical ceiling "
                f"({self.CATALYST_DP_CRITICAL_KPA:.2f} kPa). High backpressure risks engine stall!"
            )
        elif sootblow_demanded:
            warnings.append(
                f"Catalyst fouling detected: dP {telem.catalyst_dp_kpa:.2f} kPa >= {self.CATALYST_DP_SOOTBLOW_KPA:.2f} kPa. "
                "Triggering compressed air/acoustic sootblowing."
            )

        # 6. Status determination
        if critical_dp or (telem.def_tank_level_pct < 5.0 and not telem.scr_bypass_damper_open):
            status = "CRITICAL_SCR_FAULT"
        elif abs_risk or injection_inhibited:
            status = "INJECTION_INHIBITED_COLD"
        elif not slip_ok:
            status = "AMMONIA_SLIP_EXCESS"
        elif sootblow_demanded:
            status = "CATALYST_FOULING_SOOTBLOW"
        elif tier_iii_ok:
            status = "OPTIMAL_TIER_III_ACTIVE"
        else:
            status = "LOW_EFFICIENCY_ALERT"

        compliance_flags = {
            "tier_iii_compliant": tier_iii_ok,
            "ammonia_slip_compliant": slip_ok,
            "mot_temperature_satisfied": not abs_risk,
            "catalyst_dp_acceptable": not critical_dp,
            "def_tank_sufficient": telem.def_tank_level_pct >= 10.0,
        }

        return SCRDeNOxAssessment(
            denox_efficiency_pct=round(efficiency_pct, 2),
            urea_dosing_rate_l_h=round(dosing_l_h, 2),
            ammonia_slip_compliant=slip_ok,
            tier_iii_compliant=tier_iii_ok,
            catalyst_sootblower_demanded=sootblow_demanded,
            abs_condensation_risk=abs_risk,
            urea_injection_inhibited=injection_inhibited,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
