"""Pytest test suite for Maritime Safety Automation Batch 16 (Phases 523-526).
Covers Torsional BSR Damper, BNWAS Cascade, Paint Locker Deluge, and Accommodation Ladder.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_523_torsional_vibration_bsr_damper import (
    TorsionalBsrState, TorsionalBsrTelemetry, TorsionalVibrationBsrDamperEngine,
)
from src.core.maritime.phase_524_bnwas_watch_alarm_cascade import (
    BnwasCascadeState, BnwasTelemetry, BnwasWatchAlarmCascadeEngine,
)
from src.core.maritime.phase_525_paint_locker_vent_waterspray import (
    PaintLockerSafetyState, PaintLockerTelemetry, PaintLockerVentWatersprayEngine,
)
from src.core.maritime.phase_526_accommodation_ladder_winch_safety import (
    AccommodationLadderState, AccommodationLadderTelemetry, AccommodationLadderWinchSafetyEngine,
)
from src.core.maritime_safety_auxiliary_batch16_engine import (
    MaritimeSafetyAuxiliaryBatch16Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch16_command import maritime_aux16_app

runner = CliRunner()


def test_phase_523_torsional_vibration_bsr_damper() -> None:
    res_safe = TorsionalVibrationBsrDamperEngine.evaluate(
        TorsionalBsrTelemetry(shaft_rpm=76.0, dwell_time_in_bsr_sec=0.0)
    )
    assert res_safe.bsr_state == TorsionalBsrState.SAFE_CONTINUOUS_RPM_ENVELOPE
    assert res_safe.fast_passage_boost_active is False

    res_transit = TorsionalVibrationBsrDamperEngine.evaluate(
        TorsionalBsrTelemetry(shaft_rpm=48.0, dwell_time_in_bsr_sec=10.0)
    )
    assert res_transit.bsr_state == TorsionalBsrState.BSR_FAST_PASSAGE_TRANSIT
    assert res_transit.fast_passage_boost_active is True
    assert res_transit.alarm_active is False

    res_dwell = TorsionalVibrationBsrDamperEngine.evaluate(
        TorsionalBsrTelemetry(shaft_rpm=48.0, dwell_time_in_bsr_sec=28.0)
    )
    assert res_dwell.bsr_state == TorsionalBsrState.BSR_DWELL_RESONANCE_SLOWDOWN_TRIP
    assert res_dwell.governor_leave_bsr_cmd is True

    res_stress = TorsionalVibrationBsrDamperEngine.evaluate(
        TorsionalBsrTelemetry(shaft_rpm=75.0, torsional_stress_mpa=49.0)
    )
    assert res_stress.bsr_state == TorsionalBsrState.DAMPER_THERMAL_STRESS_CRITICAL_ALARM


def test_phase_524_bnwas_watch_alarm_cascade() -> None:
    res_dormant = BnwasWatchAlarmCascadeEngine.evaluate(
        BnwasTelemetry(unattended_elapsed_sec=200.0, dormant_period_sec=360.0)
    )
    assert res_dormant.cascade_state == BnwasCascadeState.WATCH_OFFICER_ALERT_DORMANT

    res_s1 = BnwasWatchAlarmCascadeEngine.evaluate(
        BnwasTelemetry(unattended_elapsed_sec=365.0, dormant_period_sec=360.0)
    )
    assert res_s1.cascade_state == BnwasCascadeState.STAGE1_BRIDGE_VISUAL_AUDIBLE_ALERT
    assert res_s1.bridge_local_alarm is True
    assert res_s1.back_up_officer_call is False

    res_s2 = BnwasWatchAlarmCascadeEngine.evaluate(
        BnwasTelemetry(unattended_elapsed_sec=385.0, dormant_period_sec=360.0)
    )
    assert res_s2.cascade_state == BnwasCascadeState.STAGE2_BACKUP_OFFICER_CABIN_ALARM
    assert res_s2.back_up_officer_call is True

    res_s3 = BnwasWatchAlarmCascadeEngine.evaluate(
        BnwasTelemetry(unattended_elapsed_sec=475.0, dormant_period_sec=360.0)
    )
    assert res_s3.cascade_state == BnwasCascadeState.STAGE3_MASTER_SHIPWIDE_EMERGENCY_ALARM
    assert res_s3.master_all_cabin_gong is True


def test_phase_525_paint_locker_vent_waterspray() -> None:
    res_ok = PaintLockerVentWatersprayEngine.evaluate(
        PaintLockerTelemetry(air_changes_per_hour=10.0, flammable_vapor_lel_pct=2.0)
    )
    assert res_ok.safety_state == PaintLockerSafetyState.SAFE_VENTILATED_LOCKER
    assert res_ok.ex_lighting_energized is True

    res_vent = PaintLockerVentWatersprayEngine.evaluate(
        PaintLockerTelemetry(air_changes_per_hour=4.0, flammable_vapor_lel_pct=2.0)
    )
    assert res_vent.safety_state == PaintLockerSafetyState.VENTILATION_FAILURE_LIGHTING_INTERLOCK
    assert res_vent.ex_lighting_energized is False

    res_fire = PaintLockerVentWatersprayEngine.evaluate(
        PaintLockerTelemetry(air_changes_per_hour=10.0, flammable_vapor_lel_pct=35.0, fire_detected_in_locker=True)
    )
    assert res_fire.safety_state == PaintLockerSafetyState.FIRE_WATERSPRAY_DELUGE_RELEASE
    assert res_fire.waterspray_deluge_open is True
    assert res_fire.vent_damper_closed is True


def test_phase_526_accommodation_ladder_winch_safety() -> None:
    res_ok = AccommodationLadderWinchSafetyEngine.evaluate(
        AccommodationLadderTelemetry(ladder_angle_deg=42.0, live_load_kg=350.0)
    )
    assert res_ok.ladder_state == AccommodationLadderState.SAFE_EMBARKATION_ACCESS
    assert res_ok.winch_lowering_permitted is True

    res_steep = AccommodationLadderWinchSafetyEngine.evaluate(
        AccommodationLadderTelemetry(ladder_angle_deg=58.0, live_load_kg=200.0)
    )
    assert res_steep.ladder_state == AccommodationLadderState.STEEP_INCLINATION_55DEG_LOCKOUT
    assert res_steep.mechanical_pawl_engaged is True

    res_sea = AccommodationLadderWinchSafetyEngine.evaluate(
        AccommodationLadderTelemetry(ladder_angle_deg=30.0, live_load_kg=0.0, vessel_underway_speed_kn=3.5, ladder_stowed_and_latched=False)
    )
    assert res_sea.ladder_state == AccommodationLadderState.UNSTOWED_AT_SEA_DEPARTURE_ALARM


def test_maritime_auxiliary_batch16_coordinator() -> None:
    bsr = TorsionalBsrTelemetry(shaft_rpm=78.0)
    bnwas = BnwasTelemetry(unattended_elapsed_sec=100.0)
    paint = PaintLockerTelemetry(air_changes_per_hour=10.0, flammable_vapor_lel_pct=1.0)
    ladder = AccommodationLadderTelemetry(ladder_angle_deg=40.0, live_load_kg=250.0)

    res = MaritimeSafetyAuxiliaryBatch16Engine.evaluate_batch16(bsr, bnwas, paint, ladder)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch16_cli() -> None:
    res1 = runner.invoke(maritime_aux16_app, ["torsionalbsr-check", "--rpm", "78.0"])
    assert res1.exit_code == 0
    assert "SAFE_CONTINUOUS_RPM_ENVELOPE" in res1.stdout

    res2 = runner.invoke(maritime_aux16_app, ["bnwas-check", "--elapsed-sec", "120.0"])
    assert res2.exit_code == 0
    assert "WATCH_OFFICER_ALERT_DORMANT" in res2.stdout

    res3 = runner.invoke(maritime_aux16_app, ["paintlocker-check", "--ach", "10.0"])
    assert res3.exit_code == 0
    assert "SAFE_VENTILATED_LOCKER" in res3.stdout

    res4 = runner.invoke(maritime_aux16_app, ["accomladder-check", "--angle-deg", "38.0"])
    assert res4.exit_code == 0
    assert "SAFE_EMBARKATION_ACCESS" in res4.stdout
