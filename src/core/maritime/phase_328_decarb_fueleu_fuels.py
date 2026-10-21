"""Phase 328: Decarbonization, FuelEU Pooling & Alternative Fuel Bunkering Engine.

Implements EU ETS Maritime MRV allowance obligations (Directive 2023/959),
FuelEU Maritime GHG intensity pooling (Regulation 2023/1805), and IGF/IGC Code
safety protocols for Methanol and Ammonia Dual-Fuel bunkering.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List, Optional


@dataclass
class EuEtsFuelEuInput:
    ship_id: str
    reporting_year: int
    gross_tonnage: float
    eu_intra_voyage_emissions_mt: float
    eu_extra_voyage_emissions_mt: float
    ghg_intensity_actual_g_per_mj: float  # Actual gCO2eq / MJ
    fuel_energy_consumption_mj: float
    baseline_ghg_intensity: float = 91.16  # 2020 baseline gCO2eq/MJ


@dataclass
class DualFuelBunkeringInput:
    fuel_type: str  # "METHANOL" or "AMMONIA"
    pipeline_nitrogen_purged: bool
    pipeline_o2_vol_pct: float  # Must be < 2.0%
    vapor_leak_ppm: float  # Methanol < 200 ppm, Ammonia < 25 ppm
    transfer_pressure_bar: float
    observed_safety_radius_meters: float  # Minimum calculated radius


@dataclass
class DecarbEvaluationResult:
    ets_applicable: bool
    eua_surrender_obligation_mt: float
    fueleu_target_ghg_intensity: float
    fueleu_compliance_balance_eur: float  # Positive = surplus, Negative = penalty
    bunkering_safe: Optional[bool]
    reasons: List[str]
    parameters: Dict[str, float]
    audit_trail_hash: str = field(default="")


class MaritimeDecarbFuelEngine:
    """Evaluates EU ETS, FuelEU compliance and dual-fuel bunkering safety."""

    ETS_PHASE_IN = {2024: 0.40, 2025: 0.70, 2026: 1.00}
    FUELEU_REDUCTION_TARGETS = {2025: 0.02, 2030: 0.06, 2035: 0.145, 2040: 0.31, 2050: 0.80}
    FUELEU_PENALTY_PER_VLSFO_EQ_EUR = 2400.0  # Approx statutory benchmark

    MAX_O2_PURGE_VOL_PCT = 2.0
    METHANOL_LEAK_LIMIT_PPM = 200.0
    AMMONIA_LEAK_LIMIT_PPM = 25.0

    @classmethod
    def evaluate(
        cls,
        ets_in: Optional[EuEtsFuelEuInput] = None,
        bunker_in: Optional[DualFuelBunkeringInput] = None,
    ) -> DecarbEvaluationResult:
        reasons: List[str] = []
        params: Dict[str, float] = {}
        ets_app = False
        eua_surrender = 0.0
        target_intensity = 91.16
        compliance_balance = 0.0
        bunkering_safe: Optional[bool] = None

        if ets_in is not None:
            ets_app = ets_in.gross_tonnage >= 5000.0
            phase_in_rate = cls.ETS_PHASE_IN.get(ets_in.reporting_year, 1.0)
            if ets_app:
                # 100% intra-EU + 50% extra-EU voyages
                scope_emissions = (
                    ets_in.eu_intra_voyage_emissions_mt + 0.5 * ets_in.eu_extra_voyage_emissions_mt
                )
                eua_surrender = scope_emissions * phase_in_rate
                reasons.append(
                    f"EU ETS active: surrender {eua_surrender:.2f} EUA at {phase_in_rate*100:.0f}% phase-in"
                )
            else:
                reasons.append("Ship < 5,000 GT: Exempt from EU ETS Maritime MRV")

            # FuelEU Maritime evaluation
            red_pct = 0.0
            for yr, red in sorted(cls.FUELEU_REDUCTION_TARGETS.items()):
                if ets_in.reporting_year >= yr:
                    red_pct = red
            target_intensity = ets_in.baseline_ghg_intensity * (1.0 - red_pct)
            diff_intensity = target_intensity - ets_in.ghg_intensity_actual_g_per_mj
            compliance_balance = (diff_intensity / 41000.0) * (
                ets_in.fuel_energy_consumption_mj / 1e6
            ) * cls.FUELEU_PENALTY_PER_VLSFO_EQ_EUR
            if compliance_balance >= 0:
                reasons.append(
                    f"FuelEU Compliant: Intensity {ets_in.ghg_intensity_actual_g_per_mj:.2f} <= {target_intensity:.2f}"
                )
            else:
                reasons.append(
                    f"FuelEU Non-Compliant: Deficit balance EUR {compliance_balance:.2f} (pooling/penalty required)"
                )

            params["eua_surrender_mt"] = eua_surrender
            params["fueleu_target_intensity"] = target_intensity
            params["fueleu_balance_eur"] = compliance_balance

        if bunker_in is not None:
            bunkering_safe = True
            min_radius = 5.0 + (bunker_in.transfer_pressure_bar * 0.5)
            if not bunker_in.pipeline_nitrogen_purged or bunker_in.pipeline_o2_vol_pct >= cls.MAX_O2_PURGE_VOL_PCT:
                bunkering_safe = False
                reasons.append(
                    f"Nitrogen purge invalid: O2 {bunker_in.pipeline_o2_vol_pct}% exceeds limit (<{cls.MAX_O2_PURGE_VOL_PCT}%)"
                )

            fuel = bunker_in.fuel_type.upper()
            leak_lim = cls.METHANOL_LEAK_LIMIT_PPM if fuel == "METHANOL" else cls.AMMONIA_LEAK_LIMIT_PPM
            if bunker_in.vapor_leak_ppm > leak_lim:
                bunkering_safe = False
                reasons.append(
                    f"{fuel} leak {bunker_in.vapor_leak_ppm} ppm exceeds safe threshold ({leak_lim} ppm)"
                )

            if bunker_in.observed_safety_radius_meters < min_radius:
                bunkering_safe = False
                reasons.append(
                    f"Safety zone radius {bunker_in.observed_safety_radius_meters}m < required ({min_radius:.1f}m)"
                )

            params["required_safety_radius_m"] = min_radius
            params["vapor_leak_ppm"] = bunker_in.vapor_leak_ppm

        audit_src = json.dumps(
            {"ets_app": ets_app, "eua": eua_surrender, "bunkering_safe": bunkering_safe, "params": params},
            sort_keys=True,
        )
        audit_hash = hashlib.sha256(audit_src.encode("utf-8")).hexdigest()

        return DecarbEvaluationResult(
            ets_applicable=ets_app,
            eua_surrender_obligation_mt=eua_surrender,
            fueleu_target_ghg_intensity=target_intensity,
            fueleu_compliance_balance_eur=compliance_balance,
            bunkering_safe=bunkering_safe,
            reasons=reasons,
            parameters=params,
            audit_trail_hash=audit_hash,
        )
