"""Unit tests for Maritime Phases 359 & 360 (Autopilot & Shaft Vibration).

Strictly kept under 200 lines, 0 mocks, testing real engineering dynamics.
"""

import pytest

from src.core.maritime.phase_359_adaptive_autopilot_rudder import (
    AdaptiveAutopilotEngine,
    AdaptiveAutopilotInput,
)
from src.core.maritime.phase_360_shaft_alignment_vibration import (
    ShaftAlignmentVibrationEngine,
    ShaftAlignmentVibrationInput,
)


def test_autopilot_nominal_steady_course():
    inp = AdaptiveAutopilotInput(
        vessel_id="V-CONTAINER-01",
        target_heading_deg=180.0,
        actual_heading_deg=180.2,
        rate_of_turn_deg_s=0.01,
        actual_rudder_angle_deg=0.5,
        sea_state_douglas=2,
        speed_knots=18.0,
        command_latency_seconds=0.8,
    )
    res = AdaptiveAutopilotEngine.evaluate(inp)
    assert res.vessel_id == "V-CONTAINER-01"
    assert res.heading_error_deg == -0.2
    assert res.adaptive_deadband_deg == 0.5
    assert res.is_hunting_prevented is True
    assert res.commanded_rudder_angle_deg == 0.0
    assert not res.is_steering_gear_lag_critical
    assert res.status == "STEADY_SEAWAY_HEADING"


def test_autopilot_high_sea_state_deadband_suppression():
    inp = AdaptiveAutopilotInput(
        vessel_id="V-TANKER-02",
        target_heading_deg=45.0,
        actual_heading_deg=46.5,
        rate_of_turn_deg_s=0.05,
        actual_rudder_angle_deg=0.0,
        sea_state_douglas=7,  # Rough/very high sea: deadband 2.5 deg
        speed_knots=12.0,
        command_latency_seconds=1.2,
    )
    res = AdaptiveAutopilotEngine.evaluate(inp)
    assert res.adaptive_deadband_deg == 2.5
    assert res.heading_error_deg == -1.5
    assert res.is_hunting_prevented is True
    assert res.commanded_rudder_angle_deg == 0.0
    assert res.status == "STEADY_SEAWAY_HEADING"


def test_autopilot_course_correction_and_solas_lag_alarm():
    inp = AdaptiveAutopilotInput(
        vessel_id="V-BULK-03",
        target_heading_deg=270.0,
        actual_heading_deg=250.0,  # 20 deg error
        rate_of_turn_deg_s=0.8,
        actual_rudder_angle_deg=5.0,
        sea_state_douglas=3,
        speed_knots=14.0,
        command_latency_seconds=4.5,  # SOLAS lag > 3.0 sec
    )
    res = AdaptiveAutopilotEngine.evaluate(inp)
    assert res.heading_error_deg == 20.0
    assert not res.is_hunting_prevented
    assert res.commanded_rudder_angle_deg > 10.0
    assert res.is_steering_gear_lag_critical is True
    assert res.status == "STEERING_GEAR_FOLLOW_UP_FAILURE"
    assert any("SOLAS II-1/29" in adv for adv in res.advisories)


def test_shaft_vibration_nominal_condition():
    inp = ShaftAlignmentVibrationInput(
        shaft_id="SHAFT-M-01",
        engine_rpm=90.0,
        propeller_blades_count=4,
        aft_bearing_reaction_kn=320.0,
        bearing_length_m=1.2,
        bearing_diameter_m=0.5,
        whirling_natural_frequency_hz=10.5,
        vibration_velocity_rms_mm_s=2.1,
    )
    res = ShaftAlignmentVibrationEngine.evaluate(inp)
    assert res.shaft_id == "SHAFT-M-01"
    # P = 0.320 MN / (1.2 * 0.5 = 0.6 m2) = 0.533 MPa <= 0.80 MPa
    assert res.aft_bearing_pressure_mpa == pytest.approx(0.533, abs=0.01)
    assert res.is_bearing_pressure_safe is True
    # BPF = 4 * 90 / 60 = 6.0 Hz. Whirling natural freq = 10.5 Hz. Margin = |6.0 - 10.5| / 10.5 = 42.86%
    assert res.blade_passing_frequency_hz == 6.0
    assert res.whirling_resonance_margin_percent > 40.0
    assert res.is_in_barred_speed_range is False
    assert res.vibration_severity_grade == "GOOD"
    assert res.status == "NOMINAL_PROPULSION"


def test_shaft_overpressure_and_barred_speed_range():
    inp = ShaftAlignmentVibrationInput(
        shaft_id="SHAFT-M-02",
        engine_rpm=100.0,
        propeller_blades_count=6,  # BPF = 6 * 100 / 60 = 10.0 Hz
        aft_bearing_reaction_kn=650.0,
        bearing_length_m=1.0,
        bearing_diameter_m=0.6,  # Area = 0.6 m2 -> P = 0.65 / 0.6 = 1.083 MPa (> 0.8 MPa)
        whirling_natural_frequency_hz=10.2,  # Resonance margin = |10.0 - 10.2| / 10.2 = 1.96% <= 10%
        vibration_velocity_rms_mm_s=8.5,  # Grade RESTRICTED_ALARM
    )
    res = ShaftAlignmentVibrationEngine.evaluate(inp)
    assert res.aft_bearing_pressure_mpa > 0.80
    assert res.is_bearing_pressure_safe is False
    assert res.blade_passing_frequency_hz == 10.0
    assert res.is_in_barred_speed_range is True
    assert res.vibration_severity_grade == "RESTRICTED_ALARM"
    assert res.status == "CRITICAL_BEARING_HAZARD"
    assert any("OVERLOAD" in adv for adv in res.advisories)
    assert any("BARRED SPEED RANGE" in adv for adv in res.advisories)
