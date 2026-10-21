"""Phase 383: Marine Centrifugal Fuel Oil Purifier & Clarifier Automation Engine.

Implements ISO 8217:2024, CIMAC guidelines, and MEPC.1/Circ.753 for centrifugal
separation of HFO/VLSFO, catalytic fines removal, bowl de-sludging and vibration.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class FuelPurifierInput:
    """Input telemetry for centrifugal fuel purifier & clarifier."""
    fuel_type: str = "HFO"  # HFO, VLSFO, MGO
    flow_rate_m3_h: float = 3.5
    bowl_speed_rpm: float = 8500.0
    bowl_radius_m: float = 0.22
    inlet_temp_c: float = 98.0
    cat_fines_inlet_ppm: float = 45.0  # Al + Si particles
    water_content_inlet_pct: float = 1.2
    vibration_velocity_rms_mm_s: float = 3.8  # ISO 10816-3
    operating_water_pressure_bar: float = 3.0
    hours_since_last_discharge: float = 1.2


@dataclass
class FuelPurifierResult:
    """Evaluation result for marine fuel purifier operation."""
    g_force_factor: float
    separation_efficiency_pct: float
    cat_fines_outlet_ppm: float
    water_content_outlet_pct: float
    purifier_status: str  # OPTIMAL, SUB_OPTIMAL, WARNING, CRITICAL_TRIP
    desludge_required: bool
    vibration_status: str  # NORMAL, RESTRICTED, UNACCEPTABLE
    feed_valve_open: bool
    warnings: List[str] = field(default_factory=list)


class MarineFuelPurifierEngine:
    """Evaluates centrifuge purification performance and safety interlocks."""

    G_ACCEL = 9.80665  # m/s^2
    MAX_OUTLET_CAT_FINES_PPM = 15.0
    CRITICAL_CAT_FINES_PPM = 25.0
    ISO_VIB_LIMIT_RMS = 7.1  # mm/s
    MIN_WATER_PRESSURE_BAR = 2.5
    MAX_DESLUDGE_INTERVAL_HOURS = 2.0

    def evaluate(self, telemetry: FuelPurifierInput) -> FuelPurifierResult:
        warnings: List[str] = []

        # 1. Centrifugal Acceleration Factor G = r * omega^2 / g
        omega = (2.0 * math.pi * telemetry.bowl_speed_rpm) / 60.0
        g_force = (telemetry.bowl_radius_m * (omega ** 2)) / self.G_ACCEL

        # 2. Separation Efficiency based on temperature and fuel type
        # Optimum separation temperature for HFO: 98 C +/- 2 C
        temp_delta = abs(telemetry.inlet_temp_c - 98.0)
        temp_penalty = min(0.35, (temp_delta / 10.0) * 0.15) if telemetry.fuel_type == "HFO" else 0.05
        base_efficiency = 0.90 - temp_penalty

        # Higher flow rate reduces residence time
        flow_penalty = max(0.0, (telemetry.flow_rate_m3_h - 2.5) * 0.04)
        efficiency = max(0.50, min(0.96, base_efficiency - flow_penalty))
        efficiency_pct = round(efficiency * 100.0, 2)

        # 3. Residual Catalytic Fines & Water
        cat_fines_outlet = round(telemetry.cat_fines_inlet_ppm * (1.0 - efficiency), 2)
        water_outlet = round(telemetry.water_content_inlet_pct * (1.0 - (efficiency * 0.95)), 3)

        # 4. De-sludge / Bowl Discharge check
        desludge_required = (
            telemetry.hours_since_last_discharge >= self.MAX_DESLUDGE_INTERVAL_HOURS
            or cat_fines_outlet > self.MAX_OUTLET_CAT_FINES_PPM
        )

        # 5. Vibration Evaluation (ISO 10816-3 Class II/III)
        if telemetry.vibration_velocity_rms_mm_s >= self.ISO_VIB_LIMIT_RMS:
            vibration_status = "UNACCEPTABLE"
            warnings.append(f"VIBRATION TRIP: {telemetry.vibration_velocity_rms_mm_s} mm/s exceeds 7.1 mm/s limit.")
        elif telemetry.vibration_velocity_rms_mm_s >= 4.5:
            vibration_status = "RESTRICTED"
            warnings.append(f"VIBRATION WARNING: High bowl vibration {telemetry.vibration_velocity_rms_mm_s} mm/s.")
        else:
            vibration_status = "NORMAL"

        # 6. Operating Water Interlock
        if telemetry.operating_water_pressure_bar < self.MIN_WATER_PRESSURE_BAR:
            warnings.append(
                f"OPERATING WATER LOW: {telemetry.operating_water_pressure_bar} bar < {self.MIN_WATER_PRESSURE_BAR} bar. "
                "Bowl closing pressure lost."
            )

        # 7. Overall System Status
        feed_valve_open = True
        if vibration_status == "UNACCEPTABLE" or cat_fines_outlet > self.CRITICAL_CAT_FINES_PPM:
            purifier_status = "CRITICAL_TRIP"
            feed_valve_open = False
            warnings.append("FEED CUT-OFF: Purifier trip activated, 3-way feed valve diverted to settling tank.")
        elif cat_fines_outlet > self.MAX_OUTLET_CAT_FINES_PPM or desludge_required:
            purifier_status = "WARNING"
            warnings.append(
                f"AL+SI EXCEEDANCE: Outlet cat fines {cat_fines_outlet} ppm exceeds {self.MAX_OUTLET_CAT_FINES_PPM} ppm limit."
            )
        elif temp_delta > 5.0 and telemetry.fuel_type == "HFO":
            purifier_status = "SUB_OPTIMAL"
            warnings.append(f"TEMPERATURE DEVIATION: HFO inlet temperature {telemetry.inlet_temp_c}C off target 98C.")
        else:
            purifier_status = "OPTIMAL"

        return FuelPurifierResult(
            g_force_factor=round(g_force, 1),
            separation_efficiency_pct=efficiency_pct,
            cat_fines_outlet_ppm=cat_fines_outlet,
            water_content_outlet_pct=water_outlet,
            purifier_status=purifier_status,
            desludge_required=desludge_required,
            vibration_status=vibration_status,
            feed_valve_open=feed_valve_open,
            warnings=warnings,
        )
