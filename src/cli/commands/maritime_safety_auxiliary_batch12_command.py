"""CLI commands for Maritime Safety Auxiliary Batch 12 (Phases 507-510).
Strictly < 85 LOC, Typer subcommands for Shaft Grounding, Emergency Bilge, WTD, and Helideck Foam.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_507_shaft_grounding_slip_ring import (
    ShaftGroundingSlipRingEngine, ShaftGroundingTelemetry,
)
from src.core.maritime.phase_508_emergency_bilge_direct_suction import (
    EmergencyBilgeDirectSuctionEngine, EmergencyBilgeTelemetry,
)
from src.core.maritime.phase_509_watertight_sliding_door_safety import (
    WatertightDoorTelemetry, WatertightSlidingDoorSafetyEngine,
)
from src.core.maritime.phase_510_helideck_foam_monitor_system import (
    HelideckFoamMonitorSystemEngine, HelideckFoamTelemetry,
)

maritime_aux12_app = typer.Typer(
    name="maritime-aux12",
    help="Maritime Safety Automation Batch 12: Shaft Earthing, Emergency Bilge, WTD, Helideck Foam",
)
console = Console()


@maritime_aux12_app.command("shaft-check")
def check_shaft(potential_mv: float = 22.0, current_ma: float = 45.0, wear_pct: float = 15.0) -> None:
    res = ShaftGroundingSlipRingEngine.evaluate(
        ShaftGroundingTelemetry(shaft_potential_mv=potential_mv, grounding_current_ma=current_ma, brush_wear_pct=wear_pct)
    )
    console.print(f"[bold cyan]Shaft Earthing:[/bold cyan] {res.grounding_state.value} | Pitting Risk: {res.bearing_pitting_risk} | Code: {res.alarm_code}")


@maritime_aux12_app.command("bilge-check")
def check_bilge(level_mm: float = 80.0, sw_pump_on: bool = True, high_sensor: bool = False) -> None:
    res = EmergencyBilgeDirectSuctionEngine.evaluate(
        EmergencyBilgeTelemetry(well_water_level_mm=level_mm, main_sw_pump_running=sw_pump_on, independent_high_sensor_tripped=high_sensor)
    )
    console.print(f"[bold green]Bilge State:[/bold green] {res.flood_state.value} | Direct Suction: {res.emergency_direct_suction_open} | Code: {res.alarm_code}")


@maritime_aux12_app.command("wtd-check")
def check_wtd(close_cmd: bool = True, closed: bool = True, acc_bar: float = 175.0, duration_sec: float = 28.0) -> None:
    res = WatertightSlidingDoorSafetyEngine.evaluate(
        WatertightDoorTelemetry(bridge_master_close_cmd=close_cmd, door_fully_closed=closed, accumulator_pressure_bar=acc_bar, closing_duration_sec=duration_sec)
    )
    console.print(f"[bold red]WTD Status:[/bold red] {res.door_status.value} | 3-Closures Ready: {res.solas_3_closures_ready} | Code: {res.alarm_code}")


@maritime_aux12_app.command("helideck-check")
def check_helideck(released: bool = False, nozzle_bar: float = 8.2, ratio_pct: float = 3.1, tank_pct: float = 95.0) -> None:
    res = HelideckFoamMonitorSystemEngine.evaluate(
        HelideckFoamTelemetry(release_activated=released, nozzle_manifold_bar=nozzle_bar, afff_induction_ratio_pct=ratio_pct, foam_tank_level_pct=tank_pct)
    )
    console.print(f"[bold yellow]Helideck Foam:[/bold yellow] {res.foam_status.value} | CAP437 Compliant: {res.cap437_compliant} | Code: {res.alarm_code}")
