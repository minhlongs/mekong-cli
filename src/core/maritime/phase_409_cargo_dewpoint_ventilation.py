"""Phase 409: Cargo Hold Dew Point & Hold Ventilation Humidity Control.

Complies with IMSBC Code and IMO MSC.268(85) (Safe carriage of solid bulk cargoes).
Computes saturation vapor pressure using the Magnus-Tetens psychrometric formulation,
evaluates cargo sweat vs ship sweat risk, and governs mechanical hold ventilation.
Strictly < 180 LOC, zero mocks, deterministic psychrometric calculations.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class HoldVentilationStatus(str, Enum):
    """Governing operational decision for bulk cargo hold ventilation."""
    VENTILATION_RECOMMENDED = "VENTILATION_RECOMMENDED"
    VENTILATION_PROHIBITED = "VENTILATION_PROHIBITED"
    MAINTAIN_SEALED = "MAINTAIN_SEALED"
    CRITICAL_SHIP_SWEAT_RISK = "CRITICAL_SHIP_SWEAT_RISK"


@dataclass
class HoldPsychrometricInput:
    """Atmospheric and thermal conditions inside and outside the cargo hold."""
    hold_temp_c: float = 22.0  # Cargo hold dry bulb air temp (°C)
    hold_relative_humidity_pct: float = 78.0  # Cargo hold relative humidity (%)
    outside_temp_c: float = 14.0  # Ambient outside dry bulb air temp (°C)
    outside_relative_humidity_pct: float = 65.0  # Ambient outside relative humidity (%)
    cargo_surface_temp_c: float = 20.0  # Bulk cargo surface temperature (°C)
    deckhead_hull_temp_c: float = 12.0  # Steel deckhead / outer shell temp (°C)


@dataclass
class HoldPsychrometricResult:
    """Psychrometric dew points and cargo preservation recommendation."""
    status: HoldVentilationStatus
    hold_dew_point_c: float
    outside_dew_point_c: float
    cargo_sweat_risk: bool
    ship_sweat_risk: bool
    ventilation_action: str
    warnings: List[str] = field(default_factory=list)


class HoldVentilationEngine:
    """Physical psychrometric calculator and IMSBC ventilation rules engine."""

    @staticmethod
    def calculate_dew_point(temp_c: float, rh_pct: float) -> float:
        """Calculate dew point (°C) using the Magnus-Tetens approximation."""
        rh_clamped = max(1.0, min(100.0, rh_pct))
        # Saturation vapor pressure e_s (hPa)
        a = 17.67
        b = 243.5
        alpha = (a * temp_c) / (b + temp_c) + math.log(rh_clamped / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        return round(dew_point, 2)

    def evaluate(self, telemetry: HoldPsychrometricInput) -> HoldPsychrometricResult:
        warnings: List[str] = []

        hold_dp = self.calculate_dew_point(telemetry.hold_temp_c, telemetry.hold_relative_humidity_pct)
        outside_dp = self.calculate_dew_point(telemetry.outside_temp_c, telemetry.outside_relative_humidity_pct)

        # Cargo sweat: Outside air dew point > cargo temperature => moisture condenses on cargo
        cargo_sweat_risk = outside_dp > telemetry.cargo_surface_temp_c

        # Ship sweat: Hold air dew point > cold deckhead/hull temperature => condensation drips from deckhead
        ship_sweat_risk = hold_dp > telemetry.deckhead_hull_temp_c

        if cargo_sweat_risk:
            warnings.append(
                f"Cargo Sweat Alert: Outside dew point ({outside_dp}°C) exceeds cargo temp ({telemetry.cargo_surface_temp_c}°C). "
                "DO NOT VENTILATE with ambient air; introducing outside air will soak cargo."
            )

        if ship_sweat_risk:
            warnings.append(
                f"Ship Sweat Alert: Hold dew point ({hold_dp}°C) exceeds steel deckhead temp ({telemetry.deckhead_hull_temp_c}°C). "
                "Condensation dripping from deckhead onto cargo imminent."
            )

        if cargo_sweat_risk:
            status = HoldVentilationStatus.VENTILATION_PROHIBITED
            ventilation_action = "STOP VENTILATION: Maintain hermetic hold seal to protect cargo"
        elif ship_sweat_risk:
            if outside_dp < telemetry.deckhead_hull_temp_c:
                status = HoldVentilationStatus.VENTILATION_RECOMMENDED
                ventilation_action = "START FORCED VENTILATION: Purge moist hold air with drier ambient air"
            else:
                status = HoldVentilationStatus.CRITICAL_SHIP_SWEAT_RISK
                ventilation_action = "RECIRCULATE / DEHUMIDIFY: Outside air too humid to purge deckhead condensation safely"
        else:
            status = HoldVentilationStatus.MAINTAIN_SEALED
            ventilation_action = "NORMAL: Holds stable, natural or closed circulation acceptable"

        return HoldPsychrometricResult(
            status=status,
            hold_dew_point_c=hold_dp,
            outside_dew_point_c=outside_dp,
            cargo_sweat_risk=cargo_sweat_risk,
            ship_sweat_risk=ship_sweat_risk,
            ventilation_action=ventilation_action,
            warnings=warnings,
        )
