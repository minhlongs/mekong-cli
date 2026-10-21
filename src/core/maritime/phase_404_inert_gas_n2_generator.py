"""Phase 404: Marine Inert Gas System (IGS) & Nitrogen (N2) Membrane Generator.

Implements SOLAS II-2 Reg 4.5.5, IMO FSS Code Ch.15, polymer hollow-fiber membrane
selectivity/permeability, O2 <= 5% alarm, O2 >= 8% safety trip venting to atmosphere,
and P/V breaker hydrostatic liquid seal displacement.
Strictly < 200 LOC, zero mocks, pure analytical physics.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Dict, List


class IgsOperatingState(str, Enum):
    NORMAL_SUPPLY = "NORMAL_SUPPLY"
    O2_HIGH_ALARM = "O2_HIGH_ALARM"
    O2_SAFETY_TRIP_VENTING = "O2_SAFETY_TRIP_VENTING"
    PRESSURE_SURGE_RELIEF = "PRESSURE_SURGE_RELIEF"
    VACUUM_BREAKER_RELIEF = "VACUUM_BREAKER_RELIEF"


@dataclass(frozen=True)
class InertGasN2Telemetry:
    """Telemetry readings for marine N2 hollow-fiber membrane generator & deck seal."""
    feed_air_pressure_bar: float = 12.0
    feed_air_temperature_c: float = 45.0
    measured_oxygen_content_pct: float = 3.8
    inert_gas_flow_rate_nm3_h: float = 1250.0
    deck_main_pressure_mmwg: float = 850.0  # mm Water Gauge (safe range +200 to +1400 mmWG)
    pv_breaker_liquid_level_mm: float = 450.0
    pv_breaker_liquid_density_kg_m3: float = 1000.0  # Fresh water with ethylene glycol
    atmospheric_vent_valve_open: bool = False
    deck_isolating_valve_open: bool = True
    membrane_differential_pressure_bar: float = 10.5


@dataclass(frozen=True)
class InertGasN2Assessment:
    """Assessment of N2 generator performance, flammability limits, and P/V seal."""
    oxygen_content_pct: float
    permeation_flux_ratio: float
    deck_pressure_mmwg: float
    pv_breaker_displacement_mm: float
    pv_breaker_tripped: bool
    atmospheric_venting_active: bool
    state: IgsOperatingState
    compliance_flags: Dict[str, bool]
    warnings: List[str] = field(default_factory=list)


class InertGasN2GeneratorEngine:
    """Analytical physics of polymer hollow-fiber gas separation & SOLAS safety trips."""

    SOLAS_MAX_O2_CARGO_TANKS_PCT: float = 8.0  # Never admit gas > 8% O2 into cargo tanks
    SOLAS_ALARM_O2_PCT: float = 5.0            # Alarm threshold
    PV_BREAKER_MAX_PRESSURE_MMWG: float = 1400.0
    PV_BREAKER_MIN_VACUUM_MMWG: float = -350.0

    def calculate_membrane_permeation(self, pressure_bar: float, temp_c: float) -> float:
        """Arrhenius-style permeance estimate: Flux increases with temperature and delta P."""
        temp_k = temp_c + 273.15
        ref_temp_k = 293.15  # 20 C
        # Arrhenius temperature activation factor
        temp_factor = math.exp(-1200.0 * (1.0 / temp_k - 1.0 / ref_temp_k))
        pressure_factor = max(0.1, pressure_bar / 10.0)
        return temp_factor * pressure_factor

    def evaluate(self, telemetry: InertGasN2Telemetry) -> InertGasN2Assessment:
        warnings: List[str] = []

        o2_pct = telemetry.measured_oxygen_content_pct
        flux_ratio = round(
            self.calculate_membrane_permeation(
                telemetry.feed_air_pressure_bar,
                telemetry.feed_air_temperature_c,
            ),
            3,
        )

        # Hydrostatic displacement in P/V breaker seal: h = delta_P (mmWG) * (1000 / rho)
        p_ratio = 1000.0 / max(500.0, telemetry.pv_breaker_liquid_density_kg_m3)
        pv_displacement = round(telemetry.deck_main_pressure_mmwg * p_ratio, 1)

        pv_tripped = (
            telemetry.deck_main_pressure_mmwg >= self.PV_BREAKER_MAX_PRESSURE_MMWG
            or telemetry.deck_main_pressure_mmwg <= self.PV_BREAKER_MIN_VACUUM_MMWG
        )

        # Automatic safety vent tripping: if O2 >= 8%, gas MUST be dumped to atmosphere
        must_trip_vent = o2_pct >= self.SOLAS_MAX_O2_CARGO_TANKS_PCT
        venting_active = must_trip_vent or telemetry.atmospheric_vent_valve_open

        if must_trip_vent:
            warnings.append(
                f"SOLAS SAFETY TRIP: Oxygen content {o2_pct:.1f}% >= 8.0%! Deck isolating valve shut, venting to atmosphere."
            )
        elif o2_pct > self.SOLAS_ALARM_O2_PCT:
            warnings.append(
                f"IGS HIGH O2 ALARM: Oxygen content {o2_pct:.1f}% exceeds 5.0% operating limit."
            )

        if pv_tripped:
            if telemetry.deck_main_pressure_mmwg >= self.PV_BREAKER_MAX_PRESSURE_MMWG:
                warnings.append(
                    f"P/V BREAKER BLOWING: Deck pressure {telemetry.deck_main_pressure_mmwg:.0f} mmWG exceeds seal threshold {self.PV_BREAKER_MAX_PRESSURE_MMWG} mmWG!"
                )
            else:
                warnings.append(
                    f"P/V BREAKER DRAWING: Deck vacuum {telemetry.deck_main_pressure_mmwg:.0f} mmWG below seal vacuum {self.PV_BREAKER_MIN_VACUUM_MMWG} mmWG!"
                )

        # Operating state assignment
        if pv_tripped and telemetry.deck_main_pressure_mmwg < 0:
            state = IgsOperatingState.VACUUM_BREAKER_RELIEF
        elif pv_tripped and telemetry.deck_main_pressure_mmwg > 0:
            state = IgsOperatingState.PRESSURE_SURGE_RELIEF
        elif must_trip_vent:
            state = IgsOperatingState.O2_SAFETY_TRIP_VENTING
        elif o2_pct > self.SOLAS_ALARM_O2_PCT:
            state = IgsOperatingState.O2_HIGH_ALARM
        else:
            state = IgsOperatingState.NORMAL_SUPPLY

        compliance_flags = {
            "o2_below_8_percent_safety": o2_pct < self.SOLAS_MAX_O2_CARGO_TANKS_PCT,
            "o2_below_5_percent_normal": o2_pct <= self.SOLAS_ALARM_O2_PCT,
            "pv_breaker_liquid_level_adequate": telemetry.pv_breaker_liquid_level_mm >= 350.0,
            "deck_seal_pressure_positive": telemetry.deck_main_pressure_mmwg > 100.0,
            "vent_isolated_during_normal": not (state == IgsOperatingState.NORMAL_SUPPLY and telemetry.atmospheric_vent_valve_open),
        }

        return InertGasN2Assessment(
            oxygen_content_pct=round(o2_pct, 2),
            permeation_flux_ratio=flux_ratio,
            deck_pressure_mmwg=telemetry.deck_main_pressure_mmwg,
            pv_breaker_displacement_mm=pv_displacement,
            pv_breaker_tripped=pv_tripped,
            atmospheric_venting_active=venting_active,
            state=state,
            compliance_flags=compliance_flags,
            warnings=warnings,
        )
