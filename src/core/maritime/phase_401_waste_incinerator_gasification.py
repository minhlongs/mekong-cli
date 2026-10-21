"""Phase 401: Shipboard Waste High-Temperature Incinerator & Gasification.

Complies with IMO MARPOL Annex V Reg 16 and Resolution MEPC.244(66).
Evaluates two-stage combustion, flue emissions, dioxin destruction, and interlocks.
Strictly < 200 LOC, zero-mock deterministic thermodynamics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class IncineratorStatus(str, Enum):
    """Overall operational state of the shipboard incinerator."""
    NOMINAL_BURNING = "NOMINAL_BURNING"
    PREHEATING_WARMUP = "PREHEATING_WARMUP"
    SAFETY_TRIPPED = "SAFETY_TRIPPED"
    EMISSION_EXCEEDANCE = "EMISSION_EXCEEDANCE"


@dataclass
class IncineratorInput:
    """Combustion process telemetry and sensor inputs."""
    primary_chamber_temp_c: float = 880.0
    secondary_chamber_temp_c: float = 1100.0
    residence_time_s: float = 1.2
    flue_gas_co_mg_mj: float = 120.0
    oxygen_content_pct: float = 8.5
    smoke_density_ringelmann: float = 0.5
    draft_pressure_pa: float = -120.0
    flame_detected: bool = True


@dataclass
class IncineratorResult:
    """Operational validation and emissions conformance."""
    status: IncineratorStatus
    waste_charging_permitted: bool
    dioxin_destruction_verified: bool
    flue_emissions_compliant: bool
    safety_trip_active: bool
    combustion_efficiency_pct: float
    warnings: List[str] = field(default_factory=list)


class IncineratorEngine:
    """Thermodynamic and regulatory engine for marine incinerators."""

    MIN_PRIMARY_TEMP_C = 850.0
    MIN_SECONDARY_TEMP_C = 1000.0
    MAX_SECONDARY_TEMP_C = 1250.0
    MIN_RESIDENCE_TIME_S = 1.0
    MAX_CO_MG_MJ = 200.0
    MIN_O2_PCT = 6.0
    MAX_O2_PCT = 12.0
    MAX_RINGELMANN = 1.0
    MAX_SAFE_DRAFT_PA = -20.0  # Draft must be negative to prevent blowout

    def evaluate(self, inp: IncineratorInput) -> IncineratorResult:
        """Evaluate combustion chamber conditions, emissions, and interlocks."""
        warnings: List[str] = []
        tripped = False

        # Flame failure check
        if not inp.flame_detected:
            tripped = True
            warnings.append("Flame failure detected: burner fuel cut-off active")

        # Draft pressure check (must maintain negative furnace draft)
        if inp.draft_pressure_pa > self.MAX_SAFE_DRAFT_PA:
            tripped = True
            warnings.append(
                f"Furnace draft loss ({inp.draft_pressure_pa} Pa > {self.MAX_SAFE_DRAFT_PA} Pa): risk of flue blowout"
            )

        # Over-temperature trip
        if inp.secondary_chamber_temp_c > self.MAX_SECONDARY_TEMP_C:
            tripped = True
            warnings.append(
                f"Secondary chamber over-temperature ({inp.secondary_chamber_temp_c} C > {self.MAX_SECONDARY_TEMP_C} C)"
            )

        # Waste charging interlock (MARPOL Annex V: Primary >= 850 C)
        charging_permitted = (
            not tripped
            and inp.primary_chamber_temp_c >= self.MIN_PRIMARY_TEMP_C
            and inp.secondary_chamber_temp_c >= self.MIN_SECONDARY_TEMP_C
        )
        if not charging_permitted and not tripped:
            warnings.append(
                f"Charging locked out: Chamber temps (P:{inp.primary_chamber_temp_c}C, S:{inp.secondary_chamber_temp_c}C) below 850C/1000C"
            )

        # Dioxin/Furan destruction compliance (1000 C + >= 1.0s residence time)
        dioxin_destruction = (
            inp.secondary_chamber_temp_c >= self.MIN_SECONDARY_TEMP_C
            and inp.residence_time_s >= self.MIN_RESIDENCE_TIME_S
        )
        if not dioxin_destruction:
            warnings.append(
                f"Dioxin destruction incomplete: residence {inp.residence_time_s}s or temp {inp.secondary_chamber_temp_c}C inadequate"
            )

        # Flue emissions compliance
        emissions_ok = (
            inp.flue_gas_co_mg_mj <= self.MAX_CO_MG_MJ
            and self.MIN_O2_PCT <= inp.oxygen_content_pct <= self.MAX_O2_PCT
            and inp.smoke_density_ringelmann <= self.MAX_RINGELMANN
        )
        if inp.flue_gas_co_mg_mj > self.MAX_CO_MG_MJ:
            warnings.append(f"CO emissions ({inp.flue_gas_co_mg_mj} mg/MJ) exceed 200 mg/MJ limit")
        if not (self.MIN_O2_PCT <= inp.oxygen_content_pct <= self.MAX_O2_PCT):
            warnings.append(f"Excess O2 ({inp.oxygen_content_pct}%) outside standard 6.0-12.0% range")
        if inp.smoke_density_ringelmann > self.MAX_RINGELMANN:
            warnings.append(f"Smoke density Ringelmann {inp.smoke_density_ringelmann} > 1.0")

        # Combustion efficiency estimation: CE = (CO2 / (CO2 + CO)) * 100
        # Approximated from CO mg/MJ and excess O2
        loss_factor = (inp.flue_gas_co_mg_mj / 2000.0) + (abs(inp.oxygen_content_pct - 9.0) * 0.15)
        combustion_eff = round(max(85.0, min(99.9, 100.0 - loss_factor)), 2)

        # Determine overall status
        if tripped:
            status = IncineratorStatus.SAFETY_TRIPPED
        elif not emissions_ok:
            status = IncineratorStatus.EMISSION_EXCEEDANCE
        elif not charging_permitted:
            status = IncineratorStatus.PREHEATING_WARMUP
        else:
            status = IncineratorStatus.NOMINAL_BURNING

        return IncineratorResult(
            status=status,
            waste_charging_permitted=charging_permitted,
            dioxin_destruction_verified=dioxin_destruction,
            flue_emissions_compliant=emissions_ok,
            safety_trip_active=tripped,
            combustion_efficiency_pct=combustion_eff,
            warnings=warnings,
        )
