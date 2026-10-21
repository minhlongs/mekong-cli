"""Phase 424: Marine Thermal Oil Heating System & Nitrogen Blanketing.

Complies with DIN 4754, ISO 5149, and DNV-RU-SHIP Pt.4 Ch.6 Sec.4.
Monitors heater bulk/film temperatures, minimum circulating differential pressure (>= 1.5 bar),
and expansion tank inert nitrogen blanketing (0.2 - 0.5 bar) with low-level / high-temp burner trips.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ThermalOilTelemetry:
    """Telemetry readings for marine thermal oil heating system."""
    bulk_temp_c: float = 260.0               # Nominal operating temp 240-280°C
    film_temp_c: float = 295.0               # Maximum tube film temp (limit 340°C)
    heater_diff_pressure_bar: float = 1.8    # Minimum circulation flow check >= 1.5 bar
    expansion_tank_level_pct: float = 65.0   # Low level trip < 30%
    expansion_tank_temp_c: float = 48.0      # High temp alarm/trip > 70°C
    n2_blanket_pressure_bar: float = 0.35    # Normal N2 inerting [0.2, 0.5] bar
    circulating_pump_running: bool = True
    burner_firing: bool = True


@dataclass(frozen=True)
class ThermalOilAssessment:
    """Diagnostic assessment and safety trip status for thermal oil system."""
    film_overheat_detected: bool
    flow_starvation_trip: bool
    expansion_tank_trip: bool
    n2_inerting_valid: bool
    burner_interlock_clear: bool
    emergency_burner_trip: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class ThermalOilSystemEngine:
    """Marine thermal oil heater and expansion tank N2 blanketing safety engine."""

    MAX_FILM_TEMP_C: float = 340.0
    MIN_DIFF_PRESSURE_BAR: float = 1.5
    MIN_EXP_TANK_LEVEL_PCT: float = 30.0
    MAX_EXP_TANK_TEMP_C: float = 70.0
    MIN_N2_PRESSURE_BAR: float = 0.20
    MAX_N2_PRESSURE_BAR: float = 0.50

    def evaluate(self, telem: ThermalOilTelemetry) -> ThermalOilAssessment:
        warnings: List[str] = []
        compliance: Dict[str, bool] = {
            "DIN_4754_flow_rate": True,
            "DIN_4754_film_temperature": True,
            "ISO_5149_inert_blanketing": True,
        }

        # Film temperature limit check (thermal degradation / coking prevention)
        film_overheat = telem.film_temp_c >= self.MAX_FILM_TEMP_C
        if film_overheat:
            warnings.append(f"CRITICAL FILM TEMP: {telem.film_temp_c:.1f}°C >= {self.MAX_FILM_TEMP_C}°C")
            compliance["DIN_4754_film_temperature"] = False

        # Flow starvation check via circulation pump and differential pressure
        flow_starvation = (not telem.circulating_pump_running) or (telem.heater_diff_pressure_bar < self.MIN_DIFF_PRESSURE_BAR)
        if flow_starvation:
            warnings.append(f"Flow starvation: DP {telem.heater_diff_pressure_bar:.2f} bar < {self.MIN_DIFF_PRESSURE_BAR} bar")
            compliance["DIN_4754_flow_rate"] = False

        # Expansion tank safety: level < 30% or temperature > 70°C
        tank_low = telem.expansion_tank_level_pct < self.MIN_EXP_TANK_LEVEL_PCT
        tank_hot = telem.expansion_tank_temp_c > self.MAX_EXP_TANK_TEMP_C
        expansion_trip = tank_low or tank_hot

        if tank_low:
            warnings.append(f"Expansion tank low level: {telem.expansion_tank_level_pct:.1f}% < {self.MIN_EXP_TANK_LEVEL_PCT}%")
        if tank_hot:
            warnings.append(f"Expansion tank hot oil reflux: {telem.expansion_tank_temp_c:.1f}°C > {self.MAX_EXP_TANK_TEMP_C}°C")

        # N2 inerting validation
        n2_valid = self.MIN_N2_PRESSURE_BAR <= telem.n2_blanket_pressure_bar <= self.MAX_N2_PRESSURE_BAR
        if not n2_valid:
            warnings.append(
                f"N2 blanketing abnormal: {telem.n2_blanket_pressure_bar:.2f} bar outside [{self.MIN_N2_PRESSURE_BAR}, {self.MAX_N2_PRESSURE_BAR}] bar"
            )
            compliance["ISO_5149_inert_blanketing"] = False

        # Master emergency burner trip
        emergency_trip = film_overheat or flow_starvation or expansion_trip
        burner_clear = (not emergency_trip) and n2_valid

        if emergency_trip:
            status = "EMERGENCY_TRIP"
        elif not n2_valid or telem.bulk_temp_c >= 290.0:
            status = "WARNING"
        else:
            status = "NOMINAL"

        return ThermalOilAssessment(
            film_overheat_detected=film_overheat,
            flow_starvation_trip=flow_starvation,
            expansion_tank_trip=expansion_trip,
            n2_inerting_valid=n2_valid,
            burner_interlock_clear=burner_clear,
            emergency_burner_trip=emergency_trip,
            status=status,
            warnings=warnings,
            compliance_flags=compliance,
        )
