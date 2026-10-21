"""CLI commands for Maritime Safety Auxiliary Batch 16 (Phases 523-526).
Strictly < 85 LOC, Typer subcommands for Torsional BSR, BNWAS, Paint Locker, and Accom Ladder.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_523_torsional_vibration_bsr_damper import (
    TorsionalBsrTelemetry, TorsionalVibrationBsrDamperEngine,
)
from src.core.maritime.phase_524_bnwas_watch_alarm_cascade import (
    BnwasTelemetry, BnwasWatchAlarmCascadeEngine,
)
from src.core.maritime.phase_525_paint_locker_vent_waterspray import (
    PaintLockerTelemetry, PaintLockerVentWatersprayEngine,
)
from src.core.maritime.phase_526_accommodation_ladder_winch_safety import (
    AccommodationLadderTelemetry, AccommodationLadderWinchSafetyEngine,
)

maritime_aux16_app = typer.Typer(
    name="maritime-aux16",
    help="Maritime Safety Automation Batch 16: Torsional BSR, BNWAS, Paint Locker, Accom Ladder",
)
console = Console()


@maritime_aux16_app.command("torsionalbsr-check")
def check_torsionalbsr(rpm: float = 78.0, dwell_sec: float = 0.0, stress_mpa: float = 18.0) -> None:
    res = TorsionalVibrationBsrDamperEngine.evaluate(
        TorsionalBsrTelemetry(shaft_rpm=rpm, dwell_time_in_bsr_sec=dwell_sec, torsional_stress_mpa=stress_mpa)
    )
    console.print(f"[bold cyan]Torsional BSR:[/bold cyan] {res.bsr_state.value} | Fast Passage: {res.fast_passage_boost_active} | Code: {res.alarm_code}")


@maritime_aux16_app.command("bnwas-check")
def check_bnwas(elapsed_sec: float = 120.0, dormant_sec: float = 360.0, autopilot: bool = True) -> None:
    res = BnwasWatchAlarmCascadeEngine.evaluate(
        BnwasTelemetry(unattended_elapsed_sec=elapsed_sec, dormant_period_sec=dormant_sec, autopilot_engaged=autopilot)
    )
    console.print(f"[bold green]BNWAS Cascade:[/bold green] {res.cascade_state.value} | Officer Call: {res.back_up_officer_call} | Code: {res.alarm_code}")


@maritime_aux16_app.command("paintlocker-check")
def check_paintlocker(ach: float = 10.0, lel_pct: float = 2.0, fan_on: bool = True, fire: bool = False) -> None:
    res = PaintLockerVentWatersprayEngine.evaluate(
        PaintLockerTelemetry(air_changes_per_hour=ach, flammable_vapor_lel_pct=lel_pct, ex_exhaust_fan_running=fan_on, fire_detected_in_locker=fire)
    )
    console.print(f"[bold yellow]Paint Locker:[/bold yellow] {res.safety_state.value} | Ex Light: {res.ex_lighting_energized} | Code: {res.alarm_code}")


@maritime_aux16_app.command("accomladder-check")
def check_accomladder(angle_deg: float = 38.0, load_kg: float = 300.0, speed_kn: float = 0.0) -> None:
    res = AccommodationLadderWinchSafetyEngine.evaluate(
        AccommodationLadderTelemetry(ladder_angle_deg=angle_deg, live_load_kg=load_kg, vessel_underway_speed_kn=speed_kn)
    )
    console.print(f"[bold red]Accom Ladder:[/bold red] {res.ladder_state.value} | Pawl Engaged: {res.mechanical_pawl_engaged} | Code: {res.alarm_code}")
