"""CLI commands for Maritime Safety Auxiliary Batch 20 (Phases 539-542).
Strictly < 85 LOC, Typer subcommands for Stuffing Box, BESS Thermal, Dry Powder, Common-Rail Booster.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_539_piston_rod_stuffing_box_drain import (
    PistonRodStuffingBoxDrainEngine, StuffingBoxDrainTelemetry,
)
from src.core.maritime.phase_540_bess_thermal_runaway_offgas_interlock import (
    BessThermalRunawayOffgasEngine, BessThermalRunawayTelemetry,
)
from src.core.maritime.phase_541_dry_chemical_powder_nitrogen_interlock import (
    DryChemicalPowderNitrogenEngine, DryPowderSystemTelemetry,
)
from src.core.maritime.phase_542_common_rail_fuel_booster_interlock import (
    CommonRailBoosterTelemetry, CommonRailFuelBoosterEngine,
)

maritime_aux20_app = typer.Typer(
    name="maritime-aux20",
    help="Maritime Safety Automation Batch 20: Stuffing Box, BESS Thermal, Dry Powder, Common-Rail",
)
console = Console()


@maritime_aux20_app.command("stuffingbox-check")
def check_stuffingbox(
    blowby_bar: float = 0.08, temp_c: float = 52.0, leak_l_24h: float = 6.0, fe_ppm: float = 40.0
) -> None:
    res = PistonRodStuffingBoxDrainEngine.evaluate(
        StuffingBoxDrainTelemetry(blowby_bar, temp_c, leak_l_24h, fe_ppm)
    )
    console.print(f"[bold cyan]Stuffing Box:[/bold cyan] {res.state.value} | Slowdown: {res.engine_slowdown_cmd} | Code: {res.interlock_code}")


@maritime_aux20_app.command("bess-check")
def check_bess(
    cell_c: float = 32.0, h2_lel: float = 0.0, co_ppm: float = 2.0, flow_l_min: float = 28.0
) -> None:
    res = BessThermalRunawayOffgasEngine.evaluate(
        BessThermalRunawayTelemetry(cell_c, h2_lel, co_ppm, flow_l_min)
    )
    console.print(f"[bold green]BESS Enclosure:[/bold green] {res.state.value} | Deluge: {res.water_mist_deluge_release_cmd} | Code: {res.interlock_code}")


@maritime_aux20_app.command("dcp-check")
def check_dcp(
    n2_bar: float = 190.0, vessel_bar: float = 14.5, elapsed_s: float = 20.0, discharge: bool = False
) -> None:
    res = DryChemicalPowderNitrogenEngine.evaluate(
        DryPowderSystemTelemetry(n2_bar, vessel_bar, elapsed_s, discharge)
    )
    console.print(f"[bold yellow]Dry Powder:[/bold yellow] {res.state.value} | Valve Open: {res.main_powder_release_valve_open} | Code: {res.interlock_code}")


@maritime_aux20_app.command("commonrail-check")
def check_commonrail(
    rail_bar: float = 850.0, servo_bar: float = 220.0, eprv_lifted: bool = False, flv_seized: bool = False
) -> None:
    res = CommonRailFuelBoosterEngine.evaluate(
        CommonRailBoosterTelemetry(rail_bar, servo_bar, eprv_lifted, flv_seized)
    )
    console.print(f"[bold red]Common-Rail:[/bold red] {res.state.value} | Slowdown: {res.engine_slowdown_cmd} | Code: {res.interlock_code}")
