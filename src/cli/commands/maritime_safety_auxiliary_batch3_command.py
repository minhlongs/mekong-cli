"""CLI Commands for Maritime Automation Phases 471-474.

Exposes:
- bowthruster-check
- emergfirepump-check
- oilmist-check
- scrubbereffluent-check

Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_471_bow_thruster_interlock import (
    BowThrusterInterlockEngine,
    BowThrusterTelemetry,
)
from src.core.maritime.phase_472_emergency_fire_pump_sea_suction import (
    EmergencyFirePumpSafetyEngine,
    EmergencyFirePumpTelemetry,
)
from src.core.maritime.phase_473_crankcase_oil_mist_optical_detector import (
    OilMistDetectorEngine,
    OilMistTelemetry,
)
from src.core.maritime.phase_474_scrubber_effluent_ph_polycyclic_aromatic import (
    ScrubberEffluentSafetyEngine,
    ScrubberEffluentTelemetry,
)

maritime_aux3_app = typer.Typer(
    name="maritime-aux3",
    help="Maritime Automation Phases 471-474: Bow Thruster, Emerg Fire Pump, Oil Mist, Scrubber Effluent",
)
console = Console()


@maritime_aux3_app.command("bowthruster-check")
def check_bow_thruster(
    oil_temp: float = typer.Option(55.0, help="Hydraulic oil temp deg C"),
    header_lvl: float = typer.Option(60.0, help="Header tank level %"),
    gen_load: float = typer.Option(70.0, help="Generator load %"),
    pitch: float = typer.Option(80.0, help="Commanded pitch %"),
    grill_dp: float = typer.Option(0.15, help="Grill differential pressure bar"),
) -> None:
    """Evaluate tunnel bow thruster hydraulic interlocks and generator load."""
    telem = BowThrusterTelemetry(oil_temp, header_lvl, gen_load, pitch, grill_dp, True)
    res = BowThrusterInterlockEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux3_app.command("emergfirepump-check")
def check_emerg_fire_pump(
    suction_head_m: float = typer.Option(3.2, help="Static suction head meters"),
    vacuum_bar: float = typer.Option(-0.65, help="Priming vacuum bar"),
    elapsed_sec: float = typer.Option(20.0, help="Priming elapsed seconds"),
    discharge_p: float = typer.Option(4.5, help="Discharge pressure bar"),
    voltage: float = typer.Option(24.0, help="Diesel start battery voltage V"),
) -> None:
    """Evaluate emergency fire pump sea suction, priming, and discharge pressure."""
    telem = EmergencyFirePumpTelemetry(suction_head_m, vacuum_bar, elapsed_sec, discharge_p, voltage, True)
    res = EmergencyFirePumpSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux3_app.command("oilmist-check")
def check_oil_mist(
    mist_mg_l: float = typer.Option(0.5, help="Mist concentration mg/L"),
    obscuration: float = typer.Option(4.0, help="Lens obscuration %/m"),
    rpm: float = typer.Option(95.0, help="Engine RPM"),
) -> None:
    """Evaluate crankcase oil mist optical detector and auto slowdown."""
    telem = OilMistTelemetry(mist_mg_l, obscuration, rpm, True, True)
    res = OilMistDetectorEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux3_app.command("scrubbereffluent-check")
def check_scrubber_effluent(
    ph: float = typer.Option(7.2, help="Overboard washwater pH"),
    pah_ug_l: float = typer.Option(15.0, help="PAH increase ug/L"),
    turbidity_fntu: float = typer.Option(8.0, help="Turbidity increase FNTU"),
    nitrate: float = typer.Option(20.0, help="Nitrate concentration mg/L"),
) -> None:
    """Evaluate scrubber washwater effluent environmental compliance under MEPC.340(77)."""
    telem = ScrubberEffluentTelemetry(ph, pah_ug_l, turbidity_fntu, nitrate, False, True)
    res = ScrubberEffluentSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")
