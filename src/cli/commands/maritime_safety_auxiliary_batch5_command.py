"""CLI Commands for Maritime Automation Phases 479-482.

Exposes:
- cargoholdbilge-check
- auxblower-check
- boilerfeed-check
- steeringgear-check

Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_479_cargo_hold_bilge_eductor import (
    CargoHoldBilgeEductorEngine,
    CargoHoldBilgeTelemetry,
)
from src.core.maritime.phase_480_turbocharger_aux_blower import (
    AuxBlowerTelemetry,
    TurbochargerAuxBlowerEngine,
)
from src.core.maritime.phase_481_boiler_feedwater_deaerator import (
    BoilerFeedwaterDeaeratorEngine,
    BoilerFeedwaterTelemetry,
)
from src.core.maritime.phase_482_steering_gear_phase_failure import (
    SteeringGearSafetyEngine,
    SteeringGearTelemetry,
)

maritime_aux5_app = typer.Typer(
    name="maritime-aux5",
    help="Maritime Automation Phases 479-482: Cargo Hold Bilge, Aux Blower, Boiler Feedwater, Steering Gear",
)
console = Console()


@maritime_aux5_app.command("cargoholdbilge-check")
def check_cargohold_bilge(
    water_level_m: float = typer.Option(0.2, help="Hold water level m"),
    driving_p_bar: float = typer.Option(5.0, help="Driving pressure bar"),
    backpressure_bar: float = typer.Option(1.0, help="Discharge backpressure bar"),
    backflow_ok: bool = typer.Option(True, help="Backflow check valve status"),
) -> None:
    """Evaluate cargo hold bilge flooding level and eductor motive readiness."""
    telem = CargoHoldBilgeTelemetry(water_level_m, driving_p_bar, backpressure_bar, backflow_ok)
    res = CargoHoldBilgeEductorEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux5_app.command("auxblower-check")
def check_aux_blower(
    scavenge_p_bar: float = typer.Option(0.75, help="Scavenge pressure bar"),
    dp_dt_bar_s: float = typer.Option(0.0, help="Pressure rate bar/s"),
    blower_running: bool = typer.Option(False, help="Blower running state"),
    engine_running: bool = typer.Option(True, help="Main engine running state"),
) -> None:
    """Evaluate turbocharger auxiliary blower auto cut-in and surge protection."""
    telem = AuxBlowerTelemetry(scavenge_p_bar, dp_dt_bar_s, blower_running, engine_running)
    res = TurbochargerAuxBlowerEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux5_app.command("boilerfeed-check")
def check_boiler_feed(
    conductivity_us_cm: float = typer.Option(3.0, help="Condensate conductivity uS/cm"),
    deaerator_p_bar: float = typer.Option(0.30, help="Deaerator pressure bar"),
    tsat_c: float = typer.Option(107.0, help="Saturation temperature deg C"),
    tactual_c: float = typer.Option(106.0, help="Actual deaerator temperature deg C"),
) -> None:
    """Evaluate boiler feedwater deaeration saturation and condensate salinity."""
    telem = BoilerFeedwaterTelemetry(conductivity_us_cm, deaerator_p_bar, tsat_c, tactual_c)
    res = BoilerFeedwaterDeaeratorEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux5_app.command("steeringgear-check")
def check_steering_gear(
    reservoir_pct: float = typer.Option(80.0, help="Hydraulic reservoir level %"),
    imbalance_pct: float = typer.Option(3.0, help="3-phase imbalance %"),
    phase_loss: bool = typer.Option(False, help="Loss of power phase"),
    standby_p_bar: float = typer.Option(0.0, help="Standby unit pressure bar"),
    elapsed_s: float = typer.Option(0.0, help="Standby takeover elapsed seconds"),
) -> None:
    """Evaluate steering gear power failure, standby takeover, and auto-isolation."""
    telem = SteeringGearTelemetry(reservoir_pct, imbalance_pct, phase_loss, standby_p_bar, elapsed_s)
    res = SteeringGearSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")
