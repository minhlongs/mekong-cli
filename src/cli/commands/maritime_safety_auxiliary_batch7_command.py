"""CLI Commands for Maritime Automation Phases 487-490.

Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_487_jacket_cooling_temp_flow import (
    JacketCoolingTelemetry,
    JacketCoolingTempFlowEngine,
)
from src.core.maritime.phase_488_deck_water_seal_level import (
    DeckWaterSealLevelEngine,
    DeckWaterSealTelemetry,
)
from src.core.maritime.phase_489_central_cooling_3way_valve import (
    CentralCooling3WayValveEngine,
    CentralCoolingTelemetry,
)
from src.core.maritime.phase_490_starting_air_compressor_unloader import (
    StartingAirCompressorUnloaderEngine,
    StartingAirTelemetry,
)

maritime_aux7_app = typer.Typer(
    name="maritime-aux7",
    help="Maritime Automation Phases 487-490: Jacket Cooling, Deck Seal, Central Cooler, Starting Air",
)
console = Console()


@maritime_aux7_app.command("jacketcooling-check")
def check_jacket_cooling(
    outlet_c: float = typer.Option(84.0, help="Jacket outlet temp deg C"),
    inlet_c: float = typer.Option(72.0, help="Jacket inlet temp deg C"),
    dp_bar: float = typer.Option(1.2, help="Engine block differential pressure bar"),
    tank_pct: float = typer.Option(65.0, help="Expansion tank level %"),
    preheat_avail: bool = typer.Option(True, help="Preheater pump available"),
) -> None:
    """Evaluate jacket cooling water temperature, flow dP, and expansion tank level."""
    telem = JacketCoolingTelemetry(outlet_c, inlet_c, dp_bar, tank_pct, preheat_avail)
    res = JacketCoolingTempFlowEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux7_app.command("deckseal-check")
def check_deck_seal(
    height_mm: float = typer.Option(500.0, help="Water column height mm"),
    ambient_c: float = typer.Option(18.0, help="Ambient temperature deg C"),
    downstream_mbar: float = typer.Option(15.0, help="Downstream IGS pressure mbar"),
    inlet_mbar: float = typer.Option(20.0, help="Inlet supply pressure mbar"),
    valve_open: bool = typer.Option(False, help="Refill valve open state"),
) -> None:
    """Evaluate IGS deck water seal column height, freeze protection, and backflow."""
    telem = DeckWaterSealTelemetry(height_mm, ambient_c, downstream_mbar, inlet_mbar, valve_open)
    res = DeckWaterSealLevelEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux7_app.command("centralcooling-check")
def check_central_cooling(
    lt_temp_c: float = typer.Option(36.0, help="LT freshwater temp deg C"),
    ht_temp_c: float = typer.Option(85.0, help="HT jacket water temp deg C"),
    sw_dp_bar: float = typer.Option(1.6, help="Seawater pump differential pressure bar"),
    standby_avail: bool = typer.Option(True, help="Standby SW pump available"),
    ht_setpoint_c: float = typer.Option(85.0, help="HT setpoint deg C"),
) -> None:
    """Evaluate central cooling LT loop tolerance, HT 3-way mixing valve bypass, and SW head."""
    telem = CentralCoolingTelemetry(lt_temp_c, ht_temp_c, sw_dp_bar, standby_avail, ht_setpoint_c)
    res = CentralCooling3WayValveEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux7_app.command("startingair-check")
def check_starting_air(
    p_bar: float = typer.Option(28.0, help="Air receiver pressure bar"),
    temp_c: float = typer.Option(120.0, help="High-stage discharge temperature deg C"),
    running: bool = typer.Option(False, help="Compressor running state"),
    purge_s: float = typer.Option(6.0, help="Unloader purge elapsed seconds"),
    start_req: bool = typer.Option(False, help="Start request active"),
) -> None:
    """Evaluate starting air compressor pressure band, unloader purge, and relief valve trip."""
    telem = StartingAirTelemetry(p_bar, temp_c, running, purge_s, start_req)
    res = StartingAirCompressorUnloaderEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")
