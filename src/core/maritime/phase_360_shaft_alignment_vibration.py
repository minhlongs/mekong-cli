"""Maritime Phase 360: Propeller Shaft Alignment & Whirling Vibration Engine.

Compliant with IACS UR M68 and ISO 10816-6.
Evaluates aft stern tube bearing pressure, blade passing frequency, and barred speed range.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ShaftAlignmentVibrationInput:
    shaft_id: str
    engine_rpm: float
    propeller_blades_count: int  # e.g., 4, 5, 6 blades
    aft_bearing_reaction_kn: float
    bearing_length_m: float
    bearing_diameter_m: float
    whirling_natural_frequency_hz: float
    vibration_velocity_rms_mm_s: float = 2.8


@dataclass
class ShaftAlignmentVibrationResult:
    shaft_id: str
    aft_bearing_pressure_mpa: float
    is_bearing_pressure_safe: bool
    blade_passing_frequency_hz: float
    whirling_resonance_margin_percent: float
    is_in_barred_speed_range: bool
    vibration_severity_grade: str
    status: str
    advisories: List[str] = field(default_factory=list)


class ShaftAlignmentVibrationEngine:
    """Evaluates shaft alignment loading and whirling dynamic resonance."""

    MAX_PERMISSIBLE_PRESSURE_MPA: float = 0.80  # Babbitt / reinforced synthetic limit
    BSR_RESONANCE_THRESHOLD_PERCENT: float = 10.0  # Within 10% of natural frequency

    @classmethod
    def evaluate(cls, inp: ShaftAlignmentVibrationInput) -> ShaftAlignmentVibrationResult:
        advisories: List[str] = []

        # 1. Projected bearing area and surface pressure (P = F / (L * D))
        projected_area_m2 = max(0.001, inp.bearing_length_m * inp.bearing_diameter_m)
        bearing_pressure_mpa = round((inp.aft_bearing_reaction_kn / 1000.0) / projected_area_m2, 3)
        is_bearing_safe = bearing_pressure_mpa <= cls.MAX_PERMISSIBLE_PRESSURE_MPA

        if not is_bearing_safe:
            advisories.append(
                f"OVERLOAD: Aft Stern Tube Bearing pressure {bearing_pressure_mpa} MPa exceeds limit {cls.MAX_PERMISSIBLE_PRESSURE_MPA} MPa. Risk of edge loading or wiping."
            )

        # 2. Blade Passing Frequency (BPF = Z * RPM / 60)
        bpf_hz = round((inp.propeller_blades_count * inp.engine_rpm) / 60.0, 2)

        # 3. Whirling vibration resonance proximity
        nat_freq = max(0.1, inp.whirling_natural_frequency_hz)
        resonance_delta_percent = round((abs(bpf_hz - nat_freq) / nat_freq) * 100.0, 1)
        is_in_bsr = resonance_delta_percent <= cls.BSR_RESONANCE_THRESHOLD_PERCENT

        if is_in_bsr:
            advisories.append(
                f"BARRED SPEED RANGE (BSR): BPF {bpf_hz} Hz matches whirling mode {nat_freq} Hz (margin {resonance_delta_percent}% <= 10%). Continuous running prohibited."
            )
            advisories.append("Accelerate rapidly through this RPM band to prevent fatigue shaft fracturing.")

        # 4. Vibration severity evaluation (ISO 10816-6 Class 3/4 marine propulsion)
        if inp.vibration_velocity_rms_mm_s <= 4.5:
            severity = "GOOD"
        elif inp.vibration_velocity_rms_mm_s <= 7.1:
            severity = "SATISFACTORY"
        elif inp.vibration_velocity_rms_mm_s <= 11.2:
            severity = "RESTRICTED_ALARM"
            advisories.append(f"HIGH VIBRATION: Measured RMS {inp.vibration_velocity_rms_mm_s} mm/s indicates shaft misalignment or mass unbalance.")
        else:
            severity = "DANGER_UNACCEPTABLE"
            advisories.append(f"CRITICAL VIBRATION: Measured RMS {inp.vibration_velocity_rms_mm_s} mm/s requires immediate RPM reduction.")

        # Overall operational status
        if not is_bearing_safe or severity == "DANGER_UNACCEPTABLE":
            status = "CRITICAL_BEARING_HAZARD"
        elif is_in_bsr or severity == "RESTRICTED_ALARM":
            status = "RESONANCE_BARRED_ZONE"
        else:
            status = "NOMINAL_PROPULSION"
            advisories.append("Shaft alignment reaction and dynamic vibration within permissible class limits.")

        return ShaftAlignmentVibrationResult(
            shaft_id=inp.shaft_id,
            aft_bearing_pressure_mpa=bearing_pressure_mpa,
            is_bearing_pressure_safe=is_bearing_safe,
            blade_passing_frequency_hz=bpf_hz,
            whirling_resonance_margin_percent=resonance_delta_percent,
            is_in_barred_speed_range=is_in_bsr,
            vibration_severity_grade=severity,
            status=status,
            advisories=advisories,
        )
