"""CLI commands for Maritime Safety Auxiliary Batch 15 (Phases 519-522).
Strictly < 85 LOC, Typer subcommands for Turning Gear, Grey Water, Deck Crane, and Escape Trunk.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_519_turning_gear_start_interlock import (
    TurningGearStartInterlockEngine, TurningGearTelemetry,
)
from src.core.maritime.phase_520_grey_water_tank_ventilation import (
    GreyWaterTankVentilationEngine, GreyWaterTelemetry,
)
from src.core.maritime.phase_521_deck_crane_overload_limiter import (
    DeckCraneOverloadLimiterEngine, DeckCraneTelemetry,
)
from src.core.maritime.phase_522_escape_trunk_pressurization import (
    EscapeTrunkPressurizationEngine, EscapeTrunkTelemetry,
)

maritime_aux15_app = typer.Typer(
    name="maritime-aux15",
    help="Maritime Safety Automation Batch 15: Turning Gear, Grey Water, Deck Crane, Escape Trunk",
)
console = Console()


@maritime_aux15_app.command("turninggear-check")
def check_turninggear(disengaged: bool = True, air_open: bool = True, cocks_closed: bool = True) -> None:
    res = TurningGearStartInterlockEngine.evaluate(
        TurningGearTelemetry(turning_gear_disengaged=disengaged, main_air_shutoff_valve_open=air_open, indicator_cocks_closed=cocks_closed)
    )
    console.print(f"[bold cyan]Turning Gear:[/bold cyan] {res.interlock_state.value} | Start Permitted: {res.starting_air_permitted} | Code: {res.alarm_code}")


@maritime_aux15_app.command("greywater-check")
def check_greywater(level_pct: float = 45.0, h2s_ppm: float = 1.0, in_port: bool = False, overboard: bool = False) -> None:
    res = GreyWaterTankVentilationEngine.evaluate(
        GreyWaterTelemetry(tank_level_pct=level_pct, h2s_concentration_ppm=h2s_ppm, in_zero_discharge_port_zone=in_port, overboard_valve_open=overboard)
    )
    console.print(f"[bold green]Grey Water:[/bold green] {res.system_state.value} | Standby Pump: {res.standby_pump_running} | Code: {res.alarm_code}")


@maritime_aux15_app.command("crane-check")
def check_crane(load_pct: float = 70.0, boom_deg: float = 45.0, slack_wire: bool = False) -> None:
    res = DeckCraneOverloadLimiterEngine.evaluate(
        DeckCraneTelemetry(hook_load_pct_swl=load_pct, boom_angle_deg=boom_deg, slack_wire_detected=slack_wire)
    )
    console.print(f"[bold yellow]Deck Crane:[/bold yellow] {res.operating_state.value} | Hoist Permitted: {res.hoist_up_permitted} | Code: {res.alarm_code}")


@maritime_aux15_app.command("escapetrunk-check")
def check_escapetrunk(pressure_pa: float = 35.0, volts: float = 24.5) -> None:
    res = EscapeTrunkPressurizationEngine.evaluate(
        EscapeTrunkTelemetry(trunk_overpressure_pa=pressure_pa, emergency_lighting_volts=volts)
    )
    console.print(f"[bold red]Escape Trunk:[/bold red] {res.trunk_status.value} | Protected: {res.smoke_ingress_protected} | Code: {res.alarm_code}")
