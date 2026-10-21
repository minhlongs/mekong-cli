"""Typer CLI commands for Phases 447-450:
- COW Tank Cleaning check
- Deck Foam Extinguishing check
- Flue Gas Scrubber check
- VECS Vapor Manifold check
"""

import typer
from rich.console import Console

from src.core.maritime.phase_447_crude_oil_washing_machine import (
    CrudeOilWashingEngine,
    CowTelemetry,
)
from src.core.maritime.phase_448_fixed_deck_foam_extinguishing import (
    DeckFoamFireSystemEngine,
    DeckFoamTelemetry,
)
from src.core.maritime.phase_449_boiler_flue_gas_desulfurization import (
    BoilerFlueGasScrubberEngine,
    ScrubberTelemetry,
)
from src.core.maritime.phase_450_vapor_emission_control_vecs import (
    VaporEmissionControlEngine,
    VecsTelemetry,
)

app = typer.Typer(help="Phases 447-450 Tanker COW, Deck Foam, Scrubber & VECS Automation")
console = Console()


@app.command("cow-check")
def cow_check(
    pressure: float = typer.Option(9.5, help="Wash supply pressure in bar"),
    o2: float = typer.Option(5.2, help="Inert gas O2 volume %"),
    strip_flow: float = typer.Option(150.0, help="Stripping suction flow m3/h"),
    wash_flow: float = typer.Option(100.0, help="Washing machine flow m3/h"),
    rotation: float = typer.Option(1.8, help="Machine rotation speed deg/s"),
) -> None:
    engine = CrudeOilWashingEngine()
    res = engine.evaluate(CowTelemetry(pressure, o2, strip_flow, wash_flow, rotation))
    console.print(f"[bold]COW Status:[/bold] {res.status.value}")
    console.print(f"[bold]Wash Permitted:[/bold] {res.is_wash_permitted}")
    console.print(f"[bold]Stripping Ratio:[/bold] {res.stripping_ratio:.2f}")
    console.print(f"[bold]Summary:[/bold] {res.action_summary}")


@app.command("foam-check")
def foam_check(
    rate: float = typer.Option(0.75, help="Application rate L/min/m2"),
    induction: float = typer.Option(3.0, help="Foam induction %"),
    pressure: float = typer.Option(7.2, help="Monitor pressure bar"),
    throw: float = typer.Option(58.0, help="Throw distance meters"),
    duration: float = typer.Option(25.0, help="Foam reserve duration mins"),
) -> None:
    engine = DeckFoamFireSystemEngine()
    res = engine.evaluate(DeckFoamTelemetry(rate, induction, pressure, throw, duration))
    console.print(f"[bold]Foam Status:[/bold] {res.status.value}")
    console.print(f"[bold]Effective/Ready:[/bold] {res.is_ready_or_effective}")
    console.print(f"[bold]Throw Margin:[/bold] {res.throw_margin_m:.1f} m")
    console.print(f"[bold]Summary:[/bold] {res.action_summary}")


@app.command("vecs-check")
def vecs_check(
    manifold_p: float = typer.Option(25.0, help="Manifold pressure mbar"),
    o2: float = typer.Option(4.5, help="Vapor line O2 vol %"),
    temp_c: float = typer.Option(32.0, help="Detonation arrester temp C"),
    knockout_level: float = typer.Option(18.0, help="Knockout drum %"),
) -> None:
    engine = VaporEmissionControlEngine()
    res = engine.evaluate(VecsTelemetry(manifold_p, o2, temp_c, knockout_level))
    console.print(f"[bold]VECS Status:[/bold] {res.status.value}")
    console.print(f"[bold]Transfer Permitted:[/bold] {res.is_transfer_permitted}")
    console.print(f"[bold]O2 Margin:[/bold] {res.o2_margin_pct:.1f}%")
    console.print(f"[bold]Summary:[/bold] {res.action_summary}")
