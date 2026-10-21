"""Phase 417: Cargo Hold Dew Point & Hold Dehumidification Desiccant Wheel.

Implements IMSBC Code (Bulk Cargo Sweat Prevention) and DNV Rules for Cargo Care:
Magnus-Tetens psychrometric dew point calculation, ship vs cargo sweat risk evaluation,
ventilation decision logic, and rotary silica-gel desiccant wheel moisture removal.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass(frozen=True)
class CargoHoldDewPointTelemetry:
    """Telemetry readings for cargo hold psychrometrics and dehumidification."""
    hold_temp_c: float = 24.0
    hold_relative_humidity_pct: float = 60.0
    ambient_air_temp_c: float = 20.0
    ambient_relative_humidity_pct: float = 55.0
    seawater_temp_c: float = 22.0
    cargo_surface_temp_c: float = 22.0
    air_flow_rate_m3_h: float = 5000.0
    desiccant_wheel_rpm: float = 0.25
    regen_heater_temp_c: float = 120.0
    outside_rain_or_fog: bool = False


@dataclass(frozen=True)
class CargoHoldDewPointAssessment:
    """Cargo hold psychrometric state, sweat risks, and dehumidification performance."""
    hold_dew_point_c: float
    ambient_dew_point_c: float
    ship_sweat_margin_c: float
    cargo_sweat_margin_c: float
    moisture_removal_rate_kg_h: float
    ventilation_rule: str
    desiccant_wheel_active: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CargoHoldDewPointEngine:
    """Calculates dew points via Magnus-Tetens, evaluates sweat risk, and governs desiccant."""

    MAGNUS_B: float = 17.62
    MAGNUS_C: float = 243.12
    AIR_DENSITY_KG_M3: float = 1.204

    def calculate_dew_point(self, temp_c: float, rh_pct: float) -> float:
        """Calculate dew point using the Magnus-Tetens approximation."""
        rh_clamped = min(99.9, max(1.0, rh_pct))
        gamma = (self.MAGNUS_B * temp_c) / (self.MAGNUS_C + temp_c) + math.log(rh_clamped / 100.0)
        return (self.MAGNUS_C * gamma) / (self.MAGNUS_B - gamma)

    def calculate_humidity_ratio(self, temp_c: float, rh_pct: float) -> float:
        """Approximate humidity ratio (kg water / kg dry air)."""
        rh_frac = min(0.999, max(0.01, rh_pct / 100.0))
        # Saturation vapor pressure in hPa
        p_sat = 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))
        p_v = rh_frac * p_sat
        p_atm = 1013.25
        return 0.622 * p_v / max(10.0, p_atm - p_v)

    def evaluate(self, telemetry: CargoHoldDewPointTelemetry) -> CargoHoldDewPointAssessment:
        warnings: List[str] = []

        hold_dp = self.calculate_dew_point(telemetry.hold_temp_c, telemetry.hold_relative_humidity_pct)
        amb_dp = self.calculate_dew_point(telemetry.ambient_air_temp_c, telemetry.ambient_relative_humidity_pct)

        # Ship sweat occurs when Hold Dew Point > Ship Hull/Seawater Temperature
        ship_sweat_margin = telemetry.seawater_temp_c - hold_dp
        # Cargo sweat occurs when Ambient Dew Point > Cargo Temperature (if ventilated)
        cargo_sweat_margin = telemetry.cargo_surface_temp_c - amb_dp

        # Ventilation rule decision:
        # Rule 1: If outside dew point < hold dew point AND no rain -> Natural/Forced ventilation permitted
        # Rule 2: If outside dew point >= cargo temperature OR rain/fog -> NEVER ventilate with outside air (causes cargo sweat)
        need_desiccant = False
        if telemetry.outside_rain_or_fog:
            vent_rule = "SEAL_HOLD_RECIRCULATE_DESICCANT"
            need_desiccant = True
            warnings.append("Outside precipitation or heavy fog detected: Hold must remain tightly battened.")
        elif amb_dp >= telemetry.cargo_surface_temp_c:
            vent_rule = "SEAL_HOLD_RECIRCULATE_DESICCANT"
            need_desiccant = True
            warnings.append(
                f"Cargo sweat hazard: Ambient dew point ({amb_dp:.1f}°C) >= Cargo temperature "
                f"({telemetry.cargo_surface_temp_c:.1f}°C). Outside ventilation forbidden!"
            )
        elif amb_dp < hold_dp:
            vent_rule = "THROUGH_VENTILATION_SAFE"
            need_desiccant = False
        else:
            vent_rule = "RECIRCULATION_HOLD_CARE"
            need_desiccant = ship_sweat_margin < 2.0

        if ship_sweat_margin < 0.0:
            warnings.append(
                f"CRITICAL SHIP SWEAT: Hold dew point ({hold_dp:.1f}°C) exceeds hull seawater "
                f"temp ({telemetry.seawater_temp_c:.1f}°C). Moisture condensing on shell plating!"
            )
            need_desiccant = True
        elif ship_sweat_margin < 2.5:
            warnings.append(f"Ship sweat warning: Low margin ({ship_sweat_margin:.1f}°C) to condensation threshold.")

        # Desiccant wheel dehumidification capacity (kg/h)
        w_in = self.calculate_humidity_ratio(telemetry.hold_temp_c, telemetry.hold_relative_humidity_pct)
        # Desiccant wheel typically removes 40-60% moisture on single pass if regen temp >= 100°C
        wheel_efficiency = 0.52 if telemetry.regen_heater_temp_c >= 105.0 else 0.25
        delta_w = w_in * wheel_efficiency if need_desiccant else 0.0
        air_mass_flow_kg_h = telemetry.air_flow_rate_m3_h * self.AIR_DENSITY_KG_M3
        moisture_removal_kg_h = air_mass_flow_kg_h * delta_w

        status = "OPTIMAL"
        if ship_sweat_margin < 0.0 or (telemetry.outside_rain_or_fog and ship_sweat_margin < 1.0):
            status = "CRITICAL"
        elif warnings or need_desiccant:
            status = "WARNING"

        compliance_flags = {
            "imsbc_cargo_sweat_prevented": cargo_sweat_margin > 0.0 or vent_rule != "THROUGH_VENTILATION_SAFE",
            "imsbc_ship_sweat_prevented": ship_sweat_margin >= 0.0,
            "desiccant_regeneration_adequate": telemetry.regen_heater_temp_c >= 100.0,
            "air_relative_humidity_safe": telemetry.hold_relative_humidity_pct <= 70.0,
        }

        return CargoHoldDewPointAssessment(
            hold_dew_point_c=round(hold_dp, 2),
            ambient_dew_point_c=round(amb_dp, 2),
            ship_sweat_margin_c=round(ship_sweat_margin, 2),
            cargo_sweat_margin_c=round(cargo_sweat_margin, 2),
            moisture_removal_rate_kg_h=round(moisture_removal_kg_h, 2),
            ventilation_rule=vent_rule,
            desiccant_wheel_active=need_desiccant,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
