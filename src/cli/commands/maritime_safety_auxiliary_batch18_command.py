"""CLI commands for Maritime Safety Auxiliary Batch 18 (Phases 531-534).
Strictly < 85 LOC, Typer subcommands for Double-Wall Fuel Pipe, IGG, Stern Air-Guard, Enclosed Space.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_531_double_wall_fuel_pipe_leak import (
    DoubleWallFuelPipeLeakEngine, DoubleWallFuelPipeTelemetry,
)
from src.core.maritime.phase_532_inert_gas_generator_stoichiometry import (
    InertGasGeneratorStoichiometryEngine, InertGasGeneratorTelemetry,
)
from src.core.maritime.phase_533_stern_tube_airguard_seal_balance import (
    SternTubeAirguardSealBalanceEngine, SternTubeAirguardTelemetry,
)
from src.core.maritime.phase_534_enclosed_space_entry_gas_interlock import (
    EnclosedSpaceEntryGasInterlockEngine, EnclosedSpaceEntryTelemetry,
)

maritime_aux18_app = typer.Typer(
    name="maritime-aux18",
    help="Maritime Safety Automation Batch 18: HP Fuel Pipe, IGG Stoichiometry, Stern Air-Guard, Enclosed Space",
)
console = Console()


@maritime_aux18_app.command("fuelpipe-check")
def check_fuelpipe(
    annular_bar: float = 0.05, drain_pct: float = 10.0, surface_c: float = 145.0, qcv_bar: float = 6.5
) -> None:
    res = DoubleWallFuelPipeLeakEngine.evaluate(
        DoubleWallFuelPipeTelemetry(annular_bar, drain_pct, surface_c, qcv_bar)
    )
    console.print(f"[bold cyan]HP Fuel Pipe:[/bold cyan] {res.state.value} | Slowdown: {res.engine_slowdown_required} | Code: {res.interlock_code}")


@maritime_aux18_app.command("igg-check")
def check_igg(
    o2_pct: float = 3.8, scrubber_c: float = 42.0, water_bar: float = 2.8, eq_lambda: float = 1.03
) -> None:
    res = InertGasGeneratorStoichiometryEngine.evaluate(
        InertGasGeneratorTelemetry(o2_pct, scrubber_c, water_bar, eq_lambda)
    )
    console.print(f"[bold green]IGG Stoichiometry:[/bold green] {res.state.value} | Deck Open: {res.deck_main_isolation_valve_open} | Code: {res.interlock_code}")


@maritime_aux18_app.command("sternairguard-check")
def check_sternairguard(
    air_bar: float = 1.65, sea_bar: float = 1.40, flow_nl: float = 22.0, water_pct: float = 0.15, temp_c: float = 48.0
) -> None:
    res = SternTubeAirguardSealBalanceEngine.evaluate(
        SternTubeAirguardTelemetry(air_bar, sea_bar, flow_nl, water_pct, temp_c)
    )
    console.print(f"[bold yellow]Stern Air-Guard:[/bold yellow] {res.state.value} | dP: {res.air_over_sea_dp_bar} | Code: {res.interlock_code}")


@maritime_aux18_app.command("enclosedspace-check")
def check_enclosedspace(
    o2_pct: float = 20.9, lel_pct: float = 0.0, co_ppm: float = 0.0, h2s_ppm: float = 0.0, purge_min: float = 45.0, ach: float = 12.0
) -> None:
    res = EnclosedSpaceEntryGasInterlockEngine.evaluate(
        EnclosedSpaceEntryTelemetry(o2_pct, lel_pct, co_ppm, h2s_ppm, purge_min, ach)
    )
    console.print(f"[bold red]Enclosed Space:[/bold red] {res.state.value} | Released: {res.entry_hatch_interlock_released} | Code: {res.interlock_code}")
