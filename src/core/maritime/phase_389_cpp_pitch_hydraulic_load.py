"""Maritime Phase 389: Controllable Pitch Propeller (CPP) Hydraulics & Pitch Load Control.

Implements DNV-RU-SHIP Pt.4 Ch.5, IACS UR M43, and ISO 484 propeller standards.
Evaluates CPP hydraulic servo actuating pressure, full travel response rate,
main engine combinator pitch de-rating, and stern tube seal differential pressure.
Strictly < 200 LOC, zero mocks, deterministic physical formulation.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CppPitchControlInput:
    """Input telemetry for controllable pitch propeller and hydraulic servo hub."""
    commanded_pitch_deg: float = 20.0      # Commanded pitch angle (e.g. +25 full ahead, -15 astern)
    actual_pitch_deg: float = 19.8         # Feedback pitch angle from feedback transmitter
    pitch_travel_time_s: float = 18.0      # Time taken for full stroke traversal (<= 25.0s limit)
    hydraulic_pressure_bar: float = 55.0   # Servomotor supply oil pressure (normal 40-70 bar)
    seal_header_pressure_bar: float = 2.2  # Stern tube seal header tank pressure
    sea_water_draft_pressure_bar: float = 1.6 # Seawater hydrostatic pressure at shaft center
    main_engine_load_pct: float = 88.0     # Engine load percentage (MCR %)
    exhaust_gas_temp_c: float = 430.0      # Main engine mean exhaust temperature


@dataclass
class CppPitchControlResult:
    """Operational evaluation for marine CPP hydraulic pitch propulsion."""
    hydraulic_status: str                  # NORMAL, LOW_PRESSURE, OVERPRESSURE
    pitch_response_compliant: bool
    seal_barrier_intact: bool
    seal_pressure_margin_bar: float
    engine_overload_protection: bool
    recommended_pitch_deg: float
    warnings: List[str] = field(default_factory=list)


class CppPitchControlEngine:
    """Evaluates CPP hydraulic actuating system, stern tube seal and combinator pitch load."""

    MIN_HYD_PRESSURE_BAR = 35.0
    NORMAL_HYD_MIN_BAR = 40.0
    NORMAL_HYD_MAX_BAR = 70.0
    RELIEF_VALVE_SETPOINT_BAR = 85.0
    MAX_FULL_TRAVEL_TIME_S = 25.0
    MIN_SEAL_MARGIN_BAR = 0.30             # Minimum positive seal pressure over seawater head
    MAX_CONTINUOUS_ENGINE_LOAD_PCT = 100.0
    MAX_EXHAUST_TEMP_C = 480.0

    def evaluate(self, telemetry: CppPitchControlInput) -> CppPitchControlResult:
        warnings: List[str] = []

        # 1. Hydraulic Servomotor Oil Pressure Check
        if telemetry.hydraulic_pressure_bar < self.MIN_HYD_PRESSURE_BAR:
            hydraulic_status = "LOW_PRESSURE"
            warnings.append(
                f"CPP HYDRAULIC PRESSURE LOW: {telemetry.hydraulic_pressure_bar:.1f} bar < {self.MIN_HYD_PRESSURE_BAR} bar trip limit"
            )
        elif telemetry.hydraulic_pressure_bar >= self.RELIEF_VALVE_SETPOINT_BAR:
            hydraulic_status = "OVERPRESSURE"
            warnings.append(
                f"CPP HYDRAULIC OVERPRESSURE: {telemetry.hydraulic_pressure_bar:.1f} bar >= {self.RELIEF_VALVE_SETPOINT_BAR} bar relief"
            )
        else:
            hydraulic_status = "NORMAL"

        # 2. Pitch Response & Travel Rate (Full ahead to full astern <= 25.0s)
        pitch_response_compliant = telemetry.pitch_travel_time_s <= self.MAX_FULL_TRAVEL_TIME_S
        if not pitch_response_compliant:
            warnings.append(
                f"CPP TRAVEL SLUGGISH: Full travel time {telemetry.pitch_travel_time_s:.1f} s > {self.MAX_FULL_TRAVEL_TIME_S} s limit"
            )

        # 3. Stern Tube Seal Barrier Differential (P_seal - P_sea >= 0.30 bar)
        seal_margin = telemetry.seal_header_pressure_bar - telemetry.sea_water_draft_pressure_bar
        seal_barrier_intact = seal_margin >= self.MIN_SEAL_MARGIN_BAR
        if not seal_barrier_intact:
            warnings.append(
                f"STERN TUBE SEAL BARRIER COMPROMISED: Differential {seal_margin:.2f} bar < {self.MIN_SEAL_MARGIN_BAR} bar (ingress risk)"
            )

        # 4. Main Engine Combinator Load Control & Pitch Auto-Reduction
        # If engine is overloaded (> 100% MCR or exhaust temp > 480C), automatically reduce pitch
        engine_overload = (
            telemetry.main_engine_load_pct > self.MAX_CONTINUOUS_ENGINE_LOAD_PCT
            or telemetry.exhaust_gas_temp_c > self.MAX_EXHAUST_TEMP_C
        )
        recommended_pitch = telemetry.commanded_pitch_deg

        if engine_overload:
            # Pitch de-rating: 0.5 deg reduction per 1% overload above 100%
            overload_delta = max(0.0, telemetry.main_engine_load_pct - self.MAX_CONTINUOUS_ENGINE_LOAD_PCT)
            pitch_reduction = max(1.5, overload_delta * 0.5)
            if recommended_pitch > 0:
                recommended_pitch = max(0.0, recommended_pitch - pitch_reduction)
            warnings.append(
                f"ENGINE OVERLOAD PROTECTION ACTIVE: Pitch auto-reduced from {telemetry.commanded_pitch_deg:.1f} to {recommended_pitch:.1f} deg"
            )

        return CppPitchControlResult(
            hydraulic_status=hydraulic_status,
            pitch_response_compliant=pitch_response_compliant,
            seal_barrier_intact=seal_barrier_intact,
            seal_pressure_margin_bar=round(seal_margin, 2),
            engine_overload_protection=engine_overload,
            recommended_pitch_deg=round(recommended_pitch, 2),
            warnings=warnings,
        )
