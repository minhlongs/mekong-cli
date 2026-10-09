"""Phase 407: Marine Exhaust Gas Boiler (EGB) Economizer & Soot Blow Automation.

Complies with SOLAS II-2 Reg 4 and DNV Pt.4 Ch.6 (Boilers and Pressure Vessels).
Monitors exhaust gas differential pressure across tube banks, gas exit temperature,
circulation water flow rate, and soot accumulation fire hazard index.
Strictly < 180 LOC, zero mocks, deterministic thermodynamic calculations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class EgbEconomizerStatus(str, Enum):
    """Operational status for marine exhaust gas economizer."""
    NORMAL_HEAT_RECOVERY = "NORMAL_HEAT_RECOVERY"
    SOOT_CLEANING_REQUIRED = "SOOT_CLEANING_REQUIRED"
    SOOT_FIRE_HAZARD_TRIP = "SOOT_FIRE_HAZARD_TRIP"
    LOW_WATER_CIRCULATION = "LOW_WATER_CIRCULATION"
    LOW_ENGINE_LOAD_LOCKOUT = "LOW_ENGINE_LOAD_LOCKOUT"


@dataclass
class EgbEconomizerInput:
    """Operational telemetry for marine waste heat economizer."""
    flue_gas_inlet_temp_c: float = 310.0  # Main engine exhaust gas inlet temp (°C)
    flue_gas_outlet_temp_c: float = 175.0  # Economizer exhaust outlet temp (°C)
    gas_differential_pressure_mmwc: float = 32.0  # Gas drop across tube bundle (target 20-45 mmWC)
    steam_saturation_temp_c: float = 164.0  # Boiler drum saturation temp at operating pressure (°C)
    circulation_water_flow_m3_h: float = 24.0  # Boiler circulating pump flow (minimum 18 m3/h)
    main_engine_load_pct: float = 75.0  # Main engine MCR load % (soot blow prohibited < 50%)
    soot_blower_steam_pressure_bar: float = 8.5  # Soot blow supply steam (target 7.0 - 12.0 bar)


@dataclass
class EgbEconomizerResult:
    """Assessment of economizer thermal efficiency and fire safety."""
    status: EgbEconomizerStatus
    heat_transfer_effectiveness: float
    soot_blow_recommended: bool
    soot_blow_permitted: bool
    soot_fire_risk_detected: bool
    circulation_flow_safe: bool
    warnings: List[str] = field(default_factory=list)


class EgbEconomizerEngine:
    """Thermodynamics and safety evaluation for marine exhaust economizers."""

    WARN_GAS_DP_MMWC = 45.0  # Soot buildup alarm
    CRIT_GAS_DP_MMWC = 70.0  # Severe fouling risk
    MAX_OUTLET_TEMP_C = 220.0  # Exit gas high temp alert
    MIN_CIRCULATION_FLOW_M3_H = 18.0  # Minimum circulating water flow to avoid dry boiling
    MIN_ENGINE_LOAD_SOOT_BLOW_PCT = 50.0  # Prevent sparks at low load

    def evaluate(self, telemetry: EgbEconomizerInput) -> EgbEconomizerResult:
        warnings: List[str] = []

        # Effectiveness = (Tin - Tout) / (Tin - Tsat)
        temp_delta_max = max(1.0, telemetry.flue_gas_inlet_temp_c - telemetry.steam_saturation_temp_c)
        temp_drop = max(0.0, telemetry.flue_gas_inlet_temp_c - telemetry.flue_gas_outlet_temp_c)
        effectiveness = round(min(1.0, temp_drop / temp_delta_max), 3)

        circulation_flow_safe = telemetry.circulation_water_flow_m3_h >= self.MIN_CIRCULATION_FLOW_M3_H
        if not circulation_flow_safe:
            warnings.append(
                f"Circulation water flow {telemetry.circulation_water_flow_m3_h} m3/h below minimum {self.MIN_CIRCULATION_FLOW_M3_H} m3/h. "
                "Risk of tube dry-out and overheating."
            )

        soot_blow_recommended = telemetry.gas_differential_pressure_mmwc >= self.WARN_GAS_DP_MMWC
        if soot_blow_recommended:
            warnings.append(
                f"Exhaust gas differential pressure {telemetry.gas_differential_pressure_mmwc} mmWC >= {self.WARN_GAS_DP_MMWC} mmWC. "
                "Soot fouling detected: Initiate soot blowing cycle."
            )

        soot_fire_risk_detected = (
            telemetry.flue_gas_outlet_temp_c > self.MAX_OUTLET_TEMP_C
            or telemetry.gas_differential_pressure_mmwc >= self.CRIT_GAS_DP_MMWC
            or (telemetry.flue_gas_outlet_temp_c > 190.0 and not circulation_flow_safe)
        )
        if soot_fire_risk_detected:
            warnings.append(
                f"CRITICAL: Economizer soot fire hazard. Outlet temp={telemetry.flue_gas_outlet_temp_c}°C, "
                f"gas DP={telemetry.gas_differential_pressure_mmwc} mmWC. Stop main engine and boundary cool."
            )

        soot_blow_permitted = (
            telemetry.main_engine_load_pct >= self.MIN_ENGINE_LOAD_SOOT_BLOW_PCT
            and circulation_flow_safe
            and not soot_fire_risk_detected
            and telemetry.soot_blower_steam_pressure_bar >= 6.5
        )
        if telemetry.main_engine_load_pct < self.MIN_ENGINE_LOAD_SOOT_BLOW_PCT:
            warnings.append(
                f"Engine load {telemetry.main_engine_load_pct}% < {self.MIN_ENGINE_LOAD_SOOT_BLOW_PCT}%. "
                "Soot blow interlocked to prevent spark emission from funnel."
            )

        if soot_fire_risk_detected:
            status = EgbEconomizerStatus.SOOT_FIRE_HAZARD_TRIP
        elif not circulation_flow_safe:
            status = EgbEconomizerStatus.LOW_WATER_CIRCULATION
        elif soot_blow_recommended:
            status = EgbEconomizerStatus.SOOT_CLEANING_REQUIRED
        elif telemetry.main_engine_load_pct < self.MIN_ENGINE_LOAD_SOOT_BLOW_PCT:
            status = EgbEconomizerStatus.LOW_ENGINE_LOAD_LOCKOUT
        else:
            status = EgbEconomizerStatus.NORMAL_HEAT_RECOVERY

        return EgbEconomizerResult(
            status=status,
            heat_transfer_effectiveness=effectiveness,
            soot_blow_recommended=soot_blow_recommended,
            soot_blow_permitted=soot_blow_permitted,
            soot_fire_risk_detected=soot_fire_risk_detected,
            circulation_flow_safe=circulation_flow_safe,
            warnings=warnings,
        )
