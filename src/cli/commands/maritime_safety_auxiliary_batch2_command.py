"""CLI Commands for Maritime Automation Phases 467-470.

Exposes:
- chilledwater-check
- incinerator-check
- deepwell-check
- settlingtank-check
Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_467_chilled_water_antifreeze import (
    ChilledWaterAntiFreezeEngine,
    ChilledWaterTelemetry,
)
from src.core.maritime.phase_468_incinerator_flue_protection import (
    IncineratorProtectionEngine,
    IncineratorTelemetry,
)
from src.core.maritime.phase_469_deepwell_pump_stripping import (
    DeepwellPumpProtectionEngine,
    DeepwellPumpTelemetry,
)
from src.core.maritime.phase_470_settling_tank_safety import (
    SettlingTankSafetyEngine,
    SettlingTankTelemetry,
)

maritime_aux2_app = typer.Typer(
    name="maritime-aux2",
    help="Maritime Automation Phases 467-470: Chilled Water, Incinerator, Deepwell Pump, Settling Tank",
)
console = Console()


@maritime_aux2_app.command("chilledwater-check")
def check_chilled_water(
    supply_temp: float = typer.Option(7.0, help="Supply temp deg C"),
    return_temp: float = typer.Option(12.0, help="Return temp deg C"),
    suction_p: float = typer.Option(3.5, help="Suction pressure bar"),
    flow: float = typer.Option(25.0, help="Circulation flow m3/h"),
) -> None:
    """Evaluate chilled water anti-freeze and low suction protection."""
    telem = ChilledWaterTelemetry(supply_temp, return_temp, suction_p, flow, True)
    res = ChilledWaterAntiFreezeEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux2_app.command("incinerator-check")
def check_incinerator(
    chamber_temp: float = typer.Option(900.0, help="Chamber temp deg C"),
    flue_temp: float = typer.Option(280.0, help="Flue temp deg C"),
    draft_mm: float = typer.Option(-25.0, help="Furnace draft mm WG"),
    sludge_valve: bool = typer.Option(True, help="Sludge valve open"),
) -> None:
    """Evaluate incinerator flue gas temperature and draft vacuum."""
    telem = IncineratorTelemetry(chamber_temp, flue_temp, draft_mm, sludge_valve, True)
    res = IncineratorProtectionEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux2_app.command("deepwell-check")
def check_deepwell_pump(
    discharge_p: float = typer.Option(6.0, help="Discharge pressure bar"),
    casing_temp: float = typer.Option(45.0, help="Casing temp deg C"),
    motor_current: float = typer.Option(80.0, help="Motor current % FLA"),
    stripping: bool = typer.Option(False, help="Stripping mode"),
    purge_n2_p: float = typer.Option(5.0, help="Purge N2 pressure bar"),
) -> None:
    """Evaluate deepwell cargo pump stripping and dry run protection."""
    telem = DeepwellPumpTelemetry(discharge_p, casing_temp, motor_current, stripping, purge_n2_p, True)
    res = DeepwellPumpProtectionEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")


@maritime_aux2_app.command("settlingtank-check")
def check_settling_tank(
    oil_temp: float = typer.Option(75.0, help="Oil temperature deg C"),
    level_pct: float = typer.Option(70.0, help="Oil level %"),
    fire_wire: bool = typer.Option(False, help="Fire wire melted"),
    remote_qcv: bool = typer.Option(False, help="Remote QCV pull"),
) -> None:
    """Evaluate fuel oil settling tank temperature and quick-closing valve."""
    telem = SettlingTankTelemetry(oil_temp, level_pct, True, fire_wire, remote_qcv)
    res = SettlingTankSafetyEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}")
    console.print(f"Remarks: {res.remarks}")
