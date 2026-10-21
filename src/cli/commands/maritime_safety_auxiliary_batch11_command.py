"""CLI commands for Maritime Safety Auxiliary Batch 11 (Phases 503-506).
Strictly < 90 LOC, Typer subcommands for Hull ICCP, Sea Chest MGPS, Galley HVAC, and Reefer.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_503_iccp_hull_potential_anode import (
    IccpHullPotentialAnodeEngine, IccpTelemetry,
)
from src.core.maritime.phase_504_mgps_sea_chest_dosing import (
    MgpsSeaChestDosingEngine, MgpsTelemetry,
)
from src.core.maritime.phase_505_hvac_galley_fire_damper import (
    HvacGalleyFireDamperEngine, HvacGalleyTelemetry,
)
from src.core.maritime.phase_506_provision_reefer_leak_safety import (
    ProvisionReeferLeakSafetyEngine, ProvisionReeferTelemetry,
)

maritime_aux11_app = typer.Typer(
    name="maritime-aux11",
    help="Maritime Safety Automation Batch 11: Hull ICCP, MGPS, Galley HVAC, Provision Reefer",
)
console = Console()


@maritime_aux11_app.command("iccp-check")
def check_iccp(potential_mv: float = -850.0, current_amps: float = 65.0) -> None:
    res = IccpHullPotentialAnodeEngine.evaluate(
        IccpTelemetry(reference_potential_mv=potential_mv, anode_current_amps=current_amps)
    )
    console.print(f"[bold cyan]ICCP State:[/bold cyan] {res.protection_state.value} | Current: {res.recommended_current_amps}A | Code: {res.alarm_code}")


@maritime_aux11_app.command("mgps-check")
def check_mgps(flow_m3_h: float = 60.0, cu_amps: float = 4.2, al_amps: float = 8.0, voltage_v: float = 8.5) -> None:
    res = MgpsSeaChestDosingEngine.evaluate(
        MgpsTelemetry(seawater_flow_m3_h=flow_m3_h, copper_anode_amps=cu_amps, aluminum_anode_amps=al_amps, cell_voltage_v=voltage_v)
    )
    console.print(f"[bold green]MGPS State:[/bold green] {res.operating_state.value} | Power: {res.dosing_power_enabled} | Code: {res.alarm_code}")


@maritime_aux11_app.command("hvac-check")
def check_hvac(duct_temp_c: float = 42.0, smoke: bool = False, manual_pull: bool = False) -> None:
    res = HvacGalleyFireDamperEngine.evaluate(
        HvacGalleyTelemetry(galley_duct_temp_c=duct_temp_c, recirc_smoke_detected=smoke, manual_fire_pull_activated=manual_pull)
    )
    console.print(f"[bold red]HVAC Mode:[/bold red] {res.damper_mode.value} | Damper Closed: {res.fire_damper_closed} | Code: {res.alarm_code}")


@maritime_aux11_app.command("reefer-check")
def check_reefer(leak_ppm: float = 20.0, discharge_bar: float = 14.5, panic_button: bool = False) -> None:
    res = ProvisionReeferLeakSafetyEngine.evaluate(
        ProvisionReeferTelemetry(refrigerant_leak_ppm=leak_ppm, discharge_pressure_bar=discharge_bar, personnel_panic_button_active=panic_button)
    )
    console.print(f"[bold yellow]Reefer State:[/bold yellow] {res.plant_state.value} | Compressor: {res.compressor_running} | Code: {res.alarm_code}")
