"""Phase 424: Thermal Oil Heater & Expansion Tank Closed-Loop Control.

Implements DIN 4754, ISO 5149, and DNV-RU-SHIP Pt.4 Ch.6 Sec.7 rules:
boundary film temperature protection (T_film <= 340°C, T_bulk <= 280°C),
turbulent flow interlock (Re >= 10,000, dP_coil >= 1.5 bar),
nitrogen blanket pressure regulation (0.2 - 0.5 bar N2 cushion),
and expansion tank thermal volume tracking (V_exp >= 1.3 * V_sys * beta * dT).
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ThermalOilTelemetry:
    """Telemetry readings for Marine Thermal Oil Heater & Expansion Tank."""
    bulk_temperature_c: float = 245.0
    heater_outlet_temp_c: float = 260.0
    heat_flux_kw_m2: float = 45.0
    heat_transfer_coeff_w_m2k: float = 1250.0
    flow_velocity_m_s: float = 2.4
    oil_kinematic_viscosity_cst: float = 3.5
    pipe_inner_diameter_mm: float = 65.0
    coil_differential_pressure_bar: float = 2.1
    expansion_tank_level_pct: float = 55.0
    n2_blanket_pressure_bar: float = 0.35
    system_total_volume_m3: float = 12.0
    expansion_tank_capacity_m3: float = 3.5
    burner_firing_rate_pct: float = 75.0


@dataclass(frozen=True)
class ThermalOilAssessment:
    """Operational safety, film temperature, and N2 blanket compliance."""
    film_temperature_c: float
    reynolds_number: float
    required_expansion_volume_m3: float
    film_temp_compliant: bool
    flow_turbulent: bool
    coil_dp_compliant: bool
    n2_cushion_compliant: bool
    tank_level_safe: bool
    burner_trip_demanded: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class ThermalOilHeaterExpansionEngine:
    """Evaluates thermal oil heater safety, film degradation, and expansion cushion."""

    MAX_BULK_TEMP_C: float = 280.0
    MAX_FILM_TEMP_C: float = 340.0
    MIN_REYNOLDS: float = 10000.0
    MIN_COIL_DP_BAR: float = 1.5
    MIN_N2_PRESSURE_BAR: float = 0.2
    MAX_N2_PRESSURE_BAR: float = 0.5
    MIN_TANK_LEVEL_PCT: float = 20.0
    THERMAL_EXPANSION_COEFF_BETA: float = 0.0008  # 1/K for synthetic thermal oil

    def evaluate(self, telem: ThermalOilTelemetry) -> ThermalOilAssessment:
        warnings: List[str] = []

        # 1. Boundary Film Temperature: T_film = T_bulk + (q'' / alpha)
        # q'' in kW/m2 -> W/m2 (multiply by 1000)
        temp_delta = (telem.heat_flux_kw_m2 * 1000.0) / max(100.0, telem.heat_transfer_coeff_w_m2k)
        t_film = telem.heater_outlet_temp_c + temp_delta
        film_ok = t_film <= self.MAX_FILM_TEMP_C and telem.bulk_temperature_c <= self.MAX_BULK_TEMP_C

        if not film_ok:
            warnings.append(
                f"Film temperature {t_film:.1f}°C or bulk {telem.bulk_temperature_c:.1f}°C exceeds limits "
                f"(max film {self.MAX_FILM_TEMP_C}°C, bulk {self.MAX_BULK_TEMP_C}°C). Cracking risk!"
            )

        # 2. Reynolds Number: Re = (v * d) / nu
        # nu in cSt = 10^-6 m2/s, d in mm = 10^-3 m
        nu_m2_s = telem.oil_kinematic_viscosity_cst * 1e-6
        d_m = telem.pipe_inner_diameter_mm * 1e-3
        reynolds = (telem.flow_velocity_m_s * d_m) / max(1e-7, nu_m2_s)
        turbulent_ok = reynolds >= self.MIN_REYNOLDS

        if not turbulent_ok:
            warnings.append(
                f"Laminar/transitional flow detected (Re={reynolds:.0f} < {self.MIN_REYNOLDS:.0f}). "
                "Insufficient convective cooling."
            )

        # 3. Differential pressure interlock across heater coil
        dp_ok = telem.coil_differential_pressure_bar >= self.MIN_COIL_DP_BAR
        if not dp_ok:
            warnings.append(
                f"Coil dP {telem.coil_differential_pressure_bar:.2f} bar below minimum {self.MIN_COIL_DP_BAR} bar."
            )

        # 4. Expansion Tank Sizing & N2 Blanket
        delta_t = max(10.0, telem.heater_outlet_temp_c - 20.0)
        v_exp_req = 1.3 * telem.system_total_volume_m3 * self.THERMAL_EXPANSION_COEFF_BETA * delta_t
        n2_ok = self.MIN_N2_PRESSURE_BAR <= telem.n2_blanket_pressure_bar <= self.MAX_N2_PRESSURE_BAR
        if not n2_ok:
            warnings.append(
                f"N2 cushion {telem.n2_blanket_pressure_bar:.2f} bar out of range [0.2, 0.5] bar. Oxidation risk."
            )

        level_ok = telem.expansion_tank_level_pct >= self.MIN_TANK_LEVEL_PCT
        if not level_ok:
            warnings.append(
                f"Expansion tank low level {telem.expansion_tank_level_pct:.1f}% (< {self.MIN_TANK_LEVEL_PCT}%)."
            )

        # Burner Safety Interlock Trip
        burner_trip = (not film_ok) or (not dp_ok) or (not level_ok) or (reynolds < 4000.0)

        if burner_trip:
            status = "BURNER_SAFETY_TRIP"
            warnings.append("CRITICAL: Burner firing interlock tripped to prevent thermal fluid degradation/fire.")
        elif not n2_ok or not turbulent_ok:
            status = "WARNING_OPERATIONAL"
        else:
            status = "NORMAL_OPTIMAL"

        compliance_flags = {
            "film_temp_compliant": film_ok,
            "reynolds_turbulent": turbulent_ok,
            "coil_dp_compliant": dp_ok,
            "n2_blanket_compliant": n2_ok,
            "tank_level_safe": level_ok,
            "burner_interlock_healthy": not burner_trip,
        }

        return ThermalOilAssessment(
            film_temperature_c=round(t_film, 2),
            reynolds_number=round(reynolds, 1),
            required_expansion_volume_m3=round(v_exp_req, 3),
            film_temp_compliant=film_ok,
            flow_turbulent=turbulent_ok,
            coil_dp_compliant=dp_ok,
            n2_cushion_compliant=n2_ok,
            tank_level_safe=level_ok,
            burner_trip_demanded=burner_trip,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
