"""CLI Commands for Maritime Automation Phases 475-478.

Exposes:
- sterntubeseal-check
- nitrogengen-check
- scavengefire-check
- bwmsuv-check

Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_475_stern_tube_seal_interlock import (
    SternTubeSealInterlockEngine,
    SternTubeSealTelemetry,
)
from src.core.maritime.phase_476_nitrogen_generator_interlock import (
    NitrogenGeneratorSafetyEngine,
    NitrogenGeneratorTelemetry,
)
from src.core.maritime.phase_477_scavenge_air_relief_fire_snuffing import (
    ScavengeFireSafetyEngine,
    ScavengeFireTelemetry,
)
from src.core.maritime.phase_478_bwms_uv_dose_transmittance import (
    BwmsUvSafetyEngine,
    BwmsUvTelemetry,
)

maritime_aux4_app = typer.Typer(
    name="maritime-aux4",
    help="Maritime Automation Phases 475-478: Stern Tube Seal, Nitrogen Gen, Scavenge Fire, BWMS UV",
)
console = Console()


@maritime_aux4_app.command("sterntubeseal-check")
def check_stern_tube_seal(
    bearing_temp_c: float = typer.Option(52.0, help="White metal bearing temp deg C"),
    air_barrier_dp_bar: float = typer.Option(0.28, help="Air barrier differential pressure bar"),
    leakage_l_day: float = typer.Option(0.8, help="Seal drain oil leakage L/24h"),
    cooling_flow: float = typer.Option(5.5, help="L.O. cooling water flow m3/h"),
) -> None:
    """Evaluate stern tube bearing temperature and seal air barrier interlocks."""
    telem = SternTubeSealTelemetry(bearing_temp_c, air_barrier_dp_bar, leakage_l_day, 85.0, cooling_flow, True)
    res = SternTubeSealInterlockEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux4_app.command("nitrogengen-check")
def check_nitrogen_gen(
    feed_pressure_bar: float = typer.Option(8.2, help="Feed air pressure bar"),
    feed_temp_c: float = typer.Option(46.0, help="Feed air temperature deg C"),
    o2_pct: float = typer.Option(0.8, help="Oxygen content % vol"),
    filter_dp_bar: float = typer.Option(0.12, help="Coalescing filter differential pressure bar"),
) -> None:
    """Evaluate deck nitrogen membrane generator separation parameters and O2 limits."""
    telem = NitrogenGeneratorTelemetry(feed_pressure_bar, feed_temp_c, o2_pct, filter_dp_bar, True, True)
    res = NitrogenGeneratorSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux4_app.command("scavengefire-check")
def check_scavenge_fire(
    manifold_temp_c: float = typer.Option(48.0, help="Scavenge manifold temperature deg C"),
    manifold_p_bar: float = typer.Option(0.85, help="Scavenge manifold pressure bar"),
    diff_temp_c: float = typer.Option(12.0, help="Max cylinder scavenge temp diff deg C"),
) -> None:
    """Evaluate main engine scavenge manifold temperature, relief valve, and snuffing."""
    telem = ScavengeFireTelemetry(manifold_temp_c, manifold_p_bar, diff_temp_c, True, 75.0)
    res = ScavengeFireSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux4_app.command("bwmsuv-check")
def check_bwms_uv(
    uv_t_pct: float = typer.Option(68.0, help="UV transmittance % at 254 nm"),
    uv_dose_j_m2: float = typer.Option(340.0, help="Applied UV dose J/m2"),
    reactor_temp_c: float = typer.Option(28.0, help="Chamber water temperature deg C"),
) -> None:
    """Evaluate BWMS UV reactor transmittance, dose criteria, and chamber safety."""
    telem = BwmsUvTelemetry(uv_t_pct, uv_dose_j_m2, reactor_temp_c, 250.0, 95.0, True)
    res = BwmsUvSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")
