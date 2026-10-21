"""CLI Commands for Maritime Automation Phases 463-466.

Exposes:
- sterntube-check
- deckseal-check
- scavenge-check
- fwg-check
Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_463_stern_tube_gravity_tank import (
    SternTubeGravityTankEngine,
    SternTubeGravityTelemetry,
)
from src.core.maritime.phase_464_deck_water_seal_inert_gas import (
    DeckWaterSealEngine,
    DeckWaterSealTelemetry,
)
from src.core.maritime.phase_465_main_engine_scavenge_air_fire import (
    ScavengeAirFireEngine,
    ScavengeFireTelemetry,
)
from src.core.maritime.phase_466_fresh_water_generator_salinometer import (
    FreshWaterGeneratorEngine,
    FwgSalinometerTelemetry,
)

maritime_aux_app = typer.Typer(
    name="maritime-aux",
    help="Maritime Automation Phases 463-466: Stern Tube, Deck Seal, Scavenge Fire, FWG",
)
console = Console()


@maritime_aux_app.command("sterntube-check")
def check_stern_tube(
    level_pct: float = typer.Option(55.0, help="Gravity tank oil level %"),
    temp_c: float = typer.Option(45.0, help="Oil temperature deg C"),
    seal_dp_bar: float = typer.Option(0.25, help="Aft seal oil-water DP bar"),
    water_pct: float = typer.Option(0.01, help="Water content in oil %"),
) -> None:
    """Evaluate stern tube gravity tank lubrication and aft seal differential pressure."""
    telem = SternTubeGravityTelemetry(level_pct, temp_c, seal_dp_bar, water_pct, True)
    assessment = SternTubeGravityTankEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {assessment.status.value}")
    console.print(f"Remarks: {assessment.remarks}")


@maritime_aux_app.command("deckseal-check")
def check_deck_seal(
    level_mm_wg: float = typer.Option(500.0, help="Seal water level mm WG"),
    flow_m3_h: float = typer.Option(12.0, help="Makeup water flow m3/h"),
    water_temp_c: float = typer.Option(18.0, help="Water temperature deg C"),
    hc_ppm: float = typer.Option(5.0, help="Downstream HC gas ppm"),
) -> None:
    """Evaluate inert gas deck water seal liquid barrier integrity."""
    telem = DeckWaterSealTelemetry(level_mm_wg, flow_m3_h, water_temp_c, hc_ppm, False)
    assessment = DeckWaterSealEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {assessment.status.value}")
    console.print(f"Remarks: {assessment.remarks}")


@maritime_aux_app.command("scavenge-check")
def check_scavenge_fire(
    temp_c: float = typer.Option(48.0, help="Scavenge air temperature deg C"),
    manifold_p_bar: float = typer.Option(2.2, help="Manifold pressure bar"),
    drain_closed: bool = typer.Option(True, help="Scavenge drain shutoff closed"),
    engine_rpm: float = typer.Option(85.0, help="Main engine RPM"),
) -> None:
    """Evaluate main engine scavenge receiver fire detection and safety trip."""
    telem = ScavengeFireTelemetry(temp_c, manifold_p_bar, drain_closed, engine_rpm, False)
    assessment = ScavengeAirFireEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {assessment.status.value}")
    console.print(f"Remarks: {assessment.remarks}")


@maritime_aux_app.command("fwg-check")
def check_fwg_salinity(
    salinity_ppm: float = typer.Option(4.5, help="Distillate salinity ppm"),
    vacuum_pct: float = typer.Option(92.0, help="Evaporator vacuum %"),
    jacket_temp_c: float = typer.Option(80.0, help="Jacket water inlet temp deg C"),
    flow_m3_day: float = typer.Option(25.0, help="Fresh water output m3/day"),
) -> None:
    """Evaluate fresh water generator vacuum boiling and salinometer dump valve."""
    telem = FwgSalinometerTelemetry(salinity_ppm, vacuum_pct, jacket_temp_c, flow_m3_day, False)
    assessment = FreshWaterGeneratorEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {assessment.status.value}")
    console.print(f"Remarks: {assessment.remarks}")
