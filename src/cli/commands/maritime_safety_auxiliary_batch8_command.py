"""CLI Commands for Maritime Automation Phases 491-494 (Batch 8).

Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_491_thrust_bearing_pad_temp import (
    ThrustBearingPadTempEngine,
    ThrustBearingTelemetry,
)
from src.core.maritime.phase_492_vacuum_sewage_tank_ejector import (
    VacuumSewageTankEjectorEngine,
    VacuumSewageTelemetry,
)
from src.core.maritime.phase_493_exhaust_scrubber_washwater_demister import (
    ExhaustScrubberWashwaterDemisterEngine,
    ScrubberTelemetry,
)
from src.core.maritime.phase_494_bow_thruster_pitch_power import (
    BowThrusterPitchPowerEngine,
    BowThrusterTelemetry,
)

maritime_aux8_app = typer.Typer(
    name="maritime-aux8",
    help="Maritime Automation Phases 491-494: Thrust Bearing, Vacuum Sewage, Scrubber, Bow Thruster",
)
console = Console()


@maritime_aux8_app.command("thrustbearing-check")
def check_thrust_bearing(
    ahead_c: float = typer.Option(68.0, help="Ahead pad temp deg C"),
    astern_c: float = typer.Option(65.0, help="Astern pad temp deg C"),
    oil_p_bar: float = typer.Option(1.2, help="Oil wedge pressure bar"),
    axial_mm: float = typer.Option(0.3, help="Shaft axial displacement mm"),
    booster_avail: bool = typer.Option(True, help="Standby booster pump available"),
) -> None:
    """Evaluate ME thrust bearing pad temperature, oil wedge pressure, and shaft axial displacement."""
    telem = ThrustBearingTelemetry(ahead_c, astern_c, oil_p_bar, axial_mm, booster_avail)
    res = ThrustBearingPadTempEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux8_app.command("sewage-check")
def check_vacuum_sewage(
    vacuum_bar: float = typer.Option(-0.55, help="System vacuum level gauge bar"),
    tank_pct: float = typer.Option(45.0, help="Collecting tank level %"),
    ejector_on: bool = typer.Option(False, help="Ejector pump running"),
    macerator_on: bool = typer.Option(False, help="Macerator pump running"),
) -> None:
    """Evaluate vacuum sewage tank holding level, ejector replenishment, and discharge lockout."""
    telem = VacuumSewageTelemetry(vacuum_bar, tank_pct, ejector_on, macerator_on)
    res = VacuumSewageTankEjectorEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux8_app.command("scrubber-check")
def check_exhaust_scrubber(
    quench_c: float = typer.Option(180.0, help="Quench gas inlet temperature deg C"),
    demister_kpa: float = typer.Option(1.2, help="Demister differential pressure kPa"),
    ph: float = typer.Option(6.8, help="Washwater pH"),
    turbidity_fnu: float = typer.Option(12.0, help="Discharge turbidity FNU"),
    wash_active: bool = typer.Option(False, help="Demister wash active"),
) -> None:
    """Evaluate SOx scrubber quench temperature bypass, demister dP wash, and pH/turbidity."""
    telem = ScrubberTelemetry(quench_c, demister_kpa, ph, turbidity_fnu, wash_active)
    res = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux8_app.command("bowthruster-check")
def check_bow_thruster(
    load_pct: float = typer.Option(85.0, help="Electric motor FLA load %"),
    servo_bar: float = typer.Option(32.0, help="Hydraulic servo pressure bar"),
    header_pct: float = typer.Option(75.0, help="Header tank level %"),
    oil_temp_c: float = typer.Option(52.0, help="Hydraulic oil temp deg C"),
    cooling_open: bool = typer.Option(False, help="Cooling boost valve open"),
) -> None:
    """Evaluate bow thruster motor current load, servo hydraulic pressure, and pitch safety."""
    telem = BowThrusterTelemetry(load_pct, servo_bar, header_pct, oil_temp_c, cooling_open)
    res = BowThrusterPitchPowerEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")
