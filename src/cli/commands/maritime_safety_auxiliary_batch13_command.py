"""CLI commands for Maritime Safety Auxiliary Batch 13 (Phases 511-514).
Strictly < 85 LOC, Typer subcommands for Scavenge Drain, Medical O2, Mooring Brake, and Water-Mist.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_511_scavenge_air_condensate_drain import (
    ScavengeAirCondensateDrainEngine, ScavengeCondensateTelemetry,
)
from src.core.maritime.phase_512_medical_oxygen_manifold_safety import (
    MedicalOxygenManifoldSafetyEngine, MedicalOxygenTelemetry,
)
from src.core.maritime.phase_513_mooring_winch_brake_render import (
    MooringWinchBrakeRenderEngine, MooringWinchTelemetry,
)
from src.core.maritime.phase_514_water_mist_local_application import (
    WaterMistLocalApplicationEngine, WaterMistTelemetry,
)

maritime_aux13_app = typer.Typer(
    name="maritime-aux13",
    help="Maritime Safety Automation Batch 13: Scavenge Condensate, Medical O2, Mooring Brake, Water-Mist",
)
console = Console()


@maritime_aux13_app.command("scavdrain-check")
def check_scavdrain(air_c: float = 44.0, dew_c: float = 36.0, pot_pct: float = 25.0, dp_kpa: float = 1.2) -> None:
    res = ScavengeAirCondensateDrainEngine.evaluate(
        ScavengeCondensateTelemetry(scavenge_air_temp_c=air_c, compressed_dewpoint_c=dew_c, drain_pot_level_pct=pot_pct, mist_catcher_dp_kpa=dp_kpa)
    )
    console.print(f"[bold cyan]Scavenge Drain:[/bold cyan] {res.condensate_state.value} | Oil Boost: {res.cylinder_oil_feed_boost} | Code: {res.alarm_code}")


@maritime_aux13_app.command("medo2-check")
def check_medo2(duty_bar: float = 110.0, line_bar: float = 4.5, ambient_o2: float = 20.9) -> None:
    res = MedicalOxygenManifoldSafetyEngine.evaluate(
        MedicalOxygenTelemetry(duty_cylinder_bar=duty_bar, delivery_line_bar=line_bar, locker_ambient_o2_pct=ambient_o2)
    )
    console.print(f"[bold green]Medical O2:[/bold green] {res.gas_state.value} | Reserve Active: {res.reserve_bank_engaged} | Code: {res.alarm_code}")


@maritime_aux13_app.command("mooring-check")
def check_mooring(tension_pct: float = 32.0, brake_pct: float = 60.0, wear_mm: float = 1.2) -> None:
    res = MooringWinchBrakeRenderEngine.evaluate(
        MooringWinchTelemetry(line_tension_pct_mbl=tension_pct, brake_setpoint_pct_mbl=brake_pct, lining_wear_mm=wear_mm)
    )
    console.print(f"[bold yellow]Mooring Brake:[/bold yellow] {res.brake_status.value} | MEG4 Compliant: {res.meg4_compliant} | Code: {res.alarm_code}")


@maritime_aux13_app.command("watermist-check")
def check_watermist(flame: bool = False, smoke: bool = False, manual: bool = False, pump_bar: float = 95.0) -> None:
    res = WaterMistLocalApplicationEngine.evaluate(
        WaterMistTelemetry(flame_detector_active=flame, smoke_heat_detector_active=smoke, manual_local_release=manual, pump_discharge_bar=pump_bar)
    )
    console.print(f"[bold red]Water Mist:[/bold red] {res.system_state.value} | Valve Open: {res.section_valve_open} | Code: {res.alarm_code}")
