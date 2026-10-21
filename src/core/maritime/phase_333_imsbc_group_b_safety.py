"""Phase 333: IMSBC Code Group B Chemical Hazards & Hold Gas Monitoring.

Evaluates IMSBC Group B solid bulk cargo chemical hazards: self-heating,
toxic/flammable gas evolution (CO, CH4, H2, PH3), O2 depletion, and ventilation rules.
Kept strictly under 200 lines according to KISS/YAGNI principles.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ImsbcGroupBInput:
    cargo_name: str  # e.g., "COAL", "DRI_A", "SEED_CAKE", "FERROSILICON"
    hold_number: int
    cargo_temp_celsius: float
    previous_temp_celsius: float  # Reading from 24h prior
    o2_pct_vol: float  # Ambient in hold
    co_ppm: float  # Carbon monoxide
    ch4_pct_lel: float  # Methane % LEL
    h2_pct_lel: float = 0.0  # Hydrogen % LEL
    ph3_ppm: float = 0.0  # Phosphine gas ppm


@dataclass
class ImsbcGroupBResult:
    cargo_name: str
    hold_number: int
    temp_rise_rate_per_day: float
    is_self_heating_alert: bool
    is_explosive_gas_hazard: bool
    is_toxic_hazard: bool
    is_oxygen_depleted: bool
    recommended_ventilation: str  # "CONTINUOUS_SURFACE", "SEAL_AND_INERT", "NO_VENTILATION"
    cargo_safe_to_carry: bool
    hazards_detected: List[str]


class ImsbcGroupBEngine:
    # Statutory & Safety Thresholds under IMSBC Code Group B
    MAX_PERMISSIBLE_TEMP_C = 55.0  # Self-heating threshold (e.g. Coal / Seed Cake)
    CRITICAL_TEMP_RISE_RATE = 2.0  # >= 2°C/day signals active self-heating
    MIN_SAFE_O2_PCT = 19.5  # O2 depletion threshold
    MAX_CO_PPM_NORMAL = 50.0  # > 50 ppm CO indicates spontaneous combustion
    MAX_GAS_LEL_PCT = 20.0  # > 20% LEL triggers explosive risk
    MAX_PH3_PPM = 0.3  # Phosphine toxic threshold (0.3 ppm TLV-TWA)

    @classmethod
    def evaluate(cls, inp: ImsbcGroupBInput) -> ImsbcGroupBResult:
        hazards: List[str] = []
        temp_rise = round(inp.cargo_temp_celsius - inp.previous_temp_celsius, 2)

        # 1. Self-heating check
        self_heating = False
        if inp.cargo_temp_celsius >= cls.MAX_PERMISSIBLE_TEMP_C:
            self_heating = True
            hazards.append(
                f"Cargo temperature {inp.cargo_temp_celsius}°C exceeds limit {cls.MAX_PERMISSIBLE_TEMP_C}°C"
            )
        if temp_rise >= cls.CRITICAL_TEMP_RISE_RATE:
            self_heating = True
            hazards.append(
                f"Temperature rise rate {temp_rise}°C/day indicates active thermal runaway (>= {cls.CRITICAL_TEMP_RISE_RATE}°C/day)"
            )
        if inp.co_ppm > cls.MAX_CO_PPM_NORMAL:
            self_heating = True
            hazards.append(
                f"Elevated Carbon Monoxide {inp.co_ppm} ppm indicates deep-seated smouldering (> {cls.MAX_CO_PPM_NORMAL} ppm)"
            )

        # 2. Explosive gas hazard (Methane or Hydrogen)
        explosive_gas = False
        if inp.ch4_pct_lel >= cls.MAX_GAS_LEL_PCT:
            explosive_gas = True
            hazards.append(f"Methane {inp.ch4_pct_lel}% LEL reaches dangerous level (>= {cls.MAX_GAS_LEL_PCT}%)")
        if inp.h2_pct_lel >= cls.MAX_GAS_LEL_PCT:
            explosive_gas = True
            hazards.append(f"Hydrogen {inp.h2_pct_lel}% LEL reaches dangerous level (>= {cls.MAX_GAS_LEL_PCT}%)")

        # 3. Toxic gas hazard
        toxic_gas = False
        if inp.ph3_ppm > cls.MAX_PH3_PPM:
            toxic_gas = True
            hazards.append(f"Phosphine gas {inp.ph3_ppm} ppm exceeds TLV ({cls.MAX_PH3_PPM} ppm)")

        # 4. Oxygen depletion
        o2_depleted = inp.o2_pct_vol < cls.MIN_SAFE_O2_PCT
        if o2_depleted:
            hazards.append(f"Hold atmosphere O2 {inp.o2_pct_vol}% is asphyxiating (< {cls.MIN_SAFE_O2_PCT}%)")

        # Ventilation strategy according to IMSBC Code rules:
        # If active self-heating is detected, do NOT supply fresh oxygen (Seal & Inert).
        # If methane/hydrogen accumulation without fire, surface ventilation is required.
        cargo_upper = inp.cargo_name.upper()
        if self_heating:
            ventilation = "SEAL_AND_INERT"
        elif explosive_gas or "COAL" in cargo_upper:
            ventilation = "CONTINUOUS_SURFACE"
        elif "DRI" in cargo_upper:
            # Direct Reduced Iron reacts with water/air, requires inerting
            ventilation = "SEAL_AND_INERT"
        else:
            ventilation = "NO_VENTILATION"

        safe_to_carry = not (self_heating or explosive_gas or (toxic_gas and inp.ph3_ppm > 1.0))

        return ImsbcGroupBResult(
            cargo_name=inp.cargo_name,
            hold_number=inp.hold_number,
            temp_rise_rate_per_day=temp_rise,
            is_self_heating_alert=self_heating,
            is_explosive_gas_hazard=explosive_gas,
            is_toxic_hazard=toxic_gas,
            is_oxygen_depleted=o2_depleted,
            recommended_ventilation=ventilation,
            cargo_safe_to_carry=safe_to_carry,
            hazards_detected=hazards,
        )
