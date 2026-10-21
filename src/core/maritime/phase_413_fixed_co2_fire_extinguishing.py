"""Phase 413: Marine Fixed High-Pressure CO2 Fire Extinguishing System.

Implements SOLAS II-2 Reg 10 / IMO FSS Code Ch.5 standards for machinery space
total flooding CO2 mass calculation, 85% 2-minute discharge dynamics,
pneumatic pre-discharge sirens, and fuel/ventilation quick-closing trips.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class Co2SystemTelemetry:
    """Telemetry readings for High-Pressure CO2 Fire Extinguishing System."""
    protected_space_gross_volume_m3: float = 4000.0
    machinery_equipment_volume_m3: float = 600.0
    installed_cylinders_count: int = 35
    cylinder_nominal_mass_kg: float = 45.0
    discharge_time_seconds: float = 95.0
    pre_discharge_delay_seconds: float = 25.0
    ventilation_damper_closed: bool = True
    fuel_quick_closing_valves_tripped: bool = True
    cabinet_door_open: bool = True


@dataclass(frozen=True)
class Co2SystemAssessment:
    """Safety and regulatory assessment of Fixed CO2 flooding system."""
    net_free_volume_m3: float
    required_co2_mass_kg: float
    installed_co2_mass_kg: float
    required_cylinder_count: int
    two_minute_discharge_compliant: bool
    interlocks_satisfied: bool
    status: str
    warnings: list[str]
    compliance_flags: Dict[str, bool]


class FixedCo2FireSystemEngine:
    """Calculates required CO2 flooding mass, discharge rates, and interlocks."""

    # SOLAS II-2 / FSS Code: Machinery space free gas volume factor = 0.40 m3/kg (or 0.56 m3 free volume / kg CO2 => ~0.40 kg/m3)
    FREE_VOLUME_CO2_FACTOR: float = 0.40
    GROSS_VOLUME_CO2_FACTOR: float = 0.35
    STD_CYLINDER_MASS_KG: float = 45.0
    MAX_DISCHARGE_TIME_SEC: float = 120.0  # 85% discharged within 2 mins
    MIN_PRE_DISCHARGE_DELAY_SEC: float = 20.0
    MAX_PRE_DISCHARGE_DELAY_SEC: float = 30.0

    def evaluate(self, telemetry: Co2SystemTelemetry) -> Co2SystemAssessment:
        warnings: list[str] = []

        v_net = max(1.0, telemetry.protected_space_gross_volume_m3 - telemetry.machinery_equipment_volume_m3)
        # Required mass is max of 40% of net free volume or 35% of gross volume (using standard gas volume conversion)
        req_mass_from_net = v_net * self.FREE_VOLUME_CO2_FACTOR
        req_mass_from_gross = telemetry.protected_space_gross_volume_m3 * self.GROSS_VOLUME_CO2_FACTOR
        required_mass = round(max(req_mass_from_net, req_mass_from_gross), 1)

        cyl_mass = telemetry.cylinder_nominal_mass_kg if telemetry.cylinder_nominal_mass_kg > 0 else self.STD_CYLINDER_MASS_KG
        required_cylinders = int(-(-required_mass // cyl_mass))  # Ceiling division
        installed_mass = round(telemetry.installed_cylinders_count * cyl_mass, 1)

        if installed_mass < required_mass:
            warnings.append(
                f"Installed CO2 {installed_mass} kg insufficient for required {required_mass} kg ({required_cylinders} cyls)."
            )

        discharge_ok = telemetry.discharge_time_seconds <= self.MAX_DISCHARGE_TIME_SEC
        if not discharge_ok:
            warnings.append(
                f"Discharge time {telemetry.discharge_time_seconds} s exceeds SOLAS limit of {self.MAX_DISCHARGE_TIME_SEC} s (2 mins)."
            )

        delay_ok = self.MIN_PRE_DISCHARGE_DELAY_SEC <= telemetry.pre_discharge_delay_seconds <= self.MAX_PRE_DISCHARGE_DELAY_SEC
        if not delay_ok:
            warnings.append(
                f"Pre-discharge audible alarm delay {telemetry.pre_discharge_delay_seconds} s outside safe evacuation window [20-30 s]."
            )

        interlocks_ok = telemetry.ventilation_damper_closed and telemetry.fuel_quick_closing_valves_tripped
        if not interlocks_ok:
            if not telemetry.ventilation_damper_closed:
                warnings.append("Ventilation fire dampers NOT closed! CO2 escape / oxygen replenishment risk.")
            if not telemetry.fuel_quick_closing_valves_tripped:
                warnings.append("Fuel quick-closing valves (QCV) NOT tripped! Fuel supply must isolate.")

        status = "NORMAL"
        if installed_mass < required_mass or not interlocks_ok or not discharge_ok:
            status = "CRITICAL"
        elif not delay_ok or warnings:
            status = "WARNING"

        compliance_flags = {
            "solas_co2_mass_sufficient": installed_mass >= required_mass,
            "fss_two_minute_discharge": discharge_ok,
            "evacuation_alarm_delay_ok": delay_ok,
            "ventilation_fuel_isolated": interlocks_ok,
        }

        return Co2SystemAssessment(
            net_free_volume_m3=round(v_net, 1),
            required_co2_mass_kg=required_mass,
            installed_co2_mass_kg=installed_mass,
            required_cylinder_count=required_cylinders,
            two_minute_discharge_compliant=discharge_ok,
            interlocks_satisfied=interlocks_ok,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
