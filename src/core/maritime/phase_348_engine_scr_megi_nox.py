"""Phase 348: Marine Engine SCR & Dual-Fuel ME-GI NOx Tier III Engine.

Implements IMO MARPOL Annex VI Regulation 13 & MEPC.198(62) standards:
- Tier III NOx emission limits in NOx-ECA based on rated engine rpm.
- Selective Catalytic Reduction (SCR) temperature window (>= 300°C) verification.
- Urea AUS 40 dosage rate estimation for NOx catalytic abatement.
- Dual-fuel engine methane slip monitoring (<= 2.5 g/kWh).
Strictly under 200 LOC.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class EngineScrNoxInput:
    engine_id: str
    rated_speed_rpm: float
    engine_power_kw: float
    raw_nox_g_kwh: float
    exhaust_temp_celsius: float
    is_neca_zone: bool = True
    is_dual_fuel_gas_mode: bool = False
    methane_slip_g_kwh: float = 1.2
    scr_efficiency: float = 0.85


@dataclass
class EngineScrNoxResult:
    engine_id: str
    tier_limit_g_kwh: float
    achieved_nox_g_kwh: float
    is_compliant: bool
    scr_active: bool
    catalyst_temperature_ok: bool
    urea_consumption_kg_h: float
    methane_slip_ok: bool
    engine_status: str  # COMPLIANT, NON_COMPLIANT, DERATED
    advisories: List[str] = field(default_factory=list)


class EngineScrNoxEngine:
    """Evaluates marine diesel engine NOx compliance and SCR operation."""

    SCR_MIN_TEMP_C = 300.0
    METHANE_SLIP_MAX_G_KWH = 2.5
    UREA_AUS40_MOLAR_FACTOR = 0.652  # kg urea AUS 40 per kg NOx removed

    @classmethod
    def calculate_tier_limit(cls, rpm: float, is_neca: bool) -> float:
        """Calculate MARPOL Annex VI NOx limit in g/kWh."""
        if is_neca:
            # Tier III limits
            if rpm < 130.0:
                return 3.4
            elif rpm < 2000.0:
                return round(9.0 * math.pow(rpm, -0.2), 2)
            else:
                return 2.0
        else:
            # Tier II limits
            if rpm < 130.0:
                return 14.4
            elif rpm < 2000.0:
                return round(44.0 * math.pow(rpm, -0.23), 2)
            else:
                return 7.7

    @classmethod
    def evaluate(cls, inp: EngineScrNoxInput) -> EngineScrNoxResult:
        advisories: List[str] = []
        limit = cls.calculate_tier_limit(inp.rated_speed_rpm, inp.is_neca_zone)
        temp_ok = inp.exhaust_temp_celsius >= cls.SCR_MIN_TEMP_C

        if not temp_ok:
            advisories.append(
                f"CATALYST FOULING RISK: Exhaust temp {inp.exhaust_temp_celsius}°C < {cls.SCR_MIN_TEMP_C}°C. "
                "Risk of ammonium bisulfate (NH4HSO4) crystallization. SCR dosing blocked."
            )

        # Check raw emissions vs limit
        if inp.raw_nox_g_kwh <= limit:
            # Already compliant without SCR
            scr_active = False
            achieved = inp.raw_nox_g_kwh
            urea_kg_h = 0.0
        else:
            # Requires SCR reduction
            scr_active = temp_ok
            if scr_active:
                achieved = round(inp.raw_nox_g_kwh * (1.0 - inp.scr_efficiency), 2)
                delta_nox_kg_h = (inp.raw_nox_g_kwh - achieved) * inp.engine_power_kw / 1000.0
                urea_kg_h = round(delta_nox_kg_h * cls.UREA_AUS40_MOLAR_FACTOR, 2)
            else:
                achieved = inp.raw_nox_g_kwh
                urea_kg_h = 0.0

        is_compliant = achieved <= limit

        # Methane slip check for dual fuel engines
        methane_ok = True
        if inp.is_dual_fuel_gas_mode:
            if inp.methane_slip_g_kwh > cls.METHANE_SLIP_MAX_G_KWH:
                methane_ok = False
                advisories.append(
                    f"METHANE SLIP WARNING: Measured {inp.methane_slip_g_kwh} g/kWh > {cls.METHANE_SLIP_MAX_G_KWH} g/kWh. "
                    "Unburned fuel greenhouse penalty. Adjust pilot injection timing."
                )

        if not is_compliant:
            advisories.append(
                f"MARPOL TIER {'III' if inp.is_neca_zone else 'II'} VIOLATION: Achieved NOx {achieved} g/kWh > limit {limit} g/kWh."
            )
            status = "NON_COMPLIANT"
        elif not methane_ok:
            status = "DERATED"
        else:
            status = "COMPLIANT"

        return EngineScrNoxResult(
            engine_id=inp.engine_id,
            tier_limit_g_kwh=limit,
            achieved_nox_g_kwh=achieved,
            is_compliant=is_compliant,
            scr_active=scr_active,
            catalyst_temperature_ok=temp_ok,
            urea_consumption_kg_h=urea_kg_h,
            methane_slip_ok=methane_ok,
            engine_status=status,
            advisories=advisories,
        )
