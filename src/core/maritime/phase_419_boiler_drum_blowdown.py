"""Phase 419: Marine Auxiliary Boiler Drum Level & Blowdown Automation.

Implements IACS M53, SOLAS II-1 Reg 32, and ASME BPVC Section I requirements:
3-element feedwater control, continuous surface blowdown (TDS), bottom blowdown,
and low-low water level (LLWL) burner cutoff interlocks.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BoilerDrumTelemetry:
    """Telemetry readings for marine auxiliary steam boiler."""
    drum_level_mm: float = 0.0              # Normal Water Level = 0 mm (range -250 to +250)
    steam_mass_flow_tph: float = 12.0       # Metric tons/hour
    feedwater_flow_tph: float = 12.0        # Metric tons/hour
    drum_pressure_bar: float = 16.5         # Working pressure
    water_tds_ppm: float = 2200.0           # Total dissolved solids
    bottom_sludge_hours_since_flush: float = 12.0
    burner_flame_detected: bool = True


@dataclass(frozen=True)
class BoilerDrumAssessment:
    """Assessment of boiler drum level stability, blowdown state, and burner trip."""
    feedwater_valve_demand_pct: float
    surface_blowdown_active: bool
    bottom_blowdown_required: bool
    shrink_swell_detected: bool
    burner_tripped: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class BoilerDrumBlowdownEngine:
    """3-element level regulator and automated TDS/sludge blowdown monitor."""

    NWL_TARGET_MM: float = 0.0
    HIGH_WATER_ALARM_MM: float = 120.0
    LOW_WATER_ALARM_MM: float = -120.0
    LLWL_TRIP_MM: float = -180.0
    MAX_PERMISSIBLE_PRESSURE_BAR: float = 22.0
    TDS_BLOWDOWN_THRESHOLD_PPM: float = 2500.0
    BOTTOM_BLOWDOWN_INTERVAL_HOURS: float = 24.0

    def evaluate(self, telemetry: BoilerDrumTelemetry) -> BoilerDrumAssessment:
        warnings: List[str] = []
        burner_tripped = False

        # 3-Element Feedwater Demand: Level Error + (Steam Flow - Feed Flow)
        level_error_mm = self.NWL_TARGET_MM - telemetry.drum_level_mm
        flow_imbalance_tph = telemetry.steam_mass_flow_tph - telemetry.feedwater_flow_tph
        base_demand = 50.0 + (level_error_mm * 0.25) + (flow_imbalance_tph * 2.5)
        feedwater_valve_demand = max(0.0, min(100.0, base_demand))

        # Shrink / Swell Detection
        shrink_swell = False
        if telemetry.steam_mass_flow_tph > 15.0 and telemetry.drum_level_mm > 50.0 and flow_imbalance_tph > 2.0:
            shrink_swell = True
            warnings.append("Steam swell phenomenon detected: drum level artificially elevated by boiling bubbles")

        # Surface Continuous Blowdown (TDS control)
        surface_blowdown = telemetry.water_tds_ppm >= self.TDS_BLOWDOWN_THRESHOLD_PPM
        if surface_blowdown:
            warnings.append(f"High TDS ({telemetry.water_tds_ppm} ppm) exceeds limit: opening surface blowdown valve")

        # Bottom Sludge Intermittent Blowdown
        bottom_blowdown = telemetry.bottom_sludge_hours_since_flush >= self.BOTTOM_BLOWDOWN_INTERVAL_HOURS
        if bottom_blowdown:
            warnings.append("Bottom blowdown required for sludge and scale ejection")

        # Safety Interlocks & Burner Trip
        if telemetry.drum_level_mm <= self.LLWL_TRIP_MM:
            burner_tripped = True
            warnings.append(f"EMERGENCY: Drum level {telemetry.drum_level_mm} mm below LLWL (-180 mm). Burner trip!")

        if telemetry.drum_pressure_bar > self.MAX_PERMISSIBLE_PRESSURE_BAR:
            burner_tripped = True
            warnings.append(f"Overpressure trip: {telemetry.drum_pressure_bar} bar exceeds {self.MAX_PERMISSIBLE_PRESSURE_BAR} bar")

        if not telemetry.burner_flame_detected:
            burner_tripped = True
            warnings.append("Flame failure safeguard activated: fuel supply quick-closing valve isolated")

        status = "TRIPPED" if burner_tripped else ("WARNING" if warnings else "NORMAL")

        return BoilerDrumAssessment(
            feedwater_valve_demand_pct=round(feedwater_valve_demand, 2),
            surface_blowdown_active=surface_blowdown,
            bottom_blowdown_required=bottom_blowdown,
            shrink_swell_detected=shrink_swell,
            burner_tripped=burner_tripped,
            status=status,
            warnings=warnings,
            compliance_flags={
                "iacs_m53_water_level_safe": telemetry.drum_level_mm > self.LLWL_TRIP_MM,
                "solas_ii1_pressure_within_limits": telemetry.drum_pressure_bar <= self.MAX_PERMISSIBLE_PRESSURE_BAR,
                "asme_bpvc_flame_safeguard_healthy": telemetry.burner_flame_detected,
                "tds_within_mepc_threshold": telemetry.water_tds_ppm < self.TDS_BLOWDOWN_THRESHOLD_PPM,
            },
        )
