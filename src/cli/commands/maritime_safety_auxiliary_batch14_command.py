"""CLI commands for Maritime Safety Auxiliary Batch 14 (Phases 515-518).
Strictly < 85 LOC, Typer subcommands for Windlass, Switchboard, Bow Visor, and Elevator.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_515_anchor_windlass_payout_brake import (
    AnchorWindlassPayoutBrakeEngine, AnchorWindlassTelemetry,
)
from src.core.maritime.phase_516_switchboard_insulation_load_shed import (
    SwitchboardInsulationLoadShedEngine, SwitchboardTelemetry,
)
from src.core.maritime.phase_517_bow_visor_stern_ramp_cleat import (
    BowVisorRampTelemetry, BowVisorSternRampCleatEngine,
)
from src.core.maritime.phase_518_marine_elevator_roll_governor import (
    MarineElevatorRollGovernorEngine, MarineElevatorTelemetry,
)

maritime_aux14_app = typer.Typer(
    name="maritime-aux14",
    help="Maritime Safety Automation Batch 14: Windlass, Switchboard, Bow Visor, Marine Elevator",
)
console = Console()


@maritime_aux14_app.command("windlass-check")
def check_windlass(speed_m_s: float = 2.5, shackles: float = 5.0, heaving: bool = False, wash_bar: float = 2.8) -> None:
    res = AnchorWindlassPayoutBrakeEngine.evaluate(
        AnchorWindlassTelemetry(payout_speed_m_s=speed_m_s, remaining_shackles_in_locker=shackles, heaving_in_active=heaving, hawsepipe_wash_bar=wash_bar)
    )
    console.print(f"[bold cyan]Windlass:[/bold cyan] {res.operating_state.value} | Brake Clamp: {res.band_brake_auto_clamp} | Code: {res.alarm_code}")


@maritime_aux14_app.command("msb-check")
def check_msb(insulation_mohm: float = 5.0, load_pct: float = 78.0, duration_sec: float = 0.0) -> None:
    res = SwitchboardInsulationLoadShedEngine.evaluate(
        SwitchboardTelemetry(insulation_mohm=insulation_mohm, generator_load_pct=load_pct, overload_duration_sec=duration_sec)
    )
    console.print(f"[bold green]Switchboard:[/bold green] {res.bus_state.value} | Shed: {res.non_essential_loads_shed} | Code: {res.alarm_code}")


@maritime_aux14_app.command("visor-check")
def check_visor(at_sea: bool = True, cleats_locked: bool = True, gasket_bar: float = 3.0, ingress: bool = False) -> None:
    res = BowVisorSternRampCleatEngine.evaluate(
        BowVisorRampTelemetry(vessel_at_sea_mode=at_sea, all_hydraulic_cleats_locked=cleats_locked, pneumatic_gasket_bar=gasket_bar, threshold_water_ingress_detected=ingress)
    )
    console.print(f"[bold yellow]Shell Door:[/bold yellow] {res.seal_status.value} | Green Light: {res.bridge_departure_green_light} | Code: {res.alarm_code}")


@maritime_aux14_app.command("elevator-check")
def check_elevator(roll_deg: float = 4.0, speed_pct: float = 100.0, smoke: bool = False) -> None:
    res = MarineElevatorRollGovernorEngine.evaluate(
        MarineElevatorTelemetry(vessel_roll_angle_deg=roll_deg, car_speed_pct_rated=speed_pct, hoistway_smoke_detected=smoke)
    )
    console.print(f"[bold red]Elevator:[/bold red] {res.elevator_mode.value} | Safety Gear: {res.safety_gear_wedges_engaged} | Code: {res.alarm_code}")
